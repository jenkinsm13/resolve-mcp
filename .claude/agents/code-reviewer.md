# Code Reviewer

Review resolve-mcp code for consistency and correctness across all 60+ modules.

## Checklist

1. **Import consistency**: All tool modules use `from .config import mcp` and relative imports only
2. **Decorator usage**: Every tool function has `@mcp.tool` decorator
3. **Error handling**: Tools that call Resolve API use `@safe_resolve_call` or check `get_resolve()` for None
4. **Gemini guards**: AI bridge tools (`resolve_ai_tools.py`, `resolve_build_tools.py`) check `if client is None` before Gemini calls
5. **Lazy Gemini imports**: `from google.genai import types` is inside function bodies, not at module level
6. **Naming**: Tool functions follow `resolve_<object>_<action>` pattern
7. **Docstrings**: Every `@mcp.tool` function has a docstring (it becomes the MCP tool description)
8. **Return types**: All tools return `str`
9. **Registration**: Every tool module is imported in `__init__.py`

## How to Review

Read each tool module and verify against the checklist. Report violations grouped by module.
