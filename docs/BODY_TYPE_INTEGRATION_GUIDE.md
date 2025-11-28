# Next Steps for Body Type Support Integration

## Current Status
✅ **Database layer**: Complete - `body_type` column added, migration working  
✅ **Postman import**: Complete - body types preserved, headers auto-set  
✅ **API execution**: Complete - formdata/urlencoded/JSON all working  
✅ **Tests**: Complete - 11/11 tests passing (7 body type + 4 form-urlencoded)  

⏸️ **MainWindow integration**: Needed - UI doesn't pass body_type parameter yet  
⏸️ **CollectionIO**: Needed - Export/import doesn't include body_type field  

## Step 1: MainWindow Integration

### What Needs to Change
The `MainWindow` class needs to pass `body_type` parameter when creating or updating requests.

### Files to Modify
- `src/ui/main_window.py`

### Method Calls to Update

#### create_request() Calls
Search for: `self.db.create_request(`

**Pattern to Follow:**
```python
# OLD
request_id = self.db.create_request(
    collection_id, name, method, url, headers, body, 
    pre_request_script, post_response_script, tests_script
)

# NEW
request_id = self.db.create_request(
    collection_id, name, method, url, headers, body, 
    pre_request_script, post_response_script, tests_script,
    body_type='raw'  # or get from UI/request data
)
```

#### update_request() Calls
Search for: `self.db.update_request(`

**Pattern to Follow:**
```python
# OLD
self.db.update_request(
    request_id, name, method, url, params, headers, body,
    pre_request_script, post_response_script, tests_script
)

# NEW
self.db.update_request(
    request_id, name, method, url, params, headers, body,
    pre_request_script, post_response_script, tests_script,
    folder_id=None,  # or get from request data
    body_type='raw'  # or get from UI/request data
)
```

### Where to Get body_type Value

#### When Creating New Request
Default to `'raw'`:
```python
body_type = 'raw'
```

#### When Updating Existing Request
Get from current request data:
```python
request = self.db.get_request(request_id)
body_type = request.get('body_type', 'raw')
```

#### When Importing from Postman
Already handled by `PostmanConverter.from_postman_format()` - body_type is in the returned dict:
```python
collection_data = PostmanConverter.from_postman_format(postman_json)
for request_data in collection_data['collection']['requests']:
    body_type = request_data.get('body_type', 'raw')
    # Pass to create_request()
```

### Verification Command
```powershell
# Find all calls that need updating
grep -n "self.db.create_request\|self.db.update_request" src/ui/main_window.py
```

## Step 2: CollectionExporter/Importer

### What Needs to Change
The `CollectionExporter` and `CollectionImporter` classes need to include `body_type` field when exporting/importing `.postmini` JSON files.

### Files to Modify
- `src/features/collection_io.py`

### CollectionExporter.export_collection()

**Add body_type to request dict:**
```python
# Around line ~150-200 in collection_io.py
request_dict = {
    'name': request['name'],
    'method': request['method'],
    'url': request['url'],
    'params': request.get('params', {}),
    'headers': request.get('headers', {}),
    'body': request.get('body', ''),
    'body_type': request.get('body_type', 'raw'),  # ADD THIS LINE
    'pre_request_script': request.get('pre_request_script', ''),
    'post_response_script': request.get('post_response_script', ''),
    'tests': request.get('tests', ''),
    'order_index': request.get('order_index', 0)
}
```

### CollectionImporter.import_collection()

**Read body_type from JSON:**
```python
# When creating requests from imported data
body_type = request_data.get('body_type', 'raw')  # ADD THIS LINE

request_id = db.create_request(
    collection_id,
    request_data['name'],
    request_data['method'],
    request_data['url'],
    request_data.get('headers', {}),
    request_data.get('body', ''),
    request_data.get('pre_request_script', ''),
    request_data.get('post_response_script', ''),
    request_data.get('tests', ''),
    body_type=body_type  # ADD THIS LINE
)
```

### Verification
1. Export a collection to JSON
2. Check the JSON file includes `"body_type": "raw"` for each request
3. Import the JSON file
4. Verify body_type is preserved in database

## Step 3: End-to-End Testing

### Create Test Collection in Postman

1. **Request 1**: Raw JSON body
   - Method: POST
   - Body type: raw (JSON)
   - Body: `{"name": "test"}`

