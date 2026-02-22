"""
Fusion page node graph tools — add/remove tools, connect nodes,
set parameters, read inputs, and manage keyframes.

These tools operate on the Fusion composition inside a timeline item,
enabling programmatic construction of motion graphics, VFX composites,
title cards, and animated elements directly from the MCP layer.

Common Fusion tool IDs:
    Background, Merge, Transform, Text+, Blur, BrightnessContrast,
    ColorCorrector, Ellipse, Rectangle, Polygon, ChannelBooleans,
    Paint, Tracker, GridWarp, Crop, Dissolve, Resize, CustomTool,
    TimeStretcher, TimeSpeed, FastNoise, Plasma, DirectionalBlur,
    Glow, SoftGlow, LensDirtIn, FilmGrain, MatteControl, Duplicate,
    CornerPositioner, DVE, Displace, Shadow, Highlight
"""

import json
import logging

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate

log = logging.getLogger(__name__)


def _get_comp(project, track_type=None, track_index=None,
              item_index=None, comp_name=None):
    """Get a Fusion composition.

    If track/item args are provided, gets the comp from that timeline item.
    Otherwise tries to get the current comp from the active Fusion page.
    """
    # Route 1: specific timeline item
    if track_type and track_index and item_index:
        tl = project.GetCurrentTimeline()
        if not tl:
            raise ValueError("No active timeline.")
        items = tl.GetItemListInTrack(track_type.lower(), int(track_index)) or []
        idx = int(item_index) - 1
        if idx < 0 or idx >= len(items):
            raise ValueError(f"Item index {item_index} out of range (1–{len(items)}).")
        item = items[idx]
        if comp_name:
            comp = item.GetFusionCompByName(comp_name)
        else:
            count = item.GetFusionCompCount()
            if count == 0:
                raise ValueError("No Fusion comp on this item. Use resolve_item_add_fusion_comp first.")
            comp = item.GetFusionCompByIndex(count)
        if not comp:
            raise ValueError("Could not access Fusion comp.")
        return comp

    # Route 2: current item on Fusion page
    tl = project.GetCurrentTimeline()
    if not tl:
        raise ValueError("No active timeline.")
    item = tl.GetCurrentVideoItem()
    if not item:
        raise ValueError("No clip selected — switch to Fusion page and select a clip.")
    count = item.GetFusionCompCount()
    if count == 0:
        raise ValueError("No Fusion comp on this clip. Use resolve_item_add_fusion_comp first.")
    if comp_name:
        comp = item.GetFusionCompByName(comp_name)
    else:
        comp = item.GetFusionCompByIndex(count)
    if not comp:
        raise ValueError("Could not access Fusion comp.")
    return comp


