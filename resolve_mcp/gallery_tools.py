"""
Gallery, GalleryStillAlbum, and GalleryStill management.

Browse albums, export/delete stills, rename albums.
"""

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate


def _gallery(project):
    g = project.GetGallery()
    if not g:
        raise ValueError("Cannot access gallery.")
    return g


# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_list_still_albums() -> str:
    """List all gallery still albums.

    Args: None
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)
    albums = g.GetGalleryStillAlbums() or []
    if not albums:
        return "No still albums."
    current = g.GetCurrentStillAlbum()
    lines = [f"{len(albums)} album(s):"]
    for a in albums:
        name = a.GetAlbumName() if hasattr(a, "GetAlbumName") else str(a)
        marker = " ← active" if current and a == current else ""
        lines.append(f"  • {name}{marker}")
    return "\n".join(lines)


@mcp.tool
@safe_resolve_call
def resolve_set_current_still_album(album_name: str) -> str:
    """Switch the active gallery still album by name.

    Args:
        album_name (str): Name of the still album to activate.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)
    albums = g.GetGalleryStillAlbums() or []
    for a in albums:
        name = a.GetAlbumName() if hasattr(a, "GetAlbumName") else str(a)
        if name == album_name:
            r = g.SetCurrentStillAlbum(a)
            return f"Switched to album '{album_name}'." if r else "Failed."
    return f"Album '{album_name}' not found."


@mcp.tool
@safe_resolve_call
def resolve_rename_still_album(old_name: str, new_name: str) -> str:
    """Rename a gallery still album.

    Args:
        old_name (str): Current name of the still album.
        new_name (str): New name for the still album.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)
    albums = g.GetGalleryStillAlbums() or []
    for a in albums:
        name = a.GetAlbumName() if hasattr(a, "GetAlbumName") else str(a)
        if name == old_name:
            r = a.SetAlbumName(new_name)
            return f"Renamed '{old_name}' → '{new_name}'." if r else "Failed."
    return f"Album '{old_name}' not found."


@mcp.tool
@safe_resolve_call
def resolve_list_stills(album_name: str = "") -> str:
    """List stills in a gallery album.

    If *album_name* omitted, uses the current album.

    Args:
        album_name (str): Name of the still album. If omitted, uses the current album.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)

    if album_name:
        albums = g.GetGalleryStillAlbums() or []
        album = None
        for a in albums:
            n = a.GetAlbumName() if hasattr(a, "GetAlbumName") else str(a)
            if n == album_name:
                album = a
                break
        if not album:
            return f"Album '{album_name}' not found."
    else:
        album = g.GetCurrentStillAlbum()
        if not album:
            return "No current still album."

    stills = album.GetStills() or []
    if not stills:
        return "No stills in album."
    return f"{len(stills)} still(s) in album."


@mcp.tool
@safe_resolve_call
def resolve_export_stills(file_path: str, album_name: str = "",
                           format: str = "dpx") -> str:
    """Export all stills from an album to a folder.

    *file_path*: directory to export into.
    *format*: 'dpx', 'cin', 'tif', 'jpg', 'png', 'ppm', 'bmp', 'xpm'.

    Args:
        file_path (str): Directory path to export stills into.
        album_name (str): Name of the still album. If omitted, uses the current album.
        format (str): Output format ('dpx', 'cin', 'tif', 'jpg', 'png', 'ppm', 'bmp', 'xpm'). Defaults to 'dpx'.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)

    if album_name:
        albums = g.GetGalleryStillAlbums() or []
        album = None
        for a in albums:
            n = a.GetAlbumName() if hasattr(a, "GetAlbumName") else str(a)
            if n == album_name:
                album = a
                break
        if not album:
            return f"Album '{album_name}' not found."
    else:
        album = g.GetCurrentStillAlbum()
        if not album:
            return "No current still album."

    stills = album.GetStills() or []
    if not stills:
        return "No stills to export."
    r = album.ExportStills(stills, file_path, format)
    return f"Exported {len(stills)} still(s) to {file_path}" if r else "Export failed."


@mcp.tool
@safe_resolve_call
def resolve_delete_stills(album_name: str = "") -> str:
    """Delete all stills from an album.

    WARNING: Cannot be undone.
    If *album_name* omitted, uses current album.

    Args:
        album_name (str): Name of the still album. If omitted, uses the current album.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)

    if album_name:
        albums = g.GetGalleryStillAlbums() or []
        album = None
        for a in albums:
            n = a.GetAlbumName() if hasattr(a, "GetAlbumName") else str(a)
            if n == album_name:
                album = a
                break
        if not album:
            return f"Album '{album_name}' not found."
    else:
        album = g.GetCurrentStillAlbum()
        if not album:
            return "No current still album."

    stills = album.GetStills() or []
    if not stills:
        return "No stills to delete."
    r = album.DeleteStills(stills)
    return f"Deleted {len(stills)} still(s)." if r else "Delete failed."
