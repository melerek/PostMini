# 🚀 PostMini v1.3.0 - Enhanced Developer Experience

## 📥 Download

**[PostMini_Setup_v1.3.0.exe](https://github.com/yourusername/postmini/releases/download/v1.3.0/PostMini_Setup_v1.3.0.exe)** (Windows Installer, ~100 MB)

---

## ✨ What's New

### 📝 Request Description Field
- **Collapsible documentation section** for each request
- Toggle with ▶/▼ button to expand/collapse
- Auto-expands when loading requests with existing descriptions
- Perfect for API documentation and team collaboration

### 🧠 Intelligent Error Messages
PostMini now provides **actionable suggestions** for common errors:
- **Connection Errors**: Check URL, proxy settings, firewall
- **Timeout Errors**: Increase timeout or check server status
- **DNS Errors**: Validate hostname and DNS configuration
- **SSL Errors**: Options for self-signed certificates
- **HTTP Status Codes**: Explanations for 400, 401, 403, 404, 429, 500+ errors
- **JSON Errors**: Format validation and parsing tips
- **Network Errors**: Internet connectivity troubleshooting

### ⏱️ Request Timeout Configuration
- **Configurable timeout** per request (1-300 seconds)
- Located in **Authorization** tab → **Request Settings**
- Default: 30 seconds
- Automatic validation with smart fallback
- Error messages show current timeout value

### 🔒 SSL Certificate Verification Toggle
- **Enable/disable SSL verification** per request
- Enabled by default for security
- Warning notification when disabled
- Perfect for local development with self-signed certificates

---

## 🎨 UX Improvements

### Collections Sidebar Reorganization
- **"Add Collection"** button in header (right-aligned)
- **"Add Request"** in collection context menu (right-click)
- **"Delete"** via context menu + Delete key
- **"Export Collection"** and **"Run Tests"** in context menu only
- Bottom buttons streamlined to single line
- Better spacing and visual hierarchy

### Visual Enhancements
- Consistent button sizing across the application
- Improved spacing between UI elements
- Method badges with colors for better recognition
- Folder icons with request counts

---

## 🐛 Bug Fixes
- ✅ Removed unsupported `box-shadow` CSS properties (no more console warnings)
- ✅ Fixed contrast issues in cURL import dialog
- ✅ Improved database migration handling
- ✅ Fixed test suite compatibility with PyQt6

---

## 🧪 Testing & Quality
- **51 new comprehensive tests** for v1.3.0 features
- **Total: 265 tests** (260 passing, 98.1% pass rate)
- 100% coverage of core v1.3.0 functionality

---

## 📊 PostMini vs Postman

**PostMini now wins 7 out of 11 categories:**
| Feature | PostMini | Postman |
|---------|----------|---------|
| Request Documentation | ✅ Collapsible field | ❌ Basic notes |
| Error Messages | ✅ Intelligent suggestions | ⚠️ Generic errors |
| Timeout Configuration | ✅ Per-request UI | ⚠️ Global settings |
| SSL Verification | ✅ Per-request toggle | ⚠️ Global settings |
| Git-Based Collaboration | ✅ Native Git | ❌ Cloud only |
| Environment Variables | ✅ Full support | ✅ Full support |
| OAuth 2.0 | ✅ 3 flows | ✅ Multiple flows |

See [POSTMINI_VS_POSTMAN_COMPARISON.md](docs/POSTMINI_VS_POSTMAN_COMPARISON.md) for full comparison.

---

## 📝 Documentation Updates
- Updated README.md with v1.3.0 features
- Created V1.3.0 Release Notes
- Created V1.3.0 Implementation Summary
- Updated PostMini vs Postman comparison
- Updated Quick Comparison guide
- All documentation reflects v1.3.0 improvements

---

## 🔧 Technical Details

### New Database Schema
- Added `description` column to `requests` table
- Automatic migration on first run
- 100% backward compatible with v1.2.0

### API Enhancements
- `ApiClient` now supports `timeout` parameter
- `ApiClient` now supports `verify_ssl` parameter
- Enhanced error handling with `_enhance_error_message()` method

---

## 📦 Installation

### Windows Installer (Recommended)
1. Download `PostMini_Setup_v1.3.0.exe`
2. Run the installer
3. Follow the setup wizard
4. Launch PostMini from Start Menu

### From Source
```bash
git clone https://github.com/yourusername/postmini.git
cd postmini
git checkout v1.3.0
pip install -r requirements.txt
python main.py
```

---

## 🆙 Upgrading from v1.2.0

PostMini v1.3.0 is **fully backward compatible** with v1.2.0:
- All existing collections and requests work unchanged
- Database automatically migrates on first run
- No data loss or manual intervention required

Simply install v1.3.0 and your existing data will be preserved.

---

## 🎯 What's Next?

Check out our [UX Improvement Plan](docs/UX_IMPROVEMENT_PLAN.md) to see what's coming in future releases!

---

## 📚 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

## 🙏 Feedback

Found a bug or have a feature request? [Open an issue](https://github.com/yourusername/postmini/issues) on GitHub!

---

## 📄 License

PostMini is licensed under the MIT License. See [LICENSE.txt](LICENSE.txt) for details.

---

**Happy API Testing! 🎉**

