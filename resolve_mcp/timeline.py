"""
OTIO timeline construction, FCP7 XML rendering, and media upload for editing pass.
"""

import time
from pathlib import Path
from typing import Optional

import opentimelineio as otio
from opentimelineio.opentime import RationalTime, TimeRange

from .config import MODEL, client, log
from .retry import retry_gemini
from .ffprobe import ffprobe_duration, ffprobe_start_tc, ffprobe_audio_info, tc_to_frames
from .media import find_proxy


def upload_media_for_editing(sidecars: list[dict]) -> list:
    """Upload proxy video/audio files to Gemini Files API for the editing pass.

    Returns a list of Gemini file references (in sidecar order) that can be
    passed as content parts to generate_content.  Skips files that fail to
    upload and logs warnings.
    """
    file_refs = []
    seen_paths: dict[str, object] = {}  # dedup by resolved path

    for sc in sidecars:
        raw_path = sc.get("file_path")
        if not raw_path:
            continue
        media_path = Path(raw_path)
        if not media_path.exists():
            log.warning("Source file missing: %s", raw_path)
            continue

        upload_path = find_proxy(media_path)
        resolved = str(upload_path.resolve())

        # Reuse if already uploaded in this batch
        if resolved in seen_paths:
            file_refs.append(seen_paths[resolved])
            continue

        try:
            ref = retry_gemini(client.files.upload, file=str(upload_path))
            # Wait for processing (Gemini may need to ingest the video)
            while ref.state.name == "PROCESSING":
                time.sleep(2)
                ref = client.files.get(name=ref.name)
            if ref.state.name == "ACTIVE":
                seen_paths[resolved] = ref
                file_refs.append(ref)
            else:
                log.warning("Upload for %s ended in state %s", upload_path.name, ref.state.name)
        except Exception as exc:
            log.warning("Failed to upload %s: %s", upload_path.name, exc)

    return file_refs


def build_otio_timeline(
    edit_plan: dict,
    default_fps: float = 24.0,
    tc_offsets: Optional[dict[str, int]] = None,
    clip_durations: Optional[dict[str, float]] = None,
) -> otio.schema.Timeline:
    """Convert the Gemini EDL JSON into an OTIO Timeline with V1 + V2 tracks.

    Args:
        edit_plan: Gemini's EDL with 0-based start_sec/end_sec per cut.
        default_fps: Timeline frame rate.
        tc_offsets: Map of source_file path -> start timecode in frames.
        clip_durations: Map of source_file path -> duration in seconds.
    """
    if tc_offsets is None:
        tc_offsets = {}
    if clip_durations is None:
        clip_durations = {}

    timeline = otio.schema.Timeline(name=edit_plan.get("timeline_name", "AI_Edit"))

    v1 = otio.schema.Track(name="V1-ARoll", kind=otio.schema.TrackKind.Video)
    v2 = otio.schema.Track(name="V2-BRoll", kind=otio.schema.TrackKind.Video)
    fps = default_fps
    fps_int = round(fps)  # Integer timebase: 60 for 59.94, 30 for 29.97, 24 for 23.976

    for cut in edit_plan.get("cuts", []):
        track_num = cut.get("track", 1)
        target = v1 if track_num == 1 else v2

        source_path = cut["source_file"]
        start = float(cut["start_sec"])
        end = float(cut["end_sec"])
        dur = end - start
        if dur <= 0:
            continue

        # tc_offset is already in integer-timebase frames (from tc_to_frames fix).
        # Use fps_int throughout so OTIO writes frame counts at the integer timebase,
        # matching what FCP7/Resolve expects (timebase=60, NTSC=TRUE for 59.94fps).
        tc_offset = tc_offsets.get(source_path, 0)
        clip_dur_sec = clip_durations.get(source_path)
        avail_dur_frames = round(clip_dur_sec * fps_int) if clip_dur_sec else 360000
        start_frames = round(start * fps_int)
        dur_frames = round(dur * fps_int)

        media_ref = otio.schema.ExternalReference(
            target_url=Path(source_path).as_uri(),
            available_range=TimeRange(
                RationalTime(tc_offset, fps_int),
                RationalTime(avail_dur_frames, fps_int),
            ),
        )

        clip = otio.schema.Clip(
            name=Path(source_path).stem,
            media_reference=media_ref,
            source_range=TimeRange(
                start_time=RationalTime(tc_offset + start_frames, fps_int),
                duration=RationalTime(dur_frames, fps_int),
            ),
        )
        target.append(clip)

    # Audio track (music bed)
    audio_info = edit_plan.get("audio_track")
    if audio_info and audio_info.get("source_file"):
        audio_path = audio_info["source_file"]
        a_start = float(audio_info.get("start_sec", 0))
        a_end = float(audio_info.get("end_sec", 0))
        a_dur = a_end - a_start
        if a_dur > 0:
            audio_tc = tc_offsets.get(audio_path, 0)
            audio_dur_sec = clip_durations.get(audio_path)
            audio_avail_frames = round(audio_dur_sec * fps_int) if audio_dur_sec else 360000
            sample_rate, channels = ffprobe_audio_info(Path(audio_path))

            a1 = otio.schema.Track(name="A1-Music", kind=otio.schema.TrackKind.Audio)
            audio_ref = otio.schema.ExternalReference(
                target_url=Path(audio_path).as_uri(),
                available_range=TimeRange(
                    RationalTime(audio_tc, fps_int),
                    RationalTime(audio_avail_frames, fps_int),
                ),
                metadata={
                    "fcp_xml": {
                        "media": {
                            "audio": {
                                "channelcount": str(channels),
                                "samplecharacteristics": {
                                    "depth": "16",
                                    "samplerate": str(sample_rate),
                                },
                            }
                        }
                    }
                },
            )
            audio_clip = otio.schema.Clip(
                name=Path(audio_path).stem,
                media_reference=audio_ref,
                source_range=TimeRange(
                    start_time=RationalTime(audio_tc + round(a_start * fps_int), fps_int),
                    duration=RationalTime(round(a_dur * fps_int), fps_int),
                ),
            )
            a1.append(audio_clip)
            timeline.tracks.extend([v1, v2, a1])
        else:
            timeline.tracks.extend([v1, v2])
    else:
        timeline.tracks.extend([v1, v2])

    return timeline


