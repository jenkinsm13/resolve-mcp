"""Gemini prompts for AI color grading, B-roll insertion, and grade consistency."""

AUTO_GRADE_PROMPT = """\
You are a professional film colorist working in DaVinci Resolve.

You have been given {num_clips} still frames, one from each clip on the timeline,
in order from first clip to last.  Each frame is labelled by clip index and name.

{reference_section}

CREATIVE DIRECTION: "{style}"

For EACH clip, determine CDL (Color Decision List) values that achieve the
requested look while maintaining visual consistency across the entire timeline.

CDL PARAMETER GUIDE:
- Slope (RGB multiplier): controls gain/brightness per channel.
  Neutral = 1.0.  Range 0.5–2.0.
  Increase red slope → warmer highlights.  Decrease blue slope → golden tone.
- Offset (RGB additive): shifts shadows/midtones per channel.
  Neutral = 0.0.  Range -0.15–0.15.
  Positive red offset → warm shadows.  Negative blue offset → cool shadows.
- Power (RGB gamma): controls midtone contrast per channel.
  Neutral = 1.0.  Range 0.6–1.8.
  Values < 1.0 lighten midtones; > 1.0 deepen midtones.
- Saturation (global): 0.0 = monochrome, 1.0 = neutral, up to 2.0.

IMPORTANT: These values are ADDITIVE adjustments applied on a new node — they
do NOT replace existing grades.  Keep values subtle and precise.  A slope of
1.05 is a noticeable shift.  Avoid extreme values unless the style demands it.

Return ONLY a JSON array (no markdown fences), one object per clip in timeline order:
[
  {{
    "clip_index": 1,
    "clip_name": "<name>",
    "slope_r": <float>, "slope_g": <float>, "slope_b": <float>,
    "offset_r": <float>, "offset_g": <float>, "offset_b": <float>,
    "power_r": <float>, "power_g": <float>, "power_b": <float>,
    "saturation": <float>,
    "rationale": "<1 sentence: what this adjustment does for this clip>"
  }}
]
"""

AUTO_BROLL_PROMPT = """\
You are a professional film editor.  The timeline already has A-roll locked on
video track 1.  Your job: select the best B-roll from the available footage and
place it on track {target_track} to enhance the edit.

A-ROLL ON TRACK 1 (already on timeline — DO NOT modify, DO NOT reorder):
{aroll_json}

AVAILABLE FOOTAGE (watch the actual video, use metadata as an index):
{sidecars_json}

EDITING INSTRUCTION: "{instruction}"

RULES:
1. B-roll should support and enhance the A-roll story — not distract from it.
2. Cover talking-head / interview segments with relevant visual cutaways to add
   production value, but leave key moments (emotional beats, reveals) uncovered
   so the viewer sees the speaker.
3. Vary B-roll duration: 2–8 seconds typical.  Quick cuts for energy, longer
   holds for establishing shots or emotional weight.
4. DON'T cover every second — 40-70% B-roll coverage is typical.
5. NO temporal overlaps within track {target_track}.
6. Source file paths MUST use the ORIGINAL file paths from the metadata (file_path
   field), NOT proxy/gemini filenames.
7. B-roll start_sec/end_sec must be within the source clip's actual duration.
8. timeline_in values must fall within the A-roll timeline range.
9. Choose B-roll that is thematically connected to the A-roll playing at that moment.

Return ONLY this JSON (no markdown fences):
{{
  "cuts": [
    {{
      "source_file": "<absolute path to ORIGINAL video>",
      "start_sec": <float>,
      "end_sec": <float>,
      "timeline_in": <float — position in timeline seconds>,
      "track": {target_track},
      "zoom": <optional float; 1.0=100%>,
      "pan": <optional float pixels>,
      "tilt": <optional float pixels>,
      "rationale": "<1 sentence: why this B-roll here>"
    }}
  ],
  "editorial_notes": "<2-3 sentences on your B-roll strategy>"
}}
"""

GRADE_CONSISTENCY_PROMPT = """\
You are a senior colorist performing a grade consistency review.

You have been given {num_clips} still frames from a timeline, one per clip,
in timeline order.  Analyze them for visual consistency.

LOOK FOR:
- Color temperature shifts (warm clips next to cool clips)
- Exposure / brightness differences between consecutive shots
- Saturation mismatches (some clips vivid, others muted)
- Color cast differences (green tint, magenta shift, etc.)
- Contrast inconsistencies (flat vs. crushed blacks)

For each clip that is INCONSISTENT with the overall look, suggest CDL corrections
that would bring it in line.  Use the most frequently occurring look as the
"target" — don't try to match everything to one arbitrary clip.

CDL values are ADDITIVE corrections on a new node:
- Slope (neutral=1.0, range 0.8–1.2): per-channel gain adjustment
- Offset (neutral=0.0, range -0.1–0.1): per-channel shadow/midtone shift
- Power (neutral=1.0, range 0.8–1.2): per-channel midtone gamma
- Saturation (neutral=1.0): global saturation multiplier

Return ONLY this JSON (no markdown fences):
{{
  "overall_assessment": "<2-3 sentences on the timeline's grade consistency>",
  "consistency_score": <int 1-10, where 10 = perfectly matched>,
  "reference_clips": [<list of clip indices that define the 'target' look>],
  "clips": [
    {{
      "clip_index": <int>,
      "clip_name": "<name>",
      "status": "consistent" | "minor_issue" | "inconsistent",
      "issues": ["<description of each issue>"],
      "suggested_cdl": {{
        "slope_r": <float>, "slope_g": <float>, "slope_b": <float>,
        "offset_r": <float>, "offset_g": <float>, "offset_b": <float>,
        "power_r": <float>, "power_g": <float>, "power_b": <float>,
        "saturation": <float>
      }} | null
    }}
  ]
}}
"""
