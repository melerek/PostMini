# Git Release Instructions for PostMini v1.8.6

This document provides step-by-step instructions for creating a GitHub release for PostMini v1.8.6.

---

## Prerequisites

Before creating a GitHub release, ensure you have:
- ✅ Built the application successfully (`dist/PostMini.exe`)
- ✅ Created the installer (`dist/installer/PostMini_Setup_v1.8.6.exe`)
- ✅ Calculated SHA256 checksum
- ✅ Updated `version.json` with correct checksum
- ✅ Committed all changes to Git
- ✅ Created and pushed tag `v1.8.6`

---

## Step 1: Navigate to GitHub Releases

1. Open your web browser
2. Go to your PostMini repository on GitHub:
   ```
   https://github.com/[YOUR_USERNAME]/PostMini
   ```
3. Click on **"Releases"** in the right sidebar (or repository menu)
4. Click the **"Draft a new release"** button

---

## Step 2: Fill Release Form Fields

### Tag Version
- **Field:** "Choose a tag"
- **Value:** `v1.8.6`
- **Action:** Select existing tag (pushed in Step 7.3 of BUILD_INSTRUCTIONS.md)
- **Note:** If tag doesn't appear, select "Create new tag" and enter `v1.8.6`

### Target Branch
- **Field:** "Target"
- **Value:** `main` (or your default branch)
- **Note:** This should be automatically selected

### Release Title
- **Field:** "Release title"
- **Value:** 
  ```
  PostMini v1.8.6 - Temporary Tabs & Keyboard Shortcuts
  ```

---

## Step 3: Write Release Description

Copy and paste the following markdown into the release description:

```markdown
## 🎯 PostMini v1.8.6

**Release Date:** November 6, 2025

A **polish and UX improvement release** focusing on refined UI elements, better keyboard accessibility, and enhanced user workflows.

---

## ✨ What's New

### 🆕 Temporary Tabs (Preview Mode)
- **Single-click** opens requests in temporary tab (italic, auto-closes)
- **Double-click** opens in permanent tab
- Similar to VS Code's file preview behavior
- More efficient tab management for large collections

### ⌨️ Keyboard Shortcuts for Panel Toggles
Quick access to all panels:
- **Alt+C** - Collections
- **Alt+E** - Environments  
- **Alt+V** - Variables
- **Alt+G** - Git Sync
- **Alt+H** - History
- **Alt+R** - Recent Requests

### 📋 History Panel as Overlay
- Right-side overlay panel (non-blocking)
- 800px wide with smooth animations
- Filter by status, view details, replay requests
- Keyboard shortcut: **Alt+H**

### 🔧 Add Collection Variables
- Add variables directly to collections from Variables panel
- Dropdown menu on "+ Add" button
- Streamlined variable management workflow

---

## 🎨 UI/UX Improvements

### Tab Header Width Optimization
- Tighter tabs with better space usage
- More tabs visible simultaneously
- ~8px space from edge to text

### Modernized "Recent" Button
- Changed from emoji 🕐 to text "Recent"
- Fixed hover cutoff issue
- Matches "New request" button style

### Simplified Tooltips
All panel tooltips now show shortcuts:
- Example: "Collections [Alt+C]"
- Cleaner, more informative

### Removed Bullet Separator
- Tab labels: "GET New Request" (was "GET • New Request")
- More space for request names

---

## 🐛 Bug Fixes

- ✅ Fixed Recent button hover cutoff
- ✅ Improved signal blocking during request load
- ✅ History and Recent panels now mutually exclusive

---

## 📥 Installation

### New Installation
1. Download `PostMini_Setup_v1.8.6.exe`
2. Run the installer
3. Follow the setup wizard
4. Launch PostMini from Start Menu

### Upgrade from Previous Version
1. Download `PostMini_Setup_v1.8.6.exe`
2. Run the installer (it will detect existing installation)
3. Your data is automatically preserved:
   - ✅ All collections
   - ✅ All requests
   - ✅ All environments
   - ✅ All settings
   - ✅ All history

---

## 📋 Full Details

For comprehensive release notes, see [V1.8.6 Release Notes](https://github.com/[YOUR_USERNAME]/PostMini/blob/main/docs/release_notes/V1.8.6_RELEASE_NOTES.md)

For complete changelog, see [CHANGELOG.md](https://github.com/[YOUR_USERNAME]/PostMini/blob/main/CHANGELOG.md)

---

## 🔒 Checksum Verification

**SHA256:** `[PASTE_YOUR_CHECKSUM_HERE]`

To verify:
```powershell
Get-FileHash -Path "PostMini_Setup_v1.8.6.exe" -Algorithm SHA256
```

---

## 💬 Feedback & Support

- 🐛 Found a bug? [Open an issue](https://github.com/[YOUR_USERNAME]/PostMini/issues)
- 💡 Have a suggestion? [Start a discussion](https://github.com/[YOUR_USERNAME]/PostMini/discussions)
- ⭐ Enjoying PostMini? Give us a star!

---

**Happy Testing! 🚀**

*PostMini Team*
```

