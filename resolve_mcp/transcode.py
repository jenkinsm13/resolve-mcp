"""
Video transcoding for Gemini upload — downsample to HEVC/AAC MP4 at ≤1280px.
Uses VideoToolbox on Apple Silicon, libx265 elsewhere.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

from .config import GEMINI_MAX_BYTES, GEMINI_MAX_LONG_EDGE, SAFE_CODECS, log
from .ffprobe import ffprobe_codec, ffprobe_duration, ffprobe_resolution


def _detect_hw_encoder() -> Optional[str]:
    """Return the best available hardware HEVC encoder, or None."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=10,
        )
        encoders = result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if sys.platform == "darwin" and "hevc_videotoolbox" in encoders:
        return "hevc_videotoolbox"
    return None


# Cache at module load so we don't probe ffmpeg on every file
_HW_ENCODER: Optional[str] = None
_HW_ENCODER_CHECKED = False


def get_hw_encoder() -> Optional[str]:
    global _HW_ENCODER, _HW_ENCODER_CHECKED
    if not _HW_ENCODER_CHECKED:
        _HW_ENCODER = _detect_hw_encoder()
        _HW_ENCODER_CHECKED = True
    return _HW_ENCODER


def _needs_transcode(video_path: Path) -> bool:
    """Decide whether a video needs transcoding before Gemini upload."""
    if video_path.stat().st_size > GEMINI_MAX_BYTES:
        return True
    codec = ffprobe_codec(video_path)
    if codec is None:
        return True
    if codec not in SAFE_CODECS:
        return True
    w, h = ffprobe_resolution(video_path)
    if w is not None and h is not None:
        if max(w, h) > GEMINI_MAX_LONG_EDGE:
            return True
    return False


def _pick_quality_params(source_path: Path, duration_sec: float) -> list[str]:
    """Return ffmpeg encoder + quality flags appropriate to the platform."""
    src_gb = source_path.stat().st_size / (1024 ** 3)
    hw = get_hw_encoder()

    if hw:
        if duration_sec < 600 and src_gb < 4:
            q = 65
        elif duration_sec < 1800:
            q = 55
        else:
            q = 45
        return ["-c:v", hw, "-q:v", str(q), "-tag:v", "hvc1"]
    else:
        if duration_sec < 600 and src_gb < 4:
            crf = 26
        elif duration_sec < 1800:
            crf = 28
        else:
            crf = 32
        return ["-c:v", "libx265", "-preset", "fast", "-crf", str(crf)]


def prepare_for_gemini(video_path: Path) -> Path:
    """Return a Gemini-safe file path.

    If the source is already H.264/H.265 at ≤1280px and under 2 GB, return as-is.
    Otherwise, transcode to HEVC/AAC MP4 and cache as {name}.gemini.mp4.
    """
    if not _needs_transcode(video_path):
        return video_path

    cache_path = video_path.with_suffix(".gemini.mp4")
    if cache_path.exists():
        return cache_path

    duration = ffprobe_duration(video_path) or 300.0
    encoder_flags = _pick_quality_params(video_path, duration)
    hw = get_hw_encoder() or "libx265"

    log.info("Transcoding %s → %s (%s)", video_path.name, cache_path.name, hw)

    scale_filter = (
        f"scale='min(1,{GEMINI_MAX_LONG_EDGE}/max(iw,ih))*iw':"
        f"'min(1,{GEMINI_MAX_LONG_EDGE}/max(iw,ih))*ih',"
        f"scale=trunc(iw/2)*2:trunc(ih/2)*2"
    )

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", scale_filter,
        *encoder_flags,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-map_metadata", "-1",
        str(cache_path),
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=3600, check=True)
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg not found. Install it: brew install ffmpeg (macOS) "
            "or download from https://ffmpeg.org"
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg transcode failed for {video_path.name}: {exc.stderr[:500]}")

    if cache_path.stat().st_size > GEMINI_MAX_BYTES:
        log.warning(
            "%s is still %.1f GB after transcode — Gemini may reject it.",
            cache_path.name,
            cache_path.stat().st_size / (1024 ** 3),
        )

    return cache_path
