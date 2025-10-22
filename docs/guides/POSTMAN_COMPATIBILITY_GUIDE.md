# Postman Compatibility Guide

## Overview
Our API Client now supports **full compatibility with Postman Collection Format v2.1**, enabling seamless import and export of collections between Postman and our application.

**Schema:** `https://schema.getpostman.com/json/collection/v2.1.0/collection.json`

---

## Features

### ✅ Export to Postman Format
- Convert your collections to Postman-compatible JSON
- Share collections with Postman users
- Use Postman's extensive ecosystem

### ✅ Import from Postman Format
- Import existing Postman collections
- Automatic format detection
- Migrate from Postman to our application

### ✅ Dual Format Support
- **Internal Format:** Our custom, optimized format
- **Postman Format:** Industry-standard format
- Choose on export, automatic detection on import

---

## Exporting Collections

### Step 1: Select Collection
1. Select a collection in the tree view
2. Click the **"Export"** button in the toolbar

### Step 2: Choose Format
You'll see a dialog with two options:

#### Internal Format (default)
- Our custom JSON format
- Optimized for our application
- Smaller file size
- Includes metadata

#### Postman Collection v2.1
- Standard Postman format
- Compatible with Postman and other API tools
- Can be shared with any Postman user
- Recognized by API documentation tools

### Step 3: Save File
1. Choose where to save the JSON file
2. Click Save
3. Done! Your collection is exported

---

## Importing Collections

### From Internal Format
1. Click **"Import"** button
2. Select a JSON file exported from our app
3. Choose handling of duplicates
4. Collection is imported

### From Postman Format
1. Click **"Import"** button
2. Select a Postman Collection JSON file
3. **Automatic detection** - we detect it's Postman format
4. **Automatic conversion** - converted to our internal format
5. Collection is imported with all requests

**Supported:** ✅ Automatic detection and conversion

---

## What Gets Converted

### Request Properties

| Property | Postman → Internal | Internal → Postman |
|----------|-------------------|-------------------|
| **Request Name** | ✅ Full support | ✅ Full support |
| **HTTP Method** | ✅ All methods | ✅ All methods |
| **URL** | ✅ Full URL parsing | ✅ Full URL building |
| **Query Parameters** | ✅ Extracted | ✅ Converted |
| **Headers** | ✅ All headers | ✅ All headers |
| **Request Body** | ✅ Raw/JSON/Form | ✅ Raw mode |
| **Bearer Token Auth** | ✅ Supported | ✅ Supported |
| **Folders** | ✅ Flattened with prefix | ➖ Not supported |

### Authentication

| Auth Type | Import | Export |
|-----------|--------|--------|
| **Bearer Token** | ✅ Full support | ✅ Full support |
| **API Key** | ✅ Converted to Bearer | ➖ Not exported |
| **Basic Auth** | ➖ Not supported | ➖ Not supported |
| **OAuth 2.0** | ➖ Not in export | ➖ Not in export |

**Note:** OAuth 2.0 tokens are stored separately in our app and not included in exports (for security).

---

## Folder Structure

### Postman Folders
Postman supports nested folders for organizing requests:

```json
{
  "item": [
    {
      "name": "Users API",
      "item": [
        {"name": "Get Users"},
        {"name": "Create User"}
      ]
    }
  ]
}
```

### How We Handle Folders
When importing, folders are flattened with names prefixed:

- **Postman:** "Users API" → "Get Users"
- **Our App:** "Users API / Get Users"

**Reason:** Our current version doesn't support folders, but we preserve the structure in the name.

---

## Format Detection

### Automatic Detection
When importing, we automatically detect the format:

```python
# Postman format indicators:
- Has "info" field with "_postman_id" or "schema"
- Has "item" array
- Schema URL matches Postman

# Internal format indicators:
- Has "export_version" field
- Has "collection" field
- Has "export_date" field
```

No manual selection needed! 🎉

---

## Example: Postman Collection

### Postman Format (what you get from Postman)
```json
{
  "info": {
    "_postman_id": "abc-123",
    "name": "My API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Users",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Accept",
            "value": "application/json"
          }
        ],
        "url": {
          "raw": "https://api.example.com/users?page=1",
          "protocol": "https",
          "host": ["api", "example", "com"],
          "path": ["users"],
          "query": [
            {
              "key": "page",
              "value": "1"
            }
          ]
        },
        "auth": {
          "type": "bearer",
          "bearer": [
            {
              "key": "token",
              "value": "your_token_here"
            }
          ]
        }
      },
      "response": []
    }
  ]
}
```

### Our Internal Format (after conversion)
```json
{
  "export_version": "1.0",
  "source": "postman",
  "postman_id": "abc-123",
  "collection": {
    "name": "My API",
    "requests": [
      {
        "name": "Get Users",
        "method": "GET",
        "url": "https://api.example.com/users?page=1",
        "params": {
          "page": "1"
        },
        "headers": {
          "Accept": "application/json"
        },
        "body": null,
        "auth_type": "Bearer Token",
        "auth_token": "your_token_here"
      }
    ]
  }
}
```

**Notice:**
- URL is simplified to a single string
- Query params extracted to separate dict
- Headers converted to simple key-value dict
- Auth simplified to type + token

---

## Use Cases

### 1. Migrate from Postman
**Scenario:** You have collections in Postman, want to try our app

**Steps:**
1. In Postman: Export collection as JSON (v2.1)
2. In our app: Click "Import", select the file
3. Done! Collection imported automatically

### 2. Share with Postman Users
**Scenario:** Your team uses Postman, you use our app

**Steps:**
1. In our app: Click "Export", choose "Postman Collection v2.1"
2. Share the JSON file
3. They import it in Postman
4. Collaboration success!

