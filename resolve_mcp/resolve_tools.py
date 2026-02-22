"""
Resolve AI tools — re-exported from focused submodules.
Importing this module registers all MCP tools via side-effect.
"""

from . import (
    resolve_ai_tools,  # noqa: F401  — resolve_add_markers, resolve_analyze_timeline, resolve_build_from_markers
    resolve_build_tools,  # noqa: F401  — resolve_build_timeline, resolve_build_status, resolve_edit_bin
    resolve_info_tools,  # noqa: F401  — resolve_get_info, resolve_list_bins, resolve_inspect_item
    resolve_ingest_tools,  # noqa: F401  — resolve_ingest_bin
)
