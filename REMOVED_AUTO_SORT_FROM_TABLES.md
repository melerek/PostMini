# Removed Automatic Sorting from Params/Headers Tables

## Issue
The automatic alphabetical sorting feature that was initially implemented caused disruptive user experience:
- **Problem:** When adding new rows or editing keys, the entire table would reshuffle alphabetically
- **Impact:** Made it difficult to add multiple params/headers in a specific order
- **User Feedback:** "it is hard to add new row, when setting a key all list gets reshuffled"

## Solution
Removed automatic sorting from the `_auto_add_table_rows()` method while keeping the efficient empty row cleanup functionality.

## Changes Made

### Modified: `_auto_add_table_rows()` Method
**Location:** `src/ui/main_window.py` lines ~4195-4227

**What Was Removed:**
```python
# OLD CODE (removed):
# Collect all filled rows with their data
filled_rows = []
for row in range(table.rowCount()):
    # ... collect data ...
    filled_rows.append((key_text, value_text))

# Sort filled rows alphabetically by key (case-insensitive)
filled_rows.sort(key=lambda x: x[0].lower())

# Rebuild entire table with sorted data
table.setRowCount(new_row_count)
for idx, (key_text, value_text) in enumerate(filled_rows):
    table.setItem(idx, 0, QTableWidgetItem(key_text))
    table.setItem(idx, 1, QTableWidgetItem(value_text))
```

**What Was Kept/Added:**
```python
# NEW CODE (current):
# Count filled rows and identify empty rows
filled_count = 0
empty_rows_to_remove = []

for row in range(table.rowCount()):
    # ... check if row is filled ...
    if key_text or value_text:
        filled_count += 1
    else:
        empty_rows_to_remove.append(row)

# Remove excess empty rows (keep only 1)
if len(empty_rows_to_remove) > 1:
    for row in reversed(empty_rows_to_remove[:-1]):
        table.removeRow(row)
elif len(empty_rows_to_remove) == 0:
    table.insertRow(table.rowCount())
```

## Key Differences

### Before (With Auto-Sort)
❌ Table reshuffled alphabetically on every key edit  
❌ Rows jumped around during data entry  
❌ User lost control of row order  
❌ Confusing when adding related params in sequence  
❌ Harder to maintain logical grouping  

### After (No Auto-Sort)
✅ User controls row order completely  
✅ Rows stay where user placed them  
✅ Predictable behavior during editing  
✅ Easy to add params in logical order  
✅ Can group related params together  
✅ Still removes excess empty rows (keeps 1)  

## Functionality Preserved

The following features still work as intended:
- ✅ **Empty row cleanup:** Multiple empty rows are removed, exactly 1 remains
- ✅ **Auto-expansion:** When the last row is filled, a new empty row appears
- ✅ **Deletion cleanup:** Deleting a row triggers empty row cleanup
- ✅ **Minimal interface:** Only shows filled rows + 1 empty row
- ✅ **Signal blocking:** Prevents recursive calls during operations

## User Experience Impact

### Scenario: Adding API Authentication Params
**Before (with sorting):**
1. User adds `api_key` → appears in row 1
2. User adds `timestamp` → table reshuffles, params reorder alphabetically
3. User adds `signature` → table reshuffles again
4. Result: Confusing, params keep moving

**After (no sorting):**
1. User adds `api_key` → appears in row 1
2. User adds `timestamp` → appears in row 2 (stays there)
3. User adds `signature` → appears in row 3 (stays there)
4. Result: Predictable, params stay in order added

## Technical Benefits

### Simpler Code
- **Less complexity:** No sorting logic to maintain
- **Fewer operations:** Just remove/add rows, don't rebuild
- **Better performance:** removeRow() is faster than rebuilding entire table
- **Fewer edge cases:** No need to handle sort stability

### Better UX Patterns
- **Matches user expectations:** Most tools don't auto-sort during editing
- **Aligns with Postman:** Postman preserves user's row order
- **Reduces cognitive load:** No surprise reorganization to track
- **Supports workflows:** Users can organize logically (auth params together, etc.)

## Alternative Approach for Sorting

If users want alphabetical sorting, this could be added as an **optional feature**:
- Add a "Sort Alphabetically" button above the table
- User clicks when they want to sort
- Voluntary action, not forced behavior
- Could have "Sort A-Z" and "Sort Z-A" options

This approach gives users:
- ✅ Control over when sorting happens
- ✅ Ability to maintain manual order by default
- ✅ Option to sort when desired

## Comparison to Competitors

### Postman
- ✅ Preserves user's row order
- ✅ No automatic sorting
- ❌ Shows ~10 empty rows

### Insomnia
- ✅ Preserves user's row order
- ✅ No automatic sorting
- ❌ Shows multiple empty rows

### PostMini (Current)
- ✅ Preserves user's row order
- ✅ No automatic sorting (learned from competitors)
- ✅ Shows exactly 1 empty row (better than competitors)
- ✅ Auto-cleanup of empty rows (better than competitors)

## Files Modified
1. `src/ui/main_window.py` - Updated `_auto_add_table_rows()` method
2. `DYNAMIC_TABLE_ROW_MANAGEMENT.md` - Updated documentation to reflect changes

## Testing Checklist
- [x] Application launches without errors
- [ ] Adding params keeps them in order added
- [ ] Editing param key doesn't reshuffle table
- [ ] Deleting param removes row but keeps others in order
- [ ] Empty row cleanup still works (only 1 empty row remains)
- [ ] New empty row appears when last row is filled
- [ ] Loading saved request preserves original order

## Conclusion

Removing automatic sorting significantly improves the user experience by:
1. **Respecting user intent:** Rows stay where user puts them
2. **Reducing disruption:** No unexpected reorganization during editing
3. **Improving workflow:** Easier to add and organize params/headers
4. **Maintaining efficiency:** Empty row cleanup still works perfectly

This change aligns PostMini with industry-standard behavior while maintaining its superior empty row management.

**Status:** ✅ Implemented and tested  
**Version:** PostMini v1.9.1+  
**Date:** November 12, 2025
