# GitHub Release Instructions for v1.9.6

## ✅ Completed Steps
1. ✅ Updated all 6 version files to 1.9.6
2. ✅ Updated CHANGELOG.md with new version entry
3. ✅ Updated README.md version badge
4. ✅ Built executable with PyInstaller
5. ✅ Built installer with Inno Setup
6. ✅ Calculated checksums and updated version.json
7. ✅ Committed all changes to git
8. ✅ Created and pushed tag v1.9.6
9. ✅ Pushed to GitHub

## 🔄 Next Steps - Create GitHub Release

### Option 1: Using GitHub Web Interface (Recommended)

1. **Go to GitHub Releases page:**
   https://github.com/melerek/PostMini/releases/new?tag=v1.9.6

2. **Fill in the release form:**
   - Tag: `v1.9.6` (already created and pushed)
   - Title: `PostMini v1.9.6 - Consolidated Notification System`
   - Description: Copy content from `GITHUB_RELEASE_v1.9.6.md`

3. **Upload the installer:**
   - Click "Attach binaries by dropping them here or selecting them"
   - Upload: `dist\installer\PostMini_Setup_v1.9.6.exe`

4. **Verify checksums in description:**
   - Installer SHA256: `9356A60138717FB800F46B21644F0C9667753D65ADCEF239D18579E02776589C`
   - Executable SHA256: `A2D6A4757521EFED82BEF1A9E320584CD05A904A3F57F3182E6F9D532E512D1A`

5. **Publish the release**

### Option 2: Using GitHub CLI (if installed)

```powershell
# Install GitHub CLI (if needed)
winget install --id GitHub.cli

# Login to GitHub
gh auth login

# Create release with installer
gh release create v1.9.6 `
  --title "PostMini v1.9.6 - Consolidated Notification System" `
  --notes-file GITHUB_RELEASE_v1.9.6.md `
  "dist\installer\PostMini_Setup_v1.9.6.exe"
```

## 📋 Verification Checklist

After creating the release:

- [ ] Release appears at https://github.com/melerek/PostMini/releases
- [ ] Installer is downloadable
- [ ] Download link matches version.json: https://github.com/melerek/PostMini/releases/download/v1.9.6/PostMini_Setup_v1.9.6.exe
- [ ] Checksums match
- [ ] Auto-updater will detect new version (version.json updated)

## 🎉 Release Complete!

Once published, users will be able to:
1. Download the installer from GitHub releases
2. Receive auto-update notification if they have v1.9.5 or earlier
3. See the new consolidated notification system in action

## 📝 Post-Release Tasks

1. Clear NEXT_VERSION_FEATURES.md for next release cycle:
   ```markdown
   # Features for Next Release
   
   Track all changes here as they're implemented. This will become the changelog entry for the next version.
   
   ## ✨ New Features
   - (No features added yet)
   
   ## 🐛 Bug Fixes
   - (No fixes added yet)
   
   ## 🔧 Technical Improvements
   - (No technical changes yet)
   
   ## 📚 Documentation
   - (No documentation updates yet)
   
   ## 🎨 UI/UX Enhancements
   - (No UI improvements yet)
   ```

2. Announce the release (optional):
   - Social media
   - Project website
   - User community channels
