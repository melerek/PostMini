# PostMini v1.9.1 - GitHub Release Instructions

## Release Information

**Version:** 1.9.1  
**Release Date:** November 13, 2025  
**Tag:** v1.9.1  
**Branch:** main  
**Commit:** aa510a4

---

## Step-by-Step GitHub Release Creation

### 1. Go to GitHub Releases Page
Navigate to: https://github.com/melerek/PostMini/releases/new

### 2. Select the Tag
- **Tag:** v1.9.1
- **Target:** main branch (already pushed)

### 3. Release Title
```
PostMini v1.9.1: Drag & Drop Ordering
```

### 4. Release Description (Copy this exactly)

```markdown
## 🎯 Drag & Drop Ordering Feature

PostMini v1.9.1 introduces comprehensive drag & drop ordering functionality with full Postman compatibility, allowing you to organize your API collections, folders, and requests exactly how you want them.

### ✨ What's New

#### Drag & Drop Ordering
- **User-controlled ordering** - Drag and drop to reorder collections, folders, and requests
- **Persistent order** - Order is saved immediately and persists across restarts
- **Import/export preservation** - Order is maintained when exporting/importing collections
- **Visual feedback** - Drop indicators show where items will be placed (above, below, or inside)
- **Automatic updates** - Item counts refresh automatically after moves
- **Expanded state preservation** - Folders stay expanded during drag & drop operations
- **Comprehensive test coverage** - 17 passing tests covering all scenarios

#### Postman-Compatible Validation Rules
- ✅ Collections can be reordered at root level only (cannot be nested)
- ✅ Folders can be moved within their collection (cannot move between collections)
- ✅ Folders cannot be at root level (must be inside collections)
- ✅ Requests can be moved between collections and folders
- ✅ Circular reference prevention (folders cannot be dropped into themselves or descendants)
- ✅ Type-safe drops (invalid operations are blocked)

### 🐛 Bug Fixes
- Fixed database queries to use `order_index` for consistent sorting
- Fixed `get_folders_by_collection()` to include `order_index` in returned data
- Fixed `get_requests_by_folder()` to order by `order_index` instead of name
- Fixed test suite parameter order for `create_request()` calls
- Fixed import/export test data format expectations

### 🔧 Technical Details
- Added `order_index` column to collections, folders, and requests tables
- Custom `ReorderableTreeWidget` class with comprehensive drop validation
- Transaction-safe database updates with rollback on error
- Circular reference detection for folder moves
- Smart tree reload only when items are moved (not just reordered)

### 📚 Documentation
- Complete technical guide: `docs/guides/DRAG_DROP_ORDERING.md`
- Comprehensive test suite: `tests/test_drag_drop_ordering.py` (17 tests)
- Updated README.md with feature details
- Updated CHANGELOG.md with complete release notes

---

## 📥 Installation

### Windows Installer (Recommended)
Download and run `PostMini_Setup_v1.9.1.exe` below.

**Features:**
- ✅ No Python installation required
- ✅ All dependencies bundled
- ✅ Automatic desktop shortcuts
- ✅ Start menu integration
- ✅ Easy updates

### Manual Installation
See [Installation Guide](https://github.com/melerek/PostMini/blob/main/docs/USER_INSTALLATION_GUIDE.md) for Python-based installation.

---

## 🔐 SHA256 Checksums

**Verify your download integrity:**

### Installer (PostMini_Setup_v1.9.1.exe)
```
873C57E675C4B4CA643AC0E0FBD1AC8BA92C04525821D4C3BD8C37414D91C0B6
```

### Executable (PostMini.exe - from dist folder)
```
6DE93B4B204C331038AE15C1F680E3D347BF5A2228E7D69242735EE2B6861FA7
```

**How to verify (Windows PowerShell):**
```powershell
Get-FileHash -Path "PostMini_Setup_v1.9.1.exe" -Algorithm SHA256
```

---

## 🚀 Automatic Updates

Users running PostMini v1.0.0 or later will receive an automatic update notification.

The `version.json` file has been updated with:
- ✅ Correct version number (1.9.1)
- ✅ Correct download URL
- ✅ Valid SHA256 checksum
- ✅ Release notes for auto-update notification

**Update verification:**
- The app checks: `https://raw.githubusercontent.com/melerek/PostMini/main/version.json`
- Users will see a notification about the new version
- One-click download and installation

---

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md) for complete version history.

---

## 🎓 Getting Started

1. **Download** the installer from Assets below
2. **Run** `PostMini_Setup_v1.9.1.exe`
3. **Follow** the installation wizard
4. **Launch** PostMini from Start Menu or Desktop
5. **Start** organizing your API collections with drag & drop!

