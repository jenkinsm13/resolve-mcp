"""Render settings tools: presets, formats, codecs, current settings."""

import json

from .config import mcp
from .resolve import _boilerplate


@mcp.tool
def resolve_get_render_presets() -> str:
    """List all available render presets."""
    _, project, _ = _boilerplate()
    presets = project.GetRenderPresetList()
    if not presets:
        return "No render presets found."
    return f"{len(presets)} preset(s):\n" + "\n".join(f"  • {p}" for p in presets)


@mcp.tool
def resolve_get_render_formats() -> str:
    """List all supported render formats and their available codecs.

    Returns a JSON mapping of format → [codecs].
    """
    _, project, _ = _boilerplate()
    formats = project.GetRenderFormats()
    if not formats:
        return "No render formats available."

    result = {}
    for fmt_name, fmt_ext in formats.items():
        codecs = project.GetRenderCodecs(fmt_name)
        result[f"{fmt_name} (.{fmt_ext})"] = list(codecs.keys()) if codecs else []
    return json.dumps(result, indent=2)


@mcp.tool
def resolve_set_render_settings(settings_json: str) -> str:
    """Configure render settings for the next render job.

    *settings_json*: JSON object with render setting key-value pairs.

    Common keys: SelectAllFrames, MarkIn/MarkOut, TargetDir, CustomName,
    FormatWidth/FormatHeight, FrameRate, VideoQuality, AudioCodec,
    AudioBitDepth, AudioSampleRate, ColorSpaceTag, ExportAlpha.
    """
    _, project, _ = _boilerplate()
    try:
        settings = json.loads(settings_json)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON: {exc}"

    result = project.SetRenderSettings(settings)
    return f"Render settings updated ({len(settings)} key(s))." if result else "Failed to apply render settings. Check key names and values."


@mcp.tool
def resolve_load_render_preset(preset_name: str) -> str:
    """Load a render preset by name.

    Use resolve_get_render_presets() to see available presets.
    """
    _, project, _ = _boilerplate()
    result = project.LoadRenderPreset(preset_name)
    return f"Loaded render preset '{preset_name}'." if result else f"Failed to load preset '{preset_name}'. Check the name."


@mcp.tool
def resolve_get_current_render_settings() -> str:
    """Get the current render format and codec as JSON."""
    _, project, _ = _boilerplate()
    settings = project.GetCurrentRenderFormatAndCodec()
    if isinstance(settings, dict):
        return json.dumps(settings, indent=2)
    return str(settings) if settings else "No render format/codec set."


@mcp.tool
def resolve_set_render_format_and_codec(format_name: str, codec_name: str) -> str:
    """Set the render format and codec.

    Use resolve_get_render_formats() to see valid format/codec combinations.
    """
    _, project, _ = _boilerplate()
    result = project.SetCurrentRenderFormatAndCodec(format_name, codec_name)
    return f"Render format set to {format_name} / {codec_name}." if result else "Failed. Check format/codec names with resolve_get_render_formats()."
