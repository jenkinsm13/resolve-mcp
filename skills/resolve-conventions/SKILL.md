---
name: resolve-conventions
description: Project conventions and patterns for resolve-mcp development. Explains tool registration, error handling, module organization, and naming rules.
user-invocable: false
---

# resolve-mcp Conventions

This skill provides Claude with the project conventions for the resolve-mcp codebase. It is automatically invoked when Claude needs to write or review code in this project.

## Tool Registration Pattern

Every tool follows this exact structure:

```python
from .config import mcp
from .resolve import get_resolve, _boilerplate


@mcp.tool
def resolve_do_something(param: str) -> str:
    """One-line description of what this tool does."""
    resolve, project, media_pool, timeline = _boilerplate()
    # ... implementation ...
    return "Success: description of what happened"
```

### Rules

1. **All tool names start with `resolve_`** — this is the MCP namespace prefix
2. **All tools return `str`** — never return dict, list, or None
3. **Use `_boilerplate()`** for tools that need project/timeline access
4. **Use `get_resolve()`** only for tools that work without a project open
5. **Docstrings are required** — they become the tool description in MCP
6. **One tool per function** — no combining multiple operations

## Error Handling

```python
from .errors import safe_resolve_call

@mcp.tool
@safe_resolve_call
def resolve_my_tool() -> str:
    ...
```

The `@safe_resolve_call` decorator catches all exceptions and returns clean MCP error strings. Custom exceptions:

| Exception | When |
|-----------|------|
| `ResolveNotRunning` | `get_resolve()` returns None |
| `ProjectNotOpen` | No project loaded |
| `TimelineNotFound` | No current timeline |
| `BinNotFound` | Requested bin doesn't exist |
| `ClipNotFound` | Clip index out of range |
| `ItemNotFound` | Timeline item not found |
| `StudioRequired` | Feature needs DaVinci Resolve Studio |

## Module Organization

- **One domain per module** — don't mix timeline tools with color tools
- **Module name pattern**: `{domain}_tools.py` (e.g., `color_tools.py`, `marker_tools.py`)
- **New modules must be imported in `__init__.py`** with the noqa comment:
  ```python
  from . import my_new_tools  # noqa: F401  — description (N tools)
  ```

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Tool function | `resolve_{verb}_{noun}` | `resolve_get_timeline_info` |
| Module file | `{domain}_tools.py` | `color_tools.py` |
| Agent file | `{role}.md` (kebab-case) | `colorist.md` |
| Skill directory | `{action}` (kebab-case) | `bump-publish` |

## Import Style

- **Relative imports only** inside `resolve_mcp/` package
- `from .config import mcp` — never absolute
- Heavy imports (google.genai) go **inside** functions, not at module level

## Type Annotations

- All tool parameters must have type hints
- All tools return `-> str`
- Use `int` for indices (1-based for user-facing, 0-based internally)
- Use `str` for Resolve enums (colors, track types, etc.)

## Testing

- Tests go in `tests/` directory
- Test files: `test_{module}.py`
- Resolve API is not available in CI — tests should focus on:
  - Import validation (all modules load without error)
  - Parameter validation logic
  - String formatting / return value shapes
  - Mock-based integration tests where appropriate

## Linting & Formatting

- **Ruff** for linting and formatting (config in `pyproject.toml`)
- Line length: 120
- Quote style: double
- Auto-fixed on save via PostToolUse hook
