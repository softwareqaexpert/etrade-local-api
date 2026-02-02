# Important Note: E*TRADE App Registration

## OAuth Step 2 Potential Issue

**If Step 2 (Authorization redirect) fails**, it may be because:

- E*TRADE requires the app to be **pre-registered** with them
- We may need to inform E*TRADE of:
  - Application name
  - Callback URL
  - Company/developer information
  - Terms of service agreement

## Current Status

We are attempting to use the OAuth flow **without pre-registering the app**. 

This might work because:
1. Sandbox environment may be more permissive
2. pyetrade library may handle this automatically
3. E*TRADE sandbox may not require registration

Or it might fail if:
1. E*TRADE enforces app registration even in sandbox
2. Callback URL redirect is blocked
3. Consumer key validation requires registration

## Testing Plan

We will:
1. Implement the OAuth request token endpoint
2. Try to get a request token
3. Attempt to redirect to authorization URL
4. If Step 2 fails, document the error
5. Register the app with E*TRADE if needed

## References

- Check E*TRADE Developer Portal: https://developer.etrade.com/
- Look for "Register Application" or "Create App" sections
- May need to specify callback URL: http://localhost:8000/oauth/callback (or similar)

---

*Created: February 2, 2026*
*Status: About to test OAuth flow*
