"""
Resolve build tools: Gemini edit → AppendToTimeline pipeline.
"""

import contextlib
import json
import threading
from pathlib import Path

from .build import _active_build_workers
from .config import MODEL, client, mcp
from .ingest import _ingest_worker
from .media import load_sidecars
from .outputs import save_directors_notes, save_music_brief, save_voiceover_script
from .prompts import EDIT_PROMPT_TEMPLATE, MUSIC_BRIEF_ADDENDUM
from .resolve import _boilerplate, _find_bin
from .resolve_build import build_timeline_direct
from .resolve_ingest_tools import _dirs_from_bin
from .retry import retry_gemini
from .timeline import upload_media_for_editing

_RESOLVE_BUILD_PROGRESS = ".resolve_build_progress.json"


def _resolve_build_worker(root: Path, sidecars: list, instruction: str) -> None:
    """Background thread: upload → Gemini edit plan → AppendToTimeline."""
    from google.genai import types

    progress_file = root / _RESOLVE_BUILD_PROGRESS

    def _write(data):
        progress_file.write_text(json.dumps(data, indent=2))

    try:
        _write({"status": "uploading", "detail": f"Uploading {len(sidecars)} file(s)…", "error": None})

        file_refs = upload_media_for_editing(sidecars)
        if not file_refs:
            _write({"status": "error", "detail": "No media uploaded.", "error": "Check proxies."})
            return

        _write({"status": "editing", "detail": f"Gemini reviewing {len(file_refs)} files…", "error": None})

        prompt_text = EDIT_PROMPT_TEMPLATE.format(
            sidecars_json=json.dumps(sidecars, indent=2),
            instruction=instruction,
        )
        has_audio = any(sc.get("media_type") == "audio" for sc in sidecars)
        if not has_audio:
            prompt_text += MUSIC_BRIEF_ADDENDUM

        response = retry_gemini(
            client.models.generate_content,
            model=MODEL,
            contents=list(file_refs) + [prompt_text],
            config=types.GenerateContentConfig(
                media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                response_mime_type="application/json",
            ),
        )

        decoder = json.JSONDecoder()
        edit_plan, _ = decoder.raw_decode(response.text.strip())

        if isinstance(edit_plan, list):
            edit_plan = next((x for x in edit_plan if isinstance(x, dict)), None)
            if edit_plan is None:
                _write({"status": "error", "detail": "Gemini returned JSON array with no dict.", "error": None})
                return

        cuts = edit_plan.get("cuts", [])
        if not cuts:
            _write({"status": "error", "detail": "Gemini returned empty cut list.", "error": None})
            return

        safe_name = edit_plan.get("timeline_name", "AI_Edit").replace(":", " -").replace("/", "-")
        (root / f"{safe_name}.edl.json").write_text(json.dumps(edit_plan, indent=2), encoding="utf-8")
        save_directors_notes(root, safe_name, edit_plan)
        save_voiceover_script(root, safe_name, edit_plan)
        save_music_brief(root, safe_name, edit_plan)

        _write({"status": "building", "detail": f"Calling AppendToTimeline with {len(cuts)} cuts…", "error": None})

        from .resolve import get_resolve

        resolve_obj = get_resolve()
        if not resolve_obj:
            _write({"status": "error", "detail": "Resolve not running at build time.", "error": None})
            return

        success, msg = build_timeline_direct(edit_plan, resolve_obj)
        _write(
            {
                "status": "complete" if success else "error",
                "detail": msg,
                "error": None,
            }
        )

    except Exception as exc:
        _write({"status": "error", "detail": "Unexpected error.", "error": str(exc)})


@mcp.tool
def resolve_build_timeline(bin_name_or_folder: str, instruction: str) -> str:
    """
    Build an AI-edited timeline from a Resolve bin or a folder path.

    - If *bin_name_or_folder* is an existing filesystem path, uses sidecars there.
    - Otherwise treats it as a Resolve bin name and collects clip file paths.

    Use ``resolve_build_status(bin_name_or_folder)`` to monitor progress.
    """
    if client is None:
        return "Error: GEMINI_API_KEY not set. This tool requires Gemini."
    candidate = Path(bin_name_or_folder)
    if candidate.is_absolute() and candidate.is_dir():
        root = candidate
        sidecars = load_sidecars(root)
        if not sidecars:
            return "No sidecar JSONs found in folder. Run ingest_footage first."
        key = str(root)
        progress_file = root / _RESOLVE_BUILD_PROGRESS
        if key in _active_build_workers and _active_build_workers[key].is_alive():
            prog = json.loads(progress_file.read_text()) if progress_file.exists() else {}
            return f"Build already running: {prog.get('status', '?')} — {prog.get('detail', '?')}"
        t = threading.Thread(target=_resolve_build_worker, args=(root, sidecars, instruction), daemon=True)
        t.start()
        _active_build_workers[key] = t
        return (
            f"Build started for folder '{root}' ({len(sidecars)} sidecars). "
            f"Use resolve_build_status('{bin_name_or_folder}') to monitor."
        )

    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    target = _find_bin(media_pool.GetRootFolder(), bin_name_or_folder)
    if target is None:
        return f"Error: bin '{bin_name_or_folder}' not found in media pool."

    clips = target.GetClipList() or []
    if not clips:
        return f"Bin '{bin_name_or_folder}' is empty."

    dirs: set[Path] = set()
    for clip in clips:
        try:
            fp = clip.GetClipProperty("File Path")
            if fp:
                dirs.add(Path(fp).parent)
        except Exception:
            continue

    if not dirs:
        return f"Could not determine file paths for clips in '{bin_name_or_folder}'."

    root = sorted(dirs)[0]
    sidecars = load_sidecars(root)
    if not sidecars:
        return f"No sidecars found in '{root}'. Run resolve_ingest_bin('{bin_name_or_folder}') first."

    key = str(root)
    progress_file = root / _RESOLVE_BUILD_PROGRESS
    if key in _active_build_workers and _active_build_workers[key].is_alive():
        prog = json.loads(progress_file.read_text()) if progress_file.exists() else {}
        return f"Build already running: {prog.get('status', '?')} — {prog.get('detail', '?')}"

    t = threading.Thread(target=_resolve_build_worker, args=(root, sidecars, instruction), daemon=True)
    t.start()
    _active_build_workers[key] = t
    return (
        f"Build started for bin '{bin_name_or_folder}' ({len(sidecars)} sidecars in '{root}'). "
        f"Use resolve_build_status('{bin_name_or_folder}') to monitor."
    )


