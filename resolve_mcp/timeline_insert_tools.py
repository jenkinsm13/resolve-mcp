"""
Timeline insert & detection tools — generators, titles, Fusion inserts,
scene cut detection, frame queries, DRX grade application, and IDs.
"""

import json

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate


def _tl(project):
    tl = project.GetCurrentTimeline()
    if not tl:
        raise ValueError("No active timeline.")
    return tl


# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_insert_generator(generator_name: str, duration: float = 5.0, track_index: int = 1) -> str:
    """Insert a built-in generator into the timeline (bars, black, color, etc.).

    *generator_name*: e.g. '10 Step', 'Grey Scale', 'Color Bars', 'Black',
    'Window', etc.
    *duration*: seconds.

    Args:
        generator_name (str): Name of the generator to insert (e.g., '10 Step', 'Color Bars', 'Black').
        duration (float): Duration in seconds. Defaults to 5.0.
        track_index (int): Video track index (1-based). Defaults to 1.
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    fps = float(tl.GetSetting("timelineFrameRate") or 24)
    info = {"generatorName": generator_name, "duration": round(duration * fps), "trackIndex": track_index}
    r = tl.InsertGeneratorIntoTimeline(info)
    return f"Generator '{generator_name}' inserted ({duration}s)." if r else "Failed — check generator name."


@mcp.tool
@safe_resolve_call
def resolve_insert_title(title_name: str, duration: float = 5.0, track_index: int = 1) -> str:
    """Insert a title/text template into the timeline.

    *title_name*: e.g. 'Text+', 'Lower Third', 'Scroll', etc.

    Args:
        title_name (str): Name of the title template to insert (e.g., 'Text+', 'Lower Third').
        duration (float): Duration in seconds. Defaults to 5.0.
        track_index (int): Video track index (1-based). Defaults to 1.
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    fps = float(tl.GetSetting("timelineFrameRate") or 24)
    info = {"templateName": title_name, "duration": round(duration * fps), "trackIndex": track_index}
    r = tl.InsertTitleIntoTimeline(info)
    return f"Title '{title_name}' inserted." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_insert_fusion_title(title_name: str, duration: float = 5.0, track_index: int = 1) -> str:
    """Insert a Fusion-based title template.

    Args:
        title_name (str): Name of the Fusion title template to insert.
        duration (float): Duration in seconds. Defaults to 5.0.
        track_index (int): Video track index (1-based). Defaults to 1.
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    fps = float(tl.GetSetting("timelineFrameRate") or 24)
    info = {"templateName": title_name, "duration": round(duration * fps), "trackIndex": track_index}
    r = tl.InsertFusionTitleIntoTimeline(info)
    return f"Fusion title '{title_name}' inserted." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_insert_fusion_generator(generator_name: str, duration: float = 5.0, track_index: int = 1) -> str:
    """Insert a Fusion-based generator.

    Args:
        generator_name (str): Name of the Fusion generator to insert.
        duration (float): Duration in seconds. Defaults to 5.0.
        track_index (int): Video track index (1-based). Defaults to 1.
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    fps = float(tl.GetSetting("timelineFrameRate") or 24)
    info = {"generatorName": generator_name, "duration": round(duration * fps), "trackIndex": track_index}
    r = tl.InsertFusionGeneratorIntoTimeline(info)
    return f"Fusion generator '{generator_name}' inserted." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_insert_fusion_composition(track_index: int = 1, duration: float = 5.0) -> str:
    """Insert an empty Fusion composition into the timeline.

    Args:
        track_index (int): Video track index (1-based). Defaults to 1.
        duration (float): Duration in seconds. Defaults to 5.0.
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    fps = float(tl.GetSetting("timelineFrameRate") or 24)
    info = {"duration": round(duration * fps), "trackIndex": track_index}
    r = tl.InsertFusionCompositionIntoTimeline(info)
    return "Fusion composition inserted." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_insert_ofx_generator(
    generator_name: str, plugin_id: str, duration: float = 5.0, track_index: int = 1
) -> str:
    """Insert an OFX plugin generator into the timeline.

    *plugin_id*: the OFX plugin identifier string.

    Args:
        generator_name (str): Display name for the OFX generator.
        plugin_id (str): OFX plugin identifier string.
        duration (float): Duration in seconds. Defaults to 5.0.
        track_index (int): Video track index (1-based). Defaults to 1.
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    fps = float(tl.GetSetting("timelineFrameRate") or 24)
    info = {
        "generatorName": generator_name,
        "pluginId": plugin_id,
        "duration": round(duration * fps),
        "trackIndex": track_index,
    }
    r = tl.InsertOFXGeneratorIntoTimeline(info)
    return "OFX generator inserted." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_detect_scene_cuts() -> str:
    """Detect scene cuts on the current timeline. Returns cut frames.

    Args: None
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    r = tl.DetectSceneCuts()
    if r and isinstance(r, list):
        return f"{len(r)} scene cut(s) detected:\n" + "\n".join(f"  frame {f}" for f in r[:50])
    return "Scene detection returned no results or failed."


@mcp.tool
@safe_resolve_call
def resolve_get_timeline_frame_range() -> str:
    """Get the start and end frame numbers of the current timeline.

    Args: None
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    start = tl.GetStartFrame()
    end = tl.GetEndFrame()
    return f"Frames {start} → {end} ({end - start} total)"


@mcp.tool
@safe_resolve_call
def resolve_apply_drx_grade(drx_path: str, track_type: str = "video", track_index: int = 1, item_index: int = 0) -> str:
    """Apply a saved .drx grade file to timeline clips.

    If *item_index* is 0, applies to all items on the track.
    Otherwise applies to the specific 1-based item.

    Args:
        drx_path (str): Path to the .drx grade file to apply.
        track_type (str): Track type ('video' or 'audio'). Defaults to 'video'.
        track_index (int): Track index (1-based). Defaults to 1.
        item_index (int): Clip index (0 = all, 1-based otherwise). Defaults to 0.
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    items = tl.GetItemListInTrack(track_type.lower(), int(track_index)) or []
    if not items:
        return "No items on track."
    if item_index > 0:
        items = [items[item_index - 1]]
    r = tl.ApplyGradeFromDRX(drx_path, 0, items)
    return f"DRX grade applied to {len(items)} item(s)." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_grab_all_stills() -> str:
    """Grab stills from all clips on the current timeline.

    Args: None
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    r = tl.GrabAllStills()
    return "All stills grabbed to gallery." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_get_timeline_id() -> str:
    """Get the unique ID of the current timeline.

    Args: None
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    uid = tl.GetUniqueId()
    return f"Timeline unique ID: {uid}" if uid else "Could not retrieve."


@mcp.tool
@safe_resolve_call
def resolve_import_into_timeline(file_path: str, import_options: str = "{}") -> str:
    """Import media directly into the current timeline.

    *import_options*: JSON with keys like autoImportSourceClipsIntoMediaPool,
    ignoreFileExtensionsWhenMatching, insertAdditionalTracks, etc.

    Args:
        file_path (str): Path to the media file or EDL/XML to import.
        import_options (str): JSON string with import settings. Defaults to "{}".
    """
    _, project, _ = _boilerplate()
    tl = _tl(project)
    try:
        opts = json.loads(import_options)
    except json.JSONDecodeError:
        opts = {}
    r = tl.ImportIntoTimeline(file_path, opts) if opts else tl.ImportIntoTimeline(file_path)
    return f"Imported into timeline from {file_path}" if r else "Import failed."
