# Build Instructions for v1.9.7 Release

## Pre-Build Checklist
- [x] All 6 version files updated to 1.9.7
- [x] CHANGELOG.md updated with v1.9.7 changes
- [x] POSTMINI_VS_POSTMAN_COMPARISON.md updated
- [x] GitHub release notes created
- [ ] Application tested and working
- [ ] Build completed
- [ ] Checksums calculated
- [ ] version.json updated with checksums

## Build Steps

### 1. Clean Previous Builds
```powershell
Remove-Item -Path "build","dist" -Recurse -Force -ErrorAction SilentlyContinue
```

### 2. Build Executable
```powershell
python -m PyInstaller build_installer.spec --clean --noconfirm
```

### 3. Calculate Executable Checksum
```powershell
Get-FileHash -Path "dist\PostMini\PostMini.exe" -Algorithm SHA256
```
**Save this value as `exe_sha256`**

### 4. Build Installer
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

### 5. Calculate Installer Checksum
```powershell
Get-FileHash -Path "dist\installer\PostMini_Setup_v1.9.7.exe" -Algorithm SHA256
```
**Save this value as `installer_sha256` and `checksum`**

### 6. Update version.json
Update these fields in `version.json`:
- `exe_sha256` = Executable checksum from step 3
- `installer_sha256` = Installer checksum from step 5
- `checksum` = Same as installer checksum

### 7. Commit Changes
```powershell
git add .
git commit -m "Release v1.9.7: Cookie Management & Path Parameters

- Added complete cookie management system with automatic persistence
- Added Postman-compatible path parameter support (:paramName syntax)
- Visual feedback and tooltips for path parameters
- Postman-style scripts tab toggle interface
- Content indicators for all tabs
- Consistent styling across all tabs

Checksums included in version.json"

git tag v1.9.7
git push origin main
git push origin v1.9.7
```

### 8. Create GitHub Release
1. Go to https://github.com/melerek/PostMini/releases/new
2. Tag: `v1.9.7`
3. Title: `PostMini v1.9.7 - Cookie Management & Path Parameters`
4. Description: Copy content from `GITHUB_RELEASE_v1.9.7.md`
5. Attach file: `dist\installer\PostMini_Setup_v1.9.7.exe`
6. Update release notes with actual checksums
7. Publish release

### 9. Verify Download
After publishing:
```powershell
# Download the installer from GitHub
# Verify checksum matches
Get-FileHash -Path "path\to\downloaded\PostMini_Setup_v1.9.7.exe" -Algorithm SHA256
# Compare with installer_sha256 in version.json
```

### 10. Reset for Next Version
```powershell
# Clear NEXT_VERSION_FEATURES.md for next release
git add NEXT_VERSION_FEATURES.md
git commit -m "Reset NEXT_VERSION_FEATURES.md for next release cycle"
git push origin main
```

## Verification
- [ ] Installer downloads correctly from GitHub
- [ ] Checksum matches published value
- [ ] Fresh install works on clean Windows machine
- [ ] Upgrade from v1.9.6 works correctly
- [ ] All new features functional
- [ ] Auto-updater detects new version

## Notes
- Installer will be in: `dist\installer\PostMini_Setup_v1.9.7.exe`
- Executable will be in: `dist\PostMini\PostMini.exe`
- Keep both checksums for version.json
- Tag format is `v1.9.7` (with 'v' prefix)
