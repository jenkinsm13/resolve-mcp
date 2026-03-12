"""Timeline query and management tools: list, info, switch, duplicate, delete, settings."""

import json

from .config import mcp
from .resolve import _boilerplate


def _get_timeline_by_name(project, name: str):
    """Find a timeline by name. Returns the timeline object or None."""
    for i in range(1, project.GetTimelineCount() + 1):
        tl = project.GetTimelineByIndex(i)
        if tl and tl.GetName() == name:
            return tl
    return None


@mcp.tool
def resolve_list_timelines() -> str:
    """List all timelines in the current project with basic info.

    Returns name, duration, track counts, and frame rate for each timeline.
    """
    _, project, _ = _boilerplate()
    count = project.GetTimelineCount()
    if count == 0:
        return "No timelines in current project."

    lines = [f"{count} timeline(s):"]
    for i in range(1, count + 1):
        tl = project.GetTimelineByIndex(i)
        if not tl:
            continue
        fps = tl.GetSetting("timelineFrameRate") or "?"
        v_tracks = tl.GetTrackCount("video") or 0
        a_tracks = tl.GetTrackCount("audio") or 0
        start_tc = tl.GetStartTimecode() or "?"
        lines.append(f"  {i}. {tl.GetName()} — {fps}fps, V{v_tracks}/A{a_tracks}, start TC {start_tc}")
    return "\n".join(lines)


@mcp.tool
def resolve_get_timeline_info(timeline_name: str = "") -> str:
    """Get detailed info about a timeline (tracks, fps, resolution, clip counts).

    If *timeline_name* is omitted, uses the current active timeline.
    """
    _, project, _ = _boilerplate()
    tl = _get_timeline_by_name(project, timeline_name) if timeline_name else project.GetCurrentTimeline()
    if not tl:
        return f"Timeline '{timeline_name}' not found." if timeline_name else "No active timeline."

    v_tracks = tl.GetTrackCount("video") or 0
    a_tracks = tl.GetTrackCount("audio") or 0
    s_tracks = tl.GetTrackCount("subtitle") or 0

    track_details = []
    for track_type, count in [("video", v_tracks), ("audio", a_tracks), ("subtitle", s_tracks)]:
        for idx in range(1, count + 1):
            items = tl.GetItemListInTrack(track_type, idx) or []
            track_details.append({
                "type": track_type,
                "index": idx,
                "name": tl.GetTrackName(track_type, idx) or "",
                "clip_count": len(items),
                "enabled": bool(tl.GetIsTrackEnabled(track_type, idx)),
                "locked": bool(tl.GetIsTrackLocked(track_type, idx)),
            })

    return json.dumps({
        "name": tl.GetName(),
        "start_timecode": tl.GetStartTimecode(),
        "frame_rate": tl.GetSetting("timelineFrameRate"),
        "video_tracks": v_tracks,
        "audio_tracks": a_tracks,
        "subtitle_tracks": s_tracks,
        "tracks": track_details,
    }, indent=2)


@mcp.tool
def resolve_set_current_timeline(timeline_name: str) -> str:
    """Switch the active timeline by name."""
    _, project, _ = _boilerplate()
    tl = _get_timeline_by_name(project, timeline_name)
    if not tl:
        return f"Timeline '{timeline_name}' not found."
    return f"Switched to timeline '{timeline_name}'." if project.SetCurrentTimeline(tl) else f"Failed to switch to '{timeline_name}'."


@mcp.tool
def resolve_duplicate_timeline(new_name: str = "") -> str:
    """Duplicate the current active timeline.

    If *new_name* is omitted, Resolve auto-generates a name.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline to duplicate."
    dup = tl.DuplicateTimeline(new_name) if new_name else tl.DuplicateTimeline()
    return f"Duplicated timeline → '{dup.GetName()}'." if dup else "Failed to duplicate timeline."


@mcp.tool
def resolve_delete_timelines(timeline_names: str) -> str:
    """Delete one or more timelines by name (comma-separated).

    WARNING: This permanently removes the timelines.
    """
    _, project, media_pool = _boilerplate()
    names = [n.strip() for n in timeline_names.split(",") if n.strip()]
    timelines, missing = [], []
    for name in names:
        tl = _get_timeline_by_name(project, name)
        (timelines if tl else missing).append(tl or name)
    if not timelines:
        return f"No matching timelines found. Missing: {', '.join(missing)}"
    result = media_pool.DeleteTimelines(timelines)
    msg = f"Deleted {len(timelines)} timeline(s)."
    if missing:
        msg += f" Not found: {', '.join(missing)}."
    return ("Delete returned failure. " + msg) if not result else msg


@mcp.tool
def resolve_get_timeline_settings() -> str:
    """Get all settings for the current timeline as JSON."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    settings = tl.GetSetting() or {}
    return json.dumps(settings, indent=2) if isinstance(settings, dict) else str(settings)


@mcp.tool
def resolve_set_timeline_setting(setting_name: str, value: str) -> str:
    """Set a specific timeline setting.

    Common settings: timelineFrameRate, timelineResolutionWidth, timelineResolutionHeight.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    return f"Timeline setting {setting_name} = {value}" if tl.SetSetting(setting_name, value) else f"Failed to set timeline setting '{setting_name}'."


@mcp.tool
def resolve_set_timeline_start_timecode(timecode: str) -> str:
    """Set the start timecode for the current timeline (e.g. '01:00:00:00')."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    return f"Timeline start TC set to {timecode}." if tl.SetStartTimecode(timecode) else f"Failed to set start TC to '{timecode}'."
