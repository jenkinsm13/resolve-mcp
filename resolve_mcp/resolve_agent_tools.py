"""
MCP tools for Gemini agent editing sessions.

These let Claude trigger Gemini agent sessions where Gemini has direct
tool-calling access to DaVinci Resolve for building timelines.

Unlike the EDL JSON path (resolve_build_timeline), the agent path gives
Gemini interactive feedback — it sees the result of each operation and
can adapt.  Both paths coexist; use whichever fits the task.
"""

import json
import threading
from pathlib import Path

from .build_worker import _active_build_workers
from .config import client, log, mcp
from .gemini_agent import run_agent_loop
from .media import load_sidecars
from .resolve import _boilerplate
from .resolve_ingest_tools import _dirs_from_bin
from .timeline import upload_media_for_editing

_AGENT_PROGRESS_FILE = ".resolve_agent_progress.json"


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------


def _agent_worker(root: Path, sidecars: list, instruction: str, num_edits: int) -> None:
    """Background thread: upload media once → run *num_edits* agent sessions."""
    progress_file = root / _AGENT_PROGRESS_FILE

    def _write(data: dict) -> None:
        progress_file.write_text(json.dumps(data, indent=2))

    try:
        _write(
            {
                "status": "uploading",
                "detail": f"Uploading {len(sidecars)} file(s) to Gemini…",
                "completed": 0,
                "total": num_edits,
                "error": None,
            }
        )

        file_refs = upload_media_for_editing(sidecars)
        if not file_refs:
            _write(
                {
                    "status": "error",
                    "detail": "No media uploaded — check proxies exist.",
                    "completed": 0,
                    "total": num_edits,
                    "error": "upload_media_for_editing returned empty.",
                }
            )
            return

        summaries: list[str] = []

        for i in range(1, num_edits + 1):
            tool_log: list[dict] = []

            _write(
                {
                    "status": "editing",
                    "detail": f"Gemini building variant {i}/{num_edits}…",
                    "completed": i - 1,
                    "total": num_edits,
                    "error": None,
                    "tool_calls": [],
                }
            )

            def _on_progress(name: str, args: dict, result: str, _i: int = i, _log: list = tool_log) -> None:
                _log.append({"tool": name, "result": result[:200]})
                _write(
                    {
                        "status": "editing",
                        "detail": f"Variant {_i}/{num_edits}: {name}",
                        "completed": _i - 1,
                        "total": num_edits,
                        "error": None,
                        "tool_calls": _log[-10:],
                    }
                )

            try:
                summary = run_agent_loop(
                    sidecars=sidecars,
                    instruction=instruction,
                    file_refs=list(file_refs),
                    variant_num=i,
                    total_variants=num_edits,
                    on_progress=_on_progress,
                )
            except Exception as exc:
                summary = f"Variant {i} failed: {exc}"
                log.warning("Agent variant %d failed: %s", i, exc)

            summaries.append(f"v{i}: {summary}")

        _write(
            {
                "status": "complete",
                "detail": f"{num_edits} edit(s) built.\n" + "\n".join(summaries),
                "completed": num_edits,
                "total": num_edits,
                "error": None,
            }
        )

    except Exception as exc:
        log.exception("Agent worker crashed.")
        _write(
            {
                "status": "error",
                "detail": "Agent session crashed.",
                "completed": 0,
                "total": num_edits,
                "error": str(exc),
            }
        )


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


def _resolve_root(bin_name_or_folder: str) -> Path | None:
    """Resolve a bin name or folder path to a filesystem root directory."""
    candidate = Path(bin_name_or_folder)
    if candidate.is_absolute() and candidate.is_dir():
        return candidate

    try:
        _, _, media_pool = _boilerplate()
    except ValueError:
        return None

    target, dirs = _dirs_from_bin(media_pool, bin_name_or_folder)
    if not target or not dirs:
        return None

    # Pick the directory containing the most clips.
    dir_counts: dict[str, int] = {}
    for clip in target.GetClipList() or []:
        try:
            fp = clip.GetClipProperty("File Path")
            if fp:
                d = str(Path(fp).parent)
                dir_counts[d] = dir_counts.get(d, 0) + 1
        except Exception:
            continue

    if dir_counts:
        return Path(max(dir_counts, key=dir_counts.get))
    return Path(next(iter(dirs.values()))) if dirs else None


@mcp.tool
def resolve_agent_edit(bin_name_or_folder: str, instruction: str, num_edits: int = 4) -> str:
    """Launch a Gemini agent session that builds timelines using Resolve tools.

    Unlike ``resolve_build_timeline`` (which generates an EDL JSON and executes
    it in bulk), the agent mode gives Gemini interactive tool access — it can
    see results of each operation and adapt its editing decisions in real time.

    Gemini creates *num_edits* very different timeline variants, each with a
    distinct creative approach (different clip selection, pacing, structure).

    *bin_name_or_folder*: Resolve bin name or absolute folder path with sidecars.
    *instruction*: Creative direction for the edit.
    *num_edits*: How many distinct edit variants to generate (1-8, default 4).

    Monitor progress with ``resolve_agent_status(bin_name_or_folder)``.
    """
    if client is None:
        return "Error: GEMINI_API_KEY not set. Agent mode requires Gemini."

    num_edits = max(1, min(int(num_edits), 8))

    root = _resolve_root(bin_name_or_folder)
    if root is None:
        return f"Could not locate '{bin_name_or_folder}' as bin or folder."

    sidecars = load_sidecars(root)
    if not sidecars:
        return f"No sidecar JSONs in '{root}'. Run ingest first."

    key = f"agent:{root}"
    if key in _active_build_workers and _active_build_workers[key].is_alive():
        return "Agent session already running for this target."

    t = threading.Thread(
        target=_agent_worker,
        args=(root, sidecars, instruction, num_edits),
        daemon=True,
    )
    t.start()
    _active_build_workers[key] = t

    return (
        f"Agent started: {num_edits} edit variant(s) from {len(sidecars)} clip(s).\n"
        f"Monitor: resolve_agent_status('{bin_name_or_folder}')"
    )


@mcp.tool
def resolve_agent_status(bin_name_or_folder: str) -> str:
    """Check progress of a ``resolve_agent_edit`` session.

    Pass the same *bin_name_or_folder* used to start the session.
    Returns status, completion count, and recent tool calls.
    """
    root = _resolve_root(bin_name_or_folder)
    if root is None:
        return f"Could not locate '{bin_name_or_folder}'."

    progress_file = root / _AGENT_PROGRESS_FILE
    if not progress_file.exists():
        return "No agent session in progress for this target."

    try:
        prog = json.loads(progress_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "Could not read agent progress file."

    status = prog.get("status", "unknown")
    detail = prog.get("detail", "")
    completed = prog.get("completed", 0)
    total = prog.get("total", 0)
    error = prog.get("error")

    if status == "complete":
        return f"Agent complete ({completed}/{total} edits):\n{detail}"
    if status == "error":
        return f"Agent failed: {detail}" + (f"\n{error}" if error else "")
    return f"Agent {status} ({completed}/{total}): {detail}"
