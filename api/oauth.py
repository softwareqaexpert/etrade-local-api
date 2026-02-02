"""OAuth handling for E*TRADE API."""

import logging
from typing import Dict, Optional
from api.etrade_client import etrade_client
from api.config import settings

logger = logging.getLogger(__name__)


class OAuthManager:
    """Manages OAuth flow with E*TRADE."""

    def __init__(self):
        """Initialize OAuth manager."""
        self.request_token: Optional[str] = None
        self.request_token_secret: Optional[str] = None
        self.oauth_verifier: Optional[str] = None

    def get_request_token(self) -> Dict[str, str]:
        """
        Step 1 of OAuth flow: Get request token from E*TRADE.
        
        Returns:
            Dictionary with:
            - oauth_token: Request token to use in authorization
            - oauth_token_secret: Secret for signing requests
            - authorization_url: URL for user to visit for approval
            
        Raises:
            Exception: If E*TRADE API call fails
        """
        try:
            logger.info("Requesting OAuth token from E*TRADE")
            
            # Call E*TRADE OAuth to get request token and authorization URL
            # This also sets the request token in etrade_client.oauth.resource_owner_key
            authorization_url = etrade_client.oauth.get_request_token()
            
            # Get the request token that was set internally
            self.request_token = etrade_client.oauth.resource_owner_key
            
            # Get the request token secret from the session
            if hasattr(etrade_client.oauth, 'session') and etrade_client.oauth.session:
                # Extract token secret from the session
                token_secret = etrade_client.oauth.session.token.get('oauth_token_secret', '')
                self.request_token_secret = token_secret
            else:
                # Fallback to empty string if session not available
                self.request_token_secret = ""
            
            logger.info(f"Got request token: {self.request_token[:20] if self.request_token else 'None'}...")
            
            return {
                "oauth_token": self.request_token or "",
                "oauth_token_secret": self.request_token_secret or "",
                "authorization_url": authorization_url,
            }
            
        except Exception as e:
            logger.error(f"Error getting request token: {e}")
            raise

    def set_oauth_verifier(self, verifier: str) -> None:
        """
        Step 2 of OAuth flow: User approves on E*TRADE, gets verifier code.
        
        Args:
            verifier: 5-character OAuth verifier from E*TRADE authorization
        """
        self.oauth_verifier = verifier
        logger.info(f"OAuth verifier set: {verifier}")

    def get_access_token(self) -> Dict[str, str]:
        """
        Step 3 of OAuth flow: Exchange verifier for access token.
        
        Returns:
            Dictionary with:
            - oauth_token: Access token for API calls
            - oauth_token_secret: Secret for signing API requests
            
        Raises:
            Exception: If verifier not set or E*TRADE API call fails
        """
        if not self.oauth_verifier:
            raise ValueError("OAuth verifier not set. User must authorize first.")
        
        if not self.request_token or not self.request_token_secret:
            raise ValueError("Request token not available. Call get_request_token first.")
        
        try:
            logger.info("Exchanging OAuth verifier for access token")
            
            # Exchange verifier for access token
            # Update the oauth object with request token info first
            etrade_client.oauth.resource_owner_key = self.request_token
            etrade_client.oauth.resource_owner_secret = self.request_token_secret
            
            # Get access token using verifier
            access_token = etrade_client.oauth.get_access_token(self.oauth_verifier)
            
            logger.info(f"Got access token: {access_token.get('oauth_token', '')[:20]}...")
            
            return {
                "oauth_token": access_token.get("oauth_token", ""),
                "oauth_token_secret": access_token.get("oauth_token_secret", ""),
            }
            
        except Exception as e:
            logger.error(f"Error exchanging verifier for access token: {e}")
            raise


# Global OAuth manager instance
oauth_manager = OAuthManager()
