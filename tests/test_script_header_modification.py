"""
Test that headers added via pm.request.headers.add() in pre-request scripts
are properly included in the actual HTTP request.

This test validates the fix for the bug where script-added headers were
lost during variable re-substitution.
"""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow
import json
import time


@pytest.fixture
def app(qtbot):
    """Create application instance for testing with in-memory database."""
    main_window = MainWindow(db_path=":memory:")
    qtbot.addWidget(main_window)
    main_window.show()
    qtbot.waitExposed(main_window)
    yield main_window
    main_window.close()


def test_script_adds_headers_to_request(app, qtbot, monkeypatch):
    """
    Test that headers added via pm.request.headers.add() in pre-request script
    are included in the actual HTTP request.
    
    This reproduces the bug where headers added by script were lost.
    """
    # Track the actual request that gets sent
    actual_headers = {}
    
    def mock_execute_request(method, url, headers=None, params=None, body=None, 
                            auth=None, timeout=None, verify_ssl=None, 
                            allow_redirects=True, cert=None):
        """Mock HTTP request to capture headers."""
        nonlocal actual_headers
        actual_headers = headers.copy() if headers else {}
        
        # Return mock response
        return {
            'status_code': 200,
            'reason': 'OK',
            'headers': {'Content-Type': 'application/json'},
            'content': json.dumps({'success': True, 'headers_received': actual_headers}),
            'elapsed_ms': 100,
            'size_bytes': 50
        }
    
    # Mock the ApiClient.execute_request method
    from src.core import api_client
    monkeypatch.setattr(api_client.ApiClient, 'execute_request', mock_execute_request)
    
    # Create a test collection and request
    collection_id = app.db.create_collection("Test Collection")
    request_id = app.db.create_request(
        collection_id=collection_id,
        name="Test Request",
        method="POST",
        url="https://api.example.com/test",
        headers=json.dumps({"Content-Type": "application/json"}),
        body='{"test": "data"}'
    )
    
    # Add pre-request script that adds a header
    pre_request_script = """
    // Add custom header via script
    pm.request.headers.add({
        key: 'X-Ctx-User-Id', 
        value: 'product-delivery-process-test-automation@services'
    });
    
    // Add another header to ensure multiple additions work
    pm.request.headers.add({
        key: 'X-Custom-Token',
        value: 'script-generated-token-12345'
    });
    
    console.log('Headers added by script');
    """
    
    # Get the request to update it with the script
    request = app.db.get_request(request_id)
    app.db.update_request(
        request_id=request_id,
        name=request['name'],
        method=request['method'],
        url=request['url'],
        params=request.get('params'),
        headers=request.get('headers'),
        body=request.get('body'),
        auth_type=request.get('auth_type', 'None'),
        auth_token=request.get('auth_token'),
        description=request.get('description'),
        pre_request_script=pre_request_script
    )
    
    # Set current collection and request
    app.current_collection_id = collection_id
    app.current_request_id = request_id
    
    # Load the request into UI
    app._load_request(request_id)
    qtbot.wait(100)
    
    # Verify request is loaded
    assert app.url_input.text() == "https://api.example.com/test"
    
    # Send the request
    app._send_request()
    qtbot.wait(500)  # Wait for async processing
    
    # Verify that script-added headers are in the actual request
    assert 'X-Ctx-User-Id' in actual_headers, \
        f"Script-added header 'X-Ctx-User-Id' missing from request. Headers sent: {actual_headers}"
    
    assert actual_headers['X-Ctx-User-Id'] == 'product-delivery-process-test-automation@services', \
        f"Script-added header has wrong value. Expected 'product-delivery-process-test-automation@services', got '{actual_headers.get('X-Ctx-User-Id')}'"
    
    assert 'X-Custom-Token' in actual_headers, \
        f"Script-added header 'X-Custom-Token' missing from request. Headers sent: {actual_headers}"
    
    assert actual_headers['X-Custom-Token'] == 'script-generated-token-12345', \
        f"Script-added header has wrong value"
    
    # Verify original headers are also preserved
    assert 'Content-Type' in actual_headers, \
        "Original header 'Content-Type' was lost"
    
    assert actual_headers['Content-Type'] == 'application/json', \
        "Original header value was changed"


