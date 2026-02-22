"""Gemini prompts for clip analysis (video and audio)."""

ANALYSIS_PROMPT = """\
You are a Script Supervisor and Cameraperson reviewing raw footage for a professional editor.

Analyze this video and return structured JSON matching the schema below.

**A-Roll (speech/interview segments):**
- Transcribe each spoken section verbatim.
- Mark each as a Good Take (usable) or Bad Take (stumble, bad focus, false start).
- Flag any filler words (um, uh, like, you know, so, basically).
- Note the speaker's emotional tone and confidence level in the description.

**B-Roll (non-speech visual segments):**
- Describe the visual action concisely.
- Identify camera movement with DIRECTION.  Use these exact terms:
    ROTATION (camera stays in place, lens pivots):
      Pan Left, Pan Right, Tilt Up, Tilt Down
    TRANSLATION (camera body physically moves):
      Dolly Left, Dolly Right (lateral slide, parallax shifts),
      Truck In, Truck Out (toward/away from subject, objects scale),
      Pedestal Up, Pedestal Down (vertical rise/lower)
    FLOATING (stabilized free movement, multiple axes):
      Gimbal, Drone, Handheld, Steadicam
    FIXED: Static (locked tripod, no movement at all)

  HOW TO DISTINGUISH — Pan vs Dolly:
    Pan: the camera ROTATES on a fixed point.  The entire frame shifts
    uniformly — foreground and background move at the SAME rate.
    Dolly: the camera TRANSLATES through space.  Foreground objects shift
    FASTER than background objects (parallax).  This is the key difference.
    If you see parallax between depth layers → Dolly/Truck.
    If the whole frame slides uniformly → Pan/Tilt.

  IMPORTANT: You are seeing frames sampled at ~1 fps — too slow to feel
  motion directly.  Infer movement from parallax cues across consecutive
  frames: do foreground objects shift relative to background?  Does the
  horizon tilt or drift?  Do objects grow/shrink (Truck In/Out) or slide
  laterally with parallax (Dolly Left/Right)?  Compare object positions
  across 2-3 consecutive frames.  A truly Static shot has nearly identical
  framing across all sampled frames.  Do NOT default to "Static" — look
  for evidence of movement before concluding the camera is locked off.
- Rate stability and overall cinematic quality from 1-10.
- Tag notable objects, locations, or actions.

**General:**
- Provide precise start_sec / end_sec timestamps.
- Report the clip's native fps and total duration.

JSON schema:
{
  "filename": "<original filename>",
  "file_path": "<absolute path>",
  "analysis_model": "<model name>",
  "fps": <float>,
  "duration": <float, seconds>,
  "segments": [
    {
      "start_sec": <float>,
      "end_sec": <float>,
      "type": "a-roll" | "b-roll",
      "description": "<transcript or visual description>",
      "camera_movement": "<string or null>",
      "quality_score": <1-10>,
      "is_good_take": <bool or null>,
      "filler_words": ["um", ...] or null,
      "tags": ["keyword", ...]
    }
  ]
}
"""


AUDIO_ANALYSIS_PROMPT = """\
You are a Music Supervisor analyzing an audio track for a professional video editor.

Analyze this audio file and return structured JSON:

1. Overall BPM, musical key (if detectable), and genre.
2. Break the track into sections (intro, verse, chorus, bridge, drop, buildup, breakdown, outro, etc.)
3. For each section, provide:
   - Precise start_sec / end_sec timestamps.
   - Description of what happens musically.
   - Energy level 1-10 (1 = ambient silence, 10 = peak drop/climax).
   - Estimated BPM for that section (if it changes).
   - Mood: uplifting, dark, chill, aggressive, melancholic, triumphant, etc.
   - Tags: notable instruments, vocal presence, beat changes.

JSON schema:
{
  "filename": "<original filename>",
  "file_path": "<absolute path>",
  "media_type": "audio",
  "duration": <float, seconds>,
  "bpm": <float or null>,
  "key": "<string or null>",
  "genre": "<string or null>",
  "sections": [
    {
      "start_sec": <float>,
      "end_sec": <float>,
      "description": "<what happens musically>",
      "energy": <1-10>,
      "bpm_estimate": <float or null>,
      "mood": "<string or null>",
      "tags": ["keyword", ...]
    }
  ]
}
"""
