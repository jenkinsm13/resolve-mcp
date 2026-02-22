"""
TimelineItem version management, color group assignment,
grade-from-still, and stereo convergence.
"""

import json

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate


def _item(project, track_type, track_index, item_index):
    tl = project.GetCurrentTimeline()
    if not tl:
        raise ValueError("No active timeline.")
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index)) or []
    idx = int(item_index) - 1
    if idx < 0 or idx >= len(items):
        raise ValueError(f"Item index {item_index} out of range (1–{len(items)}).")
    return items[idx]


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_item_list_versions(track_type: str, track_index: int,
                                item_index: int) -> str:
    """List all clip versions on a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_item_add_version, resolve_item_load_version
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    names = it.GetVersionNameList() or []
    current = it.GetCurrentVersion()
    if not names:
        return "No versions."
    lines = [f"{len(names)} version(s):"]
    for n in names:
        marker = " ← active" if current and n == current.get("versionName", "") else ""
        lines.append(f"  • {n}{marker}")
    return "\n".join(lines)


@mcp.tool
@safe_resolve_call
def resolve_item_add_version(track_type: str, track_index: int,
                              item_index: int, version_name: str,
                              version_type: int = 0) -> str:
    """Create a new clip version.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        version_name: Name for the new version.
        version_type: 0 = local, 1 = remote (default 0).

    See also: resolve_item_load_version, resolve_item_delete_version
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.AddVersion(version_name, version_type)
    return f"Version '{version_name}' created." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_load_version(track_type: str, track_index: int,
                               item_index: int, version_name: str,
                               version_type: int = 0) -> str:
    """Switch to a specific clip version.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        version_name: Name of the version to load.
        version_type: 0 = local, 1 = remote (default 0).

    See also: resolve_item_list_versions, resolve_item_add_version
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.LoadVersionByName(version_name, version_type)
    return f"Loaded version '{version_name}'." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_delete_version(track_type: str, track_index: int,
                                 item_index: int, version_name: str,
                                 version_type: int = 0) -> str:
    """Delete a clip version.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        version_name: Name of the version to delete.
        version_type: 0 = local, 1 = remote (default 0).

    See also: resolve_item_list_versions, resolve_item_load_version
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.DeleteVersionByName(version_name, version_type)
    return f"Deleted version '{version_name}'." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_rename_version(track_type: str, track_index: int,
                                 item_index: int, old_name: str,
                                 new_name: str,
                                 version_type: int = 0) -> str:
    """Rename a clip version.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        old_name: Current version name.
        new_name: New version name.
        version_type: 0 = local, 1 = remote (default 0).

    See also: resolve_item_list_versions, resolve_item_load_version
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.RenameVersionByName(old_name, new_name, version_type)
    return f"Renamed '{old_name}' → '{new_name}'." if r else "Failed."


# ---------------------------------------------------------------------------
# Color group assignment
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_item_get_color_group(track_type: str, track_index: int,
                                  item_index: int) -> str:
    """Get the color group assigned to a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_item_set_color_group
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    cg = it.GetColorGroup()
    if cg:
        name = cg.GetName() if hasattr(cg, "GetName") else str(cg)
        return f"Color group: {name}"
    return "No color group assigned."


@mcp.tool
@safe_resolve_call
def resolve_item_set_color_group(track_type: str, track_index: int,
                                  item_index: int,
                                  group_name: str) -> str:
    """Assign a color group to a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        group_name: Name of the color group to assign.

    See also: resolve_item_get_color_group, resolve_list_color_groups
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)

    groups = project.GetColorGroupsList() or []
    target = None
    for g in groups:
        gn = g.GetName() if hasattr(g, "GetName") else str(g)
        if gn == group_name:
            target = g
            break
    if not target:
        return f"Color group '{group_name}' not found."
    r = it.SetColorGroup(target)
    return f"Assigned color group '{group_name}'." if r else "Failed."


# ---------------------------------------------------------------------------
# Grade from still / gallery
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_item_assign_grade_from_album(track_type: str, track_index: int,
                                          item_index: int,
                                          still_index: int = 0) -> str:
    """Apply grade from a gallery still to a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        still_index: 0-based index into the current still album (default 0).

    Note:
        Uses the current still album from the project gallery.
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    gallery = project.GetGallery()
    if not gallery:
        return "Cannot access gallery."
    album = gallery.GetCurrentStillAlbum()
    if not album:
        return "No current still album."
    stills = album.GetStills() or []
    if still_index >= len(stills):
        return f"Still index {still_index} out of range (0–{len(stills)-1})."
    r = it.AssignStillFromGallery(stills[still_index])
    return "Grade applied from still." if r else "Failed."


# ---------------------------------------------------------------------------
# Stereo convergence (niche — 3D workflows)
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_item_get_stereo_convergence(track_type: str, track_index: int,
                                         item_index: int) -> str:
    """Get stereo convergence values for a 3D timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    Note:
        Returns stereo convergence data for 3D workflows. Only populated for
        items in stereo timelines.
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    vals = it.GetStereoConvergenceValues()
    if vals:
        return json.dumps(vals, indent=2, default=str)
    return "No stereo convergence data (not a stereo timeline?)."
