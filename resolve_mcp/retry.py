"""
Retry helper for transient Gemini API errors (overload, rate-limit, quota).
"""

import time

from .config import log

_RETRIABLE_STRINGS = {"overloaded", "resource exhausted", "rate limit", "503", "429", "quota"}


def _is_retriable(exc: Exception) -> bool:
    """Return True if the exception looks like a transient Gemini error."""
    msg = str(exc).lower()
    return any(s in msg for s in _RETRIABLE_STRINGS)


def retry_gemini(fn, *args, max_retries: int = 5, base_delay: float = 5.0, **kwargs):
    """Call *fn* with retries on transient Gemini errors.

    Uses exponential backoff: 5s, 10s, 20s, 40s, 80s.
    Non-retriable exceptions propagate immediately.
    """
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries and _is_retriable(exc):
                delay = base_delay * (2 ** attempt)
                log.warning(
                    "Gemini error (attempt %d/%d), retrying in %.0fs: %s",
                    attempt + 1, max_retries + 1, delay, exc,
                )
                time.sleep(delay)
            else:
                raise
    raise last_exc  # unreachable, but keeps type checkers happy
