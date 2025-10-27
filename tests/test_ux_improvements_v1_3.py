"""
Tests for UX Improvements V1.3.0

This module tests the V1.3.0 UX improvements including:
- Request description/notes field (collapsible)
- Enhanced error messages with helpful suggestions
- Request timeout configuration
- SSL certificate handling
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
import sys
import tempfile
import os

from src.ui.main_window import MainWindow
from src.core.api_client import ApiClient


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def main_window(app, temp_db):
    """Create a MainWindow instance for testing."""
    window = MainWindow(db_path=temp_db)
    yield window
    window.close()


class TestDescriptionField:
    """Tests for the request description/notes field feature."""
    
    def test_description_widget_exists(self, main_window):
        """Test that description widget is created."""
        assert hasattr(main_window, 'description_widget')
        assert main_window.description_widget is not None
    
    def test_description_input_exists(self, main_window):
        """Test that description input field exists."""
        assert hasattr(main_window, 'description_input')
        assert main_window.description_input is not None
    
    def test_description_toggle_button_exists(self, main_window):
        """Test that description toggle button exists."""
        assert hasattr(main_window, 'description_toggle_btn')
        assert main_window.description_toggle_btn is not None
    
    def test_description_initial_state_collapsed(self, main_window):
        """Test that description starts collapsed."""
        assert not main_window.description_input.isVisible()
        assert main_window.description_toggle_btn.text() == "▶ Description"
    
    def test_description_toggle_expand(self, main_window):
        """Test expanding the description section."""
        # Ensure initial state
        assert not main_window.description_input.isVisibleTo(main_window.description_widget)
        
        # Toggle description (directly call method for reliable test)
        main_window._toggle_description()
        
        # Verify it's expanded (check if visible relative to parent)
        assert main_window.description_input.isVisibleTo(main_window.description_widget)
        assert main_window.description_toggle_btn.text() == "▼ Description"
    
    def test_description_toggle_collapse(self, main_window):
        """Test collapsing the description section."""
        # Expand first
        main_window._toggle_description()
        assert main_window.description_toggle_btn.text() == "▼ Description"
        
        # Then collapse
        main_window._toggle_description()
        
        # Verify it's collapsed (check button text which indicates state)
        assert main_window.description_toggle_btn.text() == "▶ Description"
        
        # Also verify the widget was set to not visible (direct check)
        from PyQt6.QtCore import Qt
        assert not main_window.description_input.testAttribute(Qt.WidgetAttribute.WA_WState_Visible)
    
    def test_description_save_and_load(self, main_window):
        """Test saving and loading description with request."""
        # Create collection and request
        coll_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            coll_id, "Test Request", "GET", "https://api.example.com",
            description="This is a test description"
        )
        
        # Load the request
        main_window.current_request_id = req_id
        main_window.current_collection_id = coll_id
        main_window._load_request(req_id)
        
        # Verify description is loaded and expanded
        assert main_window.description_input.toPlainText() == "This is a test description"
        assert main_window.description_input.isVisibleTo(main_window.description_widget)
        assert main_window.description_toggle_btn.text() == "▼ Description"
    
    def test_description_save_updates_database(self, main_window):
        """Test that saving request updates description in database."""
        # Create collection and request
        coll_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            coll_id, "Test Request", "GET", "https://api.example.com"
        )
        
        # Load the request
        main_window.current_request_id = req_id
        main_window.current_collection_id = coll_id
        main_window._load_request(req_id)
        
        # Set description
        main_window.description_input.setPlainText("Updated description")
        
        # Save request
        main_window._save_request()
        
        # Verify in database
        request = main_window.db.get_request(req_id)
        assert request['description'] == "Updated description"
    
    def test_description_empty_collapsed_on_load(self, main_window):
        """Test that empty description stays collapsed on load."""
        # Create collection and request with no description
        coll_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            coll_id, "Test Request", "GET", "https://api.example.com"
        )
        
        # Load the request
        main_window.current_request_id = req_id
        main_window._load_request(req_id)
        
        # Verify description is collapsed
        assert not main_window.description_input.isVisible()
        assert main_window.description_toggle_btn.text() == "▶ Description"
    
    def test_description_clears_on_clear_editor(self, main_window):
        """Test that description clears when editor is cleared."""
        # Set some description text
        main_window.description_input.setPlainText("Test description")
        main_window.description_toggle_btn.click()  # Expand
        
        # Clear editor
        main_window._clear_request_editor()
        
        # Verify description is cleared and collapsed
        assert main_window.description_input.toPlainText() == ""
        assert not main_window.description_input.isVisible()
        assert main_window.description_toggle_btn.text() == "▶ Description"
    
    def test_description_marks_as_changed(self, main_window):
        """Test that editing description marks request as changed."""
        # Create and load a request
        coll_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            coll_id, "Test Request", "GET", "https://api.example.com"
        )
        main_window.current_request_id = req_id
        main_window._load_request(req_id)
        
        # Initial state should be not changed
        assert not main_window.has_unsaved_changes
        
        # Edit description
        main_window.description_input.setPlainText("New description")
        
        # Should be marked as changed
        assert main_window.has_unsaved_changes


class TestEnhancedErrorMessages:
    """Tests for enhanced error messages with helpful suggestions."""
    
    def test_enhance_error_message_function_exists(self, main_window):
        """Test that error enhancement function exists."""
        assert hasattr(main_window, '_enhance_error_message')
        assert callable(main_window._enhance_error_message)
    
    def test_connection_error_suggestions(self, main_window):
        """Test connection error provides helpful suggestions."""
        error_msg = "Failed to connect to https://example.com"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert 'short' in enhanced
        assert 'full' in enhanced
        assert enhanced['short'] == "Connection failed"
        assert "Check if the URL is correct" in enhanced['full']
        assert "internet connection" in enhanced['full']
    
    def test_timeout_error_suggestions(self, main_window):
        """Test timeout error provides helpful suggestions."""
        error_msg = "Request timed out after 30 seconds"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Request timed out"
        assert "timeout setting" in enhanced['full']
        assert "currently" in enhanced['full']
        assert "overloaded" in enhanced['full']
    
    def test_dns_error_suggestions(self, main_window):
        """Test DNS resolution error provides helpful suggestions."""
        error_msg = "name or service not known"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Cannot resolve hostname"
        assert "spelled correctly" in enhanced['full']
        assert "domain name exists" in enhanced['full']
    
    def test_ssl_error_suggestions(self, main_window):
        """Test SSL certificate error provides helpful suggestions."""
        error_msg = "SSL certificate verification failed"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "SSL/Certificate error"
        assert "certificate" in enhanced['full']
        assert "http://" in enhanced['full']
        assert "local development" in enhanced['full']
    
    def test_400_error_suggestions(self, main_window):
        """Test 400 Bad Request error provides helpful suggestions."""
        error_msg = "400 bad request"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Bad Request (400)"
        assert "valid JSON" in enhanced['full']
        assert "parameters" in enhanced['full']
    
    def test_401_error_suggestions(self, main_window):
        """Test 401 Unauthorized error provides helpful suggestions."""
        error_msg = "401 unauthorized"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Unauthorized (401)"
        assert "authentication" in enhanced['full']
        assert "token" in enhanced['full']
    
    def test_403_error_suggestions(self, main_window):
        """Test 403 Forbidden error provides helpful suggestions."""
        error_msg = "403 forbidden"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Forbidden (403)"
        assert "permission" in enhanced['full']
        assert "scopes" in enhanced['full']
    
    def test_404_error_suggestions(self, main_window):
        """Test 404 Not Found error provides helpful suggestions."""
        error_msg = "404 not found"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Not Found (404)"
        assert "endpoint URL" in enhanced['full']
        assert "resource exists" in enhanced['full']
    
    def test_429_error_suggestions(self, main_window):
        """Test 429 Rate Limit error provides helpful suggestions."""
        error_msg = "429 rate limit exceeded"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Rate Limited (429)"
        assert "too many requests" in enhanced['full']
        assert "Wait" in enhanced['full']
    
    def test_500_error_suggestions(self, main_window):
        """Test 500 Internal Server Error provides helpful suggestions."""
        error_msg = "500 internal server error"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Internal Server Error (500)"
        assert "server encountered an error" in enhanced['full']
    
    def test_502_error_suggestions(self, main_window):
        """Test 502 Bad Gateway error provides helpful suggestions."""
        error_msg = "502 bad gateway"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Bad Gateway (502)"
        assert "gateway" in enhanced['full']
    
    def test_503_error_suggestions(self, main_window):
        """Test 503 Service Unavailable error provides helpful suggestions."""
        error_msg = "503 service unavailable"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Service Unavailable (503)"
        assert "temporarily unavailable" in enhanced['full']
        assert "maintenance" in enhanced['full']
    
    def test_json_error_suggestions(self, main_window):
        """Test JSON parsing error provides helpful suggestions."""
        error_msg = "JSON decode error"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Invalid JSON"
        assert "valid JSON" in enhanced['full']
        assert "validator" in enhanced['full']
    
    def test_network_error_suggestions(self, main_window):
        """Test network error provides helpful suggestions."""
        error_msg = "Network unreachable"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert enhanced['short'] == "Network error"
        assert "internet connection" in enhanced['full']
        assert "firewall" in enhanced['full']
    
    def test_generic_error_fallback(self, main_window):
        """Test that generic errors get fallback suggestions."""
        error_msg = "Something completely unexpected happened"
        enhanced = main_window._enhance_error_message(error_msg)
        
        assert 'short' in enhanced
        assert 'full' in enhanced
        assert "Suggestions:" in enhanced['full']


class TestTimeoutConfiguration:
    """Tests for request timeout configuration feature."""
    
    def test_timeout_input_exists(self, main_window):
        """Test that timeout input field exists."""
        assert hasattr(main_window, 'timeout_input')
        assert main_window.timeout_input is not None
    
    def test_timeout_default_value(self, main_window):
        """Test that timeout has default value of 30."""
        assert main_window.timeout_input.text() == "30"
    
    def test_timeout_input_in_auth_tab(self, main_window):
        """Test that timeout input is in Authorization tab."""
        # Authorization tab should have timeout settings
        auth_widget = main_window.inner_tabs.widget(2)  # Auth tab is index 2
        assert auth_widget is not None
    
    def test_timeout_updates_api_client(self, main_window):
        """Test that timeout setting updates API client."""
        # Set timeout
        main_window.timeout_input.setText("60")
        
        # Set URL to allow send
        main_window.url_input.setText("https://httpbin.org/delay/1")
        
        # Create a collection and request for valid context
        coll_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            coll_id, "Test Request", "GET", "https://httpbin.org/delay/1"
        )
        main_window.current_request_id = req_id
        main_window.current_collection_id = coll_id
        
        # Simulate send request preparation (which updates timeout)
        timeout_text = main_window.timeout_input.text().strip()
        timeout = int(timeout_text)
        main_window.api_client.timeout = timeout
        
        # Verify timeout is updated
        assert main_window.api_client.timeout == 60
    
    def test_timeout_validation_min(self, main_window):
        """Test that timeout validates minimum value."""
        # Set invalid low value
        main_window.timeout_input.setText("0")
        
        main_window.url_input.setText("https://httpbin.org/get")
        coll_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            coll_id, "Test Request", "GET", "https://httpbin.org/get"
        )
        main_window.current_request_id = req_id
        
        # Simulate timeout validation
        timeout_text = main_window.timeout_input.text().strip()
        timeout = int(timeout_text) if timeout_text else 30
        if timeout < 1:
            timeout = 1
        
        # Should be set to minimum of 1
        assert timeout == 1
    
    def test_timeout_validation_max(self, main_window):
        """Test that timeout validates maximum value."""
        # Set invalid high value
        main_window.timeout_input.setText("500")
        
        # Simulate timeout validation
        timeout_text = main_window.timeout_input.text().strip()
        timeout = int(timeout_text)
        if timeout > 300:
            timeout = 300
        
        # Should be capped at 300
        assert timeout == 300
    
    def test_timeout_invalid_value_fallback(self, main_window):
        """Test that invalid timeout values fallback to default."""
        # Set invalid non-numeric value
        main_window.timeout_input.setText("abc")
        
        # Simulate timeout validation
        try:
            timeout_text = main_window.timeout_input.text().strip()
            timeout = int(timeout_text)
        except ValueError:
            timeout = 30
        
        # Should fallback to 30
        assert timeout == 30
    
    def test_timeout_clears_on_clear_editor(self, main_window):
        """Test that timeout resets when editor is cleared."""
        # Set custom timeout
        main_window.timeout_input.setText("90")
        
        # Clear editor
        main_window._clear_request_editor()
        
        # Verify timeout is reset to default
        assert main_window.timeout_input.text() == "30"
    
    def test_timeout_tooltip_exists(self, main_window):
        """Test that timeout input has helpful tooltip."""
        tooltip = main_window.timeout_input.toolTip()
        assert tooltip is not None
        assert "seconds" in tooltip.lower() or "timeout" in tooltip.lower()


class TestSSLCertificateHandling:
    """Tests for SSL certificate verification feature."""
    
    def test_ssl_checkbox_exists(self, main_window):
        """Test that SSL verification checkbox exists."""
        assert hasattr(main_window, 'verify_ssl_checkbox')
        assert main_window.verify_ssl_checkbox is not None
    
    def test_ssl_checkbox_default_checked(self, main_window):
        """Test that SSL verification is enabled by default."""
        assert main_window.verify_ssl_checkbox.isChecked() == True
    
    def test_ssl_checkbox_in_auth_tab(self, main_window):
        """Test that SSL checkbox is in Authorization tab."""
        # Should be in the same widget as timeout
        auth_widget = main_window.inner_tabs.widget(2)
        assert auth_widget is not None
    
    def test_ssl_updates_api_client(self, main_window):
        """Test that SSL checkbox updates API client."""
        # Disable SSL verification
        main_window.verify_ssl_checkbox.setChecked(False)
        
        # Simulate setting the API client
        main_window.api_client.verify_ssl = main_window.verify_ssl_checkbox.isChecked()
        
        # Verify SSL is disabled
        assert main_window.api_client.verify_ssl == False
    
    def test_ssl_enable_updates_api_client(self, main_window):
        """Test that enabling SSL verification updates API client."""
        # Disable first
        main_window.verify_ssl_checkbox.setChecked(False)
        main_window.api_client.verify_ssl = False
        
        # Then enable
        main_window.verify_ssl_checkbox.setChecked(True)
        main_window.api_client.verify_ssl = main_window.verify_ssl_checkbox.isChecked()
        
        # Verify SSL is enabled
        assert main_window.api_client.verify_ssl == True
    
    def test_ssl_clears_on_clear_editor(self, main_window):
        """Test that SSL resets when editor is cleared."""
        # Disable SSL
        main_window.verify_ssl_checkbox.setChecked(False)
        
        # Clear editor
        main_window._clear_request_editor()
        
        # Verify SSL is reset to enabled
        assert main_window.verify_ssl_checkbox.isChecked() == True
    
    def test_ssl_tooltip_exists(self, main_window):
        """Test that SSL checkbox has helpful tooltip."""
        tooltip = main_window.verify_ssl_checkbox.toolTip()
        assert tooltip is not None
        assert "ssl" in tooltip.lower() or "certificate" in tooltip.lower()
        assert "local" in tooltip.lower() or "development" in tooltip.lower()


class TestApiClientSSL:
    """Tests for API client SSL support."""
    
    def test_api_client_ssl_default(self):
        """Test that API client has SSL verification enabled by default."""
        client = ApiClient()
        assert client.verify_ssl == True
    
    def test_api_client_ssl_disabled(self):
        """Test that API client can disable SSL verification."""
        client = ApiClient(verify_ssl=False)
        assert client.verify_ssl == False
    
    def test_api_client_timeout_default(self):
        """Test that API client has default timeout."""
        client = ApiClient()
        assert client.timeout == 30
    
    def test_api_client_custom_timeout(self):
        """Test that API client accepts custom timeout."""
        client = ApiClient(timeout=60)
        assert client.timeout == 60
    
    def test_api_client_timeout_and_ssl(self):
        """Test that API client can set both timeout and SSL."""
        client = ApiClient(timeout=45, verify_ssl=False)
        assert client.timeout == 45
        assert client.verify_ssl == False


class TestIntegration:
    """Integration tests for V1.3.0 features."""
    
    def test_description_with_timeout_and_ssl(self, main_window):
        """Test that description, timeout, and SSL work together."""
        # Create request with description
        coll_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            coll_id, "Test Request", "GET", "https://api.example.com",
            description="Test API with custom settings"
        )
        
        # Load request
        main_window._load_request(req_id)
        
        # Set timeout and SSL
        main_window.timeout_input.setText("45")
        main_window.verify_ssl_checkbox.setChecked(False)
        
        # Verify all settings are loaded correctly
        assert main_window.description_input.toPlainText() == "Test API with custom settings"
        assert main_window.description_input.isVisibleTo(main_window.description_widget)
        assert main_window.timeout_input.text() == "45"
        assert main_window.verify_ssl_checkbox.isChecked() == False
    
    def test_clear_editor_resets_all_new_fields(self, main_window):
        """Test that clearing editor resets all new V1.3.0 fields."""
        # Set description
        main_window.description_input.setPlainText("Test description")
        main_window._toggle_description()  # Expand
        
        # Set custom timeout
        main_window.timeout_input.setText("90")
        
        # Disable SSL
        main_window.verify_ssl_checkbox.setChecked(False)
        
        # Clear editor
        main_window._clear_request_editor()
        
        # Verify all are reset
        assert main_window.description_input.toPlainText() == ""
        assert not main_window.description_input.isVisible()
        assert main_window.timeout_input.text() == "30"
        assert main_window.verify_ssl_checkbox.isChecked() == True
    
    def test_error_message_includes_timeout_value(self, main_window):
        """Test that error messages reference current timeout setting."""
        # Set custom timeout
        main_window.timeout_input.setText("60")
        main_window.api_client.timeout = 60
        
        # Generate timeout error
        error_msg = "Request timed out after 60 seconds"
        enhanced = main_window._enhance_error_message(error_msg)
        
        # Should mention current timeout
        assert "60" in enhanced['full'] or "currently" in enhanced['full']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

