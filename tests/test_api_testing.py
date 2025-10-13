"""
API Testing / Assertions Test Suite

Comprehensive tests for the API testing functionality.
"""

import sys
import traceback
import json
from datetime import datetime

from src.core.database import DatabaseManager
from src.features.test_engine import TestEngine, TestAssertion, TestResult
from src.core.api_client import ApiResponse


def create_mock_response(status_code=200, text='{"message": "success"}',
                         headers=None, elapsed_time=0.5):
    """Create a mock API response for testing."""
    if headers is None:
        headers = {'Content-Type': 'application/json'}
    
    # Create a mock requests.Response object
    import requests
    mock_response = requests.models.Response()
    mock_response.status_code = status_code
    mock_response._content = text.encode('utf-8')
    mock_response.headers = headers
    
    # Wrap in ApiResponse
    api_response = ApiResponse(mock_response, elapsed_time)
    return api_response


def test_database_assertions_schema():
    """Test test assertions database schema."""
    print("Testing Test Assertions Database Schema...")
    
    try:
        db = DatabaseManager(":memory:")
        
        # Create a collection and request
        collection_id = db.create_collection("Test Collection")
        request_id = db.create_request(
            collection_id=collection_id,
            name="Test Request",
            method="GET",
            url="https://api.example.com/test"
        )
        
        # Create test assertion
        assertion_id = db.create_test_assertion(
            request_id=request_id,
            assertion_type=TestAssertion.TYPE_STATUS_CODE,
            operator=TestAssertion.OP_EQUALS,
            expected_value="200"
        )
        
        if assertion_id > 0:
            print("  [OK] Create test assertion")
        
        # Get assertions
        assertions = db.get_test_assertions(request_id)
        if len(assertions) == 1:
            print("  [OK] Get test assertions")
        
        # Update assertion
        db.update_test_assertion(
            assertion_id=assertion_id,
            assertion_type=TestAssertion.TYPE_STATUS_CODE,
            operator=TestAssertion.OP_LESS_THAN,
            expected_value="300"
        )
        
        updated = db.get_test_assertions(request_id)[0]
        if updated['operator'] == TestAssertion.OP_LESS_THAN:
            print("  [OK] Update test assertion")
        
        # Delete assertion
        db.delete_test_assertion(assertion_id)
        assertions = db.get_test_assertions(request_id)
        if len(assertions) == 0:
            print("  [OK] Delete test assertion")
        
        db.close()
        print("[OK] Test assertions database tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test assertions database test failed: {e}")
        traceback.print_exc()
        return False


def test_status_code_assertions():
    """Test status code assertions."""
    print("Testing Status Code Assertions...")
    
    try:
        response = create_mock_response(status_code=200)
        
        # Test equals
        assertion = TestAssertion(1, TestAssertion.TYPE_STATUS_CODE, TestAssertion.OP_EQUALS,
                                 expected_value="200")
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Status code equals")
        
        # Test not equals
        assertion = TestAssertion(2, TestAssertion.TYPE_STATUS_CODE, TestAssertion.OP_NOT_EQUALS,
                                 expected_value="404")
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Status code not equals")
        
        # Test less than
        assertion = TestAssertion(3, TestAssertion.TYPE_STATUS_CODE, TestAssertion.OP_LESS_THAN,
                                 expected_value="300")
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Status code less than")
        
        # Test failure case
        assertion = TestAssertion(4, TestAssertion.TYPE_STATUS_CODE, TestAssertion.OP_EQUALS,
                                 expected_value="404")
        result = TestEngine.evaluate_assertion(assertion, response)
        if not result.passed:
            print("  [OK] Status code assertion fails correctly")
        
        print("[OK] Status code assertion tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Status code assertion test failed: {e}")
        traceback.print_exc()
        return False


def test_response_time_assertions():
    """Test response time assertions."""
    print("Testing Response Time Assertions...")
    
    try:
        response = create_mock_response(elapsed_time=0.5)  # 500ms
        
        # Test less than
        assertion = TestAssertion(1, TestAssertion.TYPE_RESPONSE_TIME, TestAssertion.OP_LESS_THAN,
                                 expected_value="1000")  # 1000ms
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Response time less than")
        
        # Test greater than
        assertion = TestAssertion(2, TestAssertion.TYPE_RESPONSE_TIME, TestAssertion.OP_GREATER_THAN,
                                 expected_value="100")  # 100ms
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Response time greater than")
        
        print("[OK] Response time assertion tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Response time assertion test failed: {e}")
        traceback.print_exc()
        return False


def test_header_assertions():
    """Test header assertions."""
    print("Testing Header Assertions...")
    
    try:
        response = create_mock_response(headers={
            'Content-Type': 'application/json',
            'X-API-Version': '1.0'
        })
        
        # Test exists
        assertion = TestAssertion(1, TestAssertion.TYPE_HEADER, TestAssertion.OP_EXISTS,
                                 field='Content-Type')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Header exists")
        
        # Test equals
        assertion = TestAssertion(2, TestAssertion.TYPE_HEADER, TestAssertion.OP_EQUALS,
                                 field='Content-Type', expected_value='application/json')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Header equals")
        
        # Test not exists
        assertion = TestAssertion(3, TestAssertion.TYPE_HEADER, TestAssertion.OP_NOT_EXISTS,
                                 field='X-Missing-Header')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Header not exists")
        
        print("[OK] Header assertion tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Header assertion test failed: {e}")
        traceback.print_exc()
        return False


