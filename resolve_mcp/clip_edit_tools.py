"""Clip editing tools: set properties, enable/disable, color, delete, link, compound, stabilize, append, insert, swap, fit-to-fill."""

import json
from pathlib import Path

from .clip_query_tools import _get_item
from .config import mcp
from .resolve import _boilerplate, _collect_clips_recursive
from .resolve_transforms import _apply_speed_ramp


@mcp.tool
def resolve_set_item_properties(track_type: str, track_index: int, item_index: int, properties_json: str) -> str:
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
def resolve_set_clip_enabled(track_type: str, track_index: int, item_index: int, enabled: bool = True) -> str:
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
def resolve_set_clip_color_on_timeline(track_type: str, track_index: int, item_index: int, color: str) -> str:
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
        f"Set color '{color}' on clip {item_index}." if item.SetClipColor(color) else f"Failed to set color '{color}'."
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
def resolve_link_clips(track_type: str, track_index: int, item_indices: str, linked: bool = True) -> str:
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
        f"{len(selected)} clips {action}." if tl.SetClipsLinked(selected, linked) else f"Failed to {action[:-2]} clips."
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
def resolve_stabilize_clip(track_type: str, track_index: int, item_index: int) -> str:
    """Apply stabilization to a clip on the timeline. Requires Resolve Studio."""
    _, project, _ = _boilerplate()
    try:
        _, item = _get_item(project, track_type, track_index, item_index)
    except ValueError as e:
        return str(e)
    return (
        f"Stabilization applied to clip {item_index}."
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
    return (
        f"Smart Reframe applied to clip {item_index}."
        if item.SmartReframe()
        else "Smart Reframe failed. Requires Resolve Studio."
    )


# ---------------------------------------------------------------------------
# Timeline-level clip operations
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_append_to_timeline(clip_names: str, in_out_points_json: str = "") -> str:
    """Append one or more media pool clips to the end of the current timeline.

    *clip_names*: comma-separated clip filenames or stems (e.g. 'A001.mov,B002').
    *in_out_points_json*: optional JSON array of {startFrame, endFrame} objects
        matching the clip order.  If omitted, full clips are appended.

    Returns the number of clips appended.
    """
    _, project, mp = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    pool = _collect_clips_recursive(mp.GetRootFolder())
    names = [n.strip() for n in clip_names.split(",") if n.strip()]
    if not names:
        return "No clip names provided."

    in_out: list[dict] = []
    if in_out_points_json:
        try:
            in_out = json.loads(in_out_points_json)
        except json.JSONDecodeError as exc:
            return f"Invalid in_out_points_json: {exc}"

    clip_infos: list = []
    missing: list[str] = []
    for i, name in enumerate(names):
        clip = pool.get(name) or pool.get(Path(name).stem)
        if not clip:
            missing.append(name)
            continue
        if in_out and i < len(in_out):
            clip_infos.append(
                {
                    "mediaPoolItem": clip,
                    "startFrame": in_out[i].get("startFrame", 0),
                    "endFrame": in_out[i].get("endFrame"),
                }
            )
        else:
            clip_infos.append(clip)

    if not clip_infos:
        return f"None of the clips found: {', '.join(missing)}"

    result = mp.AppendToTimeline(clip_infos)
    appended = len(result) if result else 0
    msg = f"Appended {appended} clip(s) to timeline '{tl.GetName()}'."
    if missing:
        msg += f" Not found: {', '.join(missing)}."
    return msg


@mcp.tool
def resolve_insert_clip_at_playhead(clip_name: str, track_type: str = "video", track_index: int = 1) -> str:
    """Insert a media pool clip at the current playhead position.

    Uses the timeline's Import function to place the clip at the playhead on
    the specified track.

    *clip_name*: clip filename or stem in the media pool.
    *track_type*: 'video' or 'audio' (default 'video').
    *track_index*: 1-based track number (default 1).
    """
    _, project, mp = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    pool = _collect_clips_recursive(mp.GetRootFolder())
    clip = pool.get(clip_name) or pool.get(Path(clip_name).stem)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."

    tc = tl.GetCurrentTimecode()
    clip_info = {
        "mediaPoolItem": clip,
        "mediaType": 1 if track_type.lower() == "video" else 2,
        "trackIndex": int(track_index),
    }
    result = mp.AppendToTimeline([clip_info])
    if result:
        return f"Inserted '{clip_name}' at {tc} on {track_type} track {track_index}."
    return f"Failed to insert '{clip_name}' at playhead."


@mcp.tool
def resolve_swap_clips(track_type: str, track_index: int, item_index_a: int, item_index_b: int) -> str:
    """Swap the source media of two clips on the same track.

    Uses the take selector system (conform-to-clip) to replace each item's
    source with the other's media pool clip, then finalizes the takes so the
    swap is permanent.

    *item_index_a*, *item_index_b*: 1-based clip positions within the track.

    Falls back to a property-exchange approach if either item has no
    media pool source (e.g. generators or titles).
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    items = tl.GetItemListInTrack(track_type.lower(), int(track_index))
    if not items:
        return f"No items on {track_type} track {track_index}."

    idx_a, idx_b = int(item_index_a) - 1, int(item_index_b) - 1
    if idx_a < 0 or idx_a >= len(items):
        return f"Item A index {item_index_a} out of range (1–{len(items)})."
    if idx_b < 0 or idx_b >= len(items):
        return f"Item B index {item_index_b} out of range (1–{len(items)})."
    if idx_a == idx_b:
        return "Both indices are the same — nothing to swap."

    item_a, item_b = items[idx_a], items[idx_b]

    pool_a = item_a.GetMediaPoolItem()
    pool_b = item_b.GetMediaPoolItem()
    name_a = pool_a.GetName() if pool_a else f"clip {item_index_a}"
    name_b = pool_b.GetName() if pool_b else f"clip {item_index_b}"

    # ── Takes-based swap (conform-to-clip) ──────────────────────────
    if pool_a and pool_b:
        ok_a = item_a.AddTake(pool_b)
        ok_b = item_b.AddTake(pool_a)
        if ok_a and ok_b:
            # New take is always the last one.
            count_a = item_a.GetTakesCount()
            count_b = item_b.GetTakesCount()
            item_a.SelectTakeByIndex(count_a)
            item_b.SelectTakeByIndex(count_b)
            item_a.FinalizeTake()
            item_b.FinalizeTake()
            return (
                f"Swapped source media: '{name_a}' (pos {item_index_a}) ↔ "
                f"'{name_b}' (pos {item_index_b}) via take selector."
            )
        # Partial failure — clean up any added take.
        if ok_a:
            item_a.DeleteTakeByIndex(item_a.GetTakesCount())
        if ok_b:
            item_b.DeleteTakeByIndex(item_b.GetTakesCount())
        # Fall through to property-swap fallback.

    # ── Fallback: property exchange (generators / titles) ───────────
    swap_props = ["Pan", "Tilt", "ZoomX", "ZoomY", "RotationAngle", "Opacity", "CompositeMode"]
    swapped = 0
    for prop in swap_props:
        try:
            val_a = item_a.GetProperty(prop)
            val_b = item_b.GetProperty(prop)
            if val_a is not None and val_b is not None:
                item_a.SetProperty(prop, val_b)
                item_b.SetProperty(prop, val_a)
                swapped += 1
        except Exception:
            pass

    try:
        color_a = item_a.GetClipColor()
        color_b = item_b.GetClipColor()
        if color_a:
            item_b.SetClipColor(color_a)
        if color_b:
            item_a.SetClipColor(color_b)
    except Exception:
        pass

    reason = "one or both items lack a media pool source" if not (pool_a and pool_b) else "take swap failed"
    return (
        f"Swapped properties between '{name_a}' (pos {item_index_a}) "
        f"and '{name_b}' (pos {item_index_b}). "
        f"{swapped} properties exchanged (fallback: {reason})."
    )


# ---------------------------------------------------------------------------
# Fit to Fill
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_fit_to_fill(
    clip_name: str,
    target_duration_seconds: float,
    start_frame: int = -1,
    end_frame: int = -1,
    track_type: str = "video",
    track_index: int = 1,
    retime_process: str = "OpticalFlow",
) -> str:
    """Append a clip and speed-ramp it to exactly fill a target duration (Fit to Fill).

    The clip is appended to the timeline, then a Fusion TimeStretcher is applied
    to uniformly adjust its speed so the output matches *target_duration_seconds*.

    *clip_name*: filename or stem in the media pool.
    *target_duration_seconds*: desired on-timeline duration in seconds.
    *start_frame*/*end_frame*: optional source sub-clip range (-1 = full clip).
    *track_type*: 'video' or 'audio' (default 'video').
    *track_index*: 1-based track number (default 1).
    *retime_process*: interpolation mode — 'OpticalFlow', 'FrameBlend', or
        'NearestFrame' (default OpticalFlow).
    """
    _, project, mp = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    try:
        fps = float(tl.GetSetting("timelineFrameRate") or 24)
    except (ValueError, TypeError):
        fps = 24.0

    # ── Find the clip in the media pool ─────────────────────────────
    pool = _collect_clips_recursive(mp.GetRootFolder())
    clip = pool.get(clip_name) or pool.get(Path(clip_name).stem)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."

    # ── Build clipInfo with optional sub-clip range ─────────────────
    clip_info: dict = {
        "mediaPoolItem": clip,
        "mediaType": 1 if track_type.lower() == "video" else 2,
        "trackIndex": int(track_index),
    }
    if start_frame >= 0 and end_frame >= 0:
        clip_info["startFrame"] = int(start_frame)
        clip_info["endFrame"] = int(end_frame)

    # ── Append the clip ─────────────────────────────────────────────
    result = mp.AppendToTimeline([clip_info])
    if not result:
        return f"Failed to append '{clip_name}' to timeline."

    # ── Locate the new timeline item (last item on the track) ───────
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index))
    if not items:
        return "Clip appended but could not locate it on the track."
    new_item = items[-1]

    # ── Calculate speed ratio ───────────────────────────────────────
    src_dur = new_item.GetDuration()
    target_frames = round(target_duration_seconds * fps)
    if target_frames <= 0:
        return "Target duration must be positive."
    if src_dur <= 0:
        return "Source clip has zero duration."

    speed_ratio = src_dur / target_frames  # >1 = speed up, <1 = slow down
    speed_pct = speed_ratio * 100

    # ── Apply uniform speed via Fusion TimeStretcher ────────────────
    ramp_points = [
        {"t_sec": 0.0, "speed": speed_ratio},
        {"t_sec": target_duration_seconds, "speed": speed_ratio},
    ]
    ok = _apply_speed_ramp(new_item, ramp_points, fps)

    # Set retime interpolation mode.
    new_item.SetProperty("RetimeProcess", retime_process)

    clip_display = clip.GetName() if hasattr(clip, "GetName") else clip_name
    if ok:
        return (
            f"Fit-to-fill: '{clip_display}' → {target_duration_seconds:.2f}s "
            f"at {speed_pct:.1f}% speed ({retime_process}). "
            f"Source: {src_dur} frames, target: {target_frames} frames."
        )
    return (
        f"Appended '{clip_display}' but speed ramp failed. "
        f"Clip is at native speed. Manually set speed to {speed_pct:.1f}%."
    )
