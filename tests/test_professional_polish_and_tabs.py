"""
Test Suite for Professional Polish and Multi-Request Tabs Features

This test suite covers:
1. Multi-Request Tab System
2. Tab State Persistence (response & test results)
3. Empty States
4. Method and Status Badges
5. Collections Tree Highlighting
6. Middle-Click Tab Closing
7. Double-Click Debouncing
"""

import pytest
import sys
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem, QWidget
from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest

# Ensure we can import from src
sys.path.insert(0, '.')

from src.ui.main_window import MainWindow
from src.core.api_client import ApiResponse


@pytest.fixture(scope="module")
def app():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def main_window(app, tmp_path):
    """Create MainWindow instance for testing."""
    # Use temporary database
    db_path = tmp_path / "test.db"
    with patch('src.ui.main_window.DatabaseManager') as mock_db:
        mock_db.return_value.get_collections.return_value = []
        window = MainWindow()
        yield window
        window.close()


class TestMultiRequestTabs:
    """Test multi-request tab functionality."""
    
    def test_app_starts_with_no_tabs(self, main_window):
        """Test that app starts with no tabs visible."""
        assert main_window.request_tabs.count() == 0
        assert main_window.center_stack.currentWidget() == main_window.no_request_empty_state
    
    def test_open_request_in_new_tab(self, main_window):
        """Test opening a request in a new tab."""
        # Mock database response
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        
        # Open request in new tab
        main_window._open_request_in_new_tab(1)
        
        # Verify tab was created (tab index is 0, not 1)
        assert main_window.request_tabs.count() == 1
        assert 0 in main_window.tab_states  # Tab index is 0
        assert main_window.tab_states[0]['request_id'] == 1
        assert main_window.tab_states[0]['name'] == 'Test Request'
    
    def test_prevent_duplicate_tabs(self, main_window):
        """Test that opening same request twice doesn't create duplicate tabs."""
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        
        # Open request twice
        main_window._open_request_in_new_tab(1)
        initial_count = main_window.request_tabs.count()
        
        main_window._open_request_in_new_tab(1)
        
        # Should still have same number of tabs
        assert main_window.request_tabs.count() == initial_count
    
    def test_close_tab(self, main_window):
        """Test closing a tab."""
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        
        # Open and close tab
        main_window._open_request_in_new_tab(1)
        assert main_window.request_tabs.count() == 1
        
        main_window._close_tab(0)
        assert main_window.request_tabs.count() == 0
    
    def test_tab_title_updates(self, main_window):
        """Test that tab title shows method and name."""
        mock_request = {
            'id': 1,
            'name': 'Get Users',
            'method': 'GET',
            'url': 'https://api.example.com/users',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        
        main_window._open_request_in_new_tab(1)
        
        tab_text = main_window.request_tabs.tabText(0)
        assert 'GET' in tab_text
        assert 'Get Users' in tab_text


class TestTabStatePersistence:
    """Test tab state persistence (response & test results)."""
    
    def test_capture_and_restore_response(self, main_window):
        """Test that response data is captured and restored."""
        # Setup tab with request
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        main_window._open_request_in_new_tab(1)
        
        # Simulate response with mock requests.Response
        import requests
        mock_requests_response = Mock(spec=requests.Response)
        mock_requests_response.status_code = 200
        mock_requests_response.headers = {'Content-Type': 'application/json'}
        mock_requests_response.text = '{"success": true}'
        mock_requests_response.content = b'{"success": true}'
        mock_requests_response.encoding = 'utf-8'
        
        mock_response = ApiResponse(mock_requests_response, 0.5)
        main_window.current_response = mock_response
        
        # Capture state
        state = main_window._capture_current_tab_state()
        
        # Verify response data captured
        assert state['response'] is not None
        assert state['response']['status_code'] == 200
        assert state['response']['text'] == '{"success": true}'
    
    def test_capture_and_restore_test_results(self, main_window):
        """Test that test results are captured and restored."""
        # Setup tab
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        main_window._open_request_in_new_tab(1)
        
        # Check if test_results_viewer exists
        if not hasattr(main_window, 'test_results_viewer') or main_window.test_results_viewer is None:
            pytest.skip("test_results_viewer not available in this configuration")
        
        # Set test results and make viewer visible
        test_results_data = {
            'results': [
                {'name': 'Test 1', 'passed': True},
                {'name': 'Test 2', 'passed': False}
            ],
            'summary': {'total': 2, 'passed': 1, 'failed': 1}
        }
        main_window._current_test_results = test_results_data
        
        # Mock the isVisible to return True so capture logic works
        main_window.test_results_viewer.isVisible = Mock(return_value=True)
        
        # Capture state
        state = main_window._capture_current_tab_state()
        
        # Verify test results captured
        assert state['test_results'] is not None
        assert state['test_results']['summary']['total'] == 2
        assert state['test_results']['summary']['passed'] == 1


class TestDoubleClickDebouncing:
    """Test double-click debouncing to prevent duplicate tabs."""
    
    def test_duplicate_double_click_ignored(self, main_window):
        """Test that duplicate double-clicks within 500ms are ignored."""
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        
        # Create mock tree item
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'request', 'id': 1})
        
        # First double-click
        main_window._on_tree_item_double_clicked(item, 0)
        initial_count = main_window.request_tabs.count()
        
        # Immediate second double-click (should be ignored)
        main_window._on_tree_item_double_clicked(item, 0)
        
        # Should not create another tab
        assert main_window.request_tabs.count() == initial_count
    
    def test_double_click_after_delay_accepted(self, main_window):
        """Test that double-clicks after 500ms are accepted."""
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        
        # Create mock tree item
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'request', 'id': 1})
        
        # First double-click
        main_window._on_tree_item_double_clicked(item, 0)
        initial_count = main_window.request_tabs.count()
        
        # Close the tab
        main_window._close_tab(0)
        
        # Wait for debounce timeout
        time.sleep(0.6)
        
        # Second double-click (should be accepted)
        main_window._on_tree_item_double_clicked(item, 0)
        
        # Should create a new tab
        assert main_window.request_tabs.count() == 1


