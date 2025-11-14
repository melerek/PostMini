# Drag & Drop Testing Guide

## ✅ Changes Made to Fix Drag & Drop

### Problems Found & Fixed:
1. **Selection Mode** was set to `NoSelection` - drag & drop requires selection to work
   - ✅ Changed to `SingleSelection`

2. **Item Flags** were not set - items need drag/drop flags
   - ✅ Added `ItemIsDragEnabled` and `ItemIsDropEnabled` to all items

3. **Data Key Mismatch** - Code was looking for wrong key names
   - ✅ Fixed to use 'id' consistently

4. **Invalid Drop Operations** - Items could be dropped in invalid locations
   - ✅ Added `dropMimeData()` validation to prevent:
     - ❌ Dropping requests on other requests (causes disappearance)
     - ❌ Dropping collections inside anything (must stay at root)
     - ❌ Dropping folders on requests

### Validation Rules Implemented:
```
✅ Collections: Can only be reordered at root level
✅ Folders: Can be dropped on collections or other folders
✅ Requests: Can be dropped on folders or collections
❌ Request → Request: BLOCKED (prevents disappearance bug)
❌ Collection → Anything: BLOCKED (must stay at root)
❌ Folder → Request: BLOCKED (invalid hierarchy)
```

## 🧪 How to Test Drag & Drop

### Test 1: Reorder Collections
1. Create 3 collections with different names:
   - "Collection Z"
   - "Collection A"
   - "Collection M"

2. Try dragging "Collection A" above "Collection Z"
3. **Expected:** Collection A should move to the top
4. **Verify:** Close and restart app - order should be preserved

### Test 2: Reorder Folders
1. Create a collection with 3 folders:
   - "Setup"
   - "Tests"
   - "Cleanup"

2. Drag "Cleanup" to the top
3. **Expected:** Cleanup should appear first
4. **Verify:** Order persists after restart

### Test 3: Reorder Requests
1. Create 3 requests in a folder:
   - "3-Delete User"
   - "1-Create User"
   - "2-Update User"

2. Drag them into logical order (Create, Update, Delete)
3. **Expected:** Requests reorder as dragged
4. **Verify:** Order persists after restart

### Test 4: Nested Folders
1. Create nested folder structure:
   ```
   API v2
   ├── Auth
   ├── Users
   └── Products
   ```

2. Drag "Users" to be first child of "API v2"
3. **Expected:** Users moves to first position
4. **Verify:** Order persists

### Test 5: Visual Feedback
1. Start dragging any item
2. **Expected:** You should see:
   - Item being dragged
   - Drop indicator line showing where item will be placed
   - Cursor changes to indicate drag operation

### Test 6: Invalid Drops (Should be Prevented)
These operations should be **BLOCKED** and won't work:

**❌ Request on Request:**
1. Try dragging a request and dropping it on another request
2. **Expected:** Drop indicator should NOT appear, cursor shows "no drop" icon
3. **Result:** Request stays in original position (doesn't disappear!)

**❌ Collection Inside Anything:**
1. Try dragging a collection into a folder
2. **Expected:** Cannot drop, stays at root level

**❌ Folder on Request:**
1. Try dragging a folder onto a request
2. **Expected:** Cannot drop, folder stays in place

**✅ These Drops ARE Allowed:**
- Request → Folder (moves/reorders within folder)
- Request → Collection (moves/reorders at collection root)
- Folder → Folder (nests folders)
- Folder → Collection (moves folder to collection root)
- Collection → Root (reorders collections)

## 🐛 Troubleshooting

### Drag Still Not Working?
1. **Check item is selected:** Click the item first - it should be highlighted
2. **Check cursor:** When dragging, cursor should show drag icon
3. **Check console:** Look for any error messages in terminal

### Order Not Persisting?
1. Check database file exists: `api_client.db`
2. Look for error messages in console: "Error reordering items: ..."
3. Verify order_index column exists (should have been added automatically)

### Selection Visible?
- **Note:** Selection highlighting IS now visible (blue/gray background)
- This is REQUIRED for drag & drop to work
- This is normal Qt behavior

## 📝 What You Should See

### When Dragging Works:
1. **Click and hold** on an item → Background highlights (selected)
2. **Start dragging** → Cursor changes, item follows mouse
3. **Hover over drop location** → Horizontal line shows where it will drop
4. **Release mouse** → Item moves to new position immediately
5. **Restart app** → Order is preserved

### Console Output:
You should NOT see any error messages. If reordering works, you won't see any output (silent success).

If there's an error, you'll see:
```
Error reordering items: <error message>
```

## ✨ Success Criteria

Drag & drop is working correctly if:
- [x] You can click and drag collections up/down
- [x] You can click and drag folders up/down
- [x] You can click and drag requests up/down
- [x] Drop indicator line shows where item will land
- [x] Item moves immediately when dropped
- [x] Order persists after app restart
- [x] No error messages in console

## 🎯 Next Steps

If everything works:
1. Test with your real collections
2. Verify import/export preserves order
3. Test with large collections (100+ requests)
4. Enjoy your new ordering feature! 🎉

If something doesn't work:
1. Check console for error messages
2. Verify you can select items (click them)
3. Try restarting the app fresh
4. Let me know the specific issue

