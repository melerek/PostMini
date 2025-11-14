# Drag & Drop Ordering Implementation Plan

## Overview
Enable manual ordering of collections, folders, and requests through drag & drop interface while maintaining all existing functionality.

## Current State Analysis

### Database Schema
- **collections table**: No `order_index` field
- **folders table**: No `order_index` field  
- **requests table**: No `order_index` field

### Current Behavior
- Collections/folders/requests likely sorted by ID or name (alphabetically)
- No user-defined ordering
- Tree widget doesn't have drag/drop enabled

## Implementation Strategy

### Phase 1: Database Schema Updates ✅
Add ordering fields without breaking existing data:

1. **Add `order_index` column to collections table**
   - Default value: `id * 100` (preserves current order)
   - Nullable initially for safety

2. **Add `order_index` column to folders table**
   - Scoped per collection (ordering within parent)
   - Default value: `id * 100`

3. **Add `order_index` column to requests table**
   - Scoped per collection/folder (ordering within parent)
   - Default value: `id * 100`

### Phase 2: Database Methods ✅
Add methods without modifying existing ones:

```python
# New methods to add to DatabaseManager:

def reorder_collections(self, collection_ids_in_order: List[int]):
    """Update order_index for collections based on new order."""
    
def reorder_folders(self, collection_id: int, folder_ids_in_order: List[int]):
    """Update order_index for folders within a collection."""
    
def reorder_requests(self, parent_id: int, is_folder: bool, request_ids_in_order: List[int]):
    """Update order_index for requests within a collection or folder."""
```

### Phase 3: UI Changes ✅
Enable drag & drop on collections tree:

1. **Enable drag/drop on tree widget**
   ```python
   self.collections_tree.setDragEnabled(True)
   self.collections_tree.setAcceptDrops(True)
   self.collections_tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
   ```

2. **Implement drop validation**
   - Collections can only be reordered at root level
   - Folders can move within same collection or to another collection
   - Requests can move within same parent or to different folder
   - Cannot drop collection into folder, etc.

3. **Handle drop events**
   - Override `dropEvent` or connect to drag/drop signals
   - Update database order_index values
   - Prevent breaking folder hierarchy
   - Maintain expanded/collapsed states

### Phase 4: Loading with Order ✅
Modify `_load_collections()` to respect order:

```python
# Change FROM:
collections = self.db.get_all_collections()

# Change TO:
collections = self.db.get_all_collections_ordered()
```

Similar changes for folders and requests loading.

### Phase 5: Safety Measures ✅

1. **Backup before changes**
   - Create database backup before implementing

2. **Transaction safety**
   - Use database transactions for reordering
   - Rollback on errors

3. **Validation**
   - Verify parent relationships remain valid
   - Ensure no circular dependencies
   - Check order_index uniqueness within scope

4. **Existing functionality preservation**
   - All CRUD operations continue to work
   - Search/filter not affected
   - Import/export maintains order
   - Keyboard navigation works
   - Context menus work

## Implementation Steps

### Step 1: Database Migration
```sql
-- Add order_index columns with safe defaults
ALTER TABLE collections ADD COLUMN order_index INTEGER;
ALTER TABLE folders ADD COLUMN order_index INTEGER;
ALTER TABLE requests ADD COLUMN order_index INTEGER;

-- Set initial values based on existing IDs
UPDATE collections SET order_index = id * 100 WHERE order_index IS NULL;
UPDATE folders SET order_index = id * 100 WHERE order_index IS NULL;
UPDATE requests SET order_index = id * 100 WHERE order_index IS NULL;
```

### Step 2: Add Database Methods
- `reorder_collections()`
- `reorder_folders()`
- `reorder_requests()`
- `get_all_collections_ordered()`
- `get_folders_by_collection_ordered()`
- `get_requests_ordered()`

### Step 3: Modify Loading Logic
- Update `_load_collections()` to sort by order_index
- Update folder loading to sort by order_index
- Update request loading to sort by order_index

### Step 4: Enable Drag & Drop
- Set tree widget drag/drop properties
- Implement drop validation logic
- Handle reordering on drop

### Step 5: Testing
- Test drag/drop within same parent
- Test drag/drop to different parent
- Test moving folders between collections
- Test moving requests between folders
- Verify existing features still work
- Test import/export preserves order

## Risk Mitigation

### Risks
1. **Breaking existing queries**: Mitigated by adding new methods, not modifying existing
2. **Data loss on drop**: Mitigated by transactions and validation
3. **UI becoming unresponsive**: Mitigated by efficient database updates
4. **Circular dependencies**: Mitigated by validation before save
5. **Import/export losing order**: Mitigated by including order_index in export

### Rollback Plan
If issues occur:
1. Restore database from backup
2. Remove drag/drop UI code
3. System returns to original behavior

## Success Criteria
- ✅ Users can drag/drop to reorder collections
- ✅ Users can drag/drop to reorder folders within collection
- ✅ Users can drag/drop to reorder requests within parent
- ✅ Order persists across app restarts
- ✅ All existing CRUD operations work unchanged
- ✅ Import/export maintains order
- ✅ No performance degradation
- ✅ Folder expansion states preserved after reorder

## Future Enhancements
- Drag folders between collections (cross-collection move)
- Drag requests between collections/folders
- Multi-select drag/drop
- Keyboard shortcuts for reordering (Ctrl+Up/Down)
- "Sort alphabetically" option in context menu
