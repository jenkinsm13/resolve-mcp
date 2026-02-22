"""
Gemini agent loop: gives Gemini direct tool-calling access to DaVinci Resolve.

Claude (MCP agent) controls *when* this runs.  Gemini gets a curated subset
of resolve_* tools and builds timelines interactively, seeing results of each
operation before deciding the next step.

This is additive — the existing EDL JSON pipeline (resolve_build_timeline)
is unchanged.  The agent path is for richer, more adaptive editing sessions.
"""

from __future__ import annotations

import contextlib
import inspect
import json
import logging
from collections.abc import Callable

from .config import MODEL, client
from .retry import retry_gemini

log = logging.getLogger(__name__)

# Max tool-call round-trips per variant before forcing termination.
MAX_AGENT_TURNS = 50

# ---------------------------------------------------------------------------
# Agent system prompt
# ---------------------------------------------------------------------------

AGENT_PROMPT = """\
You are an expert video editor working inside DaVinci Resolve.
You have direct tool access to build and edit timelines.

AVAILABLE FOOTAGE (sidecar metadata — use file_path values as clip names):
{sidecars_json}

INSTRUCTION:
{instruction}

{variant_instruction}

Workflow:
1. Create a new timeline with resolve_create_empty_timeline.
2. Use resolve_search_clips to verify clip names in the media pool.
3. Use resolve_append_to_timeline to add clips (pass the filename or stem).
4. Use resolve_set_item_properties to adjust zoom, pan, tilt, opacity.
5. Use resolve_add_track if you need additional video or audio tracks.
6. Use resolve_insert_audio_at_playhead for music/audio beds.
7. Use resolve_list_clips_on_track to verify your work after adding clips.
8. Use resolve_add_marker_at for editorial notes explaining key decisions.

Editorial rules:
- Choose clips that serve the creative intent — don't use everything.
- Vary pacing: mix longer holds with quicker cuts for rhythm.
- Think about story arc: opening hook, development, climax, resolution.
- Use zoom/pan sparingly and purposefully — not on every clip.
- Track 1 = primary footage (A-roll), Track 2+ = B-roll/cutaways.

When finished, respond with a SHORT summary: timeline name, clip count,
duration estimate, and 1-2 sentences on the creative approach.
"""

MULTI_EDIT_VARIANT = """\
This is variant {variant_num} of {total_variants}.
Each variant MUST be SIGNIFICANTLY different from every other:
- Different clip selection and ordering
- Different pacing (some fast-cut, some slow and meditative)
- Different story structure (chronological vs. thematic vs. emotional arc)
- Different mood and energy level
- Different use of A-roll vs. B-roll balance

Name the timeline with "v{variant_num}" in it to distinguish variants.
Make this variant feel like a DIFFERENT EDITOR cut it.
"""

# ---------------------------------------------------------------------------
# Tool allowlist — curated subset of resolve_* tools for Gemini
# ---------------------------------------------------------------------------


def _get_agent_tools() -> dict[str, callable]:
    """Import and return {name: function} for each tool Gemini may call."""
    from .clip_edit_tools import (
        resolve_append_to_timeline,
        resolve_insert_clip_at_playhead,
        resolve_set_clip_color_on_timeline,
        resolve_set_item_properties,
        resolve_swap_clips,
    )
    from .clip_query_tools import resolve_get_item_properties, resolve_list_clips_on_track
    from .fairlight_tools import resolve_insert_audio_at_playhead
    from .marker_tools import resolve_add_marker_at, resolve_set_playhead
    from .media_pool_extras import resolve_create_empty_timeline
    from .media_pool_query_tools import resolve_search_clips
    from .timeline_insert_tools import resolve_insert_fusion_title, resolve_insert_title
    from .timeline_query_tools import resolve_get_timeline_info
    from .timeline_track_tools import (
        resolve_add_track,
        resolve_create_subtitles,
        resolve_set_track_name,
    )

    funcs = [
        # Timeline management
        resolve_create_empty_timeline,
        resolve_get_timeline_info,
        # Track management
        resolve_add_track,
        resolve_set_track_name,
        # Clip insertion
        resolve_append_to_timeline,
        resolve_insert_clip_at_playhead,
        # Clip editing
        resolve_set_item_properties,
        resolve_swap_clips,
        resolve_set_clip_color_on_timeline,
        # Queries (read-only — lets Gemini verify its work)
        resolve_list_clips_on_track,
        resolve_get_item_properties,
        resolve_search_clips,
        # Markers
        resolve_add_marker_at,
        resolve_set_playhead,
        # Titles
        resolve_insert_title,
        resolve_insert_fusion_title,
        # Audio
        resolve_insert_audio_at_playhead,
        # Subtitles
        resolve_create_subtitles,
    ]
    return {f.__name__: f for f in funcs}


