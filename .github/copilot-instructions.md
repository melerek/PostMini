# PostMini - AI Coding Agent Instructions

## Project Overview
PostMini is a desktop API client (Postman alternative) built with PyQt6. It's a single-window desktop application focused on **Postman compatibility**, **privacy (100% local storage)**, and **Git-based collaboration**.

## Architecture

### Three-Layer Structure
```
src/
├── core/           # Database, HTTP client, design system, app paths
├── features/       # Business logic modules (stateless utilities)
└── ui/             # PyQt6 UI (MainWindow + dialogs + widgets)
```

**Critical Pattern**: `MainWindow` (9400+ lines) is the orchestrator. It owns:
- `DatabaseManager` (SQLite CRUD for collections/requests/environments)
- `ApiClient` (requests library wrapper)
- `EnvironmentManager` (variable resolution with 4 scopes)
- All UI state and inter-widget coordination

**Why**: PyQt6's signal/slot architecture works best with centralized state. Features are stateless utilities called by MainWindow.

### Data Flow
```
User Action → MainWindow method → Feature module → DatabaseManager → SQLite
                                → ApiClient → HTTP request
                                ↓
                       Update UI widgets
```

### Key Components
- **DatabaseManager** (`src/core/database.py`): SQLite with `row_factory` for dict-like access. Handles collections, requests, environments, history, OAuth tokens, test results.
- **ScriptEngine** (`src/features/script_engine.py`): PyMiniRacer (V8) for executing Postman-compatible JavaScript pre/post scripts. Implements `pm` API.
- **EnvironmentManager** (`src/features/variable_substitution.py`): Resolves variables in 4 scopes with priority: `{{ext.*}}` > `{{col.*}}` > `{{env.*}}` > `{{$dynamic}}`. Handles nested substitution (max depth: 10).
- **AppPaths** (`src/core/app_paths.py`): Stores data in `%APPDATA%\PostMini` on Windows. SQLite DB + secrets live there.

## Postman Compatibility

**Critical Design Goal**: PostMini must import/export Postman Collection Format v2.1 and Postman Environment Format.

### Import/Export Patterns
- **Collections**: `PostmanConverter` converts between internal format and Postman v2.1 schema
- **Environments**: `PostmanEnvironmentConverter` handles Postman env format with secret/non-secret value distinction
- **Variable Syntax**: Support both prefixed `{{env.var}}` and legacy `{{var}}` (checks all scopes for backward compat)

### Drag & Drop Ordering
**Postman-style validation** (see `ReorderableTreeWidget.dropMimeData`):
- Collections are TOP-LEVEL ONLY (cannot nest)
- Folders can be in collections or other folders (not on requests)
- Requests can be in folders or collections (not on other requests)
- Order persists via `display_order` column in SQLite

## Variable System

**Four Scopes** (priority order):
1. **Extracted**: `{{ext.token}}` - Values extracted from responses via JSONPath/Regex
2. **Collection**: `{{col.baseUrl}}` - Collection-level variables
3. **Environment**: `{{env.apiKey}}` - Environment-level variables
4. **Dynamic**: `{{$timestamp}}`, `{{$guid}}` - Auto-generated values (moment of substitution)

**Nested Variables**: Variables can reference other variables. Example:
```
env.protocol = "https"
env.domain = "api.example.com"
env.baseUrl = "{{protocol}}://{{domain}}"  # Resolves to "https://api.example.com"
```

**Substitution**: Call `VariableSubstitution.substitute()` for strings or `substitute_dict()` for nested dicts. Always returns `(result, unresolved_list)`.

## Development Workflow

### Running the App
```powershell
python main.py  # Run from project root
```

### Running Tests
```powershell
pytest tests/                      # All tests (374+ tests)
pytest tests/test_app.py           # Core functionality
pytest tests/test_drag_drop_ordering.py  # Drag & drop
pytest -v                          # Verbose output
```

**Test Structure**: Tests use `pytest-qt` for PyQt6 testing. Most tests create a `MainWindow` instance and use `qtbot` fixture for interactions.

### Building Installer
```powershell
pyinstaller build_installer.spec --clean  # Creates dist/PostMini.exe
```

**PyInstaller Config**: `build_installer.spec` includes:
- Custom fonts (Inter for UI, JetBrains Mono for code)
- PyMiniRacer's `mini_racer.dll` (required for JavaScript execution)
- QSS stylesheets (light + dark themes)
- 40+ module exclusions to reduce build time and size

## PyQt6 Patterns

