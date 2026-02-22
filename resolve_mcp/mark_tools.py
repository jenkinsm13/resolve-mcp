"""
Mark In/Out MCP tools.

Covers: Setting, getting, and clearing mark in/out points on timelines,
timeline items, and media pool items. These control the active range for
rendering, playback, and editing operations.
"""

from .config import mcp
from .resolve import _boilerplate


# ---------------------------------------------------------------------------
# Timeline Mark In/Out
# ---------------------------------------------------------------------------

@mcp.tool
def resolve_get_timeline_mark_in_out() -> str:
    """Get the current mark in/out points on the timeline.

    Returns video and audio in/out frame numbers.
    Used to define render range or playback range.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    marks = tl.GetMarkInOut()
    if not marks:
        return "No marks set on timeline."

    parts = []
    if "video" in marks:
        v = marks["video"]
        parts.append(f"Video: in={v.get('in', '?')}, out={v.get('out', '?')}")
    if "audio" in marks:
        a = marks["audio"]
        parts.append(f"Audio: in={a.get('in', '?')}, out={a.get('out', '?')}")
    return "Timeline marks — " + "; ".join(parts) if parts else "No marks set."


@mcp.tool
def resolve_set_timeline_mark_in_out(mark_in: int, mark_out: int,
                                       mark_type: str = "all") -> str:
    """Set mark in/out points on the timeline.

    *mark_in*: frame number for mark in.
    *mark_out*: frame number for mark out.
    *mark_type*: 'video', 'audio', or 'all' (default).

    Defines the active range for rendering and export.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    result = tl.SetMarkInOut(int(mark_in), int(mark_out), mark_type)
    if result:
        return f"Timeline mark set: in={mark_in}, out={mark_out} ({mark_type})."
    return "Failed to set timeline marks."


@mcp.tool
def resolve_clear_timeline_mark_in_out(mark_type: str = "all") -> str:
    """Clear mark in/out points on the timeline.

    *mark_type*: 'video', 'audio', or 'all' (default).
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    result = tl.ClearMarkInOut(mark_type)
    if result:
        return f"Timeline marks cleared ({mark_type})."
    return "Failed to clear timeline marks."


# ---------------------------------------------------------------------------
# Media Pool Item Mark In/Out
# ---------------------------------------------------------------------------

@mcp.tool
def resolve_get_clip_mark_in_out(clip_name: str) -> str:
    """Get mark in/out points on a media pool clip.

    *clip_name*: name of the clip in the media pool.
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp.GetRootFolder(), clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."

    marks = clip.GetMarkInOut()
    if not marks:
        return f"No marks set on '{clip_name}'."

    parts = []
    if "video" in marks:
        v = marks["video"]
        parts.append(f"Video: in={v.get('in', '?')}, out={v.get('out', '?')}")
    if "audio" in marks:
        a = marks["audio"]
        parts.append(f"Audio: in={a.get('in', '?')}, out={a.get('out', '?')}")
    return f"Marks on '{clip_name}' — " + "; ".join(parts) if parts else "No marks set."


@mcp.tool
def resolve_set_clip_mark_in_out(clip_name: str, mark_in: int, mark_out: int,
                                   mark_type: str = "all") -> str:
    """Set mark in/out points on a media pool clip.

    *clip_name*: name of the clip in the media pool.
    *mark_in*/*mark_out*: frame numbers.
    *mark_type*: 'video', 'audio', or 'all' (default).
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp.GetRootFolder(), clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."

    result = clip.SetMarkInOut(int(mark_in), int(mark_out), mark_type)
    if result:
        return f"Marks set on '{clip_name}': in={mark_in}, out={mark_out} ({mark_type})."
    return f"Failed to set marks on '{clip_name}'."


@mcp.tool
def resolve_clear_clip_mark_in_out(clip_name: str, mark_type: str = "all") -> str:
    """Clear mark in/out points on a media pool clip.

    *clip_name*: name of the clip.
    *mark_type*: 'video', 'audio', or 'all' (default).
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp.GetRootFolder(), clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."

    result = clip.ClearMarkInOut(mark_type)
    if result:
        return f"Marks cleared on '{clip_name}' ({mark_type})."
    return f"Failed to clear marks on '{clip_name}'."


def _find_clip(folder, name):
    """Recursively search for a clip by name."""
    for clip in (folder.GetClipList() or []):
        if clip.GetName() == name:
            return clip
    for sub in (folder.GetSubFolderList() or []):
        found = _find_clip(sub, name)
        if found:
            return found
    return None
