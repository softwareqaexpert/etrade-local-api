"""OAuth handling for E*TRADE API."""

import logging
from typing import Dict, Optional
from requests_oauthlib import OAuth1Session
from api.config import settings

logger = logging.getLogger(__name__)


class OAuthManager:
    """Manages OAuth flow with E*TRADE using requests_oauthlib directly."""

    def __init__(self):
        """Initialize OAuth manager."""
        self.request_token: Optional[str] = None
        self.request_token_secret: Optional[str] = None
        self.oauth_verifier: Optional[str] = None
        self.access_token: Optional[str] = None
        self.access_token_secret: Optional[str] = None
        self.session: Optional[OAuth1Session] = None

    def get_request_token(self) -> Dict[str, str]:
        """
        Step 1 of OAuth flow: Get request token from E*TRADE.
        
        Creates and stores session for use in get_access_token().
        """
        try:
            logger.info("Requesting OAuth token from E*TRADE")
            
            # Get correct URLs based on sandbox/prod
            if settings.etrade_sandbox:
                req_token_url = "https://apisb.etrade.com/oauth/request_token"
            else:
                req_token_url = "https://api.etrade.com/oauth/request_token"
            
            # Create session and store it for later use
            self.session = OAuth1Session(
                settings.consumer_key,
                settings.consumer_secret,
                callback_uri="oob",
                signature_type="AUTH_HEADER"
            )
            
            # Get request token
            self.session.fetch_request_token(req_token_url)
            
            # Store tokens
            self.request_token = self.session.token['oauth_token']
            self.request_token_secret = self.session.token['oauth_token_secret']
            
            logger.info(f"Got request token: {self.request_token[:20]}...")
            
            # Build authorization URL
            authorization_url = f"https://us.etrade.com/e/t/etws/authorize?key={settings.consumer_key}&token={self.request_token}"
            
            return {
                "oauth_token": self.request_token,
                "oauth_token_secret": self.request_token_secret,
                "authorization_url": authorization_url,
            }
            
        except Exception as e:
            logger.error(f"Error getting request token: {e}")
            raise

    def set_oauth_verifier(self, verifier: str) -> None:
        """Step 2: User approves on E*TRADE, gets verifier code."""
        self.oauth_verifier = verifier
        logger.info(f"OAuth verifier set: {verifier}")

    def get_access_token(self) -> Dict[str, str]:
        """
        Step 3: Exchange verifier for access token.
        Uses the SAME session from get_request_token().
        """
        if not self.oauth_verifier:
            raise ValueError("OAuth verifier not set. User must authorize first.")
        
        if not self.session:
            raise ValueError("Session not available. Call get_request_token first.")
        
        try:
            logger.info("Exchanging OAuth verifier for access token")
            
            # Get correct URL based on sandbox/prod
            if settings.etrade_sandbox:
                access_token_url = "https://apisb.etrade.com/oauth/access_token"
            else:
                access_token_url = "https://api.etrade.com/oauth/access_token"
            
            # Set verifier on the client INSIDE the session
            self.session._client.client.verifier = self.oauth_verifier
            
            # Fetch access token using SAME session
            access_token = self.session.fetch_access_token(access_token_url)
            
            # Store access tokens
            self.access_token = access_token['oauth_token']
            self.access_token_secret = access_token['oauth_token_secret']
            
            logger.info(f"Got access token: {self.access_token[:20]}...")
            
            return {
                "oauth_token": self.access_token,
                "oauth_token_secret": self.access_token_secret,
            }
            
        except Exception as e:
            logger.error(f"Error exchanging verifier for access token: {e}")
            raise

    def is_authenticated(self) -> bool:
        """Check if we have a valid access token."""
        return bool(self.access_token and self.access_token_secret)


oauth_manager = OAuthManager()
