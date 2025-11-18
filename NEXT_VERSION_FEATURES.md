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

- **Variable Autocomplete** - Smart autocomplete for variables when typing:
  - **Triggers**: Autocomplete appears when typing `{{` or `:` (for path parameters)
  - **All Scopes**: Shows variables from environment, collection, extracted, and dynamic variables
  - **Visual Design**: Modern dropdown with variable name, scope badge (ENV/COL/EXT/DYNAMIC), and value preview
  - **Scope Colors**: Blue (environment), Purple (collection), Green (extracted), Orange (dynamic)
  - **Navigation**: Tab/Down Arrow for next, Shift+Tab/Up Arrow for previous, Enter to select, Escape to close
  - **Mouse Support**: Click to select variable
  - **Live Filtering**: Type after `{{` to filter variables by name or value
  - **Smart Insertion**: Automatically adds closing `}}` for variables, correct syntax for path parameters
  - **Supported Fields**: URL input, request body, params table, headers table
  - **Theme-Aware**: Fully integrated with both light and dark themes

## 🐛 Bug Fixes
- (No fixes added yet)

## 🔧 Technical Improvements
- **Database** - Added cookies table with comprehensive schema (domain, name, value, path, expires, secure, http_only, same_site)
- **ApiClient** - Extended with cookie management methods: get_cookies(), set_cookie(), clear_cookies(), load_cookies_from_db(), save_cookies_to_db()
- **CookieTabWidget** - New widget component for cookie management UI with editable table and bulk operations
- **Variable Substitution** - Added `substitute_path_params()` method to handle :paramName syntax
- **EnvironmentManager** - Updated `substitute_in_request()` to automatically resolve path parameters after variable substitution
- **New Widget Components**:
  - `VariableAutocompleteWidget` - Main autocomplete dropdown with filtering and navigation
  - `VariableAutocompleteItem` - Custom list item widget showing variable name, scope badge, and value preview
  - `AutocompleteTextEdit` - QTextEdit subclass with autocomplete trigger detection and insertion
- **Enhanced HighlightedLineEdit** - Extended with autocomplete functionality for URL field
- **Theme Support** - Autocomplete widget fully integrated with theme switching system

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
- **Modern Autocomplete** - Professional autocomplete UI with scope badges, value previews, and smooth keyboard navigation