---

## 🆚 PostMini vs Postman

- **FREE** vs $49+/user/month
- **100% Local Data Storage** vs Cloud-only
- **Git-Native Collaboration** vs Limited Git
- **Open Source** vs Closed Source
- **Unlimited Users** vs Per-seat pricing

**Save $17,640** over 3 years for a 10-person team!

---

## 🐛 Found a Bug?

Report issues at: https://github.com/melerek/PostMini/issues

---

## ⭐ Support the Project

If you find PostMini useful, please:
- ⭐ Star this repository
- 🐛 Report bugs and suggest features
- 📢 Share with your team
- 🤝 Contribute code or documentation

---

## 📄 License

MIT License - see [LICENSE.txt](https://github.com/melerek/PostMini/blob/main/LICENSE.txt)
```

### 5. Upload the Installer

Click **"Add binaries by dropping them here or selecting them"** and upload:
- **File:** `dist\installer\PostMini_Setup_v1.9.1.exe`
- **Location:** `C:\Users\MariuszMilew_jstooze\Documents\WORK\Apps\PostmanAlternative\dist\installer\PostMini_Setup_v1.9.1.exe`

### 6. Release Settings

- ✅ **Set as the latest release** (checked)
- ✅ **Create a discussion for this release** (checked, category: Announcements)
- ⬜ **Set as a pre-release** (unchecked)

### 7. Publish Release

Click **"Publish release"**

---

## Post-Release Verification Checklist

### Immediately After Publishing:

1. **Verify Release Page**
   - [ ] Release appears at https://github.com/melerek/PostMini/releases
   - [ ] Installer file is downloadable
   - [ ] SHA256 checksums match

2. **Verify Auto-Update**
   - [ ] Open PostMini v1.9.0 or earlier
   - [ ] Wait for update notification (checks version.json from main branch)
   - [ ] Notification should show v1.9.1 with release notes
   - [ ] Download link should point to correct installer

3. **Test Installation**
   - [ ] Download fresh installer from GitHub release
   - [ ] Verify SHA256 checksum matches
   - [ ] Run installer on clean machine (if possible)
   - [ ] Launch app and verify version is 1.9.1
   - [ ] Test drag & drop ordering feature
   - [ ] Verify order persists after restart

4. **Test Auto-Update Flow**
   - [ ] Run old version (v1.9.0)
   - [ ] Click update notification
   - [ ] Download completes
   - [ ] New installer runs
   - [ ] App updates to v1.9.1
   - [ ] All settings and data preserved

5. **Verify Documentation**
   - [ ] README.md shows correct version
   - [ ] CHANGELOG.md shows v1.9.1 entry
   - [ ] Documentation links work
   - [ ] All markdown renders correctly

### Within 24 Hours:

1. **Monitor for Issues**
   - [ ] Check GitHub issues for installation problems
   - [ ] Monitor download count
   - [ ] Watch for Windows SmartScreen warnings

2. **Community Announcement**
   - [ ] Post announcement in discussion
   - [ ] Update any social media/forums
   - [ ] Notify team members

---

## Emergency Rollback Plan

If critical issues are discovered:

1. **Mark as Pre-Release**
   - Edit the v1.9.1 release
   - Check "Set as a pre-release"
   - This prevents auto-update notifications

2. **Update version.json**
   - Revert to previous stable version in main branch
   - Push the change
   - This stops new auto-update notifications

3. **Create Hotfix**
   - Fix the critical issue
   - Create v1.9.2 with fix
   - Test thoroughly before release

---

## Key Files and Locations

| File | Location | Purpose |
|------|----------|---------|
| Installer | `dist\installer\PostMini_Setup_v1.9.1.exe` | Main distribution file |
| Executable | `dist\PostMini\PostMini.exe` | Standalone app (bundled in installer) |
| Version JSON | `version.json` | Auto-update configuration |
| Changelog | `CHANGELOG.md` | Release history |
| Release Tag | `v1.9.1` | Git tag for this release |

---

## Contact

- **Repository:** https://github.com/melerek/PostMini
- **Issues:** https://github.com/melerek/PostMini/issues
- **Discussions:** https://github.com/melerek/PostMini/discussions

---

## Success Criteria

Release is successful when:
- ✅ Installer downloads and installs without errors
- ✅ SHA256 checksums match
- ✅ Auto-update works for existing users
- ✅ Drag & drop ordering works as documented
- ✅ No critical bugs reported within 48 hours
- ✅ Download count increases steadily

---

**Release prepared by:** AI Assistant  
**Date:** November 13, 2025  
**Time:** (Current Time)
