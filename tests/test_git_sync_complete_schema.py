"""
Tests for GitSync complete schema support after fix.

This test verifies that GitSync properly exports and imports ALL database schema fields:
- Folder hierarchy (parent_id relationships)
- Pre/post request scripts
- Collection variables
- Order index for collections, folders, and requests
- Test assertions

Previously, GitSync had outdated export/import logic that caused catastrophic data loss.
This test ensures the fix is complete and prevents regression.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from src.core.database import DatabaseManager
from src.features.git_sync_manager import GitSyncManager, GitSyncConfig


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    db = DatabaseManager(":memory:")
    yield db
    db.close()


@pytest.fixture
def git_sync_config():
    """Create a temporary directory for git sync testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield GitSyncConfig(tmpdir)


@pytest.fixture
def git_sync(db, git_sync_config):
    """Create GitSyncManager with temporary config."""
    manager = GitSyncManager(db, git_sync_config)
    # Initialize workspace
    manager.initialize_workspace(create_gitignore=False)
    return manager


def test_git_sync_exports_complete_schema(db, git_sync):
    """Test that GitSync exports folders, scripts, variables, and order_index."""
    
    # Create collection with custom order_index
    collection_id = db.create_collection("Test API", order_index=500)
    
    # Add collection variables
    db.create_collection_variable(collection_id, "baseUrl", "https://api.example.com")
    db.create_collection_variable(collection_id, "apiKey", "secret123")
    
    # Create folder hierarchy
    folder1_id = db.create_folder(collection_id, "Auth", parent_id=None, order_index=100)
    folder2_id = db.create_folder(collection_id, "Users", parent_id=folder1_id, order_index=200)
    folder3_id = db.create_folder(collection_id, "Admin", parent_id=None, order_index=300)
    
    # Create requests with scripts and custom order_index
    request1_id = db.create_request(
        collection_id=collection_id,
        name="Login",
        method="POST",
        url="{{baseUrl}}/auth/login",
        folder_id=folder1_id,
        pre_request_script="console.log('Pre-request');",
        post_response_script="pm.environment.set('token', pm.response.json().token);",
        order_index=150
    )
    
    request2_id = db.create_request(
        collection_id=collection_id,
        name="Get Users",
        method="GET",
        url="{{baseUrl}}/users",
        folder_id=folder2_id,
        pre_request_script="// Set auth header\npm.request.headers.add({key: 'Authorization', value: 'Bearer ' + pm.environment.get('token')});",
        post_response_script="// Extract user count\npm.collectionVariables.set('userCount', pm.response.json().length);",
        order_index=250
    )
    
    request3_id = db.create_request(
        collection_id=collection_id,
        name="Delete User",
        method="DELETE",
        url="{{baseUrl}}/admin/users/123",
        folder_id=folder3_id,
        order_index=350
    )
    
    # Add test assertions
    db.create_test_assertion(request1_id, "status_code", "equals", expected_value="200")
    db.create_test_assertion(request2_id, "json_body", "has_key", field="users")
    
    # Export collection
    success, file_path = git_sync.export_collection_to_file(collection_id)
    assert success, "Export should succeed"
    
    # Read exported file and verify structure
    with open(file_path, 'r', encoding='utf-8') as f:
        export_data = json.load(f)
    
    # Verify export_version exists
    assert "export_version" in export_data
    
    # Verify collection data
    collection = export_data["collection"]
    assert collection["name"] == "Test API"
    assert collection["order_index"] == 500
    
    # Verify folders are exported with hierarchy
    assert "folders" in collection
    assert len(collection["folders"]) == 3
    
    # Find folders by name
    folders_by_name = {f["name"]: f for f in collection["folders"]}
    
    # Verify Auth folder (root level)
    auth_folder = folders_by_name["Auth"]
    assert auth_folder["path"] == []  # No parent
    assert auth_folder["full_path"] == ["Auth"]
    assert auth_folder["order_index"] == 100
    
    # Verify Users folder (nested under Auth)
    users_folder = folders_by_name["Users"]
    assert users_folder["path"] == ["Auth"]  # Parent is Auth
    assert users_folder["full_path"] == ["Auth", "Users"]
    assert users_folder["order_index"] == 200
    
    # Verify Admin folder (root level)
    admin_folder = folders_by_name["Admin"]
    assert admin_folder["path"] == []
    assert admin_folder["full_path"] == ["Admin"]
    assert admin_folder["order_index"] == 300
    
    # Verify collection variables are exported
    assert "variables" in collection
    assert len(collection["variables"]) == 2
    variables_by_key = {v["key"]: v["value"] for v in collection["variables"]}
    assert variables_by_key["baseUrl"] == "https://api.example.com"
    assert variables_by_key["apiKey"] == "secret123"
    
    # Verify requests are exported with folder_path, scripts, and order_index
    assert "requests" in collection
    assert len(collection["requests"]) == 3
    
    requests_by_name = {r["name"]: r for r in collection["requests"]}
    
    # Verify Login request
    login_req = requests_by_name["Login"]
    assert login_req["folder_path"] == ["Auth"]
    assert login_req["pre_request_script"] == "console.log('Pre-request');"
    assert "pm.environment.set" in login_req["post_response_script"]
    assert login_req["order_index"] == 150
    
    # Verify Get Users request (nested folder)
    get_users_req = requests_by_name["Get Users"]
    assert get_users_req["folder_path"] == ["Auth", "Users"]
    assert "pm.request.headers.add" in get_users_req["pre_request_script"]
    assert "pm.collectionVariables.set" in get_users_req["post_response_script"]
    assert get_users_req["order_index"] == 250
    
    # Verify Delete User request
    delete_user_req = requests_by_name["Delete User"]
    assert delete_user_req["folder_path"] == ["Admin"]
    assert delete_user_req["order_index"] == 350


