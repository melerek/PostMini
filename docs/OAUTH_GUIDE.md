# OAuth 2.0 - User Guide

## Overview

OAuth 2.0 is the industry-standard protocol for authorization. This application provides comprehensive OAuth 2.0 support, allowing you to:

- 🔐 **Authenticate** with OAuth 2.0 providers (GitHub, Google, etc.)
- 🔄 **Automatically refresh** expired tokens
- 💾 **Store and reuse** tokens across sessions
- 🎯 **Support multiple flow types** for different use cases

---

## Supported OAuth 2.0 Flows

### 1. ✅ Authorization Code Flow (Recommended)

**Best for:** User-facing applications, web apps, mobile apps

**How it works:**
1. Opens browser for user login
2. User grants permission
3. Application receives authorization code
4. Code is exchanged for access token
5. Token is stored and auto-refreshed

**Use this when:**
- Your API requires user authorization
- You're building applications where users need to grant access
- You want the most secure OAuth flow

**Examples:**
- GitHub OAuth
- Google OAuth
- Facebook Login
- Microsoft Azure AD

---

### 2. ⚡ Client Credentials Flow

**Best for:** Server-to-server communication, backend services

**How it works:**
1. Application authenticates with client ID and secret
2. Receives access token immediately
3. No user interaction required

**Use this when:**
- Your application needs to access its own resources
- Server-to-server API calls
- Batch processing or background jobs
- Microservices authentication

**Examples:**
- Accessing your company's API
- Machine-to-machine communication
- Scheduled tasks

---

### 3. ⚠️ Password Grant Flow (Legacy)

**Best for:** Trusted first-party applications only

**How it works:**
1. User provides username and password to application
2. Application sends credentials to OAuth server
3. Receives access token

**Use this when:**
- You own both the client and the server
- Other flows are not supported by the API
- Migrating legacy systems

**⚠️ Warning:** This flow is deprecated. Use Authorization Code flow when possible.

---

## Getting Started

### Step 1: Create an OAuth Configuration

1. **In the main window**, go to the **Authorization** tab
2. Select **"OAuth 2.0"** from the Type dropdown
3. Click **"🔐 Configure OAuth"**
4. Go to the **"➕ Add/Edit Config"** tab

### Step 2: Fill in OAuth Details

#### Required Fields:

- **Config Name:** A friendly name (e.g., "GitHub OAuth", "My API")
- **Flow Type:** Select the appropriate OAuth flow
- **Token URL:** The OAuth token endpoint (e.g., `https://github.com/login/oauth/access_token`)
- **Client ID:** Your application's client ID
- **Client Secret:** Your application's client secret

#### Optional Fields:

- **Authorization URL:** Required for Authorization Code flow
- **Scope:** Permissions you're requesting (space-separated, e.g., `read write`)

### Step 3: Save Configuration

Click **"💾 Save Configuration"** to save your OAuth setup.

### Step 4: Authorize and Get Token

1. Go to the **"📋 Manage Configs"** tab
2. Select your configuration from the list
3. Click **"🔐 Authorize"**
4. For **Authorization Code flow**: Browser will open, complete the authorization
5. For **Client Credentials flow**: Token is obtained automatically
6. For **Password Grant flow**: Enter username and password when prompted

### Step 5: Use the Token

1. After authorization, you'll see **"✅ Valid token"** status
2. Click **"✅ Use This Token"**
3. Your API requests will now include the OAuth token automatically!

---

## Example: GitHub OAuth

### Prerequisites

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create a new OAuth App
3. Set Authorization callback URL to: `http://localhost:8080`
4. Note down Client ID and Client Secret

### Configuration

**Config Name:** GitHub OAuth  
**Flow Type:** Authorization Code  
**Authorization URL:** `https://github.com/login/oauth/authorize`  
**Token URL:** `https://github.com/login/oauth/access_token`  
**Client ID:** Your GitHub Client ID  
**Client Secret:** Your GitHub Client Secret  
**Scope:** `repo user` (or as needed)

### Authorization

1. Click **"🔐 Authorize"**
2. Browser opens → Sign in to GitHub
3. Grant permissions
4. Return to application
5. ✅ Token saved!

### Use

1. Click **"✅ Use This Token"**
2. Make API requests to GitHub:
   - URL: `https://api.github.com/user`
   - Method: GET
   - **OAuth token is automatically included!**

