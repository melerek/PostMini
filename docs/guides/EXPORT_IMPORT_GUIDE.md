# Export/Import Collections - User Guide

## Overview

The Export/Import feature allows you to:
- 📤 **Export** collections (with all requests) to JSON files
- 📥 **Import** collections from JSON files
- 🤝 **Share** API configurations with your team
- 💾 **Backup** your collections
- 🔄 **Transfer** collections between installations

## Features

✅ **Complete Export** - Exports collection with all requests, params, headers, body, and auth  
✅ **Variable Preservation** - Environment variables like `{{baseUrl}}` are preserved  
✅ **Duplicate Handling** - Smart handling when importing collections with existing names  
✅ **Validation** - Comprehensive validation of imported data  
✅ **Safe Filenames** - Automatically generates valid filenames with timestamps  

---

## How to Export a Collection

### Step 1: Select Collection
1. In the left panel, **click on a collection** (not a request)
2. The collection will be highlighted

### Step 2: Export
1. Click the **"Export"** button in the left panel
2. A "Save File" dialog will appear
3. **Choose where to save** the JSON file
4. The default filename includes collection name and timestamp
5. Click **"Save"**

### Step 3: Success!
- You'll see a success message
- The JSON file is now saved
- Share it with your team via email, Slack, Git, etc.

---

## How to Import a Collection

### Step 1: Import
1. Click the **"Import"** button in the left panel
2. A "Open File" dialog will appear
3. **Select the JSON file** to import
4. Click **"Open"**

### Step 2: Handle Duplicates
You'll see a dialog asking what to do if the collection name already exists:

**Options:**
- **YES** - Rename the imported collection (e.g., "My API (imported 1)")
- **NO** - Skip the import
- **CANCEL** - Cancel the import

### Step 3: Success!
- The collection will appear in your collections list
- All requests will be imported with full configuration
- The imported collection will be automatically selected

---

## JSON File Format

### Structure
```json
{
  "export_version": "1.0",
  "export_date": "2025-10-13T18:58:37.580226",
  "collection": {
    "name": "My API Collection",
    "requests": [
      {
        "name": "Get Users",
        "method": "GET",
        "url": "{{baseUrl}}/users",
        "params": {"limit": "10"},
        "headers": {"Authorization": "Bearer {{token}}"},
        "body": null,
        "auth_type": "None",
        "auth_token": null
      }
    ]
  }
}
```

### Fields Explanation

**Collection Level:**
- `export_version` - Format version (for future compatibility)
- `export_date` - When the export was created
- `collection.name` - Name of the collection
- `collection.requests` - Array of all requests

**Request Level:**
- `name` - Request name
- `method` - HTTP method (GET, POST, PUT, DELETE, etc.)
- `url` - Request URL (can contain variables)
- `params` - Query parameters as key-value pairs (can be null)
- `headers` - Request headers as key-value pairs (can be null)
- `body` - Request body text (can be null)
- `auth_type` - Authentication type ("None" or "Bearer Token")
- `auth_token` - Authentication token (can be null)

---

## Use Cases

### 1. Team Collaboration

**Scenario:** Share your API collection with teammates

**Steps:**
1. Export your collection → `my_api.json`
2. Share file via Slack/Email/Git
3. Teammate imports the file
4. Both have identical configurations!

**Benefits:**
- Everyone uses the same endpoints
- Consistent request configurations
- Easy onboarding for new team members

### 2. Backup & Restore

**Scenario:** Backup your collections before making changes

**Steps:**
1. Export all important collections
2. Store in safe location (Git, cloud storage)
3. Make changes to your collections
4. If something goes wrong, import the backup
5. You're back to the previous state!

**Benefits:**
- Protection against accidental deletions
- Version control for API configurations
- Easy rollback if needed

### 3. Environment Setup

**Scenario:** Set up collections on a new machine

**Steps:**
1. On old machine: Export all collections
2. Transfer files to new machine
3. On new machine: Install app and import files
4. All collections restored!

**Benefits:**
- Quick setup on new machines
- Consistent development environment
- No manual recreation needed

### 4. Collection Templates

**Scenario:** Create reusable API templates

**Steps:**
1. Create a collection with common endpoints
2. Use variables for flexibility: `{{baseUrl}}`, `{{apiKey}}`
3. Export as template
4. Share template with team
5. Each person imports and sets their own variables

**Benefits:**
- Standardized API structure
- Reusable across projects
- Easy customization per user

### 5. Version Control Integration

**Scenario:** Track API configurations in Git

**Steps:**
1. Create a `collections/` directory in your repo
2. Export collections to this directory
3. Commit to Git
4. Team pulls from Git
5. Import collections from local files

**Benefits:**
- API configurations versioned with code
- Track changes over time
- Code review for API changes
- CI/CD integration possible

---

## Best Practices

### ✅ DO:

1. **Use Descriptive Names**
   - Good: "Production API - User Service"
   - Bad: "API", "Test", "Collection1"

2. **Use Environment Variables**
   - Export: `{{baseUrl}}/users`
   - Instead of: `https://specific-domain.com/users`
   - Reason: Works across different environments

3. **Export Regularly**
   - Before major changes
   - Weekly backups
   - Before sharing with team

4. **Organize Exports**
   - Create a `collections/` folder
   - Use version numbers: `my_api_v1.json`, `my_api_v2.json`
   - Include dates in filenames

5. **Document Your Collections**
   - Add comments in request names
   - Use clear, descriptive names
   - Group related requests together

### ❌ DON'T:

1. **Don't Export Sensitive Data in Filenames**
   - Bad: `production_api_key_12345.json`
   - Good: `production_api.json`

2. **Don't Commit Production Secrets**
   - Use variables for sensitive data
   - Set actual values in environments (not in collections)

