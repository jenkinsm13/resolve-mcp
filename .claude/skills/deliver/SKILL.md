---
name: deliver
description: One-command render and export from DaVinci Resolve. Accepts a preset name or shorthand like "h265 4k", "prores proxy", "youtube", "instagram".
disable-model-invocation: true
---

# /deliver — Quick Render & Export

Set up render settings, add the job, start rendering, and poll until complete — all in one command.

## Arguments

The user provides a delivery target as free text. Map it to Resolve render settings:

| Shorthand | Format | Codec | Resolution | Notes |
|-----------|--------|-------|------------|-------|
| `h265 4k` or `4k` | MP4 | H.265 | 3840x2160 | Default high-quality delivery |
| `h265 1080` or `1080` | MP4 | H.265 | 1920x1080 | Standard HD |
| `h264 1080` | MP4 | H.264 | 1920x1080 | Maximum compatibility |
| `prores` or `prores 422` | QuickTime | Apple ProRes 422 | Timeline resolution | Editing/mastering codec |
| `prores proxy` | QuickTime | Apple ProRes 422 Proxy | Timeline resolution | Lightweight proxy |
| `prores hq` | QuickTime | Apple ProRes 422 HQ | Timeline resolution | High quality |
| `prores 4444` | QuickTime | Apple ProRes 4444 | Timeline resolution | With alpha channel |
| `youtube` | MP4 | H.264 | 1920x1080 | YouTube-optimized (high bitrate) |
| `instagram` | MP4 | H.264 | 1080x1080 | Square crop for IG feed |
| `instagram reel` or `reel` | MP4 | H.264 | 1080x1920 | 9:16 vertical |
| `tiktok` | MP4 | H.264 | 1080x1920 | 9:16 vertical |
| `dnxhd` | MXF | DNxHD | Timeline resolution | Broadcast delivery |

If the user provides a Resolve render preset name instead, use `resolve_load_render_preset` to load it directly.

## Workflow

1. **Parse the delivery target** from the user's argument
2. Use `resolve_set_render_format_and_codec` to set format and codec
3. Use `resolve_set_render_settings` to set resolution, frame rate, and any other settings (e.g., `SelectAllFrames: true`)
4. If the user specified an output directory, set `TargetDir`. Otherwise use the project default.
5. Use `resolve_add_render_job` to queue the job
6. Use `resolve_start_render` to begin rendering
7. Poll with `resolve_get_render_status` every few seconds until complete
8. Report final status: success, output path, file size if available

## Example Interactions

User: `/deliver h265 4k`
→ Set MP4/H.265 at 3840x2160, add job, start render, poll to completion.

User: `/deliver youtube`
→ Set MP4/H.264 at 1920x1080 with high bitrate, render.

User: `/deliver prores hq to /Volumes/Exports/`
→ Set QuickTime/ProRes 422 HQ, TargetDir = /Volumes/Exports/, render.

User: `/deliver "Custom Preset Name"`
→ Load the named preset, add job, render.
