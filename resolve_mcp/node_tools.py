"""
Advanced node graph tools — labels, node enable/disable, tool inspection.

For a colorist: these control the individual nodes in the grade tree,
letting you toggle corrections, label nodes for organization, and
inspect what OFX/ResolveFX tools are loaded per node.
"""

import json

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate


def _graph(project):
    """Get the node graph for the current clip on the Color page."""
    tl = project.GetCurrentTimeline()
    if not tl:
        raise ValueError("No active timeline.")
    item = tl.GetCurrentVideoItem()
    if not item:
        raise ValueError("No clip selected — switch to Color page.")
    ng = item.GetNodeGraph()
    if not ng:
        raise ValueError("Cannot access node graph.")
    return ng


# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_node_get_label(node_index: int) -> str:
    """Get the label/name of a specific node in the grade.

    *node_index*: 1-based. Use resolve_get_node_count() first.
    Node labels help colorists organize complex grades (e.g. 'Skin',
    'Sky Key', 'Vignette', 'Film Print Emulation').

    Args:
        node_index (int): 1-based node index in the grade tree.
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    label = ng.GetNodeLabel(node_index)
    return f"Node {node_index}: '{label}'" if label else f"Node {node_index} has no label."


@mcp.tool
@safe_resolve_call
def resolve_node_set_enabled(node_index: int, enabled: bool = True) -> str:
    """Enable or disable a node in the grade.

    Disabling a node bypasses its correction — essential for A/B
    comparing individual corrections during a grading session.

    Args:
        node_index (int): 1-based node index in the grade tree.
        enabled (bool): Whether to enable (True) or disable (False) the node. Defaults to True.
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    r = ng.SetNodeEnabled(node_index, enabled)
    state = "enabled" if enabled else "disabled"
    return f"Node {node_index} {state}." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_node_get_enabled(node_index: int) -> str:
    """Check if a node is enabled or bypassed.

    Args:
        node_index (int): 1-based node index in the grade tree.
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    r = ng.GetNodeEnabled(node_index)
    state = "enabled" if r else "disabled/bypassed"
    return f"Node {node_index}: {state}"


@mcp.tool
@safe_resolve_call
def resolve_node_get_tools(node_index: int) -> str:
    """List OFX/ResolveFX tools loaded in a specific node.

    Returns tool IDs and names — useful for checking what effects
    (noise reduction, sharpening, film grain, glow, etc.) are applied.

    Args:
        node_index (int): 1-based node index in the grade tree.
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    tools = ng.GetToolsInNode(node_index)
    if not tools:
        return f"No tools in node {node_index}."
    if isinstance(tools, dict):
        return json.dumps(tools, indent=2, default=str)
    return str(tools)


@mcp.tool
@safe_resolve_call
def resolve_node_overview() -> str:
    """Full overview of all nodes in the current clip's grade.

    Shows each node's index, label, enabled state, LUT, and tools.
    A colorist's quick-glance summary of the entire grade stack.

    Args: None
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    count = ng.GetNumNodes()
    if not count:
        return "No nodes."
    lines = [f"{count} node(s) in grade:"]
    for i in range(1, count + 1):
        label = ng.GetNodeLabel(i) or "(unlabeled)"
        enabled = ng.GetNodeEnabled(i)
        lut = ng.GetLUT(i) or "none"
        tools = ng.GetToolsInNode(i)
        tool_ct = len(tools) if isinstance(tools, (dict, list)) else 0
        state = "ON" if enabled else "OFF"
        lines.append(f"  {i}. [{state}] {label} | LUT: {lut} | {tool_ct} tool(s)")
    return "\n".join(lines)
