# Features for Next Release

Track all changes here as they're implemented. This will become the changelog entry for the next version.

## ✨ New Features

### Comprehensive Postman Body Type Support (COMPLETE END-TO-END)
- **Added**: Full support for all Postman body types: `none`, `raw`, `form-data`, `x-www-form-urlencoded`
- **UI Enhancement**: Body type selector dropdown in request editor (Postman-style)
  - Options: none, form-data, x-www-form-urlencoded, raw
  - Smart placeholder text updates based on selection
  - Disables editor when "none" is selected
- **Database**: Added `body_type` column to `requests` table with migration (default: 'raw')
- **Postman Import**: Collection imports now preserve original body types instead of converting everything to JSON
- **API Execution**: 
  - `multipart/form-data`: Sends data as dict with automatic boundary handling
  - `application/x-www-form-urlencoded`: Converts JSON to URL-encoded format
  - `application/json`: Uses JSON parameter (existing behavior)
- **Auto-Headers**: Postman converter automatically sets `Content-Type` headers for formdata and urlencoded bodies
- **MainWindow Integration**: All create_request/update_request calls updated to pass body_type parameter
- **Collection Export/Import**: `.postmini` format includes body_type field for Git Sync compatibility
- **Tab State Management**: Body type preserved when switching between tabs
- **Impact**: Postman collections with different body types now work identically after import to PostMini
- **Test Coverage**: 15 comprehensive tests covering all scenarios (11 unit + 4 integration tests, all passing)

## 🐛 Bug Fixes

### Postman Body Type Import Mapping
- **Fixed**: Postman collection imports now correctly map body types to PostMini's internal format
- **Issue**: When importing collections with `urlencoded` or `formdata` body types, body type dropdown showed "raw" instead of correct type, even though request executed correctly
- **Root Cause**: PostmanConverter used Postman body type names (`"urlencoded"`, `"formdata"`) directly instead of mapping to internal names (`"x-www-form-urlencoded"`, `"form-data"`)
- **Resolution**:
  - Added bidirectional mapping in `PostmanConverter`:
    - Import: Postman `"urlencoded"` → PostMini `"x-www-form-urlencoded"`
    - Import: Postman `"formdata"` → PostMini `"form-data"`
    - Export: PostMini `"x-www-form-urlencoded"` → Postman `"urlencoded"`
    - Export: PostMini `"form-data"` → Postman `"formdata"`
  - Export now properly converts JSON body back to Postman array format for urlencoded/formdata
- **Impact**: Imported requests now display correct body type in dropdown, matching what was in original Postman collection
- **Example**: OAuth token requests with `body.mode: "urlencoded"` now show "x-www-form-urlencoded" in body type selector
- **Test Coverage**: 4 comprehensive tests covering import mapping, export mapping, and roundtrip conversions

### Request Details Display Shows Actual Sent Format
- **Fixed**: Request Details tab now displays the actual body format sent to the server, not the JSON stored in the editor
- **Issue**: When user selected `x-www-form-urlencoded` body type and entered JSON in editor, Request Details showed JSON instead of the URL-encoded format that was actually sent
- **Root Cause**: Request Details viewer displayed body as-is from storage, without applying the same conversion logic that ApiClient uses during execution
- **Resolution**: 
  - Added `_convert_body_for_display()` method that mirrors ApiClient conversion logic
  - Request Details now shows URL-encoded format (`grant_type=password&username=admin%40ecovadis.com`) instead of JSON
  - Multipart form-data displays as structured key-value pairs
- **Impact**: Users can now see exactly what was sent to the server for debugging and verification
- **Test Coverage**: 4 comprehensive tests covering URL-encoded, multipart, raw JSON, and Content-Type auto-setting

### Content-Type Header Auto-Setting
- **Fixed**: Content-Type header now automatically set when user selects body type from dropdown
- **Issue**: Users had to manually add Content-Type header even after selecting form-data or x-www-form-urlencoded from body type selector
- **Root Cause**: `_on_body_type_changed()` only updated placeholder text, didn't modify headers table
- **Resolution**:
  - Added `_auto_set_content_type_header()` method that sets appropriate header based on body type
  - `form-data` → `multipart/form-data`
  - `x-www-form-urlencoded` → `application/x-www-form-urlencoded`
  - `raw` → `application/json`
  - `none` → Removes Content-Type header
- **Impact**: Streamlined workflow - selecting body type automatically configures correct Content-Type header
- **Test Coverage**: Tests verify all body types set correct headers, including header updates when changing types

