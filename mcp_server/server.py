"""FastMCP server for E*TRADE API integration."""

import sys
import logging
import json
import xml.etree.ElementTree as ET
from fastmcp import FastMCP

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from api.oauth import oauth_manager
from api.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)
logger = logging.getLogger(__name__)

# Create FastMCP server
server = FastMCP("etrade-api")
logger.info(f"E*TRADE MCP Server initialized (sandbox={settings.etrade_sandbox})")


def get_base_url():
    """Get E*TRADE API base URL based on sandbox setting."""
    if settings.etrade_sandbox:
        return "https://apisb.etrade.com/v1"
    return "https://api.etrade.com/v1"


def ensure_auth():
    """Check authentication, return error dict if not authenticated."""
    if not oauth_manager.ensure_authenticated():
        return {"status": "error", "error": "Not authenticated. Run etrade_auth_status to get auth URL."}
    return None


# =============================================================================
# Authentication Tools
# =============================================================================

@server.tool()
def etrade_auth_status() -> dict:
    """Check E*TRADE authentication status and get login URL if needed.
    
    Returns auth status. If not authenticated, returns authorization URL
    that user must visit to complete OAuth flow.
    """
    logger.info("Tool: etrade_auth_status")
    
    if oauth_manager.is_authenticated():
        return {
            "status": "authenticated",
            "sandbox": settings.etrade_sandbox,
            "token_date": str(oauth_manager.token_date),
        }
    
    # Get new request token and auth URL
    try:
        result = oauth_manager.get_request_token()
        return {
            "status": "not_authenticated",
            "authorization_url": result["authorization_url"],
            "instructions": "Visit the URL, login, and call etrade_auth_callback with the verifier code.",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@server.tool()
def etrade_auth_callback(verifier: str) -> dict:
    """Complete E*TRADE OAuth with verifier code from authorization page.
    
    Args:
        verifier: The verification code shown after authorizing on E*TRADE
    """
    logger.info(f"Tool: etrade_auth_callback")
    try:
        oauth_manager.set_oauth_verifier(verifier)
        oauth_manager.get_access_token()
        return {
            "status": "success",
            "authenticated": oauth_manager.is_authenticated(),
            "sandbox": settings.etrade_sandbox,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Account Tools
# =============================================================================

@server.tool()
def etrade_get_accounts() -> dict:
    """Get list of all E*TRADE accounts."""
    logger.info("Tool: etrade_get_accounts")
    
    auth_err = ensure_auth()
    if auth_err:
        return auth_err
    
    try:
        url = f"{get_base_url()}/accounts/list"
        response = oauth_manager.session.get(url)
        response.raise_for_status()
        
        # Parse XML to JSON
        root = ET.fromstring(response.text)
        accounts = []
        for acct in root.findall('.//Account'):
            accounts.append({
                "accountIdKey": acct.find('accountIdKey').text,
                "accountId": acct.find('accountId').text,
                "accountDesc": acct.find('accountDesc').text,
                "accountType": acct.find('accountType').text,
            })
        
        return {"status": "success", "accounts": accounts}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@server.tool()
def etrade_get_summary() -> dict:
    """Get comprehensive summary of all accounts with balances and positions.
    
    Returns each account with cash balance, portfolio value, and all positions.
    """
    logger.info("Tool: etrade_get_summary")
    
    auth_err = ensure_auth()
    if auth_err:
        return auth_err
    
    try:
        base_url = get_base_url()
        
        # Get accounts
        resp = oauth_manager.session.get(f"{base_url}/accounts/list")
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        
        accounts_data = []
        total_cash = 0
        total_portfolio = 0
        total_gain = 0
        
        for account in root.findall('.//Account'):
            acct_key = account.find('accountIdKey').text
            acct_info = {
                "accountIdKey": acct_key,
                "accountDesc": account.find('accountDesc').text,
                "accountType": account.find('accountType').text,
            }
            
            # Get balance
            bal_resp = oauth_manager.session.get(
                f"{base_url}/accounts/{acct_key}/balance",
                params={"instType": "BROKERAGE", "realTimeNAV": "true"}
            )
            cash = 0
            if bal_resp.status_code == 200:
                bal_root = ET.fromstring(bal_resp.text)
                cash_elem = bal_root.find('.//cashAvailableForInvestment')
                cash = float(cash_elem.text) if cash_elem is not None else 0
            
            # Get positions
            port_resp = oauth_manager.session.get(f"{base_url}/accounts/{acct_key}/portfolio")
            positions = []
            portfolio_value = 0
            account_gain = 0
            
            if port_resp.status_code == 200:
                port_root = ET.fromstring(port_resp.text)
                for p in port_root.findall('.//Position'):
                    symbol = p.find('.//symbol').text
                    qty = float(p.find('quantity').text)
                    price_elem = p.find('.//lastTrade')
                    price = float(price_elem.text) if price_elem is not None else 0
                    value = float(p.find('marketValue').text)
                    gain = float(p.find('totalGain').text)
                    gain_pct = float(p.find('totalGainPct').text)
                    
                    positions.append({
                        "symbol": symbol,
                        "quantity": qty,
                        "price": price,
                        "marketValue": value,
                        "gain": gain,
                        "gainPct": gain_pct,
                    })
                    portfolio_value += value
                    account_gain += gain
            
            accounts_data.append({
                "account": acct_info,
                "cash": cash,
                "portfolioValue": portfolio_value,
                "totalValue": cash + portfolio_value,
                "totalGain": account_gain,
                "positions": positions,
            })
            
            total_cash += cash
            total_portfolio += portfolio_value
            total_gain += account_gain
        
        return {
            "status": "success",
            "accounts": accounts_data,
            "totals": {
                "cash": total_cash,
                "portfolioValue": total_portfolio,
                "totalValue": total_cash + total_portfolio,
                "totalGain": total_gain,
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Market Data Tools
# =============================================================================

@server.tool()
def etrade_get_quote(symbols: str) -> dict:
    """Get stock quotes for one or more symbols.
    
    Args:
        symbols: Comma-separated symbols (e.g., "AAPL,MSFT,TSLA")
    """
    logger.info(f"Tool: etrade_get_quote({symbols})")
    
    auth_err = ensure_auth()
    if auth_err:
        return auth_err
    
    try:
        url = f"{get_base_url()}/market/quote/{symbols}"
        response = oauth_manager.session.get(url)
        response.raise_for_status()
        
        # Parse quotes
        root = ET.fromstring(response.text)
        quotes = []
        for q in root.findall('.//QuoteData'):
            all_data = q.find('.//All')
            quotes.append({
                "symbol": q.find('.//Product/symbol').text if q.find('.//Product/symbol') is not None else symbols,
                "lastTrade": float(all_data.find('lastTrade').text) if all_data.find('lastTrade') is not None else None,
                "bid": float(all_data.find('bid').text) if all_data.find('bid') is not None else None,
                "ask": float(all_data.find('ask').text) if all_data.find('ask') is not None else None,
                "changeClose": float(all_data.find('changeClose').text) if all_data.find('changeClose') is not None else None,
                "changeClosePercentage": float(all_data.find('changeClosePercentage').text) if all_data.find('changeClosePercentage') is not None else None,
            })
        
        return {"status": "success", "quotes": quotes}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@server.tool()
def etrade_lookup_symbol(search: str) -> dict:
    """Search for securities by name or partial symbol.
    
    Args:
        search: Search term (e.g., "apple", "micro")
    """
    logger.info(f"Tool: etrade_lookup_symbol({search})")
    
    auth_err = ensure_auth()
    if auth_err:
        return auth_err
    
    try:
        url = f"{get_base_url()}/market/lookup/{search}"
        response = oauth_manager.session.get(url)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        results = []
        for data in root.findall('.//Data'):
            results.append({
                "symbol": data.find('symbol').text,
                "description": data.find('description').text,
                "type": data.find('type').text,
            })
        
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Order Tools
# =============================================================================

@server.tool()
def etrade_list_orders(account_id_key: str, status: str = None) -> dict:
    """List orders for an account.
    
    Args:
        account_id_key: Account ID key from etrade_get_accounts
        status: Filter by status (OPEN, EXECUTED, CANCELLED, etc.)
    """
    logger.info(f"Tool: etrade_list_orders({account_id_key})")
    
    auth_err = ensure_auth()
    if auth_err:
        return auth_err
    
    try:
        url = f"{get_base_url()}/accounts/{account_id_key}/orders"
        params = {}
        if status:
            params["status"] = status
        
        response = oauth_manager.session.get(url, params=params)
        response.raise_for_status()
        
        # Parse orders
        root = ET.fromstring(response.text)
        orders = []
        for order in root.findall('.//Order'):
            order_detail = order.find('.//OrderDetail')
            instrument = order.find('.//Instrument')
            orders.append({
                "orderId": order.find('orderId').text,
                "orderType": order.find('orderType').text,
                "status": order_detail.find('status').text if order_detail is not None else None,
                "symbol": instrument.find('.//symbol').text if instrument is not None else None,
                "quantity": instrument.find('orderedQuantity').text if instrument is not None else None,
                "priceType": order_detail.find('priceType').text if order_detail is not None else None,
            })
        
        return {"status": "success", "orders": orders}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@server.tool()
def etrade_preview_order(
    account_id_key: str,
    symbol: str,
    action: str,
    quantity: int,
    price_type: str = "MARKET",
    limit_price: float = None,
    stop_price: float = None,
    order_term: str = "GOOD_FOR_DAY",
) -> dict:
    """Preview an order before placing it.
    
    Args:
        account_id_key: Account ID key
        symbol: Stock symbol (e.g., "AAPL")
        action: BUY or SELL
        quantity: Number of shares
        price_type: MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP_PRCT
        limit_price: Required for LIMIT orders
        stop_price: Required for STOP orders, or percentage for TRAILING_STOP_PRCT
        order_term: GOOD_FOR_DAY or GOOD_UNTIL_CANCEL
    
    Returns preview with previewId needed for placing order.
    """
    logger.info(f"Tool: etrade_preview_order({symbol} {action} {quantity})")
    
    auth_err = ensure_auth()
    if auth_err:
        return auth_err
    
    try:
        import time
        url = f"{get_base_url()}/accounts/{account_id_key}/orders/preview"
        
        order = {
            "PreviewOrderRequest": {
                "orderType": "EQ",
                "clientOrderId": f"mcp-{int(time.time())}",
                "Order": [{
                    "allOrNone": "false",
                    "priceType": price_type,
                    "orderTerm": order_term,
                    "marketSession": "REGULAR",
                    "Instrument": [{
                        "Product": {"securityType": "EQ", "symbol": symbol},
                        "orderAction": action,
                        "quantityType": "QUANTITY",
                        "quantity": str(quantity),
                    }]
                }]
            }
        }
        
        if limit_price:
            order["PreviewOrderRequest"]["Order"][0]["limitPrice"] = str(limit_price)
        if stop_price:
            order["PreviewOrderRequest"]["Order"][0]["stopPrice"] = str(stop_price)
        
        response = oauth_manager.session.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(order)
        )
        response.raise_for_status()
        
        # Parse response
        root = ET.fromstring(response.text)
        preview_id = root.find('.//previewId').text
        
        return {
            "status": "success",
            "previewId": preview_id,
            "clientOrderId": order["PreviewOrderRequest"]["clientOrderId"],
            "message": "Call etrade_place_order with this previewId to execute.",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@server.tool()
def etrade_place_order(
    account_id_key: str,
    preview_id: str,
    client_order_id: str,
    symbol: str,
    action: str,
    quantity: int,
    price_type: str = "MARKET",
    limit_price: float = None,
    stop_price: float = None,
    order_term: str = "GOOD_FOR_DAY",
) -> dict:
    """Place an order after previewing.
    
    Args:
        account_id_key: Account ID key
        preview_id: previewId from etrade_preview_order
        client_order_id: clientOrderId from etrade_preview_order
        symbol: Stock symbol
        action: BUY or SELL
        quantity: Number of shares
        price_type: MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP_PRCT
        limit_price: For LIMIT orders
        stop_price: For STOP orders or TRAILING_STOP_PRCT percentage
        order_term: GOOD_FOR_DAY or GOOD_UNTIL_CANCEL
    """
    logger.info(f"Tool: etrade_place_order({symbol} {action} {quantity})")
    
    auth_err = ensure_auth()
    if auth_err:
        return auth_err
    
    try:
        url = f"{get_base_url()}/accounts/{account_id_key}/orders/place"
        
        order = {
            "PlaceOrderRequest": {
                "orderType": "EQ",
                "clientOrderId": client_order_id,
                "PreviewIds": [{"previewId": preview_id}],
                "Order": [{
                    "allOrNone": "false",
                    "priceType": price_type,
                    "orderTerm": order_term,
                    "marketSession": "REGULAR",
                    "Instrument": [{
                        "Product": {"securityType": "EQ", "symbol": symbol},
                        "orderAction": action,
                        "quantityType": "QUANTITY",
                        "quantity": str(quantity),
                    }]
                }]
            }
        }
        
        if limit_price:
            order["PlaceOrderRequest"]["Order"][0]["limitPrice"] = str(limit_price)
        if stop_price:
            order["PlaceOrderRequest"]["Order"][0]["stopPrice"] = str(stop_price)
        
        response = oauth_manager.session.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(order)
        )
        response.raise_for_status()
        
        # Parse response
        root = ET.fromstring(response.text)
        order_id = root.find('.//orderId').text
        
        return {
            "status": "success",
            "orderId": order_id,
            "message": f"Order {order_id} placed successfully.",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@server.tool()
def etrade_cancel_order(account_id_key: str, order_id: str) -> dict:
    """Cancel an open order.
    
    Args:
        account_id_key: Account ID key
        order_id: Order ID to cancel
    """
    logger.info(f"Tool: etrade_cancel_order({order_id})")
    
    auth_err = ensure_auth()
    if auth_err:
        return auth_err
    
    try:
        url = f"{get_base_url()}/accounts/{account_id_key}/orders/cancel"
        response = oauth_manager.session.put(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"CancelOrderRequest": {"orderId": order_id}})
        )
        response.raise_for_status()
        
        return {"status": "success", "orderId": order_id, "message": "Order cancelled."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    """Run the MCP server."""
    logger.info("Starting E*TRADE MCP Server")
    server.run()


if __name__ == "__main__":
    main()
