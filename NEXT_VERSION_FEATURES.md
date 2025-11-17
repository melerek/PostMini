# Features for Next Release

## ✨ New Features
- **Variable Tooltip Copy** - Added "Copy to Clipboard" button in variable tooltips for quick value copying (Postman-style)
  - Works in URL input, parameters, headers, body, and all other variable fields
  - Shows variable name, resolved value, and copy button in custom tooltip widget
  - Visual feedback on copy with green checkmark confirmation
  - Auto-hides after 500ms when mouse leaves tooltip

- **Live URL ↔ Params Synchronization** - Replicated Postman's query parameter sync behavior
  - URL query parameters automatically populate in Params tab in real-time
  - Typing in URL box updates Params table instantly (both keys and values)
  - Editing Params table updates URL query string live
  - Removing params from URL removes them from table, and vice versa
  - Bidirectional sync prevents manual concatenation errors

- **Auto-refresh Variable Inspector** - Variable inspector panel now updates automatically after scripts run
  - Refreshes when pre-request scripts modify variables (e.g., `pm.collectionVariables.set()`)
  - Refreshes when post-response scripts modify variables
  - Only refreshes if the panel is open (no performance impact when closed)
  - Shows updated variable values immediately without needing to close/reopen the panel

## 🐛 Bug Fixes
- **Body Tab Tooltip Fix** - Fixed tooltip disappearing before reaching copy button in Body tab
  - Added 150ms delay before hiding tooltip when mouse leaves variable
  - Tooltip now stays visible when hovering over it, allowing button interaction
  - Applied to HighlightedTextEdit (Body tab multi-line editor)

- **Pre-request Script Variable Timing** - Fixed pre-request scripts executing after variable substitution
  - Collection variables set by pre-request scripts (e.g., `pm.collectionVariables.set()`) are now properly used in the request
  - **Always** reloads collection variables after pre-request script execution (not conditionally)
  - **CRITICAL FIX**: Re-substitutes from ORIGINAL unsubstituted values, not from already-substituted strings
  - This prevents the issue where variables were already replaced with old values before re-substitution
  - Stores original URL, params, headers, body, and auth token before first substitution
  - Re-applies variable substitution after pre-request script using the original values with updated variables
  - Fixes issue where request used old variable values instead of script-updated values
  - Headers added by scripts (e.g., `pm.request.headers.add()`) now correctly appear in sent request
  - Request Details tab now shows the ACTUAL values sent to server (after script execution and re-substitution)
  - Debug logs now show "Re-applying substitution from ORIGINAL values" to confirm correct behavior

## 🔧 Technical Improvements
- Created `VariableTooltipWidget` custom widget with copy button functionality
- Replaced standard QToolTip with interactive custom tooltip in HighlightedLineEdit, HighlightedTextEdit, and VariableHighlightDelegate
- Added clipboard integration using QApplication.clipboard()
- Implemented `_sync_url_to_params()` method to parse URL query string and update params table
- Implemented `_sync_params_to_url()` method to rebuild URL with updated query parameters
- Added `_syncing_params` flag to prevent infinite loop between URL and params updates
- Integrated `urllib.parse` for robust URL parsing and query string manipulation
- Added collection variable reload and re-substitution after pre-request script execution
- Debug logging for pre/post-script variable states to aid troubleshooting
- Modern button styling applied to Scripts tab (Clear, Clear Console, Hide buttons)
- Added code snippets for setting and getting collection variables in both pre-request and post-response scripts

## 📚 Documentation
- (Track documentation updates here as they're implemented)
