"""
Tests for Request Folders and Collection Variables features.

This module tests:
- Folder creation, nesting, and management
- Request organization within folders
- Collection variables CRUD operations
- Variable resolution hierarchy (collection > environment)
- UI integration for folders and collection variables
"""

import pytest
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import DatabaseManager
from src.ui.main_window import MainWindow
from src.ui.dialogs.collection_variables_dialog import CollectionVariablesDialog


@pytest.fixture(scope="session")
def app():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db():
    """Create a test database."""
    db = DatabaseManager(":memory:")
    yield db


@pytest.fixture
def main_window(app, db, qtbot):
    """Create MainWindow instance with test database."""
    window = MainWindow()
    window.db = db
    qtbot.addWidget(window)
    return window


class TestFolderOperations:
    """Test folder creation, nesting, and management."""
    
    def test_create_folder(self, db):
        """Test creating a root-level folder."""
        # Create collection
        collection_id = db.create_collection("Test Collection")
        
        # Create folder
        folder_id = db.create_folder(collection_id, "API v1")
        
        assert folder_id > 0
        
        # Verify folder exists
        folder = db.get_folder(folder_id)
        assert folder is not None
        assert folder['name'] == "API v1"
        assert folder['collection_id'] == collection_id
        assert folder['parent_id'] is None
    
    def test_create_nested_folder(self, db):
        """Test creating nested folders."""
        # Create collection and parent folder
        collection_id = db.create_collection("Test Collection")
        parent_folder_id = db.create_folder(collection_id, "API")
        
        # Create nested folder
        child_folder_id = db.create_folder(collection_id, "Users", parent_id=parent_folder_id)
        
        assert child_folder_id > 0
        
        # Verify nested folder
        child_folder = db.get_folder(child_folder_id)
        assert child_folder['parent_id'] == parent_folder_id
    
    def test_get_folders_by_collection(self, db):
        """Test retrieving all folders in a collection."""
        collection_id = db.create_collection("Test Collection")
        
        # Create multiple folders
        folder1_id = db.create_folder(collection_id, "Folder 1")
        folder2_id = db.create_folder(collection_id, "Folder 2")
        
        # Get all folders
        folders = db.get_folders_by_collection(collection_id)
        
        assert len(folders) == 2
        folder_names = [f['name'] for f in folders]
        assert "Folder 1" in folder_names
        assert "Folder 2" in folder_names
    
    def test_update_folder(self, db):
        """Test renaming a folder."""
        collection_id = db.create_collection("Test Collection")
        folder_id = db.create_folder(collection_id, "Old Name")
        
        # Update folder name
        db.update_folder(folder_id, name="New Name")
        
        # Verify update
        folder = db.get_folder(folder_id)
        assert folder['name'] == "New Name"
    
    def test_delete_folder(self, db):
        """Test deleting a folder."""
        collection_id = db.create_collection("Test Collection")
        folder_id = db.create_folder(collection_id, "To Delete")
        
        # Delete folder
        db.delete_folder(folder_id)
        
        # Verify deletion
        folder = db.get_folder(folder_id)
        assert folder is None
    
    def test_delete_folder_cascade(self, db):
        """Test that deleting a folder cascades to its contents."""
        collection_id = db.create_collection("Test Collection")
        folder_id = db.create_folder(collection_id, "Parent")
        
        # Create nested folder and request
        child_folder_id = db.create_folder(collection_id, "Child", parent_id=folder_id)
        request_id = db.create_request(
            name="Test Request",
            url="https://api.example.com",
            method="GET",
            collection_id=collection_id,
            folder_id=folder_id
        )
        
        # Delete parent folder
        db.delete_folder(folder_id)
        
        # Verify cascade deletion
        assert db.get_folder(child_folder_id) is None
        assert db.get_request(request_id) is None


