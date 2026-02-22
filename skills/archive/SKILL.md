---
name: archive
description: Archive a DaVinci Resolve project — export the .drp project file, media list, timeline markers, render queue status, and editorial notes as a complete archive package.
disable-model-invocation: true
---

# /archive — Project Archive Package

Export everything needed to fully document and archive a completed project.

## Arguments

- Output directory (required): where to save the archive
- Optional: `with render` to also render a final ProRes master

## Workflow

### 1. Create archive folder

Create a timestamped folder at the specified path:
`[ProjectName]_archive_[YYYY-MM-DD]/`

### 2. Export project file

Use `resolve_export_project` with `with_stills_and_luts=True` to export the `.drp` file into the archive folder.

### 3. Gather project metadata

Use `resolve_get_project_settings` to get all project settings. Format as JSON and save to `project_settings.json` in the archive folder.

Use `resolve_get_version` to record the Resolve version used.

### 4. Export media list

Use `resolve_list_bins` to get the bin structure.
For each bin, use `resolve_search_clips` and `resolve_get_clip_info` to build a complete media manifest:

```json
{
  "clips": [
    {
      "name": "clip_001.mp4",
      "path": "/Volumes/Media/clip_001.mp4",
      "bin": "B-Roll",
      "duration": "00:01:23:15",
      "resolution": "3840x2160",
      "fps": 24.0,
      "codec": "H.265"
    }
  ]
}
```

Save as `media_manifest.json`.

### 5. Export timeline info

For each timeline (use `resolve_list_timelines`):
- `resolve_get_timeline_info` — duration, track count, fps
- `resolve_list_clips_on_track` for each track — clip list with positions
- `resolve_list_markers` — all markers

Save as `timelines.json`.

### 6. Export editorial notes

Use `resolve_list_markers` on each timeline. Format markers as editorial notes (same as `/markers-to-notes` skill) and save as `editorial_notes.md`.

### 7. Export render queue

Use `resolve_list_render_jobs` to document any pending or completed renders. Save as `render_queue.json`.

### 8. Optional: Render final master

If the user requested `with render`:
- Set ProRes 422 HQ at timeline resolution
- Render to the archive folder as `[ProjectName]_master.mov`
- Poll until complete

### 9. Save project

Use `resolve_save_project` to ensure the project is saved.

### 10. Report

Output the complete archive manifest:

```
# Archive Complete — [Project Name]
**Location:** /path/to/archive/
**Date:** [today]
**Resolve Version:** [version]

## Contents
- ProjectName.drp (project file with stills + LUTs)
- project_settings.json (all project settings)
- media_manifest.json (X clips across Y bins)
- timelines.json (X timelines)
- editorial_notes.md (X markers across all timelines)
- render_queue.json (X render jobs)
- ProjectName_master.mov (ProRes HQ master) [if rendered]

## Media Summary
- Total clips: X
- Total duration: HH:MM:SS
- Source locations: /Volumes/..., /Volumes/...
```

## Example Interactions

User: `/archive /Volumes/Archives/`
→ Full archive package to the specified directory.

User: `/archive ~/Desktop/ with render`
→ Full archive + ProRes HQ master render.

User: `/archive /Volumes/Projects/done/`
→ Archive to the projects done folder.