---

## Example: Google OAuth

### Prerequisites

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable APIs you need (e.g., Google Drive API)
4. Create OAuth 2.0 Client ID
5. Add `http://localhost:8080` to Authorized redirect URIs

### Configuration

**Config Name:** Google OAuth  
**Flow Type:** Authorization Code  
**Authorization URL:** `https://accounts.google.com/o/oauth2/v2/auth`  
**Token URL:** `https://oauth2.googleapis.com/token`  
**Client ID:** Your Google Client ID  
**Client Secret:** Your Google Client Secret  
**Scope:** `openid email profile` (or as needed)

### Authorization

1. Click **"🔐 Authorize"**
2. Browser opens → Sign in with Google
3. Grant permissions
4. Return to application
5. ✅ Token saved!

---

## Example: Client Credentials Flow

### Configuration

**Config Name:** My API Service  
**Flow Type:** Client Credentials  
**Token URL:** `https://api.example.com/oauth/token`  
**Client ID:** your_client_id  
**Client Secret:** your_client_secret  
**Scope:** `api.read api.write`

### Authorization

1. Click **"🔐 Authorize"**
2. Token obtained immediately (no browser)
3. ✅ Token saved!

---

## Token Management

### Token Expiry

- Tokens have expiration times
- Application automatically checks expiry before requests
- ⚠️ Warning appears if token is expired

### Refreshing Tokens

**If your configuration supports refresh tokens:**

1. Click **"🔄 Refresh Token"**
2. New access token obtained automatically
3. No need to re-authorize!

**Note:** Not all OAuth providers issue refresh tokens. Authorization Code flow usually includes them, but Client Credentials flow may not.

### Multiple Configurations

You can save multiple OAuth configurations:
- GitHub OAuth for personal projects
- Company API for work
- Google OAuth for integrations

Switch between them easily!

---

## Advanced Features

### Automatic Token Inclusion

When OAuth 2.0 is selected:
- Access token is automatically added to all requests
- Added as `Authorization: Bearer <token>` header
- No manual token entry needed

### Token Expiry Checks

Before each request:
- Application checks if token is expired
- Warns you if refresh is needed
- Prevents failed requests due to expired tokens

### Secure Storage

- Tokens are stored securely in local database
- Persist across application restarts
- Encrypted client secrets (recommended to add encryption in production)

### Environment Variables Integration

OAuth tokens work seamlessly with environment variables:
- Use `{{variable}}` in other fields (URL, params, etc.)
- OAuth token is applied separately
- Full flexibility

---

## Common OAuth Providers

### GitHub

- **Auth URL:** `https://github.com/login/oauth/authorize`
- **Token URL:** `https://github.com/login/oauth/access_token`
- **Scopes:** `repo`, `user`, `gist`, `notifications`, etc.
- **Docs:** https://docs.github.com/en/developers/apps/authorizing-oauth-apps

### Google

- **Auth URL:** `https://accounts.google.com/o/oauth2/v2/auth`
- **Token URL:** `https://oauth2.googleapis.com/token`
- **Scopes:** `openid`, `email`, `profile`, plus API-specific scopes
- **Docs:** https://developers.google.com/identity/protocols/oauth2

### Microsoft

- **Auth URL:** `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize`
- **Token URL:** `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`
- **Scopes:** Various based on Microsoft Graph API
- **Docs:** https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow

### Spotify

- **Auth URL:** `https://accounts.spotify.com/authorize`
- **Token URL:** `https://accounts.spotify.com/api/token`
- **Scopes:** `user-read-private`, `playlist-read-private`, etc.
- **Docs:** https://developer.spotify.com/documentation/general/guides/authorization/

### LinkedIn

- **Auth URL:** `https://www.linkedin.com/oauth/v2/authorization`
- **Token URL:** `https://www.linkedin.com/oauth/v2/accessToken`
- **Scopes:** `r_liteprofile`, `r_emailaddress`, etc.
- **Docs:** https://docs.microsoft.com/en-us/linkedin/shared/authentication/authentication

---

## Troubleshooting

### Issue: "Authorization cancelled or timed out"

**Cause:** You didn't complete authorization in browser within 5 minutes.

**Solution:**
- Try again
- Complete authorization faster
- Check if popup blocker prevented browser from opening

