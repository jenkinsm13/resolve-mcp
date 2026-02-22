"""Media pool query tools: search clips, get clip info."""

import json
from pathlib import Path

from .config import mcp
from .resolve import _boilerplate, _collect_clips_recursive, _find_bin


def _resolve_clip(media_pool, clip_name: str):
    """Find a clip in the media pool by name (stem or full filename)."""
    pool_clips = _collect_clips_recursive(media_pool.GetRootFolder())
    return pool_clips.get(clip_name) or pool_clips.get(Path(clip_name).stem)


def _resolve_clips(media_pool, clip_names: list) -> tuple:
    """Resolve multiple clip names to clip objects. Returns (found, missing)."""
    pool_clips = _collect_clips_recursive(media_pool.GetRootFolder())
    found, missing = [], []
    for name in clip_names:
        clip = pool_clips.get(name) or pool_clips.get(Path(name).stem)
        (found if clip else missing).append(clip or name)
    return found, missing


@mcp.tool
def resolve_search_clips(query: str, search_in: str = "") -> str:
    """Search for clips in the media pool by name substring (case-insensitive).

    *search_in* optionally limits search to a specific bin. Returns up to 50 matches.
    """
    _, _, media_pool = _boilerplate()
    if search_in:
        folder = _find_bin(media_pool.GetRootFolder(), search_in)
        if not folder:
            return f"Bin '{search_in}' not found."
    else:
        folder = media_pool.GetRootFolder()

    query_lower = query.lower()
    matches, seen = [], set()
    for name in _collect_clips_recursive(folder):
        if query_lower in name.lower() and name not in seen:
            seen.add(name)
            matches.append(name)
            if len(matches) >= 50:
                break

    return (
        f"{len(matches)} match(es):\n" + "\n".join(f"  • {m}" for m in matches)
        if matches
        else f"No clips matching '{query}' found."
    )


@mcp.tool
def resolve_get_clip_info(clip_name: str) -> str:
    """Get all properties and metadata for a media pool clip.

    Returns clip properties (resolution, fps, codec, duration, etc.) and user-set metadata.
    """
    _, _, media_pool = _boilerplate()
    clip = _resolve_clip(media_pool, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."
    return json.dumps(
        {
            "name": clip.GetName(),
            "properties": clip.GetClipProperty() or {},
            "metadata": clip.GetMetadata() or {},
        },
        indent=2,
        default=str,
    )
