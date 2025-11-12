# Environment Import/Export Guide

## Overview

PostMini now supports **full import/export compatibility with Postman Environment Format**, enabling seamless migration and sharing of environment configurations between PostMini and Postman.

**Key Features:**
- ✅ Export environments to Postman format
- ✅ Import Postman environments automatically
- ✅ Automatic format detection
- ✅ Secret variable handling
- ✅ Bulk import/export operations
- ✅ Full bidirectional compatibility

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Export Environments](#export-environments)
3. [Import Environments](#import-environments)
4. [Format Comparison](#format-comparison)
5. [Secret Variables](#secret-variables)
6. [Bulk Operations](#bulk-operations)
7. [Use Cases](#use-cases)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Export an Environment

1. Open the **Environments** panel (🌍 icon in left sidebar)
2. Select an environment from the list
3. Click **📤 Export** button
4. Choose format: **Internal** or **Postman Environment**
5. Choose secret handling: **Include values** or **Replace with placeholders**
6. Select save location
7. Done! ✅

### Import an Environment

1. Open the **Environments** panel
2. Click **📥 Import** button
3. Select JSON file (format is auto-detected)
4. Environment is imported automatically
5. Done! ✅

---

## Export Environments

### Step-by-Step Export Process

#### 1. Select Environment

Navigate to the Environments panel and select the environment you want to export.

#### 2. Choose Export Format

When you click **Export**, you'll see a dialog with two format options:

**Internal Format (PostMini)**
- Native PostMini format
- Optimized for PostMini features
- Includes metadata
- Recommended for PostMini-to-PostMini sharing

**Postman Environment Format**
- Industry-standard Postman format
- Compatible with Postman and other API tools
- Recommended for cross-tool sharing
- Follows Postman schema specification

#### 3. Handle Secret Variables

Choose how to handle sensitive variables (those containing keywords like `key`, `token`, `password`, `secret`, `auth`):

**Include actual values**
- Exports with real secret values
- Use when exporting for personal backups
- ⚠️ Be careful not to commit to version control

**Replace with placeholders**
- Replaces secret values with `{{SECRET_variableName}}`
- Safe for sharing with team members
- Recipients can add their own secret values

#### 4. Save File

Choose a location and filename. File will be saved as `.json`.

### Export All Environments

To export all environments at once:

1. Use the bulk export feature in the Git Sync module
2. All environments will be exported to individual files
3. Choose format for all environments

---

## Import Environments

### Automatic Format Detection

PostMini automatically detects whether your JSON file is:
- **Postman Environment Format** (has `_postman_variable_scope` field)
- **Internal Format** (has `environment` nested structure)

No need to specify the format - just import!

### Import Process

1. Click **📥 Import** button
2. Select JSON file
3. PostMini will:
   - Detect the format automatically
   - Validate the structure
   - Convert if needed
   - Handle duplicate names
   - Import variables

### Handling Duplicate Names

If an environment with the same name already exists:

**Default Behavior (Create New)**
- Creates new environment with modified name
- Example: "Production" becomes "Production (1)"
- Original environment is preserved

**Update Existing (via bulk import)**
- Updates existing environment's variables
- Merges with existing variables
- Use when syncing updates

### Disabled Variables

Postman supports enabled/disabled variables. When importing:
- **Enabled variables** → Imported normally
- **Disabled variables** → Imported with `_DISABLED_` prefix
- You can manually remove the prefix to enable them

---

## Format Comparison

### Postman Environment Format

```json
{
  "id": "abc123-def456-ghi789",
  "name": "Production Environment",
  "values": [
    {
      "key": "baseUrl",
      "value": "https://api.example.com",
      "enabled": true,
      "type": "default"
    },
    {
      "key": "apiKey",
      "value": "secret123",
      "enabled": true,
      "type": "secret"
    },
    {
      "key": "debugMode",
      "value": "false",
      "enabled": false,
      "type": "default"
    }
  ],
  "_postman_variable_scope": "environment",
  "_postman_exported_at": "2025-11-12T10:00:00.000Z",
  "_postman_exported_using": "Postman/10.0"
}
```

**Structure:**
- `id`: Unique identifier (UUID)
- `name`: Environment name
- `values`: Array of variable objects
  - `key`: Variable name
  - `value`: Variable value
  - `enabled`: Whether variable is active
  - `type`: "default" or "secret"
- `_postman_variable_scope`: Always "environment"
- `_postman_exported_at`: Export timestamp
- `_postman_exported_using`: Tool version

### PostMini Internal Format

```json
{
  "export_version": "1.0",
  "export_date": "2025-11-12T10:00:00",
  "environment": {
    "id": 1,
    "name": "Production Environment",
    "variables": {
      "baseUrl": "https://api.example.com",
      "apiKey": "secret123"
    }
  }
}
```

**Structure:**
- `export_version`: Format version
- `export_date`: Export timestamp
- `environment`: Nested environment object
  - `id`: Database ID (internal)
  - `name`: Environment name
  - `variables`: Simple key-value object

**Key Differences:**
- PostMini uses simple key-value pairs
- Postman uses array of objects
- Postman supports enabled/disabled per variable
- Postman has explicit secret types
- PostMini infers secrets from variable names

---

## Secret Variables

### Secret Detection

PostMini automatically detects secret variables based on keywords in the variable name:

**Keywords:**
- `secret`
- `key`
- `token`
- `password`
- `auth`
- `api_key` / `apikey`
- `credential`
- `private`
- `sensitive`

**Examples:**
- `apiKey` → Marked as secret ✅
- `authToken` → Marked as secret ✅
- `secretValue` → Marked as secret ✅
- `baseUrl` → Not a secret ❌
- `timeout` → Not a secret ❌

### Exporting Secrets

#### With Actual Values

```json
{
  "key": "apiKey",
  "value": "sk_live_abc123xyz",
  "type": "secret"
}
```

**Use when:**
- Creating personal backups
- Transferring to your own machines
- Not sharing with others

#### With Placeholders

```json
{
  "key": "apiKey",
  "value": "{{SECRET_apiKey}}",
  "type": "secret"
}
```

**Use when:**
- Sharing with team members
- Committing to Git repositories
- Creating templates
- Public documentation

### Importing Secrets

When importing environments with secret placeholders:
1. Environment is imported with placeholder values
2. Go to Variables panel
3. Replace placeholders with actual values
4. Save changes

---

## Bulk Operations

### Export All Environments

To export all environments at once:

```python
# Using the API
from src.features.environment_io import EnvironmentExporter

exporter = EnvironmentExporter(db)
success_count, total = exporter.export_all_environments_to_directory(
    "/path/to/export/folder",
    format='postman',
    include_secrets=False
)
```

**Via UI:**
- Currently available through Git Sync module
- Exports all environments to configured directory
- Individual files per environment

### Import Multiple Environments

To import all JSON files from a directory:

```python
# Using the API
from src.features.environment_io import EnvironmentImporter

importer = EnvironmentImporter(db)
success_count, total, messages = importer.import_environments_from_directory(
    "/path/to/import/folder"
)
```

**File Naming:**
- Each environment exports to `EnvironmentName.json`
- Special characters replaced with underscores
- Spaces replaced with underscores

---

## Use Cases

### 1. Migrate from Postman to PostMini

**Scenario:** You have environments in Postman and want to use PostMini.

**Steps:**
1. In Postman: Select environment → Export
2. Save JSON file
3. In PostMini: Environments panel → Import
4. Select the JSON file
5. Done! ✅

**Result:** All variables imported, secrets detected automatically.

### 2. Share Environment with Postman Users

**Scenario:** Your team uses Postman, you use PostMini.

**Steps:**
1. In PostMini: Select environment → Export
2. Choose "Postman Environment Format"
3. Choose "Replace with placeholders" for secrets
4. Share the JSON file
5. Team imports in Postman
6. They add their own secret values

**Result:** Team collaboration across tools! 🤝

### 3. Backup All Environments

**Scenario:** Create a backup of all your environments.

**Steps:**
1. Use bulk export to directory
2. Choose "Internal Format" for PostMini
3. Choose "Include actual values"
4. Store in secure location (not Git!)

**Result:** Complete backup with all secrets.

### 4. Environment Templates

**Scenario:** Create reusable environment templates.

**Steps:**
1. Create environment with common variables
2. Export with "Replace with placeholders"
3. Share template with team
4. Each person imports and fills in their values

**Result:** Standardized environment structure.

### 5. Multi-Environment Setup

**Scenario:** Set up Development, Staging, Production environments.

**Steps:**
1. Export Production environment
2. Import 3 times
3. Rename to Dev, Staging, Production
4. Update URLs and credentials per environment

**Result:** Quick multi-environment setup.

---

## Troubleshooting

### Import Failed: Invalid JSON

**Problem:** File is not valid JSON.

**Solutions:**
- Verify file is proper JSON format
- Check for trailing commas
- Use JSON validator (jsonlint.com)
- Ensure file encoding is UTF-8

### Import Failed: Invalid Postman Environment

**Problem:** File doesn't match Postman schema.

**Causes:**
- Missing required fields (`_postman_variable_scope`, `name`, `values`)
- Invalid variable scope (must be "environment")
- Values is not an array

**Solution:**
- Check error message for specific field
- Compare with example format above
- Validate against Postman schema

### Variables Not Showing

**Problem:** Imported environment has no variables.

**Solutions:**
- Check if original file had variables
- Verify variables array in JSON
- Check if variables were disabled in Postman
- Look for `_DISABLED_` prefix in variable names

### Secret Values Missing

**Problem:** Secret variables show placeholders.

**Cause:** Environment was exported with "Replace with placeholders" option.

**Solution:**
- This is expected behavior for shared environments
- Go to Variables panel
- Replace `{{SECRET_variableName}}` with actual values
- Save changes

### Duplicate Environment Names

**Problem:** Environment already exists with that name.

**Behavior:**
- Import creates new environment with modified name
- Example: "Production" → "Production (1)"

**Solutions:**
- Accept the new name
- Manually rename after import
- Delete old environment before importing
- Use bulk import with `update_existing=True`

### Export Button Disabled

**Problem:** Can't click Export button.

**Cause:** No environment selected.

**Solution:**
- Click on an environment in the list to select it
- Selected environment will be highlighted
- Export button will become enabled

---

## API Reference

### EnvironmentExporter

```python
from src.features.environment_io import EnvironmentExporter

exporter = EnvironmentExporter(db)

# Export single environment
data = exporter.export_environment(
    environment_id=1,
    format='postman',  # or 'internal'
    include_secrets=True
)

# Export to file
success = exporter.export_environment_to_file(
    environment_id=1,
    file_path='/path/to/file.json',
    format='postman',
    include_secrets=False
)

# Export all environments
environments = exporter.export_all_environments(
    format='postman',
    include_secrets=False
)

# Export all to directory
success_count, total = exporter.export_all_environments_to_directory(
    directory_path='/path/to/folder',
    format='postman',
    include_secrets=False
)
```

### EnvironmentImporter

```python
from src.features.environment_io import EnvironmentImporter

importer = EnvironmentImporter(db)

# Import from dictionary
success, message, env_id = importer.import_environment(
    environment_data=data,
    update_existing=False
)

# Import from file (auto-detects format)
success, message, env_id = importer.import_environment_from_file(
    file_path='/path/to/file.json',
    update_existing=False
)

# Import multiple from directory
success_count, total, messages = importer.import_environments_from_directory(
    directory_path='/path/to/folder',
    update_existing=False
)

# Detect format
format_type = importer.detect_format(data)  # Returns 'postman' or 'internal'
```

### PostmanEnvironmentConverter

```python
from src.features.postman_environment_converter import PostmanEnvironmentConverter

# Convert to Postman format
postman_data = PostmanEnvironmentConverter.to_postman_format(
    environment_data=internal_data,
    include_secrets=True
)

# Convert from Postman format
internal_data = PostmanEnvironmentConverter.from_postman_format(
    postman_data=postman_data
)

# Check format
is_postman = PostmanEnvironmentConverter.is_postman_format(data)

# Validate Postman environment
is_valid, error_message = PostmanEnvironmentConverter.validate_postman_environment(data)

# Count variables
count = PostmanEnvironmentConverter.get_variable_count(data)
```

---

## Best Practices

### 1. Never Commit Secrets to Git

```bash
# ❌ DON'T: Export with actual secret values to Git
git add environments/production.json  # Contains real secrets!

# ✅ DO: Export with placeholders for Git
# Export → Replace with placeholders
git add environments/production.json  # Safe to commit
```

### 2. Use Descriptive Variable Names

```javascript
// ❌ BAD: Unclear names
url1, url2, key1

// ✅ GOOD: Clear, descriptive names
baseUrl, apiUrl, authToken, apiKey
```

### 3. Organize by Environment Type

```
environments/
├── development.json
├── staging.json
├── production.json
└── testing.json
```

### 4. Document Required Variables

Create a README for your environments:

```markdown
# Required Environment Variables

## Development
- `baseUrl`: API base URL (http://localhost:3000)
- `apiKey`: Development API key (get from admin)
- `timeout`: Request timeout in ms (5000)

## Production
- `baseUrl`: Production API URL (https://api.example.com)
- `apiKey`: Production API key (⚠️ SECRET - get from vault)
- `timeout`: Request timeout in ms (10000)
```

### 5. Regular Backups

- Export environments weekly
- Store in secure location
- Include actual values in personal backups
- Use placeholders for shared backups

### 6. Version Control Strategy

```bash
# Commit templates (no secrets)
git add environments/*.template.json

# Ignore actual environment files
echo "environments/*.json" >> .gitignore
echo "!environments/*.template.json" >> .gitignore
```

---

## Examples

### Example 1: Basic Export/Import

```python
# Export from PostMini
from src.features.environment_io import EnvironmentExporter

exporter = EnvironmentExporter(db)
exporter.export_environment_to_file(
    environment_id=1,
    file_path='my_environment.json',
    format='postman'
)

# Import to another PostMini instance
from src.features.environment_io import EnvironmentImporter

importer = EnvironmentImporter(db2)
success, msg, env_id = importer.import_environment_from_file(
    'my_environment.json'
)
print(f"Import result: {msg}")
```

### Example 2: Team Sharing

```python
# Developer 1: Export for team (without secrets)
exporter.export_environment_to_file(
    environment_id=1,
    file_path='team_environment.json',
    format='postman',
    include_secrets=False  # Replace with placeholders
)

# Developer 2: Import and verify
importer = EnvironmentImporter(db)
success, msg, env_id = importer.import_environment_from_file(
    'team_environment.json'
)

# Developer 2: Add their own secrets via UI
# Variables panel → Replace {{SECRET_apiKey}} → Save
```

### Example 3: Bulk Migration

```python
# Export all from Postman (manual step in Postman UI)
# Then import all to PostMini:

importer = EnvironmentImporter(db)
success_count, total, messages = importer.import_environments_from_directory(
    'postman_exports/'
)

print(f"Imported {success_count}/{total} environments")
for msg in messages:
    print(msg)
```

---

## Related Documentation

- [Variables Guide](./VARIABLES_GUIDE.md) - Managing variables in PostMini
- [Postman Compatibility Guide](./POSTMAN_COMPATIBILITY_GUIDE.md) - Collection import/export
- [Git Sync Guide](./GIT_SYNC_GUIDE.md) - Version control for API collections

---

## Version History

### v1.9.0 (Current)
- ✅ Initial Postman Environment Format support
- ✅ Export to Postman format
- ✅ Import from Postman format
- ✅ Automatic format detection
- ✅ Secret variable detection and handling
- ✅ Bulk import/export operations
- ✅ Disabled variable support
- ✅ Duplicate name handling
- ✅ Full validation

### Future Enhancements
- 🔄 Environment variables in collections export
- 🔄 Global variables support
- 🔄 Environment templates library
- 🔄 Variable validation rules
- 🔄 Environment diff viewer

---

## Support

**Need help?**
- Check [Troubleshooting](#troubleshooting) section
- Review [Examples](#examples)
- Open an issue on GitHub
- Check Postman's environment documentation

---

**Status:** ✅ **Production Ready**  
**Postman Compatibility:** Full (Environment Format)  
**Tested:** Extensively  
**Maintained:** Yes
