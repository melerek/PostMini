"""
Test Postman Collection Format v2.1 Compatibility
"""
import sys
import os
import json
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.features.collection_io import CollectionExporter, CollectionImporter
from src.features.postman_converter import PostmanConverter


def test_postman_export():
    """Test exporting to Postman format."""
    print("Testing Postman Export...")
    
    # Create test database
    db = DatabaseManager(":memory:")
    
    # Create a collection with requests
    collection_id = db.create_collection("Test API")
    
    # Add various request types
    db.create_request(
        collection_id=collection_id,
        name="Get Users",
        method="GET",
        url="https://api.example.com/users",
        params={"page": "1", "limit": "10"},
        headers={"Accept": "application/json"},
        body=None,
        auth_type="Bearer Token",
        auth_token="test_token_123"
    )
    
    db.create_request(
        collection_id=collection_id,
        name="Create User",
        method="POST",
        url="https://api.example.com/users",
        params=None,
        headers={"Content-Type": "application/json"},
        body='{"name": "John Doe", "email": "john@example.com"}',
        auth_type="None",
        auth_token=None
    )
    
    # Export to Postman format
    exporter = CollectionExporter(db)
    export_data = exporter.export_collection(collection_id)
    postman_data = PostmanConverter.to_postman_format(export_data)
    
    # Verify Postman structure
    assert "info" in postman_data, "Missing 'info' field"
    assert "item" in postman_data, "Missing 'item' field"
    assert postman_data["info"]["schema"] == PostmanConverter.POSTMAN_SCHEMA
    assert len(postman_data["item"]) == 2, f"Expected 2 items, got {len(postman_data['item'])}"
    
    # Find requests by name (order may vary)
    requests_by_name = {item["name"]: item for item in postman_data["item"]}
    
    # Verify GET request with auth
    assert "Get Users" in requests_by_name, "Missing 'Get Users' request"
    get_request = requests_by_name["Get Users"]
    assert get_request["request"]["method"] == "GET"
    assert "auth" in get_request["request"], "Missing auth field"
    assert get_request["request"]["auth"]["type"] == "bearer"
    
    # Verify URL structure
    url = get_request["request"]["url"]
    assert url["protocol"] == "https"
    assert "query" in url
    assert len(url["query"]) == 2
    
    # Verify POST request with body
    assert "Create User" in requests_by_name, "Missing 'Create User' request"
    post_request = requests_by_name["Create User"]
    assert post_request["request"]["method"] == "POST"
    assert "body" in post_request["request"]
    assert post_request["request"]["body"]["mode"] == "raw"
    
    print("  [OK] Postman export structure correct")
    print(f"  [OK] Exported {len(postman_data['item'])} requests")
    print(f"  [OK] Schema: {postman_data['info']['schema']}")
    return True


def test_postman_import():
    """Test importing from Postman format."""
    print("\nTesting Postman Import...")
    
    # Create sample Postman collection
    postman_collection = {
        "info": {
            "_postman_id": "12345-67890",
            "name": "Sample API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Get Posts",
                "request": {
                    "method": "GET",
                    "header": [
                        {
                            "key": "Accept",
                            "value": "application/json",
                            "type": "text"
                        }
                    ],
                    "url": {
                        "raw": "https://jsonplaceholder.typicode.com/posts?userId=1",
                        "protocol": "https",
                        "host": ["jsonplaceholder", "typicode", "com"],
                        "path": ["posts"],
                        "query": [
                            {
                                "key": "userId",
                                "value": "1"
                            }
                        ]
                    }
                },
                "response": []
            }
        ]
    }
    
    # Convert to internal format
    internal_data = PostmanConverter.from_postman_format(postman_collection)
    
    # Verify conversion
    assert "collection" in internal_data
    assert internal_data["collection"]["name"] == "Sample API"
    assert "requests" in internal_data["collection"]
    assert len(internal_data["collection"]["requests"]) == 1
    
    request = internal_data["collection"]["requests"][0]
    assert request["name"] == "Get Posts"
    assert request["method"] == "GET"
    assert request["url"] == "https://jsonplaceholder.typicode.com/posts?userId=1"
    assert request["headers"] == {"Accept": "application/json"}
    assert request["params"] == {"userId": "1"}
    
    print("  [OK] Postman import structure correct")
    print(f"  [OK] Imported {len(internal_data['collection']['requests'])} requests")
    print(f"  [OK] Collection name: {internal_data['collection']['name']}")
    return True


