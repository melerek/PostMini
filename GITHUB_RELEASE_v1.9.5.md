# PostMini v1.9.5 - Light Theme Fixes & Script Header Preservation

## 🐛 Bug Fixes

### Light Theme Button Styling (Critical Fix)
- **Fixed** - Scripts tab buttons (Clear, Clear Console, Hide) now display correctly in light theme
- **Fixed** - Response section buttons (Copy Response, Pretty, Wrap, Search) now use proper light theme colors  
- **Fixed** - Button sizes consistent across both themes (reduced light theme padding from 4px 12px to 4px 8px)
- **Fixed** - Clear button and Snippets dropdown now perfectly vertically aligned
- **Fixed** - Test tab separator no longer uses hardcoded dark theme color

### Pre-request Script Headers Preservation
- **Fixed** - Headers added via `pm.request.headers.add()` in pre-request scripts are now correctly included in HTTP requests
- **Root cause** - Variable re-substitution was discarding script-modified headers
- **Solution** - Script-modified headers are preserved and merged after variable re-substitution with proper priority

## 🔧 Technical Improvements
- **Theme-aware button system** - Added `_update_response_buttons_style()` method for dynamic theme switching
- **Console button theme support** - Extended `_update_clear_button_styles()` to include Clear Console and Hide buttons
- **Button reference storage** - Stored references to all theme-dependent buttons for proper updates
- **Dual-theme consistency** - All inline button styles now properly adapt to active theme

## 📚 Documentation
- **Added** comprehensive "Styling & Theme Management" section to copilot-instructions.md
- **Documented** dual-theme update checklist and critical patterns
- **Added** bug prevention guidelines for theme-related changes

---

## 📥 Installation

### Windows Installer
Download and run `PostMini_Setup_v1.9.5.exe`

**Checksums:**
- **Installer SHA256:** `99370E1EC3411DA707E747AF6E9867299B42FA01AD464FF356068057C0E8B3D6`
- **Executable SHA256:** `E5E78A3F2C9EC18CBD02EE39482A7FB97A7B570E1AAEFE90A44C2FCC5CD6D6CE`

### Verify Download
```powershell
# PowerShell verification command
Get-FileHash -Path "PostMini_Setup_v1.9.5.exe" -Algorithm SHA256
```

Expected output: `99370E1EC3411DA707E747AF6E9867299B42FA01AD464FF356068057C0E8B3D6`

---

## 🔄 Update from Previous Version

If you have PostMini installed, the application will automatically notify you about this update. You can also:
1. Download the new installer
2. Run it to upgrade your existing installation
3. Your data (collections, environments, settings) will be preserved

---

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md) for complete version history.

---

## 🎯 What's Next?

Stay tuned for upcoming features! Track development on the [GitHub repository](https://github.com/melerek/PostMini).

---

**Note:** This is a maintenance release focusing on UI consistency and script functionality. All existing features remain fully functional.
