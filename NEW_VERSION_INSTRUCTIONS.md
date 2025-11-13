# NEW VERSION RELEASE INSTRUCTIONS FOR AI AGENT

## 📋 Complete Checklist for Releasing a New Version

This document provides a comprehensive, step-by-step guide for preparing and releasing a new version of PostMini. Follow these steps in order to ensure a successful release without missing any version updates.

---

## 🎯 Pre-Release Preparation

### Step 1: Version Number Decision
- [ ] Determine new version number (e.g., 1.9.2, 1.10.0, 2.0.0)
- [ ] Follow semantic versioning: MAJOR.MINOR.PATCH
  - MAJOR: Breaking changes
  - MINOR: New features, backward compatible
  - PATCH: Bug fixes, backward compatible

### Step 2: Update CHANGELOG.md
- [ ] Move features from `[Unreleased]` section to new version section
- [ ] Add release date: `[X.Y.Z] - YYYY-MM-DD`
- [ ] Include all changes:
  - ✨ New features
  - 🐛 Bug fixes
  - 🔧 Technical improvements
  - 📚 Documentation updates
  - ⚠️ Breaking changes (if any)

---

## 🔢 Version Number Updates - CRITICAL!

**⚠️ IMPORTANT:** There are **FIVE** files that contain version numbers. ALL must be updated!

### Step 3: Update version.json
**File:** `version.json`
- [ ] Update `latest_version` to new version (e.g., "1.9.2")
- [ ] Update `release_date` to current date (YYYY-MM-DD format)
- [ ] Update `download_url` to point to new version tag
- [ ] Update `changelog_url` to point to new version tag
- [ ] Update `release_notes` array with new features
- [ ] **Note:** `checksum`, `exe_sha256`, and `installer_sha256` will be updated later after building

**Example:**
```json
{
  "latest_version": "1.9.2",
  "release_date": "2025-11-14",
  "download_url": "https://github.com/melerek/PostMini/releases/download/v1.9.2/PostMini_Setup_v1.9.2.exe",
  "changelog_url": "https://github.com/melerek/PostMini/releases/tag/v1.9.2",
  ...
}
```

### Step 4: Update main.py
**File:** `main.py` (around line 178)
- [ ] Find: `app.setApplicationVersion("X.Y.Z")`
- [ ] Update to new version number
- [ ] This controls the version shown in the application title bar

**Example:**
```python
app.setApplicationVersion("1.9.2")
```

### Step 5: Update installer.iss
**File:** `installer.iss` (line 5)
- [ ] Find: `#define MyAppVersion "X.Y.Z"`
- [ ] Update to new version number
- [ ] This controls the installer file name and version metadata

**Example:**
```
#define MyAppVersion "1.9.2"
```

### Step 6: Update auto_updater.py ⚠️ CRITICAL - OFTEN MISSED!
**File:** `src/features/auto_updater.py` (around line 26)
- [ ] Find: `CURRENT_VERSION = "X.Y.Z"`
- [ ] Update to new version number
- [ ] **This is the version the auto-update checker uses to compare against latest**
- [ ] **If not updated, users will always see update notifications!**

**Example:**
```python
CURRENT_VERSION = "1.9.2"  # Should match installer version
```

### Step 7: Update settings_panel.py ⚠️ CRITICAL - OFTEN MISSED!
**File:** `src/ui/widgets/settings_panel.py` (around line 20)
- [ ] Find: `APP_VERSION = "X.Y.Z"`
- [ ] Update to new version number
- [ ] **This is the version shown in the Settings panel**
- [ ] **If not updated, Settings will show wrong version!**

**Example:**
```python
APP_VERSION = "1.9.2"  # Current application version
```

### Step 8: Update README.md
**File:** `README.md`
- [ ] Find version badge (usually near the top)
- [ ] Update version number in badge URL
- [ ] Update "What's New" section with new features

**Example:**
```markdown
![Version](https://img.shields.io/badge/version-1.9.2-blue.svg)
```

---

## 🔨 Build Process

### Step 9: Clean Previous Builds
- [ ] Delete `build/` directory if it exists
- [ ] Delete `dist/` directory if it exists
- [ ] This ensures a clean build without artifacts from previous versions

**Command:**
```powershell
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
```

### Step 10: Build Application with PyInstaller
- [ ] Run PyInstaller with the build specification
- [ ] Verify build completes successfully
- [ ] Check for any warnings or errors
- [ ] Verify `dist\PostMini\PostMini.exe` exists

