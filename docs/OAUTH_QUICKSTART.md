# OAuth 2.0 - Quick Start Guide

## 🎯 What is OAuth 2.0?

OAuth 2.0 is the industry-standard protocol for authorization. Instead of sharing passwords, users grant your application limited access to their accounts through secure tokens.

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Select OAuth 2.0

1. Open the application
2. Go to the **Authorization** tab
3. Select **"OAuth 2.0"** from the dropdown
4. Click **"🔐 Configure OAuth"**

### Step 2: Add Configuration

In the dialog that opens:

1. Go to **"➕ Add/Edit Config"** tab
2. Fill in:
   - **Config Name:** "My OAuth App" (any name you like)
   - **Flow Type:** Select "Authorization Code" (most common)
   - **Authorization URL:** Get from your OAuth provider
   - **Token URL:** Get from your OAuth provider
   - **Client ID:** From your OAuth provider
   - **Client Secret:** From your OAuth provider
   - **Scope:** Permissions you need (e.g., `read write`)
3. Click **"💾 Save Configuration"**

### Step 3: Authorize

1. Go to **"📋 Manage Configs"** tab
2. Select your configuration
3. Click **"🔐 Authorize"**
4. Browser opens → Log in and grant permissions
5. Return to application
6. ✅ Token obtained!

### Step 4: Use Token

1. Click **"✅ Use This Token"**
2. Done! All your requests now include the OAuth token

---

## 📱 Real-World Example: GitHub

### Get OAuth Credentials

1. Go to https://github.com/settings/developers
2. Click **"New OAuth App"**
3. Fill in:
   - **Application name:** "API Client Test"
   - **Homepage URL:** `http://localhost`
   - **Authorization callback URL:** `http://localhost:8080`
4. Click **"Register application"**
5. Note your **Client ID** and **Client Secret**

### Configure in Application

```
Config Name: GitHub OAuth
Flow Type: Authorization Code
Authorization URL: https://github.com/login/oauth/authorize
Token URL: https://github.com/login/oauth/access_token
Client ID: [Your GitHub Client ID]
Client Secret: [Your GitHub Client Secret]
Scope: repo user
```

### Test

1. Authorize (browser opens, login to GitHub)
2. Use Token
3. Make a request:
   - **Method:** GET
   - **URL:** `https://api.github.com/user`
4. Click **"Send"**
5. 🎉 See your GitHub profile data!

---

## 🔄 When Token Expires

### Refresh Token

1. You'll see **"❌ Token expired"** warning
2. Click **"🔄 Refresh Token"**
3. New token obtained automatically!

### Or Re-Authorize

1. Click **"🔐 Authorize"** again
2. Complete authorization
3. New token saved

---

## 💡 Tips

### Tip 1: Multiple Providers

Set up separate configs for:
- GitHub
- Google
- Your company API
- Development vs Production

### Tip 2: Scope Selection

Start with minimal scopes:
- GitHub: `user` (basic profile)
- Google: `openid email profile`
- Then add more as needed

### Tip 3: Client Credentials Flow

For server-to-server (no user login):
1. Select **"Client Credentials"** flow type
2. No Authorization URL needed
3. Token obtained instantly

---

## ❓ Common Questions

**Q: Do I need to authorize every time?**  
A: No! Tokens are saved and reused. Only re-authorize when expired or revoked.

**Q: Can I use multiple OAuth configs?**  
A: Yes! Create as many as you need for different APIs.

**Q: Is it secure?**  
A: Yes! Uses industry-standard OAuth 2.0 with CSRF protection and secure token exchange.

**Q: What if I get "State mismatch" error?**  
A: This is a security check. Just try authorizing again.

---

## 📚 Learn More

- **[OAUTH_GUIDE.md](OAUTH_GUIDE.md)** - Comprehensive user guide with all features
- **[OAUTH_SUMMARY.md](OAUTH_SUMMARY.md)** - Technical implementation details

---

## 🎉 You're Ready!

OAuth 2.0 is configured and working. Enjoy secure API authentication! 🔐🚀