3. **Don't Share Personal Configs**
   - Remove personal API keys before sharing
   - Use variables instead of hardcoded values

4. **Don't Overwrite Without Backup**
   - Always backup before importing
   - Use "rename" option when importing

---

## Troubleshooting

### Issue: Import Failed - "Invalid JSON"

**Cause:** File is corrupted or not valid JSON

**Solution:**
1. Open file in text editor
2. Check for syntax errors
3. Validate JSON at jsonlint.com
4. Re-export the collection

### Issue: Import Failed - "Collection already exists"

**Cause:** Collection with same name exists

**Solution:**
1. Choose "YES" to rename on import
2. Or delete existing collection first
3. Or rename the collection in JSON file before importing

### Issue: Exported File Missing Requests

**Cause:** Collection was empty or export failed

**Solution:**
1. Verify collection has requests
2. Check file size (should be > 100 bytes)
3. Re-export the collection
4. Check disk space

### Issue: Variables Not Substituting After Import

**Cause:** Environment not selected

**Solution:**
1. Variables are preserved in JSON
2. Select appropriate environment from toolbar
3. Variables will substitute when sending requests

### Issue: Can't Find Export Button

**Cause:** No collection selected

**Solution:**
1. Click on a collection (not a request)
2. Export button should be enabled
3. It's in the second row of buttons in left panel

---

## File Format Compatibility

### Current Version: 1.0

**Supported Features:**
- Collection name
- Requests with all properties
- Environment variables in URLs, headers, params, body
- Bearer token authentication
- JSON request bodies
- Query parameters
- Custom headers

**Future Versions:**
- Pre-request scripts (coming soon)
- Test assertions (coming soon)
- Environment export/import (coming soon)
- Multiple collections in one file (already supported!)

---

## Advanced Tips

### Tip 1: Batch Export/Import

**Export all collections at once:**
```python
# Use the API
from database import DatabaseManager
from collection_io import CollectionExporter

db = DatabaseManager()
exporter = CollectionExporter(db)
exporter.export_all_collections_to_file("all_collections.json")
```

### Tip 2: Edit JSON Manually

You can manually edit the JSON file:
1. Export collection
2. Open in text editor
3. Modify URLs, add variables, update names
4. Save file
5. Import modified version

### Tip 3: Merge Collections

To combine multiple collections:
1. Export collection A
2. Export collection B
3. Manually merge JSON files
4. Create new collection structure
5. Import merged file

### Tip 4: Git Integration

Store in Git repository:
```bash
# Add to .gitignore if sensitive data
echo "api_client.db" >> .gitignore

# Store collections
mkdir collections
# Export to collections/
git add collections/
git commit -m "Add API collections"
```

---

## Security Considerations

### 🔒 What's Exported:

- Collection name
- Request configurations
- URLs (may contain variables)
- Headers (may contain auth tokens!)
- Query parameters
- Request bodies
- Auth tokens (if used)

### ⚠️ Security Warnings:

1. **Auth Tokens**: Exported files may contain authentication tokens
2. **API Keys**: Headers may include API keys
3. **Sensitive URLs**: URLs may reveal internal infrastructure
4. **Request Bodies**: May contain sensitive test data

### 🛡️ Recommendations:

1. **Use Variables**: `{{apiKey}}` instead of actual keys
2. **Review Before Sharing**: Check file for sensitive data
3. **Team-Only Files**: Only share with trusted team members
4. **Encrypt if Needed**: Use file encryption for sensitive exports
5. **Don't Commit Secrets**: Use .gitignore for files with secrets

---

## Examples

### Example 1: Basic Export/Import

```
1. Select "GitHub API" collection
2. Click "Export"
3. Save as "github_api_20251013.json"
4. Share with teammate
5. Teammate clicks "Import"
6. Select file
7. Choose "Rename if exists"
8. Done! Collection imported
```

### Example 2: Using with Environment Variables

**Before Export:**
```
Collection: "My API"
Request: "Get Users"
URL: {{baseUrl}}/users
Headers: Authorization: Bearer {{token}}
```

**After Import:**
```
Same structure preserved!
Set environment variables:
- baseUrl: https://api.example.com
- token: your-token-here

Requests work immediately!
```

### Example 3: Team Onboarding

**Setup:**
1. Senior dev creates "Company API" collection
2. Adds all endpoints with variables
3. Exports to "company_api_template.json"
4. Stores in shared drive

**New Developer:**
1. Installs API client
2. Imports "company_api_template.json"
3. Creates personal environment
4. Sets their own API keys
5. Ready to work in 2 minutes!

---

## FAQ

**Q: Can I export multiple collections at once?**  
A: Currently, you export one at a time through the UI. See Advanced Tips for batch export.

**Q: Can I import the same file multiple times?**  
A: Yes! Use the "rename" option to create multiple copies.

**Q: Are environment variables included in the export?**  
A: No. Environments are separate. Variables in requests (like `{{baseUrl}}`) are preserved, but you need to create matching environments after import.

**Q: What happens if I import a huge collection?**  
A: The import process is efficient. Collections with 100+ requests import quickly.

**Q: Can I share files via cloud storage?**  
A: Yes! Google Drive, Dropbox, OneDrive all work great.

**Q: Is there a file size limit?**  
A: No practical limit. JSON files are typically small (a few KB).

**Q: Can I import Postman collections?**  
A: Not directly. The format is different. You'd need to convert the JSON structure.

---

## Support

Having issues? Check:
1. This guide
2. README.md - Main documentation
3. BUGFIXES.md - Known issues and fixes
4. Test files - See examples in `test_import_export.py`

---

**Happy Exporting & Importing! 🚀**

