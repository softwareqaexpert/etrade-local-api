"""Tests for MCP server."""

import pytest
import os
import sys


def test_mcp_server_module_exists():
    """Test that mcp_server module can be imported."""
    try:
        import mcp_server
        assert mcp_server is not None
    except ImportError:
        pytest.fail("Could not import mcp_server module")


def test_mcp_server_file_exists():
    """Test that MCP server.py file exists."""
    # Get path to mcp_server directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    server_file = os.path.join(project_root, 'mcp_server', 'server.py')
    
    assert os.path.exists(server_file), f"MCP server file not found at {server_file}"
