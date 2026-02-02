#!/usr/bin/env python3
"""
Interactive OAuth test - complete the full E*TRADE OAuth flow.

Usage:
    python oauth_interactive_test.py

This script will:
1. Get a request token from E*TRADE
2. Print the authorization URL for you to visit
3. Wait for you to enter the verifier code
4. Exchange the verifier for an access token
5. Test by fetching your accounts list
"""

import sys
from api.oauth import oauth_manager
from api.config import settings


def main():
    print("=" * 70)
    print("E*TRADE OAuth Interactive Test")
    print("=" * 70)
    print(f"\nMode: {'PRODUCTION' if not settings.etrade_sandbox else 'SANDBOX'}")
    print(f"Consumer Key: {settings.consumer_key[:20]}...")

    # Step 1: Get request token
    print("\n[Step 1] Getting request token from E*TRADE...")
    try:
        result = oauth_manager.get_request_token()
        print(f"✅ Request token obtained")
        print(f"\n{'='*70}")
        print("AUTHORIZATION REQUIRED")
        print("="*70)
        print(f"\n1. Open this URL in your browser:\n")
        print(f"   {result['authorization_url']}")
        print(f"\n2. Log in with your E*TRADE credentials")
        print(f"3. Click 'Accept' to authorize the application")
        print(f"4. Copy the verification code shown on the page")
        print("="*70)
    except Exception as e:
        print(f"❌ Failed to get request token: {e}")
        return False

    # Step 2: Get verifier from user
    print("\nEnter the verification code from E*TRADE:")
    try:
        oauth_verifier = input("> ").strip()
        if not oauth_verifier:
            print("❌ No verifier entered")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Cancelled")
        return False

    # Step 3: Exchange verifier for access token
    print(f"\n[Step 2] Exchanging verifier '{oauth_verifier}' for access token...")
    try:
        oauth_manager.set_oauth_verifier(oauth_verifier)
        access_token_data = oauth_manager.get_access_token()
        print(f"✅ Access token obtained!")
        print(f"   Token: {access_token_data['oauth_token'][:30]}...")
    except Exception as e:
        print(f"❌ Failed to get access token: {e}")
        return False

    # Step 4: Test by getting accounts
    print(f"\n[Step 3] Testing authentication by fetching accounts...")
    try:
        # Use the authenticated session from oauth_manager
        if settings.etrade_sandbox:
            accounts_url = "https://apisb.etrade.com/v1/accounts/list"
        else:
            accounts_url = "https://api.etrade.com/v1/accounts/list"
        
        response = oauth_manager.session.get(accounts_url)
        response.raise_for_status()
        
        print(f"✅ SUCCESS - Authentication working!")
        print(f"\nAccounts Response (Status {response.status_code}):")
        print(response.text[:500] if len(response.text) > 500 else response.text)
        return True
    except Exception as e:
        print(f"❌ Failed to get accounts: {e}")
        return False


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 70)
    if success:
        print("✅ Full OAuth flow completed and verified!")
    else:
        print("❌ OAuth flow failed")
    print("=" * 70)
    sys.exit(0 if success else 1)
