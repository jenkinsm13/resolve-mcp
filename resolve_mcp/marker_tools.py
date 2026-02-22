"""
Marker and playhead MCP tools.

Covers: Timeline markers (add, delete, list, update custom data),
playhead position (get/set timecode), and marker-based queries.
"""

from .config import mcp
from .resolve import _boilerplate

# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_list_markers(target: str = "timeline") -> str:
    """List all markers on the current timeline or a specific clip.

    *target*: 'timeline' (default) for timeline markers.
    Returns each marker with frame, timecode, color, name, and note.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    try:
        fps = float(tl.GetSetting("timelineFrameRate") or 24)
    except (ValueError, TypeError):
        fps = 24.0

    raw = tl.GetMarkers() or {}
    if not raw:
        return "No markers on timeline."

    lines = [f"{len(raw)} marker(s):"]
    for frame_id in sorted(raw.keys(), key=int):
        info = raw[frame_id]
        sec = int(frame_id) / fps
        color = info.get("color", "?")
        name = info.get("name", "")
        note = info.get("note", "")
        dur = info.get("duration", 1)
        custom = info.get("customData", "")
        line = f"  frame {frame_id} ({sec:.2f}s) [{color}]"
        if name:
            line += f" name='{name}'"
        if note:
            line += f" note='{note}'"
        if dur > 1:
            line += f" dur={dur}f"
        if custom:
            line += f" data='{custom}'"
        lines.append(line)
    return "\n".join(lines)


@mcp.tool
def resolve_add_marker_at(
    seconds: float, color: str = "Blue", name: str = "", note: str = "", duration: int = 1, custom_data: str = ""
) -> str:
    """Add a marker to the current timeline at a specific time.

    *seconds*: position in seconds from timeline start.
    *color*: Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia,
             Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream.
    *duration*: marker duration in frames (default 1).
    *custom_data*: optional string to attach as custom data.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    try:
        fps = float(tl.GetSetting("timelineFrameRate") or 24)
    except (ValueError, TypeError):
        fps = 24.0

    frame = round(seconds * fps)

    result = tl.AddMarker(frame, color, name, note, int(duration), custom_data)
    if result:
        return f"Marker added at {seconds:.2f}s (frame {frame}), color={color}."
    return f"Failed to add marker. A marker may already exist at frame {frame}."


@mcp.tool
def resolve_delete_markers(color: str = "All") -> str:
    """Delete markers from the current timeline by color.

    *color*: specific color name to delete only that color's markers,
    or 'All' to delete all markers.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    result = tl.DeleteMarkersByColor(color)
    if result:
        if color == "All":
            return "All markers deleted."
        return f"All '{color}' markers deleted."
    return f"Failed to delete markers (color='{color}')."


@mcp.tool
def resolve_delete_marker_at(seconds: float) -> str:
    """Delete a specific marker at the given time position.

    *seconds*: position in seconds where the marker exists.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    try:
        fps = float(tl.GetSetting("timelineFrameRate") or 24)
    except (ValueError, TypeError):
        fps = 24.0

    frame = round(seconds * fps)
    result = tl.DeleteMarkerAtFrame(frame)
    if result:
        return f"Marker deleted at frame {frame} ({seconds:.2f}s)."
    return f"No marker found at frame {frame}."


@mcp.tool
def resolve_update_marker_data(seconds: float, custom_data: str) -> str:
    """Attach or update custom data on an existing marker.

    *seconds*: position of the marker.
    *custom_data*: string data to associate with the marker.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    try:
        fps = float(tl.GetSetting("timelineFrameRate") or 24)
    except (ValueError, TypeError):
        fps = 24.0

    frame = round(seconds * fps)
    result = tl.UpdateMarkerCustomData(frame, custom_data)
    if result:
        return f"Custom data updated on marker at frame {frame}."
    return f"Failed — no marker at frame {frame} or update rejected."


@mcp.tool
def resolve_get_marker_data(seconds: float) -> str:
    """Read the custom data string from a marker at the given position."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    try:
        fps = float(tl.GetSetting("timelineFrameRate") or 24)
    except (ValueError, TypeError):
        fps = 24.0

    frame = round(seconds * fps)
    data = tl.GetMarkerCustomData(frame)
    if data:
        return f"Custom data at frame {frame}: {data}"
    return f"No custom data on marker at frame {frame}."


@mcp.tool
def resolve_get_playhead() -> str:
    """Get the current playhead position as timecode and seconds."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    tc = tl.GetCurrentTimecode()
    return f"Playhead at {tc}"


@mcp.tool
def resolve_set_playhead(timecode: str) -> str:
    """Move the playhead to a specific timecode.

    *timecode*: TC string like '01:00:05:12'.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    result = tl.SetCurrentTimecode(timecode)
    if result:
        return f"Playhead moved to {timecode}."
    return f"Failed to set playhead to '{timecode}'. Check TC format."
