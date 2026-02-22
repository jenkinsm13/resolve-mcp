---
name: multi-deliver
description: Render multiple deliverables from one DaVinci Resolve timeline in a single batch — YouTube, Instagram, broadcast, ProRes master, etc.
disable-model-invocation: true
---

# /multi-deliver — Batch Render Multiple Formats

Queue multiple render jobs from the same timeline and render them all. One command for all your deliverables.

## Arguments

The user lists the formats they need, separated by commas, `+`, or `and`.

## Preset Definitions

Use these presets (same as `/deliver` skill):

| Preset | Format | Codec | Resolution |
|--------|--------|-------|------------|
| `youtube` | MP4 | H.264 | 1920x1080 |
| `youtube 4k` | MP4 | H.265 | 3840x2160 |
| `instagram` | MP4 | H.264 | 1080x1080 |
| `instagram reel` / `reel` / `tiktok` | MP4 | H.264 | 1080x1920 |
| `h265 4k` / `4k` | MP4 | H.265 | 3840x2160 |
| `h265 1080` / `1080` | MP4 | H.265 | 1920x1080 |
| `h264 1080` | MP4 | H.264 | 1920x1080 |
| `prores` | QuickTime | ProRes 422 | Timeline res |
| `prores hq` | QuickTime | ProRes 422 HQ | Timeline res |
| `prores proxy` | QuickTime | ProRes 422 Proxy | Timeline res |
| `dnxhd` | MXF | DNxHD | Timeline res |
| `broadcast` | MXF | DNxHR | 1920x1080 |

## Workflow

1. Parse the user's requested formats into a list of presets
2. For each preset:
   a. Use `resolve_set_render_format_and_codec` to set format and codec
   b. Use `resolve_set_render_settings` to set resolution and other settings
   c. Append a `CustomName` suffix to differentiate outputs (e.g., `TimelineName_youtube`, `TimelineName_instagram`)
   d. If the user specified an output directory, set `TargetDir`
   e. Use `resolve_add_render_job` to queue the job
3. After all jobs are queued, use `resolve_start_render` to begin (renders all queued jobs)
4. Poll with `resolve_get_render_status` and `resolve_list_render_jobs` until all jobs complete
5. Report final status for each deliverable: format, resolution, file path, success/failure

## Example Interactions

User: `/multi-deliver youtube + instagram reel + prores hq`
→ Queues 3 render jobs (H.264 1080p, H.264 1080x1920, ProRes HQ), renders all, reports results.

User: `/multi-deliver youtube, 4k, prores to /Volumes/Exports/`
→ Queues 3 jobs to specified directory.

User: `/multi-deliver all social`
→ Queues: youtube (1080p), instagram (square), instagram reel (vertical), tiktok (vertical)

User: `/multi-deliver broadcast + youtube 4k + prores hq`
→ Queues broadcast MXF, YouTube 4K H.265, and ProRes HQ master.
