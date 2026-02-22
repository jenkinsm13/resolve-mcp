# resolve-mcp

**The most comprehensive MCP server for DaVinci Resolve.** 295+ tools covering the complete DaVinci Resolve scripting API (v20.3) — control every aspect of Resolve from Claude, ChatGPT, or any MCP-compatible AI assistant.

[![PyPI](https://img.shields.io/pypi/v/resolve-mcp)](https://pypi.org/project/resolve-mcp/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What is resolve-mcp?

`resolve-mcp` is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes **295+ tools** for controlling DaVinci Resolve through AI assistants like Claude, Claude Code, Cursor, Windsurf, ChatGPT, and any other MCP client.

It turns natural language into Resolve scripting API calls — letting you manage projects, edit timelines, grade color, render deliverables, manage media pools, control Fusion compositions, and more, all through conversation with an AI.

### Why resolve-mcp?

- **Complete API coverage** — 295+ tools spanning every Resolve scripting API surface: projects, media pool, timelines, editing, markers, rendering, color grading, Fusion, Fairlight, galleries, node graphs, Dolby Vision, and stereo 3D
- **Zero code required** — just talk to your AI assistant: *"Create a new timeline called 'Final Cut' at 24fps"* or *"Add a dissolve transition to every cut point"*
- **One-line install** — `uvx resolve-mcp` or `pip install resolve-mcp`
- **Works with any MCP client** — Claude Desktop, Claude Code, Cursor, Windsurf, VS Code + Continue, or your own MCP client
- **Optional AI editing tools** — 3 bonus Gemini-powered tools for AI timeline analysis, marker-driven editing, and automated marker placement
- **Cross-platform** — macOS, Windows, Linux (wherever Resolve runs)

---

## Quick Start

### Prerequisites

1. **DaVinci Resolve** (Free or Studio) must be running
2. Enable scripting: `Preferences → System → General → External scripting using = Network`
3. **Python 3.11+**
4. **ffmpeg** (for AI tools only): `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)

### Install

```bash
# Using uvx (recommended — runs in isolated environment)
uvx resolve-mcp

# Using pip
pip install resolve-mcp

# Using pipx
pipx install resolve-mcp

# Install with the AI editing assistant (resolve-assistant) included
pip install resolve-mcp[assistant]
```

### Configure Claude Desktop

Add to your Claude Desktop MCP config:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "resolve-mcp": {
      "command": "uvx",
      "args": ["resolve-mcp"]
    }
  }
}
```

### Configure Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "resolve-mcp": {
      "command": "uvx",
      "args": ["resolve-mcp"]
    }
  }
}
```

### Configure Cursor / Windsurf / VS Code

Follow your editor's MCP server configuration docs, pointing to `uvx resolve-mcp` as the command.

### Enable AI Bridge Tools (Optional)

To use the 3 Gemini-powered AI tools (`resolve_analyze_timeline`, `resolve_add_markers`, `resolve_build_from_markers`), set your Gemini API key:

```json
{
  "mcpServers": {
    "resolve-mcp": {
      "command": "uvx",
      "args": ["resolve-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

> **Windows note:** If `uvx` is not on your system PATH, use the full path to `uvx.exe` (e.g., `C:\\Users\\YOU\\.local\\bin\\uvx.exe`) as the `"command"` value.

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com/).

---

## Using Both Servers Together — resolve-mcp + resolve-assistant

`resolve-mcp` gives you **295+ tools for direct DaVinci Resolve control** — projects, timelines, editing, color grading, rendering, Fusion, Fairlight, and more.

**[resolve-assistant](https://github.com/jenkinsm13/resolve-assistant)** is a separate MCP server that adds **AI-powered automatic editing** — point it at a folder of footage and give it an editing instruction, and it uses Google Gemini to watch every frame, plan the edit, and build the timeline in Resolve automatically.

**They are independent MCP servers.** You can use either one alone, or both together for the complete AI video editing toolkit. When used together, you get full manual control over Resolve (resolve-mcp) plus AI-driven footage analysis and automatic timeline building (resolve-assistant).

### Install Both With One Command

```bash
# Install resolve-mcp with the AI editing assistant included
pip install resolve-mcp[assistant]

# Or install them separately
pip install resolve-mcp
pip install resolve-assistant
```

### Configure Both Servers

Because they are **two separate MCP servers**, each needs its own entry in your Claude Desktop or Claude Code config. Here is the complete configuration with both servers:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows, `~/.config/Claude/claude_desktop_config.json` on Linux):

```json
{
  "mcpServers": {
    "resolve-mcp": {
      "command": "uvx",
      "args": ["resolve-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    },
    "resolve-assistant": {
      "command": "uvx",
      "args": ["resolve-assistant"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

**Claude Code** (`.mcp.json` in your project root):

```json
{
  "mcpServers": {
    "resolve-mcp": {
      "command": "uvx",
      "args": ["resolve-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    },
    "resolve-assistant": {
      "command": "uvx",
      "args": ["resolve-assistant"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

> **Note:** `GEMINI_API_KEY` is optional for resolve-mcp (only the 3 AI bridge tools need it) but **required** for resolve-assistant. Both servers use the same Gemini API key.

### Which Server Do I Need?

| Use Case | resolve-mcp | resolve-assistant | Both |
|----------|:-----------:|:-----------------:|:----:|
| Control Resolve via AI (projects, timelines, editing, rendering) | Yes | | |
| Color grading, Fusion, Fairlight, node graphs | Yes | | |
| AI footage analysis — watch every frame, transcribe speech, tag content | | Yes | |
| AI automatic editing — give an instruction, get a timeline | | Yes | |
| Full AI video editing pipeline with manual Resolve control | | | Yes |
| AI timeline critique + marker-driven editing | Yes | | |

For more about the AI editing assistant, see the **[resolve-assistant documentation](https://github.com/jenkinsm13/resolve-assistant)**.

---

## Tool Categories

### Project Management (10 tools)
Create, open, close, save, and configure DaVinci Resolve projects. Switch databases, manage project settings, and query project metadata.

| Tool | Description |
|------|-------------|
| `resolve_list_projects` | List all projects in the current database |
| `resolve_create_project` | Create a new project with optional settings |
| `resolve_load_project` | Open a project by name |
| `resolve_save_project` | Save the current project |
| `resolve_get_project_settings` | Read project settings (resolution, frame rate, etc.) |
| `resolve_set_project_setting` | Modify a project setting |
| `resolve_switch_page` | Navigate to a specific Resolve page (edit, color, deliver, etc.) |
| `resolve_get_version` | Get Resolve version and edition info |
| `resolve_get_product_name` | Get product name (Free vs Studio) |
| `resolve_get_project_id` | Get the unique project ID |

### Media Pool (21 tools)
Import, organize, search, and manage clips in the media pool. Create bins, move clips, set metadata, relink media, and more.

| Tool | Description |
|------|-------------|
| `resolve_import_media` | Import files into the media pool |
| `resolve_import_folder_to_media_pool` | Import an entire folder |
| `resolve_create_bin` | Create a new media pool bin |
| `resolve_list_bins` | List all bins with clip counts |
| `resolve_search_clips` | Search clips by name |
| `resolve_get_clip_info` | Get detailed clip properties |
| `resolve_set_clip_metadata` | Set clip metadata fields |
| `resolve_set_clip_color` | Set clip color label |
| `resolve_move_clips` | Move clips between bins |
| `resolve_delete_clips` | Delete clips from the pool |
| `resolve_relink_clips` | Relink offline media |
| `resolve_auto_sync_audio` | Auto-sync audio to video |
| ...and more | |

### Timeline Management (15 tools)
Create, duplicate, delete, import, and export timelines. Manage tracks, set timeline properties, and navigate between timelines.

| Tool | Description |
|------|-------------|
| `resolve_create_empty_timeline` | Create a blank timeline |
| `resolve_create_timeline_from_clips` | Create a timeline from selected clips |
| `resolve_list_timelines` | List all timelines in the project |
| `resolve_get_timeline_info` | Get timeline metadata (tracks, duration, etc.) |
| `resolve_set_current_timeline` | Switch to a specific timeline |
| `resolve_duplicate_timeline` | Duplicate a timeline |
| `resolve_delete_timelines` | Delete timelines |
| `resolve_export_timeline` | Export as AAF, EDL, XML, FCPXML, OTIO, etc. |
| `resolve_import_timeline_from_file` | Import a timeline from file |
| `resolve_add_track` | Add video, audio, or subtitle tracks |
| `resolve_delete_track` | Remove a track |
| `resolve_set_track_name` | Rename a track |
| `resolve_set_track_enabled` | Enable/disable a track |
| `resolve_set_track_locked` | Lock/unlock a track |
| `resolve_get_timeline_settings` | Read timeline-level settings |

### Editing (12 tools)
Manipulate timeline items — set properties, transforms, composite modes, speed changes, and clip-level operations.

| Tool | Description |
|------|-------------|
| `resolve_list_clips_on_track` | List all clips on a given track |
| `resolve_get_item_properties` | Read clip properties (zoom, pan, opacity, etc.) |
| `resolve_set_item_properties` | Set clip properties |
| `resolve_set_clip_enabled` | Enable/disable a clip |
| `resolve_set_clip_color_on_timeline` | Color-code a clip on the timeline |
| `resolve_delete_clips_from_timeline` | Remove clips from the timeline |
| `resolve_link_clips` | Link video and audio clips |
| `resolve_unlink_clips` | Unlink video from audio |
| `resolve_create_compound_clip` | Create a compound clip |
| `resolve_stabilize_clip` | Run stabilization analysis |
| `resolve_smart_reframe` | Apply Smart Reframe (Studio) |
| `resolve_get_clip_source_info` | Get source media info for a timeline clip |

### Markers & Playhead (9 tools)
Add, edit, delete, and query markers on timelines. Control playhead position.

| Tool | Description |
|------|-------------|
| `resolve_list_markers` | List all markers on the current timeline |
| `resolve_add_marker_at` | Add a marker at a specific frame |
| `resolve_delete_markers` | Delete markers by color |
| `resolve_delete_marker_at` | Delete a marker at a specific frame |
| `resolve_update_marker_data` | Update marker name, note, or color |
| `resolve_get_marker_data` | Read marker data at a frame |
| `resolve_get_playhead` | Get current playhead position |
| `resolve_set_playhead` | Move playhead to a specific frame |

### Rendering (14 tools)
Configure render settings, manage the render queue, and control rendering jobs.

| Tool | Description |
|------|-------------|
| `resolve_add_render_job` | Add a render job to the queue |
| `resolve_start_render` | Start rendering |
| `resolve_stop_render` | Stop rendering |
| `resolve_get_render_status` | Check render progress |
| `resolve_list_render_jobs` | List all jobs in the queue |
| `resolve_delete_render_job` | Remove a job from the queue |
| `resolve_get_render_presets` | List available render presets |
| `resolve_load_render_preset` | Load a render preset |
| `resolve_set_render_settings` | Configure render settings |
| `resolve_set_render_format_and_codec` | Set format and codec |
| `resolve_get_render_formats` | List available formats and codecs |
| `resolve_get_current_render_settings` | Read current render settings |
| `resolve_get_render_resolutions` | Get available resolutions |
| `resolve_is_rendering` | Check if a render is in progress |

### Color Grading (12 tools)
Control color grading — apply LUTs, set CDL values, manage nodes, copy grades, grab stills, and export frames.

| Tool | Description |
|------|-------------|
| `resolve_apply_lut` | Apply a LUT to a clip |
| `resolve_get_lut` | Read the current LUT |
| `resolve_set_cdl` | Set CDL (slope, offset, power, saturation) |
| `resolve_get_cdl` | Read CDL values |
| `resolve_get_node_count` | Count nodes in the grade |
| `resolve_reset_grades` | Reset all grading |
| `resolve_copy_grade` | Copy grade from one clip to another |
| `resolve_grab_still` | Capture a still from the current frame |
| `resolve_export_frame` | Export the current frame as an image |
| `resolve_list_color_groups` | List color groups |
| `resolve_add_color_group` | Create a new color group |
| `resolve_delete_color_group` | Delete a color group |

### Fusion (8 tools)
Manage Fusion compositions on timeline clips.

| Tool | Description |
|------|-------------|
| `resolve_item_list_fusion_comps` | List Fusion comps on a clip |
| `resolve_item_add_fusion_comp` | Add a new Fusion comp |
| `resolve_item_import_fusion_comp` | Import a .comp file |
| `resolve_item_export_fusion_comp` | Export a Fusion comp |
| `resolve_item_delete_fusion_comp` | Delete a Fusion comp |
| `resolve_item_load_fusion_comp` | Load a Fusion comp for editing |
| `resolve_item_rename_fusion_comp` | Rename a Fusion comp |

### Fairlight Audio (4 tools)
Control Fairlight audio features — voice isolation, audio insertion, and track info.

| Tool | Description |
|------|-------------|
| `resolve_get_voice_isolation` | Check voice isolation status |
| `resolve_set_voice_isolation` | Enable/disable voice isolation |
| `resolve_insert_audio_at_playhead` | Insert audio at the playhead |
| `resolve_get_audio_track_info` | Get audio track details |

### Additional Categories

- **Clip Metadata** (18 tools) — markers, flags, proxy management, transcription
- **Timeline Items** (11 tools) — item-level markers and flags
- **Clip Versions** (11 tools) — version management, color group assignment
- **Gallery & Stills** (7 tools) — still albums, still export/import
- **Node Graph** (5 tools) — node labels, enable/disable, tool inspection
- **Layout Presets** (22 tools) — UI layouts, render presets, burn-in presets
- **Dolby Vision & Stereo 3D** (4 tools) — Dolby Vision analysis, stereo conversion
- **Media Storage** (3 tools) — browse volumes and storage locations
- **Project Manager** (10 tools) — archive, delete, import, restore projects
- **Bin/Folder Operations** (4 tools) — transcription, metadata export, folder IDs
- **Generators & Titles** (13 tools) — insert generators, titles, Fusion compositions, scene cut detection

### AI Bridge Tools (3 tools, requires GEMINI_API_KEY)

| Tool | Description |
|------|-------------|
| `resolve_analyze_timeline` | AI-powered editorial critique of the current timeline |
| `resolve_add_markers` | Add director's note markers from an edit plan |
| `resolve_build_from_markers` | Fill marker-defined slots with AI-selected footage |

### MCP Resources (Read-Only)

| Resource URI | Description |
|--------------|-------------|
| `resolve://version` | Resolve version and edition |
| `resolve://project` | Current project name and settings |
| `resolve://timelines` | All timelines with track counts |
| `resolve://bins` | Media pool bin tree with clip counts |
| `resolve://render-queue` | Render job queue with statuses |

---

## Usage Examples

Once configured, just talk to your AI assistant naturally:

### Project Management
> "List all my Resolve projects"
> "Create a new project called 'Summer Campaign' at 4K 24fps"
> "What are the current project settings?"

### Media Pool
> "Import all files from /Volumes/Media/Footage into the 'Raw' bin"
> "How many clips are in the 'B-Roll' bin?"
> "Set the clip color of all clips in 'Interviews' to Blue"

### Timeline Editing
> "Create a new timeline called 'Final Cut v3' with 2 video and 4 audio tracks"
> "List all clips on video track 1"
> "Add a Blue marker at frame 1200 with the note 'Great reaction shot'"

### Rendering
> "Set up a render job for H.265 MP4 at 4K"
> "Start rendering and tell me when it's done"
> "What render presets are available?"

### Color Grading
> "Apply the 'Kodak 2383' LUT to the current clip"
> "Set the CDL lift to add warmth to the shadows"
> "Grab a still from the current frame"

### AI-Powered Analysis (requires Gemini)
> "Analyze the current timeline and give me editorial feedback"
> "Build a timeline from markers using the footage in /Volumes/Media/Footage"

---

## Claude Code Plugin — Skills, Agents & Hooks

This repo is also a **Claude Code plugin** that installs 13 editor-focused skills, 3 specialized agents, and safety hooks directly into Claude Code.

### Install Everything With One Command

```bash
claude plugin add github.com/jenkinsm13/resolve-mcp
```

This installs the **MCP server** (295+ tools) AND all skills, agents, and hooks in one step. No separate MCP configuration needed — the plugin bundles it all.

> **Note:** Set your `GEMINI_API_KEY` in the MCP server config after install if you want the AI bridge tools. The 215+ Resolve tools work without it.

### Skills (invoke with `/skill-name`)

| Skill | Description |
|-------|-------------|
| `/color-assist` | AI color grading — exports sRGB frame, analyzes it visually, applies CDL adjustments |
| `/match-reference` | Match a reference image — compare side-by-side, adjust CDL to match the look |
| `/deliver` | One-command render with presets (H.265 4K, ProRes, YouTube, Instagram, TikTok) |
| `/multi-deliver` | Batch render multiple deliverables from one timeline |
| `/preflight` | Full pre-delivery QC — gaps, disabled clips, FPS mismatches, un-graded clips, markers |
| `/dolby-vision` | Dolby Vision render pipeline with profile selection and analyzer |
| `/review-cut` | Render review cut + AI editorial feedback via Gemini |
| `/archive` | Export complete project archive (DRP + media manifest + timelines + markers) |
| `/prep-timeline` | Create timeline with standard track layout (V1 A-Roll, V2 B-Roll, V3 GFX, etc.) |
| `/organize` | Auto-organize media pool into bins by clip type |
| `/markers-to-notes` | Export timeline markers as editorial notes markdown |
| `/import-notes` | Parse timecoded client notes into color-coded markers |
| `/timeline-diff` | Compare two timelines — report added, removed, trimmed, moved clips |

### Agents

| Agent | Description |
|-------|-------------|
| `color-analyst` | Structured color analysis with CDL recommendations (dispatched by `/color-assist`) |
| `timeline-auditor` | Pre-delivery QC for gaps, disabled clips, FPS mismatches, markers |
| `color-consistency-checker` | Post-grading QC for grade coverage, LUT consistency, CDL ranges |

### Hooks

- **`.env` protection** — blocks editing of `.env` files containing API keys
- **Destructive operation warning** — warns before delete operations in Resolve (clips, timelines, grades, markers, bins, projects)

> **Note:** The plugin bundles both the MCP server and all skills/agents/hooks. For standalone MCP server install (without skills), use `uvx resolve-mcp` or `pip install resolve-mcp`.

---

## Architecture

```
resolve-mcp
├── resolve_mcp/               # Python package (installed via pip/uvx)
│   ├── __init__.py            # Package init, registers all tool modules
│   ├── __main__.py            # python -m resolve_mcp entry point
│   ├── config.py              # FastMCP server + optional Gemini client
│   ├── resolve.py             # DaVinci Resolve scripting API connection
│   ├── errors.py              # Error handling + @safe_resolve_call decorator
│   ├── resources.py           # MCP resources (resolve://project, etc.)
│   ├── project_tools.py       # Project management (10 tools)
│   ├── media_pool_tools.py    # Media pool operations (11 tools)
│   ├── timeline_mgmt_tools.py # Timeline management (15 tools)
│   ├── edit_tools.py          # Timeline item editing (12 tools)
│   ├── marker_tools.py        # Markers & playhead (9 tools)
│   ├── render_tools.py        # Render pipeline (14 tools)
│   ├── color_tools.py         # Color grading (12 tools)
│   ├── fusion_tools.py        # Fusion comp management (8 tools)
│   ├── fairlight_tools.py     # Fairlight audio (4 tools)
│   ├── ...                    # 10+ more tool modules
│   └── resolve_ai_tools.py    # AI bridge tools (3 tools)
├── skills/                    # Claude Code plugin skills
│   ├── color-assist/SKILL.md
│   ├── deliver/SKILL.md
│   ├── preflight/SKILL.md
│   └── ...                    # 13 skills total
├── agents/                    # Claude Code plugin agents
│   ├── color-analyst.md
│   ├── timeline-auditor.md
│   └── color-consistency-checker.md
├── hooks/hooks.json           # Claude Code plugin hooks
├── .claude-plugin/plugin.json # Plugin manifest
├── pyproject.toml
├── .env.example
└── README.md
```

### How It Works

1. **resolve-mcp** starts a FastMCP server that registers 295+ tools
2. Your AI client (Claude, Cursor, etc.) connects via the MCP protocol
3. When you make a request, the AI selects the appropriate tool(s)
4. Each tool calls the DaVinci Resolve scripting API via the Python SDK
5. Results are returned as structured text to the AI for interpretation

The server connects to Resolve over the network scripting interface, which must be enabled in Resolve's preferences. No plugins or extensions needed — just enable the scripting API and run the server.

---

## Troubleshooting

### "DaVinci Resolve is not running"
- Make sure Resolve is open
- Enable scripting: `Preferences → System → General → External scripting using = Network`
- Restart Resolve after enabling scripting

### "No project open in Resolve"
- Open or create a project in Resolve before using project-dependent tools

### Tools not appearing in Claude Desktop
- Restart Claude Desktop after modifying `claude_desktop_config.json`
- Check the MCP server logs in Claude Desktop's developer console
- Verify `uvx resolve-mcp` runs successfully from the terminal

### AI bridge tools return "GEMINI_API_KEY not set"
- Add `GEMINI_API_KEY` to the `env` section of your MCP config
- The 215+ Resolve tools work without Gemini — only the 3 AI bridge tools require it

---

## DaVinci Resolve API Compatibility

- **Tested with:** DaVinci Resolve 20.3 (Free and Studio)
- **Platform support:** macOS (Apple Silicon + Intel), Windows, Linux
- **Studio-only features** are clearly marked — the server gracefully handles Free edition limitations

---

## Related Projects

- **[resolve-assistant](https://github.com/jenkinsm13/resolve-assistant)** — AI-powered video editing assistant that uses Google Gemini to analyze footage, plan professional edits, and build timelines in DaVinci Resolve automatically. Install alongside resolve-mcp with `pip install resolve-mcp[assistant]` for the complete AI video editing toolkit.
- **[FastMCP](https://github.com/jlowin/fastmcp)** — The MCP framework powering this server
- **[Model Context Protocol](https://modelcontextprotocol.io)** — The open protocol for AI tool use

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Please open an issue or PR on [GitHub](https://github.com/jenkinsm13/resolve-mcp).

---

*Built for video editors, colorists, and post-production professionals who want to control DaVinci Resolve with AI. Works with Claude Desktop, Claude Code, Cursor, Windsurf, ChatGPT, and any MCP-compatible client. Pair with [resolve-assistant](https://github.com/jenkinsm13/resolve-assistant) for AI-powered automatic editing.*
