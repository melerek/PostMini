"""
Test authorization widget visibility when loading requests.

This test verifies the fix for the bug where authorization fields
were not visible when loading a request with Bearer Token auth.
"""

import pytest
import json
from src.ui.main_window import MainWindow
from src.core.database import DatabaseManager


@pytest.fixture
def main_window(qtbot, tmp_path):
    """Create a MainWindow instance with a test database."""
    db_path = tmp_path / "test_auth_visibility.db"
    window = MainWindow(db_path=str(db_path))
    qtbot.addWidget(window)
    window.show()
    return window


class TestAuthorizationVisibility:
    """Test authorization widget visibility."""

    def test_bearer_token_visible_on_load(self, main_window, qtbot):
        """Test that Bearer Token widget is visible when loading a request with Bearer auth."""
        # Create a collection
        col_id = main_window.db.create_collection("Test Collection")
        
        # Create a request with Bearer Token auth
        req_id = main_window.db.create_request(
            name="Test Bearer Request",
            method="GET",
            url="https://api.example.com/test",
            collection_id=col_id,
            auth_type="Bearer Token",
            auth_token="test_token_123"
        )
        
        # Load the request using the internal method
        main_window._open_request_in_new_tab(req_id, is_temporary=False)
        qtbot.wait(100)  # Wait for UI updates
        
        # Switch to the Authorization tab (index 2: 0=Params, 1=Headers, 2=Authorization)
        main_window.inner_tabs.setCurrentIndex(2)
        qtbot.wait(50)
        
        # Verify auth type is set correctly
        assert main_window.auth_type_combo.currentText() == "Bearer Token"
        
        # Verify Bearer Token widget is visible
        assert main_window.bearer_token_widget.isVisible(), "Bearer Token widget should be visible"
        
        # Verify OAuth widget is NOT visible
        assert not main_window.oauth_widget.isVisible(), "OAuth widget should be hidden"
        
        # Verify token value is loaded
        assert main_window.auth_token_input.text() == "test_token_123"

    def test_no_auth_visible_on_load(self, main_window, qtbot):
        """Test that no auth widgets are visible when loading a request with None auth."""
        # Create a collection
        col_id = main_window.db.create_collection("Test Collection")
        
        # Create a request with no auth
        req_id = main_window.db.create_request(
            name="Test No Auth Request",
            method="GET",
            url="https://api.example.com/test",
            collection_id=col_id,
            auth_type="None"
        )
        
        # Load the request using the internal method
        main_window._open_request_in_new_tab(req_id, is_temporary=False)
        qtbot.wait(100)
        
        # Switch to the Authorization tab
        main_window.inner_tabs.setCurrentIndex(2)
        qtbot.wait(50)
        
        # Verify auth type is set correctly
        assert main_window.auth_type_combo.currentText() == "None"
        
        # Verify both auth widgets are NOT visible
        assert not main_window.bearer_token_widget.isVisible(), "Bearer Token widget should be hidden"
        assert not main_window.oauth_widget.isVisible(), "OAuth widget should be hidden"

    def test_auth_visibility_on_tab_restore(self, main_window, qtbot):
        """Test that auth widgets are visible when restoring tab state."""
        # Create a collection and request
        col_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            name="Test Request",
            method="POST",
            url="https://api.example.com/auth",
            collection_id=col_id,
            auth_type="Bearer Token",
            auth_token="secret_token_456"
        )
        
        # Load the request using the internal method
        main_window._open_request_in_new_tab(req_id, is_temporary=False)
        qtbot.wait(100)
        
        # Capture the tab state
        state = main_window._capture_current_tab_state()
        
        # Create a new tab
        main_window._create_new_tab()
        qtbot.wait(100)
        
        # Verify Bearer Token widget is NOT visible (new empty tab)
        assert not main_window.bearer_token_widget.isVisible()
        
        # Restore the previous tab state
        main_window._restore_tab_state(state)
        qtbot.wait(100)
        
        # Switch to the Authorization tab
        main_window.inner_tabs.setCurrentIndex(2)
        qtbot.wait(50)
        
        # Verify auth type is restored
        assert main_window.auth_type_combo.currentText() == "Bearer Token"
        
        # Verify Bearer Token widget IS visible after restore
        assert main_window.bearer_token_widget.isVisible(), "Bearer Token widget should be visible after tab restore"
        
        # Verify token value is restored
        assert main_window.auth_token_input.text() == "secret_token_456"

    def test_switching_auth_types(self, main_window, qtbot):
        """Test that widget visibility updates correctly when switching auth types."""
        # Create a minimal request to have a tab context
        col_id = main_window.db.create_collection("Test Collection")
        req_id = main_window.db.create_request(
            name="Test Request",
            method="GET",
            url="https://api.example.com",
            collection_id=col_id
        )
        main_window._open_request_in_new_tab(req_id, is_temporary=False)
        qtbot.wait(100)
        
        # Switch to Authorization tab
        main_window.inner_tabs.setCurrentIndex(2)
        qtbot.wait(50)
        
        # Start with Bearer Token
        main_window.auth_type_combo.setCurrentText("Bearer Token")
        qtbot.wait(50)
        
        assert main_window.bearer_token_widget.isVisible()
        assert not main_window.oauth_widget.isVisible()
        
        # Switch to OAuth 2.0
        main_window.auth_type_combo.setCurrentText("OAuth 2.0")
        qtbot.wait(50)
        
        assert not main_window.bearer_token_widget.isVisible()
        assert main_window.oauth_widget.isVisible()
        
        # Switch to None
        main_window.auth_type_combo.setCurrentText("None")
        qtbot.wait(50)
        
        assert not main_window.bearer_token_widget.isVisible()
        assert not main_window.oauth_widget.isVisible()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
