"""
Folder (media pool bin) object tools — transcription, export, unique IDs.

For an editor/assistant editor: folder-level transcription processes
all clips in a bin at once, essential for documentary and interview
workflows where you need searchable dialogue across hundreds of clips.
"""

from .config import mcp
from .errors import safe_resolve_call
from .resolve import _boilerplate, _find_bin

# ---------------------------------------------------------------------------


@mcp.tool
@safe_resolve_call
def resolve_folder_transcribe(bin_name: str) -> str:
    """Start audio transcription for all clips in a bin.

    Transcribes dialogue/narration so clips become searchable by
    spoken content. Essential for documentary, interview, and
    dialogue-heavy projects.

    Requires DaVinci Resolve Studio.

    Args:
        bin_name (str): Name of the media pool bin to transcribe.
    """
    _, _, mp = _boilerplate()
    folder = _find_bin(mp.GetRootFolder(), bin_name)
    if not folder:
        return f"Bin '{bin_name}' not found."
    r = folder.TranscribeAudio()
    return f"Transcription started for bin '{bin_name}'." if r else "Failed — requires Resolve Studio."


@mcp.tool
@safe_resolve_call
def resolve_folder_clear_transcription(bin_name: str) -> str:
    """Clear all transcription data from clips in a bin.

    Args:
        bin_name (str): Name of the media pool bin to clear transcriptions from.
    """
    _, _, mp = _boilerplate()
    folder = _find_bin(mp.GetRootFolder(), bin_name)
    if not folder:
        return f"Bin '{bin_name}' not found."
    r = folder.ClearTranscription()
    return f"Transcription cleared for bin '{bin_name}'." if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_folder_export(bin_name: str, file_path: str) -> str:
    """Export a bin's contents to a file.

    Useful for archiving bin structures or sharing between projects.

    Args:
        bin_name (str): Name of the media pool bin to export.
        file_path (str): Destination file path for the export.
    """
    _, _, mp = _boilerplate()
    folder = _find_bin(mp.GetRootFolder(), bin_name)
    if not folder:
        return f"Bin '{bin_name}' not found."
    r = folder.Export(file_path)
    return f"Bin '{bin_name}' exported to {file_path}" if r else "Failed."


@mcp.tool
@safe_resolve_call
def resolve_folder_get_id(bin_name: str) -> str:
    """Get the unique ID of a media pool bin.

    Args:
        bin_name (str): Name of the media pool bin.
    """
    _, _, mp = _boilerplate()
    folder = _find_bin(mp.GetRootFolder(), bin_name)
    if not folder:
        return f"Bin '{bin_name}' not found."
    uid = folder.GetUniqueId()
    return f"Bin '{bin_name}' ID: {uid}" if uid else "Could not retrieve."
