"""
Standardised error handling for Resolve MCP tools.

Wraps Resolve API calls to produce consistent, actionable error messages
instead of bare "Failed." strings.
"""

import functools
import logging

log = logging.getLogger(__name__)


class ResolveError(Exception):
    """Base error for Resolve API failures."""


class ResolveNotRunning(ResolveError):
    """Resolve is not running or the scripting API is unreachable."""


class ProjectNotOpen(ResolveError):
    """No project is currently open in Resolve."""


class TimelineNotFound(ResolveError):
    """The requested timeline does not exist or no timeline is active."""


class BinNotFound(ResolveError):
    """The requested media pool bin does not exist."""


class ClipNotFound(ResolveError):
    """The requested clip does not exist in the media pool."""


class ItemNotFound(ResolveError):
    """The timeline item at the given track/index does not exist."""


class StudioRequired(ResolveError):
    """The feature requires DaVinci Resolve Studio."""


def safe_resolve_call(func):
    """Decorator: catch exceptions from Resolve API and return error strings.

    Converts Python exceptions into MCP-friendly error strings so the
    LLM gets actionable feedback instead of a traceback.  ValueError
    from _boilerplate() is passed through as-is (already formatted).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as exc:
            # From _boilerplate() — already a clean error message.
            return str(exc)
        except ResolveError as exc:
            return f"Error: {exc}"
        except (AttributeError, TypeError) as exc:
            log.warning("Resolve API error in %s: %s", func.__name__, exc)
            return (
                f"Error: Resolve API returned an unexpected result in "
                f"{func.__name__}. This may indicate an API version mismatch "
                f"or that the required object is not available. Detail: {exc}"
            )
        except Exception as exc:
            log.exception("Unexpected error in %s", func.__name__)
            return f"Error: Unexpected failure in {func.__name__}: {exc}"
    return wrapper