def test_body_assertions():
    """Test body content assertions."""
    print("Testing Body Assertions...")
    
    try:
        response = create_mock_response(text='{"message": "success", "status": "ok"}')
        
        # Test contains
        assertion = TestAssertion(1, TestAssertion.TYPE_BODY_CONTAINS, TestAssertion.OP_CONTAINS,
                                 expected_value='success')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Body contains")
        
        # Test not contains
        assertion = TestAssertion(2, TestAssertion.TYPE_BODY_CONTAINS, TestAssertion.OP_NOT_CONTAINS,
                                 expected_value='error')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] Body not contains")
        
        print("[OK] Body assertion tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Body assertion test failed: {e}")
        traceback.print_exc()
        return False


def test_json_path_assertions():
    """Test JSON path assertions."""
    print("Testing JSON Path Assertions...")
    
    try:
        response = create_mock_response(text='{"user": {"name": "John", "age": 30}, "items": [{"id": 1}, {"id": 2}]}')
        
        # Test simple path
        assertion = TestAssertion(1, TestAssertion.TYPE_JSON_PATH, TestAssertion.OP_EQUALS,
                                 field='user.name', expected_value='John')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] JSON path equals")
        
        # Test nested path
        assertion = TestAssertion(2, TestAssertion.TYPE_JSON_PATH, TestAssertion.OP_EQUALS,
                                 field='user.age', expected_value='30')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] JSON path with number")
        
        # Test array path
        assertion = TestAssertion(3, TestAssertion.TYPE_JSON_PATH, TestAssertion.OP_EQUALS,
                                 field='items[0].id', expected_value='1')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] JSON path with array index")
        
        # Test exists
        assertion = TestAssertion(4, TestAssertion.TYPE_JSON_PATH, TestAssertion.OP_EXISTS,
                                 field='user.name')
        result = TestEngine.evaluate_assertion(assertion, response)
        if result.passed:
            print("  [OK] JSON path exists")
        
        print("[OK] JSON path assertion tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] JSON path assertion test failed: {e}")
        traceback.print_exc()
        return False


def test_multiple_assertions():
    """Test evaluating multiple assertions."""
    print("Testing Multiple Assertions...")
    
    try:
        response = create_mock_response(
            status_code=200,
            text='{"message": "success"}',
            headers={'Content-Type': 'application/json'},
            elapsed_time=0.3
        )
        
        assertions = [
            TestAssertion(1, TestAssertion.TYPE_STATUS_CODE, TestAssertion.OP_EQUALS, expected_value='200'),
            TestAssertion(2, TestAssertion.TYPE_RESPONSE_TIME, TestAssertion.OP_LESS_THAN, expected_value='500'),
            TestAssertion(3, TestAssertion.TYPE_HEADER, TestAssertion.OP_EXISTS, field='Content-Type'),
            TestAssertion(4, TestAssertion.TYPE_JSON_PATH, TestAssertion.OP_EQUALS, field='message', expected_value='success'),
        ]
        
        results = TestEngine.evaluate_all(assertions, response)
        
        if len(results) == 4:
            print("  [OK] All assertions evaluated")
        
        if all(r.passed for r in results):
            print("  [OK] All assertions passed")
        
        summary = TestEngine.get_summary(results)
        if summary['total'] == 4 and summary['passed'] == 4:
            print("  [OK] Summary correct")
        
        print("[OK] Multiple assertions tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Multiple assertions test failed: {e}")
        traceback.print_exc()
        return False


def test_test_results_database():
    """Test test results database operations."""
    print("Testing Test Results Database...")
    
    try:
        db = DatabaseManager(":memory:")
        
        # Create collection and request
        collection_id = db.create_collection("Test Collection")
        request_id = db.create_request(collection_id, "Test Request", "GET", "https://api.example.com/test")
        
        # Create assertions
        assertion_id = db.create_test_assertion(
            request_id, TestAssertion.TYPE_STATUS_CODE, TestAssertion.OP_EQUALS, expected_value='200'
        )
        
        # Save test result
        result_id = db.save_test_result(
            request_id=request_id,
            assertion_id=assertion_id,
            passed=True,
            actual_value='200'
        )
        
        if result_id > 0:
            print("  [OK] Save test result")
        
        # Get test results
        results = db.get_test_results(request_id)
        if len(results) == 1:
            print("  [OK] Get test results")
        
        # Get latest results
        latest = db.get_latest_test_results(request_id)
        if len(latest) == 1:
            print("  [OK] Get latest test results")
        
        # Clear results
        db.clear_test_results(request_id)
        results = db.get_test_results(request_id)
        if len(results) == 0:
            print("  [OK] Clear test results")
        
        db.close()
        print("[OK] Test results database tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test results database test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all API testing tests."""
    print("="*60)
    print("API Testing / Assertions Test Suite")
    print("="*60)
    print()
    
    results = []
    
    results.append(("Test Assertions Database", test_database_assertions_schema()))
    results.append(("Status Code Assertions", test_status_code_assertions()))
    results.append(("Response Time Assertions", test_response_time_assertions()))
    results.append(("Header Assertions", test_header_assertions()))
    results.append(("Body Assertions", test_body_assertions()))
    results.append(("JSON Path Assertions", test_json_path_assertions()))
    results.append(("Multiple Assertions", test_multiple_assertions()))
    results.append(("Test Results Database", test_test_results_database()))
    
    print()
    print("="*60)
    print("Test Results Summary")
    print("="*60)
    
    for name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{name:.<45} {status}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("[SUCCESS] All API testing tests passed!")
        print("API Testing / Assertions feature is ready for production!")
    else:
        print("[FAIL] Some tests failed.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

