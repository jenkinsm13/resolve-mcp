"""
Fusion composition management on TimelineItems.

Create, import, export, delete, rename, and list Fusion comps
attached to clips on the timeline.
"""

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


@mcp.tool
@safe_resolve_call
def resolve_item_list_fusion_comps(track_type: str, track_index: int, item_index: int) -> str:
    """List all Fusion compositions on a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_item_add_fusion_comp, resolve_item_delete_fusion_comp
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    names = it.GetFusionCompNameList() or []
    count = it.GetFusionCompCount()
    if not names:
        return "No Fusion compositions."
    return f"{count} comp(s): " + ", ".join(names)


@mcp.tool
@safe_resolve_call
def resolve_item_add_fusion_comp(track_type: str, track_index: int, item_index: int) -> str:
    """Create a new Fusion composition on a timeline item.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.

    See also: resolve_item_list_fusion_comps, resolve_item_delete_fusion_comp
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    comp = it.AddFusionComp()
    return "Fusion comp added." if comp else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_import_fusion_comp(track_type: str, track_index: int, item_index: int, file_path: str) -> str:
    """Import a Fusion composition from a .comp file.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        file_path: Path to the .comp file to import.

    See also: resolve_item_export_fusion_comp, resolve_item_list_fusion_comps
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.ImportFusionComp(file_path)
    return f"Imported Fusion comp from {file_path}" if r else "Import failed."


@mcp.tool
@safe_resolve_call
def resolve_item_export_fusion_comp(
    track_type: str, track_index: int, item_index: int, comp_name: str, file_path: str
) -> str:
    """Export a Fusion composition to a .comp file.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        comp_name: Name of the composition to export.
        file_path: Destination path for the .comp file.

    See also: resolve_item_import_fusion_comp, resolve_item_list_fusion_comps
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.ExportFusionComp(comp_name, file_path)
    return f"Exported '{comp_name}' → {file_path}" if r else "Export failed."


@mcp.tool
@safe_resolve_call
def resolve_item_delete_fusion_comp(track_type: str, track_index: int, item_index: int, comp_name: str) -> str:
    """Delete a Fusion composition by name.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        comp_name: Name of the composition to delete.

    See also: resolve_item_list_fusion_comps, resolve_item_add_fusion_comp
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.DeleteFusionCompByName(comp_name)
    return f"Deleted Fusion comp '{comp_name}'." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_load_fusion_comp(track_type: str, track_index: int, item_index: int, comp_name: str) -> str:
    """Load/select a Fusion composition by name.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        comp_name: Name of the composition to load.

    See also: resolve_item_list_fusion_comps, resolve_item_rename_fusion_comp
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.LoadFusionCompByName(comp_name)
    return f"Loaded '{comp_name}'." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_item_rename_fusion_comp(
    track_type: str, track_index: int, item_index: int, old_name: str, new_name: str
) -> str:
    """Rename a Fusion composition.

    Args:
        track_type: Track type — 'video', 'audio', or 'subtitle'.
        track_index: 1-based track number.
        item_index: 1-based item position on the track.
        old_name: Current composition name.
        new_name: New composition name.

    See also: resolve_item_list_fusion_comps, resolve_item_load_fusion_comp
    """
    _, project, _ = _boilerplate()
    it = _item(project, track_type, track_index, item_index)
    r = it.RenameFusionCompByName(old_name, new_name)
    return f"Renamed '{old_name}' → '{new_name}'." if r else "Failed."