def test_format_detection():
    """Test automatic format detection."""
    print("\nTesting Format Detection...")
    
    # Postman format
    postman_data = {
        "info": {"_postman_id": "123", "name": "Test"},
        "item": []
    }
    assert PostmanConverter.is_postman_format(postman_data) == True
    print("  [OK] Postman format detected correctly")
    
    # Internal format
    internal_data = {
        "export_version": "1.0",
        "collection": {"name": "Test", "requests": []}
    }
    assert PostmanConverter.is_postman_format(internal_data) == False
    print("  [OK] Internal format detected correctly")
    
    return True


def test_roundtrip_conversion():
    """Test converting from internal to Postman and back."""
    print("\nTesting Roundtrip Conversion...")
    
    # Create test database
    db = DatabaseManager(":memory:")
    collection_id = db.create_collection("Roundtrip Test")
    
    db.create_request(
        collection_id=collection_id,
        name="Test Request",
        method="POST",
        url="https://api.test.com/data",
        params={"key": "value"},
        headers={"X-API-Key": "secret"},
        body='{"test": "data"}',
        auth_type="Bearer Token",
        auth_token="token123"
    )
    
    # Export to internal format
    exporter = CollectionExporter(db)
    internal_data = exporter.export_collection(collection_id)
    
    # Convert to Postman
    postman_data = PostmanConverter.to_postman_format(internal_data)
    
    # Convert back to internal
    converted_internal = PostmanConverter.from_postman_format(postman_data)
    
    # Verify data integrity
    original_request = internal_data["collection"]["requests"][0]
    converted_request = converted_internal["collection"]["requests"][0]
    
    assert converted_request["name"] == original_request["name"]
    assert converted_request["method"] == original_request["method"]
    assert converted_request["body"] == original_request["body"]
    
    print("  [OK] Roundtrip conversion maintains data integrity")
    return True


