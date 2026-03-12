"""
Build timeline background worker: Gemini edit plan → XML + Resolve AppendToTimeline.
"""

import json
import threading
from pathlib import Path
from typing import Optional

from google.genai import types

from .config import MODEL, client, log
from .retry import retry_gemini
from .prompts import EDIT_PROMPT_TEMPLATE, MUSIC_BRIEF_ADDENDUM
from .timeline import upload_media_for_editing, render_xml
from .outputs import save_directors_notes, save_voiceover_script, save_music_brief
from .resolve import get_resolve, build_timeline_direct

_BUILD_PROGRESS_FILENAME = ".build_progress.json"

# Active build worker threads keyed by resolved folder path.
_active_build_workers: dict[str, threading.Thread] = {}


def _write_build_progress(root: Path, data: dict) -> None:
    (root / _BUILD_PROGRESS_FILENAME).write_text(json.dumps(data, indent=2))


def _read_build_progress(root: Path) -> Optional[dict]:
    pf = root / _BUILD_PROGRESS_FILENAME
    if not pf.exists():
        return None
    try:
        return json.loads(pf.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _build_worker(root: Path, sidecars: list[dict], instruction: str,
                  cached_plan: Optional[dict] = None) -> None:
    """Background thread: optionally query Gemini for edit plan, then build timeline."""
    try:
        if cached_plan:
            edit_plan = cached_plan
        else:
            _write_build_progress(root, {
                "status": "uploading",
                "detail": f"Uploading {len(sidecars)} media file(s) to Gemini…",
                "error": None, "xml_path": None,
            })

            file_refs = upload_media_for_editing(sidecars)
            if not file_refs:
                _write_build_progress(root, {
                    "status": "error",
                    "detail": "Failed to upload any media files.",
                    "error": "No files uploaded — check proxies exist.", "xml_path": None,
                })
                return

            _write_build_progress(root, {
                "status": "editing",
                "detail": f"Gemini reviewing {len(file_refs)} files and planning cuts…",
                "error": None, "xml_path": None,
            })

            prompt_text = EDIT_PROMPT_TEMPLATE.format(
                sidecars_json=json.dumps(sidecars, indent=2),
                instruction=instruction,
            )
            if not any(sc.get("media_type") == "audio" for sc in sidecars):
                prompt_text += MUSIC_BRIEF_ADDENDUM

            response = retry_gemini(
                client.models.generate_content, model=MODEL,
                contents=list(file_refs) + [prompt_text],
                config=types.GenerateContentConfig(
                    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                    response_mime_type="application/json",
                ),
            )

            try:
                decoder = json.JSONDecoder()
                edit_plan, _ = decoder.raw_decode(response.text.strip())
                if isinstance(edit_plan, list):
                    edit_plan = next((x for x in edit_plan if isinstance(x, dict)), None)
                    if edit_plan is None:
                        raise json.JSONDecodeError("No dict found in list", response.text, 0)
            except json.JSONDecodeError as exc:
                _write_build_progress(root, {
                    "status": "error", "detail": "Gemini returned invalid JSON.",
                    "error": f"{exc}\nRaw: {response.text[:500]}", "xml_path": None,
                })
                return

            if not edit_plan.get("cuts"):
                _write_build_progress(root, {
                    "status": "error", "detail": "Gemini returned an empty cut list.",
                    "error": "No cuts in EDL. Try a different instruction.", "xml_path": None,
                })
                return

            safe_tl = edit_plan.get("timeline_name", "AI_Edit").replace(":", " -").replace("/", "-").replace("\\", "-")
            (root / f"{safe_tl}.edl.json").write_text(json.dumps(edit_plan, indent=2))

        tl_name = edit_plan.get("timeline_name", "AI_Edit").replace(":", " -").replace("/", "-").replace("\\", "-")
        save_directors_notes(root, tl_name, edit_plan)
        save_voiceover_script(root, tl_name, edit_plan)
        save_music_brief(root, tl_name, edit_plan)

        cuts = edit_plan.get("cuts", [])
        _write_build_progress(root, {
            "status": "building",
            "detail": f"Building timeline with {len(cuts)} cuts…",
            "error": None, "xml_path": None,
        })

        xml_path, tc_debug = None, []
        try:
            xml_path, tc_debug = render_xml(root, edit_plan, sidecars)
        except Exception as xml_exc:
            log.warning("XML render failed (non-fatal): %s", xml_exc)

        resolve_obj = get_resolve()
        if resolve_obj:
            success, resolve_msg = build_timeline_direct(edit_plan, resolve_obj)
            if not success and xml_path:
                resolve_msg += f" Backup XML: {xml_path.name}"
        else:
            xml_note = f" XML: {xml_path.name}" if xml_path else ""
            resolve_msg = f"Resolve not running — import XML manually.{xml_note}"

        _write_build_progress(root, {
            "status": "complete",
            "detail": (
                f"Timeline '{edit_plan.get('timeline_name')}' — "
                f"{len(cuts)} cuts. TC offsets: {len(tc_debug)} probed. {resolve_msg}"
            ),
            "error": None,
            "xml_path": str(xml_path),
            "tc_debug": tc_debug[:10],
        })

    except Exception as exc:
        _write_build_progress(root, {
            "status": "error",
            "detail": "Unexpected error during timeline build.",
            "error": str(exc), "xml_path": None,
        })
