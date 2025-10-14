# Quick Build Guide - PostMini Installer

**TL;DR:** This guide will help you create a Windows installer for PostMini in 5 minutes.

---

## 🚀 Quick Start

### 1. Install Build Tools
```bash
# Install development dependencies (includes PyInstaller)
pip install -r requirements-dev.txt

# Download and install Inno Setup from:
# https://jrsoftware.org/isdl.php
```

### 2. Build the Executable
```bash
# Clean previous builds (optional)
rmdir /s /q build dist

# Build with PyInstaller
pyinstaller build_installer.spec
```

**✅ Result:** `dist/PostMini/PostMini.exe` created

### 3. Test the Executable
```bash
cd dist\PostMini
PostMini.exe
```

**Check:**
- ✅ App opens without errors
- ✅ Console shows: "Application data directory: C:\Users\<You>\AppData\Roaming\PostMini"
- ✅ Create a test collection and request
- ✅ Close app and verify database exists at: `%APPDATA%\PostMini\api_client.db`

### 4. Create the Installer
```bash
# Return to project root
cd ..\..

# Compile with Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

**✅ Result:** `dist/installer/PostMini_Setup_v1.0.0.exe` created

### 5. Test the Installer
```bash
# Run the installer
dist\installer\PostMini_Setup_v1.0.0.exe
```

**Verify:**
- ✅ Installer runs without errors
- ✅ PostMini installs to: `C:\Program Files\PostMini\`
- ✅ Desktop shortcut created (if selected)
- ✅ Start Menu entry exists
- ✅ Launch PostMini from Start Menu
- ✅ Create test data
- ✅ Verify data is in: `%APPDATA%\PostMini\` (NOT in Program Files)

---

## 📦 What You Get

**Installer Size:** ~80-120 MB (includes Python runtime + PyQt6)

**Includes:**
- ✅ Standalone executable (no Python needed)
- ✅ All dependencies bundled
- ✅ Professional installer wizard
- ✅ Desktop + Start Menu shortcuts
- ✅ User data in %APPDATA% (safe from permissions issues)
- ✅ Uninstaller

---

## 🔧 Customization

### Change Version Number

**`main.py` - line 75:**
```python
app.setApplicationVersion("1.0.0")  # <- Change here
```

**`installer.iss` - line 5:**
```ini
#define MyAppVersion "1.0.0"  ; <- Change here
```

### Add Your Logo/Icon

1. Create `resources/icon.ico` (256x256 PNG -> ICO)
2. Update `build_installer.spec` line 70:
   ```python
   icon='resources/icon.ico',  # <- Uncomment and set path
   ```
3. Update `installer.iss` line 18:
   ```ini
   SetupIconFile=resources\icon.ico  ; <- Update path
   ```

### Change App Name

**`main.py` - line 73:**
```python
app.setApplicationName("PostMini")  # <- Change
```

**`src/core/app_paths.py` - line 14:**
```python
APP_NAME = "PostMini"  # <- Change
```

**`installer.iss` - line 4:**
```ini
#define MyAppName "PostMini"  ; <- Change
```

---

## ❓ Troubleshooting

### "pyinstaller: command not found"
```bash
pip install pyinstaller
```

### "PyQt6 not found" during build
```bash
pip install PyQt6
```

### Executable crashes on launch
```bash
# Run from command line to see error:
dist\PostMini\PostMini.exe
```

### Installer won't compile
- Make sure Inno Setup is installed
- Check path: `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
- Verify all files exist in `dist/PostMini/`

### "Database is locked" error
- Close all PostMini instances before building
- Check Task Manager for `PostMini.exe` processes

---

## 📚 More Information

For complete build documentation, see: **[BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)**

For development setup, see: **[README.md](README.md)**

---

## 🎯 Distribution Checklist

Before sharing the installer with users:

- [ ] Tested on clean Windows machine (no Python installed)
- [ ] Verified data goes to `%APPDATA%\PostMini\`
- [ ] Tested all major features (collections, requests, Git sync)
- [ ] Tested uninstall/reinstall (data preserved)
- [ ] Checked installer size is reasonable (~100MB)
- [ ] Verified antivirus doesn't flag it (VirusTotal scan)
- [ ] Updated version numbers in all files
- [ ] Created GitHub Release with installer
- [ ] Written release notes/changelog

---

**You're ready to ship! 🚀**

Share `dist/installer/PostMini_Setup_v1.0.0.exe` with your users!

