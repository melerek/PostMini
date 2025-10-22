"""
Variable Extractor Module

This module provides functionality to extract values from API responses and save them
as variables for use in subsequent requests (request chaining).
"""

import json
import re
from typing import Any, Optional, Dict, List
from src.core.api_client import ApiResponse


class VariableExtractor:
    """
    Utility class for extracting values from API responses using various methods.
    """
    
    @staticmethod
    def extract_from_json_path(response: ApiResponse, json_path: str) -> Optional[Any]:
        """
        Extract value from JSON response using simple dot notation path.
        
        Args:
            response: API response object
            json_path: Path like "data.user.id" or "items[0].name"
            
        Returns:
            Extracted value or None if not found/error
            
        Examples:
            "data.token" -> response.data.token
            "user.id" -> response.user.id
            "items[0].name" -> response.items[0].name
            "meta.pagination.total" -> response.meta.pagination.total
        """
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return None
        
        return VariableExtractor._extract_json_value(data, json_path)
    
    @staticmethod
    def extract_from_header(response: ApiResponse, header_name: str) -> Optional[str]:
        """
        Extract value from response header.
        
        Args:
            response: API response object
            header_name: Name of header (case-insensitive)
            
        Returns:
            Header value or None if not found
            
        Examples:
            "Authorization" -> "Bearer token123"
            "X-Request-ID" -> "abc-123-def"
        """
        # Case-insensitive header lookup
        for key, value in response.headers.items():
            if key.lower() == header_name.lower():
                return value
        return None
    
    @staticmethod
    def extract_from_regex(response: ApiResponse, pattern: str, group: int = 1) -> Optional[str]:
        """
        Extract value using regex pattern.
        
        Args:
            response: API response object
            pattern: Regular expression pattern
            group: Capture group to extract (default: 1)
            
        Returns:
            Matched value or None if not found
            
        Examples:
            pattern="token\\":\\s*\\"([^"]+)\\"" -> extracts token value
            pattern="id=(\\d+)" -> extracts numeric ID
        """
        try:
            match = re.search(pattern, response.text)
            if match:
                return match.group(group)
        except (re.error, IndexError):
            pass
        return None
    
    @staticmethod
    def _extract_json_value(data: Any, path: str) -> Any:
        """
        Extract value from JSON using dot notation path.
        
        Args:
            data: JSON data (dict or list)
            path: Dot notation path (e.g., "user.profile.email")
            
        Returns:
            Extracted value or None if path doesn't exist
        """
        parts = path.split('.')
        current = data
        
        for part in parts:
            # Handle array indexing (e.g., "items[0]")
            if '[' in part and ']' in part:
                field = part[:part.index('[')]
                index = int(part[part.index('[') + 1:part.index(']')])
                
                if field:
                    if isinstance(current, dict):
                        current = current.get(field)
                    else:
                        return None
                
                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
                
                if current is None:
                    return None
        
        return current
    
    @staticmethod
    def get_suggested_variables(response: ApiResponse) -> List[Dict[str, str]]:
        """
        Analyze response and suggest common variables to extract.
        
        Args:
            response: API response object
            
        Returns:
            List of suggestions with format:
            [{"name": "token", "path": "data.token", "value": "abc123"}, ...]
        """
        suggestions = []
        
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return suggestions
        
        # Common patterns to look for
        common_keys = [
            ('token', ['token', 'access_token', 'accessToken', 'auth_token', 'authToken']),
            ('refreshToken', ['refresh_token', 'refreshToken']),
            ('userId', ['id', 'user_id', 'userId', 'user.id']),
            ('sessionId', ['session_id', 'sessionId', 'session.id']),
            ('apiKey', ['api_key', 'apiKey', 'key']),
        ]
        
        def search_dict(obj: Any, prefix: str = ''):
            """Recursively search dictionary for common keys."""
            if not isinstance(obj, dict):
                return
            
            for key, value in obj.items():
                current_path = f"{prefix}.{key}" if prefix else key
                
                # Check if this key matches any common pattern
                for suggested_name, patterns in common_keys:
                    if key.lower() in patterns:
                        # Don't include complex objects, only primitives
                        if isinstance(value, (str, int, float, bool)):
                            suggestions.append({
                                'name': suggested_name,
                                'path': current_path,
                                'value': str(value)
                            })
                            break
                
                # Recurse into nested objects
                if isinstance(value, dict):
                    search_dict(value, current_path)
                elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    # Check first item in array
                    search_dict(value[0], f"{current_path}[0]")
        
        search_dict(data)
        return suggestions


class ExtractionRule:
    """Represents a rule for extracting a variable from a response."""
    
    def __init__(self, variable_name: str, extraction_type: str, 
                 json_path: Optional[str] = None,
                 header_name: Optional[str] = None,
                 regex_pattern: Optional[str] = None,
                 description: Optional[str] = None):
        """
        Initialize extraction rule.
        
        Args:
            variable_name: Name to save extracted value as
            extraction_type: Type of extraction ('json_path', 'header', 'regex')
            json_path: JSONPath for JSON extraction
            header_name: Header name for header extraction
            regex_pattern: Regex pattern for regex extraction
            description: Optional description of what this variable is for
        """
        self.variable_name = variable_name
        self.extraction_type = extraction_type
        self.json_path = json_path
        self.header_name = header_name
        self.regex_pattern = regex_pattern
        self.description = description
    
    def extract(self, response: ApiResponse) -> Optional[Any]:
        """
        Execute this extraction rule on a response.
        
        Args:
            response: API response object
            
        Returns:
            Extracted value or None if extraction fails
        """
        if self.extraction_type == 'json_path' and self.json_path:
            return VariableExtractor.extract_from_json_path(response, self.json_path)
        
        elif self.extraction_type == 'header' and self.header_name:
            return VariableExtractor.extract_from_header(response, self.header_name)
        
        elif self.extraction_type == 'regex' and self.regex_pattern:
            return VariableExtractor.extract_from_regex(response, self.regex_pattern)
        
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'variable_name': self.variable_name,
            'extraction_type': self.extraction_type,
            'json_path': self.json_path,
            'header_name': self.header_name,
            'regex_pattern': self.regex_pattern,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExtractionRule':
        """Create from dictionary."""
        return cls(
            variable_name=data['variable_name'],
            extraction_type=data['extraction_type'],
            json_path=data.get('json_path'),
            header_name=data.get('header_name'),
            regex_pattern=data.get('regex_pattern'),
            description=data.get('description')
        )

