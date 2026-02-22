"""
Fairlight (audio) MCP tools.

Covers: Voice isolation, audio insertion at playhead, and audio track
inspection for the Fairlight page.
"""

from .config import mcp
from .resolve import _boilerplate

# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_voice_isolation(track_index: int) -> str:
    """Get the voice isolation state for an audio track.

    *track_index*: 1-based audio track number.
    Returns whether voice isolation is enabled and its amount.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    state = tl.GetVoiceIsolationState(int(track_index))
    if state is None:
        return f"Could not read voice isolation for audio track {track_index}."

    if isinstance(state, dict):
        enabled = state.get("enable", False)
        amount = state.get("amount", 0)
        return f"Voice isolation on track {track_index}: {'ON' if enabled else 'OFF'}, amount={amount}"
    return f"Voice isolation on track {track_index}: {state}"


@mcp.tool
def resolve_set_voice_isolation(track_index: int, enabled: bool = True, amount: int = 50) -> str:
    """Set voice isolation on an audio track.

    *track_index*: 1-based audio track number.
    *enabled*: True to enable, False to disable.
    *amount*: isolation strength (0-100, default 50).

    Requires DaVinci Resolve Studio.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    state = {"enable": enabled, "amount": int(amount)}
    result = tl.SetVoiceIsolationState(int(track_index), state)
    action = "enabled" if enabled else "disabled"
    if result:
        return f"Voice isolation {action} on audio track {track_index} (amount={amount})."
    return "Failed to set voice isolation. Requires Resolve Studio."


@mcp.tool
def resolve_insert_audio_at_playhead(media_path: str, offset: float = 0, duration: float = 0) -> str:
    """Insert an audio file at the current playhead position.

    *media_path*: absolute path to the audio file.
    *offset*: start offset within the file (seconds, default 0).
    *duration*: duration to insert (seconds, 0 = full file).

    Operates on the current audio track on the Fairlight page.
    """
    _, project, _ = _boilerplate()

    args = {"FilePath": media_path}
    if offset > 0:
        args["Offset"] = int(offset * 1000)  # milliseconds
    if duration > 0:
        args["Duration"] = int(duration * 1000)

    result = project.InsertAudioToCurrentTrackAtPlayhead(media_path, int(offset), int(duration))
    if result:
        return f"Audio inserted at playhead from '{media_path}'."
    return "Failed to insert audio. Check file path and ensure Fairlight page is active."


@mcp.tool
def resolve_get_audio_track_info() -> str:
    """Get info about all audio tracks on the current timeline.

    Returns track count, names, enabled state, and clip counts.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    a_tracks = tl.GetTrackCount("audio") or 0
    if a_tracks == 0:
        return "No audio tracks on timeline."

    lines = [f"{a_tracks} audio track(s):"]
    for i in range(1, a_tracks + 1):
        name = tl.GetTrackName("audio", i) or f"Audio {i}"
        enabled = tl.GetIsTrackEnabled("audio", i)
        locked = tl.GetIsTrackLocked("audio", i)
        items = tl.GetItemListInTrack("audio", i) or []
        state_parts = []
        if not enabled:
            state_parts.append("disabled")
        if locked:
            state_parts.append("locked")
        state_str = f" ({', '.join(state_parts)})" if state_parts else ""
        lines.append(f"  {i}. {name} — {len(items)} clip(s){state_str}")
    return "\n".join(lines)