def render_xml(root: Path, edit_plan: dict, sidecars: list[dict]) -> tuple[Path, list[str]]:
    """Convert an edit plan to FCP7 XML with correct timecodes.

    Returns (xml_path, tc_debug_lines).  Pure local operation — no Gemini.
    """
    # Timeline fps = highest fps found across video sidecars.
    video_fps_values = [
        sc.get("fps", 0) for sc in sidecars
        if sc.get("media_type") != "audio" and sc.get("fps")
    ]
    timeline_fps = max(video_fps_values) if video_fps_values else 24.0

    # Probe each source file with ffprobe for start timecode and duration.
    tc_offsets: dict[str, int] = {}
    clip_durations: dict[str, float] = {}
    tc_debug: list[str] = []
    for sc in sidecars:
        fp = sc.get("file_path")
        if not fp:
            continue
        clip_fps = sc.get("fps", timeline_fps)
        media_path = Path(fp)
        is_audio = sc.get("media_type") == "audio"
        exists = media_path.exists()
        if exists:
            dur = ffprobe_duration(media_path)
            if dur:
                clip_durations[fp] = dur
            if not is_audio:
                probe_tc = ffprobe_start_tc(media_path)
                if probe_tc:
                    tc_offsets[fp] = tc_to_frames(probe_tc, clip_fps)
                    tc_debug.append(f"{media_path.name}: TC={probe_tc} → {tc_offsets[fp]}f, dur={dur:.2f}s")
                else:
                    tc_debug.append(f"{media_path.name}: no TC, dur={dur}s")
        else:
            tc_debug.append(f"{media_path.name}: file not found")

    log.info("TC offsets: %d/%d, durations: %d/%d",
             len(tc_offsets), len(sidecars), len(clip_durations), len(sidecars))

    timeline = build_otio_timeline(edit_plan, timeline_fps, tc_offsets, clip_durations)
    tl_name = edit_plan.get("timeline_name", "AI_Edit")
    # Sanitise for filesystem (macOS forbids colons, Windows forbids more).
    safe_name = tl_name.replace(":", " -").replace("/", "-").replace("\\", "-")
    # Append short timestamp to avoid overwriting previous exports.
    import time as _time
    stamp = _time.strftime("%m%d-%H%M")
    xml_path = root / f"{safe_name}_{stamp}.xml"
    otio.adapters.write_to_file(timeline, str(xml_path), adapter_name="fcp_xml")
    return xml_path, tc_debug
