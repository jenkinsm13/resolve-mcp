"""
MCP Resources — passive, read-only data exposed without tool invocations.

Resources let the LLM inspect project state cheaply (no round-trip tool
call required).  FastMCP exposes these via the ``resource://`` URI scheme.

Registered resources:
  resolve://project     — current project name, settings, timeline count
  resolve://timelines   — all timelines with track counts and durations
  resolve://bins        — full media pool bin tree with clip counts
  resolve://render-queue — render job list with statuses
  resolve://version     — Resolve version and edition (Free vs Studio)
"""

import contextlib
import json

from .config import mcp
from .resolve import _boilerplate, _enumerate_bins, get_resolve, is_studio


@mcp.resource("resolve://version")
def resource_version() -> str:
    """Resolve version string and edition (Free vs Studio)."""
    resolve = get_resolve()
    if not resolve:
        return json.dumps({"error": "DaVinci Resolve is not running."})
    ver = "unknown"
    with contextlib.suppress(AttributeError, TypeError):
        ver = resolve.GetVersionString() or ver
    return json.dumps(
        {
            "version": ver,
            "studio": is_studio(),
            "page": resolve.GetCurrentPage() or "unknown",
        },
        indent=2,
    )


@mcp.resource("resolve://project")
def resource_project() -> str:
    """Current project name, key settings, and timeline count."""
    try:
        resolve, project, mp = _boilerplate()
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    settings = {}
    for key in (
        "timelineFrameRate",
        "timelineResolutionWidth",
        "timelineResolutionHeight",
        "videoBitDepth",
        "videoMonitorFormat",
        "timelinePlaybackFrameRate",
    ):
        try:
            val = project.GetSetting(key)
            if val is not None:
                settings[key] = val
        except Exception:
            pass
    tl_count = project.GetTimelineCount() or 0
    current_tl = project.GetCurrentTimeline()
    return json.dumps(
        {
            "name": project.GetName(),
            "timeline_count": tl_count,
            "current_timeline": current_tl.GetName() if current_tl else None,
            "settings": settings,
        },
        indent=2,
    )


@mcp.resource("resolve://timelines")
def resource_timelines() -> str:
    """All timelines in the current project with basic metadata."""
    try:
        _, project, _ = _boilerplate()
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    count = project.GetTimelineCount() or 0
    timelines = []
    for i in range(1, count + 1):
        tl = project.GetTimelineByIndex(i)
        if not tl:
            continue
        info = {
            "name": tl.GetName(),
            "video_tracks": tl.GetTrackCount("video") or 0,
            "audio_tracks": tl.GetTrackCount("audio") or 0,
            "subtitle_tracks": tl.GetTrackCount("subtitle") or 0,
        }
        # Duration as timecode string
        try:
            start = tl.GetStartTimecode() or "00:00:00:00"
            end = tl.GetEndTimecode() or "00:00:00:00"
            info["start_tc"] = start
            info["end_tc"] = end
        except Exception:
            pass
        timelines.append(info)
    return json.dumps(timelines, indent=2)


@mcp.resource("resolve://bins")
def resource_bins() -> str:
    """Full media pool bin tree with clip counts per bin."""
    try:
        _, _, mp = _boilerplate()
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    root = mp.GetRootFolder()
    bins = _enumerate_bins(root)
    return json.dumps(bins, indent=2)


@mcp.resource("resolve://render-queue")
def resource_render_queue() -> str:
    """Render job queue with statuses."""
    try:
        _, project, _ = _boilerplate()
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    jobs = project.GetRenderJobList() or []
    result = []
    for job in jobs:
        entry = {}
        for k in ("JobId", "TimelineName", "TargetDir", "OutputFilename", "RenderStatus", "CompletionPercentage"):
            if k in job:
                entry[k] = job[k]
        result.append(entry)
    return json.dumps(result, indent=2)
