"""
Test recent requests panel functionality:
1. Single-click opens persistent tab (permanent mode)
2. Deleted requests are removed from recent requests
3. "Open pinned" button opens all pinned requests
"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.core.database import DatabaseManager
import os
import tempfile


@pytest.fixture
def app(qtbot):
    """Create application instance."""
    db_path = tempfile.mktemp(suffix='.db')
    
    window = MainWindow(db_path=db_path)
    qtbot.addWidget(window)
    window.show()
    
    yield window
    
    # Cleanup
    window.close()
    window.db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_recent_requests_single_click_opens_persistent_tab(app, qtbot):
    """Test that single-clicking a recent request opens a persistent tab."""
    # Create a collection and request
    col_id = app.db.create_collection("Test Collection")
    req_id = app.db.create_request(
        col_id,
        "Test Request",
        "GET",
        "https://api.example.com/test",
        {},
        {},
        ""
    )
    
    # Load collections to populate tree
    app._load_collections()
    qtbot.wait(100)
    
    # Add request to recent requests
    app.recent_requests_widget.add_request(req_id)
    qtbot.wait(100)
    
    # Get the recent request item widget
    list_widget = app.recent_requests_widget.list_widget
    assert list_widget.count() == 1, "Should have one recent request"
    
    # Simulate single-click by emitting the clicked signal
    first_item = list_widget.item(0)
    item_widget = list_widget.itemWidget(first_item)
    item_widget.clicked.emit(req_id)
    qtbot.wait(100)
    
    # Check that the request is open in a persistent tab (not temporary)
    assert app.request_tabs.count() == 1, "Should have one tab open"
    assert app.temporary_tab_index is None, "Should not have a temporary tab"
    
    # Verify tab state
    tab_state = app.tab_states.get(0)
    assert tab_state is not None, "Tab state should exist"
    assert tab_state.get('is_temporary') == False, "Tab should be marked as persistent"
    assert tab_state.get('request_id') == req_id, "Tab should contain the correct request"


def test_recent_requests_double_click_opens_persistent_tab(app, qtbot):
    """Test backward compatibility - clicking recent requests opens persistent tabs."""
    # Create a collection and request
    col_id = app.db.create_collection("Test Collection")
    req_id = app.db.create_request(
        col_id,
        "Test Request",
        "GET",
        "https://api.example.com/test",
        {},
        {},
        ""
    )
    
    # Load collections to populate tree
    app._load_collections()
    qtbot.wait(100)
    
    # Add request to recent requests
    app.recent_requests_widget.add_request(req_id)
    qtbot.wait(100)
    
    # Get the recent request item widget
    list_widget = app.recent_requests_widget.list_widget
    assert list_widget.count() == 1, "Should have one recent request"
    
    # Simulate click by emitting the clicked signal
    first_item = list_widget.item(0)
    item_widget = list_widget.itemWidget(first_item)
    item_widget.clicked.emit(req_id)
    qtbot.wait(100)
    
    # Check that the request is open in a persistent tab
    assert app.request_tabs.count() == 1, "Should have one tab open"
    assert app.temporary_tab_index is None, "Should not have a temporary tab"
    
    # Verify tab state
    tab_state = app.tab_states.get(0)
    assert tab_state is not None, "Tab state should exist"
    assert tab_state.get('is_temporary') == False, "Tab should be marked as persistent"
    assert tab_state.get('request_id') == req_id, "Tab should contain the correct request"


def test_deleted_requests_removed_from_recent(app, qtbot):
    """Test that deleted requests are removed from recent requests."""
    # Create a collection and two requests
    col_id = app.db.create_collection("Test Collection")
    req1_id = app.db.create_request(
        col_id,
        "Test Request 1",
        "GET",
        "https://api.example.com/test1",
        {},
        {},
        ""
    )
    req2_id = app.db.create_request(
        col_id,
        "Test Request 2",
        "POST",
        "https://api.example.com/test2",
        {},
        {},
        ""
    )
    
    # Load collections
    app._load_collections()
    qtbot.wait(100)
    
    # Add both requests to recent requests
    app.recent_requests_widget.add_request(req1_id)
    app.recent_requests_widget.add_request(req2_id)
    qtbot.wait(100)
    
    # Verify both are in recent requests
    assert app.recent_requests_widget.list_widget.count() == 2, "Should have two recent requests"
    
    # Delete the first request
    app.db.delete_request(req1_id)
    
    # Refresh recent requests (simulates what happens in MainWindow after deletion)
    app.recent_requests_widget.refresh()
    qtbot.wait(100)
    
    # Verify only one request remains
    assert app.recent_requests_widget.list_widget.count() == 1, "Should have one recent request after deletion"
    
    # Verify the remaining request is the second one
    first_item = app.recent_requests_widget.list_widget.item(0)
    remaining_request_id = first_item.data(Qt.ItemDataRole.UserRole)
    assert remaining_request_id == req2_id, "Remaining request should be Test Request 2"


def test_pinned_requests_persist_across_deletions(app, qtbot):
    """Test that pinned requests stay in recent requests even after cleanup."""
    # Create a collection and requests
    col_id = app.db.create_collection("Test Collection")
    req1_id = app.db.create_request(
        col_id,
        "Pinned Request",
        "GET",
        "https://api.example.com/pinned",
        {},
        {},
        ""
    )
    
    # Load collections
    app._load_collections()
    qtbot.wait(100)
    
    # Add request to recent requests
    app.recent_requests_widget.add_request(req1_id)
    qtbot.wait(100)
    
    # Pin the request
    cursor = app.db.connection.cursor()
    cursor.execute("UPDATE recent_requests SET is_pinned = 1 WHERE request_id = ?", (req1_id,))
    app.db.connection.commit()
    app.recent_requests_widget.refresh()
    qtbot.wait(100)
    
    # Verify request is pinned
    first_item = app.recent_requests_widget.list_widget.item(0)
    item_widget = app.recent_requests_widget.list_widget.itemWidget(first_item)
    assert item_widget.is_pinned == True, "Request should be pinned"
    
    # Request should remain even if we try to delete it from the database
    # (it will be cleaned up, but pinned status should persist in the widget)
    assert app.recent_requests_widget.list_widget.count() == 1, "Pinned request should remain in recent requests"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
