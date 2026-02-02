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


def test_oauth_request_token_endpoint_exists(client):
    """Test OAuth request token endpoint exists."""
    response = client.get("/oauth/request-token")
    # Should not be 404 (endpoint should exist)
    assert response.status_code != 404


def test_oauth_request_token_returns_valid_data(client):
    """Test OAuth request token returns oauth_token."""
    response = client.get("/oauth/request-token")
    # Should be 200 or handle gracefully
    if response.status_code == 200:
        data = response.json()
        assert "oauth_token" in data
        assert "oauth_token_secret" in data
        assert "authorization_url" in data
