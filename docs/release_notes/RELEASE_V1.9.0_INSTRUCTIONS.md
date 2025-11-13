# PostMini v1.9.0 Release Instructions

## 📦 Release Package Summary

**Version:** 1.9.0  
**Release Date:** November 13, 2025  
**Installer:** `PostMini_Setup_v1.9.0.exe`  
**Location:** `dist/installer/PostMini_Setup_v1.9.0.exe`

---

## 🎯 What's New in v1.9.0

### 🌍 Environment Import/Export (Major Feature)
Full Postman environment format compatibility with import/export functionality

### 🎨 Enhanced Light Theme & UI Polish
Comprehensive light theme improvements with theme-aware components throughout the application

### 🖥️ Advanced UI Features
Temporary tabs, keyboard shortcuts, optimized panels, and improved user experience

---

## 📋 GitHub Release Instructions

### Step 1: Create New Release on GitHub

1. Go to: `https://github.com/melerek/PostMini/releases/new`
2. **Tag version:** `v1.9.0`
3. **Release title:** `PostMini v1.9.0 - Environment Import/Export & Enhanced UI`
4. **Target branch:** `main`

### Step 2: Upload Release Assets

Upload the following file from `dist/installer/`:
- `PostMini_Setup_v1.9.0.exe` (the Windows installer)

### Step 3: Release Description

Copy and paste the following markdown into the release description:

---

## 🎉 PostMini v1.9.0 - Environment Import/Export & Enhanced UI

### ✨ Major Features

#### 🌍 Environment Import/Export with Full Postman Compatibility

**Complete environment management system:**
- ✅ **Import from Postman** - Full Postman environment format support
- ✅ **Export to Postman** - Share environments with Postman users
- ✅ **Bidirectional conversion** - Seamlessly switch between formats
- ✅ **Secret handling** - Choose to include actual values or use placeholders
- ✅ **Bulk operations** - Import/export multiple environments
- ✅ **Disabled variables** - Postman's enabled/disabled state preserved
- ✅ **Auto-detection** - Automatically identifies environment format
- ✅ **Smart validation** - Validates structure on import

**Use Cases:**
- Migrate from Postman to PostMini
- Team collaboration across tools
- Create environment templates
- Backup with or without secrets

**New Files:**
- `src/features/postman_environment_converter.py` - Bidirectional converter
- `src/features/environment_io.py` - Import/export infrastructure  
- `tests/test_postman_environment_compatibility.py` - 9 comprehensive tests (all passing)
- `docs/guides/ENVIRONMENT_IMPORT_EXPORT_GUIDE.md` - Complete guide

---

### 🎨 Enhanced Light Theme & UI Polish

#### Comprehensive Light Theme Improvements
- **Enhanced contrast** - All UI elements optimized for readability
- **QPushButtons** - White backgrounds, dark text (#212121), strong borders
- **Send Button** - Material Design blue (#1976D2) for prominence
- **ComboBoxes** - Strong borders, bold text, blue focus states
- **Text Inputs** - Enhanced borders with blue focus indication
- **Tree Widgets** - Darker text (#424242), strong selection highlights
- **Environment Selector** - Theme-aware status bar styling

#### Theme-Aware Components
- **All panel buttons** - Environment, Collections, Variables panels
- **Central buttons** - New Request, Recent, Save buttons
- **Icon bar** - All 6 sidebar icons maintain correct styling
- **Theme toggle** - Quick access in status bar (🌙 Dark / ☀️ Light)

#### Bug Fixes
- **Fixed initialization bug** - Dark theme startup now shows correct button styling
- **Fixed theme switching** - Icon bar buttons work correctly across themes
- **Panel width** - Left panels now default to 400px (was 250px)
- **Dynamic tables** - Variables remain in user-defined order (no auto-sorting)

---

### 🖥️ Advanced UI Features

#### Temporary Tabs (Preview Mode)
- **Single-click** opens in temporary tab (italic, auto-closes)
- **Double-click** opens permanent tab
- Auto-converts to permanent when editing/sending/saving
- Similar to VS Code preview behavior

#### Keyboard Shortcuts for Panels
- **Alt+C** - Collections
- **Alt+E** - Environments  
- **Alt+V** - Variables
- **Alt+G** - Git Sync
- **Alt+H** - History
- **Alt+R** - Recent Requests

#### History as Overlay Panel
- Non-blocking 800px right-side overlay
- Smooth animations
- Mutual exclusion with Recent Requests

#### Tab & Button Optimizations
- **Tab headers** - Optimized padding and width (more tabs visible)
- **Recent button** - Modernized from emoji to text-based
- **Simplified tooltips** - Cleaner with keyboard shortcuts
- **No bullet separators** - Cleaner tab labels

---

## 📥 Installation

### For New Users

1. **Download:** `PostMini_Setup_v1.9.0.exe`
2. **Run installer** - Follow the installation wizard
3. **Launch PostMini** - Find it in Start Menu or Desktop shortcut

### For Existing Users (Upgrading)

1. **Download:** `PostMini_Setup_v1.9.0.exe`
2. **Run installer** - It will upgrade your existing installation
3. **Your data is safe** - All collections, environments, and settings preserved
4. **Launch PostMini** - Enjoy the new features!

> **Note:** Windows SmartScreen may show a warning. Click "More info" → "Run anyway". This is normal for unsigned applications.

---

## 🔧 Technical Details

### Modified Files
- `CHANGELOG.md` - Full release notes
- `version.json` - Updated to 1.9.0
- `installer.iss` - Updated version
- `src/ui/main_window.py` - Theme management, button styling
- `src/ui/widgets/environments_panel.py` - Theme-aware buttons
- `src/ui/widgets/variable_inspector_panel.py` - Theme support
- `main.py` - Theme initialization
- `styles.qss` - Enhanced light theme

### New Files
- `src/features/postman_environment_converter.py` (342 lines)
- `src/features/environment_io.py` (425 lines)
- `tests/test_postman_environment_compatibility.py` (438 lines)
- `docs/guides/ENVIRONMENT_IMPORT_EXPORT_GUIDE.md` (comprehensive guide)

### Requirements
- **OS:** Windows 10/11 (64-bit)
- **Disk Space:** ~200 MB
- **No Python required** - Fully standalone installer

---

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md) for complete version history.

---

## 🐛 Known Issues

None reported for this release.

---

## 💬 Feedback & Support

- **Issues:** [GitHub Issues](https://github.com/melerek/PostMini/issues)
- **Discussions:** [GitHub Discussions](https://github.com/melerek/PostMini/discussions)

---

## 🙏 Thank You

Thank you for using PostMini! This release represents significant improvements to environment management and UI polish. We hope you enjoy the new features!

---

### Checksums (for verification)

**File:** `PostMini_Setup_v1.9.0.exe`  
**SHA256:** `507AE526568FBB7C211E660C697DF1DCC36AEF8A564B0D8E4D13080AF46A37F6`

You can verify the integrity of your download:
```powershell
Get-FileHash PostMini_Setup_v1.9.0.exe -Algorithm SHA256
```

Expected hash: `507AE526568FBB7C211E660C697DF1DCC36AEF8A564B0D8E4D13080AF46A37F6`

---

