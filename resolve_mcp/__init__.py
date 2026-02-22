"""
resolve_mcp — MCP server for DaVinci Resolve scripting API.
215+ tools covering the full Resolve API (v20.3) plus AI-enhanced editing tools.
"""

from .config import mcp  # noqa: F401 — re-export for entry points


def main():
    """Entry point for `resolve-mcp` console script."""
    mcp.run()


# --- Resolve scripting API tools ---
from . import project_tools       # noqa: F401  — project/DB management (10 tools)
from . import media_pool_tools    # noqa: F401  — media pool operations (11 tools)
from . import timeline_mgmt_tools # noqa: F401  — timeline management (15 tools)
from . import edit_tools          # noqa: F401  — timeline item editing (12 tools)
from . import marker_tools        # noqa: F401  — markers & playhead (9 tools)
from . import render_tools        # noqa: F401  — render/deliver pipeline (14 tools)
from . import color_tools         # noqa: F401  — color grading (12 tools)
from . import media_storage_tools # noqa: F401  — media storage browsing (3 tools)
from . import fairlight_tools     # noqa: F401  — Fairlight audio tools (4 tools)

# --- Extended Resolve API coverage ---
from . import project_mgr_tools   # noqa: F401  — archive/delete/DB switching (10 tools)
from . import media_pool_extras   # noqa: F401  — timeline-from-clips, import folder (10 tools)
from . import clip_metadata_tools # noqa: F401  — clip markers/flags/proxy/transcription (18 tools)
from . import timeline_insert_tools  # noqa: F401  — generators/titles/scene detect (13 tools)
from . import item_marker_tools   # noqa: F401  — timeline item markers & flags (11 tools)
from . import item_version_tools  # noqa: F401  — clip versions/color groups (11 tools)
from . import fusion_tools        # noqa: F401  — Fusion comp management (8 tools)
from . import gallery_tools       # noqa: F401  — gallery albums & stills (7 tools)
from . import node_tools          # noqa: F401  — node graph (5 tools)
from . import layout_preset_tools # noqa: F401  — layouts/burn-in/render presets (22 tools)
from . import dolby_stereo_tools  # noqa: F401  — Dolby Vision & 3D stereo (4 tools)
from . import folder_tools        # noqa: F401  — bin transcription/export/IDs (4 tools)

# --- AI bridge tools (require GEMINI_API_KEY) ---
from . import resolve_tools       # noqa: F401  — AI-driven Resolve tools (9 tools)

# --- MCP Resources ---
from . import resources           # noqa: F401  — resolve://project, timelines, bins, etc.
