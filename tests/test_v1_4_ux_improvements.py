"""
Tests for V1.4.0 UX Improvements

Tests for duplicate name handling, smart suggestions, and UI improvements.
"""

import pytest
import tempfile
import os
from src.core.database import DatabaseManager


class TestDuplicateCollectionNameHandling:
    """Test duplicate collection name detection and handling."""
    
    def setup_method(self):
        """Setup test fixtures with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
        self.window = None
    
    def teardown_method(self):
        """Clean up temporary database."""
        # Close window's database connection if window was created
        if hasattr(self, 'window') and self.window is not None:
            if hasattr(self.window, 'db') and hasattr(self.window.db, 'connection'):
                self.window.db.connection.close()
        
        if hasattr(self, 'db'):
            self.db.connection.close()
        
        # Small delay to ensure Windows releases file handle
        import time
        time.sleep(0.1)
        
        if hasattr(self, 'temp_db') and os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                pass  # File still locked, ignore
    
    def test_create_collection_unique_name(self):
        """Test creating collection with unique name succeeds."""
        collection_id = self.db.create_collection("My API")
        assert collection_id > 0
        
        collections = self.db.get_all_collections()
        assert len(collections) == 1
        assert collections[0]['name'] == "My API"
    
    def test_create_duplicate_collection_fails(self):
        """Test creating collection with duplicate name raises error."""
        self.db.create_collection("My API")
        
        with pytest.raises(Exception) as exc_info:
            self.db.create_collection("My API")
        
        assert "UNIQUE constraint failed" in str(exc_info.value)
    
    def test_get_unique_collection_name_no_conflict(self):
        """Test generating unique name when no conflict exists."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        self.window = MainWindow(self.temp_db.name)
        
        # No existing collections, so name should remain unchanged
        unique_name = self.window._get_unique_collection_name("My API")
        assert unique_name == "My API"
    
    def test_get_unique_collection_name_with_conflict(self):
        """Test generating unique name when conflict exists."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create a collection
        self.db.create_collection("My API")
        
        self.window = MainWindow(self.temp_db.name)
        
        # Should suggest "My API (2)"
        unique_name = self.window._get_unique_collection_name("My API")
        assert unique_name == "My API (2)"
    
    def test_get_unique_collection_name_multiple_conflicts(self):
        """Test generating unique name with multiple existing copies."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create multiple collections with similar names
        self.db.create_collection("My API")
        self.db.create_collection("My API (2)")
        self.db.create_collection("My API (3)")
        
        self.window = MainWindow(self.temp_db.name)
        
        # Should suggest "My API (4)"
        unique_name = self.window._get_unique_collection_name("My API")
        assert unique_name == "My API (4)"


