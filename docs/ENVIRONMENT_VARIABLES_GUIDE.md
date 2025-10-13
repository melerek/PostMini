# Environment Variables Guide

## Overview

Environment variables allow you to create reusable configurations that can be easily switched between different environments (Development, Staging, Production, etc.). This is essential for team collaboration and managing API endpoints across different deployment stages.

## Features

✅ **Variable Substitution**: Use `{{variableName}}` syntax anywhere in your requests  
✅ **Multiple Environments**: Create unlimited environments (Dev, Staging, Prod, etc.)  
✅ **Easy Switching**: Switch between environments with a single click  
✅ **Team Sharing**: Export/import environments to share with your team  
✅ **Validation**: Warns you about unresolved variables before sending requests  

## Using Environment Variables

### 1. Creating an Environment

1. Click **"Manage Environments"** in the toolbar
2. Click **"Add"** to create a new environment
3. Enter a name (e.g., "Development", "Production")
4. Add variables in the table:
   - **Variable**: The name (e.g., `baseUrl`, `apiKey`)
   - **Value**: The actual value (e.g., `https://api.dev.example.com`, `dev-key-123`)
5. Click **"Save Environment"**

### 2. Variable Syntax

Use double curly braces to reference variables:

```
{{variableName}}
```

**Examples:**
- `{{baseUrl}}/users`
- `Authorization: Bearer {{apiToken}}`
- `{"apiKey": "{{apiKey}}"}`

### 3. Where to Use Variables

Variables can be used in:
- ✅ **URL**: `{{baseUrl}}/api/{{version}}/users`
- ✅ **Query Parameters**: `key={{apiKey}}&limit={{pageSize}}`
- ✅ **Headers**: `Authorization: Bearer {{token}}`
- ✅ **Body**: `{"username": "{{defaultUser}}"}`
- ✅ **Auth Token**: `{{bearerToken}}`

### 4. Selecting an Environment

1. Use the **Environment dropdown** in the toolbar
2. Select your desired environment
3. The toolbar will show how many variables are active
4. Send requests - variables will be automatically substituted!

## Example Setup

### Development Environment

Create an environment named **"Development"** with these variables:

| Variable | Value |
|----------|-------|
| `baseUrl` | `https://api.dev.example.com` |
| `apiKey` | `dev-api-key-12345` |
| `version` | `v1` |
| `timeout` | `5000` |

### Production Environment

Create an environment named **"Production"** with these variables:

| Variable | Value |
|----------|-------|
| `baseUrl` | `https://api.example.com` |
| `apiKey` | `prod-api-key-67890` |
| `version` | `v2` |
| `timeout` | `10000` |

### Example Request Using Variables

**URL:**
```
{{baseUrl}}/{{version}}/users
```

**Headers:**
```
Content-Type: application/json
X-API-Key: {{apiKey}}
```

**Body:**
```json
{
  "timeout": {{timeout}},
  "endpoint": "{{baseUrl}}"
}
```

### Results

When **Development** is selected:
- URL becomes: `https://api.dev.example.com/v1/users`
- Header becomes: `X-API-Key: dev-api-key-12345`

When **Production** is selected:
- URL becomes: `https://api.example.com/v2/users`
- Header becomes: `X-API-Key: prod-api-key-67890`

## Common Use Cases

### 1. API Endpoint Management
```
URL: {{baseUrl}}/{{version}}/{{resource}}

Variables:
- baseUrl: https://api.example.com
- version: v1
- resource: users
```

### 2. Authentication Tokens
```
Authorization Tab:
Type: Bearer Token
Token: {{authToken}}

Variables:
- authToken: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Dynamic Query Parameters
```
Params Tab:
- api_key: {{apiKey}}
- limit: {{defaultLimit}}
- offset: {{offset}}

