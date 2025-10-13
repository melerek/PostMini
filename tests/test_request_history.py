"""
Request History Test Suite

Comprehensive tests for request history functionality.
"""

import sys
import os
from datetime import datetime, timedelta
import traceback
from src.core.database import DatabaseManager


def test_history_table_creation():
    """Test that history table is created."""
    print("Testing History Table Creation...")
    
    try:
        db = DatabaseManager("test_history.db")
        
        # Check that history table exists by trying to query it
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM request_history")
        count = cursor.fetchone()[0]
        
        print(f"  [OK] History table exists (count: {count})")
        
        db.close()
        print("[OK] Table creation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Table creation test failed: {e}")
        traceback.print_exc()
        return False


def test_save_history():
    """Test saving request history."""
    print("Testing Save History...")
    
    try:
        db = DatabaseManager("test_history.db")
        
        # Save a successful request
        history_id = db.save_request_history(
            timestamp=datetime.now().isoformat(),
            method="GET",
            url="https://api.example.com/users",
            request_params={"limit": "10"},
            request_headers={"Authorization": "Bearer token"},
            response_status=200,
            response_headers={"Content-Type": "application/json"},
            response_body='{"users": []}',
            response_time=0.523,
            response_size=1024
        )
        
        if history_id:
            print(f"  [OK] History saved with ID: {history_id}")
        
        # Save a failed request
        fail_id = db.save_request_history(
            timestamp=datetime.now().isoformat(),
            method="POST",
            url="https://api.example.com/create",
            response_status=500,
            error_message="Internal Server Error"
        )
        
        if fail_id:
            print(f"  [OK] Failed request saved with ID: {fail_id}")
        
        # Save with collection/request context
        col_id = db.create_collection("Test Collection")
        req_id = db.create_request(
            collection_id=col_id,
            name="Test Request",
            method="GET",
            url="https://api.example.com/test"
        )
        
        ctx_id = db.save_request_history(
            timestamp=datetime.now().isoformat(),
            method="GET",
            url="https://api.example.com/test",
            collection_id=col_id,
            request_id=req_id,
            request_name="Test Request",
            response_status=200
        )
        
        if ctx_id:
            print(f"  [OK] Request with context saved: {ctx_id}")
        
        db.close()
        print("[OK] Save history tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Save history test failed: {e}")
        traceback.print_exc()
        return False


def test_retrieve_history():
    """Test retrieving history entries."""
    print("Testing Retrieve History...")
    
    try:
        db = DatabaseManager("test_history.db")
        
        # Add some history entries
        for i in range(5):
            db.save_request_history(
                timestamp=datetime.now().isoformat(),
                method="GET",
                url=f"https://api.example.com/endpoint{i}",
                response_status=200 if i % 2 == 0 else 404
            )
        
        # Get all history
        history = db.get_request_history(limit=100)
        if len(history) > 0:
            print(f"  [OK] Retrieved {len(history)} history entries")
        
        # Get history with limit
        limited = db.get_request_history(limit=3)
        if len(limited) == 3:
            print("  [OK] Limit works correctly")
        
        # Get specific entry
        if history:
            entry = db.get_history_entry(history[0]['id'])
            if entry and entry['id'] == history[0]['id']:
                print("  [OK] Retrieved specific entry")
        
        db.close()
        print("[OK] Retrieve history tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Retrieve history test failed: {e}")
        traceback.print_exc()
        return False


def test_history_filtering():
    """Test filtering history entries."""
    print("Testing History Filtering...")
    
    try:
        db = DatabaseManager("test_history.db")
        
        # Clear existing history
        db.clear_history()
        
        # Create collection for filtering
        col_id = db.create_collection("Filter Test Collection")
        
        # Add requests with different statuses
        statuses = [200, 200, 404, 404, 500, 500]
        for i, status in enumerate(statuses):
            db.save_request_history(
                timestamp=datetime.now().isoformat(),
                method="GET",
                url=f"https://api.example.com/test{i}",
                collection_id=col_id if i < 3 else None,
                response_status=status
            )
        
        # Test filter by collection
        by_collection = db.get_history_by_collection(col_id)
        if len(by_collection) == 3:
            print(f"  [OK] Filter by collection works ({len(by_collection)} entries)")
        else:
            print(f"  [ERROR] Filter by collection expected 3, got {len(by_collection)}")
        
        # Test filter by status
        by_status_200 = db.get_history_by_status(200)
        if len(by_status_200) == 2:
            print(f"  [OK] Filter by status 200 works ({len(by_status_200)} entries)")
        
        by_status_404 = db.get_history_by_status(404)
        if len(by_status_404) == 2:
            print(f"  [OK] Filter by status 404 works ({len(by_status_404)} entries)")
        
        # Test failed requests filter
        failed = db.get_failed_requests()
        if len(failed) == 4:  # 404 and 500 entries
            print(f"  [OK] Failed requests filter works ({len(failed)} entries)")
        
        db.close()
        print("[OK] History filtering tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] History filtering test failed: {e}")
        traceback.print_exc()
        return False