**Important:** Replace `[YOUR_USERNAME]` with your actual GitHub username!

---

## Step 4: Upload Release Assets

### 4.1 Add the Installer
1. Scroll down to **"Attach binaries by dropping them here or selecting them"**
2. Click or drag-and-drop: `dist/installer/PostMini_Setup_v1.8.6.exe`
3. Wait for upload to complete (may take a few minutes depending on file size)

### 4.2 Add Release Notes (Optional)
You can also attach the release notes document:
1. Click "Attach binaries" again
2. Select: `docs/release_notes/V1.8.6_RELEASE_NOTES.md`
3. Wait for upload

### 4.3 Verify Uploads
Ensure you see:
- ✅ `PostMini_Setup_v1.8.6.exe` (installer)
- ✅ `V1.8.6_RELEASE_NOTES.md` (optional documentation)

---

## Step 5: Configure Release Options

### Set as Latest Release
- ✅ Check **"Set as the latest release"**
  - This makes v1.8.6 the default download
  - Updates the "latest" badge
  - Shows at the top of releases page

### Pre-release (Optional)
- ☐ Leave **"Set as a pre-release"** unchecked
  - This is a stable release, not a beta/RC

### Create Discussion (Optional)
- ☑️ Check **"Create a discussion for this release"**
  - Automatically creates a discussion thread
  - Good for collecting feedback
  - Recommended for major releases

---

## Step 6: Publish the Release

### 6.1 Save as Draft (Recommended)
1. Click **"Save draft"** button
2. Review everything one more time:
   - Tag: `v1.8.6`
   - Title correct
   - Description properly formatted
   - Installer uploaded
   - Checksum added
   - Links working

### 6.2 Publish
1. Once everything looks good, click **"Publish release"**
2. GitHub will:
   - Make the release public
   - Send notifications to watchers
   - Create a discussion (if enabled)
   - Update the releases page

---

## Step 7: Update version.json (CRITICAL!)

After publishing the release, you **must** update `version.json` with the actual download URL:

### 7.1 Get the Download URL
The URL format will be:
```
https://github.com/[YOUR_USERNAME]/PostMini/releases/download/v1.8.6/PostMini_Setup_v1.8.6.exe
```

### 7.2 Update version.json
Edit `version.json` and update:
```json
{
  "latest_version": "1.8.6",
  "release_date": "2025-11-06",
  "download_url": "https://github.com/[YOUR_USERNAME]/PostMini/releases/download/v1.8.6/PostMini_Setup_v1.8.6.exe",
  "changelog_url": "https://github.com/[YOUR_USERNAME]/PostMini/releases/tag/v1.8.6",
  "checksum": "sha256:YOUR_ACTUAL_CHECKSUM_HERE",
  ...
}
```

### 7.3 Commit and Push
```powershell
git add version.json
git commit -m "Update version.json with v1.8.6 release info and checksum"
git push origin main
```

