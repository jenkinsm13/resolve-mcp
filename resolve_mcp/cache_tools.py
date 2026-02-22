"""
Cache control MCP tools.

Covers: Color output cache, Fusion output cache, and per-node cache modes.
These are critical for playback performance and render optimization.
"""

from .config import mcp
from .resolve import _boilerplate

# ---------------------------------------------------------------------------
# Cache value mappings
# ---------------------------------------------------------------------------

_CACHE_VALUES = {
    "auto": -1,  # CACHE_AUTO_ENABLED  (Fusion only)
    "off": 0,  # CACHE_DISABLED
    "on": 1,  # CACHE_ENABLED
}

_CACHE_LABELS = {-1: "Auto", 0: "Off", 1: "On"}


def _get_current_item():
    """Return the current timeline item on the Color page."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        raise ValueError("No active timeline.")
    item = tl.GetCurrentVideoItem()
    if not item:
        raise ValueError("No current video item. Navigate to a clip on the Color page.")
    return item, tl, project


# ---------------------------------------------------------------------------
# Timeline Item cache tools
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_get_color_cache(track_type: str = "video", track_index: int = 1, item_index: int = 0) -> str:
    """Check if Color Output Cache is enabled for a timeline clip.

    *item_index*: 0 = current clip (Color page), or 1-based clip index on track.
    Returns the cache state.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    if item_index == 0:
        item = tl.GetCurrentVideoItem()
        if not item:
            return "No current clip. Navigate to a clip on the Color page."
    else:
        items = tl.GetItemListInTrack(track_type, int(track_index)) or []
        if item_index < 1 or item_index > len(items):
            return f"Item index {item_index} out of range (1-{len(items)})."
        item = items[item_index - 1]

    val = item.GetIsColorOutputCacheEnabled()
    label = _CACHE_LABELS.get(val, str(val))
    name = item.GetName() or f"clip {item_index}"
    return f"Color output cache for '{name}': {label}"


@mcp.tool
def resolve_set_color_cache(enabled: bool, track_type: str = "video", track_index: int = 1, item_index: int = 0) -> str:
    """Enable or disable Color Output Cache for a timeline clip.

    *enabled*: True to enable, False to disable.
    *item_index*: 0 = current clip (Color page), or 1-based clip index.
    Equivalent to right-click → Render Cache Color Output.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    if item_index == 0:
        item = tl.GetCurrentVideoItem()
        if not item:
            return "No current clip."
    else:
        items = tl.GetItemListInTrack(track_type, int(track_index)) or []
        if item_index < 1 or item_index > len(items):
            return f"Item index {item_index} out of range."
        item = items[item_index - 1]

    cache_val = 1 if enabled else 0
    result = item.SetColorOutputCache(cache_val)
    state = "enabled" if enabled else "disabled"
    name = item.GetName() or f"clip {item_index}"
    if result:
        return f"Color output cache {state} for '{name}'."
    return f"Failed to set color cache for '{name}'."


@mcp.tool
def resolve_get_fusion_cache(track_type: str = "video", track_index: int = 1, item_index: int = 0) -> str:
    """Check the Fusion Output Cache state for a timeline clip.

    *item_index*: 0 = current clip, or 1-based clip index.
    Returns Auto, On, or Off.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    if item_index == 0:
        item = tl.GetCurrentVideoItem()
        if not item:
            return "No current clip."
    else:
        items = tl.GetItemListInTrack(track_type, int(track_index)) or []
        if item_index < 1 or item_index > len(items):
            return f"Item index {item_index} out of range."
        item = items[item_index - 1]

    val = item.GetIsFusionOutputCacheEnabled()
    label = _CACHE_LABELS.get(val, str(val))
    name = item.GetName() or f"clip {item_index}"
    return f"Fusion output cache for '{name}': {label}"


@mcp.tool
def resolve_set_fusion_cache(
    mode: str = "auto", track_type: str = "video", track_index: int = 1, item_index: int = 0
) -> str:
    """Set the Fusion Output Cache mode for a timeline clip.

    *mode*: 'auto', 'on', or 'off'.
    *item_index*: 0 = current clip, or 1-based clip index.
    Equivalent to right-click → Render Cache Fusion Output.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    cache_val = _CACHE_VALUES.get(mode.lower())
    if cache_val is None:
        return f"Invalid mode '{mode}'. Use 'auto', 'on', or 'off'."

    if item_index == 0:
        item = tl.GetCurrentVideoItem()
        if not item:
            return "No current clip."
    else:
        items = tl.GetItemListInTrack(track_type, int(track_index)) or []
        if item_index < 1 or item_index > len(items):
            return f"Item index {item_index} out of range."
        item = items[item_index - 1]

    result = item.SetFusionOutputCache(cache_val)
    name = item.GetName() or f"clip {item_index}"
    if result:
        return f"Fusion output cache set to '{mode}' for '{name}'."
    return f"Failed to set Fusion cache for '{name}'."


# ---------------------------------------------------------------------------
# Node-level cache tools (via Graph object)
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_node_get_cache(node_index: int) -> str:
    """Get the cache mode for a specific node in the current clip's grade.

    *node_index*: 1-based node number.
    Returns Auto, On, or Off.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    item = tl.GetCurrentVideoItem()
    if not item:
        return "No current clip."

    graph = item.GetNodeGraph()
    if not graph:
        return "No node graph available."

    val = graph.GetNodeCacheMode(int(node_index))
    label = _CACHE_LABELS.get(val, str(val))
    node_label = graph.GetNodeLabel(int(node_index)) or f"Node {node_index}"
    return f"Cache mode for '{node_label}' (node {node_index}): {label}"


@mcp.tool
def resolve_node_set_cache(node_index: int, mode: str = "auto") -> str:
    """Set the cache mode for a specific node in the current clip's grade.

    *node_index*: 1-based node number.
    *mode*: 'auto', 'on', or 'off'.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    item = tl.GetCurrentVideoItem()
    if not item:
        return "No current clip."

    graph = item.GetNodeGraph()
    if not graph:
        return "No node graph available."

    cache_val = _CACHE_VALUES.get(mode.lower())
    if cache_val is None:
        return f"Invalid mode '{mode}'. Use 'auto', 'on', or 'off'."

    result = graph.SetNodeCacheMode(int(node_index), cache_val)
    node_label = graph.GetNodeLabel(int(node_index)) or f"Node {node_index}"
    if result:
        return f"Cache mode for '{node_label}' (node {node_index}) set to '{mode}'."
    return f"Failed to set cache mode for node {node_index}."
