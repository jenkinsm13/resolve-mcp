"""
Media Storage MCP tools.

Covers: MediaStorage object — browsing mounted volumes, listing files
at paths, and importing from storage locations into the media pool.
"""

from .config import mcp
from .resolve import _boilerplate, get_resolve

# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_list_volumes() -> str:
    """List all mounted media storage volumes visible to Resolve.

    These are the volumes configured in Resolve's Media Storage preferences.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."

    storage = resolve.GetMediaStorage()
    if not storage:
        return "Cannot access Media Storage."

    volumes = storage.GetMountedVolumeList()
    if not volumes:
        return "No mounted volumes found."

    return f"{len(volumes)} volume(s):\n" + "\n".join(f"  • {v}" for v in volumes)


@mcp.tool
def resolve_browse_storage(folder_path: str) -> str:
    """List files and subfolders at a media storage path.

    *folder_path*: absolute path to browse.
    Returns subfolders and media files found at that location.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."

    storage = resolve.GetMediaStorage()
    if not storage:
        return "Cannot access Media Storage."

    subfolders = storage.GetSubFolderList(folder_path)
    files = storage.GetFileList(folder_path)

    parts = [f"Contents of {folder_path}:"]
    if subfolders:
        parts.append(f"\nSubfolders ({len(subfolders)}):")
        for sf in subfolders[:50]:  # Cap at 50 to avoid huge output
            parts.append(f"  📁 {sf}")
        if len(subfolders) > 50:
            parts.append(f"  … and {len(subfolders) - 50} more")
    if files:
        parts.append(f"\nFiles ({len(files)}):")
        for f in files[:100]:  # Cap at 100
            parts.append(f"  📄 {f}")
        if len(files) > 100:
            parts.append(f"  … and {len(files) - 100} more")
    if not subfolders and not files:
        parts.append("  (empty or not accessible)")
    return "\n".join(parts)


@mcp.tool
def resolve_add_from_storage(file_paths: str, target_bin: str = "") -> str:
    """Import files from media storage into the media pool.

    *file_paths*: comma-separated absolute paths of files to import.
    *target_bin*: optional bin name to import into (uses current folder if omitted).

    This uses the MediaStorage.AddItemListToMediaPool API which handles
    RAW formats and multi-part media (e.g. R3D, BRAW) correctly.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."

    storage = resolve.GetMediaStorage()
    if not storage:
        return "Cannot access Media Storage."

    paths = [p.strip() for p in file_paths.split(",") if p.strip()]

    if target_bin:
        _, _, media_pool = _boilerplate()
        from .resolve import _find_bin

        folder = _find_bin(media_pool.GetRootFolder(), target_bin)
        if folder:
            media_pool.SetCurrentFolder(folder)

    result = storage.AddItemListToMediaPool(paths)
    if result:
        count = len(result) if isinstance(result, list) else 1
        return f"Added {count} item(s) from storage to media pool."
    return "Failed to add items. Check file paths."
