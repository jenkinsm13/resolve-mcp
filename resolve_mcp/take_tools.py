"""
Take selector MCP tools.

Covers: Adding takes, selecting between takes, and finalizing take choices.
Take selectors allow editors to stack multiple versions of a clip and
switch between them non-destructively.
"""

from .config import mcp
from .resolve import _boilerplate


def _get_item(track_type, track_index, item_index):
    """Get a timeline item by track and index."""
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        raise ValueError("No active timeline.")
    items = tl.GetItemListInTrack(track_type, int(track_index)) or []
    if item_index < 1 or item_index > len(items):
        raise ValueError(f"Item {item_index} out of range (1-{len(items)}).")
    return items[item_index - 1]


@mcp.tool
def resolve_item_add_take(track_type: str, track_index: int,
                           item_index: int, clip_name: str,
                           start_frame: int = -1, end_frame: int = -1) -> str:
    """Add a media pool clip as a new take for a timeline item.

    *track_type*: 'video' or 'audio'.
    *item_index*: 1-based clip position on the track.
    *clip_name*: name of the media pool clip to add as a take.
    *start_frame*/*end_frame*: optional sub-clip range (-1 = full clip).

    Initializes a take selector on the timeline item if one doesn't exist.
    """
    _, project, mp = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    items = tl.GetItemListInTrack(track_type, int(track_index)) or []
    if item_index < 1 or item_index > len(items):
        return f"Item {item_index} out of range (1-{len(items)})."
    item = items[item_index - 1]

    # Find clip in media pool
    root = mp.GetRootFolder()
    target_clip = _find_clip_recursive(root, clip_name)
    if not target_clip:
        return f"Clip '{clip_name}' not found in media pool."

    if start_frame >= 0 and end_frame >= 0:
        result = item.AddTake(target_clip, int(start_frame), int(end_frame))
    else:
        result = item.AddTake(target_clip)

    if result:
        return f"Added '{clip_name}' as take for item {item_index}."
    return "Failed to add take."


def _find_clip_recursive(folder, name):
    """Recursively search for a clip by name."""
    for clip in (folder.GetClipList() or []):
        if clip.GetName() == name:
            return clip
    for sub in (folder.GetSubFolderList() or []):
        found = _find_clip_recursive(sub, name)
        if found:
            return found
    return None


@mcp.tool
def resolve_item_get_takes_count(track_type: str, track_index: int,
                                  item_index: int) -> str:
    """Get the number of takes for a timeline item.

    Returns 0 if the clip is not a take selector.
    """
    item = _get_item(track_type, track_index, item_index)
    count = item.GetTakesCount()
    if count == 0:
        return f"Item {item_index} is not a take selector (0 takes)."
    return f"Item {item_index} has {count} take(s)."


@mcp.tool
def resolve_item_get_selected_take(track_type: str, track_index: int,
                                    item_index: int) -> str:
    """Get the currently selected take index for a timeline item.

    Returns 0 if the clip is not a take selector.
    """
    item = _get_item(track_type, track_index, item_index)
    idx = item.GetSelectedTakeIndex()
    if idx == 0:
        return f"Item {item_index} is not a take selector."
    count = item.GetTakesCount()
    return f"Item {item_index}: take {idx} of {count} selected."


@mcp.tool
def resolve_item_get_take(track_type: str, track_index: int,
                           item_index: int, take_index: int) -> str:
    """Get information about a specific take.

    *take_index*: 1-based take number.
    Returns start frame, end frame, and media pool item name.
    """
    item = _get_item(track_type, track_index, item_index)
    info = item.GetTakeByIndex(int(take_index))
    if not info:
        return f"No take at index {take_index}."

    mp_item = info.get("mediaPoolItem")
    name = mp_item.GetName() if mp_item else "Unknown"
    start = info.get("startFrame", "?")
    end = info.get("endFrame", "?")
    return f"Take {take_index}: '{name}' (frames {start}-{end})"


@mcp.tool
def resolve_item_select_take(track_type: str, track_index: int,
                              item_index: int, take_index: int) -> str:
    """Select a specific take for a timeline item.

    *take_index*: 1-based take number.
    """
    item = _get_item(track_type, track_index, item_index)
    result = item.SelectTakeByIndex(int(take_index))
    if result:
        return f"Selected take {take_index} for item {item_index}."
    return f"Failed to select take {take_index}."


@mcp.tool
def resolve_item_delete_take(track_type: str, track_index: int,
                              item_index: int, take_index: int) -> str:
    """Delete a take from a timeline item's take selector.

    *take_index*: 1-based take number.
    """
    item = _get_item(track_type, track_index, item_index)
    result = item.DeleteTakeByIndex(int(take_index))
    if result:
        return f"Deleted take {take_index} from item {item_index}."
    return f"Failed to delete take {take_index}."


@mcp.tool
def resolve_item_finalize_take(track_type: str, track_index: int,
                                item_index: int) -> str:
    """Finalize the take selection, removing the take selector.

    After finalization, the currently selected take becomes the clip
    and other takes are discarded. This is irreversible.
    """
    item = _get_item(track_type, track_index, item_index)
    result = item.FinalizeTake()
    if result:
        return f"Take selection finalized for item {item_index}."
    return "Failed to finalize take selection."
