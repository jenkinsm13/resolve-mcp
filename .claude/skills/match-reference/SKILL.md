---
name: match-reference
description: Match the color grade of the current DaVinci Resolve timeline frame to a reference image. Exports both in sRGB, visually compares them, and adjusts CDL nodes to match the reference look.
disable-model-invocation: true
---

# /match-reference — Match a Reference Image

Look at a reference image and the current timeline frame side by side, then adjust the grade to match the reference.

## Arguments

The user provides a path to a reference image. This can be:
- A still frame from another project
- A film still or screenshot
- A LUT preview image
- Any image that represents the target look

## Workflow

### 1. Switch to Color page

Use `resolve_switch_page("color")`.

### 2. Export current frame in sRGB

Use `resolve_export_frame` to export to `/tmp/resolve_match_current.png`.

Convert to sRGB with ffmpeg:
```bash
ffmpeg -y -i /tmp/resolve_match_current.png \
  -vf "colorspace=all=bt709:iall=bt2020:fast=1" \
  -color_primaries bt709 -color_trc iec61966-2-1 -colorspace bt709 \
  /tmp/resolve_match_current_srgb.png 2>/dev/null
```

Fallback if that fails:
```bash
ffmpeg -y -i /tmp/resolve_match_current.png -pix_fmt rgb24 /tmp/resolve_match_current_srgb.png 2>/dev/null
```

### 3. Read both images

Use the **Read tool** on both:
- `/tmp/resolve_match_current_srgb.png` (current timeline frame)
- The user's reference image path

Claude can see both images simultaneously and compare them visually.

### 4. Get current grade state

Use `resolve_node_overview` to see all nodes.
Use `resolve_get_cdl` to read current CDL.
Use `resolve_get_node_count` for node count.

### 5. Analyze the difference

Compare the reference to the current frame across these dimensions:

**Overall exposure:** Is the reference brighter/darker?
**Contrast curve:** Is the reference higher/lower contrast? Are blacks lifted or crushed?
**Color temperature:** Is the reference warmer or cooler?
**Shadow color:** What hue are the shadows in the reference? (teal, blue, purple, neutral)
**Highlight color:** What hue are the highlights? (warm, cool, neutral)
**Midtone color:** Any color shift in the midtones?
**Saturation level:** More or less saturated than current?
**Specific color shifts:** Any obvious color grading choices (orange/teal, bleach bypass, cross-process, etc.)

### 6. Calculate CDL adjustments

Map the visual difference to CDL values:

- **Slope (R,G,B)** — match overall brightness and color balance
- **Offset (R,G,B)** — match shadow color and black level
- **Power (R,G,B)** — match midtone density and color
- **Saturation** — match overall saturation level

Work on the last node in the chain. If the existing grade is complex, add a new node for the match adjustment.

Apply with `resolve_set_cdl`.

### 7. Verify the match

Export a new frame after adjustments:
- `/tmp/resolve_match_after.png` → convert to sRGB
- Read it alongside the reference
- Compare: does it match closer now?
- If not close enough, make additional adjustments
- Iterate up to 3 times to refine the match

### 8. Report

Tell the user:
- What the reference look is characterized by (e.g., "warm highlights, teal shadows, lifted blacks, moderate contrast")
- What CDL values were applied
- How close the match is (exact match is impossible with CDL alone — note if a LUT would get closer)
- Suggest a LUT if the look requires more than CDL can achieve (e.g., film emulation, S-curve, heavy color shifts)

## Limitations

CDL is a linear correction (slope, offset, power, saturation). It cannot replicate:
- S-curve contrast (use a LUT or Resolve curves)
- Selective color shifts (use qualifier/HSL tools manually)
- Film grain, halation, bloom (use OFX plugins)
- Heavy cross-process looks (use a LUT)

If the reference requires these, describe what additional manual adjustments the user should make.

## Example Interactions

User: `/match-reference /Users/me/Desktop/film_still.jpg`
→ Read both images, analyze difference, apply CDL to match, verify.

User: `/match-reference ~/Pictures/teal_orange_look.png`
→ Match the teal/orange look from the reference.

User: `/match-reference /Volumes/Stills/hero_frame_graded.tiff`
→ Match a previously graded hero frame from another project.
