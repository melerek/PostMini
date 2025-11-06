# Auto-Update System Setup Guide

## Overview

PostMini now includes an automatic update system that checks GitHub for new releases and allows users to download and install updates with one click.

## Architecture

```
┌──────────────┐     Check version.json    ┌─────────────────┐
│   PostMini   │ ───────────────────────>  │ GitHub (main)   │
│     App      │                            │  version.json   │
│              │ <─────────────────────────  └─────────────────┘
│              │    Download new installer            │
│              │                                      │
│              │     Get installer         ┌─────────▼────────┐
│              │ ─────────────────────────> │ GitHub Releases  │
└──────────────┘                            │   v1.8.3         │
       │                                    └──────────────────┘
       │ Run installer & restart
       ▼
┌──────────────┐
│   Updated    │
│   PostMini   │
└──────────────┘
```

## Features

✅ **Automatic Update Checking** - Checks on startup (configurable)  
✅ **Manual Update Check** - "Check for Updates" button in Settings  
✅ **Version Display** - Shows current version in Settings panel  
✅ **Download Progress** - Shows download progress with MB counter  
✅ **Background Download** - Downloads in separate thread  
✅ **Checksum Verification** - Verifies downloaded installer integrity  
✅ **Silent Install** - Can install silently or show wizard  
✅ **Settings Persistence** - Auto-check preference saved to database  

## Setup Instructions

### 1. Configure GitHub Repository

#### Update the Repository URL

Edit `src/features/auto_updater.py`:

```python
class UpdateChecker(QThread):
    # UPDATE THESE FOR YOUR REPOSITORY
    VERSION_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/postmini/main/version.json"
    CURRENT_VERSION = "1.8.3"  # Update this when releasing new versions
```

**Replace:**
- `YOUR_USERNAME` - Your GitHub username
- `YOUR_REPO_NAME` - Your repository name (e.g., "postmini")

### 2. Create version.json

Create a `version.json` file in the root of your GitHub repository:

```json
{
  "latest_version": "1.8.3",
  "release_date": "2025-11-06",
  "download_url": "https://github.com/yourusername/postmini/releases/download/v1.8.3/PostMini_Setup_v1.8.3.exe",
  "changelog_url": "https://github.com/yourusername/postmini/releases/tag/v1.8.3",
  "checksum": "sha256:abc123def456...",
  "min_version": "1.0.0",
  "critical": false,
  "release_notes": [
    "FIXED: Postman folder structure import",
    "Folders now import with proper hierarchy",
    "Clean request names without concatenation"
  ]
}
```

**Field Descriptions:**

- `latest_version` - The latest version number (semantic versioning)
- `release_date` - Release date in YYYY-MM-DD format
- `download_url` - Direct download URL to the installer on GitHub Releases
- `changelog_url` - URL to the release notes page
- `checksum` - SHA256 checksum of the installer (optional but recommended)
- `min_version` - Minimum version required before upgrading (for future use)
- `critical` - If true, shows a warning that this is a critical security update
- `release_notes` - Array of bullet points for what's new

### 3. Calculate Checksum (Optional but Recommended)

To generate the SHA256 checksum of your installer:

**PowerShell:**
```powershell
Get-FileHash .\PostMini_Setup_v1.8.3.exe -Algorithm SHA256
```

**Command Prompt (certutil):**
```cmd
certutil -hashfile PostMini_Setup_v1.8.3.exe SHA256
```

**Python:**
```python
import hashlib

def calculate_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"

checksum = calculate_checksum("PostMini_Setup_v1.8.3.exe")
print(checksum)
```

### 4. Commit version.json to GitHub

```bash
git add version.json
git commit -m "Add version manifest for auto-updates"
git push origin main
```

**Important:** This file must be in the `main` branch and accessible at:  
`https://raw.githubusercontent.com/yourusername/postmini/main/version.json`

## Release Workflow

