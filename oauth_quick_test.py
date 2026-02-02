#!/usr/bin/env python3
"""OAuth test - stores request token for verifier exchange"""
import sys
import json
import os
from requests_oauthlib import OAuth1Session
from api.config import settings

TOKEN_FILE = "/tmp/etrade_oauth_token.json"

if len(sys.argv) < 2:
    # Step 1: Get request token
    session = OAuth1Session(
        settings.etrade_consumer_key_prod,
        settings.etrade_consumer_secret_prod,
        callback_uri="oob",
        signature_type="AUTH_HEADER"
    )
    session.fetch_request_token("https://api.etrade.com/oauth/request_token")
    
    token_data = {
        "oauth_token": session.token['oauth_token'],
        "oauth_token_secret": session.token['oauth_token_secret']
    }
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)
    
    print(f"Open and authorize:\n")
    print(f"https://us.etrade.com/e/t/etws/authorize?key={settings.etrade_consumer_key_prod}&token={token_data['oauth_token']}")
    print(f"\nThen run: python oauth_quick_test.py <verifier>")
    sys.exit(0)

# Step 2: Exchange stored token + verifier for access token
if not os.path.exists(TOKEN_FILE):
    print("❌ No stored token. Run without args first.")
    sys.exit(1)

with open(TOKEN_FILE) as f:
    token_data = json.load(f)

verifier = sys.argv[1]
print(f"Request token: {token_data['oauth_token'][:20]}...")
print(f"Verifier: {verifier}")

# Create session with STORED request token
session = OAuth1Session(
    settings.etrade_consumer_key_prod,
    settings.etrade_consumer_secret_prod,
    resource_owner_key=token_data['oauth_token'],
    resource_owner_secret=token_data['oauth_token_secret'],
    signature_type="AUTH_HEADER"
)

# Set verifier and exchange
session._client.client.verifier = verifier

try:
    access = session.fetch_access_token("https://api.etrade.com/oauth/access_token")
    print(f"✅ Access token: {access['oauth_token'][:30]}...\n")
    
    # Test accounts
    from api.etrade_client import etrade_client
    etrade_client.oauth.resource_owner_key = access['oauth_token']
    etrade_client.oauth.resource_owner_secret = access['oauth_token_secret']
    
    accounts = etrade_client.accounts.get_account_list()
    print(f"✅ ACCOUNTS:")
    print(json.dumps(accounts, indent=2))
    
    # Clean up
    os.remove(TOKEN_FILE)
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
