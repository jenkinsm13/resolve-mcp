"""Clip editing tools: set properties, enable/disable, color, delete, link, compound, stabilize, speed ramp."""

import json

from .config import mcp
from .resolve import _boilerplate
from .clip_query_tools import _get_item
from .resolve_transforms import _apply_speed_ramp


@mcp.tool
def resolve_set_item_properties(
    track_type: str, track_index: int, item_index: int, properties_json: str
) -> str:
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
    results = [
        f"  {k}={v}: {'OK' if item.SetProperty(k, v) else 'FAILED'}"
        for k, v in props.items()
    ]
    return "Property updates:\n" + "\n".join(results)


@mcp.tool
def resolve_set_clip_enabled(
    track_type: str, track_index: int, item_index: int, enabled: bool = True
) -> str:
    """Enable or disable a clip on the timeline."""
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    state = "enabled" if enabled else "disabled"
    return (
        f"Clip {item_index} on {track_type} track {track_index} {state}."
        if item.SetClipEnabled(enabled)
        else f"Failed to set clip {state}."
    )


@mcp.tool
def resolve_set_clip_color_on_timeline(
    track_type: str, track_index: int, item_index: int, color: str
) -> str:
    """Set the color tag of a clip on the timeline.

    Valid colors: Orange, Apricot, Yellow, Lime, Olive, Green, Teal, Navy,
    Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate.
    """
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    return (
        f"Set color '{color}' on clip {item_index}."
        if item.SetClipColor(color)
        else f"Failed to set color '{color}'."
    )


@mcp.tool
def resolve_delete_clips_from_timeline(
    track_type: str, track_index: int, item_indices: str, ripple: bool = False
) -> str:
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
def resolve_link_clips(
    track_type: str, track_index: int, item_indices: str, linked: bool = True
) -> str:
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
    return (
        f"{len(selected)} clips {action}."
        if tl.SetClipsLinked(selected, linked)
        else f"Failed to {action[:-2]} clips."
    )


@mcp.tool
def resolve_create_compound_clip(
    track_type: str, track_index: int, item_indices: str, name: str = "Compound Clip"
) -> str:
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
    return (
        f"Created compound clip '{name}' from {len(selected)} items."
        if tl.CreateCompoundClip(selected, {"name": name})
        else "Failed to create compound clip."
    )


@mcp.tool
def resolve_stabilize_clip(
    track_type: str,
    track_index: int,
    item_index: int,
    mode: str = "",
) -> str:
    """Apply stabilization to a clip on the timeline. Requires Resolve Studio.

    *mode*: optional — 'Perspective', 'Similarity', or 'Translation'. Best-effort:
    Resolve's scripting API (as of 20.3.2) does NOT expose stabilization mode,
    so the Inspector's current mode is used regardless. When a future Resolve
    build exposes the property we try SetProperty here as well so the tool
    upgrades automatically.
    """
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    mode_note = ""
    if mode:
        enum_map = {"perspective": 0, "similarity": 1, "translation": 2}
        want = enum_map.get(mode.lower())
        applied = False
        for key in ("StabilizationMethod", "StabilizationMode", "Stabilization Mode"):
            if want is not None and item.SetProperty(key, want):
                applied = True
                break
            if item.SetProperty(key, mode):
                applied = True
                break
        mode_note = f" (mode='{mode}' {'set' if applied else 'NOT SETTABLE via API — set in Inspector'})"
    return (
        f"Stabilization applied to clip {item_index}.{mode_note}"
        if item.Stabilize()
        else "Stabilization failed. Requires Resolve Studio."
    )


@mcp.tool
def resolve_smart_reframe(track_type: str, track_index: int, item_index: int) -> str:
    """Apply Smart Reframe to a clip (auto-crops for different aspect ratios). Requires Resolve Studio."""
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    return f"Smart Reframe applied to clip {item_index}." if item.SmartReframe() else "Smart Reframe failed. Requires Resolve Studio."


@mcp.tool
def resolve_speed_ramp(track_type: str, track_index: int, item_index: int,
                       speed_points_json: str) -> str:
    """Apply a speed ramp to a timeline clip via a Fusion TimeStretcher.

    Creates a Fusion composition on the clip with a TimeStretcher node
    whose SourceTime input is keyframed to produce variable speed.

    *speed_points_json*: JSON array of control points, each with:
      - ``t_sec`` (float): time in seconds from clip start
      - ``speed`` (float): playback speed at this point (1.0 = normal, 2.0 = 2× fast, 0.5 = half speed)

    Speed is linearly interpolated between control points. The last
    control point's ``t_sec`` should match the clip duration.

    Example — gradual ramp up then snap back::

        [
            {"t_sec": 0.0, "speed": 1.0},
            {"t_sec": 5.0, "speed": 8.0},
            {"t_sec": 5.5, "speed": 8.0},
            {"t_sec": 5.6, "speed": 1.0},
            {"t_sec": 6.5, "speed": 1.0}
        ]

    Warning: the clip must have enough source handle for the total source
    frames consumed. Higher speeds consume more source. Check source
    availability with resolve_get_item_properties (left/right offset).
    """
    _, project, _ = _boilerplate()
    try:
        tl, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)

    try:
        points = json.loads(speed_points_json)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON: {exc}"

    if not isinstance(points, list) or len(points) < 2:
        return "speed_points_json must be a JSON array with at least 2 control points."

    for i, pt in enumerate(points):
        if "t_sec" not in pt or "speed" not in pt:
            return f"Control point {i} missing 't_sec' or 'speed' key."
        if pt["speed"] <= 0:
            return f"Control point {i}: speed must be > 0."

    fps_str = tl.GetSetting("timelineFrameRate")
    try:
        fps = float(fps_str)
    except (TypeError, ValueError):
        return f"Could not determine timeline frame rate (got '{fps_str}')."

    if _apply_speed_ramp(item, points, fps):
        dur = item.GetDuration()
        n_pts = len(points)
        speeds = [f"{p['speed']}x@{p['t_sec']:.1f}s" for p in points]
        return (f"Speed ramp applied to clip {item_index} on {track_type} track {track_index}. "
                f"{n_pts} control points, {dur} frames at {fps}fps. "
                f"Curve: {', '.join(speeds)}")
    return ("Speed ramp failed. Possible causes: clip already has a Fusion comp "
            "that blocked creation, or TimeStretcher tool not available.")
