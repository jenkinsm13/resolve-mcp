---
name: import-notes
description: Paste timecoded client feedback or review notes and auto-create color-coded markers on the DaVinci Resolve timeline at each timecode.
disable-model-invocation: true
---

# /import-notes — Import Timecoded Notes as Markers

Paste client feedback, director's notes, or review comments with timecodes and automatically create markers on the current timeline.

## Arguments

The user pastes their notes directly after the command. The notes can be in any common format — the skill parses them flexibly.

## Supported Formats

Parse these timecode formats (be flexible, editors use all of them):

| Format | Example |
|--------|---------|
| HH:MM:SS:FF | `01:02:15:03 — fix this transition` |
| HH:MM:SS | `01:02:15 needs color correction` |
| MM:SS | `2:15 - cut is too abrupt` |
| Seconds | `135s — bad audio here` |
| Frame.io style | `[01:02:15] comment text` |
| Numbered list | `1. 01:02:15 — note text` |

## Marker Color Mapping

Automatically assign marker colors based on note content keywords:

| Keywords | Color | Meaning |
|----------|-------|---------|
| fix, wrong, bad, error, mistake, reshoot, redo | Red | Problem |
| change, adjust, tweak, revise, update, move | Yellow | Needs attention |
| vfx, graphics, title, lower third, effect, cg | Purple | VFX/GFX needed |
| audio, sound, music, mix, levels, dialogue | Cyan | Audio note |
| love, great, perfect, approved, keep, good | Green | Approved |
| (no keyword match) | Blue | General note |

## Workflow

1. Use `resolve_get_timeline_info` to get fps and timeline name
2. Parse each note line to extract:
   - Timecode (convert to frame number using timeline fps)
   - Note text (everything after the timecode)
   - Color (from keyword matching above)
3. For each note, use `resolve_add_marker_at` with:
   - `frame`: calculated frame number
   - `color`: auto-detected color
   - `name`: first ~40 chars of note text (truncated for marker name field)
   - `note`: full note text
   - `duration`: 1 frame
4. Report: "Added X markers to timeline '[name]'" with a summary by color

## Example Interactions

User:
```
/import-notes
01:02:15 — fix this transition, too abrupt
01:05:30 — love this shot, keep it
01:08:00 — need VFX cleanup on the background
01:12:45 — audio levels drop here
01:15:00 — general note: consider a different song
```
→ Parses 5 notes, creates Red/Green/Purple/Cyan/Blue markers respectively.

User:
```
/import-notes
[00:30] cut feels slow
[01:15] great energy here
[02:00] needs a lower third
```
→ Parses MM:SS format, creates 3 markers.
