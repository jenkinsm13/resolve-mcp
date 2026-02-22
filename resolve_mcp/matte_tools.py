"""
Matte management MCP tools.

Covers: Clip mattes, timeline mattes — adding, listing, and deleting.
Mattes are external alpha channel files used for compositing and grading isolation.
"""

from .config import mcp
from .resolve import _boilerplate


@mcp.tool
def resolve_get_clip_mattes(clip_name: str) -> str:
    """List all mattes associated with a media pool clip.

    *clip_name*: name of the media pool clip.
    Returns file paths to the matte files.
    """
    _, _, mp = _boilerplate()
    root = mp.GetRootFolder()
    clip = _find_clip(root, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."

    mattes = mp.GetClipMatteList(clip)
    if not mattes:
        return f"No mattes for '{clip_name}'."

    lines = [f"{len(mattes)} matte(s) for '{clip_name}':"]
    for m in mattes:
        lines.append(f"  • {m}")
    return "\n".join(lines)


@mcp.tool
def resolve_add_clip_mattes(clip_name: str, matte_paths: str, stereo_eye: str = "") -> str:
    """Add matte files to a media pool clip.

    *clip_name*: name of the media pool clip.
    *matte_paths*: comma-separated absolute paths to matte files.
    *stereo_eye*: optional, 'left' or 'right' for stereo clips.
    """
    resolve, _, mp = _boilerplate()
    ms = resolve.GetMediaStorage()
    root = mp.GetRootFolder()
    clip = _find_clip(root, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."

    paths = [p.strip() for p in matte_paths.split(",")]

    if stereo_eye:
        result = ms.AddClipMattesToMediaPool(clip, paths, stereo_eye.lower())
    else:
        result = ms.AddClipMattesToMediaPool(clip, paths)

    if result:
        return f"Added {len(paths)} matte(s) to '{clip_name}'."
    return f"Failed to add mattes to '{clip_name}'."


@mcp.tool
def resolve_delete_clip_mattes(clip_name: str, matte_paths: str) -> str:
    """Delete matte files from a media pool clip.

    *clip_name*: name of the media pool clip.
    *matte_paths*: comma-separated paths of mattes to remove.
    """
    _, _, mp = _boilerplate()
    root = mp.GetRootFolder()
    clip = _find_clip(root, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."

    paths = [p.strip() for p in matte_paths.split(",")]
    result = mp.DeleteClipMattes(clip, paths)
    if result:
        return f"Deleted {len(paths)} matte(s) from '{clip_name}'."
    return f"Failed to delete mattes from '{clip_name}'."


@mcp.tool
def resolve_add_timeline_mattes(matte_paths: str) -> str:
    """Add timeline mattes to the current media pool folder.

    *matte_paths*: comma-separated absolute paths to matte files.
    Timeline mattes are used for timeline-level compositing operations.
    """
    resolve, _, _ = _boilerplate()
    ms = resolve.GetMediaStorage()
    paths = [p.strip() for p in matte_paths.split(",")]

    result = ms.AddTimelineMattesToMediaPool(paths)
    if result:
        return f"Added {len(paths)} timeline matte(s) to media pool."
    return "Failed to add timeline mattes."


@mcp.tool
def resolve_get_timeline_mattes(bin_name: str = "") -> str:
    """List timeline mattes in a media pool folder.

    *bin_name*: folder name (empty = current folder).
    """
    _, _, mp = _boilerplate()

    if bin_name:
        folder = _find_folder(mp.GetRootFolder(), bin_name)
        if not folder:
            return f"Bin '{bin_name}' not found."
    else:
        folder = mp.GetCurrentFolder()

    mattes = mp.GetTimelineMatteList(folder)
    if not mattes:
        return "No timeline mattes in folder."

    lines = [f"{len(mattes)} timeline matte(s):"]
    for m in mattes:
        name = m.GetName() if hasattr(m, "GetName") else str(m)
        lines.append(f"  • {name}")
    return "\n".join(lines)


def _find_clip(folder, name):
    """Recursively search for a clip by name."""
    for clip in folder.GetClipList() or []:
        if clip.GetName() == name:
            return clip
    for sub in folder.GetSubFolderList() or []:
        found = _find_clip(sub, name)
        if found:
            return found
    return None


def _find_folder(folder, name):
    """Recursively find a folder by name."""
    if folder.GetName() == name:
        return folder
    for sub in folder.GetSubFolderList() or []:
        found = _find_folder(sub, name)
        if found:
            return found
    return None
