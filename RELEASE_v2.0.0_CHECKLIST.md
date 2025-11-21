# PostMini v2.0.0 Release Checklist

## ✅ Version Updates (COMPLETED)

All version numbers have been updated to **2.0.0** in:
- ✅ `version.json` - latest_version, URLs (checksums need to be calculated after build)
- ✅ `main.py` - setApplicationVersion("2.0.0")
- ✅ `installer.iss` - MyAppVersion "2.0.0"
- ✅ `src/features/auto_updater.py` - CURRENT_VERSION = "2.0.0"
- ✅ `src/ui/widgets/settings_panel.py` - APP_VERSION = "2.0.0"
- ✅ `README.md` - Version badge updated
- ✅ `CHANGELOG.md` - v2.0.0 entry added with all features
- ✅ `docs/POSTMINI_VS_POSTMAN_COMPARISON.md` - Version and date updated
- ✅ `GITHUB_RELEASE_v2.0.0.md` - Created for easy copy-paste to GitHub

## 📦 Build Process

### 1. Clean Previous Builds
```powershell
Remove-Item -Path "build","dist" -Recurse -Force -ErrorAction SilentlyContinue
```

### 2. Build Executable
```powershell
python -m PyInstaller build_installer.spec --clean --noconfirm
```

### 3. Calculate EXE Checksum
```powershell
Get-FileHash -Path "dist\PostMini\PostMini.exe" -Algorithm SHA256
```

### 4. Build Installer (requires Inno Setup)
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

### 5. Calculate Installer Checksum
```powershell
Get-FileHash -Path "dist\installer\PostMini_Setup_v2.0.0.exe" -Algorithm SHA256
```

### 6. Update version.json with Checksums
Replace `PLACEHOLDER_EXE_CHECKSUM` and `PLACEHOLDER_INSTALLER_CHECKSUM` with actual SHA256 values.

## 🚀 Git & GitHub Release

### 1. Commit Changes
```powershell
git add .
git commit -m "Release v2.0.0 - Major UX & Workflow Enhancements

- Enhanced Recent Requests panel with Open Pinned button
- Single-click persistent tabs workflow
- Modern icon buttons and comprehensive tab context menu
- Fixed script indicators and request duplication bugs
- Fixed variable tooltips for path parameters
- Better error handling with automatic Request Details display"
```

### 2. Create and Push Tag
```powershell
git tag -a v2.0.0 -m "Version 2.0.0 - Major UX & Workflow Enhancements"
git push origin main
git push origin v2.0.0
```

### 3. Create GitHub Release
1. Go to: https://github.com/melerek/PostMini/releases/new
2. Choose tag: `v2.0.0`
3. Release title: `v2.0.0 - Major UX & Workflow Enhancements`
4. Copy content from `GITHUB_RELEASE_v2.0.0.md` into description
5. Update checksums in the description with calculated values
6. Upload: `dist\installer\PostMini_Setup_v2.0.0.exe`
7. Mark as latest release
8. Publish release

## ✅ Post-Release Verification

### 1. Verify Download
- Download the installer from GitHub release page
- Verify checksum matches:
```powershell
Get-FileHash -Path "PostMini_Setup_v2.0.0.exe" -Algorithm SHA256
```

### 2. Test Installation
- Run installer on clean system
- Verify version in About dialog
- Test key features:
  - Recent Requests "Open Pinned" button
  - Single-click persistent tabs
  - Tab context menu (right-click on tab)
  - Variable tooltips for `:pathParam` syntax
  - Script indicators when opening from Recent Requests
  - Request duplication with scripts
  - Error handling with Request Details display

### 3. Test Auto-Update
- Open v1.9.9 installation
- Should show update notification for v2.0.0
- Test update process

## 📝 Next Steps

1. Monitor GitHub Issues for any bug reports
2. Update NEXT_VERSION_FEATURES.md with new changes as they're implemented
3. Consider announcing release on social media/developer communities

## 🎯 Release Summary

**Version:** 2.0.0  
**Date:** November 21, 2025  
**Type:** Major Release  
**Focus:** UX improvements, bug fixes, better debugging tools

**Key Highlights:**
- ✨ Recent Requests panel enhancements (Open Pinned, single-click persistent)
- 🎨 Modern UI (icon buttons, comprehensive tab context menu)
- 🐛 Critical bug fixes (script indicators, request duplication, variable tooltips)
- 🔍 Better error handling (automatic Request Details on failed requests)

**Breaking Changes:** None (fully backward compatible)
