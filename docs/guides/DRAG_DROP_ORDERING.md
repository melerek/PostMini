# Drag & Drop Ordering Feature

## Overview

PostMini now supports full drag & drop ordering for collections, folders, and requests. Users can reorder items by dragging and dropping them, and the order persists across application restarts and import/export operations.

## Features

### User-Controlled Ordering
- **Collections**: Can be reordered at the root level (drag above/below other collections)
- **Folders**: Can be reordered within their parent (collection or folder)
- **Requests**: Can be reordered within their parent (collection or folder)

### Drag & Drop Operations
- **Visual feedback**: Drop indicators show where items will be placed (above, below, or inside)
- **Persistent order**: Order is saved to the database immediately
- **Import/export**: Order is preserved when exporting/importing collections
- **Count updates**: Item counts automatically refresh after moves

### Validation Rules

#### Collections
- ✅ Can be reordered at root level (above/below other collections)
- ❌ Cannot be nested inside anything (must stay at root)
- ❌ Cannot be dropped next to folders or requests

#### Folders
- ✅ Can be moved within their collection (to collection root or other folders)
- ✅ Can be reordered among sibling folders
- ❌ Cannot be moved between different collections
- ❌ Cannot be placed at root level (outside collections)
- ❌ Cannot be dropped on requests
- ❌ Cannot be dropped into themselves
- ❌ Cannot be dropped into their own descendants (circular reference prevention)

#### Requests
- ✅ Can be moved between collections
- ✅ Can be moved between folders
- ✅ Can be moved from folder to collection root
- ✅ Can be reordered among sibling requests
- ❌ Cannot be dropped ON other requests (but can be dropped above/below)

## Database Schema

### Order Index
Each table has an `order_index` column:
- **collections.order_index**: INTEGER (default: id * 100)
- **folders.order_index**: INTEGER (default: id * 100)
- **requests.order_index**: INTEGER (default: id * 100)

The 100-unit spacing allows for future insertions without reordering all items.

### Queries
All queries that retrieve collections, folders, or requests now use `ORDER BY order_index` instead of `ORDER BY name`.

### Reordering Methods
```python
db.reorder_collections(collection_ids_in_order)
db.reorder_folders(collection_id, folder_ids_in_order)
db.reorder_requests(collection_id, folder_id, request_ids_in_order)
```

## Import/Export

### Order Preservation
When exporting collections, the `order_index` is included in the JSON:
```json
{
  "name": "My Collection",
  "order_index": 100,
  "folders": [
    {
      "name": "Folder 1",
      "order_index": 100,
      "requests": [
        {
          "name": "Request 1",
          "order_index": 100
        }
      ]
    }
  ]
}
```

When importing:
- If `order_index` is present in JSON, it's used
- If not present, items are assigned order based on their position (0, 100, 200, ...)

## Technical Implementation

### UI Components

#### ReorderableTreeWidget
Custom QTreeWidget subclass that handles drag & drop:

```python
class ReorderableTreeWidget(QTreeWidget):
    def startDrag(self, supportedActions):
        # Captures dragged item data before drag starts
        
    def dropMimeData(self, parent, index, data, action):
        # Validates drop operations before allowing them
        # Returns False to block invalid drops
        
    def dropEvent(self, event):
        # Handles drop completion and database updates
        # Validates drop one final time
        # Calls _handle_tree_reorder() to update database
```

#### Drag & Drop Settings
```python
collections_tree.setDragEnabled(True)
collections_tree.setAcceptDrops(True)
collections_tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
collections_tree.setDropIndicatorShown(True)
collections_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
```

**Important**: `SingleSelection` mode is **required** for drag & drop to work in QTreeWidget.

#### Item Flags
Each tree item must have drag/drop flags enabled:
```python
item.setFlags(
    item.flags() | 
    Qt.ItemFlag.ItemIsDragEnabled | 
    Qt.ItemFlag.ItemIsDropEnabled
)
```

### Validation Logic

Validation happens in two places for robustness:

1. **dropMimeData()**: Pre-validation before Qt processes the drop
   - Returns `False` to block invalid drops
   - Checks collection nesting, folder constraints, circular references
   
2. **dropEvent()**: Final validation after Qt's processing
   - Can block drops that passed dropMimeData
   - Updates database if valid

### Drop Indicators
- **OnItem**: Drop inside the target (nest as child)
- **AboveItem**: Drop above the target (insert before)
- **BelowItem**: Drop below the target (insert after)

