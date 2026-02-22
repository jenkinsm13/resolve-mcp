---
name: review-cut
description: Render a quick review cut with burned-in timecode and watermark, then feed it to Gemini so the AI can see the current state of the timeline and give editorial feedback.
disable-model-invocation: true
---

# /review-cut — Review Cut + AI Visual Feedback

Render a lightweight review export, then upload it to Gemini so the AI can actually watch the timeline and give feedback. Optionally save the review file for sending to clients.

## Arguments

- No arguments: render review, upload to Gemini, get AI feedback
- `save to /path/`: also save the review render to disk
- `for client`: render with watermark text (e.g., "REVIEW COPY — NOT FOR DISTRIBUTION")
- `feedback on pacing`: give Gemini a specific focus area

## Workflow

### 1. Get timeline info

Use `resolve_get_timeline_info` to get the timeline name, duration, frame rate, and resolution.

### 2. Render a low-res review cut

Set up a lightweight render specifically for AI review and client screening:

- Use `resolve_set_render_format_and_codec` → MP4 / H.264
- Use `resolve_set_render_settings` with:
  ```json
  {
    "SelectAllFrames": true,
    "FormatWidth": "1280",
    "FormatHeight": "720",
    "VideoQuality": "10000000"
  }
  ```
  (720p, low bitrate — fast to render, small enough to upload to Gemini)

**Burned-in timecode:** Check if a burn-in preset exists with `resolve_get_render_presets`. If there's one with "burn" or "timecode" in the name, load it. Otherwise, set render settings to enable data burn-in if the API supports it, or inform the user to enable it manually in the Deliver page.

**Watermark:** If the user requested `for client`, note that the watermark text should be set manually in Resolve's burn-in settings (the scripting API has limited burn-in control). Mention this to the user.

- Use `resolve_add_render_job` to queue
- Use `resolve_start_render` to begin
- Poll with `resolve_get_render_status` until complete

### 3. Upload to Gemini for visual analysis

This is the key differentiator — the AI actually watches the edit.

- Use `resolve_analyze_timeline` which uploads the timeline's source proxies to Gemini and runs a full editorial critique
- This gives Gemini visual context of what's actually on the timeline

If `resolve_analyze_timeline` is not available (no Gemini key), skip this step and just deliver the rendered file.

### 4. Return feedback

Combine the Gemini critique with practical next steps:

- **Pacing notes** — which sections drag, which feel rushed
- **Cut quality** — jump cuts, bad match cuts, continuity issues
- **Audio** — gaps in dialogue, music drops, levels
- **Story** — does the narrative track? Are the best moments featured?
- **Technical** — any obvious issues (black frames, flash frames, out-of-sync)

If the user specified a focus area (e.g., "feedback on pacing"), tell Gemini to prioritize that.

### 5. Save if requested

If the user asked to save, report the render output path. If they asked `for client`, remind them to verify the watermark/burn-in before sending.

## Example Interactions

User: `/review-cut`
→ Render 720p H.264, run resolve_analyze_timeline for AI feedback, report critique.

User: `/review-cut save to ~/Desktop/`
→ Same + save the rendered file.

User: `/review-cut for client`
→ Render with TC burn-in note about watermark, save for sending.

User: `/review-cut feedback on pacing and music sync`
→ Render, upload, ask Gemini to focus on pacing and music sync specifically.
