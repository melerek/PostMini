# Build Instructions for PostMini v1.8.6

This document provides step-by-step instructions for building the PostMini application and creating the Windows installer.

---

## Prerequisites

### Required Software:
1. **Python 3.11+** - Installed and in PATH
2. **PyInstaller** - `pip install pyinstaller`
3. **Inno Setup 6** - Download from https://jrsoftware.org/isdl.php
4. **Git** - For version control and release management

### Verify Installation:
```powershell
python --version          # Should show Python 3.11+
pyinstaller --version    # Should show PyInstaller version
iscc                     # Should recognize Inno Setup Compiler
```

---

## Step 1: Prepare the Build Environment

### 1.1 Clean Previous Builds
```powershell
# Remove old build artifacts
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue

# Clean Python cache
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

### 1.2 Verify All Dependencies
```powershell
pip install -r requirements.txt
```

### 1.3 Verify Version Numbers
Ensure all version numbers are updated to **1.8.6**:
- ✅ `src/ui/widgets/settings_panel.py` - Line 20: `APP_VERSION = "1.8.6"`
- ✅ `src/features/auto_updater.py` - Line 26: `CURRENT_VERSION = "1.8.6"`
- ✅ `installer.iss` - Line 5: `#define MyAppVersion "1.8.6"`
- ✅ `version.json` - Line 2: `"latest_version": "1.8.6"`

---

## Step 2: Build the Application with PyInstaller

### 2.1 Run PyInstaller
```powershell
# Build using the spec file
pyinstaller build_installer.spec

# This will create:
# - dist/PostMini.exe (the executable)
# - build/ folder (intermediate files, can be deleted)
```

### 2.2 Verify the Build
```powershell
# Check that the executable was created
Test-Path dist\PostMini.exe  # Should return True

# Check file size (should be ~100-150 MB)
Get-Item dist\PostMini.exe | Select-Object Name, Length
```

### 2.3 Test the Executable
```powershell
# Run the application to verify it works
cd dist
.\PostMini.exe

# Test:
# - Application launches
# - UI displays correctly
# - Can create requests
# - Can send requests
# - Settings show version 1.8.6
```

---

## Step 3: Create the Windows Installer

### 3.1 Verify Inno Setup Script
Check that `installer.iss` is configured correctly:
- Version: `1.8.6`
- Output directory: `dist\installer`
- Source files: `dist\PostMini.exe` and resources

### 3.2 Compile the Installer
```powershell
# Navigate to project root
cd C:\Users\MariuszMilew_jstooze\Documents\WORK\Apps\PostmanAlternative

# Compile with Inno Setup
iscc installer.iss

# This will create:
# - dist/installer/PostMini_Setup_v1.8.6.exe
```

### 3.3 Verify the Installer
```powershell
# Check that installer was created
Test-Path dist\installer\PostMini_Setup_v1.8.6.exe  # Should return True

# Check file size (should be ~100-150 MB)
Get-Item dist\installer\PostMini_Setup_v1.8.6.exe | Select-Object Name, Length
```

---

## Step 4: Calculate Checksum

### 4.1 Calculate SHA256
```powershell
# Calculate checksum of the installer
$hash = Get-FileHash -Path "dist\installer\PostMini_Setup_v1.8.6.exe" -Algorithm SHA256
$hash.Hash

# Example output: 8A3F9B2E7C1D5A6F4E8B9C7D2A3F1E5B4C6D8A9F7E6C5B4A3D2E1F0C9B8A7E6
```

### 4.2 Update version.json
```powershell
# Copy the checksum from above
# Edit version.json and update the "checksum" field:
# "checksum": "sha256:YOUR_HASH_HERE"
```

---

## Step 5: Test the Installer

### 5.1 Test Installation (Optional)
**Note:** This will install PostMini on your system. Skip if you already have it installed.

```powershell
# Run the installer
.\dist\installer\PostMini_Setup_v1.8.6.exe

# Verify installation:
# - Installation wizard completes successfully
# - PostMini appears in Start Menu
# - Desktop shortcut created (if selected)
# - Uninstaller is registered in Windows
```

### 5.2 Test Upgrade (Recommended)
If you have a previous version installed:
```powershell
# Run the installer - it should detect the existing installation
.\dist\installer\PostMini_Setup_v1.8.6.exe

# Verify upgrade:
# - Installer detects previous version
# - Upgrade completes successfully
# - All data preserved (collections, environments, settings)
# - Version shows 1.8.6 in Settings
```

