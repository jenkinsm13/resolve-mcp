"""
Resolve ingest tools: scan bins for clip paths and launch ingest workers.
"""

import threading
from pathlib import Path

from .config import mcp
from .resolve import _boilerplate, _find_bin
from .ingest import _ingest_worker, _active_workers


def _dirs_from_bin(media_pool, bin_name: str) -> tuple:
    """Return ``(bin_obj, {str_path: Path})`` for all clips in *bin_name*.

    Reads ``File Path`` properties directly from Resolve — no disk scanning.
    Returns ``(None, {})`` if the bin isn't found or is empty.
    """
    target = _find_bin(media_pool.GetRootFolder(), bin_name)
    if target is None:
        return None, {}
    clips = target.GetClipList() or []
    dirs: dict[str, Path] = {}
    for clip in clips:
        try:
            fp = clip.GetClipProperty("File Path")
            if fp:
                p = Path(fp)
                dirs[str(p.parent)] = p.parent
        except Exception:
            continue
    return target, dirs


@mcp.tool
def resolve_ingest_bin(bin_name: str) -> str:
    """
    Find *bin_name* in the current Resolve project, collect all clip file
    paths from it, and launch the ingest worker for each distinct parent
    directory.  Returns the folder paths to poll with ``ingest_status()``.

    Accepts a plain bin name (depth-first search) or a ``/``-separated path.
    """
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
            return f"Bin '{bin_name}' is empty — nothing to ingest."
        return f"Could not determine file paths for clips in '{bin_name}'."

    started = []
    for dir_str, dir_path in dirs.items():
        key = str(dir_path)
        if key in _active_workers and _active_workers[key].is_alive():
            started.append(f"Already running: {dir_str}")
            continue
        t = threading.Thread(target=_ingest_worker, args=(dir_path,), daemon=True)
        t.start()
        _active_workers[key] = t
        started.append(dir_str)

    paths = "\n".join(f"  ingest_status('{p}')" for p in dirs)
    return (
        f"Ingest started for {len(dirs)} folder(s) from bin '{bin_name}'.\n"
        f"Monitor with:\n{paths}\n"
        f"Details: {'; '.join(started)}"
    )
