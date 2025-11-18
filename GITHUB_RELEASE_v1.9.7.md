# PostMini v1.9.7 - Cookie Management & Path Parameters

**Release Date:** February 2, 2025

## 🎉 Major New Features

### 🍪 Complete Cookie Management System
PostMini now includes full HTTP cookie support, matching Postman's functionality:

- **New Cookies Tab** - Dedicated interface for viewing and managing all cookies
- **Automatic Cookie Handling** - Cookies from responses are automatically saved and sent with matching requests
- **Manual Control** - Add, edit, and delete cookies with full control over all attributes
- **Smart Organization** - Domain-based grouping with support for paths, expiration, Secure, and HttpOnly flags
- **Bulk Actions** - Quickly clear all cookies or remove expired ones
- **Visual Indicators** - Content dot shows when cookies are present
- **Database Persistence** - All cookies persist across sessions

### 🔗 Path Parameter Support (Postman-Compatible)
Full support for Postman's `:paramName` URL syntax:

- **Auto-Resolution** - URLs like `/users/:userId/posts/:postId` automatically substitute values
- **Variable Integration** - Path parameters work seamlessly with environment, collection, and extracted variables
- **Visual Feedback** - Path parameters are highlighted (green when defined, red when undefined)
- **Hover Tooltips** - Mouse over `:paramName` to see the resolved value
- **Priority System** - Smart resolution: extracted variables → collection variables → environment variables
- **Example**: `{{baseUrl}}/order/v1/Rating/:invitationId` resolves both template variables and path parameters

## 🎨 UI/UX Improvements

### Postman-Style Scripts Interface
- **Toggle Design** - Switch between Pre-request and Post-response scripts with clear visual feedback
- **Space-Efficient** - Only one script editor visible at a time
- **Always-Visible Console** - Console output remains at bottom for all script types

### Content Indicators
- **At-a-Glance Visibility** - Small dots (·) on tabs show where content exists:
  - Body tab • Scripts tab • Cookies tab
  - Pre-request script button • Post-response script button
- **Never Miss Content** - Instantly see which parts of your request are populated

### Consistent Styling
- **Fixed Font Sizes** - All buttons and dropdowns use consistent 11px font
- **Aligned Elements** - Buttons, dropdowns, and inputs properly aligned across all tabs
- **Theme Consistency** - Improved styling across both light and dark themes

## 🔧 Technical Details

### New Components
- `CookieTabWidget` - Complete cookie management UI
- `substitute_path_params()` - Path parameter resolution engine
- Enhanced `HighlightedLineEdit` - Path parameter highlighting and tooltips

### Database Changes
- New `cookies` table with full schema support
- Tracks domain, name, value, path, expiration, secure, http_only, same_site flags

### API Enhancements
- `ApiClient` extended with 5 new cookie management methods
- `EnvironmentManager` now handles path parameter substitution automatically
- Request flow updated to load/save cookies seamlessly

## 📦 Installation

**Windows Installer:**
```
PostMini_Setup_v1.9.7.exe
```

**Checksums:**
- Installer SHA256: `C66612E7ABF297D82ADA93C16770270F2EBFB44D404EB8E225CF6A9534A40F20`
- Executable SHA256: `30278519DD4E3CF1B6E596089D11543A100CE8E0136BA25901D861B9B0CB9F7F`

## 🔄 Upgrading from Previous Versions

1. Download the new installer
2. Run the installer (will upgrade in-place)
3. Your data is safe - all collections, environments, and settings are preserved
4. New cookies table is created automatically on first launch

## 🐛 Known Issues

None reported for this release.

## 💡 Tips for New Features

### Using Cookies
1. Open any request and click the "Cookies" tab
2. Cookies are automatically saved from responses
3. Manually add cookies with the "+ Add Cookie" button
4. Use "Clear All" or "Delete Expired" for maintenance

### Using Path Parameters
1. In your URL, use `:paramName` syntax (e.g., `/users/:userId`)
2. Define the parameter value in environment, collection, or extracted variables
3. Hover over the path parameter to see the resolved value
4. Green highlight = defined, Red highlight = undefined

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md) for complete details.

## 🙏 Feedback

Found a bug? Have a feature request? 
- Open an issue: https://github.com/melerek/PostMini/issues
- Discussions: https://github.com/melerek/PostMini/discussions

---

**Previous Release:** [v1.9.6](https://github.com/melerek/PostMini/releases/tag/v1.9.6) - Consolidated Notification System
