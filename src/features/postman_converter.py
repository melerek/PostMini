"""
Postman Collection Format Converter

Handles conversion between our internal format and Postman Collection Format v2.1.
Schema: https://schema.getpostman.com/json/collection/v2.1.0/collection.json
"""

import json
import uuid
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs


class PostmanConverter:
    """
    Converts between our format and Postman Collection Format v2.1.
    """
    
    POSTMAN_SCHEMA = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    
    @staticmethod
    def to_postman_format(collection_data: Dict) -> Dict:
        """
        Convert our internal format to Postman Collection Format v2.1.
        
        Args:
            collection_data: Our internal collection format
            
        Returns:
            Postman-compatible collection dictionary
        """
        collection = collection_data.get('collection', {})
        
        postman_collection = {
            "info": {
                "_postman_id": str(uuid.uuid4()),
                "name": collection.get('name', 'Imported Collection'),
                "schema": PostmanConverter.POSTMAN_SCHEMA,
                "description": f"Exported from API Client on {collection_data.get('export_date', '')}"
            },
            "item": []
        }
        
        # Convert each request to Postman format
        for request in collection.get('requests', []):
            postman_item = PostmanConverter._convert_request_to_postman(request)
            postman_collection["item"].append(postman_item)
        
        return postman_collection
    
    @staticmethod
    def _convert_request_to_postman(request: Dict) -> Dict:
        """
        Convert a single request to Postman item format.
        
        Args:
            request: Our internal request format
            
        Returns:
            Postman item dictionary
        """
        # Parse URL
        url_str = request.get('url', '')
        parsed_url = urlparse(url_str)
        
        # Build Postman URL object
        postman_url = {
            "raw": url_str,
            "protocol": parsed_url.scheme if parsed_url.scheme else "https",
            "host": parsed_url.netloc.split('.') if parsed_url.netloc else [],
            "path": [p for p in parsed_url.path.split('/') if p],
        }
        
        # Add query parameters from URL
        query_params = []
        if parsed_url.query:
            for key, values in parse_qs(parsed_url.query).items():
                for value in values:
                    query_params.append({
                        "key": key,
                        "value": value
                    })
        
        # Add query parameters from params dict
        params = request.get('params')
        if params and isinstance(params, dict):
            for key, value in params.items():
                query_params.append({
                    "key": str(key),
                    "value": str(value)
                })
        
        if query_params:
            postman_url["query"] = query_params
        
        # Build headers array
        headers = []
        request_headers = request.get('headers')
        if request_headers and isinstance(request_headers, dict):
            for key, value in request_headers.items():
                headers.append({
                    "key": str(key),
                    "value": str(value),
                    "type": "text"
                })
        
        # Build request object
        postman_request = {
            "method": request.get('method', 'GET'),
            "header": headers,
            "url": postman_url
        }
        
        # Add body if present
        body = request.get('body')
        if body:
            postman_request["body"] = {
                "mode": "raw",
                "raw": body,
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            }
        
        # Add authentication
        auth_type = request.get('auth_type', 'None')
        auth_token = request.get('auth_token')
        
        if auth_type == 'Bearer Token' and auth_token:
            postman_request["auth"] = {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": auth_token,
                        "type": "string"
                    }
                ]
            }
        
        # Build complete item
        postman_item = {
            "name": request.get('name', 'Unnamed Request'),
            "request": postman_request,
            "response": []
        }
        
        return postman_item
    
    @staticmethod
    def from_postman_format(postman_data: Dict) -> Dict:
        """
        Convert Postman Collection Format v2.1 to our internal format.
        
        Args:
            postman_data: Postman collection dictionary
            
        Returns:
            Our internal collection format with folders and requests
        """
        info = postman_data.get('info', {})
        
        internal_format = {
            "export_version": "1.0",
            "source": "postman",
            "postman_id": info.get('_postman_id'),
            "collection": {
                "name": info.get('name', 'Imported Collection'),
                "description": info.get('description', ''),
                "folders": [],  # List of folders with hierarchy info
                "requests": []  # List of requests with folder_path info
            }
        }
        
        # Convert each Postman item to our format (recursively)
        items = postman_data.get('item', [])
        PostmanConverter._process_items_recursively(
            items, 
            internal_format["collection"]["folders"],
            internal_format["collection"]["requests"],
            folder_path=[]
        )
        
        return internal_format
    
    @staticmethod
    def _process_items_recursively(items: List[Dict], folders_list: List[Dict], 
                                   requests_list: List[Dict], folder_path: List[str]):
        """
        Recursively process Postman items and extract all folders and requests.
        
        Args:
            items: List of Postman items (can be folders or requests)
            folders_list: List to append folder definitions to
            requests_list: List to append converted requests to
            folder_path: Current folder path as list of folder names (e.g., ["v6", "internal"])
        """
        for item in items:
            # Check if this is a folder (has nested items)
            if 'item' in item and isinstance(item['item'], list):
                # It's a folder
                folder_name = item.get('name', 'Unnamed Folder')
                current_path = folder_path + [folder_name]
                
                # Add folder definition
                folders_list.append({
                    'name': folder_name,
                    'path': folder_path.copy(),  # Parent path (list of parent folder names)
                    'full_path': current_path.copy()  # Full path including this folder
                })
                
                # Recursively process items inside this folder
                PostmanConverter._process_items_recursively(
                    item['item'], 
                    folders_list, 
                    requests_list, 
                    current_path
                )
            else:
                # It's a request, convert it
                request = PostmanConverter._convert_postman_item_to_request(item, folder_path)
                if request:
                    requests_list.append(request)
    
    @staticmethod
    def _convert_postman_item_to_request(item: Dict, folder_path: List[str]) -> Optional[Dict]:
        """
        Convert a Postman item to our internal request format.
        
        Args:
            item: Postman item dictionary
            folder_path: List of folder names representing the path (e.g., ["v6", "internal"])
            
        Returns:
            Our internal request format with folder_path, or None if invalid
        """
        request_data = item.get('request')
        if not request_data:
            return None
        
        # Handle string-only request (simple format)
        if isinstance(request_data, str):
            return {
                "name": item.get('name', 'Unnamed Request'),
                "folder_path": folder_path.copy(),  # Store folder path as list
                "method": "GET",
                "url": request_data,
                "params": None,
                "headers": None,
                "body": None,
                "auth_type": "None",
                "auth_token": None
            }
        
        # Get request name (without folder prefix - folders are handled separately)
        name = item.get('name', 'Unnamed Request')
        
        # Extract URL
        url_data = request_data.get('url', {})
        if isinstance(url_data, str):
            url = url_data
        else:
            url = url_data.get('raw', '')
        
        # Extract headers
        headers = {}
        for header in request_data.get('header', []):
            if not header.get('disabled', False):
                headers[header.get('key', '')] = header.get('value', '')
        
        # Extract query parameters
        params = {}
        if isinstance(url_data, dict):
            for query in url_data.get('query', []):
                if not query.get('disabled', False):
                    params[query.get('key', '')] = query.get('value', '')
        
        # Extract body
        body = None
        body_data = request_data.get('body', {})
        if body_data:
            mode = body_data.get('mode', 'raw')
            if mode == 'raw':
                body = body_data.get('raw', '')
            elif mode == 'formdata':
                # Convert form data to JSON
                form_data = {}
                for item_data in body_data.get('formdata', []):
                    if not item_data.get('disabled', False):
                        form_data[item_data.get('key', '')] = item_data.get('value', '')
                body = json.dumps(form_data)
            elif mode == 'urlencoded':
                # Convert urlencoded to JSON
                urlencoded_data = {}
                for item_data in body_data.get('urlencoded', []):
                    if not item_data.get('disabled', False):
                        urlencoded_data[item_data.get('key', '')] = item_data.get('value', '')
                body = json.dumps(urlencoded_data)
        
        # Extract authentication
        auth_type = "None"
        auth_token = None
        auth_data = request_data.get('auth', {})
        
        if auth_data:
            auth_type_postman = auth_data.get('type', '')
            
            if auth_type_postman == 'bearer':
                auth_type = "Bearer Token"
                bearer_data = auth_data.get('bearer', [])
                for bearer_item in bearer_data:
                    if bearer_item.get('key') == 'token':
                        auth_token = bearer_item.get('value', '')
                        break
            elif auth_type_postman == 'apikey':
                # Map API key to Bearer Token
                auth_type = "Bearer Token"
                apikey_data = auth_data.get('apikey', [])
                for apikey_item in apikey_data:
                    if apikey_item.get('key') == 'value':
                        auth_token = apikey_item.get('value', '')
                        break
        
        return {
            "name": name,
            "folder_path": folder_path.copy(),  # Store folder path as list
            "method": request_data.get('method', 'GET'),
            "url": url,
            "params": params if params else None,
            "headers": headers if headers else None,
            "body": body,
            "auth_type": auth_type,
            "auth_token": auth_token
        }
    
    @staticmethod
    def is_postman_format(data: Dict) -> bool:
        """
        Detect if a dictionary is in Postman format.
        
        Args:
            data: Dictionary to check
            
        Returns:
            True if Postman format, False otherwise
        """
        # Check for Postman-specific keys
        if 'info' in data and 'item' in data:
            info = data.get('info', {})
            # Check for schema or _postman_id
            if 'schema' in info or '_postman_id' in info:
                return True
        return False
    
    @staticmethod
    def detect_format(file_path: str) -> str:
        """
        Detect the format of a collection file.
        
        Args:
            file_path: Path to the collection file
            
        Returns:
            'postman' or 'internal' or 'unknown'
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if PostmanConverter.is_postman_format(data):
                return 'postman'
            elif 'export_version' in data and 'collection' in data:
                return 'internal'
            else:
                return 'unknown'
        except Exception:
            return 'unknown'

