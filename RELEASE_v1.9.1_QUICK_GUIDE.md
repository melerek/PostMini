# PostMini v1.9.1 - Quick Release Guide

## ✅ Status: READY FOR GITHUB RELEASE

All preparation complete. Follow these simple steps:

---

## 🚀 Create GitHub Release (5 Minutes)

### Step 1: Go to Release Page
Visit: https://github.com/melerek/PostMini/releases/new

### Step 2: Fill in Details
- **Tag:** v1.9.1 (select from dropdown - already exists)
- **Target:** main
- **Title:** `PostMini v1.9.1: Drag & Drop Ordering`

### Step 3: Copy Release Notes
Open file: `GITHUB_RELEASE_v1.9.1.md`
Copy the entire markdown content (starting from "## 🎯 Drag & Drop Ordering Feature")
Paste into the description field on GitHub

### Step 4: Upload Installer
- Click "Add binaries by dropping them here"
- Upload: `dist\installer\PostMini_Setup_v1.9.1.exe`
- Wait for upload to complete

### Step 5: Publish
- ✅ Check "Set as the latest release"
- ✅ Check "Create a discussion for this release"
- Click "Publish release"

---

## 🔐 Key Information

### SHA256 Checksums (for release notes verification)
**Installer:**
```
873C57E675C4B4CA643AC0E0FBD1AC8BA92C04525821D4C3BD8C37414D91C0B6
```

**Executable:**
```
6DE93B4B204C331038AE15C1F680E3D347BF5A2228E7D69242735EE2B6861FA7
```

### File Locations
- Installer: `dist\installer\PostMini_Setup_v1.9.1.exe`
- Release Notes: `GITHUB_RELEASE_v1.9.1.md`
- Full Instructions: `RELEASE_v1.9.1_READY.md`

### Git Status
- ✅ Commit: aa510a4 (pushed to main)
- ✅ Tag: v1.9.1 (pushed)
- ✅ Branch: main (up to date)

---

## ✅ Post-Release Checklist

After publishing:

1. **Verify download works:**
   - Go to https://github.com/melerek/PostMini/releases/tag/v1.9.1
   - Download the installer
   - Verify SHA256 matches

2. **Test auto-update:**
   - Open PostMini v1.9.0
   - Should see update notification
   - Download should work

3. **Test installation:**
   - Run installer on test machine
   - Verify version is 1.9.1
   - Test drag & drop feature

---

## 🎯 What This Release Includes

- **NEW:** Drag & Drop Ordering for collections/folders/requests
- **NEW:** Postman-compatible validation rules
- **NEW:** Order persistence across restarts
- **NEW:** 17 comprehensive tests
- **FIXED:** Database ordering issues
- **IMPROVED:** Better organization for large projects

---

## 📞 If You Need Help

- Full instructions: `RELEASE_v1.9.1_READY.md`
- Release notes template: `GITHUB_RELEASE_v1.9.1.md`
- Feature documentation: `docs/guides/DRAG_DROP_ORDERING.md`

---

**You're all set! Just create the GitHub release and you're done! 🎉**
