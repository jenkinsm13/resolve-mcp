"""
TimelineItem-level markers and flags.

Separate from timeline markers (marker_tools.py) — these operate on
individual clips on the timeline, not the timeline itself.
"""

import json

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate


def _item(project, track_type, track_index, item_index):
    tl = project.GetCurrentTimeline()
    if not tl:
        raise ValueError("No active timeline.")
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index)) or []
    idx = int(item_index) - 1
    if idx < 0 or idx >= len(items):
        raise ValueError(f"Item index {item_index} out of range (1–{len(items)}).")
    return items[idx]


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_item_add_marker(
    track_type: str,
    track_index: int,
    item_index: int,
    frame: int,
    color: str = "Blue",
    name: str = "",
    note: str = "",
    duration: int = 1,
    custom_data: str = "",
) -> str:
    """Add a marker to a timeline item at a frame offset within the clip.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        frame: Frame offset from item start (0-based).
        color: Marker color. Valid: Blue, Cyan, Green, Yellow, Red, Pink,
            Purple, Fuchsia, Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream.
        name: Short marker title.
        note: Longer marker description.
        duration: Marker duration in frames (default 1).
        custom_data: Arbitrary string stored with the marker.

    See also: resolve_item_get_markers, resolve_item_delete_markers
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.AddMarker(frame, color, name, note, duration, custom_data)
    return f"Marker added at frame {frame}." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_get_markers(track_type: str, track_index: int, item_index: int) -> str:
    """List all markers on a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_item_add_marker, resolve_item_delete_markers
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    markers = it.GetMarkers() or {}
    if not markers:
        return "No markers on this item."
    lines = [f"{len(markers)} marker(s):"]
    for fid in sorted(markers.keys(), key=int):
        info = markers[fid]
        lines.append(f"  frame {fid} [{info.get('color', '')}] {info.get('name', '')}")
    return "\n".join(lines)


@mcp.tool
@safe_resolve_call
def resolve_item_delete_markers(track_type: str, track_index: int, item_index: int, color: str = "All") -> str:
    """Delete markers on a timeline item by color.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        color: Marker color to delete, or 'All' to delete all markers.

    See also: resolve_item_add_marker, resolve_item_get_markers
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.DeleteMarkersByColor(color)
    return f"Deleted '{color}' markers." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_delete_marker_at(track_type: str, track_index: int, item_index: int, frame: int) -> str:
    """Delete a specific marker on a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        frame: Frame offset of the marker to delete.

    See also: resolve_item_delete_markers, resolve_item_get_markers
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.DeleteMarkerAtFrame(frame)
    return f"Marker deleted at frame {frame}." if r else "No marker at that frame."


@mcp.tool
@safe_resolve_call
def resolve_item_find_marker(track_type: str, track_index: int, item_index: int, custom_data: str) -> str:
    """Find a marker on a timeline item by custom data.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        custom_data: Custom data string to search for.

    See also: resolve_item_get_markers, resolve_item_add_marker
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.GetMarkerByCustomData(custom_data)
    return json.dumps(r, indent=2, default=str) if r else "No match."


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_item_add_flag(track_type: str, track_index: int, item_index: int, color: str) -> str:
    """Add a flag to a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        color: Flag color. Valid: Orange, Apricot, Yellow, Lime, Olive, Green,
            Teal, Navy, Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate.

    See also: resolve_item_get_flags, resolve_item_clear_flags
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.AddFlag(color)
    return f"Flag '{color}' added." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_get_flags(track_type: str, track_index: int, item_index: int) -> str:
    """List all flags on a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_item_add_flag, resolve_item_clear_flags
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    flags = it.GetFlagList() or []
    return ", ".join(flags) if flags else "No flags."


@mcp.tool
@safe_resolve_call
def resolve_item_clear_flags(track_type: str, track_index: int, item_index: int) -> str:
    """Clear all flags from a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_item_add_flag, resolve_item_get_flags
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.ClearFlags()
    return "Flags cleared." if r else "Failed."


# ---------------------------------------------------------------------------
# Source info & IDs
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_item_get_source_timecodes(track_type: str, track_index: int, item_index: int) -> str:
    """Get source start/end timecodes and frames for a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_item_get_id
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    return (
        f"Source start: {it.GetSourceStartTimecode()} (frame {it.GetSourceStartFrame()})\n"
        f"Source end:   {it.GetSourceEndTimecode()} (frame {it.GetSourceEndFrame()})"
    )


@mcp.tool
@safe_resolve_call
def resolve_item_get_id(track_type: str, track_index: int, item_index: int) -> str:
    """Get the unique ID of a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_clip_get_id, resolve_item_get_source_timecodes
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    uid = it.GetUniqueId()
    return f"Item unique ID: {uid}" if uid else "Could not retrieve."
