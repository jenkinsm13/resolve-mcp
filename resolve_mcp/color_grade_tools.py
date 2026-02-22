"""Color grading tools: LUTs, CDL, node graph, grade reset."""

import json

from .config import mcp
from .resolve import _boilerplate


def _current_item(project):
    """Return the currently selected timeline item on the color page, or None."""
    tl = project.GetCurrentTimeline()
    if not tl:
        return None
    return tl.GetCurrentVideoItem()


@mcp.tool
def resolve_apply_lut(lut_path: str, node_index: int = 1) -> str:
    """Apply a LUT file to a specific node on the current clip's grade.

    *lut_path*: absolute path to a .cube, .3dl, or .dat LUT file.
    *node_index*: 1-based node index in the node graph.

    Must be on the Color page with a clip selected.
    """
    _, project, _ = _boilerplate()
    item = _current_item(project)
    if not item:
        return "No clip selected. Switch to Color page and select a clip."

    node_graph = item.GetNodeGraph()
    if not node_graph:
        return "Cannot access node graph for current clip."

    num_nodes = node_graph.GetNumNodes()
    if node_index < 1 or node_index > num_nodes:
        return f"Node index {node_index} out of range (1–{num_nodes})."

    result = node_graph.SetLUT(node_index, lut_path)
    if result:
        return f"LUT applied to node {node_index}: {lut_path}"
    return "Failed to apply LUT. Check file path and format."


@mcp.tool
def resolve_get_lut(node_index: int = 1) -> str:
    """Get the LUT path applied to a specific node on the current clip."""
    _, project, _ = _boilerplate()
    item = _current_item(project)
    if not item:
        return "No clip selected."

    node_graph = item.GetNodeGraph()
    if not node_graph:
        return "Cannot access node graph."

    lut = node_graph.GetLUT(node_index)
    if lut:
        return f"Node {node_index} LUT: {lut}"
    return f"No LUT on node {node_index}."


@mcp.tool
def resolve_set_cdl(node_index: int, slope_r: float, slope_g: float,
                    slope_b: float, offset_r: float, offset_g: float,
                    offset_b: float, power_r: float, power_g: float,
                    power_b: float, saturation: float) -> str:
    """Set CDL (Color Decision List) values on the current clip.

    Standard neutral values: slope=1.0, offset=0.0, power=1.0, saturation=1.0
    """
    _, project, _ = _boilerplate()
    item = _current_item(project)
    if not item:
        return "No clip selected."

    cdl = {
        "NodeIndex": str(node_index),
        "Slope": f"{slope_r} {slope_g} {slope_b}",
        "Offset": f"{offset_r} {offset_g} {offset_b}",
        "Power": f"{power_r} {power_g} {power_b}",
        "Saturation": str(saturation),
    }
    result = item.SetCDL(cdl)
    return f"CDL set on node {node_index}." if result else "Failed to set CDL values."


@mcp.tool
def resolve_get_cdl(node_index: int = 1) -> str:
    """Get CDL values from the current clip as JSON."""
    _, project, _ = _boilerplate()
    item = _current_item(project)
    if not item:
        return "No clip selected."

    cdl = item.GetCDL()
    if cdl:
        return json.dumps(cdl, indent=2, default=str)
    return "No CDL data available."


@mcp.tool
def resolve_get_node_count() -> str:
    """Get the number of nodes in the current clip's grade."""
    _, project, _ = _boilerplate()
    item = _current_item(project)
    if not item:
        return "No clip selected."

    node_graph = item.GetNodeGraph()
    if not node_graph:
        return "Cannot access node graph."

    count = node_graph.GetNumNodes()
    return f"Current clip has {count} node(s)."


@mcp.tool
def resolve_reset_grades() -> str:
    """Reset all grades on the current clip to neutral (removes all corrections)."""
    _, project, _ = _boilerplate()
    item = _current_item(project)
    if not item:
        return "No clip selected."

    item.ClearFlags()
    node_graph = item.GetNodeGraph()
    if node_graph:
        num = node_graph.GetNumNodes()
        neutral_cdl = {
            "Slope": "1.0 1.0 1.0",
            "Offset": "0.0 0.0 0.0",
            "Power": "1.0 1.0 1.0",
            "Saturation": "1.0",
        }
        for i in range(1, num + 1):
            neutral_cdl["NodeIndex"] = str(i)
            item.SetCDL(neutral_cdl)
            node_graph.SetLUT(i, "")
        return f"Reset {num} node(s) to neutral."
    return "Could not access node graph."
