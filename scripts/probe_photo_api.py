#!/usr/bin/env python3
"""
Probe DaVinci Resolve 21's Photo page API at runtime.

Run with Resolve open:
    python3 scripts/probe_photo_api.py

Discovers new/undocumented methods on Resolve, Project, Gallery, and
GalleryStillAlbum objects — especially anything related to the new
Photo page introduced in Resolve 21.
"""

import sys


def get_resolve():
    """Connect to running Resolve instance via scripting API."""
    try:
        import DaVinciResolveScript as dvr
        return dvr.scriptapp("Resolve")
    except ImportError:
        # Add typical macOS scripting path
        sys.path.append(
            "/Library/Application Support/Blackmagic Design"
            "/DaVinci Resolve/Developer/Scripting/Modules"
        )
        try:
            import DaVinciResolveScript as dvr
            return dvr.scriptapp("Resolve")
        except ImportError:
            return None


def introspect(obj, label: str) -> list[str]:
    """List all public methods/attrs on an object."""
    attrs = sorted(a for a in dir(obj) if not a.startswith("_"))
    print(f"\n{'='*60}")
    print(f" {label}: {len(attrs)} public attributes")
    print(f"{'='*60}")
    for a in attrs:
        try:
            val = getattr(obj, a)
            kind = "method" if callable(val) else f"attr={val!r}"
        except Exception:
            kind = "<inaccessible>"
        print(f"  {a:40s}  [{kind}]")
    return attrs


def probe_pages(resolve) -> None:
    """Test which page names Resolve accepts."""
    print(f"\n{'='*60}")
    print(" Page Availability Test")
    print(f"{'='*60}")
    pages = ["media", "cut", "edit", "fusion", "color", "fairlight", "deliver", "photo"]
    for page in pages:
        ok = resolve.OpenPage(page)
        status = "AVAILABLE" if ok else "NOT AVAILABLE"
        print(f"  {page:15s}  {status}")


def main():
    resolve = get_resolve()
    if not resolve:
        print("ERROR: Could not connect to DaVinci Resolve.")
        print("Make sure Resolve is running with scripting enabled:")
        print("  Preferences → System → General → External scripting using = Network")
        sys.exit(1)

    print(f"Connected to Resolve: {resolve.GetVersionString()}")

    introspect(resolve, "Resolve")

    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if project:
        introspect(project, "Project")
        mp = project.GetMediaPool()
        if mp:
            introspect(mp, "MediaPool")

        gallery = project.GetGallery()
        if gallery:
            introspect(gallery, "Gallery")
            albums = gallery.GetGalleryStillAlbums() or []
            if albums:
                introspect(albums[0], "GalleryStillAlbum (first)")

    probe_pages(resolve)

    # Check for any "Photo" related methods across all objects
    print(f"\n{'='*60}")
    print(" Photo/Image keyword search across all objects")
    print(f"{'='*60}")
    search_terms = ["photo", "image", "still", "album", "raw", "nef"]
    objects = {"Resolve": resolve}
    if project:
        objects["Project"] = project
        if project.GetMediaPool():
            objects["MediaPool"] = project.GetMediaPool()
        if project.GetGallery():
            objects["Gallery"] = project.GetGallery()
            albums_list = project.GetGallery().GetGalleryStillAlbums() or []
            if albums_list:
                objects["GalleryStillAlbum"] = albums_list[0]

    for obj_name, obj in objects.items():
        attrs = [a for a in dir(obj) if not a.startswith("_")]
        for term in search_terms:
            matches = [a for a in attrs if term in a.lower()]
            if matches:
                print(f"  {obj_name}.* matching '{term}': {', '.join(matches)}")


if __name__ == "__main__":
    main()
