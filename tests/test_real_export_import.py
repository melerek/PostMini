"""
Real-World Export/Import Test

Test export/import with actual demo data to ensure it works in production.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.features.collection_io import CollectionExporter, CollectionImporter


def test_with_demo_data():
    """Test export/import with the actual demo collection."""
    print("="*60)
    print("Real-World Export/Import Test")
    print("="*60)
    print()
    
    try:
        # Use the actual database
        db = DatabaseManager("api_client.db")
        exporter = CollectionExporter(db)
        importer = CollectionImporter(db)
        
        # Find the demo collection
        collections = db.get_all_collections()
        demo_collection = None
        
        for col in collections:
            if "Environment Demo" in col['name']:
                demo_collection = col
                break
        
        if not demo_collection:
            print("[WARN] Demo collection not found. Run demo_environments.py first.")
            print("Creating a test collection instead...")
            
            # Create test collection
            col_id = db.create_collection("Test Export Collection")
            db.create_request(
                collection_id=col_id,
                name="Test Request",
                method="GET",
                url="{{baseUrl}}/test"
            )
            demo_collection = {'id': col_id, 'name': 'Test Export Collection'}
        
        print(f"Testing with collection: '{demo_collection['name']}'")
        print()
        
        # Step 1: Export the collection
        print("Step 1: Exporting collection...")
        export_file = "exported_collection.json"
        
        success = exporter.export_collection_to_file(
            demo_collection['id'],
            export_file
        )
        
        if success and os.path.exists(export_file):
            file_size = os.path.getsize(export_file)
            print(f"  [OK] Exported to '{export_file}' ({file_size} bytes)")
            
            # Show file content preview
            import json
            with open(export_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            num_requests = len(data['collection']['requests'])
            print(f"  [OK] Contains {num_requests} request(s)")
            print(f"  [OK] Export date: {data['export_date']}")
        else:
            print("  [ERROR] Export failed!")
            return False
        
        print()
        
        # Step 2: Import with rename
        print("Step 2: Importing collection (with rename)...")
        
        success, message, new_col_id = importer.import_collection_from_file(
            export_file,
            rename_if_exists=True
        )
        
        if success:
            print(f"  [OK] {message}")
            
            # Verify the imported collection
            new_collection = db.get_collection(new_col_id)
            print(f"  [OK] New collection name: '{new_collection['name']}'")
            
            # Verify requests
            requests = db.get_requests_by_collection(new_col_id)
            print(f"  [OK] Imported {len(requests)} request(s)")
            
            # Show first request details
            if requests:
                first_req = requests[0]
                print(f"  [OK] First request: {first_req['method']} - {first_req['name']}")
                print(f"       URL: {first_req['url']}")
        else:
            print(f"  [ERROR] Import failed: {message}")
            return False
        
        print()
        
        # Step 3: Clean up (delete the imported collection)
        print("Step 3: Cleaning up...")
        db.delete_collection(new_col_id)
        print("  [OK] Test collection deleted")
        
        # Clean up export file
        if os.path.exists(export_file):
            os.remove(export_file)
            print("  [OK] Export file deleted")
        
        db.close()
        
        print()
        print("="*60)
        print("[SUCCESS] Real-world export/import test passed!")
        print("="*60)
        print()
        print("The feature is ready to use in the application!")
        print()
        print("Try it yourself:")
        print("1. Run: python main.py")
        print("2. Select a collection in the left panel")
        print("3. Click 'Export' button")
        print("4. Save the JSON file")
        print("5. Click 'Import' button")
        print("6. Select the JSON file")
        print("7. Choose rename option")
        print("8. See the imported collection appear!")
        print()
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Real-world test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_with_demo_data()
    sys.exit(0 if success else 1)