### Form-Urlencoded Content Type Handling
- **Fixed**: Requests with `Content-Type: application/x-www-form-urlencoded` now correctly convert JSON body to URL-encoded format
- **Issue**: When user entered JSON body (`{"key": "value"}`) with form-urlencoded content type, the app sent raw JSON instead of URL-encoded format (`key=value`)
- **Root Cause**: `ApiClient.execute_request()` only checked for `application/json` content type but didn't handle form-urlencoded conversion
- **Resolution**: Added logic to detect form-urlencoded content type and convert JSON body to proper URL-encoded format using `urllib.parse.urlencode()`
- **Impact**: OAuth token endpoints and other APIs requiring form-urlencoded data now work correctly (e.g., `grant_type=password&username=user&password=pass`)
- **Example**: Body `{"grant_type": "password", "username": "admin@ecovadis.com"}` now correctly sends as `grant_type=password&username=admin%40ecovadis.com`

### Path Parameter Substitution Without Active Environment  
- **Fixed**: Path parameters (`:paramName` syntax) not being substituted when no environment is active
- **Issue**: When user had no active environment, URLs like `/users/:userId` showed parameters in tooltips but weren't replaced in actual HTTP requests
- **Root Cause**: `_send_request()` method only called `substitute_path_params()` when `env_manager.has_active_environment()` was True
- **Resolution**: Added `substitute_path_params()` call to both non-environment paths (initial substitution and pre-request script re-substitution)
- **Impact**: Path parameters now work correctly with collection and extracted variables, regardless of environment status
- **Example**: `{{baseUrl}}/order/v1/Rating/:invitationId` now properly resolves both `{{}}` and `:` syntax without active environment

## 🔧 Technical Improvements

### UI Polish and Consistency
- **Fixed**: Body type dropdown now matches auth dropdown styling (proper font size, item padding, and height)
- **Improvement**: Variable preview tooltip hiding behavior is now consistent and user-friendly
  - Tooltip remains visible when hovering over variable in URL/header fields
  - 1-second grace period after leaving line edit allows clicking "Copy to Clipboard" button
  - Tooltip cancels grace period and stays visible when mouse re-enters it
  - Uses continuous position checking (100ms intervals) to detect when user returns to variable
  - Prevents tooltip from disappearing too quickly when trying to interact with it
- **Impact**: More polished UI appearance and intuitive tooltip interaction

### Database Schema Enhancement
- Added `body_type` TEXT column to `requests` table with automatic migration
- Updated `create_request()` and `update_request()` methods to support body_type parameter
- Backward compatible - existing databases migrate seamlessly with default 'raw' value
- All 8 create_request() call sites in MainWindow updated with body_type parameter
- All 2 update_request() call sites in MainWindow updated with body_type parameter

### API Client Refactoring
- Implemented comprehensive content-type detection and handling
- Separated multipart/form-data, urlencoded, and JSON body processing
- Automatic Content-Type header management for multipart (removes to let requests add boundary)

### UI/UX Integration
- Added body type selector to request editor with 4 options
- Integrated body_type into tab state capture/restore (prevents loss when switching tabs)
- Helper methods: `_on_body_type_changed()` and `_update_body_editor_for_type()`
- Body editor dynamically updates placeholder text based on selected type
- Body editor disabled when "none" type selected

## 📚 Documentation

- Created `docs/COMPREHENSIVE_BODY_TYPE_SUPPORT.md` - complete implementation overview
- Created `docs/BODY_TYPE_INTEGRATION_GUIDE.md` - step-by-step integration guide (now completed)
- Updated CHANGELOG.md with detailed feature and bug fix descriptions
- Updated `.github/copilot-instructions.md` with Path Parameter Substitution bug pattern

## 🎨 UI/UX Enhancements

### Body Type Selector
- Added Postman-style body type dropdown above body editor
- Options: none, form-data, x-www-form-urlencoded, raw
- Context-aware placeholder text based on selection
- Automatic UI state management (disable editor for "none")
- Full integration with save/load/tab switching

## 🧪 Testing

- Created `tests/test_body_types.py` with 7 comprehensive unit tests (all passing)
- Created `tests/test_form_urlencoded.py` with 4 content-type tests (all passing)
- Created `tests/test_body_type_integration.py` with 4 end-to-end integration tests (all passing)
- **Total: 15/15 tests passing** for body type support
- Tests cover: Postman import, database storage, API execution, export/import roundtrip, legacy data handling




