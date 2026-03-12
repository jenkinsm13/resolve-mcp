"""
Ingest MCP tools: ingest_footage and ingest_status.
"""

import shutil
import threading
from pathlib import Path
from typing import Optional

from .config import mcp
from .transcode import get_hw_encoder
from .media import list_all_videos, list_all_audio, list_pending_videos, list_pending_audio
from .ingest_worker import _ingest_worker, _active_workers, _write_progress, _read_progress


@mcp.tool
def ingest_footage(folder_path: str, instruction: Optional[str] = None) -> str:
    """
    Scan a folder for video and audio files and analyze them with Gemini.
    Launches a background worker that processes ALL pending files
    (transcoding via VideoToolbox on Apple Silicon, then uploading).
    Returns immediately — use ingest_status() to monitor progress.
    Files with existing .json sidecars are skipped automatically.

    If *instruction* is provided, a timeline build is automatically triggered
    once all sidecars are written — no manual follow-up needed.
    """
    root = Path(folder_path).resolve()
    if not root.is_dir():
        return f"Error: '{folder_path}' is not a valid directory."

    all_videos = list_all_videos(root)
    all_audio = list_all_audio(root)
    if not all_videos and not all_audio:
        return f"No media files found in {root}"

    pending_v = list_pending_videos(root)
    pending_a = list_pending_audio(root)
    pending = pending_v + pending_a
    total = len(all_videos) + len(all_audio)

    if not pending:
        return f"All {total} file(s) already have sidecars. Nothing to do."

    key = str(root)
    if key in _active_workers and _active_workers[key].is_alive():
        progress = _read_progress(root)
        if progress:
            return (
                f"Ingestion already running: {progress.get('current_step', '?')} "
                f"{progress.get('current_file', '?')} "
                f"({progress.get('completed', '?')}/{progress.get('total', '?')})"
            )
        return "Ingestion already running."

    if not shutil.which("ffmpeg"):
        return (
            "Error: ffmpeg not found on PATH. Install it before ingesting:\n"
            "  macOS:   brew install ffmpeg\n"
            "  Ubuntu:  sudo apt install ffmpeg\n"
            "  Windows: https://ffmpeg.org/download.html"
        )

    already_done = total - len(pending)
    _write_progress(root, {
        "status": "starting", "current_file": pending[0].name,
        "current_step": "queued", "completed": already_done,
        "total": total, "errors": [],
    })

    thread = threading.Thread(target=_ingest_worker, args=(root, instruction), daemon=True)
    thread.start()
    _active_workers[key] = thread

    hw = get_hw_encoder() or "libx265"
    parts = [f"Ingestion started for {len(pending)} file(s)"]
    if pending_v:
        parts.append(f"({len(pending_v)} video using {hw})")
    if pending_a:
        parts.append(f"({len(pending_a)} audio)")
    if already_done:
        parts.append(f"{already_done} already done.")
    parts.append(f"Use ingest_status('{folder_path}') to monitor.")
    return " ".join(parts)


@mcp.tool
def ingest_status(folder_path: str) -> str:
    """
    Check progress of a running or completed ingestion job.
    Returns current file, step (transcoding/uploading/analyzing),
    completion count, and any errors.
    """
    root = Path(folder_path).resolve()
    if not root.is_dir():
        return f"Error: '{folder_path}' is not a valid directory."

    progress = _read_progress(root)
    if progress is None:
        pending = list_pending_videos(root) + list_pending_audio(root)
        total = len(list_all_videos(root)) + len(list_all_audio(root))
        if not pending:
            return f"All {total} file(s) have sidecars. No ingestion needed."
        return f"{len(pending)} of {total} file(s) pending. Run ingest_footage to start."

    status = progress.get("status", "unknown")
    completed = progress.get("completed", 0)
    total = progress.get("total", 0)
    current = progress.get("current_file")
    step = progress.get("current_step")
    errors = progress.get("errors", [])

    if status == "complete":
        msg = f"Ingestion complete: {completed}/{total} files analyzed."
        if errors:
            msg += f"\nErrors ({len(errors)}):\n  " + "\n  ".join(errors)
        return msg

    if status == "running":
        msg = f"Ingestion running: {completed}/{total} done. Now {step} {current}."
        if errors:
            msg += f"\n{len(errors)} error(s) so far."
        return msg

    return f"Ingestion status: {status}. {completed}/{total} done."
