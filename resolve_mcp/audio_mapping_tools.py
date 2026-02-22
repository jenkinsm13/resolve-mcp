"""
Audio mapping MCP tools.

Covers: Reading audio channel mapping for media pool clips and timeline items.
Shows embedded channels, linked audio, track types, and mute states.
Essential for debugging multi-track audio sync and channel routing issues.
"""

import json

from .config import mcp
from .resolve import _boilerplate


@mcp.tool
def resolve_get_audio_mapping(clip_name: str) -> str:
    """Get the audio channel mapping for a media pool clip.

    *clip_name*: name of the clip in the media pool.

    Returns embedded audio channels, linked audio info (paths, channels,
    offsets), and track mapping (channel assignments, types, mute states).
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp.GetRootFolder(), clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."

    mapping_str = clip.GetAudioMapping()
    if not mapping_str:
        return f"No audio mapping available for '{clip_name}'."

    try:
        mapping = json.loads(mapping_str)
        return _format_mapping(clip_name, mapping)
    except (json.JSONDecodeError, TypeError):
        return f"Audio mapping for '{clip_name}': {mapping_str}"


@mcp.tool
def resolve_get_source_audio_mapping(track_type: str, track_index: int, item_index: int) -> str:
    """Get the source audio channel mapping for a timeline item.

    *track_type*: 'video' or 'audio'.
    *track_index*: 1-based track number.
    *item_index*: 1-based clip position on the track.

    Returns how the source clip's audio channels are mapped in the timeline.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    items = tl.GetItemListInTrack(track_type, int(track_index)) or []
    if item_index < 1 or item_index > len(items):
        return f"Item {item_index} out of range (1-{len(items)})."
    item = items[item_index - 1]

    mapping_str = item.GetSourceAudioChannelMapping()
    if not mapping_str:
        name = item.GetName() or f"item {item_index}"
        return f"No source audio mapping for '{name}'."

    try:
        mapping = json.loads(mapping_str)
        name = item.GetName() or f"item {item_index}"
        return _format_mapping(name, mapping)
    except (json.JSONDecodeError, TypeError):
        return f"Source audio mapping: {mapping_str}"


def _format_mapping(clip_name, mapping):
    """Format audio mapping dict into readable output."""
    lines = [f"Audio mapping for '{clip_name}':"]

    embedded = mapping.get("embedded_audio_channels", 0)
    lines.append(f"  Embedded channels: {embedded}")

    linked = mapping.get("linked_audio", {})
    if linked:
        lines.append(f"  Linked audio ({len(linked)} source(s)):")
        for idx, info in linked.items():
            ch = info.get("channels", "?")
            offset = info.get("offset", 0)
            path = info.get("path", "?")
            lines.append(f"    [{idx}] {ch}ch, offset={offset}, path={path}")

    tracks = mapping.get("track_mapping", {})
    if tracks:
        lines.append(f"  Track mapping ({len(tracks)} track(s)):")
        for idx, info in tracks.items():
            ch_idx = info.get("channel_idx", [])
            muted = info.get("mute", False)
            fmt = info.get("type", "?")
            mute_str = " [MUTED]" if muted else ""
            lines.append(f"    Track {idx}: {fmt}, channels={ch_idx}{mute_str}")

    return "\n".join(lines)


def _find_clip(folder, name):
    """Recursively search for a clip by name."""
    for clip in folder.GetClipList() or []:
        if clip.GetName() == name:
            return clip
    for sub in folder.GetSubFolderList() or []:
        found = _find_clip(sub, name)
        if found:
            return found
    return None