When releasing a new version, follow these steps:

### Step 1: Update Version Numbers

Update the version in **3 places**:

1. **installer.iss**
   ```pascal
   #define MyAppVersion "1.9.0"
   ```

2. **src/features/auto_updater.py**
   ```python
   CURRENT_VERSION = "1.9.0"
   ```

3. **src/ui/widgets/settings_panel.py**
   ```python
   APP_VERSION = "1.9.0"
   ```

### Step 2: Build the Installer

```bash
# Build the executable
pyinstaller build_installer.spec --clean -y

# Create the installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

This creates: `dist/PostMini_Setup_v1.9.0.exe`

### Step 3: Calculate Checksum

```powershell
Get-FileHash .\dist\PostMini_Setup_v1.9.0.exe -Algorithm SHA256
```

Save the checksum for Step 5.

### Step 4: Create GitHub Release

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. **Tag:** `v1.9.0` (click "Create new tag")
4. **Title:** `PostMini v1.9.0 - [Feature Name]`
5. **Description:** Write your release notes (Markdown supported)
6. **Upload:** Drag and drop `PostMini_Setup_v1.9.0.exe`
7. Click "Publish release"

### Step 5: Update version.json

Update the version.json file in your repository:

```json
{
  "latest_version": "1.9.0",
  "release_date": "2025-11-07",
  "download_url": "https://github.com/yourusername/postmini/releases/download/v1.9.0/PostMini_Setup_v1.9.0.exe",
  "changelog_url": "https://github.com/yourusername/postmini/releases/tag/v1.9.0",
  "checksum": "sha256:YOUR_ACTUAL_CHECKSUM_HERE",
  "critical": false,
  "release_notes": [
    "NEW: Feature description",
    "IMPROVED: Performance enhancements",
    "FIXED: Bug fixes"
  ]
}
```

### Step 6: Commit and Push

```bash
git add version.json
git commit -m "Release v1.9.0"
git push origin main
```

### Step 7: Users Get Notified

Within 5 seconds of starting the app (if auto-check is enabled), users will see a notification that an update is available!

## User Experience

### Settings Panel

Users can find update settings in the **⚙️ Settings** panel:

- **Auto-Update Settings** - Toggle auto-check on startup
- **About PostMini** section shows:
  - Current version number
  - "Check for Updates" button
  - Update status (checking, available, up to date)

### Update Flow

1. **Notification:** User sees "Update Available" dialog
2. **Review:** User reviews release notes
3. **Download:** User clicks "Download & Install"
4. **Progress:** Download progress shown with MB counter
5. **Install:** User chooses to install now or later
6. **Restart:** App closes, installer runs, new version installed

### Silent Mode

On startup, the app silently checks for updates. If an update is available, it shows a dialog. If not, it doesn't bother the user.

## Testing

### Test with Mock version.json

Create a test version.json with a higher version number to test the update flow:

```json
{
  "latest_version": "99.99.99",
  "release_date": "2025-12-31",
  "download_url": "https://example.com/test.exe",
  "changelog_url": "https://example.com/",
  "checksum": "",
  "critical": false,
  "release_notes": [
    "TEST: This is a test update"
  ]
}
```

Temporarily update the `VERSION_URL` in `auto_updater.py` to point to your test JSON.

### Test Scenarios

1. ✅ **Update Available** - version.json has higher version
2. ✅ **No Update** - version.json has same or lower version
3. ✅ **Network Error** - version.json URL is unreachable
4. ✅ **Invalid JSON** - version.json has syntax errors
5. ✅ **Invalid Version** - version string is malformed
6. ✅ **Download Error** - Download URL is invalid
7. ✅ **Checksum Mismatch** - Downloaded file has wrong checksum
8. ✅ **Manual Check** - User clicks "Check for Updates" button
9. ✅ **Auto Check on Startup** - App checks on launch
10. ✅ **Settings Toggle** - User can disable auto-check

## Troubleshooting

### Update Check Fails

**Symptoms:** "Network error" or "Check failed" message

**Solutions:**
- Verify version.json URL is correct and accessible
- Check that version.json is in the main branch
- Ensure version.json has valid JSON syntax
- Check user's internet connection

### Download Fails

**Symptoms:** "Download failed" error

**Solutions:**
- Verify download_url in version.json is correct
- Ensure installer is uploaded to GitHub Release
- Check file size isn't corrupted

### Checksum Verification Fails

**Symptoms:** "Checksum verification failed" error

**Solutions:**
- Recalculate checksum for the uploaded installer
- Update checksum in version.json
- Ensure installer wasn't corrupted during upload

### Installer Won't Run

**Symptoms:** Installation fails after download

**Solutions:**
- Check Windows SmartScreen isn't blocking
- Verify user has admin permissions
- Ensure installer file isn't corrupted

## Advanced Configuration

### Custom Update Server

Instead of GitHub, you can host version.json on any server:

```python
VERSION_URL = "https://yourdomain.com/updates/version.json"
```

### Silent Installation

To skip the installer wizard:

```python
UpdateInstaller.install_update(installer_path, silent=True)
```

This runs: `PostMini_Setup.exe /VERYSILENT /CLOSEAPPLICATIONS`

### Critical Updates

For security patches, set `"critical": true` in version.json to show a warning badge.

### Version Skipping

Users can click "Remind Me Later" to skip an update. They'll be reminded again next launch.

## Security Considerations

1. **HTTPS Only** - Always use HTTPS for version.json and downloads
2. **Checksums** - Always provide SHA256 checksums for verification
3. **Code Signing** - Consider signing the installer with a certificate
4. **GitHub Releases** - GitHub's CDN is reliable and secure
5. **No Auto-Install** - Users must confirm before installation

## Future Enhancements

Potential improvements for the future:

- **Delta Updates** - Only download changed files
- **Rollback** - Allow reverting to previous version
- **Release Channels** - Stable vs Beta updates
- **Update History** - Show past releases
- **Notification Badge** - Show update icon in toolbar
- **Background Download** - Download while app is running
- **Auto-Install** - Install on next launch without prompt

## Support

If users encounter issues with updates:

1. Check GitHub Release is published and installer is uploaded
2. Verify version.json is accessible at the correct URL
3. Ensure version numbers follow semantic versioning (X.Y.Z)
4. Test the update flow yourself before announcing

---

## Quick Reference

### Files to Update on Each Release

| File | What to Update |
|------|----------------|
| `installer.iss` | `#define MyAppVersion "X.Y.Z"` |
| `src/features/auto_updater.py` | `CURRENT_VERSION = "X.Y.Z"` |
| `src/ui/widgets/settings_panel.py` | `APP_VERSION = "X.Y.Z"` |
| `version.json` (on GitHub) | All fields |

### PowerShell Release Script Example

Save this as `release.ps1`:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "Building PostMini v$Version..." -ForegroundColor Green

# Build
pyinstaller build_installer.spec --clean -y
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# Calculate checksum
$checksum = (Get-FileHash ".\dist\PostMini_Setup_v$Version.exe" -Algorithm SHA256).Hash
Write-Host "Checksum: sha256:$checksum" -ForegroundColor Yellow

# Copy to releases folder
New-Item -Path "releases" -ItemType Directory -Force
Copy-Item ".\dist\PostMini_Setup_v$Version.exe" -Destination "releases\"

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Create GitHub Release v$Version"
Write-Host "2. Upload: releases\PostMini_Setup_v$Version.exe"
Write-Host "3. Update version.json with checksum: sha256:$checksum"
Write-Host "4. Commit and push version.json"
```

Usage:
```powershell
.\release.ps1 -Version "1.9.0"
```

---

**Congratulations!** 🎉 Your app now has automatic updates! Users will always be on the latest version.