### Issue: "State mismatch - possible CSRF attack"

**Cause:** State parameter doesn't match (security check).

**Solution:**
- This is a security feature
- Try authorizing again
- If persists, check for network issues or proxy interference

### Issue: "Token expired"

**Cause:** Access token has exceeded its lifetime.

**Solution:**
- Click **"🔄 Refresh Token"** (if refresh token available)
- Or re-authorize by clicking **"🔐 Authorize"** again

### Issue: "No refresh token available"

**Cause:** OAuth provider didn't issue a refresh token.

**Solution:**
- Some providers don't issue refresh tokens for all flows
- For Client Credentials flow, re-authorize to get new token
- Check if you need to request `offline_access` scope (Google) or `access_type=offline` parameter

### Issue: "Failed to refresh OAuth token"

**Cause:** Refresh token expired or revoked.

**Solution:**
- Re-authorize using **"🔐 Authorize"** button
- User may have revoked application access (check provider's authorized apps page)

### Issue: "Cannot start callback server"

**Cause:** Port 8080 is already in use.

**Solution:**
- Close other applications using port 8080
- The callback server stops automatically after receiving the code

---

## Security Best Practices

### ✅ DO:

1. **Keep client secrets secure**
   - Don't share them
   - Don't commit to version control
   - Rotate them periodically

2. **Use Authorization Code flow when possible**
   - Most secure
   - Supports refresh tokens
   - Recommended by OAuth 2.0 spec

3. **Request minimal scopes**
   - Only request permissions you need
   - Users are more likely to approve

4. **Check token expiry**
   - Application does this automatically
   - Refresh before making requests

5. **Use HTTPS for redirect URIs** (in production)
   - `http://localhost` is fine for development
   - Production should use `https://`

### ❌ DON'T:

1. **Don't use Password Grant flow unless necessary**
   - Deprecated for security reasons
   - Use Authorization Code flow instead

2. **Don't share access tokens**
   - They grant access to user data
   - Treat like passwords

3. **Don't ignore expiry warnings**
   - Expired tokens lead to failed requests
   - Refresh proactively

4. **Don't hardcode tokens in code**
   - Use the OAuth flow
   - Let application manage tokens

---

## Tips & Tricks

### Tip 1: Testing OAuth Flows

Before implementing in your application:
1. Configure OAuth in this tool
2. Test authorization and token retrieval
3. Make sample API requests
4. Once working, implement in your app

### Tip 2: Copy Access Tokens

Need to use a token elsewhere?
1. Authorize and get token
2. Token is stored in database
3. Use database browser to view (for debugging)

### Tip 3: Multiple Environments

Set up different OAuth configs for:
- Development (test OAuth app)
- Staging (staging OAuth app)
- Production (production OAuth app)

### Tip 4: Scope Reference

Keep provider's scope documentation handy:
- List all available scopes
- Choose the right ones for your needs
- Request incrementally (start minimal, add as needed)

### Tip 5: Token Debugging

If requests fail:
1. Check token hasn't expired
2. Verify correct scopes
3. Test token manually (curl with Authorization header)
4. Check provider's API documentation

---

## FAQ

**Q: Can I use multiple OAuth configurations?**  
A: Yes! Create separate configs for each provider or environment.

**Q: Are tokens stored securely?**  
A: Tokens are stored in local SQLite database. For production, consider adding encryption.

**Q: Can I export/import OAuth configurations?**  
A: Currently, configs are stored locally. Export/import feature coming soon.

**Q: What happens if I close the app during authorization?**  
A: The callback server stops. Just try authorizing again when you reopen.

**Q: Can I use OAuth with environment variables?**  
A: Yes! OAuth tokens are separate from environment variables and work together.

**Q: Do I need to refresh tokens manually?**  
A: Application checks expiry automatically. Refresh only when warned or proactively.

**Q: Can I revoke a token?**  
A: Delete the config or clear the token. To revoke on provider's side, visit their authorized apps page.

**Q: Is Implicit flow supported?**  
A: We support Authorization Code flow (modern replacement for Implicit). Most providers have migrated away from Implicit flow.

---

## Support

Need help?
- Check this guide
- Review provider's OAuth documentation
- Test with a simple API first
- Check for error messages in dialogs

---

**Happy OAuth-ing! 🔐🚀**

