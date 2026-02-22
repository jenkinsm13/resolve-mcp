# Color Consistency Checker

Post-grading quality check for DaVinci Resolve timelines. Verifies all clips are graded and grades are consistent.

## Checklist

Use the resolve-mcp tools to check each item:

### 1. Grade Coverage
- `resolve_list_clips_on_track` for V1 and V2 — get all clips
- For each clip, use `resolve_get_node_count` — if node count is 1 (default single corrector with no adjustments), the clip may be un-graded
- Use `resolve_get_cdl` on each clip — if slope/offset/power are all at default (1,1,1 / 0,0,0 / 1,1,1) and saturation is 1.0, the clip has no CDL grade
- Report any clips that appear un-graded

### 2. LUT Application
- Use `resolve_get_lut` on each clip
- Check for clips missing a LUT when others in the timeline have one (inconsistent look)
- Report which clips have LUTs and which don't

### 3. CDL Value Ranges
- Use `resolve_get_cdl` on each clip
- Flag extreme values that might indicate errors:
  - Slope values outside 0.5–2.0 range
  - Offset values outside -0.2–0.2 range
  - Power values outside 0.5–2.0 range
  - Saturation below 0.3 or above 2.0

### 4. Grade Consistency Across Similar Clips
- Compare CDL values between clips on the same track
- If most clips have similar grades but one is wildly different, flag it as a potential mismatch
- Pay special attention to clips from the same camera or scene (similar filenames)

### 5. Color Group Assignment
- Use `resolve_item_get_color_group` for each clip
- Check that clips are assigned to color groups if the project uses them
- Report any clips without a color group when others have one

## Output Format

Report findings as:
```
✅ Grade coverage — 24/24 clips graded on V1
⚠️  Un-graded clip — V2 at 00:32:10 "cutaway_015.mp4" (default node, no CDL)
✅ LUT consistency — All V1 clips use "Kodak 2383 D65"
❌ Missing LUT — V2 clip "drone_shot.mp4" has no LUT (others use "Kodak 2383 D65")
⚠️  Extreme CDL — V1 at 01:15:00 slope R=2.4 (outside normal range)
✅ Color groups — All clips assigned
```