Variables:
- apiKey: abc123
- defaultLimit: 50
- offset: 0
```

### 4. Request Body Templates
```json
{
  "api_key": "{{apiKey}}",
  "environment": "{{envName}}",
  "config": {
    "timeout": {{timeout}},
    "retry": {{retryCount}}
  }
}
```

## Best Practices

### ✅ DO:
- Use descriptive variable names: `apiKey`, `baseUrl`, `authToken`
- Create separate environments for each stage: Dev, Staging, Prod
- Document your variables in collection descriptions
- Use consistent naming conventions across environments
- Keep sensitive tokens in environment variables, not in requests

### ❌ DON'T:
- Don't use spaces in variable names: `{{api key}}` ❌ → `{{apiKey}}` ✅
- Don't hardcode values that change between environments
- Don't share production credentials in team environments
- Don't forget to save your environment after making changes

## Variable Naming Rules

Valid variable names:
- Must start with a letter or underscore: `{{apiKey}}`, `{{_token}}`
- Can contain letters, numbers, and underscores: `{{api_key_123}}`
- Are case-sensitive: `{{apiKey}}` ≠ `{{ApiKey}}`

Invalid variable names:
- `{{123key}}` - can't start with a number
- `{{api-key}}` - no hyphens allowed
- `{{api key}}` - no spaces allowed

## Troubleshooting

### Unresolved Variable Warning

If you see this warning:
> "The following variables are not defined in the current environment: variableName"

**Solutions:**
1. Check that you've selected an environment (not "No Environment")
2. Open "Manage Environments" and verify the variable exists
3. Check for typos in the variable name
4. Ensure variable name follows naming rules

### Variable Not Substituting

**Checklist:**
- [ ] Environment is selected in dropdown
- [ ] Variable is defined in the environment
- [ ] Variable syntax is correct: `{{variableName}}`
- [ ] Variable name matches exactly (case-sensitive)
- [ ] Environment has been saved after adding variables

## Team Collaboration

### Sharing Environments (Coming Soon)

**Method 1: Export/Import** (Future Feature)
- Export environment as JSON file
- Share file with team via email/Slack
- Team members import the file

**Method 2: Shared Configuration** (Future Feature)
- Store environments in shared Git repository
- Auto-sync across team members

**Current Method:**
1. Open "Manage Environments"
2. Take screenshots of variable tables
3. Share with team members
4. Team members manually recreate the environment

### Security Best Practices

For team environments:
- ✅ Share development API keys
- ✅ Share staging endpoints
- ❌ Never share production secrets
- ❌ Never commit sensitive tokens to version control

Use different environments for:
- **Team Dev**: Shared development environment (safe to share)
- **Personal Dev**: Your personal testing keys
- **Production**: Keep private, use secure vault

## Example Workflow

### Step-by-Step: Setting up Multi-Environment Testing

1. **Create Environments**
   ```
   Development:
     - baseUrl: https://dev.api.example.com
     - apiKey: dev-key-123
   
   Staging:
     - baseUrl: https://staging.api.example.com
     - apiKey: staging-key-456
   
   Production:
     - baseUrl: https://api.example.com
     - apiKey: prod-key-789
   ```

2. **Create Request**
   ```
   Collection: User API
   Request: Get Users
   URL: {{baseUrl}}/v1/users
   Headers:
     - Authorization: Bearer {{apiKey}}
   ```

3. **Test Across Environments**
   - Select "Development" → Send → Test with dev data
   - Select "Staging" → Send → Test with staging data
   - Select "Production" → Send → Test with prod data

4. **Save and Share**
   - Save the request
   - Share collection with team
   - Team members create their own environments

## Advanced Tips

### Nested URLs
```
URL: {{protocol}}://{{domain}}:{{port}}/{{basePath}}/{{endpoint}}

Variables:
- protocol: https
- domain: api.example.com
- port: 443
- basePath: api/v1
- endpoint: users
```

### Dynamic Headers
```
Headers:
- X-API-Version: {{apiVersion}}
- X-Client-ID: {{clientId}}
- X-Request-ID: {{requestId}}
```

### Environment-Specific Bodies
```json
{
  "environment": "{{envName}}",
  "debug": {{debugMode}},
  "log_level": "{{logLevel}}"
}
```

## Keyboard Shortcuts (Future Feature)

- `Ctrl+E`: Open Environment Manager
- `Ctrl+Shift+E`: Quick switch environment
- `Ctrl+Alt+E`: Clear active environment

## FAQ

**Q: Can I use variables in variable values?**  
A: Not currently supported. Variables are single-level only.

**Q: How many variables can I have per environment?**  
A: Unlimited! Add as many as you need.

**Q: Can I export my environments?**  
A: Coming soon! Currently stored in local SQLite database.

**Q: Are variables encrypted?**  
A: Currently stored in plain text in local database. Use OS-level encryption for sensitive data.

**Q: Can I use variables in collection/request names?**  
A: No, variables only work in request configuration (URL, headers, body, etc.).

## Support

For issues or questions:
1. Check this guide
2. Review the main README.md
3. Open an issue on GitHub

---

**Happy API Testing with Environment Variables! 🚀**

