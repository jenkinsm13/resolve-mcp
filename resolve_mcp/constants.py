"""
Canonical Resolve constants — colors, track types, composite modes, retime controls.

Import these in tool modules for input validation and docstring references.
Every list matches DaVinci Resolve v20.3 scripting API behaviour.
"""

# ---------------------------------------------------------------------------
# Marker colors (Timeline.AddMarker / TimelineItem.AddMarker)
# ---------------------------------------------------------------------------
MARKER_COLORS = frozenset({
    "Blue", "Cyan", "Green", "Yellow", "Red", "Pink",
    "Purple", "Fuchsia", "Rose", "Lavender", "Sky", "Mint",
    "Lemon", "Sand", "Cocoa", "Cream",
})

# ---------------------------------------------------------------------------
# Clip colors (MediaPoolItem.SetClipColor / TimelineItem.SetClipColor)
# ---------------------------------------------------------------------------
CLIP_COLORS = frozenset({
    "Orange", "Apricot", "Yellow", "Lime", "Olive", "Green",
    "Teal", "Navy", "Blue", "Purple", "Violet", "Pink",
    "Tan", "Beige", "Brown", "Chocolate",
})

# ---------------------------------------------------------------------------
# Flag colors (MediaPoolItem.AddFlag / TimelineItem.AddFlag)
# ---------------------------------------------------------------------------
FLAG_COLORS = CLIP_COLORS  # Same palette as clip colors.

# ---------------------------------------------------------------------------
# Track types
# ---------------------------------------------------------------------------
TRACK_TYPES = frozenset({"video", "audio", "subtitle"})

# ---------------------------------------------------------------------------
# Composite modes (TimelineItem.SetProperty("CompositeMode", ...))
# ---------------------------------------------------------------------------
COMPOSITE_MODES = frozenset({
    "Normal",
    "Add", "Subtract", "Difference",
    "Multiply", "Screen", "Overlay",
    "Hardlight", "Softlight",
    "Darken", "Lighten",
    "Color Dodge", "Color Burn",
    "Linear Dodge", "Linear Burn",
    "Linear Light", "Vivid Light", "Pin Light", "Hard Mix",
    "Exclusion",
    "Hue", "Saturation", "Color", "Luminosity",
})

# ---------------------------------------------------------------------------
# Retime processes (TimelineItem.SetProperty("RetimeProcess", ...))
# ---------------------------------------------------------------------------
RETIME_PROCESSES = frozenset({
    "NearestFrame", "FrameBlend", "OpticalFlow",
})

# ---------------------------------------------------------------------------
# Scaling modes (TimelineItem.SetProperty("ScalingMode", ...))
# ---------------------------------------------------------------------------
SCALING_MODES = frozenset({
    "crop", "fit", "fill", "stretch",
})

# ---------------------------------------------------------------------------
# Resize filters
# ---------------------------------------------------------------------------
RESIZE_FILTERS = frozenset({
    "Sharper", "Smoother", "Bicubic", "Bilinear", "Lanczos",
})

# ---------------------------------------------------------------------------
# Resolve page names (Resolve.OpenPage)
# ---------------------------------------------------------------------------
PAGES = frozenset({
    "media", "cut", "edit", "fusion", "color", "fairlight", "deliver",
})

# ---------------------------------------------------------------------------
# Timeline export formats
# ---------------------------------------------------------------------------
EXPORT_FORMATS = {
    "AAF":    "AAF",
    "DRT":    "DRT",
    "EDL":    "EDL",
    "FCP7XML": "FCP_7_XML",
    "FCPXML": "FCPXML_1_8",  # Also: FCPXML_1_9, FCPXML_1_10, FCPXML_1_11
    "HDL":    "HDL",
    "MIDI":   "MIDI",
    "OTIO":   "OTIO",
    "TEXT_CSV": "TEXT_CSV",
}

# ---------------------------------------------------------------------------
# Render format→codec lookup (common subset — full list via resolve_get_render_formats)
# ---------------------------------------------------------------------------
COMMON_RENDER_CODECS = {
    "mp4":  ["H264", "H265"],
    "mov":  ["H264", "H265", "ProRes422", "ProRes422HQ", "ProRes4444", "DNxHR"],
    "mxf":  ["DNxHR", "DNxHD"],
    "tiff": ["RGB16"],
    "dpx":  ["RGB10"],
    "exr":  ["RGB_half"],
}

# ---------------------------------------------------------------------------
# Studio-only features (for detection/gating)
# ---------------------------------------------------------------------------
STUDIO_ONLY_FEATURES = frozenset({
    "TranscribeAudio",
    "AnalyzeDolbyVision",
    "OptimizeDolbyVision",
    "ConvertTimelineToStereo",
    "VoiceIsolation",
    "SmartReframe",
    "SpeedWarp",
    "SceneCutDetection",
    "NoiseReduction",
    "MagicMask",
})
