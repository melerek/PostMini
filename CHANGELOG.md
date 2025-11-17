# Changelog

All notable changes to PostMini will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.9.4] - 2025-11-17

### ✨ New Features

#### 📋 Variable Tooltip Copy Button
- **Interactive tooltips** - Added "Copy to Clipboard" button to variable hover tooltips (Postman-style)
- **Works everywhere** - URL input, parameters, headers, body, and all other variable fields
- **Visual feedback** - Shows variable name, resolved value, and copy button with green checkmark confirmation
- **Smart behavior** - Auto-hides after 500ms when mouse leaves tooltip, stays visible when hovering over button
- **Custom widget** - Created `VariableTooltipWidget` with QPushButton integration for clipboard functionality

#### 🔗 Live URL ↔ Params Synchronization
- **Real-time sync** - Query parameters automatically populate in Params tab as you type in URL
- **Bidirectional** - Editing Params table updates URL query string instantly
- **Postman-compatible** - Replicates Postman's live query parameter behavior exactly
- **Automatic cleanup** - Removing params from URL removes them from table, and vice versa
- **URL parsing** - Robust URL parsing using urllib.parse with proper query string handling

#### 🔄 Auto-refresh Variable Inspector
- **Automatic updates** - Variable inspector panel refreshes automatically after scripts run
- **Pre-request scripts** - Shows updated values immediately when scripts call `pm.collectionVariables.set()`
- **Post-response scripts** - Reflects variable changes from response extraction scripts
- **Performance optimized** - Only refreshes when panel is open, no impact when closed
- **Live visibility** - No need to close/reopen panel to see updated variable values

#### 📚 Collection Variable Code Snippets
- **Pre-request snippets** - Added "Set Collection Variable" and "Get Collection Variable" examples
- **Post-response snippets** - Added snippets for extracting and validating collection variables
- **Quick access** - Available in Snippets dropdown on Scripts tab
- **Copy-paste ready** - Fully working examples using `pm.collectionVariables` API

### 🐛 Bug Fixes

#### 🔧 Pre-request Script Variable Timing (Critical Fix)
- **Root cause fixed** - Pre-request scripts now properly execute BEFORE variable substitution
- **Original values preserved** - Stores unsubstituted URL, params, headers, body before first substitution
- **Re-substitution from originals** - After script runs, re-applies variable substitution from original values
- **Prevents stale data** - Fixes issue where already-substituted values couldn't be re-resolved
- **Collection variables reload** - Always reloads collection variables after pre-request script execution
- **Request Details accuracy** - Request Details tab now shows ACTUAL values sent to server
- **Header support** - Headers added by scripts (e.g., `pm.request.headers.add()`) appear correctly

#### 🖱️ Body Tab Tooltip Persistence
- **150ms grace period** - Added delay before hiding tooltip when mouse leaves variable
- **Hover detection** - Tooltip stays visible when mouse is over it, allowing button interaction
- **Fixed in multi-line** - Applied to HighlightedTextEdit for Body tab editor
- **Smooth UX** - Users can now reliably click copy button without tooltip disappearing

### 🎨 UI/UX Improvements

