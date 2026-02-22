"""Layout preset tools: load/save/update/delete/export/import + burn-in/render presets."""

from .config import mcp
from .resolve import get_resolve


@mcp.tool
def resolve_load_layout_preset(preset_name: str) -> str:
    """Load a UI layout preset (e.g. 'Color Grading', 'Dual Screen Edit')."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.LoadLayoutPreset(preset_name)
    return f"Layout '{preset_name}' loaded." if r else "Failed — check preset name."


@mcp.tool
def resolve_save_layout_preset(preset_name: str) -> str:
    """Save the current UI layout as a named preset."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.SaveLayoutPreset(preset_name)
    return f"Layout saved as '{preset_name}'." if r else "Failed."


@mcp.tool
def resolve_update_layout_preset(preset_name: str) -> str:
    """Overwrite an existing layout preset with the current layout."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.UpdateLayoutPreset(preset_name)
    return f"Layout '{preset_name}' updated." if r else "Failed."


@mcp.tool
def resolve_delete_layout_preset(preset_name: str) -> str:
    """Delete a layout preset."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.DeleteLayoutPreset(preset_name)
    return f"Layout '{preset_name}' deleted." if r else "Failed."


@mcp.tool
def resolve_export_layout_preset(preset_name: str, file_path: str) -> str:
    """Export a layout preset to a file for sharing across workstations."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.ExportLayoutPreset(preset_name, file_path)
    return f"Exported layout → {file_path}" if r else "Failed."


@mcp.tool
def resolve_import_layout_preset(file_path: str, preset_name: str = "") -> str:
    """Import a layout preset from file."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.ImportLayoutPreset(file_path, preset_name) if preset_name else resolve.ImportLayoutPreset(file_path)
    return f"Layout imported from {file_path}" if r else "Failed."


@mcp.tool
def resolve_import_render_preset(file_path: str) -> str:
    """Import a render preset from file (.xml).

    Useful for sharing delivery specs (Netflix, YouTube, broadcast) across editing suites.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.ImportRenderPreset(file_path)
    return f"Render preset imported from {file_path}" if r else "Failed."


@mcp.tool
def resolve_export_render_preset(preset_name: str, file_path: str) -> str:
    """Export a render preset to file for sharing."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.ExportRenderPreset(preset_name, file_path)
    return f"Exported render preset → {file_path}" if r else "Failed."


@mcp.tool
def resolve_import_burn_in_preset(file_path: str) -> str:
    """Import a burn-in preset (TC overlay, slate info for dailies/review)."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.ImportBurnInPreset(file_path)
    return "Burn-in preset imported." if r else "Failed."


@mcp.tool
def resolve_export_burn_in_preset(preset_name: str, file_path: str) -> str:
    """Export a burn-in preset to file."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    r = resolve.ExportBurnInPreset(preset_name, file_path)
    return f"Exported burn-in preset → {file_path}" if r else "Failed."
