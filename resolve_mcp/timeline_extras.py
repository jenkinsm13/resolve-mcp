"""
Additional timeline and item tools — wrapping remaining API gaps.

Covers: timecodes, linked items, track info, thumbnails, LUT export,
Fusion clips, sidecar updates, node color reset, and Fairlight presets.
"""

import base64

from .config import mcp
from .resolve import _boilerplate, get_resolve

# ---------------------------------------------------------------------------
# Timecode tools (Timeline)
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_current_timecode() -> str:
    """Get the current playhead position as a timecode string.

    Works on Cut, Edit, Color, Fairlight, and Deliver pages.
    Returns format like '01:02:15:03'.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    tc = tl.GetCurrentTimecode()
    return f"Current timecode: {tc}" if tc else "Could not read timecode."


@mcp.tool
def resolve_set_current_timecode(timecode: str) -> str:
    """Set the playhead to a specific timecode.

    *timecode*: timecode string (e.g. '01:02:15:03').
    Works on Cut, Edit, Color, Fairlight, and Deliver pages.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    result = tl.SetCurrentTimecode(timecode)
    if result:
        return f"Playhead moved to {timecode}."
    return f"Failed to set timecode to '{timecode}'. Check format (HH:MM:SS:FF)."


# ---------------------------------------------------------------------------
# Current video item
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_current_video_item() -> str:
    """Get the current video timeline item (the clip under the playhead).

    Returns the clip name, duration, and position on the timeline.
    Useful on the Color page to identify which clip is being graded.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    item = tl.GetCurrentVideoItem()
    if not item:
        return "No current video item."

    name = item.GetName() or "Unnamed"
    duration = item.GetDuration()
    start = item.GetStart()
    end = item.GetEnd()
    return f"Current clip: '{name}' (frames {start}-{end}, duration {duration})"


# ---------------------------------------------------------------------------
# Linked items and track info (TimelineItem)
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_linked_items(track_type: str, track_index: int, item_index: int) -> str:
    """Get all timeline items linked to a specific clip.

    *track_type*: 'video' or 'audio'.
    *item_index*: 1-based clip position on the track.

    Returns a list of linked items (e.g., video clip linked to its audio).
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    items = tl.GetItemListInTrack(track_type, int(track_index)) or []
    if item_index < 1 or item_index > len(items):
        return f"Item {item_index} out of range (1-{len(items)})."
    item = items[item_index - 1]

    linked = item.GetLinkedItems()
    if not linked:
        return f"No items linked to item {item_index}."

    lines = [f"{len(linked)} linked item(s):"]
    for li in linked:
        name = li.GetName() or "Unnamed"
        track_info = li.GetTrackTypeAndIndex()
        if track_info and len(track_info) >= 2:
            lines.append(f"  • '{name}' on {track_info[0]} track {track_info[1]}")
        else:
            lines.append(f"  • '{name}'")
    return "\n".join(lines)


@mcp.tool
def resolve_get_track_type_and_index(track_type: str, track_index: int, item_index: int) -> str:
    """Get the track type and index for a timeline item.

    Returns the track type ('video', 'audio', 'subtitle') and 1-based index.
    Useful for cross-referencing items across tracks.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    items = tl.GetItemListInTrack(track_type, int(track_index)) or []
    if item_index < 1 or item_index > len(items):
        return f"Item {item_index} out of range (1-{len(items)})."
    item = items[item_index - 1]

    result = item.GetTrackTypeAndIndex()
    if result and len(result) >= 2:
        return f"Item {item_index}: {result[0]} track {result[1]}"
    return "Could not determine track type and index."


@mcp.tool
def resolve_get_track_sub_type(track_type: str, track_index: int) -> str:
    """Get the audio format type for a track.

    *track_type*: 'audio' (only meaningful for audio tracks).
    *track_index*: 1-based track number.

    Returns format like 'mono', 'stereo', '5.1', '7.1', etc.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    sub_type = tl.GetTrackSubType(track_type, int(track_index))
    if sub_type:
        return f"Track {track_index} ({track_type}): format = {sub_type}"
    return f"No sub-type for {track_type} track {track_index} (may not be an audio track)."


