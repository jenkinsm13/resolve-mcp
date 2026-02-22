# resolve-mcp

MCP server exposing 285+ tools for the DaVinci Resolve scripting API (v20.3), plus AI bridge tools powered by Google Gemini.

## Architecture

- **Package**: `resolve_mcp/` — all modules use relative imports (`from .config import mcp`)
- **Entry point**: `resolve_mcp/__init__.py` → `main()` → `mcp.run()`
- **Tool registration**: Every tool module is imported in `__init__.py`. The `@mcp.tool` decorator on each function auto-registers it with the FastMCP server.
- **MCP resources**: `resources.py` exposes read-only `resolve://` URIs (project, timelines, bins, render-queue, version)

## Key Patterns

### Adding a new tool
1. Create or edit a `*_tools.py` module
2. Import `from .config import mcp` and `from .resolve import get_resolve, _boilerplate`
3. Decorate with `@mcp.tool`
4. If the module is new, add `from . import my_new_tools` in `__init__.py`

### Resolve connection
- `get_resolve()` returns the Resolve scripting object (or `None` if not running)
- `_boilerplate()` returns `(resolve, project, media_pool, timeline)` — raises `ValueError` with a clean message if any are missing
- All Resolve API calls go through the network scripting interface

### Error handling
- `@safe_resolve_call` decorator in `errors.py` wraps tools to catch exceptions and return MCP-friendly error strings
- Custom exception classes: `ResolveNotRunning`, `ProjectNotOpen`, `TimelineNotFound`, `BinNotFound`, `ClipNotFound`, `ItemNotFound`, `StudioRequired`

### Gemini (optional)
- `GEMINI_API_KEY` is **optional** — `client = None` when not set
- Only AI bridge tools need Gemini
- AI tools must check `if client is None: return "Error: GEMINI_API_KEY not set..."` before doing anything
- `from google.genai import types` is imported **inside** functions that need it (not at module level)

### Constants
- `VIDEO_EXTS`, `AUDIO_EXTS`, `GEMINI_MAX_BYTES`, `SAFE_CODECS`, `GEMINI_MAX_LONG_EDGE` in `config.py`
- Track types: `'video'`, `'audio'`, `'subtitle'`
- Marker colors: Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia, Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream
- Clip colors: Orange, Apricot, Yellow, Lime, Olive, Green, Teal, Navy, Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate

## Module Map

| Module | Tools | Purpose |
|--------|-------|---------|
| `project_tools.py` | 10 | Project/DB management |
| `media_pool_tools.py` | 11 | Media pool operations |
| `timeline_mgmt_tools.py` | 15 | Timeline management |
| `edit_tools.py` | 12 | Timeline item editing |
| `marker_tools.py` | 9 | Markers & playhead |
| `render_tools.py` | 14 | Render pipeline |
| `color_tools.py` | 12 | Color grading |
| `fairlight_tools.py` | 4 | Fairlight audio |
| `media_storage_tools.py` | 3 | Media storage browsing |
| `project_mgr_tools.py` | 10 | Archive/delete/DB switching |
| `media_pool_extras.py` | 10 | Timeline-from-clips, import folder |
| `clip_metadata_tools.py` | 18 | Clip markers/flags/proxy/transcription |
| `timeline_insert_tools.py` | 13 | Generators/titles/scene detect |
| `item_marker_tools.py` | 11 | Timeline item markers & flags |
| `item_version_tools.py` | 11 | Clip versions/color groups |
| `fusion_tools.py` | 8 | Fusion comp management |
| `fusion_node_tools.py` | 14 | Fusion node graph manipulation |
| `gallery_tools.py` | 7 | Gallery albums & stills |
| `node_tools.py` | 9 | Node graph |
| `layout_preset_tools.py` | 22 | Layouts/burn-in/render presets |
| `dolby_stereo_tools.py` | 4 | Dolby Vision & 3D stereo |
| `folder_tools.py` | 4 | Bin transcription/export/IDs |
| `cache_tools.py` | 6 | Color/Fusion/node cache control |
| `quick_export_tools.py` | 2 | Quick Export presets & render |
| `keyframe_tools.py` | 2 | Keyframe mode get/set |
| `take_tools.py` | 7 | Take selector management |
| `magic_mask_tools.py` | 2 | AI magic mask create/regenerate |
| `matte_tools.py` | 5 | Clip/timeline matte management |
| `mark_tools.py` | 6 | Mark in/out on timelines & clips |
| `audio_mapping_tools.py` | 2 | Audio channel mapping inspection |
| `timeline_extras.py` | 17 | Timecodes, linked items, LUT export |
| `resolve_tools.py` | 9 | AI bridge tools (Gemini) |

## Dev Tooling

- **Lint/Format**: `ruff check .` / `ruff format .` (config in `pyproject.toml`)
- **Type check**: `pyright resolve_mcp/`
- **Tests**: `pytest tests/ -v` (import + convention tests — no Resolve required)
- **CI**: GitHub Actions runs lint, typecheck, and tests on push/PR
- **Hooks**: PostToolUse auto-runs ruff + pyright on `.py` edits; PreToolUse blocks `.env` edits and direct version field changes

## Build & Publish

```bash
# Use the /bump-publish skill, or manually:
# Bump version in pyproject.toml, then:
uv build && uv publish --token $PYPI_TOKEN
git add -A && git commit -m "..." && git push origin main
```

## Related

- **[resolve-assistant](https://github.com/jenkinsm13/resolve-assistant)** — AI editing assistant (separate MCP server)
- Install both: `pip install resolve-mcp[assistant]`