### Widget Lifecycle
```python
# MainWindow creates and stores widget references
self.collections_tree = ReorderableTreeWidget()  # Custom drag & drop tree
self.method_combo = QComboBox()
self.url_input = HighlightedLineEdit()  # Shows variables with syntax highlighting

# Load data into widgets
self.load_collections()  # Queries DB → populates tree
self.load_request(request_id)  # Loads request data into editor widgets
```

### Signal/Slot Pattern
```python
# Connect signals in MainWindow.__init__
self.send_button.clicked.connect(self.send_request)
self.collections_tree.itemClicked.connect(self.on_collection_item_clicked)

# Handlers update UI and call feature modules
def send_request(self):
    # 1. Get values from UI widgets
    # 2. Call ScriptEngine.execute_pre_request_script (if pre-script exists)
    # 3. Call ApiClient.execute_request
    # 4. Call ScriptEngine.execute_post_response_script (if post-script exists)
    # 5. Update response viewer widgets
```

### Custom Delegates for Syntax Highlighting
`VariableHighlightDelegate` highlights variables in table cells (params, headers). Applied via:
```python
table.setItemDelegateForColumn(column, VariableHighlightDelegate(table))
```

## Styling & Theming

**QSS Stylesheets**:
- `styles.qss` - Light theme
- `styles_dark.qss` - Dark theme

**Design System** (`src/core/design_system.py`): Centralized colors, spacing, typography. Use `DesignSystem` constants for consistency.

**Theme Toggle**: `MainWindow.toggle_theme()` swaps stylesheet and updates all code editors (QTextEdit backgrounds).

## Common Patterns

### Database Operations
```python
# Always use with connection management
db = DatabaseManager("api_client.db")  # Auto-creates tables
col_id = db.create_collection("My API")
req_id = db.create_request(col_id, "Get Users", "GET", "https://api.example.com/users", ...)
db.close()  # Or use context manager
```

### Variable Substitution in Requests
```python
# Before sending request
url_resolved, unresolved = self.env_manager.substitute_in_request(
    url, params, headers, body, auth_token
)
if unresolved:
    # Show warning to user about unresolved variables
```

### JavaScript Execution
```python
script_engine = ScriptEngine(timeout_ms=5000)
try:
    result = script_engine.execute_pre_request_script(
        script, url, method, headers, body, params,
        env_variables, collection_variables, extracted_variables
    )
    # result contains modified request data and console logs
except (ScriptExecutionError, ScriptTimeoutError) as e:
    # Show error to user
```

## Git Collaboration

**Git Sync** (`src/features/git_sync_manager.py`): Teams store collections in Git repos, not cloud.
- Export collections to `.json` files in Git repo
- Push/pull to sync with team
- Secrets are **never committed** (handled by `SecretsManager` with local `.secrets` file)

**SecretsManager**: Separates secret values (API keys, tokens) from environment variables. Secret values stored locally in `%APPDATA%\PostMini\.secrets` (Git-ignored).

## Key Files to Reference

### For Architecture Understanding
- `src/ui/main_window.py` - Central orchestrator (9400+ lines)
- `src/core/database.py` - Database schema and CRUD
- `docs/PROJECT_STRUCTURE.md` - Full directory structure

### For Features
- `src/features/variable_substitution.py` - Variable resolution
- `src/features/script_engine.py` - JavaScript execution
- `src/features/postman_converter.py` - Postman format conversion
- `src/features/collection_io.py` - Import/export logic

### For Testing
- `tests/test_app.py` - Core functionality examples
- `tests/test_drag_drop_ordering.py` - Drag & drop validation rules
- `tests/test_postman_compatibility.py` - Postman format tests

## Common Gotchas

