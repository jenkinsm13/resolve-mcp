"""
Resolve AI tools: marker placement, timeline critique, and marker-driven builds.
"""

import json
import threading
from pathlib import Path

from .config import MODEL, client, log, mcp
from .retry import retry_gemini
from .resolve import _boilerplate, _collect_clips_recursive
from .resolve_build import build_timeline_direct, read_timeline_markers, markers_to_slots
from .media import load_sidecars
from .prompts import TIMELINE_CRITIQUE_PROMPT_TEMPLATE, MARKER_EDIT_PROMPT_TEMPLATE
from .timeline import upload_media_for_editing


@mcp.tool
def resolve_add_markers(folder_path: str) -> str:
    """
    Read the ``directors_notes`` from the ``.edl.json`` in *folder_path* and
    add colour-coded markers to the currently active Resolve timeline at the
    corresponding timecode positions.
    """
    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    root = Path(folder_path).resolve()
    if not root.is_dir():
        return f"Error: '{folder_path}' is not a valid directory."

    edl_files = sorted(f for f in root.glob("*.edl.json") if not f.name.startswith("."))
    if not edl_files:
        return "No .edl.json found. Run build_timeline first."

    try:
        edit_plan = json.loads(edl_files[0].read_text(encoding="utf-8"))
    except Exception as exc:
        return f"Error reading {edl_files[0].name}: {exc}"

    notes = edit_plan.get("directors_notes", [])
    if not notes:
        return "No directors_notes in edit plan."

    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No active timeline in Resolve. Open or build a timeline first."

    try:
        fps = float(timeline.GetSetting("timelineFrameRate"))
    except Exception:
        fps = 24.0

    colors = ["Blue", "Cyan", "Green", "Yellow", "Red", "Purple"]
    added = 0
    for i, note in enumerate(notes):
        try:
            frame_id = round(float(note.get("timeline_sec", 0)) * fps)
            alt = note.get("alternative", "")
            custom_data = json.dumps({"alt": alt[:200]}) if alt else ""
            timeline.AddMarker(
                frame_id, colors[i % len(colors)],
                f"[{i + 1}] Edit Note",
                note.get("decision", "")[:255],
                1, custom_data,
            )
            added += 1
        except Exception as exc:
            log.warning("Marker %d failed: %s", i, exc)

    return f"Added {added}/{len(notes)} markers to timeline '{timeline.GetName()}'."


@mcp.tool
def resolve_analyze_timeline() -> str:
    """
    Analyze the currently active Resolve timeline using Gemini.

    Reads clips from video tracks 1–2, finds their sidecar JSONs, uploads the
    proxy files, and requests a detailed editorial critique.

    Clips ≤ 20: runs synchronously.  Clips > 20: runs in background.
    """
    if client is None:
        return "Error: GEMINI_API_KEY not set. This tool requires Gemini."
    from google.genai import types
    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No active timeline in Resolve."

    tl_name = timeline.GetName()
    try:
        fps = float(timeline.GetSetting("timelineFrameRate"))
    except Exception:
        fps = 24.0

    clip_info: list[dict] = []
    for track_num in (1, 2):
        for item in (timeline.GetItemListInTrack("video", track_num) or []):
            try:
                pool_item = item.GetMediaPoolItem()
                if pool_item is None:
                    continue
                fp = pool_item.GetClipProperty("File Path")
                clip_info.append({
                    "track": track_num,
                    "source_file": fp,
                    "start_frame": item.GetStart(),
                    "end_frame": item.GetEnd(),
                })
            except Exception:
                continue

    if not clip_info:
        return "No clips found on video tracks 1–2 of the current timeline."

    source_dirs: set[Path] = set()
    for ci in clip_info:
        if ci.get("source_file"):
            source_dirs.add(Path(ci["source_file"]).parent)

    sidecars: list[dict] = []
    for d in source_dirs:
        sidecars.extend(load_sidecars(d))

    def _run_critique():
        file_refs = upload_media_for_editing(sidecars) if sidecars else []
        prompt = TIMELINE_CRITIQUE_PROMPT_TEMPLATE.format(
            timeline_name=tl_name,
            clips_json=json.dumps(clip_info, indent=2),
            sidecars_json=json.dumps(sidecars, indent=2),
        )
        response = retry_gemini(
            client.models.generate_content,
            model=MODEL,
            contents=list(file_refs) + [prompt],
            config=types.GenerateContentConfig(
                media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
            ),
        )
        return response.text

    if len(clip_info) <= 20:
        try:
            return _run_critique()
        except Exception as exc:
            return f"Error during critique: {exc}"

    result_holder: dict = {"result": None, "error": None}

    def _bg():
        try:
            result_holder["result"] = _run_critique()
        except Exception as exc:
            result_holder["error"] = str(exc)

    threading.Thread(target=_bg, daemon=True).start()
    return (
        f"Critique running in background for '{tl_name}' ({len(clip_info)} clips). "
        "Re-call resolve_analyze_timeline() to retrieve the result."
    )