# ---------------------------------------------------------------------------
# Python → Gemini schema conversion
# ---------------------------------------------------------------------------

_TYPE_MAP = {
    int: "integer",
    float: "number",
    bool: "boolean",
    str: "string",
}


def _build_declarations(tools: dict):
    """Convert Python tool functions into Gemini Tool objects with FunctionDeclarations."""
    from google.genai import types

    declarations = []
    for name, func in tools.items():
        unwrapped = inspect.unwrap(func)
        sig = inspect.signature(unwrapped)
        doc = inspect.getdoc(unwrapped) or name

        properties = {}
        required = []
        for pname, param in sig.parameters.items():
            ptype = _TYPE_MAP.get(param.annotation, "string")
            properties[pname] = {"type": ptype}
            if param.default is inspect.Parameter.empty:
                required.append(pname)

        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required

        declarations.append(
            types.FunctionDeclaration(
                name=name,
                description=doc.split("\n\n")[0],  # first paragraph
                parameters_json_schema=schema,
            )
        )

    return [types.Tool(function_declarations=declarations)]


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------


def _coerce_args(func: callable, args: dict) -> dict:
    """Best-effort type coercion of Gemini args to match Python signature."""
    unwrapped = inspect.unwrap(func)
    sig = inspect.signature(unwrapped)
    coerced = {}
    for pname, value in args.items():
        param = sig.parameters.get(pname)
        if param is not None and param.annotation in (int, float, bool):
            with contextlib.suppress(ValueError, TypeError):
                value = param.annotation(value)
        coerced[pname] = value
    return coerced


def run_agent_loop(
    sidecars: list,
    instruction: str,
    file_refs: list | None = None,
    variant_num: int = 0,
    total_variants: int = 1,
    on_progress: Callable | None = None,
) -> str:
    """Run one Gemini agent session that builds a timeline using tool calls.

    *file_refs*: Gemini file references from ``upload_media_for_editing()``.
    *variant_num*/*total_variants*: for multi-edit, identifies this variant.
    *on_progress*: callback ``(tool_name, args_dict, result_str)`` per call.

    Returns the final summary text from Gemini.
    """
    from google.genai import types

    tools_dict = _get_agent_tools()
    gemini_tools = _build_declarations(tools_dict)

    variant_text = ""
    if total_variants > 1:
        variant_text = MULTI_EDIT_VARIANT.format(
            variant_num=variant_num,
            total_variants=total_variants,
        )

    prompt_text = AGENT_PROMPT.format(
        sidecars_json=json.dumps(sidecars, indent=2),
        instruction=instruction,
        variant_instruction=variant_text,
    )

    # Build initial user turn with optional media file references.
    user_parts = []
    if file_refs:
        user_parts.extend(file_refs)
    user_parts.append(types.Part.from_text(text=prompt_text))

    history = [types.Content(role="user", parts=user_parts)]

    for turn in range(MAX_AGENT_TURNS):
        log.info("Agent turn %d/%d", turn + 1, MAX_AGENT_TURNS)

        response = retry_gemini(
            client.models.generate_content,
            model=MODEL,
            contents=history,
            config=types.GenerateContentConfig(tools=gemini_tools),
        )

        candidate = response.candidates[0]
        history.append(candidate.content)

        # Check for function calls.
        function_calls = response.function_calls
        if not function_calls:
            # Gemini is done — extract final text.
            text_parts = [p.text for p in candidate.content.parts if hasattr(p, "text") and p.text]
            summary = "\n".join(text_parts) or "Agent completed."
            log.info("Agent finished after %d turns.", turn + 1)
            return summary

        # Execute each function call and collect responses.
        response_parts = []
        for fc in function_calls:
            func = tools_dict.get(fc.name)
            if func:
                try:
                    coerced = _coerce_args(func, dict(fc.args))
                    result = func(**coerced)
                except Exception as exc:
                    result = f"Error: {exc}"
                    log.warning("Tool %s failed: %s", fc.name, exc)
            else:
                result = f"Unknown tool: {fc.name}"

            log.debug("  %s(%s) → %s", fc.name, dict(fc.args), result[:120])
            if on_progress:
                on_progress(fc.name, dict(fc.args), str(result))

            response_parts.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response={"result": str(result)},
                )
            )

        history.append(types.Content(role="tool", parts=response_parts))

    log.warning("Agent hit MAX_AGENT_TURNS (%d).", MAX_AGENT_TURNS)
    return "Agent reached maximum turns without completing."
