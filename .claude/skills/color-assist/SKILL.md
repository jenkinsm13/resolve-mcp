---
name: color-assist
description: AI-powered color grading assistant. Exports the current frame in sRGB, visually analyzes it, and makes CDL adjustments directly on the Color page nodes. Works regardless of project color space (HDR, P3, ACES, etc.) because the frame is converted to sRGB for analysis — the color space LLMs are trained on.
disable-model-invocation: true
---

# /color-assist — AI Color Grading

Look at the current frame, analyze the color, and make adjustments directly in the Resolve Color page node graph.

## Why sRGB

Multimodal LLMs (Claude, Gemini, GPT-4V) are trained on sRGB imagery. Even if the project is graded in DaVinci Wide Gamut, ACES, Rec.2020, or HDR PQ — the exported frame MUST be converted to sRGB before analysis. This gives the AI the most accurate color perception regardless of the working color space.

## Arguments

- No arguments: analyze current frame, suggest and apply corrections
- `shadows warmer`: specific instruction for what to adjust
- `more contrast`: push contrast
- `match [style]`: aim for a specific look (e.g., "match teal and orange", "match film noir")
- `just analyze`: look at the frame and describe what you see, don't make changes
- `undo`: reset the last node to neutral

## Workflow

### 1. Switch to Color page

Use `resolve_switch_page("color")` to ensure we're on the Color page with a clip selected.

### 2. Export current frame

Use `resolve_export_frame` to export the current frame to a temporary file:
- Path: `/tmp/resolve_color_assist_frame.png`

### 3. Convert to sRGB

Run ffmpeg via Bash to convert the exported frame to sRGB:

```bash
ffmpeg -y -i /tmp/resolve_color_assist_frame.png \
  -vf "colorspace=all=bt709:iall=bt2020:fast=1" \
  -color_primaries bt709 -color_trc iec61966-2-1 -colorspace bt709 \
  /tmp/resolve_color_assist_srgb.png 2>/dev/null
```

If that fails (project might already be in Rec.709/sRGB), fall back:
```bash
ffmpeg -y -i /tmp/resolve_color_assist_frame.png \
  -pix_fmt rgb24 \
  /tmp/resolve_color_assist_srgb.png 2>/dev/null
```

If ffmpeg is not available, use the exported frame as-is and note the limitation.

### 4. Read the sRGB frame

Use the **Read tool** on `/tmp/resolve_color_assist_srgb.png` — Claude is multimodal and can see images directly. This is the key step: YOU are looking at the actual frame from the timeline.

### 5. Get current grade state

Use `resolve_node_overview` to see all nodes, their labels, LUTs, and enabled state.
Use `resolve_get_cdl` to read the current CDL values.
Use `resolve_get_node_count` to know how many nodes exist.

### 6. Analyze the image

Look at the frame and assess:

**Exposure:**
- Is the image too dark (underexposed) or too bright (overexposed)?
- Are the shadows crushed? Are the highlights clipped?
- Is the midtone exposure correct for the subject?

**White balance / Color temperature:**
- Does the image have a color cast? (too warm/orange, too cool/blue, green/magenta tint)
- Is skin tone natural? (skin should read warm but not orange)
- Are whites actually white or tinted?

**Contrast:**
- Is the image flat/low contrast or too contrasty?
- Is there separation between shadows, midtones, and highlights?
- Does it look "milky" (lifted blacks) or "crushed" (no shadow detail)?

**Saturation:**
- Is the image oversaturated or desaturated?
- Are any specific colors problematic? (neon skin, oversaturated sky, muddy greens)

**Color balance per range:**
- Shadows: usually benefit from slight cool/blue push
- Midtones: usually neutral or slightly warm
- Highlights: often slightly warm for golden hour, cool for clinical/modern

**Overall look:**
- Does it feel cinematic or flat?
- Does it match the intended mood described by the user?

### 7. Make CDL adjustments

Based on the analysis, determine CDL adjustments. Map your visual assessment to CDL values:

**CDL Primer:**
- **Slope** (gain/multiply) — affects the entire range, like a multiplier. Values >1 brighten, <1 darken. Per-channel (R,G,B) controls color balance.
  - Warm up: increase slope R slightly, decrease slope B slightly
  - Cool down: decrease slope R, increase slope B
  - Typical range: 0.7–1.5

- **Offset** (lift/add) — adds to the signal, primarily affects shadows/blacks.
  - Lift shadows: positive offset
  - Crush blacks: negative offset
  - Warm shadows: positive offset R, negative offset B
  - Typical range: -0.1 to 0.1

- **Power** (gamma/midtones) — affects midtones without changing black/white points.
  - Brighten midtones: power < 1.0
  - Darken midtones: power > 1.0
  - Typical range: 0.7–1.3

- **Saturation** — overall saturation multiplier.
  - Desaturate: < 1.0
  - Boost: > 1.0
  - Typical range: 0.8–1.3

**Strategy:**
- Work on the LAST node in the chain (or add a new node for your adjustments)
- Make SUBTLE adjustments — CDL values compound. A slope change of 0.05 is visible.
- If the grade is already complex (many nodes), prefer adjusting the existing correction node rather than adding more

Use `resolve_set_cdl` with the calculated values.

### 8. Verify

After making adjustments:
- Export a new frame to `/tmp/resolve_color_assist_after.png`
- Convert to sRGB again
- Read it with the Read tool
- Compare before and after
- Report what you changed and why

If the result doesn't look right, adjust further or offer to undo.

### 9. Undo if needed

If the user says "undo" or the result is bad:
- Read the CDL values you noted in step 5
- Use `resolve_set_cdl` to restore them
- Or use `resolve_reset_grades` on the specific node if you added one

## Example Interactions

User: `/color-assist`
→ Export frame, convert to sRGB, analyze, suggest and apply CDL corrections.

User: `/color-assist shadows warmer`
→ Same, but focus on warming the shadow tones (positive offset R, negative offset B).

User: `/color-assist more contrast, desaturate slightly`
→ Increase slope spread, adjust power, reduce saturation.

User: `/color-assist just analyze`
→ Export, convert, read frame, describe what you see — don't touch the grade.

User: `/color-assist match teal and orange`
→ Push shadows toward teal (offset B+, G+), highlights toward orange (slope R+).

User: `/color-assist undo`
→ Reset the last adjustment.
