# GitHub Release v1.9.1 - UPDATE INSTRUCTIONS

## ⚠️ IMPORTANT: Version Fix Required

A critical issue was discovered after the initial v1.9.1 release preparation. The application had **hardcoded version strings** in two files that were still showing "1.9.0", causing the auto-update checker to think the current version was 1.9.0 even after installing 1.9.1.

## 🔧 What Was Fixed

### Fixed Files:
1. **src/features/auto_updater.py** - Line 26: `CURRENT_VERSION = "1.9.1"`
2. **src/ui/widgets/settings_panel.py** - Line 20: `APP_VERSION = "1.9.1"`

### Rebuilt with Correct Version:
- ✅ Application rebuilt with PyInstaller (new executable)
- ✅ Installer rebuilt with Inno Setup (new installer)
- ✅ New SHA256 checksums calculated
- ✅ version.json updated with new checksums
- ✅ Changes committed and pushed to main branch (commit: 5321b3f)

---

## 📝 What You Need to Update in GitHub Release

### Option 1: Update Existing Release (RECOMMENDED)

If you've **already created** the GitHub release for v1.9.1:

1. **Go to:** https://github.com/melerek/PostMini/releases/tag/v1.9.1
2. **Click:** "Edit release" button
3. **Delete:** The old `PostMini_Setup_v1.9.1.exe` file from Assets
4. **Upload:** The NEW installer from: `dist\installer\PostMini_Setup_v1.9.1.exe`
5. **Update SHA256 checksums** in the release description:

#### Replace These Lines in Release Description:

**OLD SHA256 Checksums (WRONG):**
```
### Installer (PostMini_Setup_v1.9.1.exe)
```
873C57E675C4B4CA643AC0E0FBD1AC8BA92C04525821D4C3BD8C37414D91C0B6
```

### Executable (PostMini.exe - from dist folder)
```
6DE93B4B204C331038AE15C1F680E3D347BF5A2228E7D69242735EE2B6861FA7
```
```

**NEW SHA256 Checksums (CORRECT):**
```
### Installer (PostMini_Setup_v1.9.1.exe)
```
BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A
```

### Executable (PostMini.exe - from dist folder)
```
4A50A158B0F8698673D952E0A5176EA9A301C7D5B35D6B88CEFA8773EEFD0635
```
```

6. **Save changes** (Update release button)

---

### Option 2: Create Fresh Release (If not created yet)

If you **haven't created** the GitHub release yet, follow the original instructions from `GITHUB_RELEASE_v1.9.1.md`, but use these **UPDATED** values:

#### Updated SHA256 Checksums:

**Installer SHA256:**
```
BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A
```

**Executable SHA256:**
```
4A50A158B0F8698673D952E0A5176EA9A301C7D5B35D6B88CEFA8773EEFD0635
```

**Installer File Location:**
```
C:\Users\MariuszMilew_jstooze\Documents\WORK\Apps\PostmanAlternative\dist\installer\PostMini_Setup_v1.9.1.exe
```

---

## ✅ Verification Steps

After updating the GitHub release:

### 1. Verify Auto-Update System

The `version.json` file on main branch now has the correct checksums:
- ✅ `checksum`: BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A
- ✅ `exe_sha256`: 4A50A158B0F8698673D952E0A5176EA9A301C7D5B35D6B88CEFA8773EEFD0635
- ✅ `installer_sha256`: BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A

### 2. Test Fresh Installation

1. Download the **NEW** installer from GitHub release
2. Verify SHA256 matches: `BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A`
3. Install the application
4. Launch PostMini
5. Go to **Settings** tab
6. Verify version shows: **"Version 1.9.1"** (not 1.9.0!)
7. Click **"Check for Updates"**
8. Should show: **"PostMini 1.9.1 is the latest version"**

### 3. Test Auto-Update Flow

If users are running v1.9.0:
1. They should get update notification for v1.9.1
2. Download should work correctly
3. New checksum will be validated
4. After installation, version should correctly show 1.9.1

---

## 🚨 Why This Matters

### The Problem:
- Users installing v1.9.1 would see "Version 1.9.1" in the title bar (from `main.py`)
- But the **Settings panel** would show "Version 1.9.0" (wrong!)
- The **auto-update checker** would think current version is 1.9.0 (wrong!)
- This would cause the app to **always show update notifications** even when running latest version

### The Solution:
- Fixed hardcoded version strings in `auto_updater.py` and `settings_panel.py`
- Rebuilt everything with correct version 1.9.1
- New checksums ensure integrity
- Auto-update system now works correctly

---

## 📊 Comparison Table

| Item | OLD (Wrong) | NEW (Correct) |
|------|-------------|---------------|
| **Installer SHA256** | 873C57E675C4B4CA643AC0E0FBD1AC8BA92C04525821D4C3BD8C37414D91C0B6 | BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A |
| **Executable SHA256** | 6DE93B4B204C331038AE15C1F680E3D347BF5A2228E7D69242735EE2B6861FA7 | 4A50A158B0F8698673D952E0A5176EA9A301C7D5B35D6B88CEFA8773EEFD0635 |
| **auto_updater.py Version** | 1.9.0 | 1.9.1 |
| **settings_panel.py Version** | 1.9.0 | 1.9.1 |
| **Git Commit** | aa510a4 | 5321b3f |

---

## 🎯 Quick Action Checklist

- [ ] Go to GitHub release page: https://github.com/melerek/PostMini/releases/tag/v1.9.1
- [ ] Edit the release
- [ ] Delete old installer file
- [ ] Upload NEW installer: `dist\installer\PostMini_Setup_v1.9.1.exe`
- [ ] Update SHA256 checksums in release description
- [ ] Save/Update the release
- [ ] Download fresh installer from GitHub
- [ ] Verify SHA256: BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A
- [ ] Test installation
- [ ] Verify Settings shows "Version 1.9.1"
- [ ] Verify auto-update shows "PostMini 1.9.1 is the latest version"

---

## 📞 Support

If you encounter any issues:
- Check that the installer SHA256 matches: BE7406E83416037072132DE272D2B5936BDEA7EC92A5583A5D7D3A06A3CEF93A
- Verify version.json on main branch has the correct checksums
- Clear browser cache and re-download installer if needed

---

**Last Updated:** November 13, 2025  
**Commit:** 5321b3f  
**Status:** Ready for GitHub Release Update
