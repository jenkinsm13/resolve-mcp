# Timeline Auditor

Pre-delivery quality check for DaVinci Resolve timelines. Run this before rendering to catch issues.

## Checklist

Use the resolve-mcp tools to check each item:

### 1. Timeline Structure
- `resolve_get_timeline_info` — verify frame rate, resolution, and duration are correct
- `resolve_get_timeline_settings` — check for unexpected settings (wrong color science, mismatched output resolution)

### 2. Gaps and Black
- `resolve_list_clips_on_track` for V1 — check for gaps between clips (compare each clip's end frame to the next clip's start frame)
- If gaps exist, report their timecodes and durations

### 3. Disabled Clips
- `resolve_list_clips_on_track` for each video and audio track
- `resolve_get_item_properties` on each clip — check if any clips are disabled
- Report disabled clips with their timecodes

### 4. Frame Rate Mismatches
- `resolve_get_clip_source_info` for clips on V1 — compare source fps to timeline fps
- Flag any clips where source fps doesn't match timeline fps (potential judder)

### 5. Audio Tracks
- `resolve_list_clips_on_track` for each audio track — verify audio tracks have content
- Check for empty audio tracks that should have content (e.g., Music track with nothing on it)
- `resolve_get_audio_track_info` — check for muted tracks

### 6. Markers
- `resolve_list_markers` — check for any Red markers (usually indicate problems)
- Report any markers with "TODO", "FIX", "TEMP", or "PLACEHOLDER" in the name or note

### 7. Render Readiness
- `resolve_get_current_render_settings` — verify render format/codec are set
- Check that timeline duration is reasonable (not zero, not absurdly long)

## Output Format

Report findings as:
```
✅ Timeline structure — OK (24fps, 1920x1080, 02:15:30)
⚠️  Gap detected — V1 at 01:02:15 (12 frames)
❌ Disabled clip — V2 at 00:45:10 "B-roll_042.mp4"
⚠️  FPS mismatch — V1 clip "GoPro_001.mp4" is 59.94fps in 24fps timeline
✅ Audio tracks — OK
❌ Red marker at 01:30:00 — "FIX: jump cut"
✅ Render settings — MP4/H.265 ready
```
