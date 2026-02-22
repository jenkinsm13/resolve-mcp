"""
Advanced node graph tools — labels, node enable/disable, tool inspection,
and node creation (serial, parallel, layer).

For a colorist: these control the individual nodes in the grade tree,
letting you toggle corrections, label nodes for organization, build
node structures, and inspect what OFX/ResolveFX tools are loaded per node.
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
# Node creation & labelling
# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_node_set_label(node_index: int, label: str) -> str:
    """Set the label/name of a node in the grade.

    Labels help organise complex grades — e.g. 'Balance', 'Skin',
    'Sky Key', 'Look', 'CST'.  Every professional node tree uses labels.

    Args:
        node_index (int): 1-based node index in the grade tree.
        label (str): The label text to set on the node.
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    result = ng.SetNodeLabel(node_index, label)
    if result:
        return f"Node {node_index} labelled '{label}'."
    return f"Failed to label node {node_index}."


@mcp.tool
@safe_resolve_call
def resolve_node_add_serial(ref_node_index: int = 0) -> str:
    """Add a serial (corrector) node after the specified node.

    A serial node is the most common node type — corrections flow through
    them left to right.  Pass 0 to append at the end of the chain.

    Returns the new node's index.

    Args:
        ref_node_index (int): The node to insert after (1-based). 0 = append at end.
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    if ref_node_index == 0:
        ref_node_index = ng.GetNumNodes()
    new_idx = ng.AddSerialNode(ref_node_index)
    if new_idx:
        return f"Serial node added after node {ref_node_index}. New node index: {new_idx}"
    return "Failed to add serial node."


@mcp.tool
@safe_resolve_call
def resolve_node_add_parallel(ref_node_index: int) -> str:
    """Add a parallel node alongside the specified node.

    Parallel nodes process the same input independently and their
    outputs are combined — useful for separate secondary corrections
    (e.g. skin + sky in parallel).

    Returns the new node's index.

    Args:
        ref_node_index (int): The reference node to create a parallel branch from (1-based).
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    new_idx = ng.AddParallelNode(ref_node_index)
    if new_idx:
        return f"Parallel node added alongside node {ref_node_index}. New node index: {new_idx}"
    return "Failed to add parallel node."


@mcp.tool
@safe_resolve_call
def resolve_node_add_layer(ref_node_index: int) -> str:
    """Add a layer mixer node on top of the specified node.

    Layer nodes stack on top of each other — the output is blended
    via a layer mixer.  Used for overlay effects, key-based composites,
    and outside-node corrections.

    Returns the new node's index.

    Args:
        ref_node_index (int): The reference node to layer on top of (1-based).
    """
    _, project, _ = _boilerplate()
    ng = _graph(project)
    new_idx = ng.AddLayerNode(ref_node_index)
    if new_idx:
        return f"Layer node added on top of node {ref_node_index}. New node index: {new_idx}"
    return "Failed to add layer node."


# ---------------------------------------------------------------------------
# Node inspection
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
        tool_ct = len(tools) if isinstance(tools, dict | list) else 0
        state = "ON" if enabled else "OFF"
        lines.append(f"  {i}. [{state}] {label} | LUT: {lut} | {tool_ct} tool(s)")
    return "\n".join(lines)
