"""
Timeline building: AppendToTimeline pipeline, marker utilities, XML import fallback.
"""

import time
from pathlib import Path

from .resolve import (
    get_resolve, _collect_clips_recursive, _unique_timeline_name, _FPS_MAP,
)
from .resolve_transforms import _apply_clip_transform, _apply_speed_ramp


def build_timeline_direct(edit_plan: dict, resolve_obj) -> tuple:
    """Build a Resolve timeline from *edit_plan* using ``AppendToTimeline``.

    Returns ``(success: bool, message: str)``.
    Timeline fps is taken from the project's delivery setting.
    Per-clip native fps is read individually for accurate source-frame numbers.
    """
    project = resolve_obj.GetProjectManager().GetCurrentProject()
    if not project:
        return (False, "No project open in Resolve.")

    media_pool = project.GetMediaPool()
    cuts = edit_plan.get("cuts", [])
    if not cuts:
        return (False, "Edit plan has no cuts.")

    pool_clips = _collect_clips_recursive(media_pool.GetRootFolder())

    timeline_fps: float = 59.94
    try:
        fps_str = project.GetSetting("timelineFrameRate")
        if fps_str:
            timeline_fps = float(fps_str)
    except Exception:
        pass

    timeline_name = edit_plan.get("timeline_name", "AI_Edit")
    name, timeline = _unique_timeline_name(media_pool, timeline_name)
    if not timeline:
        return (False, f"Could not create timeline '{timeline_name}' in Resolve.")

    project.SetCurrentTimeline(timeline)
    fps_label = _FPS_MAP.get(round(timeline_fps, 3), str(timeline_fps))
    try:
        timeline.SetSetting("timelineFrameRate", fps_label)
    except Exception:
        pass

    clip_items: list[dict] = []
    clip_cuts:  list[dict] = []
    missing: list[str] = []

    for cut in cuts:
        src = Path(cut["source_file"])
        clip = pool_clips.get(src.stem) or pool_clips.get(src.name)

        if not clip:
            imported = media_pool.ImportMedia([str(src)])
            if imported:
                clip = imported[0]
                pool_clips[src.stem] = clip
                pool_clips[src.name] = clip

        if clip:
            clip_fps = timeline_fps
            try:
                clip_fps = float(clip.GetClipProperty("FPS"))
            except Exception:
                pass

            clip_dict: dict = {
                "mediaPoolItem": clip,
                "startFrame": round(float(cut["start_sec"]) * clip_fps),
                "endFrame": round(float(cut["end_sec"]) * clip_fps),
                "mediaType": 1,
            }
            if "timeline_in" in cut:
                clip_dict["recordFrame"] = round(float(cut["timeline_in"]) * timeline_fps)
                clip_dict["trackIndex"] = cut.get("track", 1)
            clip_items.append(clip_dict)
            clip_cuts.append(cut)
        else:
            missing.append(src.name)

    if clip_items and "recordFrame" in clip_items[0]:
        paired = sorted(
            zip(clip_items, clip_cuts),
            key=lambda c: (c[0].get("trackIndex", 1), c[0]["recordFrame"]),
        )
        clip_items, clip_cuts = [p[0] for p in paired], [p[1] for p in paired]

    appended = media_pool.AppendToTimeline(clip_items) if clip_items else []

    if appended:
        for i, item in enumerate(appended):
            if i < len(clip_cuts):
                cut = clip_cuts[i]
                _apply_clip_transform(item, cut)
                ramp = cut.get("speed_ramp")
                if ramp:
                    _apply_speed_ramp(item, ramp, timeline_fps)

    # Audio track (music bed)
    audio_info = edit_plan.get("audio_track")
    if audio_info and audio_info.get("source_file"):
        a_path = Path(audio_info["source_file"])
        a_clip = pool_clips.get(a_path.stem) or pool_clips.get(a_path.name)
        if not a_clip:
            imported = media_pool.ImportMedia([str(a_path)])
            if imported:
                a_clip = imported[0]
        if a_clip:
            a_start = float(audio_info.get("start_sec", 0))
            a_end = float(audio_info.get("end_sec", 0))
            if a_end > a_start:
                media_pool.AppendToTimeline([{
                    "mediaPoolItem": a_clip,
                    "startFrame": round(a_start * timeline_fps),
                    "endFrame": round(a_end * timeline_fps),
                    "mediaType": 2,
                }])

    n_appended = len(appended) if appended else 0
    msg = f"Timeline '{name}' created with {n_appended}/{len(clip_items)} video clips."
    if missing:
        msg += f" Missing from pool: {', '.join(missing)}."
    return (n_appended > 0 or len(clip_items) == 0, msg)


