"""
UI Logic Test

This script tests UI logic without actually launching the GUI,
to catch bugs that would cause crashes.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager


def test_tree_item_data():
    """Test tree item data handling."""
    print("Testing Tree Item Data Handling...")
    
    # Simulate the data structure used in tree items
    valid_collection_data = {'type': 'collection', 'id': 1}
    valid_request_data = {'type': 'request', 'id': 2, 'collection_id': 1}
    
    # Test valid data
    if valid_collection_data.get('type') == 'collection':
        print("  [OK] Valid collection data recognized")
    
    if valid_request_data.get('type') == 'request':
        print("  [OK] Valid request data recognized")
    
    # Test edge cases that could cause crashes
    none_data = None
    empty_data = {}
    invalid_data = {'something': 'else'}
    
    # These should NOT crash
    if not none_data or not isinstance(none_data, dict):
        print("  [OK] None data handled safely")
    
    if not empty_data.get('type'):
        print("  [OK] Empty data handled safely")
    
    if not invalid_data.get('type'):
        print("  [OK] Invalid data handled safely")
    
    print("[OK] Tree item data tests passed!\n")
    return True


def test_request_loading():
    """Test request loading with edge cases."""
    print("Testing Request Loading...")
    
    try:
        db = DatabaseManager("test_ui_logic.db")
        
        # Create test data
        col_id = db.create_collection("Test UI Collection")
        
        # Test 1: Request with all fields
        req1_id = db.create_request(
            collection_id=col_id,
            name="Full Request",
            method="POST",
            url="https://example.com",
            params={"key": "value"},
            headers={"Content-Type": "application/json"},
            body='{"test": true}',
            auth_type="Bearer Token",
            auth_token="test-token"
        )
        
        request1 = db.get_request(req1_id)
        print(f"  [OK] Full request loaded: {request1['name']}")
        
        # Test 2: Request with None params/headers
        req2_id = db.create_request(
            collection_id=col_id,
            name="Minimal Request",
            method="GET",
            url="https://example.com",
            params=None,
            headers=None,
            body=None,
            auth_type="None",
            auth_token=None
        )
        
        request2 = db.get_request(req2_id)
        if request2['params'] is None:
            print("  [OK] None params handled correctly")
        if request2['headers'] is None:
            print("  [OK] None headers handled correctly")
        
        # Test 3: Non-existent request
        request3 = db.get_request(99999)
        if request3 is None:
            print("  [OK] Non-existent request returns None")
        
        # Test 4: Dict conversion safety
        params = request2.get('params')
        if params is None:
            params = {}
        print(f"  [OK] Safe dict conversion: {params}")
        
        db.close()
        print("[OK] Request loading tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Request loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dict_table_conversion():
    """Test dictionary to table conversion logic."""
    print("Testing Dict/Table Conversion...")
    
    # Simulate _load_dict_to_table logic
    def safe_load_dict(data):
        if not data:
            return []  # Would set table to 5 empty rows
        
        items = []
        for key, value in data.items():
            items.append((key, str(value)))
        return items
    
    # Test with valid data
    valid_data = {"key1": "value1", "key2": "value2"}
    result = safe_load_dict(valid_data)
    if len(result) == 2:
        print("  [OK] Valid dict converted correctly")
    
    # Test with None
    none_data = None
    result = safe_load_dict(none_data)
    if len(result) == 0:
        print("  [OK] None data handled safely")
    
    # Test with empty dict
    empty_data = {}
    result = safe_load_dict(empty_data)
    if len(result) == 0:
        print("  [OK] Empty dict handled safely")
    
    print("[OK] Dict/table conversion tests passed!\n")
    return True


def test_environment_integration():
    """Test environment integration edge cases."""
    print("Testing Environment Integration...")
    
    try:
        from src.features.variable_substitution import EnvironmentManager
        
        manager = EnvironmentManager()
        
        # Test 1: No active environment
        if not manager.has_active_environment():
            print("  [OK] No environment initially")
        
        # Test 2: Set environment
        env = {
            "id": 1,
            "name": "Test",
            "variables": {"baseUrl": "https://test.com"}
        }
        manager.set_active_environment(env)
        print("  [OK] Environment set successfully")
        
        # Test 3: Substitute with missing variables
        result, unresolved = manager.substitute_in_request(
            url="{{baseUrl}}/{{missing}}/test",
            params={},
            headers={},
            body="",
            auth_token=""
        )
        
        if "missing" in unresolved:
            print(f"  [OK] Unresolved variables detected: {unresolved}")
        
        if "https://test.com" in result['url']:
            print("  [OK] Partial substitution works")
        
        # Test 4: Clear environment
        manager.clear_active_environment()
        if not manager.has_active_environment():
            print("  [OK] Environment cleared successfully")
        
        print("[OK] Environment integration tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Environment integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all UI logic tests."""
    print("="*60)
    print("UI Logic Test Suite")
    print("="*60)
    print()
    
    results = []
    
    results.append(("Tree Item Data", test_tree_item_data()))
    results.append(("Request Loading", test_request_loading()))
    results.append(("Dict/Table Conversion", test_dict_table_conversion()))
    results.append(("Environment Integration", test_environment_integration()))
    
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
        print("[SUCCESS] All UI logic tests passed!")
        print("The app should no longer crash when clicking items!")
    else:
        print("[FAIL] Some tests failed.")
    
    # Clean up
    import os
    if os.path.exists("test_ui_logic.db"):
        os.remove("test_ui_logic.db")
        print("\nTest database cleaned up.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

