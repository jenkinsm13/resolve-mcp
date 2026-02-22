"""
AI-powered color grading, B-roll insertion, and grade consistency tools.

Three Gemini-driven tools that extend the Resolve MCP server beyond editing:

- ``resolve_auto_grade``: apply a creative look via AI-suggested CDL values
- ``resolve_auto_broll``: auto-populate B-roll track from media pool footage
- ``resolve_check_grade_consistency``: audit + fix color consistency across clips
"""

from __future__ import annotations

import contextlib
import json
import shutil
import tempfile
import threading
from pathlib import Path

from .build_worker import _active_build_workers
from .config import MODEL, client, log, mcp
from .media import load_sidecars
from .prompts_color import AUTO_BROLL_PROMPT, AUTO_GRADE_PROMPT, GRADE_CONSISTENCY_PROMPT
from .resolve import _boilerplate
from .resolve_build import build_timeline_direct
from .retry import retry_gemini
from .timeline import upload_media_for_editing

_BROLL_PROGRESS_FILE = ".resolve_broll_progress.json"

# Background results for sync/background hybrid (auto_grade, consistency).
_color_results: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _frames_to_tc(frame: int, fps: float) -> str:
    """Convert a frame number to ``HH:MM:SS:FF`` timecode string."""
    fps_int = round(fps)
    if fps_int <= 0:
        fps_int = 24
    f = frame % fps_int
    total_secs = frame // fps_int
    s = total_secs % 60
    total_mins = total_secs // 60
    m = total_mins % 60
    h = total_mins // 60
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def _export_timeline_frames(project, timeline, tmpdir: str) -> list[dict]:
    """Export one mid-frame PNG per clip on video track 1.

    Returns ``[{clip_index, clip_name, frame_path, item}, ...]``.
    *tmpdir* must be an existing directory; caller handles cleanup.
    """
    fps = 24.0
    with contextlib.suppress(Exception):
        fps = float(timeline.GetSetting("timelineFrameRate"))

    items = timeline.GetItemListInTrack("video", 1) or []
    frames: list[dict] = []

    for idx, item in enumerate(items, start=1):
        start = item.GetStart()
        end = item.GetEnd()
        mid = (start + end) // 2

        # Move playhead to clip midpoint.
        tc = _frames_to_tc(mid, fps)
        timeline.SetCurrentTimecode(tc)

        # Export frame.
        clip_name = ""
        try:
            pool_item = item.GetMediaPoolItem()
            if pool_item:
                clip_name = pool_item.GetName()
        except Exception:
            pass
        if not clip_name:
            clip_name = f"clip_{idx}"

        safe_name = clip_name.replace("/", "_").replace("\\", "_").replace(":", "_")
        out_path = str(Path(tmpdir) / f"{idx:03d}_{safe_name}.png")

        exported = project.ExportCurrentFrameAsStill(out_path)
        if not exported or not Path(out_path).exists():
            log.warning("Frame export failed for clip %d (%s)", idx, clip_name)
            continue

        frames.append(
            {
                "clip_index": idx,
                "clip_name": clip_name,
                "frame_path": out_path,
                "item": item,
            }
        )

    return frames


def _apply_cdl_to_item(item, cdl_vals: dict, node_label: str = "AI Grade") -> bool:
    """Add a serial node and apply CDL values to a timeline item.

    Returns True on success.  *cdl_vals* must have slope_r/g/b, offset_r/g/b,
    power_r/g/b, saturation keys.
    """
    try:
        node_graph = item.GetNodeGraph()
        if not node_graph:
            return False

        # Add a new serial node at the end of the chain.
        num_before = node_graph.GetNumNodes()
        node_graph.AddSerialNode(num_before)
        new_node = node_graph.GetNumNodes()

        # Label it so the colorist knows it's AI-generated.
        with contextlib.suppress(Exception):
            node_graph.SetNodeLabel(new_node, node_label)

        cdl = {
            "NodeIndex": str(new_node),
            "Slope": f"{cdl_vals['slope_r']} {cdl_vals['slope_g']} {cdl_vals['slope_b']}",
            "Offset": f"{cdl_vals['offset_r']} {cdl_vals['offset_g']} {cdl_vals['offset_b']}",
            "Power": f"{cdl_vals['power_r']} {cdl_vals['power_g']} {cdl_vals['power_b']}",
            "Saturation": str(cdl_vals.get("saturation", 1.0)),
        }
        return bool(item.SetCDL(cdl))
    except Exception as exc:
        log.warning("CDL apply failed: %s", exc)
        return False