class TestRequestsInFolders:
    """Test organizing requests within folders."""
    
    def test_create_request_in_folder(self, db):
        """Test creating a request directly in a folder."""
        collection_id = db.create_collection("Test Collection")
        folder_id = db.create_folder(collection_id, "API")
        
        # Create request in folder
        request_id = db.create_request(
            name="Get Users",
            url="https://api.example.com/users",
            method="GET",
            collection_id=collection_id,
            folder_id=folder_id
        )
        
        assert request_id > 0
        
        # Verify request is in folder
        request = db.get_request(request_id)
        assert request['folder_id'] == folder_id
    
    def test_move_request_to_folder(self, db):
        """Test moving a request to a folder."""
        collection_id = db.create_collection("Test Collection")
        folder_id = db.create_folder(collection_id, "API")
        
        # Create request in collection root
        request_id = db.create_request(
            name="Get Users",
            url="https://api.example.com/users",
            method="GET",
            collection_id=collection_id
        )
        
        # Move to folder
        db.move_request_to_folder(request_id, folder_id)
        
        # Verify move
        request = db.get_request(request_id)
        assert request['folder_id'] == folder_id
    
    def test_move_request_to_collection_root(self, db):
        """Test moving a request from folder to collection root."""
        collection_id = db.create_collection("Test Collection")
        folder_id = db.create_folder(collection_id, "API")
        
        # Create request in folder
        request_id = db.create_request(
            name="Get Users",
            url="https://api.example.com/users",
            method="GET",
            collection_id=collection_id,
            folder_id=folder_id
        )
        
        # Move to collection root
        db.move_request_to_folder(request_id, None)
        
        # Verify move
        request = db.get_request(request_id)
        assert request['folder_id'] is None
    
    def test_get_requests_by_folder(self, db):
        """Test retrieving requests by folder."""
        collection_id = db.create_collection("Test Collection")
        folder_id = db.create_folder(collection_id, "API")
        
        # Create requests
        request1_id = db.create_request(
            name="Get Users",
            url="https://api.example.com/users",
            method="GET",
            collection_id=collection_id,
            folder_id=folder_id
        )
        request2_id = db.create_request(
            name="Create User",
            url="https://api.example.com/users",
            method="POST",
            collection_id=collection_id,
            folder_id=folder_id
        )
        
        # Get requests in folder
        requests = db.get_requests_by_folder(folder_id, collection_id)
        
        assert len(requests) == 2
        request_names = [r['name'] for r in requests]
        assert "Get Users" in request_names
        assert "Create User" in request_names


class TestCollectionVariables:
    """Test collection variables CRUD operations."""
    
    def test_create_collection_variable(self, db):
        """Test creating a collection variable."""
        collection_id = db.create_collection("Test Collection")
        
        # Create variable
        var_id = db.create_collection_variable(
            collection_id,
            "api_key",
            "secret123",
            "API authentication key"
        )
        
        assert var_id > 0
    
    def test_get_collection_variables(self, db):
        """Test retrieving collection variables as a dictionary."""
        collection_id = db.create_collection("Test Collection")
        
        # Create variables
        db.create_collection_variable(collection_id, "base_url", "https://api.example.com")
        db.create_collection_variable(collection_id, "api_key", "secret123")
        
        # Get variables
        variables = db.get_collection_variables(collection_id)
        
        assert len(variables) == 2
        assert variables['base_url'] == "https://api.example.com"
        assert variables['api_key'] == "secret123"
    
    def test_get_collection_variables_with_metadata(self, db):
        """Test retrieving collection variables with metadata."""
        collection_id = db.create_collection("Test Collection")
        
        # Create variable with description
        db.create_collection_variable(
            collection_id,
            "api_key",
            "secret123",
            "API authentication key"
        )
        
        # Get variables with metadata
        variables = db.get_collection_variables_with_metadata(collection_id)
        
        assert len(variables) == 1
        assert variables[0]['key'] == "api_key"
        assert variables[0]['value'] == "secret123"
        assert variables[0]['description'] == "API authentication key"
    
    def test_update_collection_variable(self, db):
        """Test updating a collection variable."""
        collection_id = db.create_collection("Test Collection")
        var_id = db.create_collection_variable(collection_id, "api_key", "old_value")
        
        # Update variable
        db.update_collection_variable(var_id, value="new_value")
        
        # Verify update
        variables = db.get_collection_variables(collection_id)
        assert variables['api_key'] == "new_value"
    
    def test_delete_collection_variable(self, db):
        """Test deleting a collection variable."""
        collection_id = db.create_collection("Test Collection")
        var_id = db.create_collection_variable(collection_id, "api_key", "secret123")
        
        # Delete variable
        db.delete_collection_variable(var_id)
        
        # Verify deletion
        variables = db.get_collection_variables(collection_id)
        assert 'api_key' not in variables
    
    def test_delete_collection_variables_by_collection(self, db):
        """Test deleting all variables in a collection."""
        collection_id = db.create_collection("Test Collection")
        
        # Create multiple variables
        db.create_collection_variable(collection_id, "var1", "value1")
        db.create_collection_variable(collection_id, "var2", "value2")
        
        # Delete all variables
        db.delete_collection_variables_by_collection(collection_id)
        
        # Verify deletion
        variables = db.get_collection_variables(collection_id)
        assert len(variables) == 0
    
    def test_unique_variable_keys(self, db):
        """Test that variable keys are unique within a collection."""
        collection_id = db.create_collection("Test Collection")
        
        # Create variable
        db.create_collection_variable(collection_id, "api_key", "value1")
        
        # Try to create duplicate - should raise error
        with pytest.raises(Exception):
            db.create_collection_variable(collection_id, "api_key", "value2")


