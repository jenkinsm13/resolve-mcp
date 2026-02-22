"""
Per-clip transform helpers: zoom/pan/tilt (SetProperty) and Fusion speed ramps.
"""

import logging
from pathlib import Path

log = logging.getLogger(__name__)

# DynamicZoomEase enum values (from Resolve scripting docs).
_DYNAMIC_ZOOM_EASE: dict[str, int] = {
    "linear": 0,
    "ease_in": 1,
    "ease_out": 2,
    "ease_in_and_out": 3,
}


def _apply_clip_transform(item, cut: dict) -> None:
    """Apply zoom / pan / tilt / dynamic_zoom_ease from *cut* to *item*.

    zoom        – scale multiplier: 1.0 = 100%, 1.2 = 20% push-in
    pan         – pixels, positive = right
    tilt        – pixels, positive = up
    dynamic_zoom_ease – "linear" | "ease_in" | "ease_out" | "ease_in_and_out"
    """
    try:
        zoom = cut.get("zoom")
        pan  = cut.get("pan")
        tilt = cut.get("tilt")
        dze  = cut.get("dynamic_zoom_ease")

        if zoom is not None:
            z = float(zoom)
            item.SetProperty("ZoomX", z)
            item.SetProperty("ZoomY", z)
        if pan is not None:
            item.SetProperty("Pan", float(pan))
        if tilt is not None:
            item.SetProperty("Tilt", float(tilt))
        if dze is not None:
            item.SetProperty("DynamicZoomEase",
                             _DYNAMIC_ZOOM_EASE.get(str(dze).lower(), 0))
    except Exception as exc:
        log.warning("Clip transform failed: %s", exc)


def _bake_speed_ramp(points: list, fps: float, bake_step: int = 1) -> list:
    """Convert [{t_sec, speed}] to baked [(out_frame, src_frame)] keyframe pairs.

    Uses piecewise-linear speed interpolation between control points.
    The src_frame value at each output frame is the cumulative integral of
    speed over time — i.e. the source position the player should read.
    """
    if not points:
        return []

    pts = sorted(points, key=lambda p: p["t_sec"])
    max_out = round(pts[-1]["t_sec"] * fps)

    def _speed_at(t_sec: float) -> float:
        for i in range(len(pts) - 1):
            t0, t1 = pts[i]["t_sec"], pts[i + 1]["t_sec"]
            if t0 <= t_sec <= t1:
                if t1 == t0:
                    return pts[i]["speed"]
                a = (t_sec - t0) / (t1 - t0)
                return pts[i]["speed"] + a * (pts[i + 1]["speed"] - pts[i]["speed"])
        return pts[-1]["speed"] if t_sec > pts[-1]["t_sec"] else pts[0]["speed"]

    src, result = 0.0, []
    for t in range(0, max_out + 1, bake_step):
        result.append((t, src))
        src += _speed_at(t / fps)
    return result


def _apply_speed_ramp(item, ramp_points: list, fps: float) -> bool:
    """Wire a Fusion TimeStretcher into *item* and keyframe it for a speed ramp.

    Tries tool IDs "TimeStretcher", "TimeSpeed", "TimeScaler" in order.
    Probes for the source-time input name across known variants.
    Returns True on success.
    """
    if not ramp_points:
        return False
    try:
        fcomp = item.AddFusionComp()
        if fcomp is None:
            fcomp = item.GetFusionCompByIndex(item.GetFusionCompCount())
        if fcomp is None:
            return False

        mi = fcomp.FindTool("MediaIn1")
        mo = fcomp.FindTool("MediaOut1")
        if not mi or not mo:
            return False

        ts = None
        for tid in ("TimeStretcher", "TimeSpeed", "TimeScaler"):
            try:
                ts = fcomp.AddTool(tid)
                if ts:
                    break
            except Exception:
                pass
        if not ts:
            return False

        try:
            ts.Input = mi.Output
            mo.Input = ts.Output
        except Exception:
            try:
                ts.ConnectInput("Input", mi)
                mo.ConnectInput("Input", ts)
            except Exception:
                return False

        time_input = None
        for candidate in ("SourceTime", "Source Time", "InputTime", "Time"):
            try:
                ts.SetInput(candidate, 0.0, 0)
                time_input = candidate
                break
            except Exception:
                pass
        if time_input is None:
            try:
                for _k, inp in (ts.GetInputList() or {}).items():
                    n = str(getattr(inp, "Name", _k)).lower()
                    if "time" in n or "source" in n:
                        time_input = getattr(inp, "Name", _k)
                        break
            except Exception:
                pass
        if time_input is None:
            return False

        for out_frame, src_frame in _bake_speed_ramp(ramp_points, fps):
            try:
                ts.SetInput(time_input, float(src_frame), int(out_frame))
            except Exception:
                pass
        return True

    except Exception as exc:
        log.warning("Speed ramp failed: %s", exc)
        return False
