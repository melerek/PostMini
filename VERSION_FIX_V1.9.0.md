# PostMini v1.9.0 - Version Number Fix

## Critical Bug Fixed

**Problem:** After installing PostMini v1.9.0, the application was still showing version 1.8.6 in Settings and other UI elements.

**Root Cause:** Version numbers were hardcoded in multiple source code files and were not updated during the release preparation. While the installer metadata and version.json were correct, the actual Python code still contained old version strings.

## Files Updated

### 1. main.py (Line 178)
- **Before:** `app.setApplicationVersion("1.8.2")`
- **After:** `app.setApplicationVersion("1.9.0")`
- **Impact:** Qt application metadata now shows correct version

### 2. src/features/auto_updater.py (Line 26)
- **Before:** `CURRENT_VERSION = "1.8.6"`
- **After:** `CURRENT_VERSION = "1.9.0"`
- **Impact:** Auto-update system correctly identifies current version

### 3. src/ui/widgets/settings_panel.py (Line 20)
- **Before:** `APP_VERSION = "1.8.6"`
- **After:** `APP_VERSION = "1.9.0"`
- **Impact:** Settings panel displays correct version

## Rebuild Process

1. ✅ Updated all 3 version strings in source code
2. ✅ Rebuilt application with PyInstaller (111 seconds)
3. ✅ Rebuilt installer with Inno Setup (45 seconds)
4. ✅ Calculated new SHA256 checksum: `BC035504BC33D5EAE379BE470E0A26E51FBF4421E5A20165D60B89688776EE86`
5. ✅ Updated version.json with new checksum

## New Installer Details

- **File:** `PostMini_Setup_v1.9.0.exe`
- **Location:** `dist\installer\PostMini_Setup_v1.9.0.exe`
- **SHA256:** `BC035504BC33D5EAE379BE470E0A26E51FBF4421E5A20165D60B89688776EE86`
- **Size:** ~125 MB (compressed)

## Next Steps for User

1. **Commit version.json Changes:**
   ```bash
   git add version.json
   git commit -m "Update checksum for rebuilt v1.9.0 installer with correct version numbers"
   git push origin main
   ```

2. **Update GitHub Release:**
   - Go to https://github.com/MarMil97/PostMini/releases/tag/v1.9.0
   - Delete the old `PostMini_Setup_v1.9.0.exe` file
   - Upload the new `PostMini_Setup_v1.9.0.exe` from `dist\installer\`
   - Save the release

3. **Verify Installation:**
   - Download the new installer from GitHub
   - Install PostMini
   - Open the app and go to Settings
   - Verify it shows version **1.9.0**
   - Check Help → About dialog also shows **1.9.0**

4. **Test Auto-Update:**
   - If you have v1.8.6 installed, launch it
   - It should detect v1.9.0 is available
   - Download and verify checksum passes
   - Install and verify version is correct

## Verification Checklist

- [ ] version.json committed to GitHub with new checksum
- [ ] New installer uploaded to GitHub release
- [ ] Fresh install shows v1.9.0 in Settings
- [ ] Fresh install shows v1.9.0 in About dialog
- [ ] Auto-update from v1.8.6 detects v1.9.0
- [ ] Auto-update checksum verification passes
- [ ] Auto-update installs correctly and shows v1.9.0

## Lessons Learned

### Version Management Best Practices

1. **Centralize Version Definitions**
   - Consider creating a single `version.py` file with:
     ```python
     __version__ = "1.9.0"
     ```
   - Import from all other files to ensure consistency

2. **Pre-Release Checklist**
   - Add version number audit to release checklist
   - Search codebase for hardcoded version strings before building
   - Verify installed app shows correct version before publishing

3. **Automated Version Updates**
   - Consider a script to update all version references at once
   - Could parse version from git tags or a central config file

### Files That Need Version Updates

For future releases, update these files:
- `main.py` - Application metadata
- `src/features/auto_updater.py` - Auto-update version check
- `src/ui/widgets/settings_panel.py` - Settings UI display
- `installer.iss` - Installer metadata
- `version.json` - Auto-update server data
- `CHANGELOG.md` - Release notes

## Technical Notes

- PyInstaller packages the Python source files as-is
- Installer metadata (from installer.iss) only affects installer appearance
- The actual version shown in the app comes from the Python source code
- Auto-update mechanism compares `CURRENT_VERSION` constant with `version.json`
- All three version locations must be synchronized for correct behavior

## Build Time

- PyInstaller rebuild: ~111 seconds
- Inno Setup rebuild: ~45 seconds
- Total rebuild time: ~156 seconds

## Date/Time

- **Fix Applied:** 2025-01-13
- **Rebuild Completed:** 2025-01-13
- **Release Ready:** Pending user upload to GitHub

---

**Status:** ✅ **FIXED AND READY FOR DEPLOYMENT**

The installer now correctly contains version 1.9.0 in all locations and will display the correct version when installed.
