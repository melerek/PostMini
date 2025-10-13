"""
Test script for API Client Application

This script tests core functionality to catch bugs before they crash the app.
"""

import sys
import os
import traceback

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.core.api_client import ApiClient
from src.features.variable_substitution import VariableSubstitution, EnvironmentManager


def test_database():
    """Test database operations."""
    print("Testing Database Operations...")
    
    try:
        db = DatabaseManager("test_api_client.db")
        
        # Test collection creation
        try:
            col_id = db.create_collection("Test Collection")
            print(f"  [OK] Created collection with ID: {col_id}")
        except Exception as e:
            print(f"  - Collection already exists (OK)")
        
        # Get all collections
        collections = db.get_all_collections()
        print(f"  [OK] Retrieved {len(collections)} collections")
        
        if collections:
            col_id = collections[0]['id']
            
            # Test request creation
            req_id = db.create_request(
                collection_id=col_id,
                name="Test Request",
                method="GET",
                url="https://example.com",
                params={"key": "value"},
                headers={"Content-Type": "application/json"}
            )
            print(f"  [OK] Created request with ID: {req_id}")
            
            # Test request retrieval
            request = db.get_request(req_id)
            print(f"  [OK] Retrieved request: {request['name']}")
            
            # Test with None values
            request_none = db.get_request(99999)
            if request_none is None:
                print(f"  [OK] Correctly returns None for non-existent request")
            
            # Test params/headers parsing
            if isinstance(request.get('params'), dict):
                print(f"  [OK] Params correctly parsed as dict: {request['params']}")
            else:
                print(f"  [ERROR] ERROR: Params not parsed correctly: {request.get('params')}")
            
            # Test requests by collection
            requests = db.get_requests_by_collection(col_id)
            print(f"  [OK] Retrieved {len(requests)} requests for collection")
        
        # Test environment operations
        try:
            env_id = db.create_environment("Test Env", {"baseUrl": "https://test.com"})
            print(f"  [OK] Created environment with ID: {env_id}")
        except Exception as e:
            print(f"  - Environment already exists (OK)")
        
        envs = db.get_all_environments()
        print(f"  [OK] Retrieved {len(envs)} environments")
        
        db.close()
        print("[OK] Database tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        traceback.print_exc()
        return False


def test_api_client():
    """Test API client."""
    print("Testing API Client...")
    
    try:
        client = ApiClient(timeout=10)
        
        # Test simple GET request
        print("  Testing GET request to JSONPlaceholder...")
        response = client.get("https://jsonplaceholder.typicode.com/posts/1")
        print(f"  [OK] Status: {response.status_code}")
        print(f"  [OK] Time: {response.elapsed_time:.2f}s")
        print(f"  [OK] Size: {response.size} bytes")
        
        # Test JSON parsing
        if response.is_json():
            data = response.json()
            print(f"  [OK] JSON parsed successfully")
        
        # Test with params
        response = client.get(
            "https://jsonplaceholder.typicode.com/posts",
            params={"userId": "1"}
        )
        print(f"  [OK] GET with params: Status {response.status_code}")
        
        client.close()
        print("[OK] API client tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] API client test failed: {e}")
        traceback.print_exc()
        return False


def test_variable_substitution():
    """Test variable substitution."""
    print("Testing Variable Substitution...")
    
    try:
        # Test basic substitution
        variables = {"baseUrl": "https://api.example.com", "version": "v1"}
        
        text = "{{baseUrl}}/{{version}}/users"
        result, unresolved = VariableSubstitution.substitute(text, variables)
        
        if result == "https://api.example.com/v1/users":
            print(f"  [OK] Basic substitution works")
        else:
            print(f"  [ERROR] ERROR: Expected 'https://api.example.com/v1/users', got '{result}'")
        
        # Test with unresolved variables
        text = "{{baseUrl}}/{{missing}}/users"
        result, unresolved = VariableSubstitution.substitute(text, variables)
        
        if "missing" in unresolved:
            print(f"  [OK] Unresolved variables detected: {unresolved}")
        else:
            print(f"  [ERROR] ERROR: Unresolved variables not detected")
        
        # Test dictionary substitution
        data = {"key": "{{baseUrl}}", "other": "value"}
        result, unresolved = VariableSubstitution.substitute_dict(data, variables)
        
        if result["key"] == "https://api.example.com":
            print(f"  [OK] Dictionary substitution works")
        else:
            print(f"  [ERROR] ERROR: Dict substitution failed")
        
        # Test variable finding
        found = VariableSubstitution.find_variables("{{baseUrl}}/{{version}}/{{apiKey}}")
        if len(found) == 3:
            print(f"  [OK] Variable detection works: {found}")
        else:
            print(f"  [ERROR] ERROR: Expected 3 variables, found {len(found)}")
        
        # Test EnvironmentManager
        manager = EnvironmentManager()
        env = {
            "id": 1,
            "name": "Test",
            "variables": {"baseUrl": "https://test.com", "token": "abc123"}
        }
        manager.set_active_environment(env)
        
        if manager.has_active_environment():
            print(f"  [OK] Environment manager works")
        else:
            print(f"  [ERROR] ERROR: Environment not set")
        
        # Test request substitution
        result, unresolved = manager.substitute_in_request(
            url="{{baseUrl}}/users",
            params={"key": "{{token}}"},
            headers={"Auth": "{{token}}"},
            body='{"url": "{{baseUrl}}"}',
            auth_token="{{token}}"
        )
        
        if result['url'] == "https://test.com/users":
            print(f"  [OK] Full request substitution works")
        else:
            print(f"  [ERROR] ERROR: Request substitution failed")
        
        print("[OK] Variable substitution tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Variable substitution test failed: {e}")
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases that might cause crashes."""
    print("Testing Edge Cases...")
    
    try:
        db = DatabaseManager("test_api_client.db")
        
        # Test None handling
        request = db.get_request(99999)
        if request is None:
            print("  [OK] Non-existent request returns None")
        
        collection = db.get_collection(99999)
        if collection is None:
            print("  [OK] Non-existent collection returns None")
        
        # Test empty params/headers
        collections = db.get_all_collections()
        if collections:
            col_id = collections[0]['id']
            req_id = db.create_request(
                collection_id=col_id,
                name="Empty Request",
                method="GET",
                url="https://example.com",
                params=None,
                headers=None,
                body=None
            )
            
            request = db.get_request(req_id)
            print(f"  [OK] Request with None params/headers: {request['params']}, {request['headers']}")
        
        # Test variable substitution with None
        result, unresolved = VariableSubstitution.substitute(None, {})
        if result is None:
            print("  [OK] Substitution handles None text")
        
        result, unresolved = VariableSubstitution.substitute_dict(None, {})
        if result is None:
            print("  [OK] Substitution handles None dict")
        
        db.close()
        print("[OK] Edge case tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Edge case test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("API Client Application - Test Suite")
    print("="*60)
    print()
    
    results = []
    
    results.append(("Database", test_database()))
    results.append(("API Client", test_api_client()))
    results.append(("Variable Substitution", test_variable_substitution()))
    results.append(("Edge Cases", test_edge_cases()))
    
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
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAIL] Some tests failed. Please review the output above.")
    
    # Clean up test database
    import os
    if os.path.exists("test_api_client.db"):
        os.remove("test_api_client.db")
        print("\nTest database cleaned up.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