def test_script_headers_with_variable_substitution(app, qtbot, monkeypatch):
    """
    Test that script-added headers work correctly when variable substitution is also happening.
    This is the specific scenario that was failing.
    """
    actual_headers = {}
    
    def mock_execute_request(method, url, headers=None, params=None, body=None, 
                            auth=None, timeout=None, verify_ssl=None, 
                            allow_redirects=True, cert=None):
        nonlocal actual_headers
        actual_headers = headers.copy() if headers else {}
        return {
            'status_code': 200,
            'reason': 'OK',
            'headers': {'Content-Type': 'application/json'},
            'content': json.dumps({'success': True}),
            'elapsed_ms': 100,
            'size_bytes': 50
        }
    
    from src.core import api_client
    monkeypatch.setattr(api_client.ApiClient, 'execute_request', mock_execute_request)
    
    # Create collection with variables
    collection_id = app.db.create_collection("Test Collection")
    app.db.create_collection_variable(collection_id, "baseUrl", "https://api.example.com")
    app.db.create_collection_variable(collection_id, "apiKey", "test-api-key-123")
    
    # Create request with variable references in headers
    request_id = app.db.create_request(
        collection_id=collection_id,
        name="Test Request",
        method="POST",
        url="{{baseUrl}}/endpoint",
        headers=json.dumps({
            "Content-Type": "application/json",
            "Authorization": "Bearer {{apiKey}}"
        }),
        body='{"test": "data"}'
    )
    
    # Pre-request script that adds headers (this should work alongside variable substitution)
    pre_request_script = """
    pm.request.headers.add({
        key: 'X-Ctx-User-Id', 
        value: 'script-user@example.com'
    });
    """
    
    request = app.db.get_request(request_id)
    app.db.update_request(
        request_id=request_id,
        name=request['name'],
        method=request['method'],
        url=request['url'],
        params=request.get('params'),
        headers=request.get('headers'),
        body=request.get('body'),
        auth_type=request.get('auth_type', 'None'),
        auth_token=request.get('auth_token'),
        description=request.get('description'),
        pre_request_script=pre_request_script
    )
    
    # Set current collection and load request
    app.current_collection_id = collection_id
    app.current_request_id = request_id
    app._load_request(request_id)
    qtbot.wait(100)
    
    # Send request
    app._send_request()
    qtbot.wait(500)
    
    # Verify all headers are present:
    # 1. Original headers with variables substituted
    assert 'Content-Type' in actual_headers
    assert actual_headers['Content-Type'] == 'application/json'
    
    assert 'Authorization' in actual_headers
    assert actual_headers['Authorization'] == 'Bearer test-api-key-123', \
        f"Variable substitution failed. Expected 'Bearer test-api-key-123', got '{actual_headers.get('Authorization')}'"
    
    # 2. Script-added header
    assert 'X-Ctx-User-Id' in actual_headers, \
        f"Script-added header missing. Headers: {actual_headers}"
    assert actual_headers['X-Ctx-User-Id'] == 'script-user@example.com'


def test_script_modifies_existing_header(app, qtbot, monkeypatch):
    """
    Test that scripts can modify existing headers (not just add new ones).
    """
    actual_headers = {}
    
    def mock_execute_request(method, url, headers=None, params=None, body=None, 
                            auth=None, timeout=None, verify_ssl=None, 
                            allow_redirects=True, cert=None):
        nonlocal actual_headers
        actual_headers = headers.copy() if headers else {}
        return {
            'status_code': 200,
            'reason': 'OK',
            'headers': {'Content-Type': 'application/json'},
            'content': json.dumps({'success': True}),
            'elapsed_ms': 100,
            'size_bytes': 50
        }
    
    from src.core import api_client
    monkeypatch.setattr(api_client.ApiClient, 'execute_request', mock_execute_request)
    
    collection_id = app.db.create_collection("Test Collection")
    request_id = app.db.create_request(
        collection_id=collection_id,
        name="Test Request",
        method="GET",
        url="https://api.example.com/test",
        headers=json.dumps({"User-Agent": "PostMini/1.0"}),
        body=""
    )
    
    # Script modifies existing header
    pre_request_script = """
    pm.request.headers.upsert({
        key: 'User-Agent',
        value: 'PostMini/2.0 (Modified by Script)'
    });
    """
    
    request = app.db.get_request(request_id)
    app.db.update_request(
        request_id=request_id,
        name=request['name'],
        method=request['method'],
        url=request['url'],
        params=request.get('params'),
        headers=request.get('headers'),
        body=request.get('body'),
        auth_type=request.get('auth_type', 'None'),
        auth_token=request.get('auth_token'),
        description=request.get('description'),
        pre_request_script=pre_request_script
    )
    
    app.current_request_id = request_id
    app._load_request(request_id)
    qtbot.wait(100)
    
    app._send_request()
    qtbot.wait(500)
    
    # Verify header was modified by script
    assert 'User-Agent' in actual_headers
    assert actual_headers['User-Agent'] == 'PostMini/2.0 (Modified by Script)', \
        f"Header modification failed. Expected 'PostMini/2.0 (Modified by Script)', got '{actual_headers.get('User-Agent')}'"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