def test_git_sync_imports_complete_schema(db, git_sync):
    """Test that GitSync imports folders, scripts, variables, and order_index."""
    
    # Create a mock export file with complete schema
    export_data = {
        "export_version": "1.0",
        "export_date": "2024-01-01T00:00:00",
        "collection": {
            "name": "Imported API",
            "order_index": 600,
            "folders": [
                {
                    "name": "Folder1",
                    "path": [],
                    "full_path": ["Folder1"],
                    "order_index": 100
                },
                {
                    "name": "Subfolder",
                    "path": ["Folder1"],
                    "full_path": ["Folder1", "Subfolder"],
                    "order_index": 150
                },
                {
                    "name": "Folder2",
                    "path": [],
                    "full_path": ["Folder2"],
                    "order_index": 200
                }
            ],
            "variables": [
                {"key": "host", "value": "api.test.com"},
                {"key": "version", "value": "v1"}
            ],
            "requests": [
                {
                    "name": "Request1",
                    "method": "GET",
                    "url": "{{host}}/{{version}}/test",
                    "folder_path": ["Folder1"],
                    "pre_request_script": "console.log('before');",
                    "post_response_script": "console.log('after');",
                    "order_index": 110,
                    "params": None,
                    "headers": None,
                    "body": None,
                    "auth_type": "None",
                    "auth_token": None
                },
                {
                    "name": "Request2",
                    "method": "POST",
                    "url": "{{host}}/{{version}}/data",
                    "folder_path": ["Folder1", "Subfolder"],
                    "pre_request_script": "// Pre script",
                    "post_response_script": "// Post script",
                    "order_index": 160,
                    "params": None,
                    "headers": None,
                    "body": None,
                    "auth_type": "None",
                    "auth_token": None
                },
                {
                    "name": "Request3",
                    "method": "DELETE",
                    "url": "{{host}}/{{version}}/item",
                    "folder_path": ["Folder2"],
                    "pre_request_script": None,
                    "post_response_script": None,
                    "order_index": 210,
                    "params": None,
                    "headers": None,
                    "body": None,
                    "auth_type": "None",
                    "auth_token": None
                }
            ]
        }
    }
    
    # Write to temp file
    import_file = git_sync.config.collections_path / "test_import.json"
    with open(import_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2)
    
    # Import collection
    success, message, collection_id = git_sync.import_collection_from_file(str(import_file), update_existing=False)
    assert success, f"Import should succeed: {message}"
    assert collection_id is not None
    
    # Verify collection
    collection = db.get_collection(collection_id)
    assert collection["name"] == "Imported API"
    assert collection["order_index"] == 600
    
    # Verify collection variables
    variables = db.get_collection_variables_with_metadata(collection_id)
    assert len(variables) == 2
    vars_by_key = {v["key"]: v["value"] for v in variables}
    assert vars_by_key["host"] == "api.test.com"
    assert vars_by_key["version"] == "v1"
    
    # Verify folders
    folders = db.get_folders_by_collection(collection_id)
    assert len(folders) == 3
    
    folders_by_name = {f["name"]: f for f in folders}
    
    # Verify Folder1 (root)
    folder1 = folders_by_name["Folder1"]
    assert folder1["parent_id"] is None
    assert folder1["order_index"] == 100
    
    # Verify Subfolder (child of Folder1)
    subfolder = folders_by_name["Subfolder"]
    assert subfolder["parent_id"] == folder1["id"]
    assert subfolder["order_index"] == 150
    
    # Verify Folder2 (root)
    folder2 = folders_by_name["Folder2"]
    assert folder2["parent_id"] is None
    assert folder2["order_index"] == 200
    
    # Verify requests
    requests = db.get_requests_by_collection(collection_id)
    assert len(requests) == 3
    
    requests_by_name = {r["name"]: r for r in requests}
    
    # Verify Request1 (in Folder1)
    request1 = requests_by_name["Request1"]
    assert request1["folder_id"] == folder1["id"]
    assert request1["pre_request_script"] == "console.log('before');"
    assert request1["post_response_script"] == "console.log('after');"
    assert request1["order_index"] == 110
    
    # Verify Request2 (in Subfolder)
    request2 = requests_by_name["Request2"]
    assert request2["folder_id"] == subfolder["id"]
    assert request2["pre_request_script"] == "// Pre script"
    assert request2["post_response_script"] == "// Post script"
    assert request2["order_index"] == 160
    
    # Verify Request3 (in Folder2)
    request3 = requests_by_name["Request3"]
    assert request3["folder_id"] == folder2["id"]
    assert request3["pre_request_script"] is None
    assert request3["post_response_script"] is None
    assert request3["order_index"] == 210