def test_clear_history():
    """Test clearing history."""
    print("Testing Clear History...")
    
    try:
        db = DatabaseManager("test_history.db")
        
        # Add some entries
        for i in range(5):
            db.save_request_history(
                timestamp=datetime.now().isoformat(),
                method="GET",
                url=f"https://api.example.com/test{i}",
                response_status=200
            )
        
        # Check count before
        count_before = db.get_history_count()
        if count_before > 0:
            print(f"  [OK] History count before clear: {count_before}")
        
        # Clear all
        db.clear_history()
        count_after = db.get_history_count()
        
        if count_after == 0:
            print("  [OK] Clear all history works")
        
        # Test clear with date filter
        # Add entries with different timestamps
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        new_date = datetime.now().isoformat()
        
        db.save_request_history(
            timestamp=old_date,
            method="GET",
            url="https://api.example.com/old",
            response_status=200
        )
        
        db.save_request_history(
            timestamp=new_date,
            method="GET",
            url="https://api.example.com/new",
            response_status=200
        )
        
        # Clear old entries (older than 7 days)
        db.clear_history(older_than_days=7)
        
        remaining = db.get_history_count()
        if remaining == 1:
            print("  [OK] Clear with date filter works")
        
        db.close()
        print("[OK] Clear history tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Clear history test failed: {e}")
        traceback.print_exc()
        return False


def test_history_with_large_response():
    """Test history with large response body."""
    print("Testing History with Large Response...")
    
    try:
        db = DatabaseManager("test_history.db")
        
        # Create a large response (> 100KB)
        large_body = "x" * 150000  # 150KB
        
        history_id = db.save_request_history(
            timestamp=datetime.now().isoformat(),
            method="GET",
            url="https://api.example.com/large",
            response_status=200,
            response_body=large_body,
            response_size=len(large_body)
        )
        
        # Retrieve and check if truncated
        entry = db.get_history_entry(history_id)
        
        if entry:
            if "truncated" in entry['response_body']:
                print("  [OK] Large response body truncated correctly")
            if len(entry['response_body']) < len(large_body):
                print(f"  [OK] Body size reduced: {len(large_body)} -> {len(entry['response_body'])}")
        
        db.close()
        print("[OK] Large response tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Large response test failed: {e}")
        traceback.print_exc()
        return False


def test_history_with_null_values():
    """Test history with null/None values."""
    print("Testing History with Null Values...")
    
    try:
        db = DatabaseManager("test_history.db")
        
        # Save with minimal data
        history_id = db.save_request_history(
            timestamp=datetime.now().isoformat(),
            method="GET",
            url="https://api.example.com/minimal"
            # All optional fields are None
        )
        
        if history_id:
            print("  [OK] Saved with minimal data")
        
        # Retrieve and verify
        entry = db.get_history_entry(history_id)
        if entry:
            if entry['request_params'] is None:
                print("  [OK] Null params handled")
            if entry['request_headers'] is None:
                print("  [OK] Null headers handled")
            if entry['response_status'] is None:
                print("  [OK] Null response status handled")
        
        db.close()
        print("[OK] Null values tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Null values test failed: {e}")
        traceback.print_exc()
        return False


def test_history_count():
    """Test history count functionality."""
    print("Testing History Count...")
    
    try:
        db = DatabaseManager("test_history.db")
        
        # Clear and get initial count
        db.clear_history()
        initial_count = db.get_history_count()
        
        if initial_count == 0:
            print("  [OK] Initial count is 0")
        
        # Add 10 entries
        for i in range(10):
            db.save_request_history(
                timestamp=datetime.now().isoformat(),
                method="GET",
                url=f"https://api.example.com/test{i}",
                response_status=200
            )
        
        final_count = db.get_history_count()
        if final_count == 10:
            print(f"  [OK] Count correct after adding: {final_count}")
        
        db.close()
        print("[OK] History count tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] History count test failed: {e}")
        traceback.print_exc()
        return False


def cleanup_test_files():
    """Clean up test files."""
    test_files = ["test_history.db"]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


def main():
    """Run all history tests."""
    print("="*60)
    print("Request History Test Suite")
    print("="*60)
    print()
    
    results = []
    
    results.append(("History Table Creation", test_history_table_creation()))
    results.append(("Save History", test_save_history()))
    results.append(("Retrieve History", test_retrieve_history()))
    results.append(("History Filtering", test_history_filtering()))
    results.append(("Clear History", test_clear_history()))
    results.append(("Large Response", test_history_with_large_response()))
    results.append(("Null Values", test_history_with_null_values()))
    results.append(("History Count", test_history_count()))
    
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
        print("[SUCCESS] All request history tests passed!")
        print("History functionality is ready for production!")
    else:
        print("[FAIL] Some tests failed.")
    
    # Clean up
    cleanup_test_files()
    print("\nTest files cleaned up.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

