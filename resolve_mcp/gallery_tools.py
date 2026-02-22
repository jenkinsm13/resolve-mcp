"""
Gallery, GalleryStillAlbum, and GalleryStill management.

Browse albums, export/delete stills, rename albums, create albums,
import stills, manage power grade albums, and label stills.
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


# ---------------------------------------------------------------------------
# Album creation
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_create_still_album(album_name: str = "") -> str:
    """Create a new gallery still album.

    *album_name*: optional name for the album (rename after creation).
    Returns the new album.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)
    album = g.CreateGalleryStillAlbum()
    if not album:
        return "Failed to create still album."
    if album_name:
        g.SetAlbumName(album, album_name)
    return f"Created still album{' ' + repr(album_name) if album_name else ''}."


@mcp.tool
@safe_resolve_call
def resolve_create_power_grade_album(album_name: str = "") -> str:
    """Create a new PowerGrade album in the gallery.

    PowerGrade albums store grades that persist across projects.
    *album_name*: optional name for the album.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)
    album = g.CreateGalleryPowerGradeAlbum()
    if not album:
        return "Failed to create PowerGrade album."
    if album_name:
        g.SetAlbumName(album, album_name)
    return f"Created PowerGrade album{' ' + repr(album_name) if album_name else ''}."


@mcp.tool
@safe_resolve_call
def resolve_list_power_grade_albums() -> str:
    """List all PowerGrade albums in the gallery.

    PowerGrade albums persist across projects and contain reusable grades.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)
    albums = g.GetGalleryPowerGradeAlbums() or []
    if not albums:
        return "No PowerGrade albums."
    lines = [f"{len(albums)} PowerGrade album(s):"]
    for a in albums:
        name = g.GetAlbumName(a) if hasattr(g, "GetAlbumName") else str(a)
        lines.append(f"  • {name}")
    return "\n".join(lines)


@mcp.tool
@safe_resolve_call
def resolve_import_stills(file_paths: str, album_name: str = "") -> str:
    """Import still images into a gallery album.

    *file_paths*: comma-separated absolute paths to still image files.
    *album_name*: target album (empty = current album).
    Supported formats: dpx, cin, tif, jpg, png, ppm, bmp, xpm, drx.
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)

    if album_name:
        albums = g.GetGalleryStillAlbums() or []
        album = None
        for a in albums:
            n = g.GetAlbumName(a) if hasattr(g, "GetAlbumName") else str(a)
            if n == album_name:
                album = a
                break
        if not album:
            return f"Album '{album_name}' not found."
    else:
        album = g.GetCurrentStillAlbum()
        if not album:
            return "No current still album."

    paths = [p.strip() for p in file_paths.split(",")]
    result = album.ImportStills(paths)
    if result:
        return f"Imported {len(paths)} still(s) into album."
    return "Failed to import stills."


@mcp.tool
@safe_resolve_call
def resolve_set_still_label(label: str, still_index: int = 1,
                              album_name: str = "") -> str:
    """Set a label on a gallery still.

    *label*: the label text.
    *still_index*: 1-based index of the still in the album.
    *album_name*: target album (empty = current album).
    """
    _, project, _ = _boilerplate()
    g = _gallery(project)

    if album_name:
        albums = g.GetGalleryStillAlbums() or []
        album = None
        for a in albums:
            n = g.GetAlbumName(a) if hasattr(g, "GetAlbumName") else str(a)
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
    if still_index < 1 or still_index > len(stills):
        return f"Still index {still_index} out of range (1-{len(stills)})."

    still = stills[still_index - 1]
    result = album.SetLabel(still, label)
    if result:
        return f"Label set to '{label}' on still {still_index}."
    return f"Failed to set label on still {still_index}."