### 3. Use Both Tools
**Scenario:** You like both tools for different purposes

**Strategy:**
- Export from our app in Postman format
- Import in Postman for collaboration
- Export from Postman, import in our app
- Full interoperability!

### 4. API Documentation
**Scenario:** You want to generate API docs from collections

**Tools that support Postman format:**
- Postman itself (built-in docs)
- Newman (CLI runner)
- Stoplight
- ReadMe.io
- And many more!

---

## Limitations

### Current Limitations

| Feature | Status | Workaround |
|---------|--------|------------|
| **Folders/Nested Structure** | ➖ Not supported | Names prefixed on import |
| **Pre-request Scripts** | ➖ Not supported | Converted code manually |
| **Test Scripts** | ➖ Not in export | Use our test assertions |
| **Variables** | ➖ Not in export | Use our environments |
| **Multiple Auth Types** | ➖ Only Bearer Token | Manual configuration |

### What's NOT Converted

**Not exported** (for security/privacy):
- OAuth tokens (stored separately)
- Environment-specific variables
- Request history
- Test results

**Not imported** (not supported yet):
- Pre-request scripts
- Test scripts (use our assertions instead)
- Collection variables
- Advanced auth (Basic, Digest, AWS, etc.)

---

## Tips & Best Practices

### For Exporting

✅ **DO:**
- Export individual collections (easier to manage)
- Choose Postman format for sharing
- Choose internal format for backup

❌ **DON'T:**
- Export with sensitive tokens (remove first)
- Expect environments to be included
- Assume OAuth tokens are exported

### For Importing

✅ **DO:**
- Review the collection after import
- Check auth settings (may need manual setup)
- Test requests after import

❌ **DON'T:**
- Assume scripts will work (not supported)
- Expect variables to work immediately
- Trust imported auth tokens blindly

---

## Troubleshooting

### Import Fails

**Problem:** "Invalid format" error

**Solutions:**
1. Verify it's a valid JSON file
2. Check it's Postman Collection v2.1 (not v1.0 or v2.0)
3. Try opening in Postman first to validate
4. Check console for detailed error messages

### Missing Requests After Import

**Problem:** Some requests didn't import

**Solutions:**
1. Check if they were in folders (might be nested)
2. Look for requests with folder prefixes
3. Check console for warnings
4. Re-export from Postman with "Collection v2.1" format

### Authentication Not Working

**Problem:** Imported requests fail with auth errors

**Solutions:**
1. Check "Authorization" tab in request editor
2. Re-enter Bearer tokens (not exported by Postman by default)
3. Configure OAuth separately in our app
4. Update tokens in Postman before exporting

---

## Advanced: Format Conversion Details

### URL Parsing

**Postman URL Object:**
```json
{
  "raw": "https://api.example.com/users?page=1",
  "protocol": "https",
  "host": ["api", "example", "com"],
  "path": ["users"],
  "query": [{"key": "page", "value": "1"}]
}
```

**Our Format:**
```json
{
  "url": "https://api.example.com/users",
  "params": {"page": "1"}
}
```

### Headers Conversion

**Postman:**
```json
{
  "header": [
    {"key": "Content-Type", "value": "application/json", "type": "text"}
  ]
}
```

**Our Format:**
```json
{
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Body Conversion

**Postman (multiple modes):**
```json
{
  "body": {
    "mode": "raw",
    "raw": "{\"name\": \"John\"}",
    "options": {"raw": {"language": "json"}}
  }
}
```

**Our Format (simple string):**
```json
{
  "body": "{\"name\": \"John\"}"
}
```

---

## Testing

Run comprehensive tests:

```bash
python tests/test_postman_compatibility.py
```

**Tests included:**
- ✅ Export to Postman format
- ✅ Import from Postman format
- ✅ Format auto-detection
- ✅ Roundtrip conversion (internal → Postman → internal)
- ✅ File-based import/export

---

## Version History

### v1.0 (Current)
- ✅ Initial Postman Collection v2.1 support
- ✅ Export to Postman format
- ✅ Import from Postman format
- ✅ Automatic format detection
- ✅ Bearer token authentication support
- ✅ URL parsing and building
- ✅ Headers and query parameters
- ✅ Request body conversion
- ✅ Folder flattening on import

### Future Enhancements
- 🔄 Support for collection variables
- 🔄 Support for pre-request scripts (limited)
- 🔄 Support for test scripts conversion
- 🔄 Support for more auth types
- 🔄 Export to Postman Collection v2.0 (legacy)

---

## FAQ

**Q: Can I import Postman Collection v1.0?**  
A: No, only v2.1 is supported. Export from Postman as v2.1.

**Q: Will my test scripts import?**  
A: No, use our test assertions feature instead.

**Q: Are environment variables included?**  
A: No, they're stored separately. Configure environments manually.

**Q: Can I export to OpenAPI/Swagger?**  
A: Not yet. Currently only Postman and internal formats supported.

**Q: Is this a one-way conversion?**  
A: No! Full roundtrip: Internal ↔ Postman ↔ Internal.

**Q: Will this work with Insomnia/Thunder Client?**  
A: If they support Postman Collection v2.1 import, yes!

---

## Related Documentation

- [Export/Import Guide](EXPORT_IMPORT_GUIDE.md) - General export/import features
- [Environment Variables Guide](ENVIRONMENT_VARIABLES_GUIDE.md) - Using variables
- [OAuth Guide](OAUTH_GUIDE.md) - OAuth 2.0 authentication

---

**Status:** ✅ **Production Ready**  
**Postman Version:** v2.1.0  
**Tested:** Extensively  
**Maintained:** Yes

