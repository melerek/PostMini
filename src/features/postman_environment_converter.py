"""
Postman Environment Format Converter

Handles conversion between our internal environment format and Postman Environment Format.
Postman Environment Schema: https://schema.postman.com/json/collection/v2.1.0/

Internal Format:
{
    "export_version": "1.0",
    "export_date": "ISO timestamp",
    "environment": {
        "id": int,
        "name": "string",
        "variables": {
            "key": "value",
            ...
        }
    }
}

Postman Format:
{
    "id": "uuid",
    "name": "Environment Name",
    "values": [
        {
            "key": "variableName",
            "value": "variableValue",
            "enabled": true,
            "type": "default|secret"
        }
    ],
    "_postman_variable_scope": "environment",
    "_postman_exported_at": "ISO timestamp",
    "_postman_exported_using": "Postman/version"
}
"""

import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime


class PostmanEnvironmentConverter:
    """
    Converts between our format and Postman Environment Format.
    """
    
    POSTMAN_SCOPE = "environment"
    POSTMAN_EXPORTED_USING = "PostMini API Client"
    
    # Keywords that indicate a variable should be marked as secret in Postman
    SECRET_KEYWORDS = ['secret', 'key', 'token', 'password', 'auth', 'api_key', 'apikey', 
                       'credential', 'private', 'sensitive']
    
    @staticmethod
    def to_postman_format(environment_data: Dict, include_secrets: bool = True) -> Dict:
        """
        Convert our internal format to Postman Environment Format.
        
        Args:
            environment_data: Our internal environment format
            include_secrets: If False, replace secret values with placeholders
            
        Returns:
            Postman-compatible environment dictionary
        """
        environment = environment_data.get('environment', {})
        variables = environment.get('variables', {})
        
        # Convert variables dict to Postman values array
        postman_values = []
        for key, value in variables.items():
            # Determine if this is a secret variable
            is_secret = PostmanEnvironmentConverter._is_secret_variable(key)
            
            # Handle secret masking if requested
            actual_value = value
            if is_secret and not include_secrets:
                actual_value = f"{{{{SECRET_{key}}}}}"
            
            postman_values.append({
                "key": key,
                "value": actual_value,
                "enabled": True,
                "type": "secret" if is_secret else "default"
            })
        
        # Build Postman environment
        postman_env = {
            "id": str(uuid.uuid4()),
            "name": environment.get('name', 'Imported Environment'),
            "values": postman_values,
            "_postman_variable_scope": PostmanEnvironmentConverter.POSTMAN_SCOPE,
            "_postman_exported_at": datetime.now().isoformat() + "Z",
            "_postman_exported_using": PostmanEnvironmentConverter.POSTMAN_EXPORTED_USING
        }
        
        return postman_env
    
    @staticmethod
    def from_postman_format(postman_data: Dict) -> Dict:
        """
        Convert Postman Environment Format to our internal format.
        
        Args:
            postman_data: Postman environment dictionary
            
        Returns:
            Our internal environment format
        """
        postman_values = postman_data.get('values', [])
        
        # Convert Postman values array to our variables dict
        variables = {}
        for item in postman_values:
            key = item.get('key', '')
            value = item.get('value', '')
            enabled = item.get('enabled', True)
            
            # Only include enabled variables
            # Disabled variables can be stored with a special prefix if needed
            if enabled:
                variables[key] = value
            else:
                # Store disabled variables with a comment prefix
                # Users can manually re-enable them if needed
                variables[f"_DISABLED_{key}"] = value
        
        # Build internal format
        internal_format = {
            "export_version": "1.0",
            "export_date": datetime.now().isoformat(),
            "source": "postman",
            "postman_id": postman_data.get('id'),
            "environment": {
                "name": postman_data.get('name', 'Imported Environment'),
                "variables": variables
            }
        }
        
        return internal_format
    
    @staticmethod
    def is_postman_format(data: Dict) -> bool:
        """
        Check if the given dictionary is in Postman Environment Format.
        
        Args:
            data: Dictionary to check
            
        Returns:
            True if it's Postman format, False otherwise
        """
        # Postman environments have specific fields
        has_scope = '_postman_variable_scope' in data
        has_values = 'values' in data and isinstance(data.get('values'), list)
        
        # Our internal format has 'environment' key with nested structure
        has_internal_structure = 'environment' in data and isinstance(data.get('environment'), dict)
        
        # It's Postman format if it has the Postman-specific fields and NOT our internal structure
        return has_scope and has_values and not has_internal_structure
    
    @staticmethod
    def _is_secret_variable(key: str) -> bool:
        """
        Determine if a variable should be treated as a secret based on its name.
        
        Args:
            key: Variable name
            
        Returns:
            True if the variable appears to be a secret
        """
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in PostmanEnvironmentConverter.SECRET_KEYWORDS)
    
    @staticmethod
    def validate_postman_environment(data: Dict) -> tuple[bool, str]:
        """
        Validate a Postman environment structure.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"
        
        if '_postman_variable_scope' not in data:
            return False, "Missing '_postman_variable_scope' field"
        
        if data.get('_postman_variable_scope') != 'environment':
            return False, "Invalid variable scope, must be 'environment'"
        
        if 'name' not in data:
            return False, "Missing 'name' field"
        
        if 'values' not in data:
            return False, "Missing 'values' field"
        
        if not isinstance(data.get('values'), list):
            return False, "'values' must be an array"
        
        # Validate each value entry
        for idx, value in enumerate(data.get('values', [])):
            if not isinstance(value, dict):
                return False, f"Value at index {idx} must be a dictionary"
            
            if 'key' not in value:
                return False, f"Value at index {idx} missing 'key' field"
            
            if 'value' not in value:
                return False, f"Value at index {idx} missing 'value' field"
        
        return True, "Valid Postman environment"
    
    @staticmethod
    def get_variable_count(data: Dict) -> int:
        """
        Get the number of variables in an environment (works for both formats).
        
        Args:
            data: Environment data (either format)
            
        Returns:
            Number of variables
        """
        if PostmanEnvironmentConverter.is_postman_format(data):
            return len(data.get('values', []))
        else:
            # Internal format
            environment = data.get('environment', {})
            variables = environment.get('variables', {})
            return len(variables)