# ---------------------------------------------------------------------------
# Thumbnail
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_current_thumbnail(save_path: str = "") -> str:
    """Get thumbnail image data for the current clip on the Color page.

    *save_path*: optional absolute path to save the PNG. If empty, returns
                 image dimensions only.

    The thumbnail is RGB 8-bit, base64-encoded. Useful for quick visual
    checks without a full frame export.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    thumb = tl.GetCurrentClipThumbnailImage()
    if not thumb:
        return "No thumbnail available (ensure Color page is active)."

    width = thumb.get("width", 0)
    height = thumb.get("height", 0)
    fmt = thumb.get("format", "unknown")
    data = thumb.get("data", "")

    if save_path and data:
        try:
            raw = base64.b64decode(data)
            with open(save_path, "wb") as f:
                f.write(raw)
            return f"Thumbnail saved: {save_path} ({width}x{height}, {fmt})"
        except Exception as e:
            return f"Thumbnail {width}x{height} but save failed: {e}"

    return f"Thumbnail: {width}x{height} ({fmt}), {len(data)} bytes base64"


# ---------------------------------------------------------------------------
# LUT Export (TimelineItem)
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_export_lut(
    export_path: str, lut_size: str = "33pt", track_type: str = "video", track_index: int = 1, item_index: int = 0
) -> str:
    """Export a LUT from a timeline clip's grade.

    *export_path*: absolute path for the LUT file (.cube or .vlt).
    *lut_size*: '17pt', '33pt', '65pt', or 'panasonic_vlut'.
    *item_index*: 0 = current clip, or 1-based index.

    Exports the cumulative grade of the clip as a LUT file for use
    in other applications or on-set monitoring.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    # Map size strings to API constants
    resolve = get_resolve()
    size_map = {
        "17pt": getattr(resolve, "EXPORT_LUT_17PTCUBE", 0),
        "33pt": getattr(resolve, "EXPORT_LUT_33PTCUBE", 1),
        "65pt": getattr(resolve, "EXPORT_LUT_65PTCUBE", 2),
        "panasonic_vlut": getattr(resolve, "EXPORT_LUT_PANASONICVLUT", 3),
    }
    export_type = size_map.get(lut_size.lower())
    if export_type is None:
        return f"Invalid LUT size '{lut_size}'. Use '17pt', '33pt', '65pt', or 'panasonic_vlut'."

    if item_index == 0:
        item = tl.GetCurrentVideoItem()
        if not item:
            return "No current clip."
    else:
        items = tl.GetItemListInTrack(track_type, int(track_index)) or []
        if item_index < 1 or item_index > len(items):
            return f"Item {item_index} out of range."
        item = items[item_index - 1]

    result = item.ExportLUT(export_type, export_path)
    name = item.GetName() or f"clip {item_index}"
    if result:
        return f"LUT exported from '{name}' → {export_path} ({lut_size})"
    return f"Failed to export LUT from '{name}'."


# ---------------------------------------------------------------------------
# Fusion Clip creation
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_create_fusion_clip(track_type: str, track_index: int, item_indices: str) -> str:
    """Create a Fusion clip from timeline items.

    *item_indices*: comma-separated 1-based indices of clips to merge.

    Fusion clips combine multiple timeline items into a single Fusion
    composition, allowing complex compositing across cuts.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    items = tl.GetItemListInTrack(track_type, int(track_index)) or []
    indices = [int(x.strip()) for x in item_indices.split(",")]
    selected = [items[i - 1] for i in indices if 1 <= i <= len(items)]
    if not selected:
        return "No valid items selected."

    result = tl.CreateFusionClip(selected)
    if result:
        return f"Created Fusion clip from {len(selected)} item(s)."
    return "Failed to create Fusion clip."


# ---------------------------------------------------------------------------
# Sidecar update (BRAW / R3D)
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_update_sidecar(track_type: str, track_index: int, item_index: int) -> str:
    """Update sidecar file for a BRAW or R3D clip.

    Writes current decode settings to the .sidecar (BRAW) or .RMD (R3D) file.
    Changes persist outside of Resolve and affect other applications reading
    the same media.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    items = tl.GetItemListInTrack(track_type, int(track_index)) or []
    if item_index < 1 or item_index > len(items):
        return f"Item {item_index} out of range."
    item = items[item_index - 1]

    result = item.UpdateSidecar()
    name = item.GetName() or f"item {item_index}"
    if result:
        return f"Sidecar updated for '{name}'."
    return f"Failed to update sidecar for '{name}'. Is this a BRAW/R3D clip?"


