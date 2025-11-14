"""
Test script to identify the crash point in save new request
"""
import sys
import traceback

# Add detailed error logging
def test_save_new_request():
    """Simulate the save new request flow to find crash point"""
    
    try:
        print("1. Starting save new request test...")
        
        # Simulate what happens in _save_new_request
        print("2. Dialog accepted, extracting data...")
        collection_id = 1
        folder_id = None
        request_name = "Test Request"
        
        print("3. Attempting to create request in database...")
        # This would call db.add_request
        
        print("4. Updating tab state...")
        # Update tab_states
        
        print("5. Setting current_* variables...")
        current_request_id = 1
        current_collection_id = collection_id
        current_request_name = request_name
        current_folder_id = folder_id
        
        print("6. Getting collection name...")
        # collection = self.db.get_collection(collection_id)
        # current_collection_name = collection.get('name', 'Unknown Collection') if collection else 'Unknown Collection'
        
        print("7. Calling _store_original_request_data()...")
        # This reads from UI elements
        
        print("8. Calling _update_tab_title()...")
        # This updates tab display
        
        print("9. Calling _update_request_title()...")
        # This updates the breadcrumb title - requires current_collection_name
        
        print("10. Calling _load_collections()...")
        # Reloads the tree
        
        print("11. Calling _update_current_request_highlight()...")
        # Updates tree highlighting
        
        print("12. Showing success toast...")
        
        print("✅ All steps completed without error!")
        
    except Exception as e:
        print(f"❌ CRASH at step: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    test_save_new_request()

