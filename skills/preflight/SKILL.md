---
name: preflight
description: Full pre-delivery QC check on the current DaVinci Resolve timeline — runs timeline audit and color consistency check together, then summarizes all issues.
disable-model-invocation: true
---

# /preflight — Pre-Delivery Quality Check

Run a comprehensive quality check before rendering final deliverables. Combines the timeline-auditor and color-consistency-checker into one pass.

## Workflow

Run ALL of the following checks on the current timeline and compile results into a single report.

### Timeline Structure
- `resolve_get_timeline_info` — verify frame rate, resolution, duration
- `resolve_get_timeline_settings` — check for unexpected settings

### Gap Detection
- `resolve_list_clips_on_track` for V1 — check for gaps between clips
- Compare each clip's end frame to the next clip's start frame
- Report gaps with timecodes and durations

### Disabled Clips
- For each video and audio track, `resolve_list_clips_on_track`
- `resolve_get_item_properties` on each — check for disabled clips
- Report with timecodes

### Frame Rate Mismatches
- `resolve_get_clip_source_info` for V1 clips — compare source fps to timeline fps
- Flag mismatches (potential judder/pulldown issues)

### Audio Checks
- Check all audio tracks have content (not empty)
- `resolve_get_audio_track_info` — check for muted tracks
- Flag audio tracks that are empty when they shouldn't be

### Marker Review
- `resolve_list_markers` — flag Red markers (problems), Yellow (warnings)
- Flag markers with "TODO", "FIX", "TEMP", "PLACEHOLDER", "WIP" in name/note
- These indicate unfinished work

### Color Grade Coverage
- For V1 and V2 clips, `resolve_get_node_count` — check for default/un-graded clips (1 node with no adjustments)
- `resolve_get_cdl` — check for default CDL values (all neutral = no grade)
- `resolve_get_lut` — check for LUT consistency (all clips should have same LUT or intentionally different)

### CDL Value Ranges
- Flag extreme values: slope outside 0.5–2.0, offset outside -0.2–0.2, power outside 0.5–2.0, saturation below 0.3 or above 2.0

### Render Readiness
- `resolve_get_current_render_settings` — verify format/codec are set
- Check timeline duration is non-zero

## Output Format

```
# Preflight Report — [Timeline Name]
**Date:** [today]  |  **Duration:** [HH:MM:SS]  |  **Resolution:** [WxH]  |  **FPS:** [fps]

## ✅ Passed (X checks)
- Timeline structure OK
- No gaps detected
- Audio tracks populated
- Render settings configured

## ⚠️ Warnings (X issues)
- FPS mismatch: V1 clip "GoPro_001.mp4" is 59.94fps in 24fps timeline
- Yellow marker at 01:15:00 — "needs client approval"
- 2 clips on V2 missing LUT (others use "Kodak 2383 D65")

## ❌ Problems (X issues)
- Gap on V1 at 01:02:15 (12 frames of black)
- Disabled clip on V2 at 00:45:10 "B-roll_042.mp4"
- Red marker at 01:30:00 — "FIX: jump cut"
- Un-graded clip on V1 at 00:20:00 "interview_03.mp4"

## Verdict
[READY / NOT READY — X problems must be fixed before delivery]
```

## Example Interactions

User: `/preflight`
→ Run full QC, output preflight report with pass/warn/fail for each check.