1. **PyQt6 ItemDataRole**: Use `Qt.ItemDataRole.UserRole` (not `Qt.UserRole`) for storing data in tree items
2. **Variable Syntax**: Always support BOTH prefixed (`{{env.var}}`) and legacy (`{{var}}`) syntax
3. **Database JSON Columns**: Use `json.dumps()` for params/headers before storing, `json.loads()` when retrieving
4. **PyMiniRacer DLL**: Must be included in PyInstaller build for JavaScript execution
5. **Theme Changes**: After toggling theme, manually update QTextEdit backgrounds (QSS doesn't reach them)
6. **Drag & Drop**: Validate drop operations in `dropMimeData()` BEFORE allowing them (prevent invalid structures)

## Bug Prevention & Learning

**CRITICAL**: When you discover a bug in generated code, update this section to prevent repetition.

### Known Bug Patterns to Avoid

**Pattern**: [Bug category - e.g., "PyQt6 API Misuse"]
- **Issue**: [Specific problem that occurred]
- **Correct Pattern**: [How to do it correctly]
- **Example**: [Code snippet showing correct implementation]
- **When to Apply**: [Context where this pattern applies]

### Bug Documentation Process

When fixing a bug in AI-generated code:
1. **Identify Root Cause**: Understand WHY the bug occurred (wrong assumption, outdated API, missing validation, etc.)
2. **Update Instructions**: Add the bug pattern to this section with clear correct implementation
3. **Verify Similar Code**: Search codebase for similar patterns that might have the same bug
4. **Update Tests**: Ensure test coverage exists for this bug scenario
5. **Document Context**: Note when this pattern applies (specific files, features, or components)

### Example Bug Pattern Entry

**Pattern**: Database NULL Handling
- **Issue**: Calling `dict()` on None when database returns no results causes TypeError
- **Correct Pattern**: Always check for None before accessing dict methods: `if result is None: return None`
- **Example**: 
  ```python
  # Wrong
  request = db.get_request(req_id)
  params = request['params']  # Crashes if request is None
  
  # Correct
  request = db.get_request(req_id)
  if request is None:
      return None
  params = request.get('params', {})
  ```
- **When to Apply**: All database retrieval operations in `DatabaseManager` and callers in `MainWindow`

**Pattern**: QTreeWidget Item Data Type Safety
- **Issue**: Not checking if `data()` returns None before calling dict methods causes crashes in tree operations
- **Correct Pattern**: Always validate item data exists and has expected type before accessing
- **Example**:
  ```python
  # Wrong
  item_data = item.data(0, Qt.ItemDataRole.UserRole)
  item_type = item_data['type']  # Crashes if item_data is None
  
  # Correct
  item_data = item.data(0, Qt.ItemDataRole.UserRole)
  if not item_data or not isinstance(item_data, dict):
      return
  item_type = item_data.get('type')
  ```
- **When to Apply**: All `QTreeWidget` and `QTreeWidgetItem` operations, especially in drag & drop and context menus

## Code Style

- **Imports**: Group by standard lib, third-party, local (separated by blank lines)
- **Docstrings**: Google style for classes/functions
- **Type Hints**: Use for function signatures, especially in feature modules
- **Error Handling**: Catch specific exceptions, show user-friendly messages via QMessageBox
- **Comments**: Explain "why" not "what" (code should be self-documenting)
- **Documentation Files**: **DO NOT create markdown files** to document each change or summarize work unless explicitly requested by the user. This wastes time and cost without adding value. Make changes directly in code and respond concisely.

## Styling & Theme Management

**CRITICAL**: PostMini supports BOTH light and dark themes. **ALL UI/styling changes MUST be applied to BOTH themes.**

### Theme Files
- **Dark Theme**: `styles_dark.qss` (default theme)
- **Light Theme**: `styles.qss` (alternative theme)
- **Theme Toggle**: User can switch via Settings panel

### Dual-Theme Update Checklist
When making ANY UI/styling changes:
1. ✅ **Apply to `styles_dark.qss` first** (primary development theme)
2. ✅ **Apply identical changes to `styles.qss`** (must match exactly)
3. ✅ **For Python inline styles**: Ensure styles work on both light/dark backgrounds
4. ✅ **Test color values**: Dark theme uses light colors (#E0E0E0), light theme uses dark colors (#212121)
5. ✅ **Verify font sizes match**: Both themes must have identical font-size values

### Common Styling Patterns That Need Dual-Theme Support
- QComboBox font-size and dropdown styling
- QTabWidget tab font-size and padding  
- QTableWidget item font-size
- QPushButton font-size and height
- QLabel font-size for metadata/tertiary text
- Any QSS rule with `font-size`, `padding`, `min-height`, `max-height`

### Example: Applying a Font Size Change
```css
/* In styles_dark.qss */
QTabWidget#innerTabs QTabBar::tab {
    font-size: 12px;
    padding: 6px 12px;
}

/* MUST ALSO add to styles.qss with IDENTICAL values */
QTabWidget#innerTabs QTabBar::tab {
    font-size: 12px;
    padding: 6px 12px;
}
```

### Inline Python Styles (Theme-Agnostic)
When setting inline styles in Python code, ensure they work for both themes:
```python
# Good - uses relative font-size, works on both themes
button.setStyleSheet("font-size: 11px; padding: 4px 8px;")

# Bad - uses theme-specific colors in Python (should be in QSS)
button.setStyleSheet("font-size: 11px; color: #E0E0E0;")  # Won't work in light theme
```

### Critical Reminder
**NEVER apply styling changes to only one theme.** This creates visual inconsistencies and breaks the user experience when switching themes. Always check both `styles.qss` and `styles_dark.qss` when making UI changes.

## Project Structure & File Organization

**Critical**: Maintain clean project structure. Files MUST be in proper locations.

### Root Directory - Keep Minimal
**Only these files belong in root:**
- `main.py` - Application entry point
- `version.json` - Version configuration
- `README.md` - Main documentation
- `CHANGELOG.md` - Version history
- `LICENSE.txt` - MIT license
- `requirements.txt`, `requirements-dev.txt` - Dependencies
- `build_installer.spec`, `installer.iss` - Build configuration
- `styles.qss`, `styles_dark.qss` - Stylesheets
- `postmini_logo.png`, `postmini_logo.ico` - App icons
- `.gitignore` - Git configuration
- `NEW_VERSION_INSTRUCTIONS.md` - Release procedure (critical reference)

### Proper File Locations
- **Documentation** → `docs/` (implementation notes, guides, comparisons)
- **Release notes** → `docs/release_notes/` (version-specific documentation)
- **Archived docs** → `docs/archive/` (completed implementation docs, old bug reports)
- **Test collections** → `examples/` (sample JSON files for testing)
- **Test scripts** → `tests/` (all test_*.py files)
- **Test databases** → `tests/` (test_*.db files)
- **GitHub workflows** → `.github/workflows/` (CI/CD)
- **Source code** → `src/` (never in root)

### Files That Should NOT Be in Root
❌ Implementation documentation (e.g., `DRAG_DROP_IMPLEMENTATION_COMPLETE.md`)
❌ Bug fix summaries (e.g., `BUGFIX_*.md`, `BUG_FIXES_SUMMARY.md`)
❌ Feature summaries (e.g., `COMPLETE_FEATURE_SUMMARY.md`)
❌ Release guides for old versions (e.g., `RELEASE_v1.9.1_*.md`)
❌ Cleanup summaries (e.g., `CLEANUP_COMPLETE.md`, `CLEANUP_SUMMARY.md`)
❌ GitHub release texts (e.g., `GITHUB_RELEASE_*.md`, `GITHUB_RELEASE_*.txt`)
❌ Test artifacts (e.g., `test_*.json`, `test_*.db` - these are generated dynamically by tests)
❌ Planning documents (e.g., `PROJECT_CLEANUP_PLAN.md`, `POSTMAN_API_COVERAGE_ANALYSIS.md`)
❌ Phase completion docs (e.g., `PHASE1_IMPLEMENTATION_COMPLETE.md`)

**Note**: Test artifacts like `test_export.json`, `test_*.db` are created/cleaned up automatically by test suites. They should not be committed to git or moved to examples/.

### When Creating New Files
1. **Think first**: Does this file need to exist long-term?
2. **Choose location**: Use proper directory based on file purpose
3. **Never pollute root**: Only critical operational files in root
4. **Archive when done**: Move completed implementation docs to `docs/archive/`

### Cleanup Command Pattern
When asked to "clean up project structure":
1. **Identify misplaced files** in root directory
2. **CRITICAL - Check if files are test artifacts first**:
   - Run `grep -r "filename" tests/` to see if file is referenced in tests
   - If file is created dynamically by tests (e.g., `test_export.json` in `test_import_export.py`), **DELETE IT** - don't move it
   - Only move files that are source/template files, not generated artifacts
3. **Move to proper locations**:
   - Implementation docs → `docs/archive/`
   - Release notes → `docs/release_notes/`
   - User-facing test collections → `examples/` (e.g., `QA_Features_Test_Collection.json`)
   - Debug/test scripts → `tests/` (e.g., `test_save_crash.py`)
4. **Delete test artifacts**: `test_*.json`, `test_*.db` files are generated by tests and shouldn't be committed
5. **Verify no breakage**: After moving files, check if any code references the old paths
6. **Report**: List what was moved/deleted and why

### ⚠️ Common Mistake: Moving Test Artifacts
**NEVER move files that are created by test code**. Example:
- `test_export.json` is created by `test_import_export.py` during test execution
- It's cleaned up automatically by the test's `cleanup_test_files()` function
- Moving it breaks nothing because it's regenerated each time
- **Solution**: Delete these artifacts, don't move them

**How to identify test artifacts:**
1. Check if filename appears in test cleanup functions (`cleanup_test_files()`)
2. Check if file is opened with write mode (`'w'`) in tests
3. Check `.gitignore` - test artifacts should already be ignored
4. If uncertain, search codebase: `grep -r "filename" .`

## Documentation

**Full docs** at `docs/index.html` (open in browser). Key guides:
- `docs/guides/ENVIRONMENT_IMPORT_EXPORT_GUIDE.md` - Environment format details
- `docs/guides/DRAG_DROP_ORDERING.md` - Drag & drop implementation
- `docs/POSTMINI_VS_POSTMAN_COMPARISON.md` - **Feature parity tracking - MUST update with each release**

### Maintaining Feature Comparison
**Critical**: `docs/POSTMINI_VS_POSTMAN_COMPARISON.md` must be updated with EVERY release:
- Update version and date at the top (line 3-4)
- Add new features to appropriate comparison sections
- Update "Winner" annotations if feature changes competitive position
- Update Summary Scorecard at bottom
- This document is important for marketing and shows PostMini's competitive advantages

## Version Info

Current version tracked in `version.json`. Update for releases.

## Release Preparation & New Version Workflow

**CRITICAL**: When asked to prepare a new version for release, follow `NEW_VERSION_INSTRUCTIONS.md` step-by-step.

### Version Files - ALL Must Match! (6 Files)
1. `version.json` - `latest_version` field
2. `main.py` - `app.setApplicationVersion("X.Y.Z")`
3. `installer.iss` - `#define MyAppVersion "X.Y.Z"`
4. `src/features/auto_updater.py` - `CURRENT_VERSION = "X.Y.Z"` ⚠️ **OFTEN MISSED**
5. `src/ui/widgets/settings_panel.py` - `APP_VERSION = "X.Y.Z"` ⚠️ **OFTEN MISSED**
6. `README.md` - Version badge

### Release Build Process
```powershell
# Clean previous builds
Remove-Item -Path "build","dist" -Recurse -Force -ErrorAction SilentlyContinue

# Build executable
python -m PyInstaller build_installer.spec --clean --noconfirm

# Calculate executable checksum
Get-FileHash -Path "dist\PostMini\PostMini.exe" -Algorithm SHA256

# Build installer (requires Inno Setup)
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# Calculate installer checksum
Get-FileHash -Path "dist\installer\PostMini_Setup_v1.9.2.exe" -Algorithm SHA256
```

### Critical Release Steps
1. **Update CHANGELOG.md** - Move items from `[Unreleased]` to new version section
2. **Update all 6 version files** - Verify they all match
3. **Update comparison document** - Update `docs/POSTMINI_VS_POSTMAN_COMPARISON.md` with new features (version + date at top)
4. **Build & calculate checksums** - Update `version.json` with SHA256 values
5. **Git commit & tag** - Include checksums in commit message
6. **Push to GitHub** - Both commits and tags
7. **Create GitHub release** - Upload installer from `dist\installer\`
8. **Verify download** - Test installer checksum matches
9. **Initialize next version log** - Create/update `NEXT_VERSION_FEATURES.md` to track changes for the next release

### Release Notes Management
After completing a release, **ALWAYS maintain** `NEXT_VERSION_FEATURES.md`:
- Create the file if it doesn't exist after a release
- Track all key features, bug fixes, and improvements as they're implemented
- Use this as the source for the next version's release notes
- Structure: Group by categories (✨ Features, 🐛 Bug Fixes, 🔧 Technical, 📚 Docs)
- When next release is prepared, move content to CHANGELOG.md and clear the file

**Example NEXT_VERSION_FEATURES.md structure:**
```markdown
# Features for Next Release

## ✨ New Features
- [Feature description]

## 🐛 Bug Fixes
- [Bug fix description]

## 🔧 Technical Improvements
- [Technical change]

## 📚 Documentation
- [Doc updates]
```

### Common Release Mistakes
- ❌ Forgetting `auto_updater.py` or `settings_panel.py` → Auto-update malfunction
- ❌ Not updating `version.json` checksums after rebuild → Install failures
- ❌ Version number typos → Inconsistent display, broken updates
- ❌ Not testing fresh download → Release works locally but fails from GitHub

**Reference**: See `NEW_VERSION_INSTRUCTIONS.md` for complete 33-step checklist with verification commands.
