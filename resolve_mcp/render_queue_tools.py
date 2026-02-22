"""Render queue tools: add/start/stop/status/list/delete jobs."""

import json

from .config import mcp
from .resolve import _boilerplate


@mcp.tool
def resolve_add_render_job() -> str:
    """Add the current render settings as a job to the render queue.

    Configure settings first with resolve_set_render_settings() or
    resolve_load_render_preset().
    """
    _, project, _ = _boilerplate()
    job_id = project.AddRenderJob()
    return (
        f"Render job added (ID: {job_id})." if job_id else "Failed to add render job. Check render settings are valid."
    )


@mcp.tool
def resolve_start_render(job_ids: str = "") -> str:
    """Start rendering queued jobs.

    *job_ids*: comma-separated job IDs to render. If empty, renders all queued jobs.
    """
    _, project, _ = _boilerplate()
    if job_ids:
        ids = [x.strip() for x in job_ids.split(",") if x.strip()]
        result = project.StartRendering(ids)
    else:
        result = project.StartRendering()
    return "Rendering started." if result else "Failed to start rendering."


@mcp.tool
def resolve_stop_render() -> str:
    """Stop the current render in progress."""
    _, project, _ = _boilerplate()
    project.StopRendering()
    return "Render stop requested."


@mcp.tool
def resolve_get_render_status(job_id: str) -> str:
    """Check the status of a specific render job.

    Returns completion percentage, status, and time remaining.
    """
    _, project, _ = _boilerplate()
    status = project.GetRenderJobStatus(job_id)
    if not status:
        return f"No status for job '{job_id}'."
    if isinstance(status, dict):
        return json.dumps(status, indent=2, default=str)
    return str(status)


@mcp.tool
def resolve_list_render_jobs() -> str:
    """List all jobs in the render queue with their status."""
    _, project, _ = _boilerplate()
    jobs = project.GetRenderJobList()
    if not jobs:
        return "Render queue is empty."

    lines = [f"{len(jobs)} render job(s):"]
    for job in jobs:
        jid = job.get("JobId", "?")
        name = job.get("RenderJobName", job.get("TimelineName", "?"))
        status = job.get("JobStatus", "?")
        pct = job.get("CompletionPercentage", "?")
        target = job.get("TargetDir", "?")
        lines.append(f"  [{jid}] {name} — {status} ({pct}%) → {target}")
    return "\n".join(lines)


@mcp.tool
def resolve_delete_render_job(job_id: str) -> str:
    """Remove a render job from the queue."""
    _, project, _ = _boilerplate()
    result = project.DeleteRenderJob(job_id)
    return f"Render job '{job_id}' deleted." if result else f"Failed to delete render job '{job_id}'."


@mcp.tool
def resolve_delete_all_render_jobs() -> str:
    """Clear the entire render queue."""
    _, project, _ = _boilerplate()
    result = project.DeleteAllRenderJobs()
    return "All render jobs deleted." if result else "Failed to clear render queue."


@mcp.tool
def resolve_is_rendering() -> str:
    """Check if Resolve is currently rendering."""
    _, project, _ = _boilerplate()
    rendering = project.IsRenderingInProgress()
    return f"Rendering in progress: {bool(rendering)}"
