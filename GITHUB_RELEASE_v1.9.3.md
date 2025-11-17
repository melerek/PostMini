# PostMini v1.9.3 - UI Typography Improvements

## 🎨 What's New

This release focuses on **typography optimization** and **visual consistency** across the interface, making PostMini more space-efficient and easier to read.

### Typography & Space Optimization

- **Tab headers** - Changed from bold to medium weight, allowing more text to fit
- **URL input** - Reduced font size from 13px to 11px, significantly more text visible for long addresses
- **Collections list** - Reduced from 13px to 12px for better visual consistency
- **All input fields** - Standardized to 11px font for uniform appearance
- **Tab spacing** - Optimized horizontal padding, showing more content before truncation

### Visual Improvements

- **Light theme visibility** - Fixed request names appearing too light/gray
- **Theme-aware colors** - Text colors automatically adjust based on theme
- **Better hierarchy** - Consistent font sizing creates clearer visual structure

## 📊 Impact

- **~20% more text** visible in URL input before truncation
- **~15% more space** in tab headers for longer request names
- **Better readability** with request names now properly visible in light theme
- **Modern look** matching VS Code's typography approach

## 📥 Installation

### Windows Installer
Download: `PostMini_Setup_v1.9.3.exe`

**Checksums:**
- **Installer SHA256:** `36FA957DFD161F10AF859B15246DCA4FE16F047701976C9C29F5EC9F25ACA38F`
- **EXE SHA256:** `DC3D372E591513E63CA1758F5294E5582C3D29853F48ECE5A62781C5F116DBA6`

### Verification
```powershell
# Verify installer checksum
Get-FileHash -Path "PostMini_Setup_v1.9.3.exe" -Algorithm SHA256
```

## 🔄 Auto-Update

If you're already using PostMini v1.9.0 or later, the app will automatically notify you of this update. Click "Update Now" to download and install.

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md) for complete details.

## 🐛 Known Issues

None reported for this release.

## 💬 Feedback

Found a bug or have a suggestion? [Open an issue](https://github.com/melerek/PostMini/issues) or start a [discussion](https://github.com/melerek/PostMini/discussions).

---

**Full Changelog**: https://github.com/melerek/PostMini/compare/v1.9.2...v1.9.3
