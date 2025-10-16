# Changelog

All notable changes to PostMini will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2025-10-16

### ✨ Added
- **Request Description Field**: Collapsible description/notes section for documenting API requests
  - Toggle with ▶/▼ button
  - Auto-expands when loading requests with existing descriptions
  - Fully integrated with save/load functionality
  
- **Enhanced Error Messages**: Intelligent error detection with actionable suggestions
  - Connection errors with troubleshooting steps
  - Timeout errors with configuration guidance
  - DNS resolution errors with hostname validation tips
  - SSL/Certificate errors with local development workarounds
  - HTTP status code explanations (400, 401, 403, 404, 429, 500+)
  - JSON parsing errors with format validation tips
  - Network errors with connectivity suggestions
  
- **Request Timeout Configuration**: Per-request timeout settings (1-300 seconds)
  - Located in Authorization tab → Request Settings
  - Default: 30 seconds
  - Automatic validation with fallback
  - Error messages reference current timeout value
  
- **SSL Certificate Verification Toggle**: Per-request SSL verification control
  - Enable/disable SSL certificate verification
  - Enabled by default for security
  - Warning notification when disabled
  - Perfect for local development with self-signed certificates

### 🎨 Improved
- **Collections Sidebar Reorganization**: Cleaner, more intuitive layout
  - "Add Collection" button moved to header (right-aligned)
  - "Add Request" moved to collection right-click context menu
  - "Delete" available via context menu + Delete key
  - "Export Collection" and "Run Tests" in context menu only
  - Bottom buttons streamlined to single line
  - Better spacing and visual hierarchy

- **UI/UX Enhancements**:
  - Better spacing between UI elements
  - Consistent button sizing across the application
  - Improved visual hierarchy in collections tree
  - Method badges with colors for better recognition
  - Folder icons with request counts

### 🐛 Fixed
- Removed unsupported `box-shadow` CSS properties causing console warnings
- Fixed contrast issues in cURL import dialog
- Fixed test suite compatibility with newer PyQt6 versions
- Improved database migration handling

### 🧪 Testing
- Added 51 new comprehensive tests for v1.3.0 features
- Total test count: 265 tests
- Pass rate: 98.1% (260 passing)
- 100% coverage of core v1.3.0 functionality

### 📝 Documentation
- Updated README.md with v1.3.0 features
- Created comprehensive V1.3.0 Release Notes
- Created V1.3.0 Implementation Summary
- Updated PostMini vs Postman comparison
  - PostMini now wins 7 out of 11 categories
- Updated Quick Comparison guide
- All documentation reflects v1.3.0 improvements

### 🔧 Technical
- Database schema updated with `description` column for requests table
- Automatic database migration on first run
- ApiClient enhanced with timeout and SSL verification parameters
- Improved error handling architecture with `_enhance_error_message()` method
- 100% backward compatible with v1.2.0

---

## [1.2.0] - 2025-10-14

### Added
- **Context Menus**: Right-click functionality for collections, requests, and responses
- **Recent Requests Panel**: Quick access to recently viewed requests with pinning
- **Enhanced Visual Feedback**: Toast notifications, loading states, syntax highlighting
- **Polished UI**: Focus states, hover effects, improved spacing

### Documentation
- Phase 3 completion documentation
- Updated comparison guides

---

## [1.1.2] - 2025-10-12

### Added
- **Dark Mode**: Professional dark theme with one-click toggle
- **Application Icon**: Branded icon in taskbar and window
- **cURL Import/Export**: Paste cURL commands directly to create requests
- **Improved UI**: Refined styling and better cell editors

### Fixed
- Icon loading improvements
- Stylesheet refinements
- Cell editor padding issues

---

## [1.1.0] - 2025-10-10

### Added
- **Git-Based Collaboration**: Native Git integration for version control
- **Environment Variables**: Support for `{{variables}}` in requests
- **Request History**: Track and replay all API calls
- **Code Generation**: Generate code in 7 languages
- **OAuth 2.0 Support**: Full OAuth flows (Authorization Code, Client Credentials, Password Grant)
- **API Testing**: Automated testing with 8 assertion types

### Changed
- Major architectural improvements
- Enhanced database schema
- Improved error handling

---

## [1.0.0] - 2025-10-01

### Added
- **Initial Release**: Complete API client functionality
- **Collections Management**: Organize requests into collections
- **HTTP Methods**: Support for GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Request Configuration**: URL parameters, headers, body, authentication
- **Response Viewer**: JSON formatting, headers, status codes
- **Persistent Storage**: SQLite database for collections and requests
- **Modern UI**: Clean PyQt6 interface
- **Cross-platform**: Windows, macOS, Linux support

---

## Release Links

- **v1.3.0**: [Download PostMini_Setup_v1.3.0.exe](dist/installer/PostMini_Setup_v1.3.0.exe)
- **v1.2.0**: [Download PostMini_Setup_v1.2.0.exe](dist/installer/PostMini_Setup_v1.2.0.exe)
- **v1.1.2**: [Download PostMini_Setup_v1.1.2.exe](dist/installer/PostMini_Setup_v1.1.2.exe)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