# ---------------------------------------------------------------------------
# Comp introspection
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_fusion_list_tools(comp_name: str = "") -> str:
    """List all tools in the current Fusion composition.

    Returns each tool's name and type ID (e.g. 'Background1: Background',
    'Merge1: Merge', 'Text1: TextPlus').

    Args:
        comp_name (str): Optional comp name. If empty, uses the active/last comp.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    tool_list = comp.GetToolList(False)
    if not tool_list:
        return "Comp is empty (no tools)."
    lines = [f"{len(tool_list)} tool(s) in comp:"]
    for _idx, tool in (tool_list.items() if isinstance(tool_list, dict) else enumerate(tool_list)):
        name = tool.Name if hasattr(tool, "Name") else str(tool)
        tid = tool.ID if hasattr(tool, "ID") else "unknown"
        lines.append(f"  {name}: {tid}")
    return "\n".join(lines)


@mcp.tool
@safe_resolve_call
def resolve_fusion_get_tool_inputs(tool_name: str, comp_name: str = "") -> str:
    """List all available inputs on a Fusion tool.

    Shows input names, types, and current values — essential for knowing
    what parameters you can set on a tool.

    Args:
        tool_name (str): Name of the tool (e.g. 'Background1', 'Merge1', 'Text1').
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    tool = comp.FindTool(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found."
    inputs = tool.GetInputList() or {}
    lines = [f"Inputs for {tool_name}:"]
    for key, inp in (inputs.items() if isinstance(inputs, dict) else enumerate(inputs)):
        try:
            name = inp.GetAttrs("INPS_Name") if hasattr(inp, "GetAttrs") else str(inp)
            val = tool.GetInput(str(name)) if name else None
            lines.append(f"  {name}: {val}")
        except Exception:
            lines.append(f"  {key}: (could not read)")
    return "\n".join(lines[:60])  # cap output for very complex tools


# ---------------------------------------------------------------------------
# Tool creation & deletion
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_fusion_add_tool(tool_id: str, name: str = "",
                             x: int = 0, y: int = 0,
                             comp_name: str = "") -> str:
    """Add a tool to the Fusion composition.

    Common tool IDs:
    - Backgrounds: 'Background'
    - Compositing: 'Merge', 'Dissolve', 'ChannelBooleans'
    - Text: 'TextPlus' (the Text+ tool)
    - Transform: 'Transform', 'Resize', 'Crop', 'DVE', 'CornerPositioner'
    - Masks: 'Ellipse', 'Rectangle', 'Polygon', 'BSplineMask'
    - Blur/Effects: 'Blur', 'DirectionalBlur', 'Glow', 'SoftGlow'
    - Color: 'BrightnessContrast', 'ColorCorrector', 'ColorGain'
    - Generators: 'FastNoise', 'Plasma', 'DaySky'
    - Film: 'FilmGrain', 'LensDirtIn'
    - Warp: 'GridWarp', 'Displace'
    - Particle: 'pEmitter', 'pRender'
    - 3D: 'Shape3D', 'Merge3D', 'Camera3D', 'PointLight3D', 'Renderer3D'
    - Matte: 'MatteControl', 'Primatte', 'DeltaKeyer', 'UltraKeyer'

    Returns the name of the created tool.

    Args:
        tool_id (str): The Fusion tool type ID (e.g. 'Background', 'Merge', 'TextPlus').
        name (str): Optional custom name for the tool. If empty, Fusion auto-names it.
        x (int): X position in the flow view. 0 = auto-place.
        y (int): Y position in the flow view. 0 = auto-place.
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)

    if x != 0 or y != 0:
        tool = comp.AddTool(tool_id, x, y)
    else:
        tool = comp.AddTool(tool_id)

    if not tool:
        return f"Failed to add tool '{tool_id}'. Check tool ID is valid."

    actual_name = tool.Name if hasattr(tool, "Name") else str(tool)
    if name and hasattr(tool, "SetAttrs"):
        try:
            tool.SetAttrs({"TOOLS_Name": name})
            actual_name = name
        except Exception:
            pass
    return f"Added {tool_id} as '{actual_name}'."


@mcp.tool
@safe_resolve_call
def resolve_fusion_remove_tool(tool_name: str, comp_name: str = "") -> str:
    """Remove a tool from the Fusion composition.

    Args:
        tool_name (str): Name of the tool to remove (e.g. 'Background1').
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    tool = comp.FindTool(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found."
    tool.Delete()
    return f"Removed '{tool_name}'."


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_fusion_connect(from_tool: str, to_tool: str,
                            from_output: str = "Output",
                            to_input: str = "Background",
                            comp_name: str = "") -> str:
    """Connect the output of one tool to the input of another.

    Common connection patterns:
    - Background → Merge.Background (base layer)
    - Foreground → Merge.Foreground (overlay layer)
    - Any tool → Transform.Input
    - Merge → MediaOut1.Input (final output)
    - Mask tool → any tool's EffectMask input

    Args:
        from_tool (str): Source tool name (e.g. 'Background1').
        to_tool (str): Destination tool name (e.g. 'Merge1').
        from_output (str): Output name on source tool. Defaults to 'Output'.
        to_input (str): Input name on destination tool. Defaults to 'Background'.
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    src = comp.FindTool(from_tool)
    dst = comp.FindTool(to_tool)
    if not src:
        return f"Source tool '{from_tool}' not found."
    if not dst:
        return f"Destination tool '{to_tool}' not found."

    try:
        dst.ConnectInput(to_input, src, from_output)
        return f"Connected {from_tool}.{from_output} → {to_tool}.{to_input}"
    except Exception:
        pass

    # Fallback: try direct attribute-style connection
    try:
        out = getattr(src, from_output, None)
        if out is not None:
            setattr(dst, to_input, out)
            return f"Connected {from_tool}.{from_output} → {to_tool}.{to_input}"
    except Exception as exc:
        return f"Connection failed: {exc}"
    return "Connection failed — check tool names and input/output names."


@mcp.tool
@safe_resolve_call
def resolve_fusion_disconnect(tool_name: str, input_name: str,
                               comp_name: str = "") -> str:
    """Disconnect an input on a Fusion tool.

    Args:
        tool_name (str): Tool name (e.g. 'Merge1').
        input_name (str): Input to disconnect (e.g. 'Foreground').
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    tool = comp.FindTool(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found."
    try:
        tool.ConnectInput(input_name, None)
        return f"Disconnected {tool_name}.{input_name}"
    except Exception as exc:
        return f"Disconnect failed: {exc}"


# ---------------------------------------------------------------------------
# Parameter control
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_fusion_set_input(tool_name: str, input_name: str,
                              value: str, comp_name: str = "") -> str:
    """Set a parameter value on a Fusion tool.

    Values are auto-converted: numbers become float, 'true'/'false' become
    bool, JSON arrays become tables.  Everything else is passed as string.

    Common inputs by tool type:
    - Background: TopLeftRed/Green/Blue/Alpha (0-1), Width, Height
    - TextPlus: StyledText (the text content), Font, Size, Red1/Green1/Blue1
    - Transform: Center.X, Center.Y, Size, Angle, Pivot.X, Pivot.Y
    - Merge: BlendClone (0-1 opacity), Center.X, Center.Y, Size
    - Blur: XBlurSize, YBlurSize
    - BrightnessContrast: Gain, Brightness, Contrast, Gamma, Saturation

    Args:
        tool_name (str): Tool name (e.g. 'Background1', 'Text1').
        input_name (str): Input parameter name (e.g. 'TopLeftRed', 'StyledText', 'Size').
        value (str): Value to set. Numbers, booleans, and JSON arrays are auto-converted.
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    tool = comp.FindTool(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found."

    # Auto-convert value types
    converted = _convert_value(value)

    try:
        tool.SetInput(input_name, converted)
        return f"{tool_name}.{input_name} = {converted}"
    except Exception as exc:
        return f"Failed to set {tool_name}.{input_name}: {exc}"


@mcp.tool
@safe_resolve_call
def resolve_fusion_get_input(tool_name: str, input_name: str,
                              comp_name: str = "") -> str:
    """Read the current value of a parameter on a Fusion tool.

    Args:
        tool_name (str): Tool name (e.g. 'Background1').
        input_name (str): Input parameter name (e.g. 'TopLeftRed', 'Size').
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    tool = comp.FindTool(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found."
    val = tool.GetInput(input_name)
    return f"{tool_name}.{input_name} = {val}"


# ---------------------------------------------------------------------------
# Keyframes
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_fusion_set_keyframe(tool_name: str, input_name: str,
                                 frame: int, value: str,
                                 comp_name: str = "") -> str:
    """Set a keyframe on a tool input at a specific frame.

    This enables animation — set different values at different frames and
    Fusion interpolates between them.

    Args:
        tool_name (str): Tool name.
        input_name (str): Input parameter name to keyframe.
        frame (int): Frame number to place the keyframe at.
        value (str): Value at this keyframe. Auto-converted like set_input.
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    tool = comp.FindTool(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found."

    converted = _convert_value(value)
    try:
        tool.SetInput(input_name, converted, frame)
        return f"Keyframe: {tool_name}.{input_name} = {converted} @ frame {frame}"
    except Exception as exc:
        return f"Keyframe failed: {exc}"


@mcp.tool
@safe_resolve_call
def resolve_fusion_get_keyframes(tool_name: str, input_name: str,
                                  comp_name: str = "") -> str:
    """Get all keyframes on a tool input.

    Returns frame→value pairs for animated parameters.

    Args:
        tool_name (str): Tool name.
        input_name (str): Input parameter name.
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    tool = comp.FindTool(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found."
    try:
        kf = tool.GetInput(input_name)
        if isinstance(kf, dict):
            return json.dumps(kf, indent=2, default=str)
        return f"{tool_name}.{input_name} = {kf} (not keyframed)"
    except Exception as exc:
        return f"Could not read keyframes: {exc}"


# ---------------------------------------------------------------------------
# Comp-level controls
# ---------------------------------------------------------------------------

@mcp.tool
@safe_resolve_call
def resolve_fusion_set_comp_time(frame: int, comp_name: str = "") -> str:
    """Set the current time position in the Fusion comp.

    Args:
        frame (int): Frame number to jump to.
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    comp.SetCurrentTime(frame)
    return f"Comp time set to frame {frame}."


@mcp.tool
@safe_resolve_call
def resolve_fusion_get_comp_time(comp_name: str = "") -> str:
    """Get the current time position and render range of the Fusion comp.

    Args:
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    current = comp.GetCurrentTime()
    attrs = comp.GetAttrs() or {}
    start = attrs.get("COMPN_RenderStart", "?")
    end = attrs.get("COMPN_RenderEnd", "?")
    return f"Current frame: {current}, render range: {start}–{end}"


@mcp.tool
@safe_resolve_call
def resolve_fusion_render_comp(start_frame: int = -1, end_frame: int = -1,
                                comp_name: str = "") -> str:
    """Render the current Fusion composition.

    If start/end are -1, renders the full comp range.

    Args:
        start_frame (int): Start frame. -1 = use comp default.
        end_frame (int): End frame. -1 = use comp default.
        comp_name (str): Optional comp name.
    """
    _, project, _ = _boilerplate()
    comp = _get_comp(project, comp_name=comp_name or None)
    if start_frame >= 0 and end_frame >= 0:
        r = comp.Render({"Start": start_frame, "End": end_frame})
    else:
        r = comp.Render()
    return "Fusion comp render started." if r else "Render failed."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _convert_value(value_str: str):
    """Auto-convert string value to appropriate Python type for Fusion."""
    if value_str.lower() == "true":
        return True
    if value_str.lower() == "false":
        return False
    try:
        return float(value_str) if "." in value_str else int(value_str)
    except ValueError:
        pass
    try:
        parsed = json.loads(value_str)
        return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    return value_str
