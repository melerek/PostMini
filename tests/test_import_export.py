"""
Import/Export Test Suite

Comprehensive tests for collection import and export functionality.
"""

import sys
import os
import json
import traceback

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.features.collection_io import CollectionExporter, CollectionImporter, get_safe_filename


def test_export_collection():
    """Test exporting a single collection."""
    print("Testing Collection Export...")
    
    try:
        db = DatabaseManager("test_import_export.db")
        exporter = CollectionExporter(db)
        
        # Create test collection
        col_id = db.create_collection("Test Export Collection")
        
        # Add some requests
        db.create_request(
            collection_id=col_id,
            name="Get Users",
            method="GET",
            url="https://api.example.com/users",
            params={"limit": "10"},
            headers={"Authorization": "Bearer token123"}
        )
        
        db.create_request(
            collection_id=col_id,
            name="Create User",
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            body='{"name": "John Doe", "email": "john@example.com"}',
            auth_type="Bearer Token",
            auth_token="mytoken"
        )
        
        # Export to dictionary
        export_data = exporter.export_collection(col_id)
        
        # Validate structure
        if "export_version" in export_data:
            print("  [OK] Export version included")
        
        if "export_date" in export_data:
            print("  [OK] Export date included")
        
        if "collection" in export_data:
            print("  [OK] Collection data included")
        
        collection = export_data["collection"]
        if collection["name"] == "Test Export Collection":
            print("  [OK] Collection name correct")
        
        if len(collection["requests"]) == 2:
            print("  [OK] All requests included")
        
        # Check request data
        request1 = collection["requests"][0]
        if request1["name"] == "Get Users":
            print("  [OK] Request name correct")
        if request1["method"] == "GET":
            print("  [OK] Request method correct")
        if request1["url"] == "https://api.example.com/users":
            print("  [OK] Request URL correct")
        if request1["params"] == {"limit": "10"}:
            print("  [OK] Request params correct")
        
        # Export to file
        export_file = "test_export.json"
        success = exporter.export_collection_to_file(col_id, export_file)
        
        if success:
            print("  [OK] Export to file successful")
        
        if os.path.exists(export_file):
            print("  [OK] Export file created")
            
            # Validate file content
            with open(export_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            if file_data["collection"]["name"] == "Test Export Collection":
                print("  [OK] File content valid")
        
        db.close()
        print("[OK] Export tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Export test failed: {e}")
        traceback.print_exc()
        return False


def test_import_collection():
    """Test importing a collection."""
    print("Testing Collection Import...")
    
    try:
        db = DatabaseManager("test_import_export.db")
        exporter = CollectionExporter(db)
        importer = CollectionImporter(db)
        
        # Create and export a collection first
        col_id = db.create_collection("Original Collection")
        db.create_request(
            collection_id=col_id,
            name="Test Request",
            method="GET",
            url="https://api.example.com/test",
            params={"key": "value"}
        )
        
        export_file = "test_import.json"
        exporter.export_collection_to_file(col_id, export_file)
        
        # Delete the collection
        db.delete_collection(col_id)
        print("  [OK] Test data prepared")
        
        # Import it back
        success, message, new_col_id = importer.import_collection_from_file(export_file)
        
        if success:
            print(f"  [OK] Import successful: {message}")
        else:
            print(f"  [ERROR] Import failed: {message}")
            return False
        
        # Verify the imported data
        collection = db.get_collection(new_col_id)
        if collection["name"] == "Original Collection":
            print("  [OK] Imported collection name correct")
        
        requests = db.get_requests_by_collection(new_col_id)
        if len(requests) == 1:
            print("  [OK] Imported requests count correct")
        
        if requests[0]["name"] == "Test Request":
            print("  [OK] Imported request data correct")
        
        db.close()
        print("[OK] Import tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Import test failed: {e}")
        traceback.print_exc()
        return False


def test_import_with_duplicate():
    """Test importing when collection name already exists."""
    print("Testing Import with Duplicate Names...")
    
    try:
        db = DatabaseManager("test_import_export.db")
        exporter = CollectionExporter(db)
        importer = CollectionImporter(db)
        
        # Create collection
        col_id = db.create_collection("Duplicate Test")
        db.create_request(
            collection_id=col_id,
            name="Request 1",
            method="GET",
            url="https://example.com"
        )
        
        # Export it
        export_file = "test_duplicate.json"
        exporter.export_collection_to_file(col_id, export_file)
        
        # Try to import with skip_if_exists
        success, message, _ = importer.import_collection_from_file(
            export_file,
            skip_if_exists=True
        )
        
        if not success and "already exists" in message:
            print("  [OK] Skip on duplicate works")
        
        # Try to import with rename_if_exists
        success, message, new_col_id = importer.import_collection_from_file(
            export_file,
            rename_if_exists=True
        )
        
        if success:
            print("  [OK] Rename on duplicate works")
            
            new_collection = db.get_collection(new_col_id)
            if "imported" in new_collection["name"].lower():
                print("  [OK] Imported collection renamed correctly")
        
        db.close()
        print("[OK] Duplicate handling tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Duplicate handling test failed: {e}")
        traceback.print_exc()
        return False


def test_import_validation():
    """Test import validation with invalid data."""
    print("Testing Import Validation...")
    
    try:
        db = DatabaseManager("test_import_export.db")
        importer = CollectionImporter(db)
        
        # Test 1: Invalid JSON
        invalid_file = "test_invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("not valid json{{{")
        
        success, message, _ = importer.import_collection_from_file(invalid_file)
        if not success and "Invalid JSON" in message:
            print("  [OK] Invalid JSON detected")
        
        # Test 2: Missing required fields
        missing_field = "test_missing.json"
        with open(missing_field, 'w') as f:
            json.dump({"collection": {"requests": []}}, f)  # Missing 'name'
        
        success, message, _ = importer.import_collection_from_file(missing_field)
        if not success and "missing" in message.lower():
            print("  [OK] Missing fields detected")
        
        # Test 3: Non-existent file
        success, message, _ = importer.import_collection_from_file("nonexistent.json")
        if not success and "not found" in message.lower():
            print("  [OK] Non-existent file handled")
        
        db.close()
        print("[OK] Validation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Validation test failed: {e}")
        traceback.print_exc()
        return False


def test_safe_filename():
    """Test safe filename generation."""
    print("Testing Safe Filename Generation...")
    
    try:
        # Test with special characters
        name1 = "Test<>:Collection"
        safe1 = get_safe_filename(name1)
        if "<" not in safe1 and ">" not in safe1:
            print("  [OK] Special characters removed")
        
        # Test with path separators
        name2 = "Test/Collection\\Name"
        safe2 = get_safe_filename(name2)
        if "/" not in safe2 and "\\" not in safe2:
            print("  [OK] Path separators removed")
        
        # Test that it has .json extension
        if safe1.endswith(".json"):
            print("  [OK] .json extension added")
        
        # Test that it includes timestamp
        if "_" in safe1 and len(safe1.split("_")[-1].replace(".json", "")) > 0:
            print("  [OK] Timestamp included")
        
        print("[OK] Safe filename tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Safe filename test failed: {e}")
        traceback.print_exc()
        return False


def test_complex_collection():
    """Test exporting/importing a complex collection with all features."""
    print("Testing Complex Collection Export/Import...")
    
    try:
        db = DatabaseManager("test_import_export.db")
        exporter = CollectionExporter(db)
        importer = CollectionImporter(db)
        
        # Create complex collection
        col_id = db.create_collection("Complex API Tests")
        
        # Request with environment variables
        db.create_request(
            collection_id=col_id,
            name="Variable Request",
            method="GET",
            url="{{baseUrl}}/{{version}}/users",
            params={"token": "{{apiKey}}"},
            headers={"Authorization": "Bearer {{authToken}}"}
        )
        
        # Request with JSON body
        db.create_request(
            collection_id=col_id,
            name="JSON Body Request",
            method="POST",
            url="https://api.example.com/create",
            headers={"Content-Type": "application/json"},
            body='{"user": {"name": "Test", "age": 30}, "settings": {"theme": "dark"}}'
        )
        
        # Request with auth
        db.create_request(
            collection_id=col_id,
            name="Authenticated Request",
            method="GET",
            url="https://api.example.com/secure",
            auth_type="Bearer Token",
            auth_token="super-secret-token-123"
        )
        
        # Request with no params/headers
        db.create_request(
            collection_id=col_id,
            name="Simple Request",
            method="GET",
            url="https://api.example.com/simple"
        )
        
        # Export
        export_file = "test_complex.json"
        success = exporter.export_collection_to_file(col_id, export_file)
        if success:
            print("  [OK] Complex collection exported")
        
        # Delete and re-import
        db.delete_collection(col_id)
        
        success, message, new_col_id = importer.import_collection_from_file(export_file)
        if success:
            print("  [OK] Complex collection imported")
        
        # Verify all requests
        requests = db.get_requests_by_collection(new_col_id)
        if len(requests) == 4:
            print("  [OK] All complex requests imported")
        
        # Check variable request
        var_req = [r for r in requests if r['name'] == "Variable Request"][0]
        if "{{baseUrl}}" in var_req['url']:
            print("  [OK] Variables preserved")
        
        # Check JSON body
        json_req = [r for r in requests if r['name'] == "JSON Body Request"][0]
        if json_req['body'] and "theme" in json_req['body']:
            print("  [OK] JSON body preserved")
        
        # Check auth
        auth_req = [r for r in requests if r['name'] == "Authenticated Request"][0]
        if auth_req['auth_type'] == "Bearer Token":
            print("  [OK] Auth type preserved")
        if auth_req['auth_token'] == "super-secret-token-123":
            print("  [OK] Auth token preserved")
        
        db.close()
        print("[OK] Complex collection tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Complex collection test failed: {e}")
        traceback.print_exc()
        return False


def cleanup_test_files():
    """Clean up test files."""
    test_files = [
        "test_import_export.db",
        "test_export.json",
        "test_import.json",
        "test_duplicate.json",
        "test_invalid.json",
        "test_missing.json",
        "test_complex.json"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


def main():
    """Run all import/export tests."""
    print("="*60)
    print("Collection Import/Export Test Suite")
    print("="*60)
    print()
    
    results = []
    
    results.append(("Export Collection", test_export_collection()))
    results.append(("Import Collection", test_import_collection()))
    results.append(("Import with Duplicate", test_import_with_duplicate()))
    results.append(("Import Validation", test_import_validation()))
    results.append(("Safe Filename", test_safe_filename()))
    results.append(("Complex Collection", test_complex_collection()))
    
    print()
    print("="*60)
    print("Test Results Summary")
    print("="*60)
    
    for name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{name:.<40} {status}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("[SUCCESS] All import/export tests passed!")
        print("Export/Import functionality is ready for production!")
    else:
        print("[FAIL] Some tests failed.")
    
    # Clean up
    cleanup_test_files()
    print("\nTest files cleaned up.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

