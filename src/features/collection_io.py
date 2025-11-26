"""
Collection Import/Export Module

This module handles exporting collections (with all requests) to JSON files
and importing them back. Supports both internal format and Postman Collection Format v2.1.
This enables team collaboration by sharing API configurations.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.core.database import DatabaseManager
from src.features.postman_converter import PostmanConverter


class CollectionExporter:
    """
    Handles exporting collections to JSON format.
    """
    
    EXPORT_VERSION = "1.0"
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize the exporter.
        
        Args:
            db: DatabaseManager instance
        """
        self.db = db
    
    def export_collection(self, collection_id: int) -> Dict:
        """
        Export a single collection with all its requests, folders, and variables to a dictionary.
        
        Args:
            collection_id: ID of the collection to export
            
        Returns:
            Dictionary containing collection data
            
        Raises:
            ValueError: If collection doesn't exist
        """
        # Get collection
        collection = self.db.get_collection(collection_id)
        if not collection:
            raise ValueError(f"Collection with ID {collection_id} not found")
        
        # Get all requests for this collection
        requests = self.db.get_requests_by_collection(collection_id)
        
        # Get all folders for this collection
        folders = self.db.get_folders_by_collection(collection_id)
        
        # Get all collection variables (with metadata so we get list of dicts)
        collection_variables = self.db.get_collection_variables_with_metadata(collection_id)
        
        # Build folder path map for folders
        folder_paths = {}
        folder_full_paths = {}
        
        def build_folder_path(folder_id):
            """Recursively build path for a folder."""
            folder = next((f for f in folders if f['id'] == folder_id), None)
            if not folder:
                return []
            
            parent_id = folder.get('parent_id')
            if parent_id:
                return build_folder_path(parent_id) + [folder['name']]
            else:
                return [folder['name']]
        
        # Build paths for all folders
        folders_export = []
        for folder in folders:
            parent_path = build_folder_path(folder.get('parent_id')) if folder.get('parent_id') else []
            full_path = parent_path + [folder['name']]
            
            folder_paths[folder['id']] = parent_path
            folder_full_paths[folder['id']] = full_path
            
            folders_export.append({
                'name': folder['name'],
                'path': parent_path,  # Path to parent folder
                'full_path': full_path,  # Full path including this folder
                'order_index': folder.get('order_index')
            })
        
        # Build export structure
        export_data = {
            "export_version": self.EXPORT_VERSION,
            "export_date": datetime.now().isoformat(),
            "collection": {
                "name": collection['name'],
                "order_index": collection.get('order_index'),
                "folders": folders_export,
                "variables": [],
                "requests": []
            }
        }
        
        # Add collection variables
        for var in collection_variables:
            export_data["collection"]["variables"].append({
                "key": var['key'],
                "value": var['value']
            })
        
        # Add all requests with folder paths
        for request in requests:
            folder_path = []
            if request.get('folder_id'):
                folder_path = folder_full_paths.get(request['folder_id'], [])
            
            # Get test assertions for this request
            test_assertions = self.db.get_test_assertions(request['id'])
            tests_export = [
                {
                    "type": test['assertion_type'],
                    "operator": test['operator'],
                    "field": test.get('field'),
                    "expected_value": test.get('expected_value'),
                    "enabled": test.get('enabled', True)
                }
                for test in test_assertions
            ]
            
            request_data = {
                "name": request['name'],
                "method": request['method'],
                "url": request['url'],
                "params": request.get('params'),
                "headers": request.get('headers'),
                "body": request.get('body'),
                "auth_type": request.get('auth_type', 'None'),
                "auth_token": request.get('auth_token'),
                "pre_request_script": request.get('pre_request_script'),
                "post_response_script": request.get('post_response_script'),
                "folder_path": folder_path,
                "order_index": request.get('order_index'),
                "tests": tests_export
            }
            export_data["collection"]["requests"].append(request_data)
        
        return export_data
    
    def export_collection_to_file(self, collection_id: int, file_path: str, format: str = 'internal') -> bool:
        """
        Export a collection to a JSON file.
        
        Args:
            collection_id: ID of the collection to export
            file_path: Path where to save the JSON file
            format: Export format - 'internal' or 'postman' (default: 'internal')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = self.export_collection(collection_id)
            
            # Convert to Postman format if requested
            if format == 'postman':
                export_data = PostmanConverter.to_postman_format(export_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def export_all_collections(self) -> List[Dict]:
        """
        Export all collections.
        
        Returns:
            List of exported collection dictionaries
        """
        collections = self.db.get_all_collections()
        exported = []
        
        for collection in collections:
            try:
                export_data = self.export_collection(collection['id'])
                exported.append(export_data)
            except Exception as e:
                print(f"Failed to export collection {collection['name']}: {e}")
        
        return exported
    
    def export_all_collections_to_file(self, file_path: str) -> bool:
        """
        Export all collections to a single JSON file.
        
        Args:
            file_path: Path where to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            all_collections = self.export_all_collections()
            
            export_data = {
                "export_version": self.EXPORT_VERSION,
                "export_date": datetime.now().isoformat(),
                "collections": all_collections
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False


class CollectionImporter:
    """
    Handles importing collections from JSON format.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize the importer.
        
        Args:
            db: DatabaseManager instance
        """
        self.db = db
    
    def validate_import_data(self, data: Dict) -> Tuple[bool, str]:
        """
        Validate import data structure.
        
        Args:
            data: Dictionary containing import data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for required fields
        if "collection" not in data and "collections" not in data:
            return False, "Invalid format: missing 'collection' or 'collections' key"
        
        # Single collection format
        if "collection" in data:
            collection = data["collection"]
            if "name" not in collection:
                return False, "Collection missing 'name' field"
            if "requests" not in collection:
                return False, "Collection missing 'requests' field"
            
            # Validate requests
            for i, request in enumerate(collection["requests"]):
                if "name" not in request:
                    return False, f"Request {i} missing 'name' field"
                if "method" not in request:
                    return False, f"Request {i} missing 'method' field"
                if "url" not in request:
                    return False, f"Request {i} missing 'url' field"
        
        # Multiple collections format
        elif "collections" in data:
            for i, col_data in enumerate(data["collections"]):
                if "collection" not in col_data:
                    return False, f"Collection {i} missing 'collection' field"
                
                collection = col_data["collection"]
                if "name" not in collection:
                    return False, f"Collection {i} missing 'name' field"
        
        return True, ""
    
    def import_collection(self, data: Dict, 
                         rename_if_exists: bool = False,
                         skip_if_exists: bool = False) -> Tuple[bool, str, Optional[int]]:
        """
        Import a single collection with folders support.
        
        Args:
            data: Dictionary containing collection data
            rename_if_exists: If True, rename collection if name already exists
            skip_if_exists: If True, skip import if collection exists
            
        Returns:
            Tuple of (success, message, collection_id)
        """
        # Validate
        is_valid, error = self.validate_import_data(data)
        if not is_valid:
            return False, error, None
        
        collection_data = data["collection"]
        collection_name = collection_data["name"]
        
        # Check if collection already exists
        existing_collections = self.db.get_all_collections()
        existing_names = [c['name'] for c in existing_collections]
        
        if collection_name in existing_names:
            if skip_if_exists:
                return False, f"Collection '{collection_name}' already exists (skipped)", None
            elif rename_if_exists:
                # Find unique name
                counter = 1
                new_name = f"{collection_name} (imported {counter})"
                while new_name in existing_names:
                    counter += 1
                    new_name = f"{collection_name} (imported {counter})"
                collection_name = new_name
            else:
                return False, f"Collection '{collection_name}' already exists", None
        
        try:
            # Create collection - use order_index from data if present, otherwise it will default to id * 100
            order_index = collection_data.get("order_index")
            collection_id = self.db.create_collection(collection_name, order_index=order_index)
            
            # Import collection variables (if present)
            if "variables" in collection_data:
                for var in collection_data["variables"]:
                    self.db.create_collection_variable(
                        collection_id=collection_id,
                        key=var['key'],
                        value=var.get('value', '')
                    )
            
            # Create folders first (if present) and build a mapping of paths to folder IDs
            folder_map = {}  # Maps tuple of folder path to folder_id
            
            if "folders" in collection_data:
                # Sort folders by depth (shorter paths first) to create parents before children
                folders = sorted(collection_data["folders"], key=lambda f: len(f.get('path', [])))
                
                for idx, folder_info in enumerate(folders):
                    folder_name = folder_info['name']
                    parent_path = tuple(folder_info.get('path', []))  # Convert to tuple for dict key
                    full_path = tuple(folder_info.get('full_path', []))
                    
                    # Get parent folder ID if this is a nested folder
                    parent_id = folder_map.get(parent_path, None)
                    
                    # Use order_index from data if present, otherwise use position in array
                    folder_order_index = folder_info.get('order_index', idx * 100)
                    
                    # Create folder
                    folder_id = self.db.create_folder(collection_id, folder_name, parent_id=parent_id, order_index=folder_order_index)
                    
                    # Store in map for children to reference
                    folder_map[full_path] = folder_id
            
            # Import all requests and link them to their folders
            requests_imported = 0
            for idx, request_data in enumerate(collection_data["requests"]):
                # Determine folder_id for this request
                folder_path = tuple(request_data.get("folder_path", []))  # Convert to tuple for dict key
                folder_id = folder_map.get(folder_path, None)
                
                # Use order_index from data if present, otherwise use position in array
                request_order_index = request_data.get('order_index', idx * 100)
                
                request_id = self.db.create_request(
                    collection_id=collection_id,
                    name=request_data["name"],
                    method=request_data["method"],
                    url=request_data["url"],
                    params=request_data.get("params"),
                    headers=request_data.get("headers"),
                    body=request_data.get("body"),
                    auth_type=request_data.get("auth_type", "None"),
                    auth_token=request_data.get("auth_token"),
                    folder_id=folder_id,  # Link to folder
                    pre_request_script=request_data.get("pre_request_script"),
                    post_response_script=request_data.get("post_response_script"),
                    order_index=request_order_index
                )
                
                # Import test assertions
                for test in request_data.get('tests', []):
                    self.db.create_test_assertion(
                        request_id=request_id,
                        assertion_type=test['type'],
                        operator=test['operator'],
                        field=test.get('field'),
                        expected_value=test.get('expected_value'),
                        enabled=test.get('enabled', True)
                    )
                
                requests_imported += 1
            
            folders_imported = len(folder_map)
            if folders_imported > 0:
                message = f"Imported collection '{collection_name}' with {folders_imported} folder(s) and {requests_imported} request(s)"
            else:
                message = f"Imported collection '{collection_name}' with {requests_imported} request(s)"
            return True, message, collection_id
            
        except Exception as e:
            return False, f"Import failed: {str(e)}", None
    
    def import_collection_from_file(self, file_path: str,
                                   rename_if_exists: bool = False,
                                   skip_if_exists: bool = False) -> Tuple[bool, str, Optional[int]]:
        """
        Import a collection from a JSON file.
        Automatically detects and converts Postman Collection Format v2.1.
        
        Args:
            file_path: Path to the JSON file
            rename_if_exists: If True, rename collection if name already exists
            skip_if_exists: If True, skip import if collection exists
            
        Returns:
            Tuple of (success, message, collection_id)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}", None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Auto-detect and convert Postman format
            if PostmanConverter.is_postman_format(data):
                print(f"Detected Postman Collection Format v2.1 - converting...")
                data = PostmanConverter.from_postman_format(data)
                print(f"Converted successfully: {data['collection']['name']}")
            
            # Handle both single and multiple collection formats
            if "collections" in data:
                # Multiple collections - import first one
                if data["collections"]:
                    return self.import_collection(
                        data["collections"][0], 
                        rename_if_exists, 
                        skip_if_exists
                    )
                else:
                    return False, "No collections found in file", None
            else:
                # Single collection
                return self.import_collection(data, rename_if_exists, skip_if_exists)
                
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON file: {str(e)}", None
        except Exception as e:
            return False, f"Import failed: {str(e)}", None
    
    def import_all_collections_from_file(self, file_path: str,
                                        rename_if_exists: bool = False,
                                        skip_if_exists: bool = False) -> Tuple[bool, str, List[int]]:
        """
        Import all collections from a file.
        
        Args:
            file_path: Path to the JSON file
            rename_if_exists: If True, rename collections if names already exist
            skip_if_exists: If True, skip collections that exist
            
        Returns:
            Tuple of (success, message, list_of_collection_ids)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}", []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collection_ids = []
            messages = []
            
            # Handle both formats
            if "collections" in data:
                # Multiple collections format
                for col_data in data["collections"]:
                    success, message, col_id = self.import_collection(
                        col_data, rename_if_exists, skip_if_exists
                    )
                    if success and col_id:
                        collection_ids.append(col_id)
                    messages.append(message)
            else:
                # Single collection format
                success, message, col_id = self.import_collection(
                    data, rename_if_exists, skip_if_exists
                )
                if success and col_id:
                    collection_ids.append(col_id)
                messages.append(message)
            
            summary = "\n".join(messages)
            if collection_ids:
                return True, f"Imported {len(collection_ids)} collection(s):\n{summary}", collection_ids
            else:
                return False, f"No collections imported:\n{summary}", []
                
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON file: {str(e)}", []
        except Exception as e:
            return False, f"Import failed: {str(e)}", []


def get_safe_filename(collection_name: str) -> str:
    """
    Convert a collection name to a safe filename.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Safe filename string
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    filename = collection_name
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Add timestamp to make it unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename}_{timestamp}.json"
    
    return filename

