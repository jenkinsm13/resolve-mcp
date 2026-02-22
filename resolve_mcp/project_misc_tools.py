"""Project misc tools: presets, LUT refresh, render mode, color groups, product name."""

import json

from .config import mcp
from .resolve import _boilerplate, get_resolve


@mcp.tool
def resolve_get_project_presets() -> str:
    """List available project presets (resolution/fps/color science combos)."""
    _, project, _ = _boilerplate()
    presets = project.GetPresetList()
    if not presets:
        return "No project presets."
    return "\n".join(f"  • {p}" for p in presets)


@mcp.tool
def resolve_apply_project_preset(preset_name: str) -> str:
    """Apply a project preset to the current project.

    Changes resolution, frame rate, color science, etc.
    """
    _, project, _ = _boilerplate()
    r = project.SetPreset(preset_name)
    return f"Applied preset '{preset_name}'." if r else "Failed."


@mcp.tool
def resolve_save_render_preset(preset_name: str) -> str:
    """Save current render settings as a new named preset."""
    _, project, _ = _boilerplate()
    r = project.SaveAsNewRenderPreset(preset_name)
    return f"Saved render preset '{preset_name}'." if r else "Failed."


@mcp.tool
def resolve_get_render_resolutions(format_name: str, codec_name: str) -> str:
    """Get available render resolutions for a format/codec combination.

    Returns list of {Width, Height} dicts.
    """
    _, project, _ = _boilerplate()
    res = project.GetRenderResolutions(format_name, codec_name)
    if not res:
        return "No resolutions available for that format/codec."
    return json.dumps(res, indent=2)


@mcp.tool
def resolve_refresh_lut_list() -> str:
    """Refresh the list of available LUTs.

    Call this after adding new LUT files to the LUT directories.
    """
    _, project, _ = _boilerplate()
    r = project.RefreshLUTList()
    return "LUT list refreshed." if r else "Failed."


@mcp.tool
def resolve_get_project_id() -> str:
    """Get the unique ID of the current project."""
    _, project, _ = _boilerplate()
    uid = project.GetUniqueId()
    return f"Project unique ID: {uid}" if uid else "Could not retrieve."


@mcp.tool
def resolve_delete_color_group(group_name: str) -> str:
    """Delete a color group from the project."""
    _, project, _ = _boilerplate()
    groups = project.GetColorGroupsList() or []
    for g in groups:
        name = g.GetName() if hasattr(g, "GetName") else str(g)
        if name == group_name:
            r = project.DeleteColorGroup(g)
            return f"Deleted color group '{group_name}'." if r else "Failed."
    return f"Color group '{group_name}' not found."


@mcp.tool
def resolve_get_render_mode() -> str:
    """Get the current render mode (Individual Clips or Single Clip)."""
    _, project, _ = _boilerplate()
    mode = project.GetCurrentRenderMode()
    return f"Render mode: {mode}" if mode is not None else "Could not retrieve."


@mcp.tool
def resolve_set_render_mode(mode: int) -> str:
    """Set the render mode. 0 = Individual Clips, 1 = Single Clip."""
    _, project, _ = _boilerplate()
    r = project.SetCurrentRenderMode(mode)
    label = "Individual Clips" if mode == 0 else "Single Clip"
    return f"Render mode set to {label}." if r else "Failed."


@mcp.tool
def resolve_get_product_name() -> str:
    """Get the Resolve product name (DaVinci Resolve / DaVinci Resolve Studio)."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Resolve not running."
    name = resolve.GetProductName()
    return name if name else "Could not retrieve."