2. **Request 2**: Form-data
   - Method: POST
   - Body type: form-data
   - Fields: `username=admin`, `password=secret`

3. **Request 3**: URL-encoded
   - Method: POST
   - Body type: x-www-form-urlencoded
   - Fields: `grant_type=password`, `username=admin`

4. **Request 4**: GraphQL
   - Method: POST
   - Body type: GraphQL
   - Query: `{ users { id name } }`

### Test Steps

```powershell
# 1. Export from Postman
# Save as "body_type_test_collection.json"

# 2. Import to PostMini
# File → Import Collection → Select JSON file

# 3. Verify database
sqlite3 %APPDATA%\PostMini\api_client.db
SELECT name, body_type FROM requests WHERE collection_id = (SELECT id FROM collections WHERE name = 'Your Collection Name');

# Expected output:
# Request 1 | raw
# Request 2 | formdata
# Request 3 | urlencoded
# Request 4 | graphql

# 4. Execute each request
# Verify they work correctly (can use httpbin.org for testing)

# 5. Export collection
# File → Export Collection → Save as new JSON

# 6. Check exported JSON includes body_type
# Open exported JSON, verify each request has "body_type" field

# 7. Re-import exported collection
# Verify body types still correct in database
```

### Test Endpoints (httpbin.org)

- **JSON**: `POST https://httpbin.org/post` - accepts any body format
- **Form-data**: `POST https://httpbin.org/post` - echoes back what you send
- **URL-encoded**: `POST https://httpbin.org/post` - echoes back what you send

## Step 4: UI Enhancement (Optional)

### Add Body Type Selector

**Location**: Request editor UI (below URL input, next to method dropdown)

**UI Component:**
```python
self.body_type_combo = QComboBox()
self.body_type_combo.addItems([
    "none",
    "form-data", 
    "x-www-form-urlencoded",
    "raw",
    "binary",
    "GraphQL"
])
self.body_type_combo.setCurrentText("raw")
```

**Signal Handler:**
```python
self.body_type_combo.currentTextChanged.connect(self.on_body_type_changed)

def on_body_type_changed(self, body_type):
    # Update body editor UI based on selection
    if body_type == "form-data":
        # Show key-value table
        self.body_editor.hide()
        self.form_data_table.show()
    elif body_type in ["raw", "GraphQL"]:
        # Show text editor
        self.form_data_table.hide()
        self.body_editor.show()
    # etc.
```

**Load/Save:**
```python
# When loading request
body_type = request.get('body_type', 'raw')
self.body_type_combo.setCurrentText(body_type)

# When saving request
body_type = self.body_type_combo.currentText()
self.db.update_request(..., body_type=body_type)
```

## Estimated Time

- **Step 1** (MainWindow): 2-3 hours
  - Find all call sites: 30 min
  - Update each call: 1.5 hours
  - Test: 1 hour

- **Step 2** (CollectionIO): 1 hour
  - Update exporter: 15 min
  - Update importer: 15 min
  - Test: 30 min

- **Step 3** (E2E Testing): 1 hour
  - Create Postman collection: 15 min
  - Import/verify: 15 min
  - Execute requests: 15 min
  - Export/reimport: 15 min

- **Step 4** (UI - Optional): 4-6 hours
  - Design UI: 1 hour
  - Implement: 2-3 hours
  - Test: 1-2 hours

**Total: 4-5 hours required, 8-11 hours with optional UI**

## Success Checklist

- [ ] All `create_request()` calls pass `body_type` parameter
- [ ] All `update_request()` calls pass `body_type` parameter
- [ ] CollectionExporter includes `body_type` in JSON
- [ ] CollectionImporter reads `body_type` from JSON
- [ ] End-to-end test: Import → Execute → Export → Reimport
- [ ] Body types preserved through entire cycle
- [ ] All existing tests still pass
- [ ] No regressions in request execution

## Commands for Next Developer

```powershell
# Find all places to update
grep -n "self.db.create_request" src/ui/main_window.py
grep -n "self.db.update_request" src/ui/main_window.py

# Test after changes
python -m pytest tests/test_body_types.py tests/test_form_urlencoded.py -v

# Check database after import
sqlite3 %APPDATA%\PostMini\api_client.db "SELECT name, body_type FROM requests LIMIT 10;"
```
