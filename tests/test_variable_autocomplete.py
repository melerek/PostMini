"""
Test Variable Autocomplete Feature

This test demonstrates the variable autocomplete functionality.
It creates a collection with variables and shows how autocomplete works.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow


def test_variable_autocomplete():
    """Test that autocomplete appears when typing {{ or :"""
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Create a test collection with unique name
    import time
    timestamp = int(time.time())
    collection_name = f"Autocomplete Test {timestamp}"
    col_id = window.db.create_collection(collection_name)
    
    # Add some collection variables
    col_vars = {
        'baseUrl': 'https://api.example.com',
        'apiKey': 'test-key-12345',
        'userId': '42'
    }
    for key, value in col_vars.items():
        window.db.update_collection_variable(col_id, key, value)
    
    # Create an environment with variables
    env_name = f"Test Env {timestamp}"
    env_vars = {
        'token': 'abc123xyz',
        'version': 'v1',
        'timeout': '30'
    }
    env_id = window.db.create_environment(env_name, env_vars)
    
    # Set active environment using proper format
    environment_dict = {
        'id': env_id,
        'name': env_name,
        'variables': env_vars
    }
    window.env_manager.set_active_environment(environment_dict)
    
    # Create a request in the collection
    request_name = "Test Request"
    request_id = window.db.create_request(
        col_id,
        request_name,
        "GET",
        "{{baseUrl}}/users/:userId",
        params={},
        headers={'Authorization': 'Bearer {{token}}'},
        body="",
        auth_token=""
    )
    
    # Load the collection and request in UI
    window._load_collections()
    window._load_request(request_id)
    
    print("\n" + "="*60)
    print("VARIABLE AUTOCOMPLETE TEST")
    print("="*60)
    
    print("\nSetup Complete:")
    print(f"  Collection: {collection_name}")
    print(f"  Collection Variables: {list(col_vars.keys())}")
    print(f"  Environment: {env_name}")
    print(f"  Environment Variables: {list(env_vars.keys())}")
    print(f"  Request URL: {{{{baseUrl}}}}/users/:userId")
    
    print("\n" + "-"*60)
    print("AUTOCOMPLETE USAGE GUIDE")
    print("-"*60)
    
    print("\n1. URL Field Autocomplete:")
    print("   - Type '{{' in the URL field → Autocomplete shows all variables")
    print("   - Type ':' after a '/' → Autocomplete shows variables for path params")
    print("   - Use Tab/Down to navigate, Enter to select")
    print("   - Current URL has: {{baseUrl}} and :userId")
    
    print("\n2. Body Field Autocomplete:")
    print("   - Switch to Body tab")
    print("   - Type '{{' → See all available variables")
    print("   - Type text after '{{' to filter (e.g., '{{tok' filters to 'token')")
    
    print("\n3. Visual Feedback:")
    print("   - Variables are highlighted:")
    print("     • GREEN = Variable is defined")
    print("     • RED = Variable is undefined")
    print("   - Hover over variables to see resolved values")
    
    print("\n4. Variable Scopes (shown in autocomplete):")
    print("   - ENV (Blue) = Environment variables")
    print("   - COL (Purple) = Collection variables")
    print("   - EXT (Green) = Extracted variables (from previous responses)")
    print("   - DYNAMIC (Orange) = Auto-generated (timestamp, guid, etc.)")
    
    print("\n5. Keyboard Shortcuts:")
    print("   - Tab = Next suggestion")
    print("   - Shift+Tab = Previous suggestion")
    print("   - Enter = Insert selected variable")
    print("   - Escape = Close autocomplete")
    print("   - Down/Up Arrows = Navigate list")
    
    print("\n" + "="*60)
    print("Try typing in the URL field or Body tab to see autocomplete!")
    print("="*60 + "\n")
    
    # Focus on URL input so user can test immediately
    window.url_input.setFocus()
    
    # Run the app
    sys.exit(app.exec())


if __name__ == '__main__':
    test_variable_autocomplete()
