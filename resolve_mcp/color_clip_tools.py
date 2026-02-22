"""Color clip tools: grade copy, gallery stills, frame export, color groups."""

from .config import mcp
from .resolve import _boilerplate


@mcp.tool
def resolve_copy_grade(
    source_clip_index: int, target_clip_indices: str, track_type: str = "video", track_index: int = 1
) -> str:
    """Copy the grade from one clip to others on the timeline.

    *source_clip_index*: 1-based index of the source clip on the track.
    *target_clip_indices*: comma-separated 1-based indices of target clips.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    items = tl.GetItemListInTrack(track_type.lower(), int(track_index))
    if not items:
        return f"No items on {track_type} track {track_index}."

    src_idx = int(source_clip_index) - 1
    if src_idx < 0 or src_idx >= len(items):
        return f"Source index {source_clip_index} out of range."

    target_indices = [int(x.strip()) for x in target_clip_indices.split(",")]
    targets = [items[ti - 1] for ti in target_indices if 1 <= ti <= len(items)]
    if not targets:
        return "No valid target clips."

    source = items[src_idx]
    result = True
    for target in targets:
        try:
            cdl = source.GetCDL()
            if cdl:
                target.SetCDL(cdl)
        except Exception:
            result = False

    if result:
        return f"Copied grade from clip {source_clip_index} to {len(targets)} clip(s)."
    return "Grade copy encountered errors."


@mcp.tool
def resolve_grab_still() -> str:
    """Grab a still from the current frame to the gallery.

    Must be on the Color page.
    """
    _, project, _ = _boilerplate()
    tl = project.GetCurrentTimeline()
    if not tl:
        return "No active timeline."

    result = tl.GrabStill()
    return "Still grabbed to gallery." if result else "Failed to grab still. Ensure you're on the Color page."


@mcp.tool
def resolve_export_frame(file_path: str) -> str:
    """Export the current frame as a still image.

    *file_path*: absolute path for the output image (e.g. '/path/frame.png').
    Supports: .png, .tiff, .jpg, .exr, .dpx
    """
    _, project, _ = _boilerplate()
    result = project.ExportCurrentFrameAsStill(file_path)
    return (
        f"Frame exported to {file_path}"
        if result
        else "Frame export failed. Check path and ensure a timeline is active."
    )


@mcp.tool
def resolve_list_color_groups() -> str:
    """List all color groups in the current project."""
    _, project, _ = _boilerplate()
    groups = project.GetColorGroupsList()
    if not groups:
        return "No color groups defined."

    lines = [f"{len(groups)} color group(s):"]
    for g in groups:
        name = g.GetName() if hasattr(g, "GetName") else str(g)
        lines.append(f"  • {name}")
    return "\n".join(lines)


@mcp.tool
def resolve_add_color_group(group_name: str) -> str:
    """Create a new color group in the current project."""
    _, project, _ = _boilerplate()
    result = project.AddColorGroup(group_name)
    return f"Color group '{group_name}' created." if result else f"Failed to create color group '{group_name}'."