**Command:**
```powershell
python -m PyInstaller build_installer.spec --clean --noconfirm
```

**Expected output:**
- Build should complete in 60-100 seconds
- Should show "Build complete!" message
- Executable created at: `dist\PostMini\PostMini.exe`

### Step 11: Calculate Executable SHA256
- [ ] Calculate SHA256 checksum for `PostMini.exe`
- [ ] **Save this value** - you'll need it for version.json and documentation

**Command:**
```powershell
Get-FileHash -Path "dist\PostMini\PostMini.exe" -Algorithm SHA256
```

**Example output:**
```
Algorithm: SHA256
Hash: 4A50A158B0F8698673D952E0A5176EA9A301C7D5B35D6B88CEFA8773EEFD0635
```

### Step 12: Build Installer with Inno Setup
- [ ] Run Inno Setup compiler with installer script
- [ ] Verify compilation completes successfully
- [ ] Check for any warnings (minor warnings are usually OK)
- [ ] Verify `dist\installer\PostMini_Setup_vX.Y.Z.exe` exists

**Command:**
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

**Expected output:**
- Compilation should complete in 60-80 seconds
- Should show "Successful compile" message
- Installer created at: `dist\installer\PostMini_Setup_vX.Y.Z.exe`

### Step 13: Calculate Installer SHA256
- [ ] Calculate SHA256 checksum for the installer
- [ ] **Save this value** - you'll need it for version.json and documentation

**Command:**
```powershell
Get-FileHash -Path "dist\installer\PostMini_Setup_v1.9.2.exe" -Algorithm SHA256
```

**Example output:**
```
Algorithm: SHA256
Hash: BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A
```

---

## 🔐 Update Checksums

### Step 14: Update version.json with SHA256 Checksums
- [ ] Open `version.json`
- [ ] Update `checksum` field with **installer SHA256** (with "sha256:" prefix)
- [ ] Update `exe_sha256` field with **executable SHA256** (no prefix)
- [ ] Update `installer_sha256` field with **installer SHA256** (no prefix)
- [ ] **All three fields must match the checksums calculated above**

**Example:**
```json
{
  "checksum": "sha256:BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A",
  "exe_sha256": "4A50A158B0F8698673D952E0A5176EA9A301C7D5B35D6B88CEFA8773EEFD0635",
  "installer_sha256": "BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A"
}
```

---

## 📝 Version Verification - DOUBLE CHECK!

### Step 15: Verify All Version Numbers Match
Before committing, verify these **6 files** all have the **SAME version number**:

- [ ] `version.json` - "latest_version" field
- [ ] `main.py` - `app.setApplicationVersion()`
- [ ] `installer.iss` - `#define MyAppVersion`
- [ ] `src/features/auto_updater.py` - `CURRENT_VERSION`
- [ ] `src/ui/widgets/settings_panel.py` - `APP_VERSION`
- [ ] `README.md` - version badge

**Verification Commands:**
```powershell
# Quick grep to find all version strings
grep -r "1.9.2" version.json main.py installer.iss src/features/auto_updater.py src/ui/widgets/settings_panel.py README.md
```

**⚠️ CRITICAL:** If even ONE file has the wrong version, the auto-update system will malfunction!

---

## 💾 Git Commit and Tag

### Step 16: Stage Files for Commit
- [ ] Stage all modified version files
- [ ] Stage CHANGELOG.md
- [ ] Stage version.json with checksums
- [ ] Do NOT stage build outputs (dist/, build/)

**Command:**
```powershell
git add version.json main.py installer.iss README.md CHANGELOG.md src/features/auto_updater.py src/ui/widgets/settings_panel.py
```

**Optional:** Add any other changed files (documentation, features, fixes)

### Step 17: Commit Changes
- [ ] Create a detailed commit message
- [ ] Include version number in commit message
- [ ] List key changes
- [ ] Include SHA256 checksums in commit message for reference

**Command:**
```powershell
git commit -m "Release vX.Y.Z: [Brief Description]

- Updated version numbers across all files
- Updated CHANGELOG.md with release notes
- Rebuilt application and installer
- Updated version.json with SHA256 checksums:
  * exe_sha256: [EXECUTABLE_SHA256]
  * installer_sha256: [INSTALLER_SHA256]

Key changes:
- [Feature 1]
- [Feature 2]
- [Bug fix 1]"
```

### Step 18: Create Git Tag
- [ ] Create annotated tag with version number
- [ ] Include release notes in tag message
- [ ] Include SHA256 checksums in tag message

