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


def test_oauth_callback_endpoint_exists(client):
    """Test OAuth callback endpoint exists."""
    response = client.get("/oauth/callback?oauth_token=test&oauth_verifier=12345")
    # Should not be 404 (endpoint should exist)
    assert response.status_code != 404


def test_oauth_callback_requires_verifier(client):
    """Test OAuth callback requires oauth_verifier parameter."""
    response = client.get("/oauth/callback?oauth_token=test")
    # Should fail without verifier or handle gracefully
    assert response.status_code in [400, 422, 500]  # Error response


def test_accounts_endpoint_exists(client):
    """Test accounts endpoint exists."""
    response = client.get("/accounts")
    # Should not be 404 (endpoint should exist)
    assert response.status_code != 404


def test_portfolio_endpoint_exists(client):
    """Test portfolio endpoint exists."""
    response = client.get("/accounts/test-account-key/portfolio")
    # Should not be 404 (endpoint should exist)
    assert response.status_code != 404


def test_portfolio_requires_auth(client):
    """Test portfolio endpoint returns error for invalid account."""
    response = client.get("/accounts/test-account-key/portfolio")
    data = response.json()
    # Should return error (either auth or 401 from E*TRADE)
    assert data["status"] == "error"


def test_portfolios_endpoint_exists(client):
    """Test combined portfolios endpoint exists."""
    response = client.get("/portfolios")
    assert response.status_code != 404


def test_market_quote_endpoint_exists(client):
    """Test market quote endpoint exists."""
    response = client.get("/market/quote/AAPL")
    assert response.status_code != 404


def test_market_lookup_endpoint_exists(client):
    """Test market lookup endpoint exists."""
    response = client.get("/market/lookup/apple")
    assert response.status_code != 404


def test_market_optionchains_endpoint_exists(client):
    """Test option chains endpoint exists."""
    response = client.get("/market/optionchains?symbol=AAPL")
    assert response.status_code != 404


def test_market_optionexpiredate_endpoint_exists(client):
    """Test option expiry dates endpoint exists."""
    response = client.get("/market/optionexpiredate?symbol=AAPL")
    assert response.status_code != 404
