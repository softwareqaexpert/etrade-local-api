#!/usr/bin/env python3
"""
Test script to walk through the complete OAuth flow and retrieve accounts.

This script simulates the OAuth flow:
1. Get request token and authorization URL
2. Simulate user authorization (manual step)
3. Exchange verifier for access token
4. Get accounts list
"""

import sys
from api.oauth import oauth_manager
from api.etrade_client import etrade_client

def main():
    print("=" * 70)
    print("E*TRADE OAuth Flow & Accounts Retrieval Test")
    print("=" * 70)
    
    # Step 1: Get request token
    print("\n[Step 1] Getting request token from E*TRADE...")
    try:
        result = oauth_manager.get_request_token()
        print(f"✅ SUCCESS")
        print(f"   Request Token: {result['oauth_token'][:30]}...")
        print(f"   Token Secret: {result['oauth_token_secret'][:30]}...")
        print(f"\n   Authorization URL:")
        print(f"   {result['authorization_url']}")
        request_token = result['oauth_token']
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Step 2: Simulate user authorization
    print("\n[Step 2] User Authorization (simulated)")
    print("   In a real flow, user would:")
    print("   1. Open the authorization URL in browser")
    print("   2. Log in with E*TRADE credentials")
    print("   3. Click 'Authorize' button")
    print("   4. E*TRADE returns with oauth_verifier")
    print("\n   For this test, we'll simulate with a test verifier")
    # In real scenario, E*TRADE would provide this after user authorization
    # For now, we'll get a real verifier by simulating the flow
    oauth_verifier = "12345"  # Placeholder
    print(f"   OAuth Verifier (simulated): {oauth_verifier}")
    
    # Step 3: Exchange verifier for access token
    print("\n[Step 3] Exchanging verifier for access token...")
    try:
        oauth_manager.set_oauth_verifier(oauth_verifier)
        access_token_data = oauth_manager.get_access_token()
        print(f"✅ SUCCESS")
        print(f"   Access Token: {access_token_data['oauth_token'][:30]}...")
        print(f"   Token Secret: {access_token_data['oauth_token_secret'][:30]}...")
    except Exception as e:
        print(f"⚠️  Note: {e}")
        print("   This is expected if verifier is invalid.")
        print("   In a real flow, E*TRADE would provide the actual verifier.")
        return False
    
    # Step 4: Get accounts
    print("\n[Step 4] Retrieving accounts...")
    try:
        if not oauth_manager.is_authenticated():
            print("❌ Not authenticated")
            return False
        
        accounts_list = etrade_client.accounts.get_account_list()
        print(f"✅ SUCCESS - Retrieved accounts!")
        print(f"\n   Accounts Response:")
        print(f"   {accounts_list}")
        return True
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("   This is expected since we used a simulated verifier.")
        return False


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 70)
    if success:
        print("✅ Full OAuth flow completed successfully!")
    else:
        print("⚠️  OAuth flow test completed (partial - waiting for real verifier)")
    print("=" * 70)