# ---------------------------------------------------------------------------
# Node color reset
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_reset_all_node_colors() -> str:
    """Reset node colors for all nodes in the current clip's active grade version.

    Clears any custom node label colors without affecting the actual grades.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    item = tl.GetCurrentVideoItem()
    if not item:
        return "No current clip."

    result = item.ResetAllNodeColors()
    if result:
        return "All node colors reset."
    return "Failed to reset node colors."


# ---------------------------------------------------------------------------
# ARRI CDL + LUT
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_apply_arri_cdl_lut() -> str:
    """Apply ARRI CDL and LUT to the current clip's grade.

    Reads CDL values and LUT path from the ARRI metadata embedded in the
    clip and applies them to the node graph. Only works with ARRI source media.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    item = tl.GetCurrentVideoItem()
    if not item:
        return "No current clip."

    graph = item.GetNodeGraph()
    if not graph:
        return "No node graph available."

    result = graph.ApplyArriCdlLut()
    if result:
        return "ARRI CDL and LUT applied successfully."
    return "Failed to apply ARRI CDL/LUT. Is this ARRI source media?"


# ---------------------------------------------------------------------------
# Fairlight presets
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_fairlight_presets() -> str:
    """List available Fairlight presets.

    Fairlight presets contain audio processing settings that can be
    applied to a timeline's audio.
    """
    resolve = get_resolve()
    if not resolve:
        return "DaVinci Resolve is not running."

    presets = resolve.GetFairlightPresets()
    if not presets:
        return "No Fairlight presets available."

    if isinstance(presets, dict):
        lines = [f"{len(presets)} Fairlight preset(s):"]
        for name, _info in presets.items():
            lines.append(f"  • {name}")
        return "\n".join(lines)
    elif isinstance(presets, list):
        lines = [f"{len(presets)} Fairlight preset(s):"]
        for p in presets:
            lines.append(f"  • {p}")
        return "\n".join(lines)
    return f"Fairlight presets: {presets}"


@mcp.tool
def resolve_apply_fairlight_preset(preset_name: str) -> str:
    """Apply a Fairlight preset to the current timeline.

    *preset_name*: name from resolve_get_fairlight_presets.
    Applies audio processing settings to all audio tracks.
    """
    _, project, _ = _boilerplate()
    result = project.ApplyFairlightPresetToCurrentTimeline(preset_name)
    if result:
        return f"Fairlight preset '{preset_name}' applied."
    return f"Failed to apply Fairlight preset '{preset_name}'."