### Database Updates

#### Move Detection
When an item is dropped, the system detects:
- **Reorder**: Item stayed in same parent, just changed position
- **Move**: Item changed parent (different collection_id, folder_id, or parent_id)

#### Update Strategy
- **Reorder only**: Update order_index for all siblings
- **Move**: 
  1. Update parent relationship (collection_id, folder_id, parent_id)
  2. Update order_index for siblings in new parent
  3. Reload tree to refresh counts

### Count Updates

When items are moved between parents:
- Tree is reloaded via `_load_collections()`
- Counts are recalculated from database
- Expanded state of affected folders is preserved

### Circular Reference Prevention

For folders, the system prevents:
- Dropping a folder into itself
- Dropping a folder into its own descendant

Detection walks up the parent chain:
```python
def is_descendant(target, ancestor):
    current = target
    while current:
        if current.id == ancestor.id:
            return True
        current = current.parent()
    return False
```

### Expanded State Preservation

When tree reloads after moves:
1. Captures all currently expanded collections and folders
2. Adds affected collections/folders to keep-expanded set
3. Adds current request's folder/collection to keep-expanded set
4. Reloads tree
5. Re-expands saved items
6. Clears keep-expanded sets

## Usage

### Reordering Items
1. Click and hold on a collection, folder, or request
2. Drag to desired position
3. Drop indicator shows where item will be placed:
   - Line above/below = reorder (same level)
   - Highlight = nest inside (if valid)
4. Release to drop
5. Order is saved immediately

### Moving Between Parents
1. Drag a folder or request
2. Drop ON a collection or folder to nest inside
3. Drop ABOVE/BELOW to place at same level
4. Tree reloads to show updated counts

### Invalid Operations
When you attempt an invalid drop:
- No drop indicator is shown
- Item snaps back to original position
- Console shows block reason (for debugging)

## Performance Considerations

### Order Index Spacing
- Uses 100-unit spacing (100, 200, 300, ...)
- Allows inserting items without renumbering entire list
- When gap gets too small, reordering regenerates indexes

### Tree Reload on Move
- Reordering: No reload, instant update
- Moving: Tree reloads to recalculate counts
- Reload preserves expanded state of relevant folders

### Transaction Safety
All database updates use transactions:
```python
try:
    cursor.execute("UPDATE ...")
    connection.commit()
except:
    connection.rollback()
    # Reload tree to restore correct state
```

## Debugging

### Debug Messages
During development, debug messages show:
- `[DROP EVENT]`: Drop event details
- `[FOLDER MOVE]`: Old and new parent IDs
- `[MOVE]`: Database update confirmation
- `[DB VERIFY]`: Database state after update
- `[RELOAD CHECK]`: Whether reload is needed
- `[RELOAD]`: Reload triggered
- `[BLOCK]`: Why a drop was blocked

### Common Issues

**Items not saving position**:
- Check that UserRole data includes all required fields (id, collection_id, parent_id, folder_id)
- Verify database UPDATE is being executed
- Check transaction is committed

**Items disappearing after drop**:
- Validation is blocking the drop
- Check console for `[BLOCK]` messages
- Verify item flags include ItemIsDragEnabled and ItemIsDropEnabled

**Tree collapses after move**:
- Ensure _folders_to_keep_expanded and _collections_to_keep_expanded are set
- Check that current request's folder is being added to keep-expanded set

**Circular reference error**:
- System correctly prevented invalid folder nesting
- Check that circular reference detection is working

## Future Enhancements

Potential improvements:
- Batch reordering (select multiple items and move together)
- Undo/redo for drag & drop operations
- Keyboard shortcuts for reordering (Ctrl+Up/Down)
- Visual animation for reordering operations
- Drag & drop between windows (if multiple instances)

## Testing

Key test scenarios:
1. Reorder collections at root level
2. Reorder folders within collection
3. Reorder requests within folder
4. Move folder from folder to collection root
5. Move request between folders
6. Move request between collections
7. Attempt invalid moves (should be blocked)
8. Order persists after restart
9. Order preserved in export/import
10. Counts update correctly after moves
11. Expanded state preserved during moves
12. Circular reference prevention works

## See Also

- [Database Schema](PROJECT_STRUCTURE.md#database)
- [UI Architecture](PROJECT_STRUCTURE.md#ui-components)
- [Collection Import/Export](../src/features/collection_io.py)
