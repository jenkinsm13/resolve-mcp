"""Music production brief addendum — injected when no audio file is present."""

MUSIC_BRIEF_ADDENDUM = """\

NO AUDIO FILE WAS PROVIDED.  You must generate TWO additional outputs:

1. EDIT TO AN IMAGINED SONG:
   Design a 30-second song in your head — choose a BPM, key, time signature,
   and lyrical concept that fits the footage.  Then edit the video TO that
   imagined song.  Your cuts should land on beats.  Your pacing should follow
   the song's energy arc (intro → verse → chorus or build → drop → outro).
   Set "audio_track" to {{"source_file": null, "start_sec": 0, "end_sec": 30}}.
   The total timeline duration should be ~30 seconds.

2. MUSIC PRODUCTION BRIEF — add a "music_brief" field to your JSON output.
   This is a comprehensive prompt that a music producer, songwriter, and mix
   engineer would use to create the EXACT song you edited the video to.
   It must be EXTREMELY detailed — the producer should be able to recreate
   your imagined song from this brief alone.

   The "music_brief" object MUST include ALL of the following fields:

   {{
     "title": "<working title for the track>",
     "duration_sec": 30,
     "bpm": <int>,
     "time_signature": "<e.g. 4/4, 3/4, 6/8>",
     "key": "<e.g. C minor, F# major, Bb Dorian>",
     "genre": "<primary genre and subgenre>",
     "mood_arc": "<energy/emotion trajectory across the 30 seconds>",
     "reference_tracks": ["<2-3 real songs that capture the vibe>"],

     "arrangement": [
       {{
         "section": "<intro/verse/pre-chorus/chorus/drop/bridge/outro>",
         "start_sec": <float>,
         "end_sec": <float>,
         "description": "<what happens musically in this section>",
         "energy_level": <1-10>,
         "instruments_enter": ["<instruments that come in>"],
         "instruments_exit": ["<instruments that drop out>"]
       }}
     ],

     "lyrics": [
       {{
         "section": "<verse/chorus/bridge/hook>",
         "start_sec": <float>,
         "end_sec": <float>,
         "text": "<lyric lines>",
         "vocal_direction": "<delivery: belted, whispered, spoken word, falsetto, etc.>"
       }}
     ],

     "instrumentation": [
       {{
         "instrument": "<e.g. sub bass, lead synth, acoustic guitar, hi-hats>",
         "role": "<foundation/melody/harmony/rhythm/texture/fx>",
         "synth_type": "<analog, FM, wavetable, sampler, live, etc.>",
         "adsr": {{
           "attack_ms": <float>,
           "decay_ms": <float>,
           "sustain_level": <0.0-1.0>,
           "release_ms": <float>
         }},
         "processing_chain": [
           "<e.g. LP filter at 2kHz, resonance 0.4>",
           "<e.g. chorus: rate 1.2Hz, depth 40%, mix 30%>",
           "<e.g. saturator: soft clip, drive 3dB>"
         ],
         "notes": "<any additional performance or sound design notes>"
       }}
     ],

     "mix_notes": {{
       "master_bus": {{
         "compressor": "<settings: threshold, ratio, attack, release, makeup>",
         "eq": "<broad strokes: e.g. gentle high shelf +1dB at 10kHz, HPF at 30Hz>",
         "limiter": "<ceiling, release>"
       }},
       "per_instrument": [
         {{
           "instrument": "<matches instrumentation list>",
           "pan": "<L100 to R100, or C for center>",
           "level_db": <float relative to mix>,
           "eq": "<specific EQ moves: cuts, boosts, filters>",
           "compression": "<threshold, ratio, attack, release>",
           "reverb": "<type, decay, pre-delay, wet level>",
           "delay": "<type, time, feedback, wet level>",
           "other_fx": "<any additional processing>"
         }}
       ],
       "stereo_field": "<how the mix is spread: wide, narrow, mid-side notes>",
       "dynamic_range": "<target LUFS, peak ceiling, crest factor notes>",
       "frequency_balance": "<overall tonal target: warm, bright, dark, neutral>"
     }},

     "production_notes": "<free-form paragraph with any additional creative direction, \
sonic references, vibe notes, or technical requirements that don't fit above>"
   }}

   Be SPECIFIC.  Don't write generic placeholder values.  Every BPM, every
   ADSR envelope, every compressor setting should reflect a deliberate creative
   choice that serves the footage you just watched.  The lyrics must be
   ORIGINAL and specific to the visual content — not generic filler.
"""
