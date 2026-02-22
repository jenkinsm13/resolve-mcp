"""
Project & database management MCP tools.

Covers: ProjectManager (list/load/create/export projects, DB folders),
Project settings, Resolve page navigation, and version info.
"""

import json

from .config import mcp
from .resolve import _boilerplate, get_resolve

# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool
def resolve_list_projects() -> str:
    """List all projects in the current database folder.

    Returns project names as a newline-separated list.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."
    pm = resolve.GetProjectManager()

    projects = pm.GetProjectListInCurrentFolder()
    if not projects:
        return "No projects found in current database folder."
    return f"{len(projects)} project(s):\n" + "\n".join(f"  • {p}" for p in projects)


@mcp.tool
def resolve_load_project(project_name: str) -> str:
    """Open a project by name.  Closes the current project first.

    Returns success/failure message.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."
    pm = resolve.GetProjectManager()

    # Close current project first (required by API).
    current = pm.GetCurrentProject()
    if current and current.GetName() == project_name:
        return f"Project '{project_name}' is already open."

    if current:
        pm.CloseProject(current)

    project = pm.LoadProject(project_name)
    if project:
        return f"Opened project '{project_name}'."
    return f"Failed to open project '{project_name}'. Check the name is correct."


@mcp.tool
def resolve_save_project() -> str:
    """Save the current project."""
    _, project, _ = _boilerplate()
    result = project.SaveProject()
    if result:
        return f"Project '{project.GetName()}' saved."
    return "Save failed — project may be read-only or on a locked database."


@mcp.tool
def resolve_create_project(project_name: str) -> str:
    """Create a new project with the given name and open it."""
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."
    pm = resolve.GetProjectManager()

    project = pm.CreateProject(project_name)
    if project:
        return f"Created and opened project '{project_name}'."
    return f"Failed to create project '{project_name}'. Name may already exist."


@mcp.tool
def resolve_rename_project(new_name: str) -> str:
    """Rename the current project.

    Returns success/failure message.
    """
    _, project, _ = _boilerplate()
    old_name = project.GetName()
    result = project.SetName(new_name)
    if result:
        return f"Renamed project '{old_name}' → '{new_name}'."
    return f"Failed to rename project. Name '{new_name}' may already exist or be invalid."


@mcp.tool
def resolve_export_project(project_name: str, file_path: str, with_stills_and_luts: bool = True) -> str:
    """Export a project to a .drp file at the given path.

    Set *with_stills_and_luts* to False to exclude gallery stills and LUTs.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."
    pm = resolve.GetProjectManager()

    result = pm.ExportProject(project_name, file_path, with_stills_and_luts)
    if result:
        return f"Exported '{project_name}' → {file_path}"
    return f"Export failed for '{project_name}'. Check name and path."


@mcp.tool
def resolve_get_project_settings(setting_name: str = "") -> str:
    """Read project settings.

    If *setting_name* is provided, returns that single setting's value.
    If omitted, returns ALL settings as formatted JSON.

    Common setting names: timelineFrameRate, timelineResolutionWidth,
    timelineResolutionHeight, timelinePlaybackFrameRate, videoCaptureCodec,
    audioCaptureNumChannels, colorScienceMode, superScale.
    """
    _, project, _ = _boilerplate()

    if setting_name:
        value = project.GetSetting(setting_name)
        if value is None or value == "":
            return f"Setting '{setting_name}' not found or empty."
        return f"{setting_name} = {value}"

    # Return all settings.
    all_settings = project.GetSetting()
    if isinstance(all_settings, dict):
        return json.dumps(all_settings, indent=2)
    return str(all_settings)


@mcp.tool
def resolve_set_project_setting(setting_name: str, value: str) -> str:
    """Write a project setting.

    *value* is always passed as a string — Resolve handles type coercion.
    Returns success/failure message.

    Common examples:
      timelineFrameRate → "24", "29.97", "59.94"
      timelineResolutionWidth → "3840"
      timelineResolutionHeight → "2160"
    """
    _, project, _ = _boilerplate()

    result = project.SetSetting(setting_name, value)
    if result:
        return f"Set {setting_name} = {value}"
    return f"Failed to set {setting_name}. Check that the value is valid and the project allows changes."


@mcp.tool
def resolve_switch_page(page_name: str) -> str:
    """Navigate Resolve to a specific page.

    Valid page names: media, cut, edit, fusion, color, fairlight, deliver.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."

    valid = {"media", "cut", "edit", "fusion", "color", "fairlight", "deliver"}
    page_name = page_name.lower().strip()
    if page_name not in valid:
        return f"Invalid page '{page_name}'. Must be one of: {', '.join(sorted(valid))}"

    result = resolve.OpenPage(page_name)
    if result:
        return f"Switched to {page_name} page."
    return f"Failed to switch to {page_name} page."


@mcp.tool
def resolve_get_version() -> str:
    """Return the DaVinci Resolve version string and current page."""
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."

    version = resolve.GetVersionString() or "unknown"
    page = resolve.GetCurrentPage() or "unknown"
    return f"DaVinci Resolve {version} — current page: {page}"


@mcp.tool
def resolve_list_database_folders() -> str:
    """List subfolders in the current project database.

    Useful for navigating project databases before loading a project.
    Returns the current folder name and its subfolders.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."
    pm = resolve.GetProjectManager()

    current = pm.GetCurrentFolder()
    subs = pm.GetFolderListInCurrentFolder()
    parts = [f"Current DB folder: {current or 'Root'}"]
    if subs:
        parts.append("Subfolders:")
        for s in subs:
            parts.append(f"  • {s}")
    else:
        parts.append("No subfolders.")
    return "\n".join(parts)


@mcp.tool
def resolve_navigate_database_folder(folder_name: str) -> str:
    """Navigate into a subfolder of the current project database, or use '..'
    to go up one level.

    Use resolve_list_database_folders() to see available subfolders first.
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: DaVinci Resolve is not running."
    pm = resolve.GetProjectManager()

    if folder_name == "..":
        result = pm.GotoParentFolder()
        if result:
            return "Moved up one folder."
        return "Already at root or navigation failed."

    result = pm.OpenFolder(folder_name)
    if result:
        return f"Opened database folder '{folder_name}'."
    return f"Failed to open folder '{folder_name}'. Check the name."
