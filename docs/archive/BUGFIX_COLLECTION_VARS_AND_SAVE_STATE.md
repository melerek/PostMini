# Bug Fixes - November 13, 2025

## Issues Fixed

### 1. Collection Variable KeyError ❌ → ✅

**Problem:**
```
KeyError: 'name' when adding collection variable
```

**Root Cause:**
- Code was checking `var['name']` in collection variables
- Database method `get_collection_variables_with_metadata()` returns `'key'` not `'name'`
- Mismatch between expected and actual dictionary keys

**Location:** `src/ui/main_window.py`, line 6757

**Fix:**
```python
# Before:
if any(var['name'] == name for var in existing_vars):

# After:
if any(var['key'] == name for var in existing_vars):
```

**Testing:**
1. Open any collection
2. Try to add a collection variable
3. Should work without KeyError
4. Try to add duplicate variable name - should prompt for overwrite

---

### 2. False "Unsaved Changes" on Ctrl+S with No Request ❌ → ✅

**Problem:**
1. Start application with no request selected
2. Press Ctrl+S
3. Get warning "No request selected to save!" (correct)
4. Try to open/create any request
5. Get prompted about "unsaved changes" (incorrect - nothing was opened yet!)

**Root Cause (Multiple Issues):**

**Issue A:** `_save_request()` called `_convert_temporary_to_persistent()` before validation
- This function modifies tab state even when there's nothing to save
- When showing the "No request selected" warning, tab was already marked as changed

**Issue B:** `_mark_as_changed()` doesn't validate if there's a request loaded
- Connected to `textChanged` signals on URL and body inputs
- When warning dialog appears, it might trigger widget signals
- These signals call `_mark_as_changed()` which blindly marks any tab as changed
- No check if there's actually a request to mark as changed

**Location:** 
- `src/ui/main_window.py`, line 4242 (Issue A)
- `src/ui/main_window.py`, line 4016 (Issue B)

**Fix A - Reorder save validation:**
```python
# Before:
def _save_request(self):
    # Convert temporary tab to persistent when saving request
    self._convert_temporary_to_persistent()  # Called BEFORE checking if there's a request!
    
    # ... checks ...
    
    if not self.current_request_id:
        QMessageBox.warning(self, "Warning", "No request selected to save!")
        return  # Returns but tab state was already modified!

# After:
def _save_request(self):
    # ... checks FIRST ...
    
    if is_new_request:
        # Convert temporary tab to persistent when saving new request
        self._convert_temporary_to_persistent()
        self._save_new_request()
        return
    
    if not self.current_request_id:
        QMessageBox.warning(self, "Warning", "No request selected to save!")
        # Don't convert temporary tab if there's nothing to save
        return
    
    # Convert temporary tab to persistent only when actually saving
    self._convert_temporary_to_persistent()
```

**Fix B - Add validation to _mark_as_changed():**
```python
# Before:
def _mark_as_changed(self):
    """Mark the request as having unsaved changes."""
    if not self.has_unsaved_changes:
        self.has_unsaved_changes = True
        self._update_request_title()
        
        # Update current tab's unsaved indicator
        current_tab_index = self.request_tabs.currentIndex()
        if current_tab_index >= 0 and current_tab_index in self.tab_states:
            self.tab_states[current_tab_index]['has_changes'] = True
            self._update_tab_title(current_tab_index)

# After:
def _mark_as_changed(self):
    """Mark the request as having unsaved changes."""
    # Don't mark as changed if there's no request loaded
    current_tab_index = self.request_tabs.currentIndex()
    if current_tab_index < 0:
        return  # No tab open
    
    if current_tab_index not in self.tab_states:
        return  # Tab has no state
    
    # Don't mark as changed if this tab has no request (empty/new tab with no data)
    tab_state = self.tab_states[current_tab_index]
    if not tab_state.get('request_id') and not self.current_request_id:
        return  # No request to mark as changed
    
    if not self.has_unsaved_changes:
        self.has_unsaved_changes = True
        self._update_request_title()
        
        # Update current tab's unsaved indicator
        self.tab_states[current_tab_index]['has_changes'] = True
        self._update_tab_title(current_tab_index)
```

**Key Changes:**
1. **In `_save_request()`:** Check if there's a request to save BEFORE modifying any state
2. **In `_mark_as_changed()`:** Validate that there's an actual request before marking as changed
   - Check tab exists and has state
   - Check there's a `request_id` in the tab state or `current_request_id` is set
   - Only mark as changed when there's actual content to track
3. Only call state-modifying functions when:
   - Saving a new request (after user confirms)
   - Saving an existing request (after validation passes)
   - There's actual request data loaded

**Testing:**
1. Launch app with no request selected
2. Press Ctrl+S → Should show "No request selected" warning
3. Click OK on warning
4. Create new request (Ctrl+N) → Should NOT prompt about unsaved changes ✅
5. Open existing request → Should NOT prompt about unsaved changes ✅
6. Make actual changes to a request → SHOULD prompt about unsaved changes ✅ (correct behavior)
7. Type in URL field with no request → Should NOT mark as changed ✅
8. Focus/blur inputs with no request → Should NOT mark as changed ✅

---

## Files Modified

- `src/ui/main_window.py`
  - Line 6757: Fixed collection variable key checking (`'key'` instead of `'name'`)
  - Lines 4239-4265: Reordered `_save_request()` to check validity before modifying state
  - Lines 4016-4036: Enhanced `_mark_as_changed()` to validate request exists before marking changes

---

## Impact

### Before Fixes:
- ❌ Cannot add collection variables (KeyError crash)
- ❌ False unsaved changes warnings appearing randomly
- ❌ Confusing UX when pressing Ctrl+S without a request

### After Fixes:
- ✅ Collection variables work correctly
- ✅ Unsaved changes tracking is accurate
- ✅ Clean UX - warnings only appear when appropriate
- ✅ No phantom state modifications

---

## Related Code Quality

These fixes highlight good practices:
1. **Validate before modifying state** - Check conditions before making changes
2. **Match database schema** - Use correct field names from database
3. **Early returns with guards** - Validate inputs before proceeding
4. **Clear error messages** - User knows exactly what's wrong

---

**Status:** ✅ **Both issues resolved**
**Date:** November 13, 2025
**Testing:** Ready for verification
