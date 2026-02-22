"""
Save human-readable outputs: director's notes, voiceover script, music brief.
"""

import json
from pathlib import Path

from .config import log


def format_tc(seconds: float) -> str:
    """Format seconds as MM:SS for readable timestamps."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def save_directors_notes(root: Path, timeline_name: str, edit_plan: dict) -> None:
    """Write director's notes as a markdown file."""
    notes = edit_plan.get("directors_notes", [])
    if not notes:
        return
    lines = [f"# Director's Notes — {timeline_name}\n"]
    for n in notes:
        t = format_tc(n.get("timeline_sec", 0))
        lines.append(f"## [{t}]")
        lines.append(f"**Decision:** {n.get('decision', '')}\n")
        alt = n.get("alternative", "")
        if alt:
            lines.append(f"**Alternative considered:** {alt}\n")
    path = root / f"{timeline_name} — Directors Notes.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Saved director's notes: %s", path.name)


def save_voiceover_script(root: Path, timeline_name: str, edit_plan: dict) -> None:
    """Write voiceover script as both JSON (for TTS automation) and readable text."""
    vo = edit_plan.get("voiceover_script", [])

    # Always save the raw JSON for programmatic use / TTS pipeline.
    json_path = root / f"{timeline_name} — Voiceover.json"
    json_path.write_text(json.dumps(vo, indent=2), encoding="utf-8")

    if not vo:
        log.info("Voiceover script is empty (music-only edit). Saved empty JSON.")
        return

    # Readable script for manual recording.
    lines = [f"VOICEOVER SCRIPT — {timeline_name}", "=" * 60, ""]
    for cue in vo:
        t_start = format_tc(cue.get("start_sec", 0))
        t_end = format_tc(cue.get("end_sec", 0))
        tone = cue.get("tone", "")
        text = cue.get("text", "")
        lines.append(f"[{t_start} – {t_end}]  ({tone})")
        lines.append(f"  {text}")
        lines.append("")
    txt_path = root / f"{timeline_name} — Voiceover.txt"
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Saved voiceover script: %s + %s", json_path.name, txt_path.name)


def save_music_brief(root: Path, timeline_name: str, edit_plan: dict) -> None:
    """Write the music production brief as both JSON and a readable markdown file."""
    brief = edit_plan.get("music_brief")
    if not brief:
        return

    # Raw JSON for programmatic use.
    json_path = root / f"{timeline_name} — Music Brief.json"
    json_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")

    # Human-readable markdown for producers / songwriters / engineers.
    lines = [
        f"# Music Production Brief — {timeline_name}",
        "",
        f"**Title:** {brief.get('title', 'Untitled')}",
        f"**Duration:** {brief.get('duration_sec', 30)}s",
        f"**BPM:** {brief.get('bpm', '?')}",
        f"**Time Signature:** {brief.get('time_signature', '4/4')}",
        f"**Key:** {brief.get('key', '?')}",
        f"**Genre:** {brief.get('genre', '?')}",
        f"**Mood Arc:** {brief.get('mood_arc', '?')}",
        "",
    ]

    refs = brief.get("reference_tracks", [])
    if refs:
        lines.append("**Reference Tracks:** " + ", ".join(refs))
        lines.append("")

    # Arrangement
    arrangement = brief.get("arrangement", [])
    if arrangement:
        lines.append("## Arrangement")
        lines.append("")
        for sec in arrangement:
            lines.append(
                f"### [{format_tc(sec.get('start_sec', 0))} – "
                f"{format_tc(sec.get('end_sec', 0))}] "
                f"{sec.get('section', '?').upper()} (energy {sec.get('energy_level', '?')}/10)"
            )
            lines.append(f"{sec.get('description', '')}")
            enters = sec.get("instruments_enter", [])
            exits = sec.get("instruments_exit", [])
            if enters:
                lines.append(f"  **In:** {', '.join(enters)}")
            if exits:
                lines.append(f"  **Out:** {', '.join(exits)}")
            lines.append("")

    # Lyrics
    lyrics = brief.get("lyrics", [])
    if lyrics:
        lines.append("## Lyrics")
        lines.append("")
        for lyr in lyrics:
            lines.append(
                f"### [{format_tc(lyr.get('start_sec', 0))} – "
                f"{format_tc(lyr.get('end_sec', 0))}] "
                f"{lyr.get('section', '?').upper()}"
            )
            lines.append(f"*({lyr.get('vocal_direction', '')})*")
            lines.append("```")
            lines.append(lyr.get("text", ""))
            lines.append("```")
            lines.append("")

    # Instrumentation
    instruments = brief.get("instrumentation", [])
    if instruments:
        lines.append("## Instrumentation & Sound Design")
        lines.append("")
        for inst in instruments:
            lines.append(f"### {inst.get('instrument', '?')} ({inst.get('role', '?')})")
            lines.append(f"**Synth Type:** {inst.get('synth_type', '?')}")
            adsr = inst.get("adsr", {})
            if adsr:
                lines.append(
                    f"**ADSR:** A={adsr.get('attack_ms', '?')}ms  "
                    f"D={adsr.get('decay_ms', '?')}ms  "
                    f"S={adsr.get('sustain_level', '?')}  "
                    f"R={adsr.get('release_ms', '?')}ms"
                )
            chain = inst.get("processing_chain", [])
            if chain:
                lines.append("**Processing Chain:**")
                for step in chain:
                    lines.append(f"  - {step}")
            notes = inst.get("notes", "")
            if notes:
                lines.append(f"**Notes:** {notes}")
            lines.append("")

    # Mix Notes
    mix = brief.get("mix_notes", {})
    if mix:
        lines.append("## Mix Engineer Notes")
        lines.append("")

        master = mix.get("master_bus", {})
        if master:
            lines.append("### Master Bus")
            lines.append(f"**Compressor:** {master.get('compressor', '?')}")
            lines.append(f"**EQ:** {master.get('eq', '?')}")
            lines.append(f"**Limiter:** {master.get('limiter', '?')}")
            lines.append("")

        lines.append(f"**Stereo Field:** {mix.get('stereo_field', '?')}")
        lines.append(f"**Dynamic Range:** {mix.get('dynamic_range', '?')}")
        lines.append(f"**Frequency Balance:** {mix.get('frequency_balance', '?')}")
        lines.append("")

        per_inst = mix.get("per_instrument", [])
        if per_inst:
            lines.append("### Per-Instrument Mix")
            lines.append("")
            for pi in per_inst:
                lines.append(f"**{pi.get('instrument', '?')}**")
                lines.append(f"  Pan: {pi.get('pan', '?')} | Level: {pi.get('level_db', '?')} dB")
                lines.append(f"  EQ: {pi.get('eq', '?')}")
                lines.append(f"  Compression: {pi.get('compression', '?')}")
                if pi.get("reverb"):
                    lines.append(f"  Reverb: {pi.get('reverb')}")
                if pi.get("delay"):
                    lines.append(f"  Delay: {pi.get('delay')}")
                if pi.get("other_fx"):
                    lines.append(f"  Other FX: {pi.get('other_fx')}")
                lines.append("")

    # Production notes
    prod_notes = brief.get("production_notes", "")
    if prod_notes:
        lines.append("## Production Notes")
        lines.append("")
        lines.append(prod_notes)
        lines.append("")

    md_path = root / f"{timeline_name} — Music Brief.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Saved music brief: %s + %s", json_path.name, md_path.name)