# ---------------------------------------------------------------------------
# Third-party metadata (MediaPoolItem)
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_third_party_metadata(clip_name: str, metadata_key: str = "") -> str:
    """Get third-party metadata for a media pool clip.

    *clip_name*: name of the clip.
    *metadata_key*: specific key (empty = return all third-party metadata).

    Third-party metadata is separate from standard Resolve metadata and
    is used by external tools and workflows (e.g., camera metadata, VFX IDs).
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp.GetRootFolder(), clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."

    if metadata_key:
        val = clip.GetThirdPartyMetadata(metadata_key)
        return f"'{clip_name}' [{metadata_key}]: {val}"
    else:
        all_meta = clip.GetThirdPartyMetadata()
        if not all_meta:
            return f"No third-party metadata on '{clip_name}'."
        lines = [f"Third-party metadata for '{clip_name}':"]
        for k, v in all_meta.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)


@mcp.tool
def resolve_set_third_party_metadata(clip_name: str, metadata_key: str, metadata_value: str) -> str:
    """Set third-party metadata on a media pool clip.

    *clip_name*: name of the clip.
    *metadata_key*: the metadata key to set.
    *metadata_value*: the value to assign.
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp.GetRootFolder(), clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."

    result = clip.SetThirdPartyMetadata(metadata_key, metadata_value)
    if result:
        return f"Set '{metadata_key}'='{metadata_value}' on '{clip_name}'."
    return f"Failed to set third-party metadata on '{clip_name}'."


# ---------------------------------------------------------------------------
# MediaPool extras
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_selected_clips() -> str:
    """Get the currently selected clips in the media pool.

    Returns names of all clips currently selected in the media pool panel.
    """
    _, _, mp = _boilerplate()
    clips = mp.GetSelectedClips()
    if not clips:
        return "No clips selected in media pool."

    lines = [f"{len(clips)} selected clip(s):"]
    for c in clips:
        name = c.GetName() if hasattr(c, "GetName") else str(c)
        lines.append(f"  • {name}")
    return "\n".join(lines)


@mcp.tool
def resolve_move_folders(folder_names: str, target_folder: str) -> str:
    """Move media pool folders to a target folder.

    *folder_names*: comma-separated folder names to move.
    *target_folder*: name of the destination folder.
    """
    _, _, mp = _boilerplate()
    root = mp.GetRootFolder()
    target = _find_folder(root, target_folder)
    if not target:
        return f"Target folder '{target_folder}' not found."

    names = [n.strip() for n in folder_names.split(",")]
    folders = []
    for name in names:
        f = _find_folder(root, name)
        if f:
            folders.append(f)

    if not folders:
        return "No matching folders found."

    result = mp.MoveFolders(folders, target)
    if result:
        return f"Moved {len(folders)} folder(s) to '{target_folder}'."
    return "Failed to move folders."


@mcp.tool
def resolve_reveal_in_storage(path: str) -> str:
    """Reveal a file or folder path in Resolve's Media Storage panel.

    *path*: absolute file or folder path.
    Expands and highlights the given path in the Media Storage browser.
    """
    resolve = get_resolve()
    if not resolve:
        return "DaVinci Resolve is not running."

    ms = resolve.GetMediaStorage()
    if not ms:
        return "Cannot access Media Storage."

    result = ms.RevealInStorage(path)
    if result:
        return f"Revealed in Media Storage: {path}"
    return f"Failed to reveal '{path}' — check if path exists."


@mcp.tool
def resolve_load_burn_in_preset(
    preset_name: str, track_type: str = "video", track_index: int = 1, item_index: int = 0
) -> str:
    """Load a data burn-in preset for a timeline clip.

    *preset_name*: name of the burn-in preset.
    *item_index*: 0 = current clip, or 1-based clip index.

    Burn-in presets overlay metadata (timecode, clip name, reel) onto the image.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    if item_index == 0:
        item = tl.GetCurrentVideoItem()
        if not item:
            return "No current clip."
    else:
        items = tl.GetItemListInTrack(track_type, int(track_index)) or []
        if item_index < 1 or item_index > len(items):
            return f"Item {item_index} out of range."
        item = items[item_index - 1]

    result = item.LoadBurnInPreset(preset_name)
    if result:
        return f"Burn-in preset '{preset_name}' loaded."
    return f"Failed to load burn-in preset '{preset_name}'."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _find_folder(folder, name):
    """Recursively find a folder by name."""
    if folder.GetName() == name:
        return folder
    for sub in folder.GetSubFolderList() or []:
        found = _find_folder(sub, name)
        if found:
            return found
    return None