@mcp.tool
def resolve_build_status(bin_name_or_folder: str) -> str:
    """
    Check progress of a ``resolve_build_timeline`` or ``resolve_edit_bin`` job.
    Pass the same *bin_name_or_folder* argument used to start the build.
    """
    candidate = Path(bin_name_or_folder)
    if candidate.is_absolute() and candidate.is_dir():
        root = candidate
    else:
        try:
            resolve, project, media_pool = _boilerplate()
            target = _find_bin(media_pool.GetRootFolder(), bin_name_or_folder)
            if target:
                for clip in target.GetClipList() or []:
                    try:
                        fp = clip.GetClipProperty("File Path")
                        if fp:
                            root = Path(fp).parent
                            break
                    except Exception:
                        continue
            else:
                return f"Cannot locate bin '{bin_name_or_folder}'."
        except ValueError as e:
            return str(e)

    progress_file = root / _RESOLVE_BUILD_PROGRESS
    if not progress_file.exists():
        return "No resolve build in progress for this target."
    try:
        prog = json.loads(progress_file.read_text())
    except Exception:
        return "Could not read progress file."

    status = prog.get("status", "unknown")
    detail = prog.get("detail", "")
    error = prog.get("error")

    if status == "complete":
        return f"Build complete: {detail}"
    if status == "error":
        return f"Build failed: {detail}" + (f"\n{error}" if error else "")
    return f"Build {status}: {detail}"


@mcp.tool
def resolve_edit_bin(bin_name: str, instruction: str) -> str:
    """
    One-shot: find *bin_name* in Resolve, read clip file paths directly from
    the media pool (no disk searching), ingest any un-analyzed clips, then
    build an AI-edited timeline — all in a single background pipeline.

    This is the primary tool for cutting reels from Resolve bins.
    Monitor with ``resolve_build_status(folder_path)``.
    """
    if client is None:
        return "Error: GEMINI_API_KEY not set. This tool requires Gemini."
    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    target, dirs = _dirs_from_bin(media_pool, bin_name)
    if target is None:
        return f"Error: bin '{bin_name}' not found in the media pool."
    if not dirs:
        clips = target.GetClipList() or []
        if not clips:
            return f"Bin '{bin_name}' is empty."
        return f"Could not read file paths from bin '{bin_name}' clips."

    dir_counts: dict[str, int] = {}
    clips_list = target.GetClipList() or []
    for clip in clips_list:
        try:
            fp = clip.GetClipProperty("File Path")
            if fp:
                d = str(Path(fp).parent)
                dir_counts[d] = dir_counts.get(d, 0) + 1
        except Exception:
            continue
    root = Path(max(dir_counts, key=dir_counts.get)) if dir_counts else list(dirs.values())[0]

    key = str(root)
    progress_file = root / _RESOLVE_BUILD_PROGRESS
    if key in _active_build_workers and _active_build_workers[key].is_alive():
        prog = {}
        with contextlib.suppress(Exception):
            prog = json.loads(progress_file.read_text())
        return f"Pipeline already running for '{bin_name}': {prog.get('status', '?')} — {prog.get('detail', '?')}"

    def _pipeline():
        from .media import list_pending_audio, list_pending_videos
        from .media import load_sidecars as _load

        pending = list_pending_videos(root) + list_pending_audio(root)
        if pending:
            progress_file.write_text(
                json.dumps(
                    {
                        "status": "ingesting",
                        "detail": f"Ingesting {len(pending)} clips from bin '{bin_name}'…",
                        "error": None,
                    }
                )
            )
            _ingest_worker(root)
        sidecars = _load(root)
        if not sidecars:
            progress_file.write_text(
                json.dumps(
                    {
                        "status": "error",
                        "detail": "No sidecars after ingest — check for errors.",
                        "error": None,
                    }
                )
            )
            return
        _resolve_build_worker(root, sidecars, instruction)

    t = threading.Thread(target=_pipeline, daemon=True)
    t.start()
    _active_build_workers[key] = t

    return (
        f"Pipeline started for bin '{bin_name}' ({len(clips_list)} clips → '{root}').\n"
        f"Monitor: resolve_build_status('{root}')"
    )
