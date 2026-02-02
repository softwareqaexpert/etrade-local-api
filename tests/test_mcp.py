"""Tests for MCP server."""

import pytest


def test_mcp_server_import():
    """Test that MCP server can be imported."""
    try:
        from mcp_server import server
        assert server is not None
    except ImportError as e:
        pytest.fail(f"Failed to import MCP server: {e}")


def test_mcp_server_has_tools():
    """Test that MCP server has tools defined."""
    from mcp_server.server import server
    
    # FastMCP servers have tools attribute
    assert hasattr(server, "tools") or hasattr(server, "_tools")
