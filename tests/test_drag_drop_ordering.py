"""
Tests for drag & drop ordering feature.

Tests cover:
- Order index creation and migration
- Order persistence across restarts
- Collection reordering
- Folder reordering within collections
- Request reordering within folders
- Import/export order preservation
- Database reordering methods
"""

import pytest
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.database import DatabaseManager
from features.collection_io import CollectionExporter, CollectionImporter


@pytest.fixture
def db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_ordering.db"
    database = DatabaseManager(str(db_path))
    yield database
    database.connection.close()


class TestOrderIndexMigration:
    """Test that order_index column exists and has correct defaults."""
    
    def test_collections_have_order_index(self, db):
        """Test collections table has order_index column."""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(collections)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        assert 'order_index' in columns, "collections table should have order_index column"
    
    def test_folders_have_order_index(self, db):
        """Test folders table has order_index column."""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(folders)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        assert 'order_index' in columns, "folders table should have order_index column"
    
    def test_requests_have_order_index(self, db):
        """Test requests table has order_index column."""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(requests)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        assert 'order_index' in columns, "requests table should have order_index column"
    
    def test_default_order_index_value(self, db):
        """Test that new items get default order_index = id * 100."""
        collection_id = db.create_collection("Test Collection")
        
        cursor = db.connection.cursor()
        cursor.execute("SELECT id, order_index FROM collections WHERE id = ?", (collection_id,))
        row = cursor.fetchone()
        
        assert row[1] == row[0] * 100, f"Default order_index should be id * 100, got {row[1]} for id {row[0]}"


class TestCollectionOrdering:
    """Test collection reordering functionality."""
    
    def test_collections_ordered_by_order_index(self, db):
        """Test that collections are returned in order_index order."""
        # Create collections out of order
        id1 = db.create_collection("Z Collection")
        id2 = db.create_collection("A Collection")
        id3 = db.create_collection("M Collection")
        
        # Reorder: id2, id3, id1
        db.reorder_collections([id2, id3, id1])
        
        # Get all collections
        collections = db.get_all_collections()
        
        assert len(collections) == 3
        assert collections[0]['id'] == id2  # A Collection first
        assert collections[1]['id'] == id3  # M Collection second
        assert collections[2]['id'] == id1  # Z Collection third
    
    def test_reorder_collections_updates_order_index(self, db):
        """Test that reorder_collections updates order_index correctly."""
        id1 = db.create_collection("Collection 1")
        id2 = db.create_collection("Collection 2")
        id3 = db.create_collection("Collection 3")
        
        # Reorder: 3, 1, 2
        db.reorder_collections([id3, id1, id2])
        
        cursor = db.connection.cursor()
        cursor.execute("SELECT id, order_index FROM collections ORDER BY order_index")
        rows = cursor.fetchall()
        
        assert rows[0][0] == id3  # Collection 3 first
        assert rows[1][0] == id1  # Collection 1 second
        assert rows[2][0] == id2  # Collection 2 third
        
        # Check order_index values have proper spacing
        assert rows[0][1] == 0
        assert rows[1][1] == 100
        assert rows[2][1] == 200


class TestFolderOrdering:
    """Test folder reordering functionality."""
    
    def test_folders_ordered_by_order_index(self, db):
        """Test that folders are returned in order_index order."""
        collection_id = db.create_collection("Test Collection")
        
        # Create folders out of order
        id1 = db.create_folder(collection_id, "Z Folder", None)
        id2 = db.create_folder(collection_id, "A Folder", None)
        id3 = db.create_folder(collection_id, "M Folder", None)
        
        # Reorder: id2, id3, id1
        db.reorder_folders(collection_id, [id2, id3, id1])
        
        # Get all folders
        folders = db.get_folders_by_collection(collection_id)
        
        assert len(folders) == 3
        assert folders[0]['id'] == id2  # A Folder first
        assert folders[1]['id'] == id3  # M Folder second
        assert folders[2]['id'] == id1  # Z Folder third
    
    def test_reorder_folders_within_parent(self, db):
        """Test reordering folders within a parent folder."""
        collection_id = db.create_collection("Test Collection")
        parent_id = db.create_folder(collection_id, "Parent Folder", None)
        
        # Create child folders
        id1 = db.create_folder(collection_id, "Child 1", parent_id)
        id2 = db.create_folder(collection_id, "Child 2", parent_id)
        id3 = db.create_folder(collection_id, "Child 3", parent_id)
        
        # Reorder: 3, 1, 2
        db.reorder_folders(collection_id, [id3, id1, id2])
        
        folders = db.get_folders_by_collection(collection_id)
        child_folders = [f for f in folders if f['parent_id'] == parent_id]
        
        assert child_folders[0]['id'] == id3
        assert child_folders[1]['id'] == id1
        assert child_folders[2]['id'] == id2


class TestRequestOrdering:
    """Test request reordering functionality."""
    
    def test_requests_ordered_by_order_index(self, db):
        """Test that requests are returned in order_index order."""
        collection_id = db.create_collection("Test Collection")
        
        # Create requests out of order (signature: name, url, method, collection_id)
        id1 = db.create_request("Z Request", "http://z.com", "GET", collection_id)
        id2 = db.create_request("A Request", "http://a.com", "GET", collection_id)
        id3 = db.create_request("M Request", "http://m.com", "GET", collection_id)
        
        # Reorder: id2, id3, id1
        db.reorder_requests(collection_id, None, [id2, id3, id1])
        
        # Get all requests
        requests = db.get_requests_by_collection(collection_id)
        
        assert len(requests) == 3
        assert requests[0]['id'] == id2  # A Request first
        assert requests[1]['id'] == id3  # M Request second
        assert requests[2]['id'] == id1  # Z Request third
    
    def test_reorder_requests_within_folder(self, db):
        """Test reordering requests within a folder."""
        collection_id = db.create_collection("Test Collection")
        folder_id = db.create_folder(collection_id, "Test Folder", None)
        
        # Create requests in folder (signature: name, url, method, collection_id, folder_id=)
        id1 = db.create_request("Request 1", "http://1.com", "GET", collection_id, folder_id=folder_id)
        id2 = db.create_request("Request 2", "http://2.com", "GET", collection_id, folder_id=folder_id)
        id3 = db.create_request("Request 3", "http://3.com", "GET", collection_id, folder_id=folder_id)
        
        # Reorder: 3, 1, 2
        db.reorder_requests(collection_id, folder_id, [id3, id1, id2])
        
        requests = db.get_requests_by_folder(folder_id, collection_id)
        
        assert requests[0]['id'] == id3
        assert requests[1]['id'] == id1
        assert requests[2]['id'] == id2


