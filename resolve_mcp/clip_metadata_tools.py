"""
MediaPoolItem extras — clip-level markers, flags, proxy media,
transcription, replace, and unique IDs.
"""

import json
from pathlib import Path

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate, _collect_clips_recursive


def _clip(media_pool, name: str):
    pool = _collect_clips_recursive(media_pool.GetRootFolder())
    return pool.get(name) or pool.get(Path(name).stem)


# ---------------------------------------------------------------------------
# Markers on MediaPoolItem
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_clip_add_marker(
    clip_name: str,
    frame: int,
    color: str = "Blue",
    name: str = "",
    note: str = "",
    duration: int = 1,
    custom_data: str = "",
) -> str:
    """Add a marker to a media pool clip at the given frame offset.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        frame: Frame offset from clip start (0-based).
        color: Marker color. Valid: Blue, Cyan, Green, Yellow, Red, Pink,
            Purple, Fuchsia, Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream.
        name: Short marker title.
        note: Longer marker description.
        duration: Marker duration in frames (default 1).
        custom_data: Arbitrary string stored with the marker.

    See also: resolve_clip_get_markers, resolve_clip_delete_markers
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.AddMarker(frame, color, name, note, duration, custom_data)
    return f"Marker added at frame {frame}." if r else "Failed — marker may exist at that frame."


@mcp.tool
@safe_resolve_call
def resolve_clip_get_markers(clip_name: str) -> str:
    """List all markers on a media pool clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.

    See also: resolve_clip_add_marker, resolve_clip_delete_markers
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    markers = c.GetMarkers() or {}
    if not markers:
        return "No markers."
    lines = [f"{len(markers)} marker(s):"]
    for frame_id in sorted(markers.keys(), key=int):
        info = markers[frame_id]
        lines.append(f"  frame {frame_id} [{info.get('color', '')}] {info.get('name', '')}")
    return "\n".join(lines)


@mcp.tool
@safe_resolve_call
def resolve_clip_delete_markers(clip_name: str, color: str = "All") -> str:
    """Delete markers on a media pool clip by color (or 'All').

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        color: Marker color to delete, or 'All' to delete all markers.

    See also: resolve_clip_add_marker, resolve_clip_get_markers
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.DeleteMarkersByColor(color)
    return f"Deleted '{color}' markers." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_clip_delete_marker_at(clip_name: str, frame: int) -> str:
    """Delete a specific marker on a media pool clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        frame: Frame offset of the marker to delete.

    See also: resolve_clip_delete_markers, resolve_clip_get_markers
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.DeleteMarkerAtFrame(frame)
    return f"Marker deleted at frame {frame}." if r else "No marker at that frame."


@mcp.tool
@safe_resolve_call
def resolve_clip_update_marker_data(clip_name: str, frame: int, custom_data: str) -> str:
    """Update custom data on a clip marker.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        frame: Frame offset of the marker to update.
        custom_data: New custom data string to store with the marker.

    See also: resolve_clip_get_marker_data, resolve_clip_find_marker
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.UpdateMarkerCustomData(frame, custom_data)
    return "Updated." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_clip_get_marker_data(clip_name: str, frame: int) -> str:
    """Read custom data from a clip marker.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        frame: Frame offset of the marker to read.

    See also: resolve_clip_update_marker_data, resolve_clip_find_marker
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    d = c.GetMarkerCustomData(frame)
    return d if d else "No custom data."


@mcp.tool
@safe_resolve_call
def resolve_clip_find_marker(clip_name: str, custom_data: str) -> str:
    """Find a marker on a clip by its custom data string.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        custom_data: Custom data string to search for.

    See also: resolve_clip_get_marker_data, resolve_clip_update_marker_data
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.GetMarkerByCustomData(custom_data)
    return json.dumps(r, indent=2, default=str) if r else "No match."


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_clip_add_flag(clip_name: str, color: str) -> str:
    """Add a flag to a media pool clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        color: Flag color. Valid: Orange, Apricot, Yellow, Lime, Olive, Green,
            Teal, Navy, Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate.

    See also: resolve_clip_get_flags, resolve_clip_clear_flags
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.AddFlag(color)
    return f"Flag '{color}' added." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_clip_get_flags(clip_name: str) -> str:
    """List all flags on a media pool clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.

    See also: resolve_clip_add_flag, resolve_clip_clear_flags
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    flags = c.GetFlagList() or []
    return ", ".join(flags) if flags else "No flags."


@mcp.tool
@safe_resolve_call
def resolve_clip_clear_flags(clip_name: str) -> str:
    """Clear all flags from a media pool clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.

    See also: resolve_clip_add_flag, resolve_clip_get_flags
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.ClearFlags()
    return "Flags cleared." if r else "Failed."


# ---------------------------------------------------------------------------
# Proxy, replace, transcription, IDs
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_clip_link_proxy(clip_name: str, proxy_path: str) -> str:
    """Link proxy media to a clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        proxy_path: File path to the proxy media file.

    See also: resolve_clip_unlink_proxy
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.LinkProxyMedia(proxy_path)
    return "Proxy linked." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_clip_unlink_proxy(clip_name: str) -> str:
    """Unlink proxy media from a clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.

    See also: resolve_clip_link_proxy
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.UnlinkProxyMedia()
    return "Proxy unlinked." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_clip_replace(clip_name: str, new_file_path: str) -> str:
    """Replace a clip's source media with a different file.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.
        new_file_path: File path to the replacement media file.

    See also: resolve_clip_link_proxy
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.ReplaceClip(new_file_path)
    return f"Replaced with {new_file_path}" if r else "Replace failed."


@mcp.tool
@safe_resolve_call
def resolve_clip_transcribe(clip_name: str) -> str:
    """Start audio transcription on a media pool clip. Requires Studio.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.

    See also: resolve_clip_clear_transcription
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.TranscribeAudio()
    return "Transcription started." if r else "Failed — requires Resolve Studio."


@mcp.tool
@safe_resolve_call
def resolve_clip_clear_transcription(clip_name: str) -> str:
    """Clear transcription data from a media pool clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.

    See also: resolve_clip_transcribe
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    r = c.ClearTranscription()
    return "Transcription cleared." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_clip_get_id(clip_name: str) -> str:
    """Get the unique ID and media ID of a clip.

    Args:
        clip_name: Clip filename or stem (without extension) in the media pool.

    See also: resolve_item_get_id
    """
    _, _, mp = _boilerplate()
    c = _clip(mp, clip_name)
    if not c:
        return f"Clip '{clip_name}' not found."
    uid = c.GetUniqueId() or "?"
    mid = c.GetMediaId() or "?"
    return f"UniqueId={uid}  MediaId={mid}"