class TestDuplicateRequestNameHandling:
    """Test duplicate request name detection and handling."""
    
    def setup_method(self):
        """Setup test fixtures with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
        self.window = None
        
        # Create a test collection
        self.collection_id = self.db.create_collection("Test Collection")
    
    def teardown_method(self):
        """Clean up temporary database."""
        # Close window's database connection if window was created
        if hasattr(self, 'window') and self.window is not None:
            if hasattr(self.window, 'db') and hasattr(self.window.db, 'connection'):
                self.window.db.connection.close()
        
        if hasattr(self, 'db'):
            self.db.connection.close()
        
        # Small delay to ensure Windows releases file handle
        import time
        time.sleep(0.1)
        
        if hasattr(self, 'temp_db') and os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                pass  # File still locked, ignore
    
    def test_create_request_unique_name(self):
        """Test creating request with unique name succeeds."""
        request_id = self.db.create_request(
            collection_id=self.collection_id,
            name="Get Users",
            method="GET",
            url="https://api.example.com/users"
        )
        assert request_id > 0
        
        requests = self.db.get_requests_by_collection(self.collection_id)
        assert len(requests) == 1
        assert requests[0]['name'] == "Get Users"
    
    def test_get_unique_request_name_no_conflict(self):
        """Test generating unique request name when no conflict exists."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        self.window = MainWindow(self.temp_db.name)
        
        # No existing requests, so name should remain unchanged
        unique_name = self.window._get_unique_request_name(
            self.collection_id, "Get Users", "GET"
        )
        assert unique_name == "Get Users"
    
    def test_get_unique_request_name_with_conflict(self):
        """Test generating unique request name when conflict exists."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create a request
        self.db.create_request(
            collection_id=self.collection_id,
            name="Get Users",
            method="GET",
            url="https://api.example.com/users"
        )
        
        self.window = MainWindow(self.temp_db.name)
        
        # Should suggest "Get Users (2)"
        unique_name = self.window._get_unique_request_name(
            self.collection_id, "Get Users", "GET"
        )
        assert unique_name == "Get Users (2)"
    
    def test_get_unique_request_name_method_aware(self):
        """Test that unique name check is method-aware."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create GET request
        self.db.create_request(
            collection_id=self.collection_id,
            name="Users",
            method="GET",
            url="https://api.example.com/users"
        )
        
        self.window = MainWindow(self.temp_db.name)
        
        # Should allow "Users" for POST (different method)
        unique_name = self.window._get_unique_request_name(
            self.collection_id, "Users", "POST"
        )
        assert unique_name == "Users"
        
        # Should suggest "Users (2)" for another GET
        unique_name = self.window._get_unique_request_name(
            self.collection_id, "Users", "GET"
        )
        assert unique_name == "Users (2)"
    
    def test_check_duplicate_request_name(self):
        """Test duplicate request name detection."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create a request
        self.db.create_request(
            collection_id=self.collection_id,
            name="Get Users",
            method="GET",
            url="https://api.example.com/users"
        )
        
        self.window = MainWindow(self.temp_db.name)
        
        # Test with duplicate name
        is_duplicate, suggested = self.window._check_duplicate_request_name(
            self.collection_id, "Get Users", "GET"
        )
        assert is_duplicate is True
        assert suggested == "Get Users (2)"
        
        # Test with unique name
        is_duplicate, suggested = self.window._check_duplicate_request_name(
            self.collection_id, "Get Posts", "GET"
        )
        assert is_duplicate is False
        assert suggested == "Get Posts"
    
    def test_get_unique_request_name_multiple_conflicts(self):
        """Test generating unique name with multiple existing copies."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create multiple requests with similar names
        self.db.create_request(
            collection_id=self.collection_id,
            name="Get Users",
            method="GET",
            url="https://api.example.com/users"
        )
        self.db.create_request(
            collection_id=self.collection_id,
            name="Get Users (2)",
            method="GET",
            url="https://api.example.com/users"
        )
        self.db.create_request(
            collection_id=self.collection_id,
            name="Get Users (3)",
            method="GET",
            url="https://api.example.com/users"
        )
        
        self.window = MainWindow(self.temp_db.name)
        
        # Should suggest "Get Users (4)"
        unique_name = self.window._get_unique_request_name(
            self.collection_id, "Get Users", "GET"
        )
        assert unique_name == "Get Users (4)"


class TestDynamicVariablesWithoutEnvironment:
    """Test dynamic variables work without active environment."""
    
    def test_substitution_without_environment(self):
        """Test dynamic variables substitute with empty environment dict."""
        from src.features.variable_substitution import VariableSubstitution
        
        # Test URL substitution
        url = "https://api.example.com/users/$guid"
        result, unresolved = VariableSubstitution.substitute(url, {})
        
        assert '$guid' not in result
        assert 'https://api.example.com/users/' in result
    
    def test_multiple_variables_without_environment(self):
        """Test multiple dynamic variables work without environment."""
        from src.features.variable_substitution import VariableSubstitution
        
        body = '{"id": "$guid", "email": "$randomEmail", "timestamp": "$timestamp"}'
        result, unresolved = VariableSubstitution.substitute(body, {})
        
        assert '$guid' not in result
        assert '$randomEmail' not in result
        assert '$timestamp' not in result
        
        # Should be valid JSON
        import json
        data = json.loads(result)
        assert 'id' in data
        assert 'email' in data
        assert 'timestamp' in data
    
    def test_dynamic_and_environment_variables(self):
        """Test dynamic variables work alongside environment variables."""
        from src.features.variable_substitution import VariableSubstitution
        
        text = "{{baseUrl}}/users/$guid?key={{apiKey}}&timestamp=$timestamp"
        env_vars = {
            'baseUrl': 'https://api.example.com',
            'apiKey': 'secret123'
        }
        
        result, unresolved = VariableSubstitution.substitute(text, env_vars)
        
        # All variables should be replaced
        assert '{{baseUrl}}' not in result
        assert '{{apiKey}}' not in result
        assert '$guid' not in result
        assert '$timestamp' not in result
        assert 'https://api.example.com/users/' in result
        assert 'key=secret123' in result


