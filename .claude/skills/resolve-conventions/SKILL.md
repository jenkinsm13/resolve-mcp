---
name: resolve-conventions
description: Project conventions and patterns for resolve-mcp development
user-invocable: false
---

# resolve-mcp Conventions

## Tool Module Pattern

Every tool function follows this structure:

```python
from .config import mcp
from .resolve import get_resolve, _boilerplate

@mcp.tool
def resolve_<object>_<action>(param: type) -> str:
    """Docstring describes what the tool does.

    Explains parameters and return value.
    """
    resolve, project, media_pool, timeline = _boilerplate()
    # ... Resolve API calls ...
    return "Success message"
```

## Naming Convention

- All tool functions: `resolve_<object>_<action>` (e.g., `resolve_list_projects`, `resolve_add_marker_at`)
- All tool modules: `<category>_tools.py` (e.g., `project_tools.py`, `color_tools.py`)

## Imports

- Always use **relative imports**: `from .config import mcp`, `from .resolve import get_resolve`
- Never use absolute `resolve_mcp.` imports

## Error Handling

- Use `@safe_resolve_call` decorator from `errors.py` for tools that call Resolve API
- For tools that don't use `_boilerplate()`, check `get_resolve()` returns non-None
- Return error strings (not exceptions) — MCP tools communicate via return values

## Gemini AI Tools

- Check `if client is None` before any Gemini call
- Import `from google.genai import types` inside the function body, not at module level
- Return a clear error message when Gemini is unavailable

## Adding a New Tool Module

1. Create `resolve_mcp/<name>_tools.py`
2. Add `from . import <name>_tools  # noqa: F401` to `__init__.py`
3. Follow the tool module pattern above
