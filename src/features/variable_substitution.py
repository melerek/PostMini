"""
Variable Substitution Utility

This module provides utilities for substituting environment variables in strings.
Variables are defined using {{variableName}} syntax and can be used in URLs,
headers, parameters, body, and authentication tokens.
"""

import re
from typing import Dict, Tuple, List


class VariableSubstitution:
    """
    Handles variable substitution with support for {{variable}} syntax.
    """
    
    # Regex pattern to match {{variableName}}
    VARIABLE_PATTERN = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
    
    @staticmethod
    def substitute(text: str, variables: Dict[str, str]) -> Tuple[str, List[str]]:
        """
        Replace all {{variable}} occurrences in text with their values.
        
        Args:
            text: The text containing variables to substitute
            variables: Dictionary of variable names to values
            
        Returns:
            Tuple of (substituted_text, list_of_unresolved_variables)
            
        Example:
            >>> variables = {'baseUrl': 'https://api.example.com', 'version': 'v1'}
            >>> substitute('{{baseUrl}}/{{version}}/users', variables)
            ('https://api.example.com/v1/users', [])
        """
        if not text:
            return text, []
        
        unresolved = []
        
        def replace_func(match):
            var_name = match.group(1)
            if var_name in variables:
                return str(variables[var_name])
            else:
                unresolved.append(var_name)
                return match.group(0)  # Keep original {{var}} if not found
        
        result = VariableSubstitution.VARIABLE_PATTERN.sub(replace_func, text)
        return result, unresolved
    
    @staticmethod
    def substitute_dict(data: Dict, variables: Dict[str, str]) -> Tuple[Dict, List[str]]:
        """
        Substitute variables in all values of a dictionary.
        
        Args:
            data: Dictionary with values that may contain variables
            variables: Dictionary of variable names to values
            
        Returns:
            Tuple of (substituted_dict, list_of_unresolved_variables)
        """
        if not data:
            return data, []
        
        result = {}
        all_unresolved = []
        
        for key, value in data.items():
            # Substitute in both key and value
            new_key, unresolved_key = VariableSubstitution.substitute(str(key), variables)
            new_value, unresolved_value = VariableSubstitution.substitute(str(value), variables)
            
            result[new_key] = new_value
            all_unresolved.extend(unresolved_key)
            all_unresolved.extend(unresolved_value)
        
        # Remove duplicates
        all_unresolved = list(set(all_unresolved))
        
        return result, all_unresolved
    
    @staticmethod
    def find_variables(text: str) -> List[str]:
        """
        Find all variable names in the text.
        
        Args:
            text: The text to search for variables
            
        Returns:
            List of variable names found (without {{}} syntax)
            
        Example:
            >>> find_variables('{{baseUrl}}/{{version}}/users?key={{apiKey}}')
            ['baseUrl', 'version', 'apiKey']
        """
        if not text:
            return []
        
        matches = VariableSubstitution.VARIABLE_PATTERN.findall(text)
        return list(set(matches))  # Remove duplicates
    
    @staticmethod
    def validate_variable_name(name: str) -> bool:
        """
        Check if a variable name is valid.
        Variable names must start with a letter or underscore,
        followed by letters, numbers, or underscores.
        
        Args:
            name: Variable name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not name:
            return False
        
        pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        return bool(pattern.match(name))
    
    @staticmethod
    def format_variable(name: str) -> str:
        """
        Format a variable name with {{}} syntax.
        
        Args:
            name: Variable name
            
        Returns:
            Formatted variable string
            
        Example:
            >>> format_variable('baseUrl')
            '{{baseUrl}}'
        """
        return f"{{{{{name}}}}}"
    
    @staticmethod
    def extract_variable_name(formatted: str) -> str:
        """
        Extract variable name from {{variableName}} format.
        
        Args:
            formatted: Variable in {{name}} format
            
        Returns:
            Variable name without braces, or original string if not in correct format
            
        Example:
            >>> extract_variable_name('{{baseUrl}}')
            'baseUrl'
        """
        match = VariableSubstitution.VARIABLE_PATTERN.match(formatted)
        if match:
            return match.group(1)
        return formatted


class EnvironmentManager:
    """
    Manager for handling active environment and variable resolution.
    """
    
    def __init__(self):
        self.active_environment = None
        self.active_variables = {}
    
    def set_active_environment(self, environment: Dict):
        """
        Set the active environment.
        
        Args:
            environment: Dictionary with 'id', 'name', and 'variables' keys
        """
        self.active_environment = environment
        self.active_variables = environment.get('variables', {}) if environment else {}
    
    def clear_active_environment(self):
        """Clear the active environment."""
        self.active_environment = None
        self.active_variables = {}
    
    def get_active_environment_name(self) -> str:
        """Get the name of the active environment."""
        if self.active_environment:
            return self.active_environment.get('name', 'Unknown')
        return 'No Environment'
    
    def has_active_environment(self) -> bool:
        """Check if there is an active environment."""
        return self.active_environment is not None
    
    def substitute_in_request(self, url: str, params: Dict, headers: Dict, 
                            body: str, auth_token: str) -> Tuple[Dict, List[str]]:
        """
        Substitute variables in all request components.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            body: Request body
            auth_token: Authentication token
            
        Returns:
            Tuple of (substituted_data_dict, unresolved_variables_list)
            
        The returned dictionary contains:
            - url: Substituted URL
            - params: Substituted parameters dict
            - headers: Substituted headers dict
            - body: Substituted body
            - auth_token: Substituted auth token
        """
        all_unresolved = []
        
        # Substitute URL
        new_url, unresolved = VariableSubstitution.substitute(url, self.active_variables)
        all_unresolved.extend(unresolved)
        
        # Substitute params
        new_params, unresolved = VariableSubstitution.substitute_dict(
            params or {}, self.active_variables
        )
        all_unresolved.extend(unresolved)
        
        # Substitute headers
        new_headers, unresolved = VariableSubstitution.substitute_dict(
            headers or {}, self.active_variables
        )
        all_unresolved.extend(unresolved)
        
        # Substitute body
        new_body, unresolved = VariableSubstitution.substitute(
            body or '', self.active_variables
        )
        all_unresolved.extend(unresolved)
        
        # Substitute auth token
        new_auth_token, unresolved = VariableSubstitution.substitute(
            auth_token or '', self.active_variables
        )
        all_unresolved.extend(unresolved)
        
        # Remove duplicate unresolved variables
        all_unresolved = list(set(all_unresolved))
        
        result = {
            'url': new_url,
            'params': new_params,
            'headers': new_headers,
            'body': new_body,
            'auth_token': new_auth_token
        }
        
        return result, all_unresolved

