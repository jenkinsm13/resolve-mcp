"""
DaVinci Resolve scripting API connection and media pool helpers.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Resolve-recognised frame-rate strings keyed by rounded float value.
_FPS_MAP: dict[float, str] = {
    23.976: "23.976", 24.0: "24", 25.0: "25",
    29.97: "29.97", 30.0: "30", 48.0: "48",
    50.0: "50", 59.94: "59.94", 60.0: "60",
    119.88: "119.88", 120.0: "120",
}


def _resolve_module_path() -> Optional[str]:
    """Return the Resolve scripting modules directory for the current platform."""
    override = os.getenv("RESOLVE_SCRIPT_API")
    if override and os.path.isdir(override):
        return override

    platform_paths = {
        "darwin": "/Library/Application Support/Blackmagic Design/"
                  "DaVinci Resolve/Developer/Scripting/Modules/",
        "win32": os.path.expandvars(
            r"%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve"
            r"\Support\Developer\Scripting\Modules\\"
        ),
        "linux": "/opt/resolve/Developer/Scripting/Modules/",
    }
    path = platform_paths.get(sys.platform, platform_paths["linux"])
    return path if os.path.isdir(path) else None


def get_resolve():
    """Connect to the running DaVinci Resolve instance.  Returns None on failure."""
    mod_path = _resolve_module_path()
    if mod_path is None:
        return None
    if mod_path not in sys.path:
        sys.path.insert(0, mod_path)
    try:
        import DaVinciResolveScript as dvr_script  # type: ignore
        return dvr_script.scriptapp("Resolve")
    except (ImportError, AttributeError):
        return None


def _boilerplate():
    """Return (resolve, project, media_pool) or raise ValueError with message."""
    resolve = get_resolve()
    if not resolve:
        raise ValueError("Error: DaVinci Resolve is not running.")
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        raise ValueError("Error: No project open in Resolve.")
    media_pool = project.GetMediaPool()
    return resolve, project, media_pool


def is_studio() -> bool:
    """Return True if the connected Resolve instance is Studio edition.

    Detection heuristic: Studio's version string contains 'Studio',
    and the product name from GetProductName() (v18.5+) is
    'DaVinci Resolve Studio'.  Falls back to checking whether
    a Studio-only API method exists on the project object.
    """
    resolve = get_resolve()
    if not resolve:
        return False
    # v18.5+ exposes GetProductName()
    try:
        product = resolve.GetProductName()
        if product and "Studio" in product:
            return True
    except (AttributeError, TypeError):
        pass
    # Fallback: version string on older builds
    try:
        ver = resolve.GetVersionString()
        if ver and "Studio" in ver:
            return True
    except (AttributeError, TypeError):
        pass
    return False


def _require_studio(feature_name: str) -> None:
    """Raise ValueError if not running Resolve Studio."""
    if not is_studio():
        raise ValueError(
            f"'{feature_name}' requires DaVinci Resolve Studio. "
            f"The free edition does not support this feature."
        )


def _collect_clips_recursive(folder) -> dict:
    """Depth-first media pool traversal.

    Returns a flat dict mapping both the stem and full filename to each clip.
    Resolve returns ``None`` (not ``[]``) for empty lists — guarded with ``or []``.
    """
    result: dict[str, object] = {}
    for clip in (folder.GetClipList() or []):
        try:
            name = clip.GetName()
        except Exception:
            continue
        result[Path(name).stem] = clip
        result[name] = clip
    for sub in (folder.GetSubFolderList() or []):
        result.update(_collect_clips_recursive(sub))
    return result


def _find_bin(root_folder, bin_path: str):
    """Locate a media pool folder by name or ``/``-separated path.

    Returns the folder object or ``None`` if not found.
    """
    if "/" in bin_path:
        current = root_folder
        for seg in (s for s in bin_path.split("/") if s):
            found = next(
                (sub for sub in (current.GetSubFolderList() or []) if sub.GetName() == seg),
                None,
            )
            if found is None:
                return None
            current = found
        return current

    def _search(folder):
        if folder.GetName() == bin_path:
            return folder
        for sub in (folder.GetSubFolderList() or []):
            result = _search(sub)
            if result is not None:
                return result
        return None

    return _search(root_folder)


def _enumerate_bins(folder, prefix: str = "") -> list:
    """Recursively enumerate all bins as ``{path, clip_count}`` dicts."""
    name = folder.GetName()
    path = f"{prefix}/{name}" if prefix else name
    clips = folder.GetClipList() or []
    entries = [{"path": path, "clip_count": len(clips)}]
    for sub in (folder.GetSubFolderList() or []):
        entries.extend(_enumerate_bins(sub, path))
    return entries


def _unique_timeline_name(media_pool, base_name: str) -> tuple:
    """Return *(name, timeline)* using *base_name* or an auto-suffixed variant."""
    def _try(name):
        tl = media_pool.CreateEmptyTimeline(name)
        return (name, tl) if tl else None

    result = _try(base_name)
    if result:
        return result
    for n in range(2, 21):
        result = _try(f"{base_name}_{n}")
        if result:
            return result
    stamp = time.strftime("%m%d%H%M%S")
    name = f"{base_name}_{stamp}"
    return (name, media_pool.CreateEmptyTimeline(name))


# ---------------------------------------------------------------------------
# Backward-compatible re-exports (implementation moved to submodules)
# ---------------------------------------------------------------------------
from .resolve_transforms import (  # noqa: F401
    _DYNAMIC_ZOOM_EASE, _apply_clip_transform, _bake_speed_ramp, _apply_speed_ramp,
)
from .resolve_build import (  # noqa: F401
    build_timeline_direct, read_timeline_markers, markers_to_slots, try_resolve_import,
)
