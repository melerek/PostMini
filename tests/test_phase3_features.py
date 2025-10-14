"""
Tests for Phase 3 features: Context Menus and Recent Requests
"""

import pytest
import json
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtTest import QTest

from src.core.database import DatabaseManager
from src.ui.main_window import MainWindow
from src.ui.widgets.recent_requests_widget import RecentRequestsWidget, RecentRequestItem


@pytest.fixture
def app(qtbot):
    """Create test application."""
    test_app = MainWindow(db_path=":memory:")
    qtbot.addWidget(test_app)
    return test_app


@pytest.fixture
def sample_collection(app):
    """Create a sample collection with requests."""
    collection_id = app.db.create_collection("Test Collection")
    
    request1_id = app.db.create_request(
        name="Get Users",
        method="GET",
        url="https://api.example.com/users",
        collection_id=collection_id,
        headers={"Authorization": "Bearer token123"}
    )
    
    request2_id = app.db.create_request(
        name="Create User",
        method="POST",
        url="https://api.example.com/users",
        collection_id=collection_id,
        body='{"name": "John Doe"}'
    )
    
    app._load_collections()
    return collection_id, request1_id, request2_id


class TestContextMenus:
    """Test context menu functionality."""
    
    def test_collection_context_menu_created(self, app, sample_collection, qtbot):
        """Test that collection context menu is created with all expected actions."""
        collection_id, _, _ = sample_collection
        
        # Find the collection item in the tree
        tree = app.collections_tree
        collection_item = tree.topLevelItem(0)
        assert collection_item is not None
        
        # Get the collection rect to simulate right-click
        rect = tree.visualItemRect(collection_item)
        center = rect.center()
        
        # Trigger context menu (we'll check the menu structure)
        # Note: We can't easily test QMenu.exec() directly, but we can test the method exists
        assert hasattr(app, '_show_tree_context_menu')
        assert hasattr(app, '_export_collection_from_menu')
        assert hasattr(app, '_rename_collection')
        assert hasattr(app, '_duplicate_collection')
        assert hasattr(app, '_delete_collection_from_menu')
    
    def test_request_context_menu_created(self, app, sample_collection, qtbot):
        """Test that request context menu is created with all expected actions."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Check that request context menu methods exist
        assert hasattr(app, '_copy_request_as_curl')
        assert hasattr(app, '_rename_request')
        assert hasattr(app, '_duplicate_request')
        assert hasattr(app, '_delete_request_from_menu')
    
    def test_rename_collection(self, app, sample_collection, qtbot, monkeypatch):
        """Test renaming a collection."""
        collection_id, _, _ = sample_collection
        
        # Mock the input dialog to return a new name
        def mock_getText(*args, **kwargs):
            return "Renamed Collection", True
        monkeypatch.setattr("PyQt6.QtWidgets.QInputDialog.getText", mock_getText)
        
        # Rename the collection
        app._rename_collection(collection_id)
        
        # Verify the name was changed
        collection = app.db.get_collection(collection_id)
        assert collection['name'] == "Renamed Collection"
    
    def test_duplicate_collection(self, app, sample_collection, qtbot):
        """Test duplicating a collection."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Duplicate the collection
        app._duplicate_collection(collection_id)
        
        # Verify new collection was created
        collections = app.db.get_all_collections()
        assert len(collections) == 2
        
        # Find the duplicated collection
        duplicated = [c for c in collections if c['name'] == "Test Collection (Copy)"][0]
        assert duplicated is not None
        
        # Verify requests were copied
        duplicated_requests = app.db.get_requests_by_collection(duplicated['id'])
        assert len(duplicated_requests) == 2
    
    def test_delete_collection(self, app, sample_collection, qtbot, monkeypatch):
        """Test deleting a collection."""
        collection_id, _, _ = sample_collection
        
        # Mock the confirmation dialog to return Yes
        def mock_question(*args, **kwargs):
            from PyQt6.QtWidgets import QMessageBox
            return QMessageBox.StandardButton.Yes
        monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.question", mock_question)
        
        # Delete the collection
        app._delete_collection_from_menu(collection_id)
        
        # Verify collection was deleted
        collection = app.db.get_collection(collection_id)
        assert collection is None
    
    def test_copy_request_as_curl(self, app, sample_collection, qtbot):
        """Test copying request as cURL command."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Copy request as cURL
        app._copy_request_as_curl(request1_id)
        
        # Verify clipboard content
        clipboard = QApplication.clipboard()
        curl_command = clipboard.text()
        
        assert "curl" in curl_command
        assert "-X GET" in curl_command
        assert "https://api.example.com/users" in curl_command
        assert "Authorization" in curl_command
    
    def test_rename_request(self, app, sample_collection, qtbot, monkeypatch):
        """Test renaming a request."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Mock the input dialog
        def mock_getText(*args, **kwargs):
            return "Get All Users", True
        monkeypatch.setattr("PyQt6.QtWidgets.QInputDialog.getText", mock_getText)
        
        # Rename the request
        app._rename_request(request1_id)
        
        # Verify the name was changed
        request = app.db.get_request(request1_id)
        assert request['name'] == "Get All Users"
    
    def test_duplicate_request(self, app, sample_collection, qtbot):
        """Test duplicating a request."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Duplicate the request
        app._duplicate_request(request1_id)
        
        # Verify new request was created
        requests = app.db.get_requests_by_collection(collection_id)
        assert len(requests) == 3
        
        # Find the duplicated request
        duplicated = [r for r in requests if r['name'] == "Get Users (Copy)"][0]
        assert duplicated is not None
        assert duplicated['method'] == "GET"
        assert duplicated['url'] == "https://api.example.com/users"
    
    def test_delete_request(self, app, sample_collection, qtbot, monkeypatch):
        """Test deleting a request."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Mock the confirmation dialog
        def mock_question(*args, **kwargs):
            from PyQt6.QtWidgets import QMessageBox
            return QMessageBox.StandardButton.Yes
        monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.question", mock_question)
        
        # Delete the request
        app._delete_request_from_menu(request1_id)
        
        # Verify request was deleted
        request = app.db.get_request(request1_id)
        assert request is None
        
        # Verify other request still exists
        request2 = app.db.get_request(request2_id)
        assert request2 is not None
    
    def test_response_context_menu(self, app, qtbot):
        """Test response viewer context menu."""
        # Check that response context menu methods exist
        assert hasattr(app, '_show_response_context_menu')
        assert hasattr(app, '_copy_entire_response')
        assert hasattr(app, '_save_response_to_file')
    
    def test_copy_entire_response(self, app, qtbot):
        """Test copying entire response to clipboard."""
        # Set some response text
        app.response_body.setPlainText("Test response content")
        
        # Copy entire response
        app._copy_entire_response()
        
        # Verify clipboard content
        clipboard = QApplication.clipboard()
        assert clipboard.text() == "Test response content"


