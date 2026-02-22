"""Clip query tools: list clips on track, get item properties and source info."""

import json

from .config import mcp
from .resolve import _boilerplate


def _get_item(project, track_type: str, track_index: int, item_index: int):
    """Return (timeline, item) or raise ValueError."""
    tl = project.GetCurrentTimeline()
    if not tl:
        raise ValueError("No active timeline.")
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index))
    if not items:
        raise ValueError(f"No items on {track_type} track {track_index}.")
    idx = int(item_index) - 1
    if idx < 0 or idx >= len(items):
        raise ValueError(f"Item index {item_index} out of range (1–{len(items)}).")
    return tl, items[idx]


@mcp.tool
def resolve_list_clips_on_track(track_type: str, track_index: int) -> str:
    """List all clips/items on a specific track of the current timeline.

    *track_type*: 'video', 'audio', or 'subtitle'.
    *track_index*: 1-based track number.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index))
    if not items:
        return f"No items on {track_type} track {track_index}."

    lines = [f"{len(items)} item(s) on {track_type} track {track_index}:"]
    for i, item in enumerate(items, 1):
        pool_item = item.GetMediaPoolItem()
        src_name = pool_item.GetName() if pool_item else "—"
        lines.append(
            f"  {i}. [{item.GetStart()}→{item.GetEnd()}] dur={item.GetDuration()} "
            f"name='{item.GetName() or '?'}' src='{src_name}'"
        )
    return "\n".join(lines)


@mcp.tool
def resolve_get_item_properties(track_type: str, track_index: int, item_index: int) -> str:
    """Get all properties of a timeline item (transform, composite, crop, etc.).

    *item_index*: 1-based position within the track.
    """
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)

    property_names = [
        "Pan",
        "Tilt",
        "ZoomX",
        "ZoomY",
        "ZoomGang",
        "RotationAngle",
        "AnchorPointX",
        "AnchorPointY",
        "Pitch",
        "Yaw",
        "FlipX",
        "FlipY",
        "CropLeft",
        "CropRight",
        "CropTop",
        "CropBottom",
        "CropSoftness",
        "CropRetain",
        "DynamicZoomEase",
        "CompositeMode",
        "Opacity",
        "Distortion",
        "LenCorrection",
        "LenDistortionType",
        "RetimeProcess",
        "MotionEstimation",
        "Scaling",
        "ResizeFilter",
    ]
    props = {}
    for name in property_names:
        try:
            val = item.GetProperty(name)
            if val is not None:
                props[name] = val
        except Exception:
            pass

    props["_name"] = item.GetName()
    props["_start"] = item.GetStart()
    props["_end"] = item.GetEnd()
    props["_duration"] = item.GetDuration()
    props["_left_offset"] = item.GetLeftOffset()
    props["_right_offset"] = item.GetRightOffset()
    return json.dumps(props, indent=2, default=str)


@mcp.tool
def resolve_get_clip_source_info(track_type: str, track_index: int, item_index: int) -> str:
    """Get source file info for a clip on the timeline.

    Returns media pool item name, file path, in/out points, and offsets.
    """
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)

    pool_item = item.GetMediaPoolItem()
    info = {
        "timeline_name": item.GetName(),
        "start": item.GetStart(),
        "end": item.GetEnd(),
        "duration": item.GetDuration(),
        "left_offset": item.GetLeftOffset(),
        "right_offset": item.GetRightOffset(),
        "source_name": pool_item.GetName() if pool_item else None,
        "source_path": pool_item.GetClipProperty("File Path") if pool_item else None,
        "source_fps": pool_item.GetClipProperty("FPS") if pool_item else None,
        "source_resolution": pool_item.GetClipProperty("Resolution") if pool_item else None,
    }
    return json.dumps(info, indent=2, default=str)
