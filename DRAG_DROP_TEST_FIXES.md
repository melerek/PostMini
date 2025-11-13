# Drag & Drop Ordering - Test Fixes Summary

## Issues Fixed

### 1. Wrong Parameter Order in create_request() Calls
**Problem**: Tests were calling `create_request(collection_id, name, method, url)` but actual signature is `create_request(name, url, method, collection_id)`.

**Fixed Tests**:
- `test_requests_ordered_by_order_index`
- `test_reorder_requests_within_folder`

**Fix**: Corrected parameter order to match the actual API signature.

---

### 2. Missing ORDER BY order_index in Database Queries
**Problem**: `get_requests_by_folder()` was ordering by `name` instead of `order_index`, causing reordering tests to fail.

**Fixed**: Updated SQL queries in `src/core/database.py` lines 1527 and 1536:
```sql
-- Before
ORDER BY name

-- After
ORDER BY order_index
```

---

### 3. Missing order_index in get_folders_by_collection() Return
**Problem**: `get_folders_by_collection()` wasn't selecting or returning `order_index` field, causing KeyError in import tests.

**Fixed**: Updated `src/core/database.py` line 1310-1337:
- Added `order_index` to SELECT statement
- Added `'order_index': row[5]` to returned dictionary

---

### 4. Wrong Export Format Expectation
**Problem**: Tests expected collection data directly, but `export_collection()` returns `{"collection": {...}}` structure.

**Fixed Test**: `test_export_includes_order_index`
- Changed to access `export_data['collection']` instead of `export_data`

---

### 5. Wrong Import Format in Tests
**Problem**: Tests provided raw collection data, but `import_collection()` expects `{"collection": {...}}` structure.

**Fixed Tests**:
- `test_import_preserves_order_index`
- `test_import_without_order_index_uses_position`

**Fix**: Wrapped test data in `{"collection": {...}}` structure.

---

### 6. Wrong Return Value Handling from import_collection()
**Problem**: Tests expected `collection_id` directly, but `import_collection()` returns `Tuple[bool, str, Optional[int]]`.

**Fixed Tests**:
- `test_import_preserves_order_index`
- `test_import_without_order_index_uses_position`

**Fix**: Changed to:
```python
success, message, collection_id = importer.import_collection(import_data)
assert success, f"Import failed: {message}"
```

---

### 7. Wrong Database Fixture Usage
**Problem**: `test_order_persists_after_db_reopen` tried to use existing db fixture with tmp_path, causing path confusion.

**Fixed**: Changed test to:
- Remove `db` from parameters
- Create its own DatabaseManager instance with tmp_path
- Properly close and reopen the database

---

## Test Results

**Before Fixes**: 11/17 passing (6 failures)
**After Fixes**: 17/17 passing ✅

## Files Modified

### Tests
- `tests/test_drag_drop_ordering.py` - Fixed 6 test methods

### Core Database
- `src/core/database.py` - Fixed 2 SQL queries and 1 return value

### Documentation
- `README.md` - Added drag & drop feature documentation
- Moved `docs/DRAG_DROP_ORDERING.md` → `docs/guides/DRAG_DROP_ORDERING.md`

## Verification

All drag & drop ordering tests now pass:
```
tests/test_drag_drop_ordering.py::TestOrderIndexMigration::test_collections_have_order_index PASSED
tests/test_drag_drop_ordering.py::TestOrderIndexMigration::test_folders_have_order_index PASSED
tests/test_drag_drop_ordering.py::TestOrderIndexMigration::test_requests_have_order_index PASSED
tests/test_drag_drop_ordering.py::TestOrderIndexMigration::test_default_order_index_value PASSED
tests/test_drag_drop_ordering.py::TestCollectionOrdering::test_collections_ordered_by_order_index PASSED
tests/test_drag_drop_ordering.py::TestCollectionOrdering::test_reorder_collections_updates_order_index PASSED
tests/test_drag_drop_ordering.py::TestFolderOrdering::test_folders_ordered_by_order_index PASSED
tests/test_drag_drop_ordering.py::TestFolderOrdering::test_reorder_folders_within_parent PASSED
tests/test_drag_drop_ordering.py::TestRequestOrdering::test_requests_ordered_by_order_index PASSED
tests/test_drag_drop_ordering.py::TestRequestOrdering::test_reorder_requests_within_folder PASSED
tests/test_drag_drop_ordering.py::TestOrderPersistence::test_order_persists_after_db_reopen PASSED
tests/test_drag_drop_ordering.py::TestImportExportOrder::test_export_includes_order_index PASSED
tests/test_drag_drop_ordering.py::TestImportExportOrder::test_import_preserves_order_index PASSED
tests/test_drag_drop_ordering.py::TestImportExportOrder::test_import_without_order_index_uses_position PASSED
tests/test_drag_drop_ordering.py::TestEdgeCases::test_reorder_empty_list PASSED
tests/test_drag_drop_ordering.py::TestEdgeCases::test_reorder_single_item PASSED
tests/test_drag_drop_ordering.py::TestEdgeCases::test_reorder_nonexistent_ids_ignored PASSED

==================================================================== 17 passed in 4.68s =====================================================================
```

## Notes

- One pre-existing test failure unrelated to drag & drop: `test_dynamic_variables.py::TestDynamicVariablesIntegration::test_substitution_in_url`
- All 17 drag & drop tests passing
- Database queries now properly use `order_index` for sorting
- Import/export tests now correctly handle the expected data formats
- Feature is production-ready