@mcp.tool
def resolve_build_from_markers(instruction: str, footage_folder: str = "") -> str:
    """
    Read markers from the active Resolve timeline, pair consecutive same-color
    markers into cut slots, then ask Gemini to fill each slot with the best
    available footage.  The result is built via ``AppendToTimeline``.

    Marker color → track: Blue = Track 1 (A-roll), others = Track 2, 3, … in
    order of first appearance (B-roll).

    *footage_folder* is optional — auto-detected from media pool clip paths if omitted.
    """
    if client is None:
        return "Error: GEMINI_API_KEY not set. This tool requires Gemini."
    from google.genai import types
    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No active timeline in Resolve. Create or open one and add markers."

    markers = read_timeline_markers(timeline)
    if not markers:
        return (
            "No markers found on the active timeline. "
            "Add paired same-color markers to define cut slots, then re-run."
        )

    slots = markers_to_slots(markers)
    if not slots:
        return (
            f"Found {len(markers)} marker(s) but no complete pairs. "
            "Each slot needs two markers of the same color (in + out)."
        )

    if footage_folder:
        root = Path(footage_folder).resolve()
        if not root.is_dir():
            return f"Error: footage_folder '{footage_folder}' is not a valid directory."
        sidecars = load_sidecars(root)
    else:
        pool_clips = _collect_clips_recursive(media_pool.GetRootFolder())
        dirs: set[Path] = set()
        for clip in pool_clips.values():
            try:
                fp = clip.GetClipProperty("File Path")
                if fp:
                    dirs.add(Path(fp).parent)
            except Exception:
                continue
        sidecars = []
        for d in dirs:
            sidecars.extend(load_sidecars(d))

    if not sidecars:
        return (
            "No sidecar JSONs found. Run ingest_footage (or resolve_ingest_bin) "
            "on your footage folder first, then re-run."
        )

    seen: set[str] = set()
    unique_sidecars = []
    for sc in sidecars:
        fp = sc.get("file_path", "")
        if fp not in seen:
            seen.add(fp)
            unique_sidecars.append(sc)
    sidecars = unique_sidecars

    tl_name = timeline.GetName()
    color_summary = ", ".join(
        f"{c}×{sum(1 for s in slots if s['color']==c)}"
        for c in dict.fromkeys(s["color"] for s in slots)
    )
    log.info("Marker build: %d slots (%s), %d sidecars", len(slots), color_summary, len(sidecars))

    try:
        file_refs = upload_media_for_editing(sidecars)
    except Exception as exc:
        return f"Error uploading footage: {exc}"

    if not file_refs:
        return "Failed to upload any footage to Gemini. Check proxies exist."

    prompt = MARKER_EDIT_PROMPT_TEMPLATE.format(
        slots_json=json.dumps(slots, indent=2),
        sidecars_json=json.dumps(sidecars, indent=2),
        instruction=instruction,
    )

    try:
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
        edit_plan, _ = decoder.raw_decode(response.text.strip())
    except Exception as exc:
        return f"Gemini error: {exc}"

    cuts = edit_plan.get("cuts", [])
    if not cuts:
        return "Gemini returned an empty cut list."

    success, msg = build_timeline_direct(edit_plan, resolve)

    try:
        first_sidecar_path = Path(sidecars[0].get("file_path", ""))
        if first_sidecar_path.parent.is_dir():
            safe = edit_plan.get("timeline_name", "Marker_Edit").replace(":", " -").replace("/", "-")
            (first_sidecar_path.parent / f"{safe}.edl.json").write_text(
                json.dumps(edit_plan, indent=2)
            )
    except Exception:
        pass

    track_map_desc = "Blue→V1" + "".join(
        f", {s['color']}→V{s['track']}" for s in slots if s["color"] != "Blue"
    )
    return (
        f"Marker build from '{tl_name}': {len(slots)} slots ({color_summary}), "
        f"{track_map_desc}. {msg}"
    )
