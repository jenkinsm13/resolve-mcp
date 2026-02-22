"""
Convention tests — verify all tools follow resolve-mcp coding standards.

These tests enforce naming conventions, return types, and docstring requirements
without requiring DaVinci Resolve.
"""

import ast
import pkgutil
from pathlib import Path

import pytest

PACKAGE_DIR = Path(__file__).parent.parent / "resolve_mcp"

# Modules that intentionally use non-resolve_ prefixed tool names
# (resolve-assistant bridge tools use their own namespace)
NAMING_EXCEPTIONS = {"build_tools", "ingest_tools"}

# Modules that are imported indirectly (by other modules) rather than in __init__.py
# These are sub-modules, conditional imports, or resolve-assistant bridge modules
INDIRECT_IMPORT_MODULES = {
    "build_tools",
    "clip_edit_tools",
    "clip_query_tools",
    "color_clip_tools",
    "color_grade_tools",
    "ingest_tools",
    "layout_ui_tools",
    "media_pool_edit_tools",
    "media_pool_query_tools",
    "project_misc_tools",
    "render_queue_tools",
    "render_settings_tools",
    "resolve_ai_tools",
    "resolve_build_tools",
    "resolve_info_tools",
    "resolve_ingest_tools",
    "timeline_query_tools",
    "timeline_track_tools",
}


def _get_tool_modules():
    """Return list of tool module names."""
    import resolve_mcp

    return [info.name for info in pkgutil.iter_modules(resolve_mcp.__path__) if info.name.endswith("_tools")]


def _parse_tool_functions(module_name: str):
    """Parse a module's AST and yield function names decorated with @mcp.tool."""
    source_file = PACKAGE_DIR / f"{module_name}.py"
    if not source_file.exists():
        return

    tree = ast.parse(source_file.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                # Match @mcp.tool
                if (
                    isinstance(decorator, ast.Attribute)
                    and isinstance(decorator.value, ast.Name)
                    and decorator.value.id == "mcp"
                    and decorator.attr == "tool"
                ):
                    yield node


class TestNamingConventions:
    """All tool functions must start with resolve_."""

    @pytest.mark.parametrize("module_name", _get_tool_modules())
    def test_tool_names_start_with_resolve(self, module_name):
        """Every @mcp.tool function name starts with 'resolve_' (except known bridge modules)."""
        if module_name in NAMING_EXCEPTIONS:
            pytest.skip(f"{module_name} uses a different namespace (assistant bridge)")

        violations = []
        for func_node in _parse_tool_functions(module_name):
            if not func_node.name.startswith("resolve_"):
                violations.append(func_node.name)

        assert not violations, f"Tools in {module_name}.py don't start with 'resolve_': {violations}"


class TestDocstrings:
    """All tools must have docstrings."""

    @pytest.mark.parametrize("module_name", _get_tool_modules())
    def test_tools_have_docstrings(self, module_name):
        """Every @mcp.tool function has a docstring."""
        missing = []
        for func_node in _parse_tool_functions(module_name):
            docstring = ast.get_docstring(func_node)
            if not docstring or not docstring.strip():
                missing.append(func_node.name)

        assert not missing, f"Tools in {module_name}.py missing docstrings: {missing}"


class TestReturnTypes:
    """All tools must declare -> str return type."""

    @pytest.mark.parametrize("module_name", _get_tool_modules())
    def test_tools_return_str(self, module_name):
        """Every @mcp.tool function has -> str return annotation."""
        wrong_returns = []
        for func_node in _parse_tool_functions(module_name):
            if func_node.returns is None:
                wrong_returns.append(f"{func_node.name} (no annotation)")
            elif isinstance(func_node.returns, ast.Name) and func_node.returns.id != "str":
                wrong_returns.append(f"{func_node.name} (-> {func_node.returns.id})")
            elif isinstance(func_node.returns, ast.Constant) and func_node.returns.value != "str":
                wrong_returns.append(f"{func_node.name} (-> {func_node.returns.value})")

        assert not wrong_returns, f"Tools in {module_name}.py with wrong return types: {wrong_returns}"


class TestModuleImports:
    """All tool modules must be imported in __init__.py."""

    def test_all_tool_modules_imported(self):
        """Every *_tools.py file is imported in __init__.py (or is a known indirect import)."""
        init_file = PACKAGE_DIR / "__init__.py"
        init_source = init_file.read_text(encoding="utf-8")

        tool_files = sorted(PACKAGE_DIR.glob("*_tools.py"))
        unimported = []

        for tool_file in tool_files:
            module_name = tool_file.stem
            if module_name in INDIRECT_IMPORT_MODULES:
                continue  # known to be imported by other modules
            if f"import {module_name}" not in init_source:
                unimported.append(module_name)

        assert not unimported, f"Tool modules not imported in __init__.py: {unimported}"
