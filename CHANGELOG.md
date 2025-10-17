# Changelog

All notable changes to PostMini will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] - 2025-10-17

### ✨ Added
- **Dynamic Variables System**: 38+ auto-generated variables for test data
  - Core: `$guid`, `$randomUUID`, `$timestamp`, `$isoTimestamp`, `$randomInt`
  - Strings: `$randomString`, `$randomAlphaNumeric`
  - Personal: `$randomEmail`, `$randomUserName`, `$randomFirstName`, `$randomLastName`, `$randomFullName`, `$randomNamePrefix`, `$randomNameSuffix`
  - Contact: `$randomPhoneNumber`, `$randomPhoneNumberExt`
  - Location: `$randomCity`, `$randomCountry`, `$randomCountryCode`, `$randomStreetName`, `$randomStreetAddress`
  - Internet: `$randomIP`, `$randomIPV6`, `$randomMACAddress`, `$randomPassword`, `$randomUrl`, `$randomDomainName`
  - Visual: `$randomColor`, `$randomHexColor`
  - Financial: `$randomPrice`, `$randomCreditCardNumber`
  - Business: `$randomCompanyName`, `$randomCompanySuffix`, `$randomJobTitle`
  - Logic: `$randomBoolean`
  - Postman-compatible `$variable` syntax
  - Works in URLs, headers, parameters, and request bodies
  - Integrated with existing `{{variable}}` substitution system
  
- **OpenAPI/Swagger Import**: Auto-generate collections from API specifications
  - Supports OpenAPI 3.0, 3.1, and Swagger 2.0
  - Imports JSON and YAML formats
  - Auto-generates example request bodies from schemas
  - Extracts parameters, headers, and authentication
  - Intelligent schema-to-example conversion
  - Import preview dialog with API summary
  - Preserves endpoint descriptions and documentation
  - Click "📄 Import OpenAPI" button to import specs

### 🎨 UX Improvements
- **Optimized Collections Pane**: Consolidated import buttons into dropdown menu
  - Replaced 3 separate import buttons with single "📥 Import" dropdown
  - Options: Import Collection (JSON), Import cURL Command, Import OpenAPI/Swagger
  - Significantly reduces horizontal space usage in collections pane
  
- **Smart Duplicate Name Handling**:
  - Intelligent detection of duplicate collection names
  - Auto-suggests unique names (e.g., "My Collection (2)")
  - User-friendly dialogs instead of raw database errors
  - Method-aware duplicate request name detection (GET vs POST can have same name)
  - Applied to: Add Collection, Import OpenAPI, Add Request, Rename Request, Duplicate Request

### 🐛 Bug Fixes
- **Git Sync Dark Mode**: Fixed button and dialog visibility in dark theme
  - Changed status button styling from background-color to colored borders
  - Removed hardcoded light colors from Git Sync Settings dialog info boxes
  - All Git Sync UI elements now respect theme colors
  
- **Git Sync Status Refresh**: Fixed status not updating after dialog close
  - Status now refreshes immediately when closing Git Sync dialog
  - Added periodic auto-refresh (every 30 seconds) to detect external changes
  - Timer automatically starts/stops with Git Sync enable/disable
  
- **Dynamic Variables Without Environment**: Fixed substitution when no environment active
  - Dynamic variables now work regardless of environment selection
  - Ensures consistent behavior for `$variable` syntax

### 🧪 Testing
- Added 44 comprehensive tests for Dynamic Variables
- Added 25 comprehensive tests for OpenAPI/Swagger import
- Added 20 comprehensive tests for UX improvements and duplicate name handling
- Total test count: 354 tests (347 passing, 98.0% pass rate)
- 100% coverage of new v1.4.0 features

### 📝 Documentation
- Created V1.4.0 Release Notes with comprehensive feature documentation
- Updated README.md with usage examples for Dynamic Variables and OpenAPI import
- Created 75-page Feature Feasibility Assessment for future planning
- Updated CHANGELOG.md with v1.4.0 information
- Updated comparison documentation (POSTMINI_VS_POSTMAN_COMPARISON.md)
- Updated quick comparison guide (COMPARISON_QUICK.md)

### 🔧 Technical
- Added `PyYAML>=6.0` dependency for OpenAPI/Swagger parsing
- Created `src/features/dynamic_variables.py` module (450 lines)
- Created `src/features/openapi_importer.py` module (550 lines)
- Enhanced `src/features/variable_substitution.py` with dynamic variable support
- Added OpenAPI import UI integration in `src/ui/main_window.py`
- 100% backward compatible with v1.3.0

### 🎯 Impact
- **Feature Parity**: PostMini now matches or exceeds Postman in 9/10 core API testing features
- **Time Savings**: OpenAPI import can save hours when working with documented APIs
- **Testing Efficiency**: Dynamic variables eliminate manual test data creation
- **Professional Workflows**: Enterprise-ready API testing capabilities

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