#### 🎨 Modern Button Styling on Scripts Tab
- **Consistent design** - Updated Clear, Clear Console, and Hide buttons to match collections panel style
- **Hover effects** - Smooth hover transitions with blue border on hover
- **Dark theme optimized** - Background (#2D2D2D), borders (#3C3C3C), hover state (#007ACC)
- **Professional look** - 4px border radius, proper padding, 11px font size
- **Visual feedback** - Blue pressed state for better interaction feedback

### 🔧 Technical Improvements
- **VariableTooltipWidget** - Custom QWidget with QLabel, QPushButton, and QTimer for auto-hide
- **Clipboard integration** - QApplication.clipboard() for cross-platform copy functionality
- **URL-Params sync methods** - `_sync_url_to_params()` and `_sync_params_to_url()` with loop prevention
- **urllib.parse integration** - urlparse, parse_qs, urlencode, urlunparse for robust URL handling
- **Original value storage** - Stores pre-substitution values for accurate re-substitution
- **_syncing_params flag** - Prevents infinite loops in bidirectional synchronization
- **Variable inspector refresh** - Automatic `_refresh_variable_inspector_panel()` calls after script execution
- **Debug logging** - Enhanced logging for script execution and variable substitution flow

### 📚 Documentation
- **NEXT_VERSION_FEATURES.md** - Comprehensive tracking of all v1.9.4 features and fixes
- **Code comments** - Added detailed comments explaining re-substitution logic
- **Snippet descriptions** - Clear descriptions for all new collection variable snippets

---

## [1.9.3] - 2025-11-14

### 🎨 UI/UX Improvements

#### Typography & Font Optimization
- **Tab headers font weight** - Changed from bold to medium weight for better space efficiency and modern look
- **URL input optimization** - Reduced font size from 13px to 11px, allowing significantly more text visibility for long addresses
- **Collections list consistency** - Reduced font size from 13px to 12px to match tab header sizing
- **Input fields standardization** - All input fields now use consistent 11px font size
- **Tab spacing optimization** - Reduced horizontal padding from 12px to 8px for more efficient space usage
- **Request name visibility** - Fixed light theme text color from #CCCCCC to #424242 for better readability
- **Theme-aware colors** - Request, folder, and collection names now automatically adjust color based on theme

### 🐛 Bug Fixes
- **Light theme visibility** - Request names were too light/faded in light theme, now match folder visibility
- **Text truncation** - Improved text display before "..." truncation with optimized spacing

### 🔧 Technical Changes
- **ColoredTabBar** - Updated to use QFont.Weight.Medium instead of bold
- **RequestTreeItemDelegate** - Now respects theme colors for request name rendering
- **QSS stylesheets** - Font sizes optimized across QTreeWidget, QLineEdit, and input elements

---

## [1.9.2] - 2025-11-14

### ✨ New Features

#### 🔗 Nested Variable Resolution
- **Recursive variable substitution** - Variables can now reference other variables up to 10 levels deep
- **Cross-scope nesting** - Environment variables can reference collection variables and vice versa
- **Dynamic variable support** - Nested variables work seamlessly with dynamic variables like {{$guid}}
- **Tooltip enhancement** - Hover tooltips now show fully resolved values instead of raw nested references
- **Circular reference protection** - Automatic detection and prevention of infinite loops
- **Partial resolution** - Gracefully handles missing nested variables without breaking resolution
- **Postman-compatible syntax** - Uses official {{$variableName}} format for dynamic variables
- **Comprehensive test coverage** - 7 new nested variable tests, all passing

**Example Usage:**
```
Environment Variables:
  env = "staging"
  domain = "ecovadis-ilab.com"

Collection Variables:
  baseUrl = "{{env}}.{{domain}}"
  apiPath = "/api/v1"
  fullUrl = "{{baseUrl}}{{apiPath}}"

Result: "staging.ecovadis-ilab.com/api/v1"
```

**Supported Nesting Patterns:**
- ✅ Basic nesting: `{{var1}}` contains `{{var2}}`
- ✅ Multi-level: `{{a}}` → `{{b}}` → `{{c}}` (up to 10 levels)
- ✅ Cross-scope: `{{col.baseUrl}}` references `{{env.domain}}`
- ✅ Prefix syntax: `{{env.var}}`, `{{col.var}}`, `{{ext.var}}`
- ✅ Mixed with dynamic: `{{url}}/{{$guid}}`

**Technical Details:**
- Enhanced `VariableSubstitution.substitute()` with iterative resolution
- Updated `HighlightedLineEdit` and `HighlightedTextEdit` tooltip generation
- Regex pattern supports both dynamic (`{{$var}}`) and scoped (`{{env.var}}`) syntax
- Iteration-based tracking of unresolved variables per resolution pass

**Documentation:**
- All 51 dynamic variable tests passing
- 7 new nested variable tests in `tests/test_dynamic_variables.py`
- Updated tooltip implementation in `src/ui/widgets/variable_highlight_delegate.py`

### 🐛 Bug Fixes
- Fixed dynamic variable syntax in tests to use correct `{{$guid}}` format (not `{{$.guid}}`)
- Fixed tooltip display to show fully resolved nested values
- Fixed unresolved variable tracking across recursive iterations

### 🔧 Technical Improvements
- Improved variable resolution performance with max depth limit
- Enhanced tooltip generation with nested variable support
- Better error handling for empty dynamic variable results

---

## [1.9.1] - 2025-11-13

### ✨ New Features

#### 🎯 Drag & Drop Ordering for Collections, Folders, and Requests
- **User-controlled ordering** - Drag and drop to reorder collections, folders, and requests exactly how you want them
- **Persistent order** - Order is saved to database immediately and persists across restarts
- **Import/export preservation** - Order is preserved when exporting/importing collections (Postman-compatible)
- **Visual feedback** - Drop indicators show where items will be placed (above, below, or inside)
- **Automatic count updates** - Item counts refresh automatically after moves
- **Expanded state preservation** - Folders stay expanded during drag & drop operations
- **Comprehensive test coverage** - 17 passing tests covering all scenarios

**Validation Rules (Postman-Compatible):**
- ✅ Collections can be reordered at root level only (cannot be nested)
- ✅ Folders can be moved within their collection (cannot move between collections)
- ✅ Folders cannot be at root level (must be inside collections)
- ✅ Requests can be moved between collections and folders
- ✅ Circular reference prevention (folders cannot be dropped into themselves or descendants)
- ✅ Type-safe drops (folders cannot be dropped on requests, etc.)

**Technical Details:**
- Added `order_index` column to collections, folders, and requests tables
- Custom `ReorderableTreeWidget` class with comprehensive drop validation
- Transaction-safe database updates with rollback on error
- Circular reference detection for folder moves
- Smart tree reload only when items are moved (not just reordered)

**Documentation:**
- `docs/guides/DRAG_DROP_ORDERING.md` - Complete technical and user documentation
- `tests/test_drag_drop_ordering.py` - Comprehensive test suite (17 tests)

### 🐛 Bug Fixes
- Fixed database queries to use `order_index` for consistent sorting
- Fixed `get_folders_by_collection()` to include `order_index` in returned data
- Fixed `get_requests_by_folder()` to order by `order_index` instead of name
- Fixed test suite parameter order for `create_request()` calls
- Fixed import/export test data format expectations

### 🔧 Database Changes
- Added `order_index INTEGER` column to `collections` table (default: id * 100)
- Added `order_index INTEGER` column to `folders` table (default: id * 100)
- Added `order_index INTEGER` column to `requests` table (default: id * 100)
- New methods: `reorder_collections()`, `reorder_folders()`, `reorder_requests()`
- All queries now use `ORDER BY order_index` instead of `ORDER BY name` for consistent ordering

### 🎨 UI/UX Improvements
- Single-click drag and hold to initiate drag
- Drop indicators show valid drop positions
- Invalid drops are blocked with no visual artifacts
- Folders involved in moves stay expanded
- Current request's folder stays expanded during operations
- Perfect for organizing large API projects with complex folder structures

---

## [1.9.0] - 2025-11-13

### ✨ New Features

#### 🌍 Environment Import/Export with Postman Compatibility
- **Full Postman Environment Format support** - Import and export environments compatible with Postman
- **Import button** in Environments panel - Import from Postman or PostMini format
- **Export button** in Environments panel - Export to Postman or Internal format
- **Automatic format detection** - Seamlessly import from either format
- **Secret variable handling** - Choose to include actual values or replace with placeholders
- **Bulk operations** - Import/export multiple environments at once
- **Disabled variable support** - Postman's enabled/disabled variables preserved with `_DISABLED_` prefix
- **Secret detection** - Automatically marks variables as secrets based on keywords (key, token, password, etc.)
- **Duplicate name handling** - Smart conflict resolution when importing
- **Full validation** - Validates Postman environment structure on import
- **Format selection dialog** - Choose between Internal and Postman format when exporting
- **Comprehensive documentation** - New Environment Import/Export Guide

**Use Cases:**
- ✅ Migrate environments from Postman to PostMini
- ✅ Share environments with Postman users
- ✅ Create environment templates (with placeholders)
- ✅ Backup environments with or without secrets
- ✅ Team collaboration across different tools

**New Files:**
- `src/features/postman_environment_converter.py` - Postman format converter
- `src/features/environment_io.py` - Import/export infrastructure
- `tests/test_postman_environment_compatibility.py` - Comprehensive test suite (9 tests, all passing)
- `docs/guides/ENVIRONMENT_IMPORT_EXPORT_GUIDE.md` - Complete user guide

### 🔧 Technical Improvements
- **PostmanEnvironmentConverter** class with bidirectional conversion
- **EnvironmentExporter** class with format and secret options
- **EnvironmentImporter** class with auto-detection and validation
- Secret keyword detection: `secret`, `key`, `token`, `password`, `auth`, `api_key`, `credential`, `private`, `sensitive`
- Roundtrip conversion preserves all data integrity

### 🎨 UI/UX Improvements

#### Enhanced Light Theme Readability
- **Comprehensive light theme improvements** for better contrast and readability
- **QPushButton styling** - White backgrounds, dark text (#212121), strong borders (#BDBDBD)
- **Send Button** - Material Design blue (#1976D2) with white text for prominence
- **ComboBox/Dropdown styling** - Stronger borders, bold text, blue focus state (#1976D2)
- **Text Input fields** - Enhanced borders, blue focus state for better visibility
- **Tree Widget items** - Darker text (#424242) for improved readability
- **Tree selection** - Strong blue selection (#BBDEFB background, #0D47A1 text)
- **Environment selector** - Theme-aware styling in status bar
- All improvements apply **ONLY to light theme** - dark theme unchanged

#### Theme-Aware Panel Buttons
- **Environment Panel buttons** - Import, Export, Add, Variables, Edit, Delete all theme-aware
- **Collections Panel buttons** - Add and Import buttons with proper theme support
- **Variable Inspector button** - Add button with dropdown menu theme-aware
- **Central Panel buttons** - New Request, Recent, and Save buttons properly styled per theme
- **Icon bar buttons** - All 6 left sidebar icon buttons maintain correct styling on theme switch
- Dynamic style updates ensure buttons always match active theme

#### Theme Toggle Button
- **Theme toggle in status bar** - Quick access next to keyboard shortcuts hint
- **Sun/Moon icon** - Visual indicator of current theme (🌙 Dark / ☀️ Light)
- Button styled to match current theme with proper hover states

#### Panel Width Optimization
- **Left collapsible panels** - Default width increased to 400px (was 250px)
- Better utilization of screen space for Collections, Environments, Variables, Git Sync, and History panels
- More content visible without scrolling

#### Dynamic Table Row Management
- **Environment variables table** - No automatic alphabetic sorting
- **Collection variables table** - No automatic alphabetic sorting  
- Variables remain in the order they are added
- User has full control over variable ordering

### 🐛 Bug Fixes

#### Fixed Theme Initialization Bug
- **Root cause:** MainWindow received theme after __init__ completed
- **Symptom:** Dark theme startup showed light theme button styling until first theme switch
- **Solution:** Theme now passed to MainWindow constructor for proper initialization
- Buttons correctly styled on startup in both themes

#### Fixed Icon Bar Button Theme Switching
- **Issue:** Icon bar buttons broke when switching between themes
- **Solution:** Dynamic style update methods rewrite complete inline styles on theme change
- All 6 sidebar buttons (Collections, Environments, Variables, Git Sync, History, Recent) work correctly

### 🔧 Technical Changes
- Modified `src/ui/main_window.py` - Theme initialization, button style methods, theme-aware components
- Modified `src/ui/widgets/environments_panel.py` - Added `set_theme()` method and theme-aware button styling
- Modified `src/ui/widgets/variable_inspector_panel.py` - Added theme support for Add button
- Modified `main.py` - Pass theme to MainWindow constructor
- Modified `styles.qss` - Enhanced light theme styling for all UI elements
- Theme management pattern: `set_theme(theme)` methods with `_update_*_style()` helpers

---

## [1.8.6] - 2025-11-06

### ✨ New Features

#### Temporary Tabs (Preview Mode)
- **Single-click** opens requests in temporary tab (italic text, auto-closes when opening another)
- **Double-click** opens in permanent tab
- Temporary tab converts to permanent when editing, sending, or saving
- Similar to VS Code's file preview behavior
- More efficient tab management for browsing large collections

#### Keyboard Shortcuts for Panel Toggles
- **Alt+C** - Toggle Collections panel
- **Alt+E** - Toggle Environments panel
- **Alt+V** - Toggle Variables panel
- **Alt+G** - Toggle Git Sync panel
- **Alt+H** - Toggle History panel
- **Alt+R** - Toggle Recent Requests panel
- All tooltips updated to show shortcuts

#### History Panel as Overlay
- History converted from modal dialog to right-side overlay panel
- 800px wide with smooth animations
- Non-blocking workflow (doesn't interrupt current work)
- Mutual exclusion with Recent Requests panel
- Keyboard shortcut: Alt+H

#### Add Collection Variables from Variables Panel
- New "Add Collection Variable" option in Variables panel
- Dropdown menu on "+ Add" button
- Choose collection from list when adding variable
- Streamlined variable management workflow

### 🎨 UI/UX Improvements

#### Tab Header Width Optimization
- Reduced left padding from 12px to 8px
- Reduced min-width from 60px to 40px
- Max-width limited to 250px (was 300px)
- Tabs now fit text content with ~8px space from edge
- More tabs visible simultaneously
- Less wasted horizontal space

#### Modernized "Recent" Button
- Changed from emoji "🕐" to text-based "Recent"
- Matches style of "New request" button
- Fixed hover cutoff issue
- Better readability and accessibility
- Consistent 35px height with tab bar

#### Simplified Tooltips
- Removed redundant "Toggle" and "Panel" text
- Added keyboard shortcuts in brackets
- Examples:
  - "Collections [Alt+C]" (was "Toggle Collections Panel")
  - "Git Sync [Alt+G]" (was "Toggle Git Sync Panel")
  - "Request History [Alt+H]" (was "Requests History")
- Cleaner, more informative, faster to read

#### Removed Bullet Separator in Tabs
- Tab labels now: "GET New Request" (was "GET • New Request")
- Cleaner appearance with 8px space between method and name
- More space for request names
- Modern minimalist design

### 🐛 Bug Fixes

#### Fixed Recent Button Hover Cutoff
- Converted from fixed emoji button to flexible text-based button
- Proper sizing prevents rendering artifacts
- Perfect hover effects without cutoff

#### Improved Signal Blocking During Load
- Added signal blocking for test_tab and scripts_tab during request load
- Prevents false "modified" state when loading saved requests
- No more accidental unsaved changes prompts

#### History Panel Mutual Exclusion
- History and Recent Requests panels now properly hide each other
- Only one right-side overlay visible at a time
- Cleaner UI without overlapping panels

### 🔧 Technical Changes
- Modified `src/ui/main_window.py` - Added temporary tabs, keyboard shortcuts, updated tooltips and buttons (~500+ lines)
- Modified `src/ui/widgets/variable_inspector_panel.py` - Added collection variable support (~200 lines)
- Added `src/ui/widgets/history_panel_widget.py` - New history panel widget (437 lines)
- Modified `styles.qss` and `styles_dark.qss` - Updated tab dimensions (6 lines)
- Updated version to 1.8.6 in all files

---

## [1.8.2] - 2025-11-05

### 🎨 UI Improvements

#### Button Layout Refinements
- **Fixed Send/Save button spacing** for better visual separation
  - Restored 12px spacing between Send button and Save button group
  - Improved visual clarity and button group organization
- **Added border to Save button right edge**
  - Save button now has complete border on all sides
  - Better visual separation between Save and dropdown menu buttons
  - Enhanced button group definition

#### Technical Changes
- Modified `src/ui/main_window.py` - Updated button layout spacing and styling
  - Added explicit spacing after Send button
  - Removed `border-right: none` from Save button stylesheet
  - Improved button group visual consistency

---

## [1.8.1] - 2025-11-05

### 🐛 Bug Fixes

#### Scripts Tab Dark Theme Colors Fixed
- **Fixed script editor colors** to properly match dark theme
  - Background: Changed from light to dark (`#252526`)
  - Text color: Updated to match primary text (`#E0E0E0`)
  - Border: Updated to match dark theme borders (`#2D2D2D`)
  - Selection: Updated to match dark theme selection (`#3A79D0`)
- **Fixed console output styling** to match dark theme consistently
- **Added theme update on startup** to apply saved theme preference to script editors
- **Added theme update on toggle** to immediately update script editors when changing themes

#### Technical Changes
- Modified `src/ui/widgets/code_editor.py` - Updated `_apply_theme()` with correct colors
- Modified `src/ui/widgets/script_tab_widget.py` - Updated console styling
- Modified `src/ui/main_window.py` - Added script tab theme update call in `_toggle_theme()`
- Modified `main.py` - Added theme update after window initialization

### 🎨 Improvements
- **Perfect theme consistency** across all UI elements
- **Professional appearance** with proper color matching
- **Instant theme updates** when toggling between light and dark modes

---

## [1.9.0] - 2025-11-05 (Planned)

### ✨ JavaScript Scripting - Pre & Post Request Scripts (MAJOR FEATURE)

#### Pre-request Scripts
- **Execute JavaScript before sending requests**
  - Modify request URL, method, headers, body, and parameters dynamically
  - Set environment and collection variables programmatically
  - Generate dynamic authentication signatures (HMAC, OAuth, etc.)
  - Implement complex conditional logic
  - Calculate timestamps, UUIDs, and other dynamic values

#### Post-response Scripts
- **Execute JavaScript after receiving responses**
  - Extract data from JSON responses automatically
  - Save tokens, IDs, and other values to variables
  - Run custom test assertions with `pm.test()`
  - Chain requests by extracting and storing response data
  - Implement complex validation logic beyond built-in tests

#### Postman-Compatible API
- **Full `pm` object support** for seamless migration from Postman
  - `pm.environment.get/set()` - Environment variable management
  - `pm.collectionVariables.get/set()` - Collection variable management
  - `pm.globals.get/set()` - Global variable management
  - `pm.request.url`, `pm.request.headers`, `pm.request.method` - Request modification
  - `pm.response.code`, `pm.response.json()`, `pm.response.text()` - Response access
  - `pm.test()` - Write custom test assertions
  - `pm.expect()` - Chai-style assertions
  - `console.log/info/warn/error()` - Debugging output

#### Professional Script Editor
- **Syntax-highlighted JavaScript editor**
  - Line numbers for easy reference
  - Auto-indentation and smart formatting
  - Monospace font (JetBrains Mono/Consolas)
  - Dark and light theme support
  - Separate editors for pre-request and post-response scripts

#### Script Snippets Library
- **20+ pre-built script examples** for common tasks
  - Pre-request: Set Timestamp, Generate UUID, HMAC Signature, Basic Auth, etc.
  - Post-response: Extract Token, Parse JSON, Status Tests, Header Validation, etc.
  - Quick insertion via dropdown menu
  - Learn by example - all snippets are documented

#### Console Output Panel
- **Real-time script execution feedback**
  - Color-coded log levels (info/warning/error)
  - Execution time display
  - Collapsible panel for space efficiency
  - Clear console button
  - Shows script errors with line numbers

#### Secure Execution
- **Sandboxed JavaScript environment using V8 engine (PyMiniRacer)**
  - 5-second timeout protection
  - 50MB memory limit
  - Isolated execution context
  - No file system or network access (except via pm.sendRequest in future)

#### Database Integration
- **Scripts persist with requests**
  - Saved in SQLite database
  - Automatic migration for existing databases
  - Export/import support (scripts included in collections)

### 🛠️ Technical Implementation

#### New Files
- `src/features/script_engine.py` - JavaScript execution engine (~400 lines)
- `src/ui/widgets/code_editor.py` - Syntax-highlighted editor (~350 lines)
- `src/ui/widgets/script_tab_widget.py` - Scripts tab UI (~450 lines)
- `src/features/script_snippets.py` - Pre-built examples (~350 lines)
- `tests/test_scripting.py` - Comprehensive test suite (~350 lines)

#### Modified Files
- `src/core/database.py` - Added `pre_request_script` and `post_response_script` columns
- `src/ui/main_window.py` - Integrated Scripts tab and execution flow
- `requirements.txt` - Added `py-mini-racer>=0.8.0` dependency

### 📊 Use Cases Unlocked

#### Authentication Workflows
```javascript
// Pre-request: Generate OAuth signature
const timestamp = Date.now();
pm.environment.set("timestamp", timestamp);
const signature = generateHMAC(timestamp, secret);
pm.request.headers.add({key: "X-Signature", value: signature});
```

#### Request Chaining
```javascript
// Post-response: Extract token for next request
const token = pm.response.json().access_token;
pm.environment.set("authToken", token);
console.log("Token saved for next request");
```

#### Advanced Testing
```javascript
// Post-response: Custom validation
pm.test("Response time is acceptable", function() {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

pm.test("Has valid user data", function() {
    const data = pm.response.json();
    pm.expect(data.user).to.have.property("id");
    pm.expect(data.user.email).to.include("@");
});
```

### 🎯 Competitive Advantages
- ✅ **Postman script compatibility** - Copy-paste existing scripts
- ✅ **Full-featured scripting** - Pre & post request support
- ✅ **Modern UI** - Syntax highlighting and code editor
- ✅ **Script snippets** - Learn by example
- ✅ **Secure execution** - V8 sandbox with timeouts
- ✅ **Zero-config** - Works out of the box

### 📈 Impact
- **Power users can now migrate from Postman** with their existing scripts
- **Complex API workflows** now fully supported
- **Professional-grade testing** with custom assertions
- **Request chaining** for multi-step API interactions

---

## [1.8.0] - 2025-11-04

### 🎨 Major UI Reorganization

#### Top Toolbar Removed
- **Removed entire top toolbar** for a cleaner, more spacious interface
- Maximizes vertical space for API testing workflows
- Modern, streamlined look similar to VS Code

#### Bottom Status Bar Enhancements
- **Moved Environment Selector** from top toolbar to status bar
  - Compact inline selector with minimal visual footprint
  - Easy access without taking up valuable screen space
  - Styled with subtle background and hover effects
- **Moved Git Sync Status** from top toolbar to status bar
  - Shows "Git: Not Enabled" or "📁 Git: {workspace_name}"
  - Consolidated duplicate git status labels into single label
- **Moved Keyboard Shortcuts Hint** to status bar (right side)
  - Changed from "Press Ctrl+/ for shortcuts" to "💡 Ctrl+/ for shortcuts"
  - Positioned on right side for quick reference
- **Improved Status Bar Layout**
  - Removed excessive separators for cleaner appearance
  - Consistent 12px padding throughout
  - Better color scheme: Blue (#2196F3) for active items, Gray (#999) for passive
  - Fixed empty blocks caused by unused widgets
  - Left side: Ready | Git Status | Environment
  - Right side: Keyboard shortcuts hint

#### Left Sidebar Reorganization
- **Requests History** moved to left sidebar icon bar
  - 📋 icon positioned below Environments
  - Opens dialog on click (not a panel toggle)
  - Better organization of frequently-used features
- **Settings** moved to bottom of sidebar
  - ⚙️ icon now at the bottom (logical placement for configuration)
  - Separated from main workflow icons

#### New Request Button Enhancement
- Changed from just "+" to **"+ New request"** with clear text label
- Improved sizing and styling
- Better visual hierarchy
- More discoverable for new users

### 🐛 Bug Fixes

#### Tab Width Issue
- **Fixed narrow tab width** when creating new requests
  - Tabs now show proper width immediately on creation
  - Changed default tab size hint from Qt's narrow default to 150px
  - Added forced tab bar updates after setting tab data
  - Applied fix to all tab creation scenarios (new requests, opening from collections, tab updates)
  - No more mysteriously narrow tabs!

#### Status Bar Cleanup
- Removed duplicate `status_git_sync_label` (was creating empty blocks)
- Fixed spacer widget showing as visible block
- Consolidated Git workspace status into single label
- All status bar widgets now serve a purpose

### 🎯 User Experience Impact

- **More Screen Space**: Removing top toolbar gives ~40px more vertical space
- **Cleaner Interface**: Fewer UI elements on screen = less cognitive load
- **Better Organization**: Related features grouped logically
- **Improved Discoverability**: "New request" text makes button purpose clear
- **Professional Look**: Status bar similar to VS Code, Visual Studio, JetBrains IDEs
- **Consistent Behavior**: Tab widths work reliably in all scenarios

### 🔧 Technical Changes

- Removed `_create_toolbar()` method from `main_window.py`
- Removed theme toggle button (kept hidden for future use)
- Updated `_create_status_bar()` with comprehensive redesign
- Modified left sidebar icon layout in `_init_ui()`
- Enhanced `ColoredTabBar.tabSizeHint()` with better default sizing
- Added tab bar update calls after setting tab data (3 locations)
- Cleaned up duplicate widget references

### 📊 Before/After Comparison

**Before v1.8.0:**
- Top toolbar with 7+ widgets
- Narrow status bar with limited info
- History button in top toolbar
- Settings in middle of sidebar
- Just "+" for new request button
- Tabs sometimes showed narrow width

**After v1.8.0:**
- No top toolbar (40px more space)
- Comprehensive status bar with all key info
- History icon in logical sidebar position
- Settings at bottom of sidebar
- Clear "+ New request" button
- Tabs always show correct width

### 🎨 Design Philosophy

This release focuses on **vertical space optimization** and **information density**:
- Every pixel counts in an API testing tool
- Status bar is the perfect place for contextual information
- Top toolbar was redundant - all functions accessible elsewhere
- Professional tools (VS Code, IDEs) don't waste vertical space

---

## [1.7.1] - 2025-11-04

### 🔧 Code Quality & Maintenance

- **Removed duplicate class definition** in `VariableHighlightDelegate`
  - Fixed duplicate class causing code maintenance issues
  - Cleaned up `src/ui/widgets/variable_highlight_delegate.py`
  - Improved code organization and readability

- **Enhanced table cell editor styling**
  - Added `margin: 0px` to table cell editors
  - Improved visual consistency in Headers and Params tables
  - Better alignment in both dark and light themes

### ✅ Testing

- **All tests passing**: 50+ unit tests verified
- **Fixed test suite**: `test_delegate_removes_padding` now passes
- **No network dependencies**: All tests run offline successfully

### 📚 Documentation

- **New Guide**: `VARIABLE_HIGHLIGHTING_GUIDE.md`
  - Comprehensive guide to variable highlighting features
  - Usage examples for all variable types
  - Best practices and troubleshooting tips
  - Theme support and technical details
  - Quick reference card for all variable syntaxes

### 🎯 Impact

- **Cleaner Codebase**: Removed technical debt and duplicate code
- **Better Maintainability**: Easier for developers to understand and modify
- **Improved Stability**: All tests passing ensures reliability
- **Enhanced Documentation**: Users can better understand variable highlighting

---

## [1.7.0] - 2025-10-22

### ✨ Added - QA Features
- **Request Chaining & Variable Extraction**: Extract values from API responses and use in subsequent requests
  - "Extract Variables" tab in response section with interactive JSON tree
  - Click any value in response to extract as variable
  - Use `{{extracted.variableName}}` syntax in URL, headers, params, body
  - Variable Library dialog (📚 Variables button) to view/manage all extracted variables
  - Variables persist across sessions in database
  - Perfect for authentication workflows (extract token → use in next request)
  - Database schema: New `extracted_variables` table with metadata

- **Advanced Test Reporting**: Export test results in multiple formats
  - Export as HTML (styled, readable reports)
  - Export as JUnit XML (CI/CD integration)
  - Export as JSON (programmatic processing)
  - Export as CSV (spreadsheet analysis)
  - Export buttons in Collection Test Runner dialog
  - Reports include summary statistics and detailed results

### 🎨 UI Improvements
- **Extract Variables Widget Optimization**:
  - Compact 2×2 grid layout (was 4 rows × 1 column)
  - 50% space savings for better JSON tree visibility
  - Removed confusing "Quick Extract" dropdown
  - Labels: Variable Name, JSON Path, Value, Description
  - Cleaner, more efficient use of space

- **Params/Headers Tables UX**:
  - Delete key now works to remove rows (no more error!)
  - Right-click → "Delete Row" context menu
  - Rows clear on delete (maintains table structure)
  - Immediate visual feedback

- **Test Count Updates**: Test tab count updates immediately when adding/removing tests (was delayed until tab switch)

- **Dark Theme Fixes**: Extract Variables input fields now use theme colors (removed hardcoded light backgrounds)

### 🐛 Critical Bug Fixes
- **Variable Substitution Fix**: Fixed `{{extracted.variableName}}` not substituting
  - Root cause: Key mismatch between dict keys and substitution function expectations
  - Now correctly passes extracted variables as separate parameter
  - Works with and without active environment

- **Tab State Management**: Extract Variables widget now properly cleared/restored when switching tabs
  - Each tab's response data is isolated
  - No more stale data from previous tab
  - Proper empty state when switching to tab without response

- **Toast Notification Error**: Fixed `AttributeError: 'MainWindow' object has no attribute 'toast_manager'`
  - Corrected to use `self.toast` instead of `self.toast_manager`

- **Invalid JSON Popup**: Removed annoying popup for non-JSON responses
  - Now shows friendly inline message in Extract Variables tab
  - No workflow interruption

### 🔧 Technical Improvements
- Added extensive debug logging for variable substitution troubleshooting
- Improved error handling in variable extraction
- Better state persistence across tab switches
- Enhanced `_clear_response_viewer()` to handle all response UI components
- Enhanced `_restore_response()` to restore Extract Variables widget state

### 📚 Documentation
- Added `VARIABLE_EXTRACTION_GUIDE.md` - Complete user guide for variable extraction
- Added `QA_FEATURES_GUIDE.md` - Comprehensive guide for QA testing features
- Added `TESTING_VARIABLE_SUBSTITUTION.md` - Testing guide with multiple verification methods
- Added `EXTRACT_VARIABLES_UI_OPTIMIZATION.md` - UI optimization details
- Added `FIX_TAB_STATE_EXTRACT_VARIABLES.md` - Tab state management fix documentation
- Added `CRITICAL_FIX_VARIABLE_SUBSTITUTION.md` - Details of the substitution fix

### 🧪 Testing
- Created `setup_test_collection.py` script to quickly set up test data
- Added `QA_Features_Test_Collection.json` sample collection
- Comprehensive testing instructions in `TESTING_INSTRUCTIONS.md`

### 🎯 User Experience
- **For QA Engineers**: Complete toolkit for API testing and automation
- **Request Chaining**: Extract token from login → Use in authenticated requests
- **Test Reporting**: Share results with team or integrate with CI/CD
- **Improved UX**: Faster, cleaner, more intuitive interface
- **Better Feedback**: Inline messages instead of disruptive popups

---

## [1.6.0] - 2025-01-21

### ✨ Added
- **Hierarchical Request Folders**: Organize requests with unlimited nested folders
  - Create folders and subfolders within collections
  - Move requests between folders via context menu
  - Folder counts show total subfolders and requests: `Folder [2] [5]`
  - Dynamic folder icons (open/closed) with document papers in open state
  - Full context menu support (Add Folder, Add Request, Rename, Delete, Move)
  - Cascade deletion - removing folder deletes all contents
  - Database schema: New `folders` table with `parent_id` for nesting
  - `folder_id` column added to `requests` table
  
- **Collection Variables**: Manage variables at collection scope
  - Collection-scoped key-value pairs with descriptions
  - Variable resolution hierarchy: Collection > Environment > Dynamic
  - Dedicated "Manage Variables" dialog per collection
  - Database schema: New `collection_variables` table with UNIQUE constraint
  - Automatic variable substitution in requests
  - Collection variables override environment variables
  - UI integration with DatabaseManager CRUD operations
  
- **Visual Enhancements**:
  - Colored method badges in tree view (`[GET]` in teal, `[POST]` in orange, etc.)
  - Request names now in consistent gray color for clean appearance
  - Improved open folder icon showing document papers inside
  - Theme-aware icons for folders (light/dark variants)
  - Custom `RequestTreeItemDelegate` for colored method badges
  - → Arrow icon for active request (current tab)
  - • Dot icon for other open requests
  - • Dot after collection/folder names containing open requests

### 🔧 API Changes
- `DatabaseManager.create_request()` - Added `folder_id` parameter
- `DatabaseManager` - Added 12 new methods for folder/variable management
- `EnvironmentManager.substitute_in_request()` - Added `extra_variables` parameter

### 🐛 Bug Fixes
- Fixed dropdown icons to use flat SVG design without 3D borders
- Fixed folder icon persistence across theme switches
- Fixed request highlighting in nested folder structures
- Fixed variable resolution order to respect collection > environment hierarchy
- Fixed empty open folder icon to be distinguishable from closed state

### 🧪 Testing
- Added comprehensive test suite: `test_folders_and_collection_variables.py`
- 365/391 tests passing (93.4% pass rate)
- Tests cover folder CRUD, nesting, variables, and UI integration

### 📚 Documentation
- Added `V1.6.0_RELEASE_NOTES.md` with detailed feature guide
- Added `V1.6.0_IMPLEMENTATION_SUMMARY.md` for developers
- Updated README.md with folder and collection variable features

---

## [1.5.0] - 2025-10-21

### ✨ Added
- **Multi-Request Tab System**: Work on multiple API requests simultaneously
  - Open unlimited requests in separate tabs
  - Tab state persistence (request data, response, test results)
  - Smart duplicate prevention (can't open same request in multiple tabs)
  - Visual feedback (bold + underline for active, underline for open requests)
  - Close tabs with X button, middle-click, or Ctrl+W
  - Auto-open: First request opens automatically when no tabs exist
  - Tab titles show method and request name (e.g., "GET Users")
  - Unsaved changes marked with • dot in tab title
  - Double-click request to open in new tab
  - Right-click → "Open in New Tab" context menu option
  - Each tab remembers its complete state independently
  
- **Professional UI Polish**: Complete redesign matching Postman's quality
  - **Send Button Redesign**: Bold gradient, larger size, professional styling
  - **Method Badges**: Color-coded HTTP methods (GET=blue, POST=green, PUT=orange, DELETE=red, etc.)
  - **Status Code Badges**: Color-coded by category (2xx=green, 3xx=blue, 4xx=orange, 5xx=red)
  - **Enhanced Input Fields**: Better borders, padding, focus states
  - **Tab Styling Hierarchy**: Clear distinction between request tabs and inner tabs
  
- **Empty State Illustrations**: Professional guidance when no content
  - "No Request Selected" state (shown when no tabs open)
  - "No Response Yet" state (shown before sending request)
  - "No Collections" state (shown when collections tree empty)
  - All with helpful hints and professional icons
  
- **Enhanced Visual Hierarchy**:
  - Consistent spacing (4px, 8px, 12px, 16px, 24px grid)
  - Professional borders and shadows
  - Smooth 200ms transitions
  - Better margins and alignment throughout
  - Responsive sizing and layout

### 🎨 Improved
- **Collections Tree Behavior**:
  - Single-click collection: Expands/collapses (no highlighting)
  - Double-click collection: Also expands/collapses
  - Single-click request: Does nothing (prevents accidental changes)
  - Double-click request: Opens in new tab
  - No selection highlighting (cleaner look)
  - Active request: Bold + underlined
  - Open requests: Underlined only
  - Collections: Bold if contains active request, underlined if contains open requests
  
- **Tab State Persistence**:
  - Response data preserved per tab (status, headers, body, size, time)
  - Test results preserved per tab (assertions, summary)
  - State cleared when changing request within same tab
  - State restored when switching back to tab
  - Previous tab index tracking for correct state saving
  
- **Environment Dialog**:
  - Fixed header expanding vertically with window resize
  - Static header and footer heights
  - Only central splitter area expands
  - Better proportions and layout

### 🐛 Fixed
- **Critical Fixes**:
  - Removed Ctrl+T shortcut that created unsaveable empty tabs
  - Tab titles now update immediately after save/rename
  - Response updates correctly when swapping tabs
  - Test results remembered per tab (no longer lost on tab switch)
  - Collections tree highlighting refreshes on tab changes
  - Prevented opening same request in multiple tabs
  - Fixed collections tree not updating when opening first tab
  - Fixed rapid double-clicks opening duplicate tabs (added debouncing)
  - Fixed incorrect previous tab state being saved on tab switch
  - Removed initial empty tab (app starts with zero tabs)
  
- **UI/UX Fixes**:
  - Fixed tab close icon showing rectangle on hover (now native icon)
  - Tabs no longer disappear when clicking collections
  - New requests have empty URL instead of "https://api.example.com"
  - Fixed QSS parsing errors with rgba() values (replaced with hex)
  - Fixed inner tabs (Params, Headers) visual confusion with request tabs
  
- **Technical Fixes**:
  - Added signal blocking to prevent race conditions on tab creation
  - Correct tab index tracking with previous_tab_index attribute
  - Proper event filter for middle-click tab closing
  - Test results viewer existence checks before access
  - Manual _on_tab_changed call when signal doesn't fire for first tab

### 🧪 Testing
- Added 15 comprehensive tests for Multi-Request Tabs and Professional Polish
- Test classes: TestMultiRequestTabs, TestTabStatePersistence, TestDoubleClickDebouncing, TestCollectionsTreeHighlighting, TestMiddleClickTabClosing, TestEmptyStates, TestSignalBlocking
- Total test count: 362 tests (100% pass rate for new features)
- Coverage: All tab management, state persistence, UI interactions

### 📝 Documentation
- Created V1.5.0 Release Notes with comprehensive feature documentation
- Created TEST_COVERAGE_SUMMARY.md with full test breakdown
- Updated README.md with multi-request tabs usage (pending)
- Updated CHANGELOG.md with v1.5.0 information (this section)

### 🔧 Technical
- Created `src/ui/widgets/method_badge.py` (MethodBadge, StatusBadge classes)
- Created `src/ui/widgets/empty_state.py` (EmptyStateWidget and variants)
- Enhanced `src/ui/main_window.py` with extensive tab system (~2000 lines modified)
- Updated `styles.qss` and `styles_dark.qss` for professional polish
- Modified `src/ui/dialogs/environment_dialog.py` for static header height
- 100% backward compatible with v1.4.0

### 🎯 Impact
- **UX Parity**: PostMini now matches Postman's professional UI/UX quality
- **Productivity**: Multi-request tabs enable comparing/testing multiple endpoints simultaneously
- **State Preservation**: Never lose response or test results when switching between requests
- **Professional Feel**: Empty states and polish make app feel mature and enterprise-ready
- **Smart Management**: Duplicate prevention and debouncing prevent common user errors

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

