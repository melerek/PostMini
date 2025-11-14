# Bug Fixes Summary - November 13, 2025

## Issues Fixed

### 1. ✅ Collection Variable KeyError (FIXED)
**Issue:** Getting `KeyError: 'name'` when adding collection variables  
**Root Cause:** Database returns field as 'key' but code was looking for 'name'  
**Fix:** Changed `var['name']` to `var['key']` in main_window.py line 6757  
**Status:** FIXED

### 2. ✅ False "Unsaved Changes" Warnings (FIXED)
**Issue:** Pressing Ctrl+S on empty screen showed warning, then false "unsaved changes" prompts  
**Root Cause:** Two issues:
- `_save_request()` called state conversion before validation
- `_mark_as_changed()` had no validation guards

**Fixes:**
- Reordered validation in `_save_request()` (lines 4239-4265)
- Added validation checks in `_mark_as_changed()` (lines 4016-4036)

**Status:** FIXED

### 3. ✅ Folder Collapse on Request Deletion (FIXED)
**Issue:** Deleting a request from a folder caused the folder to collapse  
**Root Cause:** Multiple issues:
- Tab wasn't being closed when deleting current request
- Wrong method name (`_close_tab_internal` vs `_close_tab`)
- Folder expansion state wasn't preserved through all reload cycles
- Only immediate folder was tracked, not parent folders
- Folders set as expanded during tree construction but Qt collapsed them afterward

**Fixes:**
- Added tab closing logic when deleting open request (line 8486)
- Fixed method name to `_close_tab()` (line 8493)
- Move expansion set clearing to end of `_load_collections()` (lines 2900-2903)
- Use `_add_folder_and_parents_to_expanded()` to track entire parent chain (line 8478)
- Added second-pass forced expansion after tree is fully built (lines 2894-2898)
- Created `_force_expand_folders_recursive()` helper method (lines 2714-2723)

**Status:** FIXED

### 4. ✅ Folder Collapse on Adding Subfolder (FIXED)
**Issue:** Adding a subfolder caused parent folders to collapse  
**Root Cause:** Same as issue #3 - parent folder chain wasn't being preserved  
**Fixes:**
- Updated `_add_folder_to_collection()` to track collection expansion (lines 3598-3616)
- Updated `_add_folder_to_folder()` to track parent folder AND all ancestors using `_add_folder_and_parents_to_expanded()` (lines 3620-3642)

**Status:** FIXED

### 5. ✅ Scripts Not Imported from Postman Collections (FIXED)
**Issue:** Pre-request and post-response scripts weren't imported from Postman collections  
**Root Cause:** 
- Internal format export/import was working correctly
- **Postman converter didn't extract scripts from Postman `event` arrays**
- Scripts in Postman are stored in `event` array with `listen: "prerequest"` and `listen: "test"`

**Fixes:**
- Updated `export_collection()` to include complete folder hierarchy (collection_io.py lines 33-127)
- **Added script extraction in `_convert_postman_item_to_request()`** (postman_converter.py lines 345-363)
- **Added script export in `_convert_request_to_postman()`** (postman_converter.py lines 158-182)

**Status:** FIXED

### 6. ✅ Collection Variables Not Imported (FIXED)
**Issue:** Collection variables weren't being imported from either internal or Postman format  
**Root Cause:** 
- Export method didn't export collection variables
- Import method didn't import collection variables
- **Postman converter** didn't extract/convert collection variables

**Fixes:**
- Added collection variables to export in `export_collection()` (collection_io.py lines 85-90)
- Added collection variables import in `import_collection()` (collection_io.py lines 270-277)
- **Added collection variables extraction in `from_postman_format()`** (postman_converter.py lines 176-181)
- **Added collection variables export in `to_postman_format()`** (postman_converter.py lines 43-48)

**Status:** FIXED

## Files Modified

### `src/ui/main_window.py`
- Line 4016-4036: Enhanced `_mark_as_changed()` with validation
- Line 4239-4265: Reordered `_save_request()` validation
- Line 6757: Fixed collection variable field name
- Lines 2714-2723: Added `_force_expand_folders_recursive()` method
- Lines 2774-2777: Added folder/collection expansion merging
- Lines 2894-2898: Added second-pass folder expansion
- Lines 2900-2903: Moved expansion set clearing to end
- Lines 8462-8490: Updated deletion to track parent folders and close tabs
- Lines 3598-3616: Updated `_add_folder_to_collection()` to preserve expansion
- Lines 3620-3642: Updated `_add_folder_to_folder()` to preserve parent expansion

### `src/features/collection_io.py`
- Lines 33-127: Complete rewrite of `export_collection()` to include:
  - Folder hierarchy with paths
  - Collection variables
  - folder_path for each request
- Lines 270-277: Added collection variables import in `import_collection()`

### `src/features/postman_converter.py`
- Lines 43-48: Added collection variables export in `to_postman_format()`
- Lines 158-182: Added scripts (pre-request and test) export in `_convert_request_to_postman()`
- Lines 176-181: Added collection variables extraction in `from_postman_format()`
- Lines 345-363: Added scripts extraction from Postman events in `_convert_postman_item_to_request()`

## Testing Recommendations

1. **Collection Variables:** Add, edit, delete collection variables - verify no KeyError
2. **Unsaved Changes:** 
   - Press Ctrl+S with no request open - should not show warning
   - Open request, don't change anything, try to close/switch - should not prompt
3. **Folder Expansion - Delete:**
   - Create nested folders (Folder1 → Folder2 → Folder3)
   - Add request to Folder3
   - Delete that request
   - Verify ALL parent folders remain expanded
4. **Folder Expansion - Add Subfolder:**
   - Expand nested folders
   - Add a subfolder to any folder
   - Verify all parent folders remain expanded
5. **Collection Import/Export:**
   - Create collection with folders, subfolders, requests with scripts, and collection variables
   - Export collection
   - Delete collection
   - Import collection
   - Verify: folders, scripts, and collection variables are all present

## Next Steps

1. Test all fixes thoroughly
2. Rebuild application (v1.9.1?)
3. Update CHANGELOG.md with bug fixes
4. Consider adding these scenarios to automated tests