**Command:**
```powershell
git tag -a vX.Y.Z -m "Version X.Y.Z: [Brief Description]

Key Features:
- [Feature 1]
- [Feature 2]

Bug Fixes:
- [Fix 1]
- [Fix 2]

SHA256 Checksums:
- Executable: [EXECUTABLE_SHA256]
- Installer: [INSTALLER_SHA256]"
```

### Step 19: Push to GitHub
- [ ] Push commits to main branch
- [ ] Push the new tag
- [ ] Verify both appear on GitHub

**Commands:**
```powershell
git push origin main
git push origin vX.Y.Z
```

**Verification:**
- Check GitHub commits: https://github.com/melerek/PostMini/commits/main
- Check GitHub tags: https://github.com/melerek/PostMini/tags

---

## 📄 Prepare GitHub Release Documentation

### Step 20: Create Release Description Document
- [ ] Create a markdown file with full release description
- [ ] Include feature highlights
- [ ] Include bug fixes
- [ ] Include SHA256 checksums for verification
- [ ] Include installation instructions
- [ ] Include upgrade instructions

**Suggested filename:** `GITHUB_RELEASE_vX.Y.Z.md`

**Template structure:**
1. Release title and version
2. Feature highlights with emojis
3. Bug fixes
4. Technical details
5. SHA256 checksums (both installer and executable)
6. Installation instructions
7. Upgrade instructions
8. Auto-update information
9. Changelog link
10. Support information

---

## 🚀 Create GitHub Release

### Step 21: Navigate to GitHub Releases Page
- [ ] Go to: https://github.com/melerek/PostMini/releases/new
- [ ] Or click "Create a new release" from releases page

### Step 22: Configure Release Settings
- [ ] Select tag: `vX.Y.Z` (should be available from push)
- [ ] Target: `main` branch
- [ ] Release title: `PostMini vX.Y.Z: [Brief Feature Description]`
- [ ] Description: Copy from release documentation markdown file

### Step 23: Upload Installer Binary
- [ ] Click "Attach binaries by dropping them here or selecting them"
- [ ] Upload: `dist\installer\PostMini_Setup_vX.Y.Z.exe`
- [ ] Wait for upload to complete
- [ ] Verify file appears in Assets section

### Step 24: Release Options
- [ ] ✅ Check: "Set as the latest release"
- [ ] ✅ Check: "Create a discussion for this release" (category: Announcements)
- [ ] ⬜ Leave unchecked: "Set as a pre-release" (unless this is a beta/RC)

### Step 25: Publish Release
- [ ] Review all information one final time
- [ ] Click "Publish release" button
- [ ] Wait for release to be created

---

## ✅ Post-Release Verification

### Step 26: Verify Release is Live
- [ ] Go to: https://github.com/melerek/PostMini/releases
- [ ] Verify new release appears at the top
- [ ] Verify release is marked as "Latest"
- [ ] Click on release and verify all information is correct

### Step 27: Verify Installer Download
- [ ] Click on installer file in release assets
- [ ] Verify download starts
- [ ] Verify downloaded file size is reasonable (should be ~80-120 MB)

### Step 28: Verify SHA256 Checksum
- [ ] Download the installer from GitHub release
- [ ] Calculate its SHA256 checksum
- [ ] Verify it matches the checksum in version.json
- [ ] Verify it matches the checksum in release description

**Command:**
```powershell
Get-FileHash -Path "Downloads\PostMini_Setup_vX.Y.Z.exe" -Algorithm SHA256
```

### Step 29: Verify Auto-Update Configuration
- [ ] Check version.json on GitHub main branch
- [ ] Verify "latest_version" is correct
- [ ] Verify "download_url" points to the new release
- [ ] Verify all three checksum fields match
- [ ] GitHub URL should be: `https://raw.githubusercontent.com/melerek/PostMini/main/version.json`

### Step 30: Test Fresh Installation
- [ ] Download installer from GitHub release (not from local dist/)
- [ ] Run installer on a clean test machine (or VM)
- [ ] Complete installation wizard
- [ ] Launch PostMini
- [ ] Verify version in title bar shows: vX.Y.Z
- [ ] Go to Settings tab
- [ ] Verify Settings panel shows: "Version X.Y.Z"
- [ ] Click "Check for Updates" button
- [ ] Should show: "PostMini X.Y.Z is the latest version"

