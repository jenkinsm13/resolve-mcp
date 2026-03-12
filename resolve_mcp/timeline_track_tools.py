"""Timeline track management and export tools: add/delete/name/enable/lock tracks, export, subtitles."""

from .config import mcp
from .resolve import _boilerplate
from .timeline_query_tools import _get_timeline_by_name


@mcp.tool
def resolve_add_track(track_type: str, sub_type: str = "") -> str:
    """Add a track to the current timeline.

    *track_type*: 'video', 'audio', or 'subtitle'.
    *sub_type* (optional): for audio → 'mono', 'stereo', '5.1', '7.1', 'adaptive1'…'adaptive24'.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    track_type = track_type.lower()
    if track_type not in {"video", "audio", "subtitle"}:
        return "track_type must be 'video', 'audio', or 'subtitle'."
    result = tl.AddTrack(track_type, sub_type if sub_type else "")
    return f"Added {track_type} track (now {tl.GetTrackCount(track_type)} total)." if result else f"Failed to add {track_type} track."


@mcp.tool
def resolve_delete_track(track_type: str, track_index: int) -> str:
    """Delete a track from the current timeline.

    WARNING: Deleting a track removes all clips on it.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    result = tl.DeleteTrack(track_type.lower(), int(track_index))
    return f"Deleted {track_type} track {track_index}." if result else f"Failed to delete {track_type} track {track_index}."


@mcp.tool
def resolve_set_track_name(track_type: str, track_index: int, name: str) -> str:
    """Rename a track on the current timeline."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    result = tl.SetTrackName(track_type.lower(), int(track_index), name)
    return f"Renamed {track_type} track {track_index} → '{name}'." if result else "Failed to rename track."


@mcp.tool
def resolve_set_track_enabled(track_type: str, track_index: int, enabled: bool = True) -> str:
    """Enable or disable a track on the current timeline."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    result = tl.SetTrackEnable(track_type.lower(), int(track_index), enabled)
    state = "enabled" if enabled else "disabled"
    return f"{track_type.capitalize()} track {track_index} {state}." if result else f"Failed to set {track_type} track {track_index} to {state}."


@mcp.tool
def resolve_set_track_locked(track_type: str, track_index: int, locked: bool = True) -> str:
    """Lock or unlock a track on the current timeline."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    result = tl.SetTrackLock(track_type.lower(), int(track_index), locked)
    state = "locked" if locked else "unlocked"
    return f"{track_type.capitalize()} track {track_index} {state}." if result else f"Failed to set track to {state}."


@mcp.tool
def resolve_export_timeline(format: str, file_path: str, timeline_name: str = "") -> str:
    """Export a timeline to a file.

    *format*: 'AAF', 'DRT', 'EDL', 'FCP_7_XML', 'FCPXML_1_8', 'FCPXML_1_9',
              'FCPXML_1_10', 'HDL', 'CSV', 'MIDI', 'OTIO'.
    """
    _, project, _ = _boilerplate()
    if timeline_name:
        tl = _get_timeline_by_name(project, timeline_name)
        if not tl:
            return f"Timeline '{timeline_name}' not found."
        project.SetCurrentTimeline(tl)
    else:
        tl = project.GetCurrentTimeline()
        if not tl:
            return "No active timeline."

    valid_formats = {"AAF", "DRT", "EDL", "FCP_7_XML", "FCPXML_1_8", "FCPXML_1_9", "FCPXML_1_10", "HDL", "CSV", "MIDI", "OTIO"}
    fmt_upper = format.upper().replace(" ", "_")
    if fmt_upper not in valid_formats:
        return f"Invalid format '{format}'. Valid: {', '.join(sorted(valid_formats))}"
    result = tl.Export(file_path, fmt_upper)
    return f"Exported timeline '{tl.GetName()}' as {fmt_upper} → {file_path}" if result else "Export failed. Check file path and permissions."


@mcp.tool
def resolve_create_subtitles(track_index: int = 0, language: str = "auto") -> str:
    """Create auto-generated subtitles on the current timeline.

    *language*: language code (e.g. 'en', 'es') or 'auto' for detection.
    Requires DaVinci Resolve Studio.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."
    settings = {}
    if language and language != "auto":
        settings["language"] = language
    if track_index > 0:
        settings["trackIndex"] = track_index
    result = tl.CreateSubtitlesFromAudio(settings) if settings else tl.CreateSubtitlesFromAudio()
    return "Auto-caption generation started." if result else "Auto-caption failed. Requires Resolve Studio and language packs."
