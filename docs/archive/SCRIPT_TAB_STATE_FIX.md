# Script Tab State Management Fix

## Problem
Scripts and console output were not properly managed when switching between request tabs:
1. Scripts were not captured when switching away from a tab
2. Scripts were not restored when switching back to a tab
3. Console output persisted across all tabs instead of being cleared
4. Script changes were not tracked for unsaved changes detection

## Solution

### 1. **Script State Capture** (`_capture_current_tab_state`)
**Location**: `src/ui/main_window.py` lines 1156-1163

Added script content capture to tab state:
```python
# Capture script content (pre-request and post-response scripts)
scripts_data = None
if hasattr(self, 'scripts_tab') and self.scripts_tab is not None:
    scripts_data = {
        'pre_request_script': self.scripts_tab.get_pre_request_script(),
        'post_response_script': self.scripts_tab.get_post_response_script()
    }
```

This ensures that any unsaved script changes are preserved when switching tabs.

### 2. **Script State Restoration** (`_restore_tab_state`)
**Location**: `src/ui/main_window.py` lines 1229-1248

Added script restoration logic with two sources:
1. **From tab state** (if scripts were modified and not saved)
2. **From database** (if no unsaved changes)

```python
# Load scripts from saved state (if available)
scripts_data = state.get('scripts')
if scripts_data:
    print(f"[DEBUG] Restoring scripts from tab state")
    self.scripts_tab.load_scripts(
        scripts_data.get('pre_request_script', ''),
        scripts_data.get('post_response_script', '')
    )
elif self.current_request_id:
    # No saved script state, load from database
    print(f"[DEBUG] Loading scripts from database for request_id={self.current_request_id}")
    request = self.db.get_request(self.current_request_id)
    if request:
        self.scripts_tab.load_scripts(
            request.get('pre_request_script', '') or '',
            request.get('post_response_script', '') or ''
        )

# Always clear console when switching tabs
self.scripts_tab._clear_console()
```

### 3. **Console Clearing on Tab Switch**
**Location**: `src/ui/main_window.py` line 1248

Always clear console output when switching tabs to prevent console logs from one request appearing in another:
```python
# Always clear console when switching tabs
self.scripts_tab._clear_console()
```

### 4. **Console Clearing on Request Load**
**Location**: `src/ui/main_window.py` lines 3515-3517

Clear console when loading a request from the database:
```python
self.scripts_tab.load_scripts(pre_request_script, post_response_script)
# Always clear console when loading a request
self.scripts_tab._clear_console()
```

### 5. **Script Change Tracking**
**Location**: `src/ui/main_window.py` lines 3645-3646

Added scripts to the original request data tracking for change detection:
```python
def _store_original_request_data(self):
    self.original_request_data = {
        # ... other fields ...
        'pre_request_script': self.scripts_tab.get_pre_request_script(),
        'post_response_script': self.scripts_tab.get_post_response_script()
    }
```

This ensures that script modifications trigger the "unsaved changes" indicator.

## Behavior After Fix

### Tab Switching Flow

1. **When leaving Tab A:**
   - Current scripts (pre-request & post-response) are captured
   - Script content saved to `tab_states[index]['ui_state']['scripts']`
   - Console output is NOT captured (intentionally)

2. **When entering Tab B:**
   - Scripts are restored from saved tab state (if exists) OR from database
   - Console is ALWAYS cleared
   - Fresh, clean console for each tab

3. **Unsaved Changes:**
   - Script modifications mark the request as having unsaved changes
   - Tab title shows asterisk (*) indicator
   - Scripts are preserved in tab state even when not saved to database

## Testing Scenarios

### Scenario 1: Script Editing Across Tabs
1. Open Request A, add pre-request script
2. Switch to Request B, add post-response script
3. Switch back to Request A
   - **Expected**: Pre-request script from step 1 is still there
   - **Expected**: Console is cleared

### Scenario 2: Console Output Isolation
1. Open Request A, run request with console.log()
2. Console shows output
3. Switch to Request B
   - **Expected**: Console is cleared
4. Run Request B with different console.log()
   - **Expected**: Only Request B's output shown

### Scenario 3: Unsaved Script Changes
1. Open saved Request A
2. Modify pre-request script
3. Tab title shows "*" indicator
4. Switch to Request B, then back to Request A
   - **Expected**: Script changes preserved
   - **Expected**: "*" indicator still present

## Files Modified

1. `src/ui/main_window.py`:
   - `_capture_current_tab_state()` - Added script capture
   - `_restore_tab_state()` - Added script restoration
   - `_load_request_data()` - Added console clearing
   - `_store_original_request_data()` - Added script tracking

## Related Components

- `src/ui/widgets/script_tab_widget.py`:
  - Already has `scripts_changed` signal that's connected to change detection
  - Already has `_clear_console()` method used for clearing
  - Already has `load_scripts()` method for loading scripts

## Benefits

1. **Data Integrity**: Scripts are never lost when switching tabs
2. **Clean UI**: Console output doesn't bleed between requests
3. **Change Detection**: Script modifications are properly tracked
4. **User Experience**: Natural behavior matching user expectations
5. **Consistency**: Same pattern as other tab state management

## No Breaking Changes

This fix is backward compatible:
- Existing requests load normally from database
- Tab switching continues to work as before
- Only adds script preservation functionality

