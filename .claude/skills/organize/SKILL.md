---
name: organize
description: Auto-organize the DaVinci Resolve media pool — create bins and sort clips by type, camera, date, or filename patterns.
disable-model-invocation: true
---

# /organize — Auto-Organize Media Pool

Scan all clips in the media pool, create bins, and sort clips intelligently.

## Workflow

1. **List all bins** with `resolve_list_bins` to see current structure
2. **Search all clips** with `resolve_search_clips` (use `*` or empty to get all)
3. **Get clip info** for each clip with `resolve_get_clip_info` to read metadata (file path, resolution, fps, codec, duration, clip color)
4. **Analyze and categorize** each clip based on:
   - **File extension**: `.mp3/.wav/.aac` → Audio bin, `.jpg/.png/.tiff` → Stills bin
   - **Resolution**: 1920x1080 vs 3840x2160 → separate by resolution if mixed
   - **Frame rate**: 23.976 vs 59.94/119.88 → high frame rate clips likely B-roll/slow-mo
   - **Filename patterns**: `INT_`, `A-cam`, `B-cam`, `GoPro`, `DJI`, `drone` → camera bins
   - **Duration**: Very short clips (<5s) → Cutaways bin, very long (>10min) → Full Takes bin
   - **Codec**: `.r3d`, `.braw` → RAW bin
5. **Create bins** with `resolve_create_bin` for each category:
   - `A-Roll / Interviews` — long clips with audio
   - `B-Roll` — high fps, short clips, no dialogue
   - `Drone / Aerial` — DJI filenames or drone metadata
   - `Audio / Music` — audio-only files
   - `Stills / Graphics` — image files
   - `Slow Motion` — clips at 60fps+
6. **Move clips** with `resolve_move_clips` into their bins
7. **Color-code bins** by setting clip colors: Green for selected/good, default for unreviewed

## Customization

If the user provides specific instructions (e.g., "organize by camera" or "organize by date"), adapt the bin structure accordingly. The default is by clip type.

## Example Interactions

User: `/organize`
→ Scan all clips, create type-based bins, sort everything.

User: `/organize by camera`
→ Create bins for each camera (A-cam, B-cam, GoPro, Drone, etc.)

User: `/organize by date`
→ Create bins for each shooting day based on file creation dates.