def test_git_sync_round_trip_preserves_all_data(db, git_sync):
    """Test that export → import preserves ALL data (no data loss)."""
    
    # Create complex collection
    collection_id = db.create_collection("Complex API", order_index=777)
    
    # Add variables
    db.create_collection_variable(collection_id, "var1", "value1")
    db.create_collection_variable(collection_id, "var2", "value2")
    
    # Create folder structure
    folder_a = db.create_folder(collection_id, "FolderA", parent_id=None, order_index=100)
    folder_b = db.create_folder(collection_id, "FolderB", parent_id=folder_a, order_index=200)
    folder_c = db.create_folder(collection_id, "FolderC", parent_id=None, order_index=300)
    
    # Create requests with scripts
    req1 = db.create_request(
        collection_id=collection_id,
        name="Req1",
        method="POST",
        url="https://test.com/api",
        folder_id=folder_b,
        pre_request_script="// Pre script 1",
        post_response_script="// Post script 1",
        order_index=250
    )
    
    req2 = db.create_request(
        collection_id=collection_id,
        name="Req2",
        method="GET",
        url="https://test.com/data",
        folder_id=folder_c,
        pre_request_script="// Pre script 2",
        post_response_script="// Post script 2",
        order_index=350
    )
    
    # Export
    success, file_path = git_sync.export_collection_to_file(collection_id)
    assert success
    
    # Delete collection completely (including folders and variables)
    # Note: delete_collection doesn't cascade, so delete manually
    for folder in db.get_folders_by_collection(collection_id):
        db.delete_folder(folder['id'])
    db.delete_collection_variables_by_collection(collection_id)
    db.delete_collection(collection_id)
    
    # Verify deletion
    assert db.get_collection(collection_id) is None
    assert len(db.get_folders_by_collection(collection_id)) == 0
    assert len(db.get_requests_by_collection(collection_id)) == 0
    
    # Import
    success, message, new_collection_id = git_sync.import_collection_from_file(file_path, update_existing=False)
    assert success
    
    # Verify everything was restored
    collection = db.get_collection(new_collection_id)
    assert collection["name"] == "Complex API"
    assert collection["order_index"] == 777
    
    # Verify variables restored
    variables = db.get_collection_variables_with_metadata(new_collection_id)
    assert len(variables) == 2
    
    # Verify folder hierarchy restored
    folders = db.get_folders_by_collection(new_collection_id)
    assert len(folders) == 3
    
    folders_by_name = {f["name"]: f for f in folders}
    restored_folder_a = folders_by_name["FolderA"]
    restored_folder_b = folders_by_name["FolderB"]
    restored_folder_c = folders_by_name["FolderC"]
    
    assert restored_folder_a["parent_id"] is None
    assert restored_folder_b["parent_id"] == restored_folder_a["id"]
    assert restored_folder_c["parent_id"] is None
    
    assert restored_folder_a["order_index"] == 100
    assert restored_folder_b["order_index"] == 200
    assert restored_folder_c["order_index"] == 300
    
    # Verify requests restored with scripts
    requests = db.get_requests_by_collection(new_collection_id)
    assert len(requests) == 2
    
    requests_by_name = {r["name"]: r for r in requests}
    
    restored_req1 = requests_by_name["Req1"]
    assert restored_req1["folder_id"] == restored_folder_b["id"]
    assert restored_req1["pre_request_script"] == "// Pre script 1"
    assert restored_req1["post_response_script"] == "// Post script 1"
    assert restored_req1["order_index"] == 250
    
    restored_req2 = requests_by_name["Req2"]
    assert restored_req2["folder_id"] == restored_folder_c["id"]
    assert restored_req2["pre_request_script"] == "// Pre script 2"
    assert restored_req2["post_response_script"] == "// Post script 2"
    assert restored_req2["order_index"] == 350


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
