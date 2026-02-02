"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_config_status(client):
    """Test config status endpoint."""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "sandbox_mode" in data
    assert "api_host" in data


def test_documentation(client):
    """Test documentation endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200
    # /docs returns HTML, not JSON
    assert "swagger" in response.text.lower() or "html" in response.text.lower()
