"""
Photo page tools for DaVinci Resolve 21+.

The Photo page is new in Resolve 21 (April 2026). These tools provide
basic Photo page navigation, album management, and a runtime API probe
for discovering undocumented methods as the scripting API evolves.
"""

import os

from .config import mcp, IMAGE_EXTS
from .errors import safe_resolve_call
from .resolve import _boilerplate, get_resolve


@mcp.tool
@safe_resolve_call
def resolve_open_photo_page() -> str:
    """Switch DaVinci Resolve to the Photo page.

    Resolve 21+ only. Returns an error message on older versions
    where 'photo' is not a recognized page name.

    Args: None
    """
    resolve = get_resolve()
    if not resolve:
        raise ValueError("DaVinci Resolve is not running.")
    result = resolve.OpenPage("photo")
    if result:
        return "Switched to Photo page."
    current = resolve.GetCurrentPage()
    return (
        f"OpenPage('photo') returned False (current page: {current}). "
        "Photo page may not be available in this Resolve version."
    )


@mcp.tool
@safe_resolve_call
def resolve_get_current_page() -> str:
    """Return the name of the currently active Resolve page.

    Useful to confirm Photo page is active before photo-specific operations.

    Args: None
    """
    resolve = get_resolve()
    if not resolve:
        raise ValueError("DaVinci Resolve is not running.")
    page = resolve.GetCurrentPage()
    return f"Current page: {page}"


@mcp.tool
@safe_resolve_call
def resolve_photo_import_to_album(
    album_name: str,
    image_paths: list[str],
    create_if_missing: bool = True,
) -> str:
    """Import image files into a gallery still album.

    Creates the album if it doesn't exist and *create_if_missing* is True.
    Works on any page — does not require Photo page to be active.

    Args:
        album_name (str): Name of the target gallery still album.
        image_paths (list[str]): Absolute paths to image files to import.
        create_if_missing (bool): Create album if it doesn't exist. Default True.
    """
    _, project, _ = _boilerplate()
    gallery = project.GetGallery()
    if not gallery:
        raise ValueError("Cannot access gallery.")

    valid = [p for p in image_paths if os.path.isfile(p)]
    if not valid:
        return "No valid image files provided."

    albums = gallery.GetGalleryStillAlbums() or []
    album = None
    for a in albums:
        name = a.GetAlbumName() if hasattr(a, "GetAlbumName") else str(a)
        if name == album_name:
            album = a
            break

    if not album and create_if_missing:
        album = gallery.CreateGalleryStillAlbum(album_name)
        if not album:
            return f"Failed to create album '{album_name}'."

    if not album:
        return f"Album '{album_name}' not found."

    gallery.SetCurrentStillAlbum(album)

    if hasattr(album, "ImportStills"):
        result = album.ImportStills(valid)
        if result:
            return f"Imported {len(valid)} image(s) into album '{album_name}'."

    return (
        f"ImportStills not available on this Resolve version. "
        f"Album '{album_name}' exists with {len(valid)} file(s) staged."
    )


@mcp.tool
@safe_resolve_call
def resolve_photo_probe_api() -> str:
    """Probe the Resolve scripting API for Photo-page-related methods.

    Introspects the Resolve, Project, Gallery, and GalleryStillAlbum
    objects to discover any new methods. Useful for exploring Resolve 21
    Photo page capabilities before official docs are published.

    Args: None
    """
    resolve = get_resolve()
    if not resolve:
        raise ValueError("DaVinci Resolve is not running.")

    sections: list[str] = []

    resolve_attrs = sorted(a for a in dir(resolve) if not a.startswith("_"))
    photo_related = [a for a in resolve_attrs if "photo" in a.lower() or "image" in a.lower()]
    sections.append(f"Resolve object: {len(resolve_attrs)} methods")
    if photo_related:
        sections.append(f"  Photo/Image related: {', '.join(photo_related)}")

    project = resolve.GetProjectManager().GetCurrentProject()
    if project:
        proj_attrs = sorted(a for a in dir(project) if not a.startswith("_"))
        photo_proj = [a for a in proj_attrs if "photo" in a.lower() or "image" in a.lower()]
        sections.append(f"Project object: {len(proj_attrs)} methods")
        if photo_proj:
            sections.append(f"  Photo/Image related: {', '.join(photo_proj)}")

        gallery = project.GetGallery()
        if gallery:
            gal_attrs = sorted(a for a in dir(gallery) if not a.startswith("_"))
            photo_gal = [a for a in gal_attrs if "photo" in a.lower() or "image" in a.lower() or "album" in a.lower()]
            sections.append(f"Gallery object: {len(gal_attrs)} methods")
            if photo_gal:
                sections.append(f"  Photo/Image/Album related: {', '.join(photo_gal)}")
            sections.append(f"  All methods: {', '.join(gal_attrs)}")

            albums = gallery.GetGalleryStillAlbums() or []
            if albums:
                album_attrs = sorted(a for a in dir(albums[0]) if not a.startswith("_"))
                sections.append(f"GalleryStillAlbum object: {len(album_attrs)} methods")
                sections.append(f"  All methods: {', '.join(album_attrs)}")

    pages_test = []
    for page in ["media", "cut", "edit", "fusion", "color", "fairlight", "deliver", "photo"]:
        ok = resolve.OpenPage(page)
        pages_test.append(f"  {page}: {'✓' if ok else '✗'}")
    sections.append("Page availability:")
    sections.extend(pages_test)

    return "\n".join(sections)