### Step 31: Test Auto-Update from Previous Version (Optional)
If you have access to the previous version:
- [ ] Install previous version (e.g., v1.9.0)
- [ ] Launch application
- [ ] Wait for auto-update notification (may take a few seconds)
- [ ] Verify notification shows new version number
- [ ] Verify notification shows release notes
- [ ] Click "Download Update" button
- [ ] Verify download URL is correct
- [ ] Verify downloaded file matches SHA256 checksum

---

## 📊 Post-Release Monitoring

### Step 32: Monitor for Issues (First 24 Hours)
- [ ] Check GitHub Issues for new bug reports
- [ ] Check GitHub Discussions for user feedback
- [ ] Monitor download count on release page
- [ ] Watch for Windows SmartScreen warnings (users may report)
- [ ] Check for any auto-update failures

### Step 33: Update Documentation (If Needed)
- [ ] Update project README if major features added
- [ ] Update user guides if UI changed significantly
- [ ] Update API documentation if public APIs changed
- [ ] Create blog post or announcement (optional)

---

## 🚨 Emergency Rollback Procedure

If critical issues are discovered after release:

### Option 1: Mark as Pre-Release (Stops Auto-Update)
1. Go to release page on GitHub
2. Click "Edit release"
3. Check "Set as a pre-release"
4. Click "Update release"
5. This prevents auto-update notifications to users

### Option 2: Revert version.json (Stops New Downloads)
1. Edit version.json in main branch
2. Revert "latest_version" to previous stable version
3. Revert checksums to previous version
4. Commit and push changes
5. This stops auto-update system from recommending broken version

### Option 3: Create Hotfix Release
1. Create new branch from broken release tag
2. Fix the critical bug
3. Increment PATCH version (e.g., 1.9.2 → 1.9.3)
4. Follow this entire checklist for the hotfix version
5. Mark previous broken release as pre-release
6. Publish hotfix as latest release

---

## 📋 Quick Reference - Files to Update

| # | File Path | What to Update | Example |
|---|-----------|---------------|---------|
| 1 | `version.json` | `latest_version`, URLs, `release_notes` | "1.9.2" |
| 2 | `main.py` | `app.setApplicationVersion()` | "1.9.2" |
| 3 | `installer.iss` | `#define MyAppVersion` | "1.9.2" |
| 4 | `src/features/auto_updater.py` | `CURRENT_VERSION` | "1.9.2" |
| 5 | `src/ui/widgets/settings_panel.py` | `APP_VERSION` | "1.9.2" |
| 6 | `README.md` | Version badge, What's New | v1.9.2 |
| 7 | `CHANGELOG.md` | New version section | [1.9.2] - 2025-11-14 |

---

## 🎯 Common Mistakes to Avoid

### ❌ Mistake 1: Forgetting auto_updater.py or settings_panel.py
**Impact:** Auto-update shows wrong current version, always notifies about updates
**Solution:** Always update ALL 6 files listed above

### ❌ Mistake 2: Not updating version.json checksums after rebuild
**Impact:** Auto-update checksum verification fails, users can't install
**Solution:** Always rebuild → calculate checksums → update version.json

### ❌ Mistake 3: Typos in version numbers across files
**Impact:** Inconsistent version display, broken auto-update
**Solution:** Copy-paste version number, use verification step

### ❌ Mistake 4: Uploading wrong installer file
**Impact:** Users get old version, checksums don't match
**Solution:** Always upload from `dist\installer\`, verify filename has correct version

### ❌ Mistake 5: Forgetting to push Git tag
**Impact:** GitHub release can't find the tag, release creation fails
**Solution:** Always `git push origin vX.Y.Z` after creating tag

### ❌ Mistake 6: Not testing fresh download
**Impact:** Release may work from local build but fail from GitHub
**Solution:** Always download installer from GitHub and test it

---

## 🤖 AI Agent Notes

When executing this checklist:

1. **Work step-by-step** - Don't skip ahead, each step depends on previous steps
2. **Verify each change** - Double-check version numbers before moving on
3. **Save checksums immediately** - Write down SHA256 values when calculated
4. **Test before publishing** - Build locally, verify it works before creating release
5. **Keep user informed** - Provide progress updates after each major step
6. **Document any issues** - If something fails, note it for future improvements

---

## 📞 Support and Issues

If you encounter issues following this checklist:
- Check recent Git commits for examples: https://github.com/melerek/PostMini/commits/main
- Review closed releases: https://github.com/melerek/PostMini/releases
- Check issues labeled "release": https://github.com/melerek/PostMini/issues?q=label%3Arelease

---

**Document Version:** 1.0  
**Last Updated:** November 13, 2025  
**Based on:** v1.9.1 release experience and lessons learned
