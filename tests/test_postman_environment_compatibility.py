"""
Unit Tests for Postman Environment Compatibility

Tests the import/export functionality for Postman environment format.
"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import DatabaseManager
from src.features.postman_environment_converter import PostmanEnvironmentConverter
from src.features.environment_io import EnvironmentExporter, EnvironmentImporter


def test_postman_format_detection():
    """Test detecting Postman environment format."""
    print("\nTesting Postman Format Detection...")
    
    # Postman format
    postman_data = {
        "id": "test-123",
        "name": "Test Environment",
        "values": [
            {"key": "baseUrl", "value": "https://api.example.com", "enabled": True, "type": "default"}
        ],
        "_postman_variable_scope": "environment"
    }
    
    # Internal format
    internal_data = {
        "export_version": "1.0",
        "environment": {
            "name": "Test",
            "variables": {"baseUrl": "https://api.example.com"}
        }
    }
    
    assert PostmanEnvironmentConverter.is_postman_format(postman_data) == True
    assert PostmanEnvironmentConverter.is_postman_format(internal_data) == False
    print("  [OK] Format detection works correctly")
    
    return True


def test_export_to_postman():
    """Test exporting to Postman format."""
    print("\nTesting Export to Postman Format...")
    
    # Create test database
    db = DatabaseManager(":memory:")
    env_id = db.create_environment("Production", {
        "baseUrl": "https://api.example.com",
        "apiKey": "secret123",
        "timeout": "5000"
    })
    
    # Export
    exporter = EnvironmentExporter(db)
    export_data = exporter.export_environment(env_id, format='postman')
    
    # Verify structure
    assert "_postman_variable_scope" in export_data
    assert export_data["_postman_variable_scope"] == "environment"
    assert export_data["name"] == "Production"
    assert "values" in export_data
    assert isinstance(export_data["values"], list)
    assert len(export_data["values"]) == 3
    
    # Check variables
    values_by_key = {v["key"]: v for v in export_data["values"]}
    assert "baseUrl" in values_by_key
    assert values_by_key["baseUrl"]["value"] == "https://api.example.com"
    assert values_by_key["baseUrl"]["enabled"] == True
    assert values_by_key["baseUrl"]["type"] == "default"
    
    # Check secret detection
    assert "apiKey" in values_by_key
    assert values_by_key["apiKey"]["type"] == "secret"
    
    print("  [OK] Export to Postman format successful")
    print(f"  [OK] Exported 3 variables")
    print(f"  [OK] Secret variable detected: apiKey")
    
    return True


def test_import_from_postman():
    """Test importing from Postman format."""
    print("\nTesting Import from Postman Format...")
    
    # Postman environment data
    postman_data = {
        "id": "abc123",
        "name": "Staging Environment",
        "values": [
            {"key": "baseUrl", "value": "https://staging.api.com", "enabled": True, "type": "default"},
            {"key": "apiToken", "value": "token456", "enabled": True, "type": "secret"},
            {"key": "debugMode", "value": "true", "enabled": False, "type": "default"}
        ],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": "2025-11-12T10:00:00.000Z",
        "_postman_exported_using": "Postman/10.0"
    }
    
    # Create test database and import
    db = DatabaseManager(":memory:")
    importer = EnvironmentImporter(db)
    success, message, env_id = importer.import_environment(postman_data)
    
    assert success == True
    assert env_id is not None
    print(f"  [OK] Import successful: {message}")
    
    # Verify imported data
    env = db.get_environment(env_id)
    assert env is not None
    assert env["name"] == "Staging Environment"
    
    variables = env.get("variables", {})
    assert "baseUrl" in variables
    assert variables["baseUrl"] == "https://staging.api.com"
    assert "apiToken" in variables
    assert variables["apiToken"] == "token456"
    
    # Disabled variables should have prefix
    assert "_DISABLED_debugMode" in variables
    assert variables["_DISABLED_debugMode"] == "true"
    
    print("  [OK] All variables imported correctly")
    print("  [OK] Disabled variables handled with prefix")
    
    return True


def test_roundtrip_conversion():
    """Test converting internal -> Postman -> internal."""
    print("\nTesting Roundtrip Conversion...")
    
    # Create test environment
    db = DatabaseManager(":memory:")
    original_vars = {
        "baseUrl": "https://api.example.com",
        "apiKey": "secret123",
        "version": "v2"
    }
    env_id = db.create_environment("Test Environment", original_vars)
    
    # Export to Postman
    exporter = EnvironmentExporter(db)
    postman_data = exporter.export_environment(env_id, format='postman')
    
    # Import back
    db2 = DatabaseManager(":memory:")
    importer = EnvironmentImporter(db2)
    success, message, new_env_id = importer.import_environment(postman_data)
    
    assert success == True
    print(f"  [OK] Roundtrip successful: {message}")
    
    # Verify data integrity
    new_env = db2.get_environment(new_env_id)
    assert new_env["name"] == "Test Environment"
    
    new_vars = new_env.get("variables", {})
    assert new_vars["baseUrl"] == original_vars["baseUrl"]
    assert new_vars["apiKey"] == original_vars["apiKey"]
    assert new_vars["version"] == original_vars["version"]
    
    print("  [OK] All variables preserved correctly")
    
    return True


def test_file_export_import():
    """Test full export/import cycle with files."""
    print("\nTesting File Export/Import...")
    
    # Create test environment
    db = DatabaseManager(":memory:")
    env_id = db.create_environment("Development", {
        "apiUrl": "http://localhost:3000",
        "authToken": "dev-token-123"
    })
    
    # Export to file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        exporter = EnvironmentExporter(db)
        success = exporter.export_environment_to_file(env_id, temp_file, format='postman')
        assert success == True
        print(f"  [OK] Exported to: {temp_file}")
        
        # Verify file is valid Postman format
        with open(temp_file, 'r') as f:
            data = json.load(f)
        
        assert PostmanEnvironmentConverter.is_postman_format(data) == True
        print("  [OK] Exported file is valid Postman format")
        
        # Import back
        db2 = DatabaseManager(":memory:")
        importer = EnvironmentImporter(db2)
        success, message, new_id = importer.import_environment_from_file(temp_file)
        
        assert success == True
        print(f"  [OK] Imported successfully: {message}")
        
        # Verify imported data
        env = db2.get_environment(new_id)
        assert env["name"] == "Development"
        variables = env.get("variables", {})
        assert variables["apiUrl"] == "http://localhost:3000"
        assert variables["authToken"] == "dev-token-123"
        
        print("  [OK] Data integrity maintained")
        
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    return True


def test_secret_handling():
    """Test secret variable handling."""
    print("\nTesting Secret Variable Handling...")
    
    # Create environment with secrets
    db = DatabaseManager(":memory:")
    env_id = db.create_environment("Production", {
        "baseUrl": "https://api.example.com",
        "apiKey": "secret123",
        "secretToken": "very-secret",
        "password": "pass123",
        "normalVar": "normal-value"
    })
    
    # Export with secrets
    exporter = EnvironmentExporter(db)
    data_with_secrets = exporter.export_environment(env_id, format='postman', include_secrets=True)
    
    values_with = {v["key"]: v for v in data_with_secrets["values"]}
    assert values_with["apiKey"]["value"] == "secret123"
    assert values_with["apiKey"]["type"] == "secret"
    print("  [OK] Secrets included when requested")
    
    # Export without secrets
    data_without_secrets = exporter.export_environment(env_id, format='postman', include_secrets=False)
    
    values_without = {v["key"]: v for v in data_without_secrets["values"]}
    assert "{{SECRET_apiKey}}" in values_without["apiKey"]["value"]
    assert values_without["apiKey"]["type"] == "secret"
    assert values_without["normalVar"]["value"] == "normal-value"
    print("  [OK] Secrets replaced with placeholders when requested")
    
    # Verify all secret keywords are detected
    secret_keys = [k for k, v in values_with.items() if v["type"] == "secret"]
    assert "apiKey" in secret_keys
    assert "secretToken" in secret_keys
    assert "password" in secret_keys
    assert "normalVar" not in secret_keys
    print(f"  [OK] Secret detection working: {len(secret_keys)} secrets detected")
    
    return True


def test_validation():
    """Test Postman environment validation."""
    print("\nTesting Postman Environment Validation...")
    
    # Valid environment
    valid_env = {
        "id": "test",
        "name": "Test",
        "values": [
            {"key": "var1", "value": "val1"}
        ],
        "_postman_variable_scope": "environment"
    }
    
    is_valid, msg = PostmanEnvironmentConverter.validate_postman_environment(valid_env)
    assert is_valid == True
    print("  [OK] Valid environment passes validation")
    
    # Invalid: missing _postman_variable_scope
    invalid_env1 = {
        "name": "Test",
        "values": []
    }
    is_valid, msg = PostmanEnvironmentConverter.validate_postman_environment(invalid_env1)
    assert is_valid == False
    assert "postman_variable_scope" in msg.lower()
    print("  [OK] Missing scope field detected")
    
    # Invalid: missing name
    invalid_env2 = {
        "values": [],
        "_postman_variable_scope": "environment"
    }
    is_valid, msg = PostmanEnvironmentConverter.validate_postman_environment(invalid_env2)
    assert is_valid == False
    assert "name" in msg.lower()
    print("  [OK] Missing name field detected")
    
    # Invalid: values not an array
    invalid_env3 = {
        "name": "Test",
        "values": "not-an-array",
        "_postman_variable_scope": "environment"
    }
    is_valid, msg = PostmanEnvironmentConverter.validate_postman_environment(invalid_env3)
    assert is_valid == False
    assert "array" in msg.lower()
    print("  [OK] Invalid values type detected")
    
    return True


def test_bulk_operations():
    """Test bulk import/export operations."""
    print("\nTesting Bulk Import/Export...")
    
    # Create multiple environments
    db = DatabaseManager(":memory:")
    env1_id = db.create_environment("Dev", {"url": "http://localhost"})
    env2_id = db.create_environment("Staging", {"url": "https://staging.com"})
    env3_id = db.create_environment("Production", {"url": "https://api.com"})
    
    # Export all to directory
    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = EnvironmentExporter(db)
        success_count, total = exporter.export_all_environments_to_directory(
            temp_dir, 
            format='postman'
        )
        
        assert success_count == 3
        assert total == 3
        print(f"  [OK] Exported {success_count}/{total} environments")
        
        # Verify files exist
        files = list(Path(temp_dir).glob("*.json"))
        assert len(files) == 3
        print(f"  [OK] Created {len(files)} files")
        
        # Import all from directory
        db2 = DatabaseManager(":memory:")
        importer = EnvironmentImporter(db2)
        success_count, total, messages = importer.import_environments_from_directory(temp_dir)
        
        assert success_count == 3
        assert total == 3
        print(f"  [OK] Imported {success_count}/{total} environments")
        
        # Verify imported environments
        all_envs = db2.get_all_environments()
        assert len(all_envs) == 3
        env_names = [e["name"] for e in all_envs]
        assert "Dev" in env_names
        assert "Staging" in env_names
        assert "Production" in env_names
        print("  [OK] All environments imported correctly")
    
    return True


def test_duplicate_name_handling():
    """Test handling of duplicate environment names."""
    print("\nTesting Duplicate Name Handling...")
    
    db = DatabaseManager(":memory:")
    
    # Create existing environment
    existing_id = db.create_environment("Test", {"var1": "value1"})
    
    # Try to import with same name
    postman_data = {
        "name": "Test",
        "values": [{"key": "var2", "value": "value2"}],
        "_postman_variable_scope": "environment"
    }
    
    importer = EnvironmentImporter(db)
    
    # Without update_existing - should create with new name
    success, message, new_id = importer.import_environment(postman_data, update_existing=False)
    assert success == True
    assert new_id != existing_id
    assert "Test (1)" in message or "conflict" in message.lower()
    print("  [OK] Duplicate name handled with rename")
    
    # With update_existing - should update
    success, message, updated_id = importer.import_environment(postman_data, update_existing=True)
    assert success == True
    assert updated_id == existing_id
    assert "Updated" in message
    print("  [OK] Duplicate name handled with update")
    
    # Verify update
    env = db.get_environment(existing_id)
    assert "var2" in env.get("variables", {})
    print("  [OK] Environment updated correctly")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("POSTMAN ENVIRONMENT COMPATIBILITY TESTS")
    print("=" * 60)
    
    tests = [
        test_postman_format_detection,
        test_export_to_postman,
        test_import_from_postman,
        test_roundtrip_conversion,
        test_file_export_import,
        test_secret_handling,
        test_validation,
        test_bulk_operations,
        test_duplicate_name_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  [FAIL] {test.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  [ERROR] {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
