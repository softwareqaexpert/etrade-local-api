"""OAuth handling for E*TRADE API with token persistence and auto-renewal."""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from requests_oauthlib import OAuth1Session
from api.config import settings

logger = logging.getLogger(__name__)

# Token storage file location
TOKEN_FILE = Path.home() / ".etrade_tokens.json"
EASTERN_TZ = ZoneInfo("America/New_York")


class OAuthManager:
    """Manages OAuth flow with E*TRADE with token persistence and auto-renewal."""

    def __init__(self):
        """Initialize OAuth manager and load saved tokens."""
        self.request_token: Optional[str] = None
        self.request_token_secret: Optional[str] = None
        self.oauth_verifier: Optional[str] = None
        self.access_token: Optional[str] = None
        self.access_token_secret: Optional[str] = None
        self.session: Optional[OAuth1Session] = None
        self.last_used: Optional[datetime] = None
        self.token_date: Optional[str] = None  # Date tokens were obtained (ET)
        
        # Try to load saved tokens
        self._load_tokens()

    def _get_eastern_date(self) -> str:
        """Get current date in Eastern timezone as string."""
        return datetime.now(EASTERN_TZ).strftime("%Y-%m-%d")

    def _save_tokens(self) -> None:
        """Save tokens to file for persistence."""
        if not self.access_token:
            return
        
        data = {
            "access_token": self.access_token,
            "access_token_secret": self.access_token_secret,
            "last_used": datetime.now(EASTERN_TZ).isoformat(),
            "token_date": self._get_eastern_date(),
            "sandbox": settings.etrade_sandbox,
        }
        
        try:
            TOKEN_FILE.write_text(json.dumps(data, indent=2))
            logger.info(f"Tokens saved to {TOKEN_FILE}")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    def _load_tokens(self) -> bool:
        """Load tokens from file. Returns True if valid tokens loaded."""
        if not TOKEN_FILE.exists():
            logger.info("No saved tokens found")
            return False
        
        try:
            data = json.loads(TOKEN_FILE.read_text())
            
            # Check if tokens are for same environment (sandbox/prod)
            if data.get("sandbox") != settings.etrade_sandbox:
                logger.info("Saved tokens are for different environment")
                return False
            
            # Check if tokens are from today (Eastern time)
            token_date = data.get("token_date")
            if token_date != self._get_eastern_date():
                logger.info(f"Tokens expired (from {token_date}, today is {self._get_eastern_date()})")
                return False
            
            # Load tokens
            self.access_token = data["access_token"]
            self.access_token_secret = data["access_token_secret"]
            self.last_used = datetime.fromisoformat(data["last_used"])
            self.token_date = token_date
            
            # Recreate session with access tokens
            self._create_authenticated_session()
            
            logger.info(f"Loaded saved tokens from {token_date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return False

    def _create_authenticated_session(self) -> None:
        """Create an authenticated session using stored access tokens."""
        self.session = OAuth1Session(
            settings.consumer_key,
            settings.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
            signature_type="AUTH_HEADER"
        )

    def _is_token_idle(self) -> bool:
        """Check if token has been idle for > 2 hours."""
        if not self.last_used:
            return True
        
        idle_time = datetime.now(EASTERN_TZ) - self.last_used.replace(tzinfo=EASTERN_TZ)
        return idle_time > timedelta(hours=2)

    def _renew_token(self) -> bool:
        """Renew access token if idle. Returns True if successful."""
        if not self.session:
            return False
        
        try:
            logger.info("Renewing access token...")
            
            if settings.etrade_sandbox:
                renew_url = "https://apisb.etrade.com/oauth/renew_access_token"
            else:
                renew_url = "https://api.etrade.com/oauth/renew_access_token"
            
            response = self.session.get(renew_url)
            response.raise_for_status()
            
            # Update last used time
            self.last_used = datetime.now(EASTERN_TZ)
            self._save_tokens()
            
            logger.info("Access token renewed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to renew token: {e}")
            return False

    def ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid, active session.
        
        Returns True if ready to make API calls.
        Returns False if re-authentication is required.
        """
        if not self.is_authenticated():
            return False
        
        # Check if tokens expired (past midnight ET)
        if self.token_date != self._get_eastern_date():
            logger.info("Tokens expired at midnight ET")
            self.access_token = None
            self.access_token_secret = None
            self.session = None
            return False
        
        # Check if idle > 2 hours, try to renew
        if self._is_token_idle():
            logger.info("Token idle > 2 hours, attempting renewal")
            if not self._renew_token():
                logger.warning("Token renewal failed, re-auth required")
                return False
        
        # Update last used time
        self.last_used = datetime.now(EASTERN_TZ)
        self._save_tokens()
        
        return True

    def get_request_token(self) -> Dict[str, str]:
        """Step 1 of OAuth flow: Get request token from E*TRADE."""
        try:
            logger.info("Requesting OAuth token from E*TRADE")
            
            if settings.etrade_sandbox:
                req_token_url = "https://apisb.etrade.com/oauth/request_token"
            else:
                req_token_url = "https://api.etrade.com/oauth/request_token"
            
            self.session = OAuth1Session(
                settings.consumer_key,
                settings.consumer_secret,
                callback_uri="oob",
                signature_type="AUTH_HEADER"
            )
            
            self.session.fetch_request_token(req_token_url)
            
            self.request_token = self.session.token['oauth_token']
            self.request_token_secret = self.session.token['oauth_token_secret']
            
            logger.info(f"Got request token: {self.request_token[:20]}...")
            
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
        """Step 3: Exchange verifier for access token."""
        if not self.oauth_verifier:
            raise ValueError("OAuth verifier not set. User must authorize first.")
        
        if not self.session:
            raise ValueError("Session not available. Call get_request_token first.")
        
        try:
            logger.info("Exchanging OAuth verifier for access token")
            
            if settings.etrade_sandbox:
                access_token_url = "https://apisb.etrade.com/oauth/access_token"
            else:
                access_token_url = "https://api.etrade.com/oauth/access_token"
            
            self.session._client.client.verifier = self.oauth_verifier
            
            access_token = self.session.fetch_access_token(access_token_url)
            
            self.access_token = access_token['oauth_token']
            self.access_token_secret = access_token['oauth_token_secret']
            self.last_used = datetime.now(EASTERN_TZ)
            self.token_date = self._get_eastern_date()
            
            # Save tokens for persistence
            self._save_tokens()
            
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
        return bool(self.access_token and self.access_token_secret and self.session)


oauth_manager = OAuthManager()
