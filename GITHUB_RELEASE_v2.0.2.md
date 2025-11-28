# PostMini v2.0.2 - Body Type Support & UX Improvements

This release brings comprehensive Postman-compatible body type support and several UX improvements based on user feedback.

## ✨ New Features

### Comprehensive Body Type Support
- **Full Postman body type compatibility**: none, raw, form-data, x-www-form-urlencoded
- **Body Type Selector**: Dropdown in request editor (matches Postman UX)
- **Smart Content-Type Headers**: Automatically sets correct headers when body type changes
- **Postman Import Accuracy**: Collections now preserve original body types instead of converting everything to JSON
- **Test Coverage**: 15 comprehensive tests covering all scenarios (100% passing)

### Automatic Content-Type Management
- **Auto-Header Setting**: Selecting "form-data" sets `Content-Type: multipart/form-data`
- **Auto-Header Setting**: Selecting "x-www-form-urlencoded" sets `Content-Type: application/x-www-form-urlencoded`
- **Manual Override**: Users can still manually edit headers if needed
- **Seamless Integration**: Works with all existing request execution flows

### Enhanced Postman Import
- **Body Type Mapping**: Correctly imports `urlencoded` → `x-www-form-urlencoded` and `formdata` → `form-data`
- **Bidirectional Conversion**: Export to Postman format also converts back correctly
- **Database Migration**: Added `body_type` column with seamless upgrade from v2.0.1

## 🐛 Bug Fixes

### Request Details Display
- **Fixed**: Request Details now shows actual sent format (URL-encoded, multipart, etc.) instead of JSON
- **Before**: Showed `{"key": "value"}` even when sent as `key=value&foo=bar`
- **After**: Shows `key=value&foo=bar` for x-www-form-urlencoded requests
- **Impact**: Users can now verify exact format sent to server

### Postman Body Type Import
- **Fixed**: Imported collections with `urlencoded` or `formdata` no longer show as "raw"
- **Before**: Opening imported request showed incorrect body type in dropdown
- **After**: Body type dropdown correctly reflects imported Postman body type
- **Impact**: Eliminates confusion when switching between Postman and PostMini

### Tooltip Behavior
- **Fixed**: Variable tooltips now stay visible for 1 second after mouse leaves
- **Before**: Tooltip disappeared instantly when trying to click copy button
- **After**: 1-second grace period allows clicking copy button comfortably
- **Impact**: Significantly improved UX for copying variable values

### Body Type Dropdown Styling
- **Fixed**: Body type dropdown now matches professional styling of other UI elements
- **Before**: Inconsistent font size and height compared to auth dropdown
- **After**: Uniform appearance (font-size: 11px, height: 24px, proper padding)
- **Impact**: More polished and consistent UI

### Path Parameter Substitution
- **Fixed**: Path parameters (`:paramName` syntax) now substitute correctly when no environment active
- **Before**: URLs like `/users/:userId` showed parameters in tooltips but weren't replaced in actual requests
- **After**: Path parameters correctly substituted using collection/extracted variables even without active environment
- **Impact**: Path parameters work reliably in all scenarios

## 🔧 Technical Improvements

- **Database Migration**: Backward-compatible `body_type` column addition
- **MainWindow Integration**: All create/update request calls updated for body type parameter
- **Collection I/O**: `.postmini` format includes body_type for Git Sync compatibility
- **Tab State**: Body type preserved when switching between request tabs
- **Code Quality**: Comprehensive test suite with integration and unit tests

## 📊 Test Results

**Total Tests**: 15 (11 unit + 4 integration)
**Status**: ✅ All Passing
**Coverage Areas**:
- Body type selection UI changes
- Content-Type auto-setting
- Postman import/export body type mapping
- Request execution with different body types
- Request Details display conversion
- Tab switching state preservation

## 📦 Installation

**Windows Installer**: [PostMini_Setup_v2.0.2.exe](https://github.com/melerek/PostMini/releases/download/v2.0.2/PostMini_Setup_v2.0.2.exe)

**Checksums**:
- **Installer SHA256**: `A88F211BDEB0619692B1EF4034644E458A0C8B66B770CF096632D15D086AB4B2`
- **EXE SHA256**: `83B7056189433F54FB8E89C3909DFC98EC94151953D3215088F0946C3596587C`

## 🚀 Upgrade Notes

- **Automatic Migration**: Database migration adds `body_type` column on first launch
- **Existing Requests**: All existing requests default to 'raw' body type (preserves current behavior)
- **No Breaking Changes**: Fully backward compatible with v2.0.1

## 🔗 Links

- [Full Changelog](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md#202---2025-11-28)
- [Documentation](https://github.com/melerek/PostMini#readme)
- [Issue Tracker](https://github.com/melerek/PostMini/issues)

---

**What's Next?** Check out our [roadmap](https://github.com/melerek/PostMini#roadmap) to see what's coming in future releases!