**Important:** This step enables the auto-update feature to work correctly!

---

## Step 8: Verify the Release

### 8.1 Check Release Page
1. Visit: `https://github.com/[YOUR_USERNAME]/PostMini/releases`
2. Verify:
   - ✅ v1.8.6 shows as "Latest"
   - ✅ Title is correct
   - ✅ Description renders properly
   - ✅ Installer is downloadable
   - ✅ File size is correct

### 8.2 Test Download
1. Click on `PostMini_Setup_v1.8.6.exe` to download
2. Verify file downloads correctly
3. Check file size matches original
4. Verify checksum matches:
   ```powershell
   Get-FileHash -Path "Downloads\PostMini_Setup_v1.8.6.exe" -Algorithm SHA256
   ```

### 8.3 Test Auto-Update (If Applicable)
1. Open PostMini v1.8.5 (previous version)
2. Go to Settings → Check for Updates
3. Verify it detects v1.8.6
4. Test the update download

---

## Step 9: Announce the Release (Optional)

### On GitHub
- Pin the release discussion (if created)
- Respond to comments and questions

### Social Media / Community
Share the release on your platforms:
- Twitter/X
- Reddit (r/programming, r/webdev, etc.)
- Dev.to blog post
- LinkedIn
- Discord/Slack communities

### Sample Announcement:
```
🎉 PostMini v1.8.6 is here!

New features:
• Temporary tabs (preview mode)
• Keyboard shortcuts for panels (Alt+C/E/V/G/H/R)
• History panel as overlay
• Collection variable management

Download: [link]
Release Notes: [link]

#PostMini #APITesting #OpenSource
```

---

## Troubleshooting

### Tag Already Exists
- **Problem:** Tag `v1.8.6` exists but with different content
- **Solution:** 
  ```powershell
  git tag -d v1.8.6                    # Delete local tag
  git push origin --delete v1.8.6     # Delete remote tag
  git tag -a v1.8.6 -m "..."          # Recreate tag
  git push origin v1.8.6               # Push new tag
  ```

### Upload Failed
- **Problem:** Installer upload times out
- **Solution:** 
  - Check internet connection
  - Try uploading again
  - If persistent, use GitHub CLI: `gh release upload v1.8.6 PostMini_Setup_v1.8.6.exe`

### Wrong Version Number
- **Problem:** Used wrong version in title/description
- **Solution:**
  - Click "Edit release"
  - Update the information
  - Click "Update release"

### Checksum Doesn't Match
- **Problem:** Downloaded file has different checksum
- **Solution:**
  - Recalculate checksum of uploaded file
  - Update version.json
  - Edit release description with correct checksum

---

## Post-Release Checklist

After publishing the release, ensure:

- ☑️ Release is visible on GitHub
- ☑️ Installer is downloadable
- ☑️ Checksum verified
- ☑️ version.json updated and pushed
- ☑️ Auto-update works
- ☑️ Links in description work
- ☑️ Discussion created (if enabled)
- ☑️ Announcement posted (if applicable)

---

## Summary: GitHub Release Form Fields

Quick reference for the release form:

| Field | Value |
|-------|-------|
| **Tag** | `v1.8.6` |
| **Target** | `main` |
| **Title** | `PostMini v1.8.6 - Temporary Tabs & Keyboard Shortcuts` |
| **Description** | See Step 3 above (markdown content) |
| **Assets** | `PostMini_Setup_v1.8.6.exe` |
| **Latest Release** | ✅ Checked |
| **Pre-release** | ☐ Unchecked |
| **Discussion** | ✅ Checked (recommended) |

---

## Additional Resources

- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**Release Complete! 🎉**

Your PostMini v1.8.6 release is now live and available for download!

Users will be able to:
- Download from GitHub Releases
- Auto-update from within the app (once version.json is pushed)
- View detailed release notes
- Verify installer integrity with checksum

Great work! 👏


