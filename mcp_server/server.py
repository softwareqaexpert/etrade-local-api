"""FastMCP server for E*TRADE Local API integration with Claude."""

import sys
import logging
from fastmcp.server import Server

# Configure stderr logging for MCP (critical for STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)
logger = logging.getLogger(__name__)

# Create FastMCP server
server = Server("etrade-local-api")
logger.info("FastMCP server initialized")


@server.tool()
def get_accounts() -> dict:
    """Get list of accounts from E*TRADE.
    
    Returns:
        Dictionary containing account information
    """
    logger.info("Tool called: get_accounts")
    return {
        "status": "success",
        "message": "Accounts tool placeholder",
        "accounts": [],
    }


@server.tool()
def get_account_balance(account_id_key: str) -> dict:
    """Get account balance from E*TRADE.
    
    Args:
        account_id_key: The account ID key from E*TRADE
        
    Returns:
        Dictionary containing balance information
    """
    logger.info(f"Tool called: get_account_balance({account_id_key})")
    return {
        "status": "success",
        "account_id_key": account_id_key,
        "balance": 0,
    }


@server.tool()
def get_portfolio(account_id_key: str) -> dict:
    """Get portfolio positions from E*TRADE.
    
    Args:
        account_id_key: The account ID key from E*TRADE
        
    Returns:
        Dictionary containing portfolio information
    """
    logger.info(f"Tool called: get_portfolio({account_id_key})")
    return {
        "status": "success",
        "account_id_key": account_id_key,
        "positions": [],
    }


@server.tool()
def get_quote(symbols: str) -> dict:
    """Get stock quotes from E*TRADE.
    
    Args:
        symbols: Comma-separated list of stock symbols
        
    Returns:
        Dictionary containing quote information
    """
    logger.info(f"Tool called: get_quote({symbols})")
    return {
        "status": "success",
        "symbols": symbols,
        "quotes": [],
    }


def main():
    """Run the MCP server."""
    logger.info("Starting E*TRADE Local API MCP Server")
    server.run()


if __name__ == "__main__":
    main()
