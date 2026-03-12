"""
Media file discovery and sidecar loading.
"""

import json
from pathlib import Path

from .config import VIDEO_EXTS, AUDIO_EXTS, log


def is_junk(p: Path) -> bool:
    """Return True for macOS resource forks, dotfiles, and other junk."""
    return p.name.startswith(".") or p.name.startswith("._")


def list_all_videos(root: Path) -> list[Path]:
    """Return all source video files in *root* (excludes .gemini.mp4 caches)."""
    return sorted(
        p for p in root.iterdir()
        if p.suffix.lower() in VIDEO_EXTS
        and p.is_file()
        and ".gemini" not in p.stem
        and not is_junk(p)
    )


def list_all_audio(root: Path) -> list[Path]:
    """Return all audio files in *root*."""
    return sorted(
        p for p in root.iterdir()
        if p.suffix.lower() in AUDIO_EXTS
        and p.is_file()
        and not is_junk(p)
    )


def list_pending_videos(root: Path) -> list[Path]:
    """Return video files in *root* that lack a sidecar JSON."""
    return [
        p for p in list_all_videos(root)
        if not p.with_suffix(p.suffix + ".json").exists()
    ]


def list_pending_audio(root: Path) -> list[Path]:
    """Return audio files in *root* that lack a sidecar JSON."""
    return [
        p for p in list_all_audio(root)
        if not p.with_suffix(p.suffix + ".json").exists()
    ]


def find_proxy(media_path: Path) -> Path:
    """Return the .gemini.mp4 proxy if it exists, otherwise the original file."""
    proxy = media_path.with_suffix(".gemini.mp4")
    if proxy.exists():
        return proxy
    return media_path


def load_sidecars(folder: Path) -> list[dict]:
    """Load sidecar JSON for each media file in *folder*.

    Sidecars follow the naming convention: {mediafile}.json
    (e.g. IMG_0004.mov.json for IMG_0004.mov).
    """
    sidecars = []
    all_media_exts = VIDEO_EXTS | AUDIO_EXTS
    media_files = sorted(
        f for f in folder.iterdir()
        if f.suffix.lower() in all_media_exts and not f.name.startswith(".")
    )
    for mf in media_files:
        sidecar_path = mf.with_name(mf.name + ".json")
        if not sidecar_path.exists():
            continue
        try:
            data = json.loads(sidecar_path.read_text(encoding="utf-8"))
            if "file_path" not in data or not data["file_path"]:
                data["file_path"] = str(mf)
            sidecars.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return sidecars
