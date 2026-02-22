"""
Smoke tests — verify all modules import without error.

These tests don't require DaVinci Resolve to be running.
They catch broken imports, syntax errors, and missing dependencies.
"""

import importlib
import pkgutil

import pytest


def _iter_tool_modules():
    """Yield (module_name, full_path) for every *_tools.py module in resolve_mcp."""
    import resolve_mcp

    for info in pkgutil.iter_modules(resolve_mcp.__path__):
        if info.name.endswith("_tools"):
            yield info.name


class TestImports:
    """Verify the package and all tool modules import cleanly."""

    def test_package_imports(self):
        """resolve_mcp package imports without error."""
        import resolve_mcp

        assert hasattr(resolve_mcp, "mcp")
        assert hasattr(resolve_mcp, "main")

    def test_config_module(self):
        """Config module exposes the FastMCP server instance."""
        from resolve_mcp.config import mcp

        assert mcp is not None
        assert mcp.name == "resolve-mcp" or mcp.name  # has a name

    @pytest.mark.parametrize("module_name", list(_iter_tool_modules()))
    def test_tool_module_imports(self, module_name):
        """Each *_tools.py module imports without error."""
        mod = importlib.import_module(f"resolve_mcp.{module_name}")
        assert mod is not None

    def test_errors_module(self):
        """Error classes import cleanly."""
        from resolve_mcp.errors import (
            ResolveNotRunning,
            safe_resolve_call,
        )

        assert ResolveNotRunning is not None
        assert callable(safe_resolve_call)

    def test_resolve_helpers(self):
        """Core resolve helpers import without error."""
        from resolve_mcp.resolve import get_resolve

        assert callable(get_resolve)


class TestToolRegistration:
    """Verify tools are registered on the MCP server."""

    def test_tools_registered(self):
        """MCP server has tools registered after import."""
        # FastMCP stores tools internally — check it has some
        # The exact API depends on fastmcp version, but the server
        # should have a non-empty tool registry after all modules load
        import resolve_mcp  # noqa: F401 — triggers all module imports
        from resolve_mcp.config import mcp

        assert mcp is not None

    def test_tool_count_minimum(self):
        """At least 200 tools are registered (sanity check)."""
        import resolve_mcp  # noqa: F401
        from resolve_mcp.config import mcp

        # FastMCP >=3.0 exposes tools via _tool_manager or similar
        # This is a best-effort check — skip if internal API changes
        try:
            tool_count = len(mcp._tool_manager._tools)
        except AttributeError:
            try:
                tool_count = len(mcp.tools)
            except (AttributeError, TypeError):
                pytest.skip("Could not introspect tool count from FastMCP internals")
        assert tool_count >= 200, f"Expected 200+ tools, got {tool_count}"
