"""
Photo clip property and metadata tools.

Read camera EXIF, RAW decode settings, and manage metadata on photo
clips in the media pool. Writable properties are limited to what the
Resolve scripting API exposes (Data Level, SuperScale, sizing, flip,
and metadata fields). RAW decode controls like exposure and white
balance are UI-only in the current API.
"""

import json
import os

from .config import mcp, IMAGE_EXTS
from .errors import safe_resolve_call
from .resolve import _boilerplate


def _find_clip(mp, clip_name: str):
    """Walk all bins to find a clip by name."""
    def _walk(folder):
        for c in (folder.GetClipList() or []):
            if c.GetName() == clip_name:
                return c
        for sub in (folder.GetSubFolderList() or []):
            found = _walk(sub)
            if found:
                return found
        return None
    return _walk(mp.GetRootFolder())


_RAW_SETTINGS_KEYS = [
    "Input Color Space", "Input Gamma", "Data Level",
    "Super Scale", "SuperScale Noise Reduction", "SuperScale Sharpness",
    "Bit Depth", "Format", "Resolution", "RAW", "Video Codec",
    "Camera Type", "Camera Manufacturer", "ISO",
    "Camera Aperture", "Shutter Speed", "Focal Point (mm)",
    "Lens Type", "Alpha mode", "PAR", "Type",
]

_WRITABLE_KEYS = {
    "Alpha mode", "Data Level", "Drop frame", "FPS",
    "H-FLIP", "Input Sizing Preset", "PAR",
    "SuperScale Noise Reduction", "SuperScale Sharpness",
    "Slate TC", "Start TC", "V-FLIP",
}


@mcp.tool
@safe_resolve_call
def resolve_photo_get_properties(clip_name: str) -> str:
    """Get all non-empty clip properties for a photo.

    Returns the full property dict including RAW decode settings,
    color space, gamma, resolution, bit depth, camera EXIF, and more.

    Args:
        clip_name (str): Exact clip name in the media pool (e.g. '_DSC2559.NEF').
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found in media pool."
    props = clip.GetClipProperty() or {}
    relevant = {k: v for k, v in props.items() if v}
    return json.dumps(relevant, indent=2, default=str)


@mcp.tool
@safe_resolve_call
def resolve_photo_get_raw_settings(clip_name: str) -> str:
    """Get RAW decode settings and camera EXIF for a photo.

    Shows color space, gamma, data level, resolution, bit depth,
    camera body, lens, ISO, aperture, shutter speed, and focal length.

    Args:
        clip_name (str): Exact clip name in the media pool.
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."
    props = clip.GetClipProperty() or {}
    result = {k: props[k] for k in _RAW_SETTINGS_KEYS if k in props and props[k]}
    return json.dumps(result, indent=2, default=str)


@mcp.tool
@safe_resolve_call
def resolve_photo_set_clip_property(
    clip_name: str,
    property_name: str,
    value: str,
) -> str:
    """Set a writable clip property on a photo.

    Writable properties (confirmed via API probe):
    - 'Data Level': 'Auto', 'Full', 'Video'
    - 'SuperScale Noise Reduction': '0.0' to '1.0'
    - 'SuperScale Sharpness': '0.0' to '1.0'
    - 'Alpha mode': 'None', 'Straight', 'Premultiplied'
    - 'PAR': 'Square', '16:9', etc.
    - 'H-FLIP' / 'V-FLIP': 'On', 'Off'
    - 'Input Sizing Preset': preset name
    - 'FPS': frame rate as number
    - 'Drop frame': '0' or '1'
    - 'Slate TC' / 'Start TC': timecode string

    NOTE: Input Color Space, Input Gamma, Super Scale, and RAW decode
    controls (exposure, white balance) are read-only in the scripting API.

    Args:
        clip_name (str): Exact clip name in the media pool.
        property_name (str): Property key to set.
        value (str): New value for the property.
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."
    if property_name not in _WRITABLE_KEYS:
        return (
            f"'{property_name}' is read-only in the scripting API. "
            f"Writable properties: {', '.join(sorted(_WRITABLE_KEYS))}"
        )
    result = clip.SetClipProperty(property_name, value)
    if result:
        return f"Set '{property_name}' = '{value}' on '{clip_name}'."
    return f"Failed to set '{property_name}'. Value may be invalid."


@mcp.tool
@safe_resolve_call
def resolve_photo_get_metadata(clip_name: str) -> str:
    """Get all metadata (built-in + third-party + flags) for a photo.

    Args:
        clip_name (str): Exact clip name in the media pool.
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."
    md = clip.GetMetadata() or {}
    tp = clip.GetThirdPartyMetadata() or {}
    flags = clip.GetFlagList() or []
    color = clip.GetClipColor()
    result = {
        "builtin_metadata": {k: v for k, v in md.items() if v},
        "third_party_metadata": tp,
        "flags": flags,
        "clip_color": color,
    }
    return json.dumps(result, indent=2, default=str)


