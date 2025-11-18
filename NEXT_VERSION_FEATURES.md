# Features for Next Release

Track all changes here as they're implemented. This will become the changelog entry for the next version.

## ✨ New Features
- **Cookie Management** - Full HTTP cookie support similar to Postman:
  - New "Cookies" tab for viewing and managing cookies
  - Automatic cookie persistence - cookies from responses are automatically saved
  - Automatic cookie sending - cookies are automatically sent with matching requests
  - Manual cookie management - add, edit, and delete cookies manually
  - Domain-based organization with path, expiration, Secure, and HttpOnly flags
  - "Clear All" and "Delete Expired" bulk actions
  - Database persistence across sessions
  - Content indicator dot shows when cookies exist
  - Full integration with request/response flow

- **Path Parameter Support** - Postman-compatible :paramName syntax in URLs:
  - URLs like `/users/:userId/posts/:postId` now automatically resolve path parameters
  - Path parameters use variable system (environment, collection, or extracted variables)
  - Example: `{{baseUrl}}/order/v1/Rating/:invitationId` resolves both {{variables}} and :params
  - Seamless Postman import compatibility - collections with path parameters work immediately
  - Priority resolution: extracted variables > collection variables > environment variables
  - **Visual feedback** - Path parameters are highlighted in URL field (green when defined, red when undefined)
  - **Hover tooltips** - Mouse over `:paramName` shows resolved value with copy button
  - Same tooltip UX as `{{variable}}` syntax for consistency

## 🐛 Bug Fixes
- (No fixes added yet)

## 🔧 Technical Improvements
- **Database** - Added cookies table with comprehensive schema (domain, name, value, path, expires, secure, http_only, same_site)
- **ApiClient** - Extended with cookie management methods: get_cookies(), set_cookie(), clear_cookies(), load_cookies_from_db(), save_cookies_to_db()
- **CookieTabWidget** - New widget component for cookie management UI with editable table and bulk operations
- **Variable Substitution** - Added `substitute_path_params()` method to handle :paramName syntax
- **EnvironmentManager** - Updated `substitute_in_request()` to automatically resolve path parameters after variable substitution

## 📚 Documentation
- (No documentation updates yet)

## 🎨 UI/UX Enhancements
- **Improved** - Scripts tab now uses Postman-style toggle between Pre-request and Post-response scripts
- **Space-saving** - Only one script editor visible at a time in upper section, console always at bottom
- **Better UX** - Toggle buttons with active/inactive states for clear visual feedback
- **Content Indicators** - Added dot indicators (·) to tab headers and buttons:
  - Body tab shows dot when body text is not empty
  - Scripts tab shows dot when either pre-request or post-response script exists
  - Cookies tab shows dot when cookies exist
  - Pre-request/Post-response toggle buttons show dots when respective scripts exist
  - Provides at-a-glance visibility of where content exists in the request
- **Consistent Styling** - Fixed button and dropdown font sizes across Cookies and Tests tabs to match Scripts tab (11px)

