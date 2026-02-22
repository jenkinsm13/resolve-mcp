---
name: prep-timeline
description: Create a new DaVinci Resolve timeline with a standard professional track layout — video tracks for A-roll, B-roll, GFX, and audio tracks for dialogue, SFX, music.
disable-model-invocation: true
---

# /prep-timeline — Set Up a New Timeline

Create a timeline with a professional track layout in one command.

## Arguments

User provides: timeline name, and optionally frame rate and resolution.

Defaults: use current project settings for fps and resolution.

## Standard Track Layout

| Track | Type | Name | Purpose |
|-------|------|------|---------|
| V1 | video | A-Roll | Primary footage, interviews, talking heads |
| V2 | video | B-Roll | Cutaways, supplementary footage |
| V3 | video | GFX | Graphics, titles, lower thirds, overlays |
| A1 | audio | Dialogue | Synced dialogue from A-roll |
| A2 | audio | SFX | Sound effects, foley, ambience |
| A3 | audio | Music | Background music, score |
| A4 | audio | VO | Voiceover, narration |

## Workflow

1. Use `resolve_create_empty_timeline` with the given name
2. The timeline starts with V1 and A1 by default
3. Use `resolve_add_track` to add:
   - V2 (video), V3 (video)
   - A2 (audio), A3 (audio), A4 (audio)
4. Use `resolve_set_track_name` to name each track:
   - V1 → "A-Roll", V2 → "B-Roll", V3 → "GFX"
   - A1 → "Dialogue", A2 → "SFX", A3 → "Music", A4 → "VO"
5. If the user specified custom settings (fps, resolution), apply them with `resolve_set_timeline_setting`
6. Confirm: "Timeline '[name]' ready — 3 video tracks, 4 audio tracks"

## Example Interactions

User: `/prep-timeline "Summer Campaign"`
→ Create timeline with default project settings, apply standard track layout.

User: `/prep-timeline "Instagram Reel" 30fps`
→ Create timeline at 30fps with standard tracks.

User: `/prep-timeline "Doc v1" 24fps 4k`
→ Create 24fps 4K timeline with standard tracks.
