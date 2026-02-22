"""
ProjectManager extras — archive, delete, database switching, folder ops,
import/restore projects.
"""

from .config import mcp
from .errors import safe_resolve_call
from .resolve import get_resolve


def _pm():
    """Return ProjectManager or raise."""
    resolve = get_resolve()
    if not resolve:
        raise ValueError("Error: DaVinci Resolve is not running.")
    return resolve.GetProjectManager()


# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_archive_project(project_name: str, archive_path: str, with_stills_and_luts: bool = True) -> str:
    """Archive a project to a .dra file.

    Args:
        project_name (str): Name of the project to archive.
        archive_path (str): Destination path for the .dra archive file.
        with_stills_and_luts (bool): Include stills and LUTs in the archive. Defaults to True.
    """
    pm = _pm()
    r = pm.ArchiveProject(project_name, archive_path, with_stills_and_luts)
    return f"Archived '{project_name}' → {archive_path}" if r else f"Archive failed for '{project_name}'."


@mcp.tool
@safe_resolve_call
def resolve_delete_project(project_name: str) -> str:
    """Permanently delete a project from the current database folder.

    WARNING: This cannot be undone.

    Args:
        project_name (str): Name of the project to delete.
    """
    pm = _pm()
    r = pm.DeleteProject(project_name)
    return f"Deleted project '{project_name}'." if r else f"Delete failed for '{project_name}'."


@mcp.tool
@safe_resolve_call
def resolve_import_project(file_path: str, project_name: str = "") -> str:
    """Import a project from a .drp file.

    If *project_name* is given the imported project is renamed.

    Args:
        file_path (str): Path to the .drp project file to import.
        project_name (str): Optional new name for the imported project. If omitted, original name is used.
    """
    pm = _pm()
    if project_name:
        r = pm.ImportProject(file_path, project_name)
    else:
        r = pm.ImportProject(file_path)
    return f"Imported project from {file_path}" if r else f"Import failed for {file_path}."


@mcp.tool
@safe_resolve_call
def resolve_restore_project(archive_path: str, project_name: str = "") -> str:
    """Restore a project from a .dra archive.

    Args:
        archive_path (str): Path to the .dra archive file to restore from.
        project_name (str): Optional new name for the restored project. If omitted, original name is used.
    """
    pm = _pm()
    if project_name:
        r = pm.RestoreProject(archive_path, project_name)
    else:
        r = pm.RestoreProject(archive_path)
    return f"Restored project from {archive_path}" if r else f"Restore failed for {archive_path}."


@mcp.tool
@safe_resolve_call
def resolve_create_db_folder(folder_name: str) -> str:
    """Create a folder in the current project database.

    Args:
        folder_name (str): Name of the folder to create.
    """
    pm = _pm()
    r = pm.CreateFolder(folder_name)
    return f"Created DB folder '{folder_name}'." if r else f"Failed to create DB folder '{folder_name}'."


@mcp.tool
@safe_resolve_call
def resolve_delete_db_folder(folder_name: str) -> str:
    """Delete a folder from the current project database.

    WARNING: Deletes all projects inside the folder.

    Args:
        folder_name (str): Name of the folder to delete.
    """
    pm = _pm()
    r = pm.DeleteFolder(folder_name)
    return f"Deleted DB folder '{folder_name}'." if r else f"Failed to delete DB folder '{folder_name}'."


@mcp.tool
@safe_resolve_call
def resolve_goto_root_folder() -> str:
    """Navigate to the root of the project database.

    Args: None
    """
    pm = _pm()
    r = pm.GotoRootFolder()
    return "Navigated to root folder." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_goto_home_folder() -> str:
    """Navigate to the home folder of the project database.

    Args: None
    """
    pm = _pm()
    r = pm.GotoHomeFolder()
    return "Navigated to home folder." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_get_database_list() -> str:
    """List all available project databases.

    Args: None
    """
    pm = _pm()
    dbs = pm.GetDatabaseList()
    if not dbs:
        return "No databases found."
    lines = [f"{len(dbs)} database(s):"]
    for db in dbs:
        if isinstance(db, dict):
            lines.append(f"  • {db.get('DbName', db)}")
        else:
            lines.append(f"  • {db}")
    return "\n".join(lines)


@mcp.tool
@safe_resolve_call
def resolve_set_current_database(db_info: str) -> str:
    """Switch to a different project database.

    *db_info* is a JSON string with keys matching the database dict
    returned by resolve_get_database_list (typically DbName, DbType, IpAddress).

    Args:
        db_info (str): JSON string with database connection info, or plain database name.
    """
    import json

    pm = _pm()
    try:
        info = json.loads(db_info)
    except json.JSONDecodeError:
        # Treat as plain DB name
        info = {"DbName": db_info}
    r = pm.SetCurrentDatabase(info)
    return "Switched database." if r else "Failed to switch database."