def read_timeline_markers(timeline) -> list:
    """Return all markers on *timeline* sorted by frame position.

    Each entry: ``{frame, sec, color, name, note}``.
    """
    try:
        fps = float(timeline.GetSetting("timelineFrameRate"))
    except Exception:
        fps = 24.0

    raw = timeline.GetMarkers() or {}
    markers = []
    for frame_id, info in sorted(raw.items(), key=lambda x: int(x[0])):
        markers.append({
            "frame": int(frame_id),
            "sec": int(frame_id) / fps,
            "color": info.get("color", "Blue"),
            "name": info.get("name", ""),
            "note": info.get("note", ""),
        })
    return markers


def markers_to_slots(markers: list) -> list:
    """Pair consecutive same-color markers into cut slots.

    Blue → track 1; each additional color → tracks 2, 3, … in order of first appearance.
    Returns slots sorted by ``timeline_in``.
    """
    by_color: dict = {}
    color_order: list = []
    for m in markers:
        c = m["color"]
        if c not in by_color:
            by_color[c] = []
            color_order.append(c)
        by_color[c].append(m)

    track_map: dict = {}
    next_track = 2
    for color in color_order:
        if color == "Blue":
            track_map[color] = 1
        else:
            track_map[color] = next_track
            next_track += 1

    slots = []
    slot_idx = 1
    for color in color_order:
        track = track_map[color]
        color_markers = by_color[color]
        for i in range(0, len(color_markers) - 1, 2):
            m_in, m_out = color_markers[i], color_markers[i + 1]
            note = m_in.get("note") or m_out.get("note") or ""
            slots.append({
                "slot": slot_idx,
                "track": track,
                "timeline_in": m_in["sec"],
                "timeline_out": m_out["sec"],
                "color": color,
                "note": note,
            })
            slot_idx += 1

    slots.sort(key=lambda s: s["timeline_in"])
    return slots


def try_resolve_import(xml_path: Path, edit_plan: dict) -> str:
    """Best-effort FCP7 XML import into DaVinci Resolve (legacy fallback)."""
    resolve = get_resolve()
    if not resolve:
        return "Resolve not detected — import XML manually."
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return "No Resolve project open — import XML manually."

    media_pool = project.GetMediaPool()
    source_files: set[str] = set()
    for cut in edit_plan.get("cuts", []):
        sf = cut.get("source_file")
        if sf and Path(sf).exists():
            source_files.add(sf)
    audio = edit_plan.get("audio_track")
    if audio and audio.get("source_file"):
        sf = audio["source_file"]
        if Path(sf).exists():
            source_files.add(sf)

    media_msgs: list[str] = []
    if source_files:
        imported = media_pool.ImportMedia(sorted(source_files))
        media_msgs.append(f"{len(imported)} media imported" if imported else "media import returned falsy")

    result = media_pool.ImportTimelineFromFile(str(xml_path))
    status = "Imported" if result else "Timeline import falsy"
    return f"{status} ({', '.join(media_msgs)}) — import XML manually." if not result else f"{status} ({', '.join(media_msgs)})."
