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


@app.get("/auth/status")
async def auth_status():
    """
    Check authentication status.
    
    Returns whether tokens are valid and when they expire.
    """
    if not oauth_manager.is_authenticated():
        return {
            "authenticated": False,
            "message": "Not authenticated. Call /oauth/request-token to start.",
        }
    
    # Check if tokens can be used
    can_use = oauth_manager.ensure_authenticated()
    
    return {
        "authenticated": can_use,
        "token_date": oauth_manager.token_date,
        "last_used": oauth_manager.last_used.isoformat() if oauth_manager.last_used else None,
        "message": "Ready" if can_use else "Tokens expired, re-authentication required",
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
        if not oauth_manager.ensure_authenticated():
            return {
                "status": "error",
                "error": "Not authenticated. Call /oauth/request-token first.",
            }
        
        logger.info("Fetching accounts from E*TRADE")
        
        # Use authenticated session directly
        if settings.etrade_sandbox:
            url = "https://apisb.etrade.com/v1/accounts/list"
        else:
            url = "https://api.etrade.com/v1/accounts/list"
        
        response = oauth_manager.session.get(url)
        response.raise_for_status()
        
        logger.info(f"Got accounts response")
        
        return {
            "status": "success",
            "accounts": response.text,
        }
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@app.get("/accounts/{account_id_key}/portfolio")
async def get_portfolio(account_id_key: str):
    """
    Get portfolio positions for a specific account.
    
    Args:
        account_id_key: The accountIdKey from /accounts endpoint
    
    Returns: List of positions with symbol, quantity, market value, gain/loss
    """
    try:
        if not oauth_manager.ensure_authenticated():
            return {
                "status": "error",
                "error": "Not authenticated. Call /oauth/request-token first.",
            }
        
        logger.info(f"Fetching portfolio for account: {account_id_key}")
        
        # Build URL for E*TRADE portfolio API
        if settings.etrade_sandbox:
            url = f"https://apisb.etrade.com/v1/accounts/{account_id_key}/portfolio"
        else:
            url = f"https://api.etrade.com/v1/accounts/{account_id_key}/portfolio"
        
        # Use authenticated session
        response = oauth_manager.session.get(url)
        response.raise_for_status()
        
        logger.info(f"Got portfolio response")
        
        return {
            "status": "success",
            "portfolio": response.text,
        }
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@app.get("/portfolios")
async def get_all_portfolios():
    """
    Get portfolios for ALL accounts.
    
    Fetches account list, then retrieves portfolio for each account.
    Returns combined results.
    """
    import xml.etree.ElementTree as ET
    
    try:
        if not oauth_manager.ensure_authenticated():
            return {
                "status": "error",
                "error": "Not authenticated. Call /oauth/request-token first.",
            }
        
        # Step 1: Get all accounts
        logger.info("Fetching all accounts...")
        if settings.etrade_sandbox:
            accounts_url = "https://apisb.etrade.com/v1/accounts/list"
            base_url = "https://apisb.etrade.com/v1"
        else:
            accounts_url = "https://api.etrade.com/v1/accounts/list"
            base_url = "https://api.etrade.com/v1"
        
        accounts_response = oauth_manager.session.get(accounts_url)
        accounts_response.raise_for_status()
        
        # Parse accounts XML to get accountIdKeys
        root = ET.fromstring(accounts_response.text)
        accounts = []
        for account in root.findall('.//Account'):
            account_id_key = account.find('accountIdKey').text
            account_desc = account.find('accountDesc').text
            account_type = account.find('accountType').text
            accounts.append({
                "accountIdKey": account_id_key,
                "accountDesc": account_desc,
                "accountType": account_type,
            })
        
        logger.info(f"Found {len(accounts)} accounts")
        
        # Step 2: Get portfolio for each account
        portfolios = []
        for account in accounts:
            account_id_key = account["accountIdKey"]
            logger.info(f"Fetching portfolio for {account['accountDesc']}...")
            
            portfolio_url = f"{base_url}/accounts/{account_id_key}/portfolio"
            portfolio_response = oauth_manager.session.get(portfolio_url)
            
            if portfolio_response.status_code == 200:
                portfolios.append({
                    "account": account,
                    "portfolio": portfolio_response.text,
                })
            else:
                portfolios.append({
                    "account": account,
                    "portfolio": None,
                    "error": f"Status {portfolio_response.status_code}",
                })
        
        return {
            "status": "success",
            "account_count": len(accounts),
            "portfolios": portfolios,
        }
    except Exception as e:
        logger.error(f"Error fetching portfolios: {e}")
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