def test_file_export_import():
    """Test full export/import cycle with files."""
    print("\nTesting File Export/Import...")
    
    # Create test database and collection
    db = DatabaseManager(":memory:")
    collection_id = db.create_collection("File Test Collection")
    
    db.create_request(
        collection_id=collection_id,
        name="GET Request",
        method="GET",
        url="https://httpbin.org/get",
        params=None,
        headers=None,
        body=None,
        auth_type="None",
        auth_token=None
    )
    
    # Export to Postman format
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        exporter = CollectionExporter(db)
        success = exporter.export_collection_to_file(collection_id, temp_file, format='postman')
        assert success, "Export failed"
        print(f"  [OK] Exported to: {temp_file}")
        
        # Verify file is valid Postman format
        with open(temp_file, 'r') as f:
            data = json.load(f)
        
        assert PostmanConverter.is_postman_format(data), "Exported file is not Postman format"
        print("  [OK] Exported file is valid Postman format")
        
        # Import back
        db2 = DatabaseManager(":memory:")
        importer = CollectionImporter(db2)
        success, message, new_id = importer.import_collection_from_file(temp_file)
        
        assert success, f"Import failed: {message}"
        print(f"  [OK] Imported successfully: {message}")
        
        # Verify imported data
        requests = db2.get_requests_by_collection(new_id)
        assert len(requests) == 1
        assert requests[0]["name"] == "GET Request"
        print("  [OK] Imported data matches original")
        
        return True
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_deeply_nested_postman_import():
    """Test importing Postman collections with deeply nested folders (3+ levels)."""
    print("Testing Deeply Nested Postman Import...")
    
    # Create a Postman collection with 3 levels of folder nesting
    postman_data = {
        "info": {
            "_postman_id": "test-nested-123",
            "name": "Deeply Nested Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Level1",
                "item": [
                    {
                        "name": "Level2",
                        "item": [
                            {
                                "name": "Level3",
                                "item": [
                                    {
                                        "name": "Deep Request 1",
                                        "request": {
                                            "method": "GET",
                                            "header": [],
                                            "url": "https://api.example.com/deep/endpoint1"
                                        }
                                    },
                                    {
                                        "name": "Deep Request 2",
                                        "request": {
                                            "method": "POST",
                                            "header": [
                                                {
                                                    "key": "Content-Type",
                                                    "value": "application/json"
                                                }
                                            ],
                                            "body": {
                                                "mode": "raw",
                                                "raw": '{"test": "data"}'
                                            },
                                            "url": "https://api.example.com/deep/endpoint2"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "Level2b",
                        "item": [
                            {
                                "name": "Another Deep Request",
                                "request": {
                                    "method": "DELETE",
                                    "header": [],
                                    "url": "https://api.example.com/resource/123"
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Convert to internal format
    internal_format = PostmanConverter.from_postman_format(postman_data)
    
    # Verify conversion
    folders = internal_format['collection']['folders']
    requests = internal_format['collection']['requests']
    
    print(f"  [OK] Found {len(folders)} folders in nested structure")
    print(f"  [OK] Found {len(requests)} requests in nested structure")
    
    # Should have 4 folders total (Level1, Level2, Level3, Level2b)
    assert len(folders) == 4, f"Expected 4 folders, got {len(folders)}"
    print("  [OK] Correct number of folders extracted")
    
    # Should have 3 requests total
    assert len(requests) == 3, f"Expected 3 requests, got {len(requests)}"
    print("  [OK] Correct number of requests imported")
    
    # Check that folders are extracted correctly
    expected_folders = [
        {'name': 'Level1', 'depth': 0},
        {'name': 'Level2', 'depth': 1},
        {'name': 'Level3', 'depth': 2},
        {'name': 'Level2b', 'depth': 1},
    ]
    
    for expected in expected_folders:
        found = any(
            f['name'] == expected['name'] and len(f['path']) == expected['depth']
            for f in folders
        )
        assert found, f"Folder '{expected['name']}' at depth {expected['depth']} not found"
    
    print("  [OK] All folders extracted correctly")
    
    # Check that request names are clean (no folder prefix)
    expected_request_names = ["Deep Request 1", "Deep Request 2", "Another Deep Request"]
    for expected_name in expected_request_names:
        found = any(req['name'] == expected_name for req in requests)
        assert found, f"Request '{expected_name}' not found in imported requests"
    
    print("  [OK] Request names are clean (no folder concatenation)")
    
    # Check that requests have folder_path information
    for req in requests:
        assert 'folder_path' in req, f"Request '{req['name']}' missing folder_path"
        assert isinstance(req['folder_path'], list), f"folder_path should be a list"
    
    print("  [OK] All requests have folder_path information")
    
    # Verify request details
    request1 = next(r for r in requests if "Deep Request 1" in r['name'])
    assert request1['method'] == "GET"
    assert request1['url'] == "https://api.example.com/deep/endpoint1"
    assert request1['folder_path'] == ['Level1', 'Level2', 'Level3']
    print("  [OK] Request details and folder paths preserved correctly")
    
    # Test with database import
    db = DatabaseManager(":memory:")
    importer = CollectionImporter(db)
    success, message, collection_id = importer.import_collection(internal_format)
    
    assert success, f"Database import failed: {message}"
    print(f"  [OK] Successfully imported to database: {message}")
    
    # Verify folders in database
    db_folders = db.get_folders_by_collection(collection_id)
    assert len(db_folders) == 4, f"Expected 4 folders in DB, got {len(db_folders)}"
    print("  [OK] All folders created in database")
    
    # Verify in database
    db_requests = db.get_requests_by_collection(collection_id)
    assert len(db_requests) == 3
    
    # Check that all requests are linked to folders
    requests_with_folders = sum(1 for r in db_requests if r['folder_id'] is not None)
    assert requests_with_folders == 3, f"Expected all 3 requests in folders, got {requests_with_folders}"
    print("  [OK] All requests linked to folders in database")
    
    return True


def main():
    print("=" * 60)
    print("Postman Collection Format v2.1 Compatibility Tests")
    print("=" * 60)
    
    try:
        results = []
        
        results.append(("Export to Postman", test_postman_export()))
        results.append(("Import from Postman", test_postman_import()))
        results.append(("Format Detection", test_format_detection()))
        results.append(("Roundtrip Conversion", test_roundtrip_conversion()))
        results.append(("File Export/Import", test_file_export_import()))
        results.append(("Deeply Nested Import", test_deeply_nested_postman_import()))
        
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        
        all_passed = all(result for _, result in results)
        
        for name, passed in results:
            status = "[PASSED]" if passed else "[FAILED]"
            print(f"{name:.<40} {status}")
        
        if all_passed:
            print("\n[SUCCESS] All Postman compatibility tests passed!")
            print("\nFeatures verified:")
            print("  - Export to Postman Collection v2.1 format")
            print("  - Import from Postman Collection v2.1 format")
            print("  - Automatic format detection")
            print("  - Data integrity in roundtrip conversion")
            print("  - File-based export/import")
            print("  - Deeply nested folder structures (3+ levels)")
            return 0
        else:
            print("\n[FAILED] Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

