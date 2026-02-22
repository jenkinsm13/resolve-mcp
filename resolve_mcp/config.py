"""
Global configuration, constants, and shared singletons (Gemini client, MCP server).
"""

import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

log = logging.getLogger("resolve-mcp")

# ---------------------------------------------------------------------------
# Gemini (optional — only needed for AI bridge tools)
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-3-flash-preview"  # free preview pricing
client = None

if GEMINI_API_KEY:
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# MCP server instance — tools register via @mcp.tool in other modules
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "resolve-mcp",
    instructions=(
        "MCP server with 285 tools for DaVinci Resolve scripting API (v20.3) "
        "plus AI-enhanced tools (analyze_timeline, add_markers, build_from_markers).\n\n"
        "PREREQUISITES: DaVinci Resolve must be running with scripting enabled "
        "(Preferences → System → General → External scripting using = Network). "
        "Set GEMINI_API_KEY in .env for AI bridge tools (optional).\n\n"
        "WORKFLOW — Direct Resolve control:\n"
        "Use resolve_* tools for project management, media pool, timelines, "
        "editing, markers, rendering, color grading, Fusion, Fairlight, and more. "
        "All tools follow the pattern: resolve_<object>_<action>.\n\n"
        "TRACK TYPES: 'video', 'audio', 'subtitle'\n"
        "MARKER COLORS: Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia, "
        "Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream\n"
        "CLIP COLORS: Orange, Apricot, Yellow, Lime, Olive, Green, Teal, Navy, "
        "Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate"
    ),
)

# ---------------------------------------------------------------------------
# Media constants
# ---------------------------------------------------------------------------

VIDEO_EXTS = {".mp4", ".mov", ".mxf", ".avi", ".webm", ".mkv", ".r3d", ".braw"}
AUDIO_EXTS = {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"}
GEMINI_MAX_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB Files API ceiling
SAFE_CODECS = {"h264", "avc", "avc1", "hevc", "h265", "hev1"}
GEMINI_MAX_LONG_EDGE = 1280