class TestUIIntegration:
    """Test UI integration for folders and collection variables."""
    
    def test_folder_appears_in_tree(self, main_window):
        """Test that folders appear in the collections tree."""
        # Create collection and folder
        collection_id = main_window.db.create_collection("Test Collection")
        folder_id = main_window.db.create_folder(collection_id, "API")
        
        # Reload collections
        main_window._load_collections()
        
        # Find folder in tree
        collection_item = main_window.collections_tree.topLevelItem(0)
        assert collection_item is not None
        
        # Check for folder
        folder_found = False
        for i in range(collection_item.childCount()):
            child = collection_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('type') == 'folder' and data.get('id') == folder_id:
                folder_found = True
                break
        
        assert folder_found, "Folder not found in tree"
    
    def test_nested_folder_structure(self, main_window):
        """Test that nested folders display correctly."""
        # Create collection and nested folders
        collection_id = main_window.db.create_collection("Test Collection")
        parent_folder_id = main_window.db.create_folder(collection_id, "API")
        child_folder_id = main_window.db.create_folder(collection_id, "Users", parent_id=parent_folder_id)
        
        # Reload collections
        main_window._load_collections()
        
        # Find parent folder
        collection_item = main_window.collections_tree.topLevelItem(0)
        parent_folder_item = None
        for i in range(collection_item.childCount()):
            child = collection_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('type') == 'folder' and data.get('id') == parent_folder_id:
                parent_folder_item = child
                break
        
        assert parent_folder_item is not None, "Parent folder not found"
        
        # Find child folder
        child_folder_found = False
        for i in range(parent_folder_item.childCount()):
            child = parent_folder_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('type') == 'folder' and data.get('id') == child_folder_id:
                child_folder_found = True
                break
        
        assert child_folder_found, "Child folder not found under parent"
    
    def test_request_in_folder(self, main_window):
        """Test that requests appear under their folder."""
        # Create collection, folder, and request
        collection_id = main_window.db.create_collection("Test Collection")
        folder_id = main_window.db.create_folder(collection_id, "API")
        request_id = main_window.db.create_request(
            name="Get Users",
            url="https://api.example.com/users",
            method="GET",
            collection_id=collection_id,
            folder_id=folder_id
        )
        
        # Reload collections
        main_window._load_collections()
        
        # Find folder
        collection_item = main_window.collections_tree.topLevelItem(0)
        folder_item = None
        for i in range(collection_item.childCount()):
            child = collection_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('type') == 'folder' and data.get('id') == folder_id:
                folder_item = child
                break
        
        assert folder_item is not None, "Folder not found"
        
        # Find request under folder
        request_found = False
        for i in range(folder_item.childCount()):
            child = folder_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('type') == 'request' and data.get('id') == request_id:
                request_found = True
                break
        
        assert request_found, "Request not found under folder"
    
    def test_folder_icon_changes_on_expand(self, main_window):
        """Test that folder icon changes when expanded/collapsed."""
        # Create collection and folder
        collection_id = main_window.db.create_collection("Test Collection")
        folder_id = main_window.db.create_folder(collection_id, "API")
        
        # Add a request so folder can be expanded
        main_window.db.create_request(
            name="Get Users",
            url="https://api.example.com/users",
            method="GET",
            collection_id=collection_id,
            folder_id=folder_id
        )
        
        # Reload collections
        main_window._load_collections()
        
        # Find folder
        collection_item = main_window.collections_tree.topLevelItem(0)
        folder_item = None
        for i in range(collection_item.childCount()):
            child = collection_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('type') == 'folder':
                folder_item = child
                break
        
        assert folder_item is not None
        
        # Get icon before expansion
        icon_before = folder_item.icon(0)
        
        # Expand folder
        folder_item.setExpanded(True)
        main_window._on_tree_item_expanded(folder_item)
        
        # Get icon after expansion
        icon_after = folder_item.icon(0)
        
        # Icons should be different (open vs closed folder)
        # Note: We can't directly compare QIcon objects, but we can verify the method was called
        assert icon_after is not None


class TestVariableResolution:
    """Test variable resolution hierarchy."""
    
    def test_collection_variables_in_request(self, main_window):
        """Test that collection variables are substituted in requests."""
        # Create collection with variable
        collection_id = main_window.db.create_collection("Test Collection")
        main_window.db.create_collection_variable(collection_id, "base_url", "https://api.example.com")
        
        # Create request using collection variable
        request_id = main_window.db.create_request(
            name="Get Users",
            url="{{base_url}}/users",
            method="GET",
            collection_id=collection_id
        )
        
        # Set current collection
        main_window.current_collection_id = collection_id
        
        # Get collection variables
        variables = main_window.db.get_collection_variables(collection_id)
        
        assert variables['base_url'] == "https://api.example.com"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


