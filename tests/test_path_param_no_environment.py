"""
Test path parameter substitution without active environment.

This test verifies the regression fix for path parameters (:paramName syntax)
not being substituted when no environment is active.
"""

import pytest
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


@pytest.fixture
def main_window(qtbot):
    """Create MainWindow instance for testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


class TestPathParamNoEnvironment:
    """Test that path parameters work without active environment."""
    
    def test_path_param_with_collection_variable_no_env(self, main_window):
        """Test :param substitution using collection variable when no environment is active."""
        # Ensure no environment is active
        main_window.env_manager.set_active_environment(None)
        assert not main_window.env_manager.has_active_environment()
        
        # Create collection with variable
        collection_id = main_window.db.create_collection("PathParam Test 1")
        main_window.db.create_collection_variable(collection_id, "orgId", "12345")
        main_window.db.create_collection_variable(collection_id, "name", "testname")
        
        # Set current collection
        main_window.current_collection_id = collection_id
        
        # Get collection variables
        collection_variables = main_window.db.get_collection_variables(collection_id)
        
        # Test path param substitution directly (simulating what _send_request does)
        from src.features.variable_substitution import VariableSubstitution
        
        url = "http://example.com/v1/domainRelationships/:name/organizationId/:orgId"
        
        # First substitute {{variables}} if any
        url, _ = VariableSubstitution.substitute(url, None, collection_variables, {})
        
        # Then substitute :pathParams
        url, unresolved = VariableSubstitution.substitute_path_params(url, None, collection_variables, {})
        
        # Verify path parameters were substituted
        assert url == "http://example.com/v1/domainRelationships/testname/organizationId/12345"
        assert len(unresolved) == 0
    
    def test_path_param_with_extracted_variable_no_env(self, main_window):
        """Test :param substitution using extracted variable when no environment is active."""
        # Ensure no environment is active
        main_window.env_manager.set_active_environment(None)
        assert not main_window.env_manager.has_active_environment()
        
        # Create collection
        collection_id = main_window.db.create_collection("PathParam Test 2")
        main_window.current_collection_id = collection_id
        
        # Set extracted variable (simulate extraction from previous response)
        extracted_variables = {"userId": "98765"}
        
        # Test path param substitution with extracted variable
        from src.features.variable_substitution import VariableSubstitution
        
        url = "http://example.com/users/:userId/posts"
        
        # First substitute {{variables}} if any
        url, _ = VariableSubstitution.substitute(url, None, {}, extracted_variables)
        
        # Then substitute :pathParams
        url, unresolved = VariableSubstitution.substitute_path_params(url, None, {}, extracted_variables)
        
        # Verify path parameter was substituted
        assert url == "http://example.com/users/98765/posts"
        assert len(unresolved) == 0
    
    def test_path_param_mixed_with_template_vars_no_env(self, main_window):
        """Test mixing {{template}} variables and :pathParams without environment."""
        # Ensure no environment is active
        main_window.env_manager.set_active_environment(None)
        
        # Create collection with variables
        collection_id = main_window.db.create_collection("PathParam Test 3")
        main_window.db.create_collection_variable(collection_id, "baseUrl", "http://api.example.com")
        main_window.db.create_collection_variable(collection_id, "invitationId", "inv-123")
        
        main_window.current_collection_id = collection_id
        collection_variables = main_window.db.get_collection_variables(collection_id)
        
        # Test URL with both {{template}} and :pathParam syntax
        from src.features.variable_substitution import VariableSubstitution
        
        url = "{{baseUrl}}/order/v1/Rating/:invitationId"
        
        # First substitute {{variables}}
        url, _ = VariableSubstitution.substitute(url, None, collection_variables, {})
        assert url == "http://api.example.com/order/v1/Rating/:invitationId"
        
        # Then substitute :pathParams
        url, unresolved = VariableSubstitution.substitute_path_params(url, None, collection_variables, {})
        
        # Verify both were substituted
        assert url == "http://api.example.com/order/v1/Rating/inv-123"
        assert len(unresolved) == 0
    
    def test_path_param_undefined_no_env(self, main_window):
        """Test unresolved path parameter without environment."""
        # Ensure no environment is active
        main_window.env_manager.set_active_environment(None)
        
        # Create collection with NO variables
        collection_id = main_window.db.create_collection("PathParam Test 4")
        main_window.current_collection_id = collection_id
        
        # Test path param substitution with undefined variable
        from src.features.variable_substitution import VariableSubstitution
        
        url = "http://example.com/users/:userId"
        
        # Substitute (should remain unchanged)
        url, _ = VariableSubstitution.substitute(url, None, {}, {})
        url, unresolved = VariableSubstitution.substitute_path_params(url, None, {}, {})
        
        # Verify path parameter was NOT substituted and reported as unresolved
        assert url == "http://example.com/users/:userId"
        assert ":userId" in unresolved
    
    def test_path_param_priority_without_env(self, main_window):
        """Test path param resolution priority: extracted > collection."""
        # Ensure no environment is active
        main_window.env_manager.set_active_environment(None)
        
        # Create collection with variable
        collection_id = main_window.db.create_collection("PathParam Test 5")
        main_window.db.create_collection_variable(collection_id, "userId", "collection-123")
        collection_variables = main_window.db.get_collection_variables(collection_id)
        
        # Set extracted variable with same name
        extracted_variables = {"userId": "extracted-456"}
        
        # Test path param substitution
        from src.features.variable_substitution import VariableSubstitution
        
        url = "http://example.com/users/:userId"
        url, _ = VariableSubstitution.substitute(url, None, collection_variables, extracted_variables)
        url, unresolved = VariableSubstitution.substitute_path_params(
            url, None, collection_variables, extracted_variables
        )
        
        # Verify extracted variable took priority
        assert url == "http://example.com/users/extracted-456"
        assert len(unresolved) == 0
