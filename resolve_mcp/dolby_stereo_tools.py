"""
Dolby Vision and 3D Stereo tools — niche but essential for
HDR mastering and stereoscopic 3D workflows.

For a colorist/finishing artist: Dolby Vision analysis and optimization
are required for DV deliverables (Netflix, Disney+, Apple TV+).
Stereo tools handle 3D convergence and floating windows.
"""

import json

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate

# ---------------------------------------------------------------------------
# Dolby Vision
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_analyze_dolby_vision(timeline_name: str = "") -> str:
    """Analyze the current timeline for Dolby Vision compatibility.

    Scans the grade and generates L1/L2/L5 metadata. Required before
    exporting Dolby Vision masters.

    Requires Resolve Studio with Dolby Vision license.

    Args:
        timeline_name (str): Optional timeline name for identification. Defaults to "".
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    r = tl.AnalyzeDolbyVision()
    return "Dolby Vision analysis started." if r else "Failed — requires Resolve Studio with Dolby Vision."


@mcp.tool
@safe_resolve_call
def resolve_optimize_dolby_vision() -> str:
    """Optimize the current timeline for Dolby Vision delivery.

    Runs after AnalyzeDolbyVision to refine metadata and ensure
    spec compliance for streaming/theatrical delivery.

    Args: None
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    r = tl.OptimizeDolbyVision()
    return "Dolby Vision optimization complete." if r else "Failed — run analyze first."


# ---------------------------------------------------------------------------
# 3D Stereo
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_convert_timeline_to_stereo() -> str:
    """Convert the current timeline to a stereo 3D timeline.

    Sets up left/right eye tracks for stereoscopic workflows.

    Args: None
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    r = tl.ConvertTimelineToStereo()
    return "Timeline converted to stereo." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_get_stereo_floating_windows(track_type: str, track_index: int, item_index: int) -> str:
    """Get stereo floating window parameters for a 3D clip.

    Returns left and right eye floating window params used to
    control 3D depth perception at frame edges.

    Args:
        track_type (str): Track type ('video' or 'audio').
        track_index (int): Track index (1-based).
        item_index (int): Clip index (1-based).
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index)) or []
    idx = int(item_index) - 1
    if idx < 0 or idx >= len(items):
        return "Item index out of range."
    it = items[idx]
    left = it.GetStereoLeftFloatingWindowParams()
    right = it.GetStereoRightFloatingWindowParams()
    return json.dumps({"left": left, "right": right}, indent=2, default=str)