def _build_image_parts(frames: list[dict], reference_path: str = "") -> list:
    """Build Gemini content parts from exported frame PNGs.

    Returns a list of ``types.Part`` objects — each frame as an inline image
    preceded by a text label, plus an optional reference image.
    """
    from google.genai import types
    from PIL import Image

    parts: list = []

    if reference_path and Path(reference_path).exists():
        parts.append(types.Part.from_text(text="REFERENCE IMAGE (match this look):"))
        parts.append(types.Part.from_image(image=Image.open(reference_path)))

    for f in frames:
        label = f"Clip {f['clip_index']}: {f['clip_name']}"
        parts.append(types.Part.from_text(text=label))
        parts.append(types.Part.from_image(image=Image.open(f["frame_path"])))

    return parts


# ---------------------------------------------------------------------------
# Tool 1: AI Auto Grade
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_auto_grade(style: str, reference_image_path: str = "") -> str:
    """Apply an AI-suggested color grade to every clip on the current timeline.

    Exports one frame per clip, sends them to Gemini with your creative direction,
    and applies the returned CDL values on a new node (preserving existing grades).

    *style*: creative direction — e.g. ``"warm cinematic"``, ``"cool desaturated noir"``,
    ``"match the reference image"``, ``"teal and orange blockbuster"``.

    *reference_image_path*: optional absolute path to a reference frame/image.
    Gemini will match the grade to this reference.

    Clips ≤ 15: runs synchronously.  Clips > 15: runs in background — re-call
    to retrieve the result.
    """
    if client is None:
        return "Error: GEMINI_API_KEY not set. AI grading requires Gemini."
    from google.genai import types

    try:
        _, project, _ = _boilerplate()
    except ValueError as e:
        return str(e)

    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No active timeline in Resolve."

    tl_name = timeline.GetName()
    result_key = f"grade:{tl_name}"

    # Check for a previously launched background result.
    if result_key in _color_results:
        entry = _color_results[result_key]
        if entry.get("result"):
            result = entry["result"]
            del _color_results[result_key]
            return result
        if entry.get("error"):
            error = entry["error"]
            del _color_results[result_key]
            return f"Error during grading: {error}"
        if entry.get("thread") and entry["thread"].is_alive():
            return f"AI grading still running for '{tl_name}'…"
        del _color_results[result_key]

    def _run_grade() -> str:
        tmpdir = tempfile.mkdtemp(prefix="resolve_grade_")
        try:
            frames = _export_timeline_frames(project, timeline, tmpdir)
            if not frames:
                return "No frames exported — ensure video track 1 has clips."

            clip_names = [f["clip_name"] for f in frames]
            reference_section = ""
            if reference_image_path and Path(reference_image_path).exists():
                reference_section = (
                    "A REFERENCE IMAGE is included.  Match all clips to this look "
                    "as closely as possible while adapting to each clip's exposure."
                )

            prompt = AUTO_GRADE_PROMPT.format(
                num_clips=len(frames),
                style=style,
                reference_section=reference_section,
                clip_names_json=json.dumps(clip_names),
            )

            image_parts = _build_image_parts(frames, reference_image_path)

            response = retry_gemini(
                client.models.generate_content,
                model=MODEL,
                contents=image_parts + [types.Part.from_text(text=prompt)],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            decoder = json.JSONDecoder()
            grades, _ = decoder.raw_decode(response.text.strip())

            if not isinstance(grades, list):
                return f"Gemini returned unexpected format: {response.text[:300]}"

            applied = 0
            rationales: list[str] = []
            for grade in grades:
                idx = int(grade.get("clip_index", 0))
                match = next((f for f in frames if f["clip_index"] == idx), None)
                if match and _apply_cdl_to_item(match["item"], grade, node_label="AI Grade"):
                    applied += 1
                    rationale = grade.get("rationale", "")
                    if rationale:
                        rationales.append(f"  {idx}. {match['clip_name']}: {rationale}")

            summary = f"Applied '{style}' grade to {applied}/{len(frames)} clips."
            if rationales:
                summary += "\n" + "\n".join(rationales[:10])
            return summary

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    # Sync for small timelines, background for large.
    items = timeline.GetItemListInTrack("video", 1) or []
    if len(items) <= 15:
        try:
            return _run_grade()
        except Exception as exc:
            return f"Error during grading: {exc}"

    entry: dict = {"result": None, "error": None, "thread": None}
    _color_results[result_key] = entry

    def _bg():
        try:
            entry["result"] = _run_grade()
        except Exception as exc:
            entry["error"] = str(exc)

    t = threading.Thread(target=_bg, daemon=True)
    entry["thread"] = t
    t.start()
    return (
        f"AI grading running in background for '{tl_name}' ({len(items)} clips). "
        "Re-call resolve_auto_grade() to retrieve the result."
    )


# ---------------------------------------------------------------------------
# Tool 2: Smart B-Roll insertion
# ---------------------------------------------------------------------------


def _broll_worker(
    resolve_obj,
    project,
    media_pool,
    timeline,
    sidecars: list[dict],
    aroll_manifest: list[dict],
    instruction: str,
    target_track: int,
    progress_root: Path,
) -> None:
    """Background thread: upload footage, ask Gemini for B-roll, build it."""
    from google.genai import types

    progress_file = progress_root / _BROLL_PROGRESS_FILE

    def _write(data: dict) -> None:
        progress_file.write_text(json.dumps(data, indent=2))

    try:
        _write(
            {
                "status": "uploading",
                "detail": f"Uploading {len(sidecars)} file(s) to Gemini…",
                "error": None,
            }
        )

        file_refs = upload_media_for_editing(sidecars)
        if not file_refs:
            _write({"status": "error", "detail": "No media uploaded.", "error": "upload returned empty"})
            return

        _write(
            {
                "status": "analyzing",
                "detail": "Gemini selecting B-roll placements…",
                "error": None,
            }
        )

        prompt = AUTO_BROLL_PROMPT.format(
            target_track=target_track,
            aroll_json=json.dumps(aroll_manifest, indent=2),
            sidecars_json=json.dumps(sidecars, indent=2),
            instruction=instruction,
        )

        response = retry_gemini(
            client.models.generate_content,
            model=MODEL,
            contents=list(file_refs) + [prompt],
            config=types.GenerateContentConfig(
                media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                response_mime_type="application/json",
            ),
        )

        decoder = json.JSONDecoder()
        result, _ = decoder.raw_decode(response.text.strip())

        cuts = result.get("cuts", [])
        if not cuts:
            _write({"status": "error", "detail": "Gemini returned no B-roll cuts.", "error": "empty cuts list"})
            return

        _write({"status": "building", "detail": f"Inserting {len(cuts)} B-roll clips…", "error": None})

        # Force all cuts to the target track and add timeline_out for build.
        for cut in cuts:
            cut["track"] = target_track
            if "timeline_out" not in cut:
                duration = float(cut.get("end_sec", 0)) - float(cut.get("start_sec", 0))
                cut["timeline_out"] = float(cut.get("timeline_in", 0)) + duration

        edit_plan = {
            "timeline_name": timeline.GetName(),
            "cuts": cuts,
        }

        success, msg = build_timeline_direct(edit_plan, resolve_obj)

        editorial = result.get("editorial_notes", "")
        detail = f"B-roll inserted: {len(cuts)} clips on track {target_track}. {msg}"
        if editorial:
            detail += f"\nStrategy: {editorial}"

        _write({"status": "complete", "detail": detail, "error": None})

    except Exception as exc:
        log.exception("B-roll worker crashed.")
        _write({"status": "error", "detail": "B-roll insertion failed.", "error": str(exc)})


@mcp.tool
def resolve_auto_broll(instruction: str, footage_folder: str = "", target_track: int = 2) -> str:
    """Auto-populate a B-roll track using AI-selected footage.

    Reads the A-roll on video track 1, examines available footage via sidecar
    metadata, uploads proxies for Gemini to watch, and inserts B-roll on the
    specified track.

    *instruction*: creative direction — e.g. ``"cover interview with product shots"``,
    ``"add dynamic landscape B-roll over talking heads"``.

    *footage_folder*: optional path to folder with sidecar JSONs.  Auto-detected
    from media pool clip paths if omitted.

    *target_track*: video track for B-roll (default 2).

    Runs in background.  Monitor with ``resolve_auto_broll_status()``.
    """
    if client is None:
        return "Error: GEMINI_API_KEY not set. AI B-roll requires Gemini."

    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No active timeline in Resolve."

    tl_name = timeline.GetName()

    # Build A-roll manifest from track 1.
    items = timeline.GetItemListInTrack("video", 1) or []
    if not items:
        return "No clips on video track 1. Add A-roll first."

    fps = 24.0
    with contextlib.suppress(Exception):
        fps = float(timeline.GetSetting("timelineFrameRate"))

    aroll_manifest: list[dict] = []
    source_dirs: set[Path] = set()
    for i, item in enumerate(items, start=1):
        clip_name = ""
        source_file = ""
        try:
            pool_item = item.GetMediaPoolItem()
            if pool_item:
                clip_name = pool_item.GetName()
                source_file = pool_item.GetClipProperty("File Path") or ""
                if source_file:
                    source_dirs.add(Path(source_file).parent)
        except Exception:
            pass

        aroll_manifest.append(
            {
                "index": i,
                "clip_name": clip_name or f"clip_{i}",
                "start_sec": round(item.GetStart() / fps, 3),
                "end_sec": round(item.GetEnd() / fps, 3),
                "duration_sec": round((item.GetEnd() - item.GetStart()) / fps, 3),
                "source_file": source_file,
            }
        )

    # Find footage sidecars.
    if footage_folder:
        root = Path(footage_folder).resolve()
        if not root.is_dir():
            return f"Error: footage_folder '{footage_folder}' is not a valid directory."
        sidecars = load_sidecars(root)
    else:
        sidecars = []
        for d in source_dirs:
            sidecars.extend(load_sidecars(d))

    if not sidecars:
        return "No sidecar JSONs found. Run ingest on your footage first."

    # Deduplicate sidecars by file_path.
    seen: set[str] = set()
    unique: list[dict] = []
    for sc in sidecars:
        fp = sc.get("file_path", "")
        if fp not in seen:
            seen.add(fp)
            unique.append(sc)
    sidecars = unique

    # Find a root directory for progress file.
    progress_root = Path(sidecars[0].get("file_path", ".")).parent if sidecars else Path(".")

    key = f"broll:{tl_name}"
    if key in _active_build_workers and _active_build_workers[key].is_alive():
        return "B-roll insertion already running for this timeline."

    t = threading.Thread(
        target=_broll_worker,
        args=(
            resolve,
            project,
            media_pool,
            timeline,
            sidecars,
            aroll_manifest,
            instruction,
            target_track,
            progress_root,
        ),
        daemon=True,
    )
    t.start()
    _active_build_workers[key] = t

    return (
        f"B-roll insertion started for '{tl_name}': {len(sidecars)} source clip(s), "
        f"{len(aroll_manifest)} A-roll clips on track 1.\n"
        f"Monitor: resolve_auto_broll_status()"
    )


@mcp.tool
def resolve_auto_broll_status() -> str:
    """Check progress of a ``resolve_auto_broll`` session.

    Reads the progress file written by the background worker.
    """
    try:
        _, project, _ = _boilerplate()
    except ValueError as e:
        return str(e)

    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "No active timeline."

    tl_name = timeline.GetName()

    # Try to find progress file from media pool clip paths.
    items = timeline.GetItemListInTrack("video", 1) or []
    for item in items:
        try:
            pool_item = item.GetMediaPoolItem()
            if pool_item:
                fp = pool_item.GetClipProperty("File Path")
                if fp:
                    pf = Path(fp).parent / _BROLL_PROGRESS_FILE
                    if pf.exists():
                        prog = json.loads(pf.read_text(encoding="utf-8"))
                        status = prog.get("status", "unknown")
                        detail = prog.get("detail", "")
                        error = prog.get("error")
                        if status == "complete":
                            return f"B-roll complete for '{tl_name}':\n{detail}"
                        if status == "error":
                            return f"B-roll failed: {detail}" + (f"\n{error}" if error else "")
                        return f"B-roll {status}: {detail}"
        except Exception:
            continue

    key = f"broll:{tl_name}"
    if key in _active_build_workers and _active_build_workers[key].is_alive():
        return f"B-roll insertion running for '{tl_name}' (progress file not yet written)."

    return "No B-roll session in progress for this timeline."


# ---------------------------------------------------------------------------
# Tool 3: Grade Consistency Checker
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_check_grade_consistency(apply_fixes: str = "false") -> str:
    """Audit color grade consistency across all clips on the current timeline.

    Exports one frame per clip, sends the batch to Gemini for analysis, and
    returns a detailed consistency report with per-clip issues.

    *apply_fixes*: ``"true"`` to auto-apply Gemini's suggested CDL corrections
    on a new node.  ``"false"`` (default) for report only.

    Clips ≤ 15: runs synchronously.  Clips > 15: runs in background — re-call
    to retrieve the result.
    """
    if client is None:
        return "Error: GEMINI_API_KEY not set. Grade consistency check requires Gemini."
    from google.genai import types

    try:
        _, project, _ = _boilerplate()
    except ValueError as e:
        return str(e)

    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No active timeline in Resolve."

    tl_name = timeline.GetName()
    result_key = f"consistency:{tl_name}"
    do_apply = apply_fixes.lower().strip() in ("true", "yes", "1")

    # Check for background result.
    if result_key in _color_results:
        entry = _color_results[result_key]
        if entry.get("result"):
            result = entry["result"]
            del _color_results[result_key]
            return result
        if entry.get("error"):
            error = entry["error"]
            del _color_results[result_key]
            return f"Error during consistency check: {error}"
        if entry.get("thread") and entry["thread"].is_alive():
            return f"Consistency check still running for '{tl_name}'…"
        del _color_results[result_key]

    def _run_check() -> str:
        tmpdir = tempfile.mkdtemp(prefix="resolve_consistency_")
        try:
            frames = _export_timeline_frames(project, timeline, tmpdir)
            if not frames:
                return "No frames exported — ensure video track 1 has clips."

            prompt = GRADE_CONSISTENCY_PROMPT.format(num_clips=len(frames))
            image_parts = _build_image_parts(frames)

            response = retry_gemini(
                client.models.generate_content,
                model=MODEL,
                contents=image_parts + [types.Part.from_text(text=prompt)],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            decoder = json.JSONDecoder()
            report, _ = decoder.raw_decode(response.text.strip())

            # Build human-readable output.
            lines: list[str] = []
            overall = report.get("overall_assessment", "")
            score = report.get("consistency_score", "?")
            lines.append(f"Grade Consistency: {score}/10")
            lines.append(overall)
            lines.append("")

            clips = report.get("clips", [])
            fixes_applied = 0

            for clip_report in clips:
                idx = clip_report.get("clip_index", 0)
                name = clip_report.get("clip_name", f"clip_{idx}")
                status = clip_report.get("status", "unknown")
                issues = clip_report.get("issues", [])

                icon = {"consistent": "✓", "minor_issue": "~", "inconsistent": "✗"}.get(status, "?")
                lines.append(f"  {icon} Clip {idx} ({name}): {status}")
                for issue in issues:
                    lines.append(f"      - {issue}")

                if do_apply and clip_report.get("suggested_cdl"):
                    match = next((f for f in frames if f["clip_index"] == idx), None)
                    if match and _apply_cdl_to_item(match["item"], clip_report["suggested_cdl"], "AI Fix"):
                        fixes_applied += 1
                        lines.append("      → CDL fix applied")

            if do_apply:
                lines.append(f"\nApplied {fixes_applied} CDL correction(s).")

            return "\n".join(lines)

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    # Sync for small timelines, background for large.
    items = timeline.GetItemListInTrack("video", 1) or []
    if len(items) <= 15:
        try:
            return _run_check()
        except Exception as exc:
            return f"Error during consistency check: {exc}"

    entry: dict = {"result": None, "error": None, "thread": None}
    _color_results[result_key] = entry

    def _bg():
        try:
            entry["result"] = _run_check()
        except Exception as exc:
            entry["error"] = str(exc)

    t = threading.Thread(target=_bg, daemon=True)
    entry["thread"] = t
    t.start()
    return (
        f"Consistency check running in background for '{tl_name}' ({len(items)} clips). "
        "Re-call resolve_check_grade_consistency() to retrieve the result."
    )
