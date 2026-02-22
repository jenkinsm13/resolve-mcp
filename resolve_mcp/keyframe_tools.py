"""
Keyframe mode MCP tools.

Controls the keyframe recording mode: All, Color, or Sizing.
This affects which parameters are keyframed when making adjustments.
"""

from .config import mcp
from .resolve import get_resolve

_MODE_NAMES = {0: "All", 1: "Color", 2: "Sizing"}
_MODE_VALUES = {"all": 0, "color": 1, "sizing": 2}


@mcp.tool
def resolve_get_keyframe_mode() -> str:
    """Get the current keyframe recording mode.

    Returns one of: All, Color, Sizing.
    - All: keyframes all parameter changes
    - Color: only keyframes color grading changes
    - Sizing: only keyframes sizing/transform changes
    """
    resolve = get_resolve()
    if not resolve:
        return "DaVinci Resolve is not running."

    mode = resolve.GetKeyframeMode()
    label = _MODE_NAMES.get(mode, f"Unknown ({mode})")
    return f"Keyframe mode: {label}"


@mcp.tool
def resolve_set_keyframe_mode(mode: str) -> str:
    """Set the keyframe recording mode.

    *mode*: 'all', 'color', or 'sizing'.
    - all: keyframes all parameter changes
    - color: only keyframes color grading changes
    - sizing: only keyframes sizing/transform changes
    """
    resolve = get_resolve()
    if not resolve:
        return "DaVinci Resolve is not running."

    mode_val = _MODE_VALUES.get(mode.lower())
    if mode_val is None:
        return f"Invalid mode '{mode}'. Use 'all', 'color', or 'sizing'."

    result = resolve.SetKeyframeMode(mode_val)
    if result:
        return f"Keyframe mode set to '{mode}'."
    return f"Failed to set keyframe mode to '{mode}'."
