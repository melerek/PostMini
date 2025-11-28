"""
Test Request Details Display and Auto Content-Type Header

This test verifies:
1. Request Details shows actual URL-encoded format (not JSON) when using x-www-form-urlencoded
2. Content-Type header is automatically set when body type is selected
3. Multipart form-data displays correctly in Request Details
"""

import pytest
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow


@pytest.fixture(scope='module')
def app():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def main_window(app, qtbot):
    """Create MainWindow instance."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window


def test_urlencoded_request_details_display(main_window, qtbot):
    """Test that Request Details shows URL-encoded format, not JSON."""
    # Create a new request
    main_window._clear_request_editor()
    
    # Set method and URL
    main_window.method_combo.setCurrentText('POST')
    main_window.url_input.setText('https://api.example.com/oauth/token')
    
    # Select x-www-form-urlencoded body type
    body_type_index = main_window.body_type_combo.findText('x-www-form-urlencoded')
    assert body_type_index >= 0, "Body type 'x-www-form-urlencoded' not found"
    main_window.body_type_combo.setCurrentIndex(body_type_index)
    
    # Check that Content-Type header was auto-set
    headers = main_window._get_table_as_dict(main_window.headers_table)
    assert 'Content-Type' in headers, "Content-Type header not auto-set"
    assert headers['Content-Type'] == 'application/x-www-form-urlencoded', \
        f"Expected 'application/x-www-form-urlencoded', got '{headers['Content-Type']}'"
    
    # Enter JSON body (user-friendly format)
    body_json = {
        "grant_type": "password",
        "username": "admin@ecovadis.com",
        "password": "secret123"
    }
    main_window.body_input.setPlainText(json.dumps(body_json, indent=2))
    
    # Manually populate request details (simulate send request flow)
    main_window.current_request_details = {
        'method': 'POST',
        'url': 'https://api.example.com/oauth/token',
        'params': {},
        'headers': headers,
        'body': json.dumps(body_json),
        'auth_type': 'None',
        'auth_token': ''
    }
    
    # Update request details viewer
    main_window._update_request_details_viewer()
    
    # Get displayed text
    displayed_text = main_window.request_details_viewer.toPlainText()
    
    # Verify URL-encoded format is shown (not JSON)
    assert 'grant_type=password' in displayed_text, \
        "Request Details should show URL-encoded format"
    assert 'username=admin%40ecovadis.com' in displayed_text, \
        "URL encoding should be applied (@ -> %40)"
    assert 'password=secret123' in displayed_text, \
        "All form fields should be URL-encoded"
    
    # Verify JSON is NOT shown
    assert '{"grant_type"' not in displayed_text, \
        "Request Details should NOT show JSON format"
    assert '"username"' not in displayed_text, \
        "JSON keys should not appear in Request Details"
    
    print("✅ Request Details correctly displays URL-encoded format")


def test_multipart_request_details_display(main_window, qtbot):
    """Test that Request Details shows multipart form-data correctly."""
    # Create a new request
    main_window._clear_request_editor()
    
    # Set method and URL
    main_window.method_combo.setCurrentText('POST')
    main_window.url_input.setText('https://api.example.com/upload')
    
    # Select form-data body type
    body_type_index = main_window.body_type_combo.findText('form-data')
    assert body_type_index >= 0, "Body type 'form-data' not found"
    main_window.body_type_combo.setCurrentIndex(body_type_index)
    
    # Check that Content-Type header was auto-set
    headers = main_window._get_table_as_dict(main_window.headers_table)
    assert 'Content-Type' in headers, "Content-Type header not auto-set"
    assert headers['Content-Type'] == 'multipart/form-data', \
        f"Expected 'multipart/form-data', got '{headers['Content-Type']}'"
    
    # Enter JSON body
    body_json = {
        "file": "document.pdf",
        "description": "Test file"
    }
    main_window.body_input.setPlainText(json.dumps(body_json, indent=2))
    
    # Manually populate request details
    main_window.current_request_details = {
        'method': 'POST',
        'url': 'https://api.example.com/upload',
        'params': {},
        'headers': headers,
        'body': json.dumps(body_json),
        'auth_type': 'None',
        'auth_token': ''
    }
    
    # Update request details viewer
    main_window._update_request_details_viewer()
    
    # Get displayed text
    displayed_text = main_window.request_details_viewer.toPlainText()
    
    # Verify multipart format is shown
    assert 'Multipart Form Data:' in displayed_text, \
        "Request Details should indicate multipart format"
    assert 'file: document.pdf' in displayed_text, \
        "Multipart fields should be displayed"
    assert 'description: Test file' in displayed_text, \
        "All multipart fields should be shown"
    
    print("✅ Request Details correctly displays multipart form-data")


def test_content_type_auto_set_on_body_type_change(main_window, qtbot):
    """Test that Content-Type header is automatically set when body type changes."""
    # Clear editor
    main_window._clear_request_editor()
    
    # Test 1: Select x-www-form-urlencoded
    body_type_index = main_window.body_type_combo.findText('x-www-form-urlencoded')
    main_window.body_type_combo.setCurrentIndex(body_type_index)
    
    headers = main_window._get_table_as_dict(main_window.headers_table)
    assert 'Content-Type' in headers, "Content-Type not set for x-www-form-urlencoded"
    assert headers['Content-Type'] == 'application/x-www-form-urlencoded'
    
    # Test 2: Change to form-data
    body_type_index = main_window.body_type_combo.findText('form-data')
    main_window.body_type_combo.setCurrentIndex(body_type_index)
    
    headers = main_window._get_table_as_dict(main_window.headers_table)
    assert 'Content-Type' in headers, "Content-Type not set for form-data"
    assert headers['Content-Type'] == 'multipart/form-data'
    
    # Test 3: Change to raw
    body_type_index = main_window.body_type_combo.findText('raw')
    main_window.body_type_combo.setCurrentIndex(body_type_index)
    
    headers = main_window._get_table_as_dict(main_window.headers_table)
    assert 'Content-Type' in headers, "Content-Type not set for raw"
    assert headers['Content-Type'] == 'application/json'
    
    # Test 4: Change to none (should remove Content-Type)
    body_type_index = main_window.body_type_combo.findText('none')
    main_window.body_type_combo.setCurrentIndex(body_type_index)
    
    headers = main_window._get_table_as_dict(main_window.headers_table)
    # Content-Type should be removed or empty
    assert 'Content-Type' not in headers or not headers.get('Content-Type'), \
        "Content-Type should be removed when body type is none"
    
    print("✅ Content-Type header auto-sets correctly for all body types")


def test_json_raw_body_not_converted(main_window, qtbot):
    """Test that raw JSON body is displayed as-is (not converted)."""
    # Clear editor
    main_window._clear_request_editor()
    
    # Reset body type to 'none' first to ensure signal fires when we select 'raw'
    none_index = main_window.body_type_combo.findText('none')
    main_window.body_type_combo.setCurrentIndex(none_index)
    qtbot.wait(50)
    
    # Now select raw body type
    body_type_index = main_window.body_type_combo.findText('raw')
    main_window.body_type_combo.setCurrentIndex(body_type_index)
    qtbot.wait(50)  # Allow signal to process
    
    # Check Content-Type header
    headers = main_window._get_table_as_dict(main_window.headers_table)
    assert headers.get('Content-Type') == 'application/json', \
        f"Expected Content-Type to be 'application/json', got: {headers.get('Content-Type')}"
    
    # Enter JSON body
    body_json = {"name": "test", "value": 123}
    main_window.body_input.setPlainText(json.dumps(body_json, indent=2))
    
    # Populate request details
    main_window.current_request_details = {
        'method': 'POST',
        'url': 'https://api.example.com/data',
        'params': {},
        'headers': headers,
        'body': json.dumps(body_json, indent=2),
        'auth_type': 'None',
        'auth_token': ''
    }
    
    # Update request details viewer
    main_window._update_request_details_viewer()
    
    # Get displayed text
    displayed_text = main_window.request_details_viewer.toPlainText()
    
    # Verify JSON is displayed as-is (not converted)
    assert '"name"' in displayed_text, "JSON keys should be preserved for raw body"
    assert '"test"' in displayed_text, "JSON values should be preserved"
    assert 'name=test' not in displayed_text, "Raw JSON should NOT be URL-encoded"
    
    print("✅ Raw JSON body correctly displayed as-is")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