class TestOrderPersistence:
    """Test that order persists across database operations."""
    
    def test_order_persists_after_db_reopen(self, tmp_path):
        """Test that order persists after closing and reopening database."""
        db_path = tmp_path / "test_persistence.db"
        
        # Create initial database
        db = DatabaseManager(str(db_path))
        
        # Create and reorder collections
        id1 = db.create_collection("Collection 1")
        id2 = db.create_collection("Collection 2")
        id3 = db.create_collection("Collection 3")
        db.reorder_collections([id3, id1, id2])
        
        # Close database
        db.connection.close()
        
        # Reopen database
        new_db = DatabaseManager(str(db_path))
        collections = new_db.get_all_collections()
        
        # Verify order
        assert collections[0]['id'] == id3
        assert collections[1]['id'] == id1
        assert collections[2]['id'] == id2
        
        new_db.connection.close()


class TestImportExportOrder:
    """Test that order is preserved during import/export."""
    
    def test_export_includes_order_index(self, db):
        """Test that exported JSON includes order_index."""
        collection_id = db.create_collection("Test Collection")
        
        # Create and reorder folders
        id1 = db.create_folder(collection_id, "Folder 1", None)
        id2 = db.create_folder(collection_id, "Folder 2", None)
        db.reorder_folders(collection_id, [id2, id1])
        
        # Export collection
        exporter = CollectionExporter(db)
        export_data = exporter.export_collection(collection_id)
        
        # Check that order_index is in exported data (nested under 'collection' key)
        assert 'collection' in export_data
        collection_data = export_data['collection']
        assert 'order_index' in collection_data, "Exported collection should have order_index"
        assert len(collection_data['folders']) == 2
        assert 'order_index' in collection_data['folders'][0], "Exported folders should have order_index"
    
    def test_import_preserves_order_index(self, db):
        """Test that importing preserves order_index from file."""
        # Create collection data with specific order_index values (wrapped in collection key)
        import_data = {
            "collection": {
                "name": "Imported Collection",
                "description": "Test",
                "order_index": 500,
                "folders": [
                    {
                        "name": "Folder 1",
                        "order_index": 200,
                        "requests": []
                    },
                    {
                        "name": "Folder 2",
                        "order_index": 100,
                        "requests": []
                    }
                ],
                "requests": []
            }
        }
        
        # Import collection (returns tuple: success, message, collection_id)
        importer = CollectionImporter(db)
        success, message, collection_id = importer.import_collection(import_data)
        assert success, f"Import failed: {message}"
        
        # Verify order is preserved
        folders = db.get_folders_by_collection(collection_id)
        
        # Folder 2 should be first (order_index 100)
        assert folders[0]['name'] == "Folder 2"
        assert folders[0]['order_index'] == 100
        
        # Folder 1 should be second (order_index 200)
        assert folders[1]['name'] == "Folder 1"
        assert folders[1]['order_index'] == 200
    
    def test_import_without_order_index_uses_position(self, db):
        """Test that importing without order_index assigns based on position."""
        import_data = {
            "collection": {
                "name": "Imported Collection",
                "description": "Test",
                "folders": [
                    {"name": "Folder 1", "requests": []},
                    {"name": "Folder 2", "requests": []},
                    {"name": "Folder 3", "requests": []}
                ],
                "requests": []
            }
        }
        
        # Import collection (returns tuple: success, message, collection_id)
        importer = CollectionImporter(db)
        success, message, collection_id = importer.import_collection(import_data)
        assert success, f"Import failed: {message}"
        
        # Verify order based on position
        folders = db.get_folders_by_collection(collection_id)
        
        assert folders[0]['name'] == "Folder 1"
        assert folders[0]['order_index'] == 0
        
        assert folders[1]['name'] == "Folder 2"
        assert folders[1]['order_index'] == 100
        
        assert folders[2]['name'] == "Folder 3"
        assert folders[2]['order_index'] == 200


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_reorder_empty_list(self, db):
        """Test that reordering with empty list doesn't crash."""
        collection_id = db.create_collection("Test Collection")
        
        # Should not crash
        db.reorder_folders(collection_id, [])
    
    def test_reorder_single_item(self, db):
        """Test that reordering single item works."""
        id1 = db.create_collection("Collection 1")
        
        # Should not crash
        db.reorder_collections([id1])
        
        collections = db.get_all_collections()
        assert len(collections) == 1
        assert collections[0]['id'] == id1
    
    def test_reorder_nonexistent_ids_ignored(self, db):
        """Test that reordering with non-existent IDs doesn't crash."""
        id1 = db.create_collection("Collection 1")
        id2 = db.create_collection("Collection 2")
        
        # Include non-existent ID 999
        db.reorder_collections([id1, 999, id2])
        
        # Should still work for existing IDs
        collections = db.get_all_collections()
        assert len(collections) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
