"""Clip editing tools: set properties, enable/disable, color, delete, link, compound, stabilize."""

import json

from .config import mcp
from .resolve import _boilerplate
from .clip_query_tools import _get_item


@mcp.tool
def resolve_set_item_properties(track_type: str, track_index: int,
                                 item_index: int, properties_json: str) -> str:
    """Set properties on a timeline item.

    *properties_json*: JSON object with property names and values.
    Supported: Pan, Tilt, ZoomX, ZoomY, RotationAngle, AnchorPointX, AnchorPointY,
    Pitch, Yaw, FlipX, FlipY, CropLeft/Right/Top/Bottom, CropSoftness,
    CompositeMode, Opacity, RetimeProcess, MotionEstimation, Scaling, ResizeFilter.
    """
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    try:
        props = json.loads(properties_json)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON: {exc}"
    results = [f"  {k}={v}: {'OK' if item.SetProperty(k, v) else 'FAILED'}" for k, v in props.items()]
    return "Property updates:\n" + "\n".join(results)


@mcp.tool
def resolve_set_clip_enabled(track_type: str, track_index: int,
                              item_index: int, enabled: bool = True) -> str:
    """Enable or disable a clip on the timeline."""
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    state = "enabled" if enabled else "disabled"
    return f"Clip {item_index} on {track_type} track {track_index} {state}." if item.SetClipEnabled(enabled) else f"Failed to set clip {state}."


@mcp.tool
def resolve_set_clip_color_on_timeline(track_type: str, track_index: int,
                                        item_index: int, color: str) -> str:
    """Set the color tag of a clip on the timeline.

    Valid colors: Orange, Apricot, Yellow, Lime, Olive, Green, Teal, Navy,
    Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate.
    """
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    return f"Set color '{color}' on clip {item_index}." if item.SetClipColor(color) else f"Failed to set color '{color}'."


@mcp.tool
def resolve_delete_clips_from_timeline(track_type: str, track_index: int,
                                        item_indices: str, ripple: bool = False) -> str:
    """Delete clips from the timeline.

    *item_indices*: comma-separated 1-based indices (e.g. '1,3,5').
    *ripple*: if True, close the gap after deletion.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index))
    if not items:
        return f"No items on {track_type} track {track_index}."
    indices = [int(x.strip()) for x in item_indices.split(",") if x.strip()]
    to_delete = [items[i - 1] for i in indices if 1 <= i <= len(items)]
    bad_idx = [str(i) for i in indices if not (1 <= i <= len(items))]
    if not to_delete:
        return f"No valid items to delete. Bad indices: {', '.join(bad_idx)}"
    result = tl.DeleteClips(to_delete, ripple)
    msg = f"Deleted {len(to_delete)} clip(s) from {track_type} track {track_index}."
    if ripple:
        msg += " (with ripple)"
    if bad_idx:
        msg += f" Invalid indices: {', '.join(bad_idx)}."
    return ("Delete returned failure. " + msg) if not result else msg


@mcp.tool
def resolve_link_clips(track_type: str, track_index: int,
                        item_indices: str, linked: bool = True) -> str:
    """Link or unlink clips on the timeline.

    *item_indices*: comma-separated 1-based indices to link together.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index))
    if not items:
        return f"No items on {track_type} track {track_index}."
    indices = [int(x.strip()) for x in item_indices.split(",") if x.strip()]
    selected = [items[i - 1] for i in indices if 1 <= i <= len(items)]
    if len(selected) < 2:
        return "Need at least 2 valid items to link/unlink."
    action = "linked" if linked else "unlinked"
    return f"{len(selected)} clips {action}." if tl.SetClipsLinked(selected, linked) else f"Failed to {action[:-2]} clips."


@mcp.tool
def resolve_create_compound_clip(track_type: str, track_index: int,
                                  item_indices: str, name: str = "Compound Clip") -> str:
    """Create a compound clip from selected items on a track.

    *item_indices*: comma-separated 1-based indices.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index))
    if not items:
        return f"No items on {track_type} track {track_index}."
    indices = [int(x.strip()) for x in item_indices.split(",") if x.strip()]
    selected = [items[i - 1] for i in indices if 1 <= i <= len(items)]
    if not selected:
        return "No valid items selected."
    return f"Created compound clip '{name}' from {len(selected)} items." if tl.CreateCompoundClip(selected, {"name": name}) else "Failed to create compound clip."


@mcp.tool
def resolve_stabilize_clip(track_type: str, track_index: int, item_index: int) -> str:
    """Apply stabilization to a clip on the timeline. Requires Resolve Studio."""
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    return f"Stabilization applied to clip {item_index}." if item.Stabilize() else "Stabilization failed. Requires Resolve Studio."


@mcp.tool
def resolve_smart_reframe(track_type: str, track_index: int, item_index: int) -> str:
    """Apply Smart Reframe to a clip (auto-crops for different aspect ratios). Requires Resolve Studio."""
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    return f"Smart Reframe applied to clip {item_index}." if item.SmartReframe() else "Smart Reframe failed. Requires Resolve Studio."
