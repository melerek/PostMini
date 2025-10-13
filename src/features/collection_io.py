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
        Export a single collection with all its requests to a dictionary.
        
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
        
        # Build export structure
        export_data = {
            "export_version": self.EXPORT_VERSION,
            "export_date": datetime.now().isoformat(),
            "collection": {
                "name": collection['name'],
                "requests": []
            }
        }
        
        # Add all requests
        for request in requests:
            request_data = {
                "name": request['name'],
                "method": request['method'],
                "url": request['url'],
                "params": request.get('params'),
                "headers": request.get('headers'),
                "body": request.get('body'),
                "auth_type": request.get('auth_type', 'None'),
                "auth_token": request.get('auth_token')
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
        Import a single collection.
        
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
            # Create collection
            collection_id = self.db.create_collection(collection_name)
            
            # Import all requests
            requests_imported = 0
            for request_data in collection_data["requests"]:
                self.db.create_request(
                    collection_id=collection_id,
                    name=request_data["name"],
                    method=request_data["method"],
                    url=request_data["url"],
                    params=request_data.get("params"),
                    headers=request_data.get("headers"),
                    body=request_data.get("body"),
                    auth_type=request_data.get("auth_type", "None"),
                    auth_token=request_data.get("auth_token")
                )
                requests_imported += 1
            
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