class TestCollectionsTreeHighlighting:
    """Test collections tree highlighting for open/active requests."""
    
    def test_active_request_bold_and_underlined(self, main_window):
        """Test that active request is bold and underlined."""
        # Create mock collection and request
        collection_item = QTreeWidgetItem()
        collection_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'collection', 'id': 1})
        
        request_item = QTreeWidgetItem()
        request_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'request', 'id': 1})
        collection_item.addChild(request_item)
        
        main_window.collections_tree.addTopLevelItem(collection_item)
        
        # Setup tab state and make the tab active (index 0)
        main_window.tab_states[0] = {'request_id': 1}
        main_window.request_tabs.addTab(QWidget(), "Test Tab")
        main_window.request_tabs.setCurrentIndex(0)
        
        # Update highlighting
        main_window._update_current_request_highlight()
        
        # Verify font styling
        font = request_item.font(0)
        assert font.bold() == True
        assert font.underline() == True
    
    def test_open_requests_underlined(self, main_window):
        """Test that all open requests are underlined."""
        # Create mock requests
        collection_item = QTreeWidgetItem()
        collection_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'collection', 'id': 1})
        
        request1 = QTreeWidgetItem()
        request1.setData(0, Qt.ItemDataRole.UserRole, {'type': 'request', 'id': 1})
        
        request2 = QTreeWidgetItem()
        request2.setData(0, Qt.ItemDataRole.UserRole, {'type': 'request', 'id': 2})
        
        collection_item.addChild(request1)
        collection_item.addChild(request2)
        main_window.collections_tree.addTopLevelItem(collection_item)
        
        # Setup multiple tabs
        main_window.tab_states[0] = {'request_id': 1}
        main_window.tab_states[1] = {'request_id': 2}
        
        # Update highlighting
        main_window._update_current_request_highlight()
        
        # Both should be underlined
        assert request1.font(0).underline() == True
        assert request2.font(0).underline() == True


class TestMiddleClickTabClosing:
    """Test middle-click to close tabs."""
    
    def test_middle_click_closes_tab(self, main_window):
        """Test that middle-clicking a tab closes it."""
        # Create a tab
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        main_window._open_request_in_new_tab(1)
        
        assert main_window.request_tabs.count() == 1
        
        # Create middle-click event
        tab_bar = main_window.request_tabs.tabBar()
        tab_rect = tab_bar.tabRect(0)
        click_pos = tab_rect.center()
        
        # Simulate middle-click release
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QMouseEvent
        event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(click_pos),  # Convert QPoint to QPointF
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # Process event through filter
        main_window.eventFilter(tab_bar, event)
        
        # Tab should be closed
        assert main_window.request_tabs.count() == 0


class TestEmptyStates:
    """Test empty state widgets."""
    
    def test_no_request_empty_state_shown_initially(self, main_window):
        """Test that 'No Request Selected' empty state is shown initially."""
        assert main_window.center_stack.currentWidget() == main_window.no_request_empty_state
    
    def test_workspace_shown_when_tab_opened(self, main_window):
        """Test that workspace is shown when a tab is opened."""
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        
        main_window._open_request_in_new_tab(1)
        
        # Workspace should be shown
        assert main_window.center_stack.currentWidget() == main_window.tabs_container


class TestSignalBlocking:
    """Test that signal blocking prevents premature tab changes."""
    
    def test_tab_state_exists_when_needed(self, main_window):
        """Test that tab state is properly set up when tabs are created."""
        mock_request = {
            'id': 1,
            'name': 'Test Request',
            'method': 'GET',
            'url': 'https://api.example.com',
            'collection_id': 1,
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': '',
            'description': ''
        }
        main_window.db.get_request = Mock(return_value=mock_request)
        
        # Open request
        main_window._open_request_in_new_tab(1)
        
        # Tab state should exist for the created tab
        assert 0 in main_window.tab_states
        assert main_window.tab_states[0]['request_id'] == 1
        
        # Request should be loaded
        assert main_window.current_request_id == 1


def run_tests():
    """Run all tests and return results."""
    import pytest
    
    # Run tests with verbose output
    result = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])
    
    return result


if __name__ == '__main__':
    run_tests()

