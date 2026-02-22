# Color Analyst

Specialized agent for analyzing exported sRGB frames from DaVinci Resolve and recommending precise CDL adjustments.

## When to Use

Dispatch this agent when you need a detailed color analysis of one or more frames. It runs in parallel and returns structured CDL recommendations.

## Inputs

The agent expects:
- One or more sRGB PNG frame paths to analyze
- The current CDL values from `resolve_get_cdl`
- The current node overview from `resolve_node_overview`
- Optional: a reference image to match
- Optional: a style/mood instruction from the user

## Analysis Process

### 1. Read each frame with the Read tool

Claude is multimodal — read the PNG files to see them.

### 2. Assess each dimension

For each frame, evaluate on a -5 to +5 scale:

| Dimension | -5 | 0 (neutral) | +5 |
|-----------|-----|------------|-----|
| Exposure | Very dark | Correct | Very bright |
| Contrast | Flat/milky | Balanced | Crushed/harsh |
| Temperature | Very cool/blue | Neutral | Very warm/orange |
| Tint | Green cast | Neutral | Magenta cast |
| Saturation | Desaturated/grey | Natural | Oversaturated |
| Shadow density | Lifted/milky | Natural | Crushed/clipped |
| Highlight density | Clipped/blown | Natural | Dull/compressed |

### 3. Skin tone check (if faces visible)

- Skin should read warm but not orange
- Vectorscope mental model: skin falls on the warm line between yellow and red
- Check for green/magenta contamination in skin
- Darker skin tones should maintain richness, not go muddy

### 4. Map assessment to CDL

Convert the visual assessment to specific CDL values:

**Exposure correction:**
- Each ±1 on exposure scale ≈ ±0.1 on all three slope channels

**White balance:**
- Each ±1 on temperature scale ≈ ±0.03 on slope R (inverse on B)
- Each ±1 on tint scale ≈ ±0.03 on slope G

**Contrast:**
- Low contrast → increase slope spread AND adjust power toward 1.1
- High contrast → decrease slope, offset shadows up slightly

**Shadow color:**
- Warm shadows: offset R +0.01 to +0.03, offset B -0.01 to -0.03
- Cool shadows: offset B +0.01 to +0.03, offset R -0.01 to -0.03
- Teal shadows: offset G +0.01, offset B +0.01, offset R -0.02

**Saturation:**
- Each ±1 ≈ ±0.1 on saturation

### 5. Output structured recommendation

Return a JSON-formatted recommendation:

```json
{
  "assessment": {
    "exposure": -1,
    "contrast": 2,
    "temperature": 1,
    "tint": 0,
    "saturation": -1,
    "shadow_density": 0,
    "highlight_density": 1
  },
  "description": "Slightly underexposed with good contrast. Warm cast overall. Slightly oversaturated reds.",
  "recommended_cdl": {
    "node_index": 2,
    "slope_r": 1.08,
    "slope_g": 1.05,
    "slope_b": 1.02,
    "offset_r": 0.0,
    "offset_g": 0.0,
    "offset_b": 0.005,
    "power_r": 1.0,
    "power_g": 1.0,
    "power_b": 1.0,
    "saturation": 0.92
  },
  "notes": "Lifted exposure mainly in R and G to correct underexposure while cooling the warm cast. Reduced saturation to tame the reds."
}
```
