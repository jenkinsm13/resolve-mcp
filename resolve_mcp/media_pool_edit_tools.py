"""Media pool editing tools: create bins, import, move, metadata, color, delete, relink, sync."""

import json

from .config import mcp
from .media_pool_query_tools import _resolve_clip, _resolve_clips
from .resolve import _boilerplate, _find_bin


@mcp.tool
def resolve_create_bin(bin_name: str, parent_bin: str = "") -> str:
    """Create a new subfolder (bin) in the media pool.

    If *parent_bin* is provided, the new bin is created under it.
    """
    _, _, media_pool = _boilerplate()
    if parent_bin:
        folder = _find_bin(media_pool.GetRootFolder(), parent_bin)
        if not folder:
            return f"Parent bin '{parent_bin}' not found."
        media_pool.SetCurrentFolder(folder)
    new_folder = media_pool.AddSubFolder(media_pool.GetCurrentFolder(), bin_name)
    return f"Created bin '{bin_name}'." if new_folder else f"Failed to create bin '{bin_name}'. It may already exist."


@mcp.tool
def resolve_import_media(file_paths: str, target_bin: str = "") -> str:
    """Import media files into the media pool.

    *file_paths*: comma-separated absolute file paths.
    *target_bin*: optionally specifies the bin to import into.
    """
    _, _, media_pool = _boilerplate()
    paths = [p.strip() for p in file_paths.split(",") if p.strip()]
    if target_bin:
        folder = _find_bin(media_pool.GetRootFolder(), target_bin)
        if not folder:
            return f"Target bin '{target_bin}' not found."
        media_pool.SetCurrentFolder(folder)
    imported = media_pool.ImportMedia(paths)
    return f"Imported {len(imported)} file(s)." if imported else "Import failed. Check file paths and formats."


@mcp.tool
def resolve_move_clips(clip_names: str, target_bin: str) -> str:
    """Move clips to a different bin.

    *clip_names*: comma-separated list of clip names.
    """
    _, _, media_pool = _boilerplate()
    names = [n.strip() for n in clip_names.split(",") if n.strip()]
    target = _find_bin(media_pool.GetRootFolder(), target_bin)
    if not target:
        return f"Target bin '{target_bin}' not found."
    found, missing = _resolve_clips(media_pool, names)
    if not found:
        return f"No matching clips found. Missing: {', '.join(missing)}"
    result = media_pool.MoveClips(found, target)
    msg = f"Moved {len(found)} clip(s) to '{target_bin}'."
    if missing:
        msg += f" Not found: {', '.join(missing)}."
    return ("Move operation returned failure. " + msg) if not result else msg


@mcp.tool
def resolve_set_clip_metadata(clip_name: str, metadata_json: str) -> str:
    """Set metadata on a media pool clip.

    *metadata_json*: JSON object of key-value pairs.
    Valid keys: Comments, Description, Keywords, People, Shot, Scene, Take, etc.
    """
    _, _, media_pool = _boilerplate()
    clip = _resolve_clip(media_pool, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON: {exc}"
    if not isinstance(metadata, dict):
        return "metadata_json must be a JSON object (dict)."
    results = [f"  {k}: {'OK' if clip.SetMetadata(k, str(v)) else 'FAILED'}" for k, v in metadata.items()]
    return "Metadata update:\n" + "\n".join(results)


@mcp.tool
def resolve_set_clip_color(clip_name: str, color: str) -> str:
    """Set the color tag on a media pool clip.

    Valid colors: Orange, Apricot, Yellow, Lime, Olive, Green, Teal, Navy,
    Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate.
    """
    _, _, media_pool = _boilerplate()
    clip = _resolve_clip(media_pool, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."
    return f"Set color '{color}' on '{clip_name}'." if clip.SetClipColor(color) else f"Failed to set color '{color}'."


@mcp.tool
def resolve_delete_clips(clip_names: str) -> str:
    """Delete clips from the media pool (comma-separated names).

    WARNING: This permanently removes clips from the project.
    """
    _, _, media_pool = _boilerplate()
    names = [n.strip() for n in clip_names.split(",") if n.strip()]
    found, missing = _resolve_clips(media_pool, names)
    if not found:
        return f"No matching clips found. Missing: {', '.join(missing)}"
    result = media_pool.DeleteClips(found)
    msg = f"Deleted {len(found)} clip(s)."
    if missing:
        msg += f" Not found: {', '.join(missing)}."
    return ("Delete returned failure. " + msg) if not result else msg


@mcp.tool
def resolve_relink_clips(clip_names: str, folder_path: str) -> str:
    """Relink offline clips to media in a new folder.

    *folder_path*: absolute path to the folder containing the source files.
    """
    _, _, media_pool = _boilerplate()
    names = [n.strip() for n in clip_names.split(",") if n.strip()]
    found, missing = _resolve_clips(media_pool, names)
    if not found:
        return f"No matching clips found. Missing: {', '.join(missing)}"
    result = media_pool.RelinkClips(found, folder_path)
    msg = f"Relinked {len(found)} clip(s) to '{folder_path}'."
    if missing:
        msg += f" Not found: {', '.join(missing)}."
    return ("Relink returned failure. " + msg) if not result else msg


@mcp.tool
def resolve_auto_sync_audio(bin_name: str, mode: str = "timecode") -> str:
    """Auto-sync audio for all clips in a bin.

    *mode*: 'timecode' or 'waveform'.
    """
    _, _, media_pool = _boilerplate()
    folder = _find_bin(media_pool.GetRootFolder(), bin_name)
    if not folder:
        return f"Bin '{bin_name}' not found."
    clips = folder.GetClipList() or []
    if not clips:
        return f"No clips in bin '{bin_name}'."
    mode_int = {"timecode": 0, "waveform": 1}.get(mode.lower(), 0)
    result = media_pool.AutoSyncAudio(clips, mode_int)
    return (
        f"Auto-synced {len(clips)} clip(s) in '{bin_name}' using {mode} mode."
        if result
        else f"Auto-sync failed for clips in '{bin_name}'."
    )
