"""
Quick Export MCP tools.

Provides fast rendering using Quick Export presets (YouTube, Vimeo, etc.)
without configuring full render settings.
"""

from .config import mcp
from .resolve import _boilerplate


@mcp.tool
def resolve_get_quick_export_presets() -> str:
    """List all available Quick Export render presets.

    Quick Export provides one-click rendering to platforms like YouTube,
    Vimeo, Twitter, etc. Returns preset names that can be passed to
    resolve_quick_export.
    """
    _, project, _ = _boilerplate()
    presets = project.GetQuickExportRenderPresets()
    if not presets:
        return "No Quick Export presets available."

    lines = [f"{len(presets)} Quick Export preset(s):"]
    for p in presets:
        lines.append(f"  • {p}")
    return "\n".join(lines)


@mcp.tool
def resolve_quick_export(preset_name: str, output_path: str) -> str:
    """Render the current timeline using a Quick Export preset.

    *preset_name*: name from resolve_get_quick_export_presets
                   (e.g. 'YouTube', 'Vimeo', 'H.264 Master').
    *output_path*: absolute path for the rendered file.

    This is faster than setting up a full render job — ideal for quick
    dailies, review copies, and social media uploads.
    """
    _, project, _ = _boilerplate()
    result = project.RenderWithQuickExport(preset_name, output_path)
    if result:
        return f"Quick Export started with preset '{preset_name}' → {output_path}"
    return f"Quick Export failed. Check preset name '{preset_name}' and output path."