@mcp.tool
@safe_resolve_call
def resolve_photo_set_metadata(
    clip_name: str,
    metadata_json: str,
) -> str:
    """Set built-in metadata fields on a photo.

    Valid keys: Scene, Shot, Description, Comments, Keywords,
    Date Recorded, Production Name, Good Take, and other built-in fields.

    Args:
        clip_name (str): Exact clip name in the media pool.
        metadata_json (str): JSON object with metadata key-value pairs.
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."
    try:
        md = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"
    result = clip.SetMetadata(md)
    if result:
        return f"Set {len(md)} metadata field(s) on '{clip_name}'."
    return "Failed. Resolve rejects the dict if any key is unrecognized."


@mcp.tool
@safe_resolve_call
def resolve_photo_set_flag(
    clip_name: str,
    color: str,
) -> str:
    """Set a flag color on a photo (clears existing flags first).

    Colors: Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia,
    Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream

    Args:
        clip_name (str): Exact clip name in the media pool.
        color (str): Flag color name.
    """
    _, _, mp = _boilerplate()
    clip = _find_clip(mp, clip_name)
    if not clip:
        return f"Clip '{clip_name}' not found."
    clip.ClearFlags("All")
    result = clip.AddFlag(color)
    if result:
        return f"Flag '{color}' set on '{clip_name}'."
    return f"Failed to set flag '{color}'. Check color name."


@mcp.tool
@safe_resolve_call
def resolve_photo_list_in_bin(bin_path: str = "") -> str:
    """List all photo/image clips in a media pool bin.

    Filters to image extensions only. Use slash-separated path like
    'Shoots/2026/04-15/MyShoot'. Empty = current folder.

    Args:
        bin_path (str): Slash-separated bin path. Empty = current folder.
    """
    _, _, mp = _boilerplate()

    if bin_path:
        folder = mp.GetRootFolder()
        for part in bin_path.strip("/").split("/"):
            found = None
            for sub in (folder.GetSubFolderList() or []):
                if sub.GetName() == part:
                    found = sub
                    break
            if not found:
                return f"Bin '{part}' not found in path '{bin_path}'."
            folder = found
    else:
        folder = mp.GetCurrentFolder()
        if not folder:
            return "No current folder."

    clips = folder.GetClipList() or []
    photos = []
    for c in clips:
        name = c.GetName()
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXTS:
            props = c.GetClipProperty() or {}
            photos.append({
                "name": name,
                "resolution": props.get("Resolution", ""),
                "format": props.get("Format", ""),
                "color_space": props.get("Input Color Space", ""),
                "iso": props.get("ISO", ""),
            })

    if not photos:
        return f"No image clips in '{bin_path or 'current folder'}'."
    lines = [f"{len(photos)} photo(s):"]
    for p in photos:
        lines.append(
            f"  {p['name']}  {p['resolution']}  {p['format']}  "
            f"CS:{p['color_space']}  ISO:{p['iso']}"
        )
    return "\n".join(lines)
