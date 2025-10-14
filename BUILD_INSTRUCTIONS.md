# PostMini - Build & Installer Instructions

This document explains how to build PostMini into a standalone Windows installer that can be distributed to users.

---

## 📋 Prerequisites

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install PyInstaller
```bash
pip install pyinstaller
```

### 3. Install Inno Setup (Windows Only)
Download and install Inno Setup from: https://jrsoftware.org/isdl.php
- Use the default installation location: `C:\Program Files (x86)\Inno Setup 6\`

### 4. (Optional) Create an Icon
Create an `icon.ico` file with multiple sizes (16x16, 32x32, 48x48, 256x256) and place it in a `resources/` folder.

---

## 🔨 Building the Application

### Step 1: Build the Executable with PyInstaller

Run PyInstaller with the provided spec file:

```bash
pyinstaller build_installer.spec
```

This will:
- Create a `dist/PostMini/` folder with the executable and all dependencies
- Bundle the PyQt6 libraries and Python runtime
- Include the `styles.qss` stylesheet
- Create a console-free GUI executable

**Output Location:** `dist/PostMini/PostMini.exe`

### Step 2: Test the Executable

Before creating the installer, test the executable:

```bash
cd dist/PostMini
PostMini.exe
```

**Verify:**
- ✅ Application launches without errors
- ✅ Check console output for data directory path: `%APPDATA%\PostMini`
- ✅ Test creating collections and requests
- ✅ Verify database is created in: `C:\Users\<YourName>\AppData\Roaming\PostMini\api_client.db`
- ✅ Test all major features (requests, environments, Git sync, etc.)

### Step 3: Create the Windows Installer

#### Option A: Using Inno Setup GUI (Easy)

1. Open Inno Setup Compiler
2. Click **File > Open** and select `installer.iss`
3. Click **Build > Compile** (or press `Ctrl+F9`)
4. Wait for compilation to complete

#### Option B: Using Command Line (Automated)

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

**Output Location:** `dist/installer/PostMini_Setup_v1.0.0.exe`

---

## 📦 Installer Features

The generated installer includes:

### Installation Features
- ✅ **User-friendly wizard** with modern interface
- ✅ **Per-user installation** (no admin rights required)
- ✅ **Automatic dependency bundling** (no Python installation needed)
- ✅ **Desktop shortcut** creation (optional)
- ✅ **Start Menu** entry
- ✅ **Uninstaller** included

### Data Management
- ✅ **Application data** stored in: `%APPDATA%\PostMini\`
  - Database: `api_client.db`
  - Logs: `logs/`
  - Exports: `exports/`
- ✅ **Data preserved** during uninstall (users can choose to keep or remove)
- ✅ **Updates don't affect** user data

### What Gets Installed
```
C:\Program Files\PostMini\
├── PostMini.exe              # Main executable
├── _internal\                # PyInstaller dependencies
│   ├── PyQt6\                # Qt libraries
│   ├── Python DLLs           # Python runtime
│   └── ...                   # Other dependencies
├── docs\                     # Documentation
│   ├── index.html
│   ├── GIT_SYNC_GUIDE.md
│   └── ...
├── README.md
└── styles.qss                # Application stylesheet
```

---

## 🧪 Testing the Installer

### Pre-Distribution Checklist

1. **Install on Clean System:**
   - Test on a Windows machine without Python installed
   - Verify it installs without errors

2. **Test User Data Location:**
   - Launch PostMini
   - Create a collection and request
   - Check that data is in: `%APPDATA%\PostMini\api_client.db`
   - Verify NO data files are created in `C:\Program Files\PostMini\`

3. **Test Git Sync:**
   - Enable Git sync with a test repository
   - Verify `.postmini/` folder is created in the selected project directory
   - Verify `.postmini-secrets/` is created in the project directory
   - Test export/import functionality

4. **Test Uninstall:**
   - Uninstall PostMini
   - Verify program files are removed
   - Verify user data in `%APPDATA%\PostMini\` is preserved
   - Reinstall and verify data is still accessible

5. **Test Updates:**
   - Install version 1.0.0
   - Create some test data
   - Build version 1.0.1 with a minor change
   - Install over the existing version
   - Verify data is preserved

---

## 🔄 Updating the Version

To create a new version:

### 1. Update Version Number

**In `main.py`:**
```python
app.setApplicationVersion("1.1.0")  # Change version
```

**In `installer.iss`:**
```ini
#define MyAppVersion "1.1.0"  ; Change version
```

### 2. Update README.md
Add release notes and changelog

### 3. Rebuild
```bash
# Clean previous builds
rmdir /s /q build dist

