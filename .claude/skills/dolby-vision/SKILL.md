---
name: dolby-vision
description: Dolby Vision render pipeline — set DV profile version, run the analyzer, adjust midtone detail, and render. Specify version (8.4 default for social/streaming, 5 for cinema, 8.1 for broadcast).
disable-model-invocation: true
---

# /dolby-vision — Dolby Vision Render Pipeline

Full Dolby Vision delivery in one command: set the DV profile, run the analyzer, optionally adjust the midtone detail slider, and render.

## Arguments

User provides a Dolby Vision profile version and optionally a format/codec and midtone adjustment.

| Shorthand | DV Profile | Use Case |
|-----------|-----------|----------|
| `8.4` or `social` or `streaming` (default) | Profile 8.4 | YouTube, Instagram, TikTok, streaming platforms. Player-led HDR-to-SDR mapping. Most compatible. |
| `8.1` or `broadcast` | Profile 8.1 | Broadcast, cable. Backward compatible with HDR10. |
| `5` or `cinema` or `theatrical` | Profile 5 | Theatrical/cinema. Dual-layer, highest quality. Requires Studio. |
| `7` or `ott` | Profile 7 | OTT streaming (Netflix, Disney+). Single RPU, mel/fel. |

## Workflow

### 1. Set Dolby Vision project settings

Use `resolve_get_project_settings` first to read current color science and DV settings. Then use `resolve_set_project_setting` to configure:

- `colorScienceMode` — should be `davinciYRGBColorManagedv2` or `davinciYRGB` for DV workflows
- Dolby Vision version/profile — set via the appropriate project setting key
- Check that the project is in HDR (wide gamut / high dynamic range)

Read all project settings and look for any keys containing "dolby", "DolbyVision", "hdr", or "HDR" to find the exact setting names for this Resolve version. Common keys include:
- `dolbyVisionVersion` or `DolbyVisionVersion`
- `dolbyVisionContentType`
- `hdrMasteringLuminanceMax`
- `hdrMasteringLuminanceMin`

### 2. Run Dolby Vision analyzer

Use `resolve_analyze_dolby_vision` to scan the timeline and generate L1/L2/L5 metadata. This must complete before rendering.

Then use `resolve_optimize_dolby_vision` to refine the metadata for spec compliance.

### 3. Lower midtone detail (optional but recommended)

Dolby Vision content often benefits from slightly reduced midtone detail to avoid harsh HDR transitions. Unless the user says otherwise, lower the midtone adjustment:

- Switch to the Color page with `resolve_switch_page("color")`
- For each clip on V1, use `resolve_get_item_properties` to read current settings
- Use `resolve_set_item_properties` to lower the midtone detail slider
- A subtle reduction is typical: if default is 0, try setting to around -10 to -15
- If the user specifies a value, use that instead

**Note:** The exact property key for midtone detail varies by Resolve version. Read the clip properties first to find the correct key — look for keys containing "midtone", "midDetail", "MidDetail", or similar. If the property isn't available via the scripting API, inform the user they'll need to adjust it manually on the Color page.

### 4. Set render format for Dolby Vision

Use `resolve_set_render_format_and_codec` and `resolve_set_render_settings`:

**For Profile 8.4 (social/streaming):**
- Format: MP4
- Codec: H.265
- Set HDR metadata export enabled
- Resolution: match timeline (usually 3840x2160 for HDR)

**For Profile 5 (cinema):**
- Format: QuickTime or IMF
- Codec: DNxHR or ProRes (for intermediate), or JPEG 2000 for IMF
- Dual-layer output

**For Profile 8.1 (broadcast):**
- Format: MXF
- Codec: DNxHD/DNxHR or XAVC
- HDR10 compatible base layer

**For Profile 7 (OTT):**
- Format: MP4
- Codec: H.265
- Single RPU stream

### 5. Render

Use `resolve_add_render_job` then `resolve_start_render`. Poll with `resolve_get_render_status` until complete.

### 6. Save project

Use `resolve_save_project` after the render completes.

## Example Interactions

User: `/dolby-vision`
→ Default: Profile 8.4, run analyzer, lower midtones slightly, render H.265 MP4.

User: `/dolby-vision 8.4`
→ Same as default.

User: `/dolby-vision 5`
→ Profile 5 cinema, run analyzer, render ProRes/IMF.

User: `/dolby-vision 8.4 midtone -20`
→ Profile 8.4, lower midtone detail to -20, render.

User: `/dolby-vision streaming no midtone`
→ Profile 8.4, skip midtone adjustment, render.

User: `/dolby-vision 7 to /Volumes/Exports/`
→ Profile 7 OTT, render to specified directory.
