"""
Magic Mask MCP tools.

DaVinci Resolve Studio's AI-powered object and person masking.
Creates automatic masks that track subjects through a shot.
"""

from .config import mcp
from .resolve import _boilerplate


@mcp.tool
def resolve_create_magic_mask(mode: str = "F", track_type: str = "video",
                               track_index: int = 1, item_index: int = 0) -> str:
    """Create a Magic Mask on a timeline clip.

    *mode*: 'F' (forward), 'B' (backward), or 'BI' (bidirectional).
    *item_index*: 0 = current clip (Color page), or 1-based clip index.

    Requires DaVinci Resolve Studio.
    Magic Mask uses AI to automatically isolate subjects (people, objects)
    for targeted color grading. The mask appears in the Color page qualifier.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    mode = mode.upper()
    if mode not in ("F", "B", "BI"):
        return f"Invalid mode '{mode}'. Use 'F' (forward), 'B' (backward), or 'BI' (bidirectional)."

    if item_index == 0:
        item = tl.GetCurrentVideoItem()
        if not item:
            return "No current clip. Navigate to a clip on the Color page."
    else:
        items = tl.GetItemListInTrack(track_type, int(track_index)) or []
        if item_index < 1 or item_index > len(items):
            return f"Item {item_index} out of range."
        item = items[item_index - 1]

    result = item.CreateMagicMask(mode)
    mode_labels = {"F": "forward", "B": "backward", "BI": "bidirectional"}
    name = item.GetName() or f"clip {item_index}"
    if result:
        return f"Magic Mask created on '{name}' ({mode_labels[mode]} tracking)."
    return f"Failed to create Magic Mask. Requires Resolve Studio."


@mcp.tool
def resolve_regenerate_magic_mask(track_type: str = "video",
                                    track_index: int = 1,
                                    item_index: int = 0) -> str:
    """Regenerate the Magic Mask on a timeline clip.

    *item_index*: 0 = current clip (Color page), or 1-based clip index.

    Use after making adjustments to the mask stroke. Requires Resolve Studio.
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
            return f"Item {item_index} out of range."
        item = items[item_index - 1]

    result = item.RegenerateMagicMask()
    name = item.GetName() or f"clip {item_index}"
    if result:
        return f"Magic Mask regenerated on '{name}'."
    return f"Failed to regenerate Magic Mask. Requires Resolve Studio."
