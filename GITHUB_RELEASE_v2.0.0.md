# 🚀 PostMini v2.0.0 - Major UX & Workflow Enhancements

**Release Date:** November 21, 2025

A major release focused on streamlining workflows, fixing critical bugs, and improving the developer experience with enhanced tab management, better error handling, and comprehensive variable tooltip support.

---

## ✨ Major New Features

### 📌 Recent Requests Panel Enhancements

**Streamlined Workflow**
- **"Open Pinned" Button** - Quickly open all your pinned requests in separate tabs with a single click
- **Single-Click Opens Persistent Tabs** - No more temporary previews! Single-click now opens requests permanently for a smoother workflow
- **Automatic Cleanup** - Deleted requests are automatically removed from the recent list
- **Always-On Security Scanning** - Security scans now run automatically on every request (simplified by removing the toggle setting)

### 🎨 Modern UI Improvements

**Enhanced Visual Design**
- **Modern Icon Button** - The "+ New request" button now uses a clean ➕ icon for better visual hierarchy and cleaner UI
- **Comprehensive Tab Context Menu** - Right-click on any tab for powerful operations:
  - 🆕 **New Request** - Create a new request from any tab
  - 📋 **Duplicate to Temp Tab** - Quickly experiment with request variations without saving
  - 📌 **Pin/Unpin Request** - Toggle pinned status directly from tab context menu
  - ⬅️ **Close Tabs on Left** - Efficiently clean up tabs to the left
  - ➡️ **Close Tabs on Right** - Efficiently clean up tabs to the right
  - 🎯 **Close All But This** - Focus on a single request
  - ❌ **Close All** - Start with a clean slate

### 🔍 Better Error Handling & Debugging

**Failed Request Debugging Made Easy**

When a request fails (connection error, invalid URL, unresolved variables, etc.):
- ✅ Response panel shows automatically
- ✅ **Request Details tab** displays exactly what parameters were attempted to be sent
- ✅ Helps quickly identify issues like:
  - Unresolved variables in URL/headers/body
  - Malformed URLs
  - Connection problems
  - Missing authentication
- ✅ Error details shown in Response tab with helpful troubleshooting suggestions
- ✅ Status displays "Connection Error" in red
- ✅ Time and Size show "N/A" to indicate no response received

**This is a game-changer for debugging API integration issues!**

---

## 🐛 Critical Bug Fixes

### Scripts Tab Indicators
**Fixed:** Script indicators (dots) not showing when opening requests from Recent Requests panel
- Scripts now properly display indicator dots on Pre-request/Post-response toggle buttons
- Indicators update immediately when switching between requests

### Request Duplication
**Fixed:** Scripts not being copied when duplicating requests
- Both "Duplicate" and "Duplicate to Temp Tab" now properly include pre-request and post-response scripts
- No more losing your carefully crafted test scripts!

### Variable Tooltips
**Fixed:** Variable value preview tooltips not working for `:paramName` path parameters
- Tooltips now work for both `{{variable}}` syntax and `:pathParam` syntax
- Tooltips display even for undefined variables (shows "❌ Undefined" message to help debugging)
- Works everywhere: URL field, Params tab, Headers tab, and all table cells
- Hover over any variable or path parameter to see its resolved value instantly

---

## 🔧 Technical Improvements

- **Improved Path Parameter Resolution** - Path parameters now use direct `main_window` reference for more reliable variable lookup
- **Enhanced Tooltip Display Logic** - Tooltips now show for both defined and undefined variables, improving debugging experience
- **Better Script Indicator Synchronization** - Script indicators update consistently across all UI components
- **Streamlined Recent Requests Behavior** - Single-click behavior is now more intuitive and responsive

---

## 📚 Developer Experience Enhancements

- **Cleaner Tab Management** - Comprehensive context menu makes managing multiple requests effortless
- **Faster Debugging** - Automatic Request Details display on errors speeds up troubleshooting
- **More Intuitive Variable Inspection** - Tooltips for all variable types (including path parameters) make debugging variable substitution trivial
- **Better Error Messages** - Connection errors now provide actionable insights into what went wrong

---

## 🎯 Why Upgrade?

This release represents a significant step forward in usability and reliability:

1. **Faster Workflows** - Single-click persistent tabs, "Open Pinned" button, and enhanced tab menu save valuable time
2. **Better Debugging** - Automatic Request Details on errors and comprehensive variable tooltips make troubleshooting much easier
3. **More Reliable** - Critical bugs fixed in script indicators, request duplication, and variable tooltips
4. **Cleaner UI** - Modern icon buttons and streamlined interface reduce visual clutter

---

## 📥 Installation

### Windows
Download and run the installer: `PostMini_Setup_v2.0.0.exe`

**Checksums:**
- **EXE:** `SHA256: [TO_BE_CALCULATED]`
- **Installer:** `SHA256: [TO_BE_CALCULATED]`

### First Time Users
See [Installation Guide](https://github.com/melerek/PostMini/blob/main/docs/USER_INSTALLATION_GUIDE.md) for detailed setup instructions.

---

## 🔄 Upgrade Notes

- **Breaking Changes:** None - fully backward compatible with v1.x
- **Settings Migration:** Automatic - all your collections, environments, and settings are preserved
- **Auto-Update:** If you're on v1.9.x, you'll be notified about this update automatically

---

## 🙏 Feedback & Support

Found a bug? Have a feature request? Want to contribute?

- 🐛 **Report Issues:** [GitHub Issues](https://github.com/melerek/PostMini/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/melerek/PostMini/discussions)
- 📖 **Documentation:** [PostMini Docs](https://github.com/melerek/PostMini/tree/main/docs)

---

## 🎉 What's Next?

Stay tuned for future enhancements! We're always working to make PostMini the best local-first API client for developers who value privacy and control.

**Previous Release:** [v1.9.9](https://github.com/melerek/PostMini/releases/tag/v1.9.9)

---

**Full Changelog:** [CHANGELOG.md](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md)