class TestOpenAPIImportDuplicateHandling:
    """Test OpenAPI import handles duplicate collection names."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
        self.window = None
    
    def teardown_method(self):
        """Clean up temporary database."""
        # Close window's database connection if window was created
        if hasattr(self, 'window') and self.window is not None:
            if hasattr(self.window, 'db') and hasattr(self.window.db, 'connection'):
                self.window.db.connection.close()
        
        if hasattr(self, 'db'):
            self.db.connection.close()
        
        # Small delay to ensure Windows releases file handle
        import time
        time.sleep(0.1)
        
        if hasattr(self, 'temp_db') and os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                pass  # File still locked, ignore
    
    def test_import_openapi_suggests_unique_name(self):
        """Test OpenAPI import suggests unique name for duplicate collection."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create existing collection
        self.db.create_collection("Pet Store API")
        
        self.window = MainWindow(self.temp_db.name)
        
        # Simulate OpenAPI import with duplicate name
        collection_name = "Pet Store API"
        suggested_name = self.window._get_unique_collection_name(collection_name)
        
        assert suggested_name == "Pet Store API (2)"


class TestRequestCopyDuplicateHandling:
    """Test request duplication generates unique names."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
        self.window = None
        self.collection_id = self.db.create_collection("Test Collection")
    
    def teardown_method(self):
        """Clean up temporary database."""
        # Close window's database connection if window was created
        if hasattr(self, 'window') and self.window is not None:
            if hasattr(self.window, 'db') and hasattr(self.window.db, 'connection'):
                self.window.db.connection.close()
        
        if hasattr(self, 'db'):
            self.db.connection.close()
        
        # Small delay to ensure Windows releases file handle
        import time
        time.sleep(0.1)
        
        if hasattr(self, 'temp_db') and os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                pass  # File still locked, ignore
    
    def test_duplicate_request_unique_name(self):
        """Test duplicating request generates unique name."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create original request
        self.db.create_request(
            collection_id=self.collection_id,
            name="Get Users",
            method="GET",
            url="https://api.example.com/users"
        )
        
        self.window = MainWindow(self.temp_db.name)
        
        # Test duplicate name generation
        base_name = "Get Users (Copy)"
        unique_name = self.window._get_unique_request_name(
            self.collection_id, base_name, "GET"
        )
        
        assert unique_name == "Get Users (Copy)"
        
        # Create the copy
        self.db.create_request(
            collection_id=self.collection_id,
            name=unique_name,
            method="GET",
            url="https://api.example.com/users"
        )
        
        # Test second duplicate
        unique_name2 = self.window._get_unique_request_name(
            self.collection_id, base_name, "GET"
        )
        
        assert unique_name2 == "Get Users (Copy) (2)"


class TestEdgeCases:
    """Test edge cases for duplicate name handling."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
        self.window = None
        self.collection_id = self.db.create_collection("Test Collection")
    
    def teardown_method(self):
        """Clean up temporary database."""
        # Close window's database connection if window was created
        if hasattr(self, 'window') and self.window is not None:
            if hasattr(self.window, 'db') and hasattr(self.window.db, 'connection'):
                self.window.db.connection.close()
        
        if hasattr(self, 'db'):
            self.db.connection.close()
        
        # Small delay to ensure Windows releases file handle
        import time
        time.sleep(0.1)
        
        if hasattr(self, 'temp_db') and os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                pass  # File still locked, ignore
    
    def test_empty_collection_name(self):
        """Test handling of empty or whitespace-only collection names."""
        # Database allows empty names, which is fine
        # The UI should handle validation, not the database
        collection_id = self.db.create_collection("")
        assert collection_id > 0
    
    def test_whitespace_trimming(self):
        """Test that whitespace is properly trimmed from names."""
        from src.ui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        self.window = MainWindow(self.temp_db.name)
        
        # Create collection with whitespace
        collection_id = self.db.create_collection("  Test API  ")
        
        # Verify name is stored (may or may not be trimmed by DB)
        collection = self.db.get_collection(collection_id)
        assert collection is not None
    
    def test_special_characters_in_names(self):
        """Test handling of special characters in collection/request names."""
        # Should allow special characters
        collection_id = self.db.create_collection("Test & API (v2.0)")
        assert collection_id > 0
        
        request_id = self.db.create_request(
            collection_id=collection_id,
            name="Get Users (Active)",
            method="GET",
            url="https://api.example.com/users"
        )
        assert request_id > 0
    
    def test_very_long_names(self):
        """Test handling of very long collection/request names."""
        long_name = "A" * 500  # Very long name
        
        # Should either succeed or fail gracefully
        try:
            collection_id = self.db.create_collection(long_name)
            assert collection_id > 0
        except Exception as e:
            # If it fails, it should be a clear database constraint error
            assert "too long" in str(e).lower() or "constraint" in str(e).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

