"""
ffprobe wrappers for extracting codec, duration, fps, timecode, resolution,
and audio info from media files.
"""

import subprocess
from pathlib import Path
from typing import Optional


def ffprobe_codec(video_path: Path) -> Optional[str]:
    """Return the lowercase video codec name via ffprobe, or None on failure."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "csv=p=0",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        codec = result.stdout.strip().lower()
        return codec if codec else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def ffprobe_duration(video_path: Path) -> Optional[float]:
    """Return duration in seconds via ffprobe, or None."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return None


def ffprobe_fps(video_path: Path) -> Optional[float]:
    """Return average frame rate via ffprobe, or None.

    Parses r_frame_rate (rational like '30000/1001' for 29.97) and
    returns the float value.  This is authoritative — never trust
    Gemini's fps guess over ffprobe.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "csv=p=0",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        raw = result.stdout.strip()
        if "/" in raw:
            num, den = raw.split("/")
            return float(num) / float(den)
        return float(raw)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, ZeroDivisionError):
        return None


def ffprobe_start_tc(video_path: Path) -> Optional[str]:
    """Return the embedded start timecode string (e.g. '14:40:52:00') via ffprobe.

    Tries stream-level timecode first (most reliable for camera footage),
    then falls back to format-level.  Returns None if no TC found.
    """
    for show_entries in [
        "stream_tags=timecode",
        "format_tags=timecode",
    ]:
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", show_entries,
                    "-of", "csv=p=0",
                    str(video_path),
                ],
                capture_output=True, text=True, timeout=30,
            )
            tc = result.stdout.strip().strip(",")
            if tc and ":" in tc:
                return tc
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return None


def tc_to_frames(tc_str: str, fps: float) -> int:
    """Convert timecode 'HH:MM:SS:FF' or 'HH:MM:SS;FF' to FCP7 integer-timebase frame count.

    FCP7 XML (and DaVinci Resolve) stores frame counts at the integer timebase
    (60 for 59.94 fps, 30 for 29.97 fps).  Using fractional fps here (e.g. 59.94)
    causes a ~6-second drift per 96 minutes that shows as a TC mismatch on import.
    """
    parts = tc_str.replace(";", ":").split(":")
    if len(parts) != 4:
        return 0
    try:
        h, m, s, f = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        return 0
    fps_int = round(fps)  # 60 for 59.94, 30 for 29.97, 24 for 23.976
    return h * 3600 * fps_int + m * 60 * fps_int + s * fps_int + f


def ffprobe_resolution(video_path: Path) -> tuple[Optional[int], Optional[int]]:
    """Return (width, height) via ffprobe, or (None, None)."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        parts = result.stdout.strip().split(",")
        return int(parts[0]), int(parts[1])
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
        return None, None


def ffprobe_audio_info(audio_path: Path) -> tuple[int, int]:
    """Return (sample_rate, channels) via ffprobe.  Defaults to (48000, 2)."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=sample_rate,channels",
                "-of", "csv=p=0",
                str(audio_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        parts = result.stdout.strip().split(",")
        return int(parts[0]), int(parts[1])
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
        return 48000, 2
