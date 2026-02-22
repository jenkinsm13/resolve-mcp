"""
Resolve info tools: project summary, bin listing, and item property inspector.
"""

import json

from .config import mcp
from .resolve import _boilerplate, _enumerate_bins


@mcp.tool
def resolve_get_info() -> str:
    """
    Return a JSON summary of the current DaVinci Resolve project:
    project name, timeline count, all timeline names, and a 2-level bin tree
    with clip counts.
    """
    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    tl_count = project.GetTimelineCount()
    timeline_names = []
    for i in range(1, tl_count + 1):
        tl = project.GetTimelineByIndex(i)
        if tl:
            timeline_names.append(tl.GetName())

    root = media_pool.GetRootFolder()
    bin_tree = []
    for top in [root] + list(root.GetSubFolderList() or []):
        top_clips = top.GetClipList() or []
        children = []
        for sub in top.GetSubFolderList() or []:
            sub_clips = sub.GetClipList() or []
            children.append({"name": sub.GetName(), "clip_count": len(sub_clips)})
        bin_tree.append(
            {
                "name": top.GetName(),
                "clip_count": len(top_clips),
                "subfolders": children,
            }
        )

    return json.dumps(
        {
            "project_name": project.GetName(),
            "timeline_count": tl_count,
            "timelines": timeline_names,
            "bin_tree": bin_tree,
        },
        indent=2,
    )


@mcp.tool
def resolve_list_bins() -> str:
    """
    Enumerate all bins in the current Resolve project as a formatted table
    showing ``path`` (``/``-separated) and ``clip_count``.
    """
    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    entries = _enumerate_bins(media_pool.GetRootFolder())
    lines = [f"{'Path':<60} {'Clips':>6}", "-" * 67]
    for e in entries:
        lines.append(f"{e['path']:<60} {e['clip_count']:>6}")
    return "\n".join(lines)


@mcp.tool
def resolve_inspect_item(track: int = 1, item_index: int = 0) -> str:
    """
    Diagnostic: read ALL GetProperty() keys from a TimelineItem in the active
    timeline and return them as JSON.  Useful for discovering undocumented
    property names (e.g. Dynamic Zoom start/end rectangles).

    *track* is the video track number (1-based).
    *item_index* is the 0-based index of the clip within that track.

    Set up a clip with Dynamic Zoom / camera moves in Resolve first, then call
    this tool to see which property keys and values Resolve exposes.
    """
    try:
        resolve, project, media_pool = _boilerplate()
    except ValueError as e:
        return str(e)

    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No active timeline in Resolve."

    items = timeline.GetItemListInTrack("video", track) or []
    if not items:
        return f"No items on video track {track}."
    if item_index >= len(items):
        return f"item_index {item_index} out of range ({len(items)} items on track {track})."

    item = items[item_index]

    known_keys = [
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
        "Opacity",
        "RetimeProcess",
        "MotionEstimation",
        "SteadiAnalysisType",
        "SteadiSmooth",
        "CompositeMode",
        "Speed",
        "FreezeFrame",
    ]

    props: dict = {}
    for key in known_keys:
        try:
            props[key] = item.GetProperty(key)
        except Exception as exc:
            props[key] = f"ERROR: {exc}"

    try:
        all_props = item.GetProperty()
        if isinstance(all_props, dict):
            props["__all__"] = all_props
    except Exception:
        pass

    clip_name = "unknown"
    try:
        pool_item = item.GetMediaPoolItem()
        if pool_item:
            clip_name = pool_item.GetClipProperty("Clip Name") or "unknown"
    except Exception:
        pass

    return json.dumps(
        {
            "track": track,
            "item_index": item_index,
            "clip_name": clip_name,
            "duration_frames": item.GetDuration(),
            "properties": props,
        },
        indent=2,
    )