# Rebuild executable
pyinstaller build_installer.spec

# Test the executable
dist\PostMini\PostMini.exe

# Create installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

---

## 📁 File Structure Reference

```
PostmanAlternative/
├── main.py                          # Entry point
├── build_installer.spec             # PyInstaller config
├── installer.iss                    # Inno Setup config
├── BUILD_INSTRUCTIONS.md            # This file
├── requirements.txt
├── styles.qss
├── LICENSE.txt                      # Add your license
├── resources/                       # Optional
│   └── icon.ico                     # App icon (if you create one)
├── src/                             # Source code
│   ├── core/
│   │   ├── app_paths.py            # 🌟 NEW! Manages %APPDATA% paths
│   │   ├── database.py
│   │   └── ...
│   ├── ui/
│   └── features/
├── tests/
├── docs/
├── dist/                            # Build output (gitignored)
│   ├── PostMini/                    # PyInstaller output
│   │   └── PostMini.exe
│   └── installer/                   # Installer output
│       └── PostMini_Setup_v1.0.0.exe
└── build/                           # Temporary build files (gitignored)
```

---

## 🚨 Common Issues & Solutions

### Issue: "PyQt6 not found" error
**Solution:** Make sure PyQt6 is installed: `pip install PyQt6`

### Issue: Executable is very large (>200MB)
**Solution:** This is normal for PyInstaller bundles. The entire Python runtime and Qt libraries are included. You can:
- Use UPX compression (enabled in spec file)
- Exclude unnecessary modules in the spec file

### Issue: Antivirus flags the executable
**Solution:** This is common for PyInstaller executables. Options:
1. Submit the file to antivirus vendors as a false positive
2. Sign the executable with a code signing certificate (recommended for distribution)

### Issue: "Database is locked" error
**Solution:** Check that only one instance of PostMini is running

### Issue: Stylesheet not loading
**Solution:** Verify `styles.qss` is in the `datas` list in `build_installer.spec`

### Issue: Application writes to Program Files
**Solution:** Make sure you're using `src/core/app_paths.py` module correctly. All data should go to `%APPDATA%\PostMini\`

---

## 🎯 Distribution

Once you've built and tested the installer:

1. **Upload to GitHub Releases:**
   ```bash
   # Create a release on GitHub
   # Upload: dist/installer/PostMini_Setup_v1.0.0.exe
   ```

2. **Share with Users:**
   - Users download `PostMini_Setup_v1.0.0.exe`
   - Double-click to install
   - No Python or dependencies required!

3. **Provide Documentation:**
   - Link to GitHub README.md
   - Link to docs/index.html (can host on GitHub Pages)

---

## 📝 Adding a Code Signing Certificate (Optional but Recommended)

For professional distribution, consider signing your executable:

1. **Obtain a Code Signing Certificate:**
   - Purchase from a Certificate Authority (e.g., DigiCert, Sectigo)
   - Cost: ~$100-400/year

2. **Sign the Executable:**
   ```bash
   signtool sign /f "certificate.pfx" /p "password" /t "http://timestamp.digicert.com" "dist\PostMini\PostMini.exe"
   ```

3. **Sign the Installer:**
   ```bash
   signtool sign /f "certificate.pfx" /p "password" /t "http://timestamp.digicert.com" "dist\installer\PostMini_Setup_v1.0.0.exe"
   ```

This will:
- ✅ Remove Windows SmartScreen warnings
- ✅ Reduce antivirus false positives
- ✅ Build user trust
- ✅ Show your organization name in Windows

---

## 🎉 You're Done!

You now have a distributable Windows installer for PostMini! 🚀

**Final Output:** `dist/installer/PostMini_Setup_v1.0.0.exe`

Users can install PostMini without:
- ❌ Installing Python
- ❌ Installing dependencies
- ❌ Any technical knowledge
- ❌ Admin privileges (optional)

Their data will be safely stored in `%APPDATA%\PostMini\` and preserved across updates!