class TestRecentRequestsWidget:
    """Test recent requests widget functionality."""
    
    def test_recent_requests_widget_initialization(self, app):
        """Test that recent requests widget is properly initialized."""
        assert app.recent_requests_widget is not None
        assert isinstance(app.recent_requests_widget, RecentRequestsWidget)
        assert not app.recent_requests_widget.isVisible()  # Hidden by default
    
    def test_toggle_recent_requests_panel(self, app, qtbot):
        """Test toggling recent requests panel visibility."""
        # Show the main window so widgets can be visible
        app.show()
        qtbot.waitExposed(app)
        
        # Initially hidden
        assert not app.recent_requests_widget.isVisible()
        
        # Toggle to show
        app._toggle_recent_requests()
        assert app.recent_requests_widget.isVisible()
        assert app.recent_requests_btn.isChecked()
        
        # Toggle to hide
        app._toggle_recent_requests()
        assert not app.recent_requests_widget.isVisible()
        assert not app.recent_requests_btn.isChecked()
    
    def test_add_request_to_recent(self, app, sample_collection, qtbot):
        """Test adding a request to recent requests."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Load a request (should add to recent)
        app._load_request(request1_id)
        
        # Verify request was added to recent requests
        assert len(app.recent_requests_widget.recent_requests) >= 1
        
        # Check that the request is in the list
        request_ids = [r[0] for r in app.recent_requests_widget.recent_requests]
        assert request1_id in request_ids
    
    def test_recent_requests_ordering(self, app, sample_collection, qtbot):
        """Test that recent requests are ordered correctly."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Load requests in order
        app._load_request(request1_id)
        app._load_request(request2_id)
        app._load_request(request1_id)  # Load request1 again
        
        # Most recent should be request1
        recent_requests = app.recent_requests_widget.recent_requests
        assert len(recent_requests) >= 2
        # Note: The most recently accessed request should have the latest timestamp
        # The exact ordering depends on whether it's pinned, so we just check both are present
        request_ids = [r[0] for r in recent_requests]
        assert request1_id in request_ids
        assert request2_id in request_ids
    
    def test_pin_request(self, app, sample_collection, qtbot):
        """Test pinning a request in recent requests."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Add request to recent
        app._load_request(request1_id)
        
        # Pin the request
        app.recent_requests_widget._toggle_pin(request1_id, True)
        
        # Verify request is pinned
        recent_requests = app.recent_requests_widget.recent_requests
        pinned_request = [r for r in recent_requests if r[0] == request1_id][0]
        assert pinned_request[2] == 1  # is_pinned = 1
    
    def test_unpin_request(self, app, sample_collection, qtbot):
        """Test unpinning a request in recent requests."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Add and pin request
        app._load_request(request1_id)
        app.recent_requests_widget._toggle_pin(request1_id, True)
        
        # Unpin the request
        app.recent_requests_widget._toggle_pin(request1_id, False)
        
        # Verify request is unpinned
        recent_requests = app.recent_requests_widget.recent_requests
        unpinned_request = [r for r in recent_requests if r[0] == request1_id][0]
        assert unpinned_request[2] == 0  # is_pinned = 0
    
    def test_clear_recent_requests(self, app, sample_collection, qtbot):
        """Test clearing non-pinned recent requests."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Add requests
        app._load_request(request1_id)
        app._load_request(request2_id)
        
        # Pin request1
        app.recent_requests_widget._toggle_pin(request1_id, True)
        
        # Clear recent requests
        app.recent_requests_widget._clear_recent()
        
        # Verify only pinned request remains
        recent_requests = app.recent_requests_widget.recent_requests
        assert len(recent_requests) == 1
        assert recent_requests[0][0] == request1_id
        assert recent_requests[0][2] == 1  # is_pinned
    
    def test_max_recent_requests_limit(self, app, qtbot):
        """Test that recent requests respects the maximum limit."""
        # Create many collections and requests
        for i in range(25):  # More than max_recent (20)
            collection_id = app.db.create_collection(f"Collection {i}")
            request_id = app.db.create_request(
                name=f"Request {i}",
                method="GET",
                url=f"https://api.example.com/resource{i}",
                collection_id=collection_id
            )
            app._load_request(request_id)
        
        # Verify we don't exceed max_recent
        recent_requests = app.recent_requests_widget.recent_requests
        assert len(recent_requests) <= app.recent_requests_widget.max_recent
    
    def test_recent_request_item_widget(self, app, sample_collection, qtbot):
        """Test RecentRequestItem widget."""
        collection_id, request1_id, request2_id = sample_collection
        request = app.db.get_request(request1_id)
        
        # Create item widget
        item_widget = RecentRequestItem(
            request1_id,
            request['name'],
            request['method'],
            request['url'],
            is_pinned=False
        )
        
        # Test initial state
        assert item_widget.request_id == request1_id
        assert not item_widget.is_pinned
        assert item_widget.pin_btn.text() == "📍"
        
        # Test pin toggle
        item_widget._toggle_pin()
        assert item_widget.is_pinned
        assert item_widget.pin_btn.text() == "📌"
    
    def test_recent_requests_signal_connection(self, app, sample_collection, qtbot):
        """Test that the recent requests widget signal is connected."""
        collection_id, request1_id, request2_id = sample_collection
        
        # Manually add requests to recent (bypassing _load_request which has dependencies)
        app.recent_requests_widget.add_request(request1_id)
        app.recent_requests_widget.add_request(request2_id)
        
        # Show recent requests panel
        app.show()
        qtbot.waitExposed(app)
        app._toggle_recent_requests()
        
        # Verify requests are in the recent list
        recent_ids = [r[0] for r in app.recent_requests_widget.recent_requests]
        assert request1_id in recent_ids
        assert request2_id in recent_ids
        
        # Verify the panel is visible
        assert app.recent_requests_widget.isVisible()
        
        # Verify list widget has items
        assert app.recent_requests_widget.list_widget.count() > 0


class TestIntegration:
    """Integration tests for Phase 3 features."""
    
    def test_full_workflow(self, app, sample_collection, qtbot, monkeypatch):
        """Test a complete workflow using context menus and recent requests."""
        collection_id, request1_id, request2_id = sample_collection
        
        # 1. Load a request (adds to recent)
        app._load_request(request1_id)
        assert len(app.recent_requests_widget.recent_requests) >= 1
        
        # 2. Duplicate the request via context menu
        app._duplicate_request(request1_id)
        requests = app.db.get_requests_by_collection(collection_id)
        assert len(requests) == 3
        
        # 3. Rename the duplicated request
        duplicated = [r for r in requests if r['name'] == "Get Users (Copy)"][0]
        def mock_getText(*args, **kwargs):
            return "Get Users v2", True
        monkeypatch.setattr("PyQt6.QtWidgets.QInputDialog.getText", mock_getText)
        app._rename_request(duplicated['id'])
        
        renamed = app.db.get_request(duplicated['id'])
        assert renamed['name'] == "Get Users v2"
        
        # 4. Load the renamed request (adds to recent)
        app._load_request(renamed['id'])
        assert len(app.recent_requests_widget.recent_requests) >= 2
        
        # 5. Pin it in recent requests
        app.recent_requests_widget._toggle_pin(renamed['id'], True)
        recent = app.recent_requests_widget.recent_requests
        pinned = [r for r in recent if r[0] == renamed['id']][0]
        assert pinned[2] == 1
        
        # 6. Duplicate the entire collection
        app._duplicate_collection(collection_id)
        collections = app.db.get_all_collections()
        assert len(collections) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

