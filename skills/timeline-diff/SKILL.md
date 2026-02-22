---
name: timeline-diff
description: Compare two DaVinci Resolve timelines and report what changed — clips added, removed, moved, trimmed, or reordered between versions.
disable-model-invocation: true
---

# /timeline-diff — Compare Two Timelines

Show what changed between two versions of a timeline. Essential for tracking revisions and understanding what the editor changed.

## Arguments

User provides two timeline names. If only one is given, compare it against the current timeline.

## Workflow

### 1. Gather clip data from both timelines

For each timeline:
- Use `resolve_set_current_timeline` to switch to it
- Use `resolve_get_timeline_info` to get duration, fps, track count
- For each video track (V1, V2, V3, etc.), use `resolve_list_clips_on_track` to get all clips
- For each clip, use `resolve_get_item_properties` and `resolve_get_clip_source_info` to get:
  - Source file name
  - Source in/out points
  - Timeline position (start frame, end frame)
  - Track number
  - Speed/retime settings
  - Enabled/disabled state

### 2. Compare

Build a diff by matching clips between timelines using source file name as the key:

**Added clips:** In timeline B but not in A (new source files on the timeline)
**Removed clips:** In timeline A but not in B
**Moved clips:** Same source file but different timeline position or track
**Trimmed clips:** Same source file, same position, but different in/out points
**Reordered clips:** Same clips on V1 but in different sequence order
**Duration change:** Overall timeline duration difference

### 3. Report

Format as a structured diff:

```
## Timeline Diff: "Edit v1" → "Edit v2"

**Duration:** 02:15:30 → 02:12:15 (−3:15)
**Tracks:** V1-V2 A1-A4 → V1-V3 A1-A4 (+1 video track)

### Added (3 clips)
+ V2 01:05:00 — drone_shot_042.mp4 (0:00–0:08)
+ V2 01:22:00 — broll_new_015.mp4 (0:00–0:12)
+ V3 00:00:00 — lower_third.png (still)

### Removed (2 clips)
− V1 00:45:10 — interview_take2.mp4 (was 0:15–0:45)
− V2 01:10:00 — old_broll_003.mp4 (was 0:00–0:06)

### Trimmed (4 clips)
~ V1 00:30:00 — interview_take1.mp4: in 0:10→0:12 out 0:45→0:42 (−5s)
~ V1 01:00:00 — hero_shot.mp4: in 0:00→0:02 (trimmed head)

### Moved (1 clip)
↕ broll_sunset.mp4: V2 01:30:00 → V2 01:15:00 (moved earlier)

### Summary
3 added, 2 removed, 4 trimmed, 1 moved
```

## Example Interactions

User: `/timeline-diff "Edit v1" "Edit v2"`
→ Compare the two named timelines, report all changes.

User: `/timeline-diff "Edit v2"`
→ Compare "Edit v2" against the currently active timeline.

User: `/timeline-diff "Rough Cut" "Fine Cut"`
→ Show what changed from rough to fine cut.