---

## Step 6: Prepare Release Assets

### 6.1 Organize Files
```powershell
# Create release folder
New-Item -ItemType Directory -Force -Path "release\v1.8.6"

# Copy installer
Copy-Item "dist\installer\PostMini_Setup_v1.8.6.exe" "release\v1.8.6\"

# Copy documentation
Copy-Item "docs\release_notes\V1.8.6_RELEASE_NOTES.md" "release\v1.8.6\"
Copy-Item "CHANGELOG.md" "release\v1.8.6\"
```

### 6.2 Create Release Notes File
The release notes are already in:
- `docs/release_notes/V1.8.6_RELEASE_NOTES.md`
- `CHANGELOG.md` (updated with v1.8.6 entry)

---

## Step 7: Commit and Push Changes

### 7.1 Stage All Changes
```powershell
# Add all modified and new files
git add src/ui/main_window.py
git add src/ui/widgets/variable_inspector_panel.py
git add src/ui/widgets/history_panel_widget.py
git add styles.qss
git add styles_dark.qss
git add src/ui/widgets/settings_panel.py
git add src/features/auto_updater.py
git add installer.iss
git add version.json
git add CHANGELOG.md
git add docs/release_notes/V1.8.6_RELEASE_NOTES.md
```

### 7.2 Commit
```powershell
git commit -m "Release v1.8.6: Temporary tabs, keyboard shortcuts, UI polish

- NEW: Temporary tabs (single-click preview, double-click permanent)
- NEW: Keyboard shortcuts for panels (Alt+C, E, V, G, H, R)
- NEW: History panel as overlay (Alt+H)
- NEW: Add collection variables from Variables panel
- IMPROVED: Tab widths optimized for better space usage
- IMPROVED: Modern 'Recent' button design  
- IMPROVED: Simplified tooltips with shortcuts
- FIXED: Recent button hover cutoff
- FIXED: Signal blocking during request load

See docs/release_notes/V1.8.6_RELEASE_NOTES.md for full details."
```

### 7.3 Create and Push Tag
```powershell
# Create annotated tag
git tag -a v1.8.6 -m "PostMini v1.8.6 - Temporary Tabs & Keyboard Shortcuts

Major improvements to UX and keyboard accessibility.
See V1.8.6_RELEASE_NOTES.md for full changelog."

# Push commits and tags
git push origin main
git push origin v1.8.6
```

---

## Summary of Build Outputs

After completing all steps, you should have:

```
PostmanAlternative/
├── dist/
│   ├── PostMini.exe                                    # Standalone executable
│   └── installer/
│       └── PostMini_Setup_v1.8.6.exe                  # Windows installer
├── release/
│   └── v1.8.6/
│       ├── PostMini_Setup_v1.8.6.exe                  # Ready for upload
│       ├── V1.8.6_RELEASE_NOTES.md                    # Release documentation
│       └── CHANGELOG.md                                # Full changelog
├── docs/release_notes/
│   └── V1.8.6_RELEASE_NOTES.md                        # Detailed release notes
└── version.json                                        # Updated with v1.8.6 info
```

---

## Troubleshooting

### PyInstaller Fails
- **Error:** Module not found
  - **Solution:** Run `pip install -r requirements.txt`
- **Error:** Spec file not found
  - **Solution:** Verify you're in the project root directory
- **Error:** Hidden imports missing
  - **Solution:** Add to `hiddenimports` in `build_installer.spec`

### Inno Setup Fails
- **Error:** Source file not found
  - **Solution:** Verify `dist/PostMini.exe` exists
- **Error:** Output directory error
  - **Solution:** Create `dist/installer/` manually
- **Error:** Permission denied
  - **Solution:** Run PowerShell as Administrator

### Application Won't Launch
- **Error:** Missing DLL
  - **Solution:** Install Microsoft Visual C++ Redistributable
- **Error:** Database error
  - **Solution:** Delete `%APPDATA%/PostMini/postmini.db` and restart
- **Error:** Qt platform plugin error
  - **Solution:** Ensure Qt DLLs are in the dist folder

---

## Next Steps

After successful build, proceed to:
1. **GitHub Release Creation** (see GIT_RELEASE_INSTRUCTIONS.md)
2. **Upload installer to GitHub Releases**
3. **Update version.json checksum**
4. **Push version.json to repository**
5. **Announce release**

---

**Build completed successfully! 🎉**

The installer is ready for distribution at:
`dist/installer/PostMini_Setup_v1.8.6.exe`


