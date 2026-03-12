"""
MediaPool extras — refresh, create timeline from clips, import timeline/folder,
export metadata, unlink clips, delete folders, unique IDs.
"""

import json
from typing import Optional

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate, _find_bin, _collect_clips_recursive


# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_refresh_folders() -> str:
    """Refresh the media pool folder structure.

    Args: None
    """
    _, _, mp = _boilerplate()
    r = mp.RefreshFolders()
    return "Media pool folders refreshed." if r else "Refresh failed."


@mcp.tool
@safe_resolve_call
def resolve_create_timeline_from_clips(timeline_name: str,
                                        clip_names: str,
                                        bin_name: str = "") -> str:
    """Create a new timeline from specific clips.

    *clip_names*: comma-separated clip names in the pool.
    *bin_name*: optional bin to search in.

    Args:
        timeline_name (str): Name for the new timeline.
        clip_names (str): Comma-separated list of clip names to include.
        bin_name (str): Optional bin name to search in. If omitted, searches root folder.
    """
    _, _, mp = _boilerplate()
    root = mp.GetRootFolder()
    folder = _find_bin(root, bin_name) if bin_name else root
    pool = _collect_clips_recursive(folder) if folder else {}

    names = [n.strip() for n in clip_names.split(",") if n.strip()]
    clips = [pool[n] for n in names if n in pool]
    if not clips:
        return "No matching clips found."

    tl = mp.CreateTimelineFromClips(timeline_name, clips)
    return f"Timeline '{timeline_name}' created with {len(clips)} clip(s)." if tl \
        else "Failed to create timeline from clips."


@mcp.tool
@safe_resolve_call
def resolve_import_timeline_from_file(file_path: str,
                                       import_options: str = "{}") -> str:
    """Import a timeline from an external file (AAF, EDL, XML, FCPXML, OTIO).

    *import_options*: optional JSON with import settings like
    {"timelineName": "My Import"}.

    Args:
        file_path (str): Path to the timeline file (AAF, EDL, XML, FCPXML, OTIO).
        import_options (str): JSON string with optional import settings. Defaults to "{}".
    """
    _, _, mp = _boilerplate()
    try:
        opts = json.loads(import_options)
    except json.JSONDecodeError:
        opts = {}
    tl = mp.ImportTimelineFromFile(file_path, opts) if opts \
        else mp.ImportTimelineFromFile(file_path)
    return f"Timeline imported from {file_path}" if tl \
        else f"Import failed for {file_path}."


@mcp.tool
@safe_resolve_call
def resolve_import_folder_to_media_pool(folder_path: str,
                                         target_bin: str = "") -> str:
    """Recursively import an entire folder into the media pool.

    Preserves subfolder structure as bins.

    Args:
        folder_path (str): Path to the folder to import.
        target_bin (str): Optional destination bin in the media pool. If omitted, uses root folder.
    """
    _, _, mp = _boilerplate()
    if target_bin:
        f = _find_bin(mp.GetRootFolder(), target_bin)
        if f:
            mp.SetCurrentFolder(f)
    items = mp.ImportFolderToMediaPool(folder_path)
    if items:
        ct = len(items) if isinstance(items, list) else 1
        return f"Imported folder — {ct} item(s) added."
    return "Folder import failed."


@mcp.tool
@safe_resolve_call
def resolve_export_metadata(file_path: str, bin_name: str = "") -> str:
    """Export clip metadata from the media pool to a CSV/file.

    *file_path*: destination path.
    *bin_name*: optional bin to export from (root if omitted).

    Args:
        file_path (str): Destination file path for metadata export.
        bin_name (str): Optional bin name to export from. If omitted, exports from root folder.
    """
    _, _, mp = _boilerplate()
    if bin_name:
        f = _find_bin(mp.GetRootFolder(), bin_name)
        if f:
            mp.SetCurrentFolder(f)
    r = mp.ExportMetadata(file_path)
    return f"Metadata exported to {file_path}" if r else "Export failed."


@mcp.tool
@safe_resolve_call
def resolve_unlink_clips(clip_names: str) -> str:
    """Unlink previously linked clips in the media pool.

    *clip_names*: comma-separated clip names.

    Args:
        clip_names (str): Comma-separated list of clip names to unlink.
    """
    _, _, mp = _boilerplate()
    pool = _collect_clips_recursive(mp.GetRootFolder())
    names = [n.strip() for n in clip_names.split(",") if n.strip()]
    clips = [pool[n] for n in names if n in pool]
    if not clips:
        return "No matching clips found."
    r = mp.UnlinkClips(clips)
    return f"Unlinked {len(clips)} clip(s)." if r else "Unlink failed."


@mcp.tool
@safe_resolve_call
def resolve_delete_bins(bin_names: str) -> str:
    """Delete bins (folders) from the media pool.

    *bin_names*: comma-separated bin names.
    WARNING: Deletes all clips inside the bins.

    Args:
        bin_names (str): Comma-separated list of bin names to delete.
    """
    _, _, mp = _boilerplate()
    root = mp.GetRootFolder()
    names = [n.strip() for n in bin_names.split(",") if n.strip()]
    folders = [_find_bin(root, n) for n in names]
    folders = [f for f in folders if f]
    if not folders:
        return "No matching bins found."
    r = mp.DeleteFolders(folders)
    return f"Deleted {len(folders)} bin(s)." if r else "Delete failed."


@mcp.tool
@safe_resolve_call
def resolve_get_media_pool_id() -> str:
    """Get the unique ID of the media pool.

    Args: None
    """
    _, _, mp = _boilerplate()
    uid = mp.GetUniqueId()
    return f"MediaPool unique ID: {uid}" if uid else "Could not retrieve ID."


@mcp.tool
@safe_resolve_call
def resolve_create_empty_timeline(timeline_name: str) -> str:
    """Create a blank empty timeline with no clips.

    Args:
        timeline_name (str): Name for the new empty timeline.
    """
    _, _, mp = _boilerplate()
    tl = mp.CreateEmptyTimeline(timeline_name)
    return f"Created empty timeline '{timeline_name}'." if tl \
        else f"Failed — name may already exist."
