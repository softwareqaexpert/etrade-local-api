"""FastAPI application for E*TRADE Local API."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.oauth import oauth_manager
from api.etrade_client import etrade_client

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="E*TRADE Local API",
    description="Local REST API wrapper for E*TRADE with MCP integration",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "etrade-local-api",
        "version": "0.1.0",
    }


@app.get("/config")
async def config_status():
    """Get current configuration status."""
    return {
        "sandbox_mode": settings.etrade_sandbox,
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "mcp_enabled": settings.mcp_enabled,
        "etrade_base_url": settings.etrade_base_url,
    }


@app.get("/docs")
async def documentation():
    """API documentation endpoint."""
    return {
        "swagger_ui": "/docs",
        "openapi_schema": "/openapi.json",
        "redoc": "/redoc",
    }


@app.get("/oauth/request-token")
async def oauth_request_token():
    """
    Step 1 of OAuth flow: Get request token.
    
    Returns authorization URL for user to visit.
    """
    try:
        token_data = oauth_manager.get_request_token()
        return {
            "oauth_token": token_data["oauth_token"],
            "oauth_token_secret": token_data["oauth_token_secret"],
            "authorization_url": token_data["authorization_url"],
            "status": "success",
        }
    except Exception as e:
        logger.error(f"OAuth request token error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@app.get("/oauth/callback")
async def oauth_callback(oauth_token: str, oauth_verifier: str):
    """
    Step 2 of OAuth flow: Handle callback from E*TRADE authorization.
    
    E*TRADE redirects here with oauth_token and oauth_verifier.
    We exchange the verifier for an access token.
    """
    try:
        if not oauth_verifier:
            return {
                "status": "error",
                "error": "oauth_verifier is required",
            }
        
        logger.info(f"OAuth callback received with verifier: {oauth_verifier}")
        
        # Set the verifier
        oauth_manager.set_oauth_verifier(oauth_verifier)
        
        # Exchange for access token
        access_token_data = oauth_manager.get_access_token()
        
        return {
            "status": "success",
            "message": "OAuth authentication complete",
            "oauth_token": access_token_data["oauth_token"],
            "oauth_token_secret": access_token_data["oauth_token_secret"],
        }
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@app.get("/accounts")
async def get_accounts():
    """
    Get list of accounts for authenticated user.
    
    Requires: Valid OAuth access token
    Returns: List of accounts with IDs and balances
    """
    try:
        if not oauth_manager.is_authenticated():
            return {
                "status": "error",
                "error": "Not authenticated. Call /oauth/request-token first.",
            }
        
        logger.info("Fetching accounts from E*TRADE")
        
        # Call E*TRADE Accounts API to get list
        accounts_list = etrade_client.accounts.get_account_list()
        
        logger.info(f"Got accounts response")
        
        return {
            "status": "success",
            "accounts": accounts_list,
        }
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
