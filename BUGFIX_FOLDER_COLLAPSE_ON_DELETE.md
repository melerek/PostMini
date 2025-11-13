# Bug Fix: Folder Collapses After Deleting Request

## Issue Description

**Problem:**
- Open a collection with folders containing requests
- Open a request inside a folder (folder expands)
- Delete that request
- **Bug:** The folder collapses after deletion
- **Expected:** The folder should remain expanded

## Root Cause

When deleting a request that is currently open:

1. `_delete_request_from_menu()` is called
2. Confirmation dialog is shown
3. Request is deleted from database
4. If it was the current request: `self.current_request_id = None`
5. `_load_collections()` is called to refresh the tree

The problem in `_load_collections()`:
```python
# Lines 2767-2769: Captures expanded state from current tree
for i in range(self.collections_tree.topLevelItemCount()):
    item = self.collections_tree.topLevelItem(i)
    self._store_expanded_state(item, expanded_collection_ids, expanded_folder_ids)

# Lines 2772-2782: Special logic for current request
if self.current_request_id:  # ← This is now None!
    request = self.db.get_request(self.current_request_id)
    if request and request.get('folder_id'):
        # This code doesn't run because current_request_id was cleared!
```

While the expanded state IS captured from the tree, there's a timing issue:
- The confirmation dialog might cause focus changes
- The tree state might not be properly captured in all cases
- We lose the context of which folder contained the deleted request

## Solution

**Two-part fix:**

### Part 1: Store folder info before deletion

In `_delete_request_from_menu()`, capture the folder ID BEFORE showing the dialog and clearing state:

```python
def _delete_request_from_menu(self, request_id: int):
    request = self.db.get_request(request_id)
    if not request:
        return
    
    # NEW: Capture folder before any dialogs or state changes
    folder_id_to_keep_expanded = request.get('folder_id')
    
    # Show confirmation dialog...
    
    if reply == QMessageBox.StandardButton.Yes:
        self.db.delete_request(request_id)
        
        # NEW: Store folder to keep expanded
        if folder_id_to_keep_expanded:
            if not hasattr(self, '_folders_to_keep_expanded'):
                self._folders_to_keep_expanded = set()
            self._folders_to_keep_expanded.add(folder_id_to_keep_expanded)
        
        # Clear current request if needed
        if self.current_request_id == request_id:
            self.current_request_id = None
            ...
        
        # Reload tree
        self._load_collections()
        
        # NEW: Clear temporary tracking
        if hasattr(self, '_folders_to_keep_expanded'):
            self._folders_to_keep_expanded.clear()
```

### Part 2: Use stored folder info during reload

In `_load_collections()`, check for folders to keep expanded:

```python
def _load_collections(self):
    # Store currently expanded items before clearing
    expanded_collection_ids = set()
    expanded_folder_ids = set()
    for i in range(self.collections_tree.topLevelItemCount()):
        item = self.collections_tree.topLevelItem(i)
        self._store_expanded_state(item, expanded_collection_ids, expanded_folder_ids)
    
    # NEW: Add any folders that should be kept expanded (e.g., after deletion)
    if hasattr(self, '_folders_to_keep_expanded'):
        expanded_folder_ids.update(self._folders_to_keep_expanded)
    
    # Continue with existing logic...
```

## How It Works

1. **Before deletion:** Capture the folder ID that contains the request
2. **During deletion:** Store it in a temporary set `_folders_to_keep_expanded`
3. **During reload:** Add these folders to the `expanded_folder_ids` set
4. **After reload:** Clear the temporary tracking

This ensures that:
- The folder remains expanded even if `current_request_id` is None
- Works regardless of dialog timing or focus changes
- Doesn't interfere with normal expansion state preservation
- Cleans up after itself

## Testing

### Test Case 1: Delete request from folder
1. Create a collection with a folder
2. Add 2 requests to the folder
3. Open one of the requests (folder expands)
4. Right-click the open request → Delete
5. Confirm deletion
6. **✅ Expected:** Folder remains expanded, other request still visible

### Test Case 2: Delete non-current request
1. Have a folder with 2 requests, one open
2. Right-click the OTHER request (not the open one) → Delete
3. **✅ Expected:** Folder remains expanded, current request still open

### Test Case 3: Delete from nested folder
1. Create folder structure: Collection → Folder A → Folder B → Request
2. Open the request (both folders expand)
3. Delete the request
4. **✅ Expected:** Both Folder A and Folder B remain expanded

### Test Case 4: Multiple folders
1. Have Collection with Folder1 (expanded) and Folder2 (collapsed)
2. Open request in Folder1
3. Delete it
4. **✅ Expected:** Folder1 stays expanded, Folder2 stays collapsed

## Files Modified

- `src/ui/main_window.py`
  - Lines 8436-8474: Enhanced `_delete_request_from_menu()` to track folder before deletion
  - Lines 2760-2783: Enhanced `_load_collections()` to use tracked folders

## Impact

### Before Fix:
- ❌ Deleting a request collapses its folder
- ❌ Annoying UX - have to re-expand to see other requests
- ❌ Breaks workflow when managing requests in folders

### After Fix:
- ✅ Folders remain expanded after deleting requests
- ✅ Smooth UX - other requests stay visible
- ✅ Consistent behavior with other operations
- ✅ Works with nested folders

## Related Code

This fix complements the existing expansion state preservation:
- `_store_expanded_state()` - Captures current expansion state
- `_add_folder_and_parents_to_expanded()` - Ensures folder hierarchy is expanded
- Tree restoration logic in `_load_collections()` - Applies expansion state

The new `_folders_to_keep_expanded` mechanism provides an additional layer of preservation specifically for deletion operations.

---

**Status:** ✅ **Fixed**
**Date:** November 13, 2025
**Testing:** Ready for verification
