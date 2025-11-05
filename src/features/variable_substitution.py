"""
Variable Substitution Utility

This module provides utilities for substituting variables in strings.
Variables use prefixed syntax to differentiate scopes:
- {{env.variable}} - Environment variables
- {{col.variable}} - Collection variables
- {{ext.variable}} - Extracted variables (from responses)
- {{$variable}} - Dynamic variables (auto-generated)

For backward compatibility, {{variable}} without prefix will check all scopes.
"""

import re
from typing import Dict, Tuple, List
from .dynamic_variables import resolve_dynamic_variable


class VariableSubstitution:
    """
    Handles variable substitution with support for:
    - {{env.variable}} - Environment variables (explicit)
    - {{col.variable}} - Collection variables (explicit)
    - {{ext.variable}} - Extracted variables (explicit)
    - {{$variable}} - Dynamic variables (explicit)
    - {{variable}} - Any scope (backward compatibility - checks all scopes)
    """
    
    # Regex pattern to match {{prefix.variableName}} or {{variableName}} or {{$variableName}}
    VARIABLE_PATTERN = re.compile(r'\{\{(?:(env|col|ext|\$)\.)?([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
    
    # Legacy pattern for backward compatibility (kept for reference but handled by main pattern)
    LEGACY_VARIABLE_PATTERN = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
    
    @staticmethod
    def substitute(text: str, env_variables: Dict[str, str] = None, 
                   collection_variables: Dict[str, str] = None,
                   extracted_variables: Dict[str, str] = None) -> Tuple[str, List[str]]:
        """
        Replace all variable occurrences in text with their values using new prefix syntax.
        
        Supported syntax:
        - {{env.variable}} - Environment variables (explicit)
        - {{col.variable}} - Collection variables (explicit)
        - {{ext.variable}} - Extracted variables (explicit)
        - {{$variable}} - Dynamic variables (explicit)
        - {{variable}} - Any scope (checks all in priority: extracted > collection > environment)
        
        Args:
            text: The text containing variables to substitute
            env_variables: Dictionary of environment variable names to values
            collection_variables: Dictionary of collection variable names to values
            extracted_variables: Dictionary of extracted variable names to values
            
        Returns:
            Tuple of (substituted_text, list_of_unresolved_variables)
            
        Example:
            >>> env_vars = {'baseUrl': 'https://api.example.com'}
            >>> col_vars = {'version': 'v1'}
            >>> ext_vars = {'authToken': 'abc123'}
            >>> substitute('{{env.baseUrl}}/{{col.version}}/users?token={{ext.authToken}}', env_vars, col_vars, ext_vars)
            ('https://api.example.com/v1/users?token=abc123', [])
        """
        if not text:
            return text, []
        
        if env_variables is None:
            env_variables = {}
        if collection_variables is None:
            collection_variables = {}
        if extracted_variables is None:
            extracted_variables = {}
        
        unresolved = []
        
        # Substitute all variables with new syntax
        def replace_variable(match):
            prefix = match.group(1)  # env, col, ext, $ or None
            var_name = match.group(2)  # The variable name
            
            # Handle dynamic variables with {{$variable}} syntax
            if prefix == '$':
                resolved = resolve_dynamic_variable(f'${var_name}')
                # If not resolved (same as input), it's unresolved
                if resolved == f'${var_name}':
                    unresolved.append(f'{{{{${var_name}}}}}')
                return resolved
            
            # Handle explicit environment variables {{env.variable}}
            elif prefix == 'env':
                if var_name in env_variables:
                    return str(env_variables[var_name])
                else:
                    unresolved.append(f'{{{{env.{var_name}}}}}')
                    return match.group(0)  # Keep original if not found
            
            # Handle explicit collection variables {{col.variable}}
            elif prefix == 'col':
                if var_name in collection_variables:
                    return str(collection_variables[var_name])
                else:
                    unresolved.append(f'{{{{col.{var_name}}}}}')
                    return match.group(0)  # Keep original if not found
            
            # Handle explicit extracted variables {{ext.variable}}
            elif prefix == 'ext':
                if var_name in extracted_variables:
                    return str(extracted_variables[var_name])
                else:
                    unresolved.append(f'{{{{ext.{var_name}}}}}')
                    return match.group(0)  # Keep original if not found
            
            # No prefix - backward compatibility: check all scopes (priority: extracted > collection > environment)
            else:
                if var_name in extracted_variables:
                    return str(extracted_variables[var_name])
                elif var_name in collection_variables:
                    return str(collection_variables[var_name])
                elif var_name in env_variables:
                    return str(env_variables[var_name])
                else:
                    unresolved.append(f'{{{{{var_name}}}}}')
                    return match.group(0)  # Keep original {{var}} if not found
        
        result = VariableSubstitution.VARIABLE_PATTERN.sub(replace_variable, text)
        return result, unresolved
    
    @staticmethod
    def substitute_dict(data: Dict, env_variables: Dict[str, str] = None,
                       collection_variables: Dict[str, str] = None,
                       extracted_variables: Dict[str, str] = None) -> Tuple[Dict, List[str]]:
        """
        Substitute variables in all values of a dictionary.
        
        Args:
            data: Dictionary with values that may contain variables
            env_variables: Dictionary of environment variable names to values
            collection_variables: Dictionary of collection variable names to values
            extracted_variables: Dictionary of extracted variable names to values
            
        Returns:
            Tuple of (substituted_dict, list_of_unresolved_variables)
        """
        if not data:
            return data, []
        
        result = {}
        all_unresolved = []
        
        for key, value in data.items():
            # Substitute in both key and value
            new_key, unresolved_key = VariableSubstitution.substitute(
                str(key), env_variables, collection_variables, extracted_variables
            )
            new_value, unresolved_value = VariableSubstitution.substitute(
                str(value), env_variables, collection_variables, extracted_variables
            )
            
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
    
    def __init__(self, db=None):
        self.active_environment = None
        self.active_variables = {}
        self.extracted_variables = {}  # For extracted variables from responses
        self.db = db  # Database manager for persisting environment variable changes
    
    def set_extracted_variables(self, extracted_vars: Dict[str, str]):
        """
        Set extracted variables (from database).
        
        Args:
            extracted_vars: Dictionary of extracted variable names to values
        """
        self.extracted_variables = extracted_vars
    
    def get_extracted_variables(self) -> Dict[str, str]:
        """Get the extracted variables."""
        return self.extracted_variables.copy()
    
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
    
    def get_active_variables(self) -> Dict[str, str]:
        """Get the active environment variables."""
        return self.active_variables.copy()
    
    def set_variable(self, key: str, value: str):
        """
        Set an environment variable (updates both in-memory and database).
        
        Args:
            key: Variable name
            value: Variable value
        """
        if not self.has_active_environment():
            return
        
        # Update in-memory
        self.active_variables[key] = value
        
        # Update in database if we have a db reference
        if self.db and self.active_environment:
            env_id = self.active_environment.get('id')
            if env_id:
                # Get current environment from database
                env = self.db.get_environment(env_id)
                if env:
                    # Update the variables dict
                    variables = env.get('variables', {})
                    variables[key] = value
                    # Save back to database
                    self.db.update_environment(env_id, env['name'], variables)
                    # Update our cached environment data
                    self.active_environment['variables'] = variables
    
    def substitute_in_request(self, url: str, params: Dict, headers: Dict, 
                            body: str, auth_token: str, collection_variables: Dict = None) -> Tuple[Dict, List[str]]:
        """
        Substitute variables in all request components using new prefix syntax.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            body: Request body
            auth_token: Authentication token
            collection_variables: Collection variables (separate from environment)
            
        Returns:
            Tuple of (substituted_data_dict, unresolved_variables_list)
            
        The returned dictionary contains:
            - url: Substituted URL
            - params: Substituted parameters dict
            - headers: Substituted headers dict
            - body: Substituted body
            - auth_token: Substituted auth token
        """
        if collection_variables is None:
            collection_variables = {}
        
        all_unresolved = []
        
        # Substitute URL
        new_url, unresolved = VariableSubstitution.substitute(
            url, self.active_variables, collection_variables, self.extracted_variables
        )
        all_unresolved.extend(unresolved)
        
        # Substitute params
        new_params, unresolved = VariableSubstitution.substitute_dict(
            params, self.active_variables, collection_variables, self.extracted_variables
        ) if params else ({}, [])
        all_unresolved.extend(unresolved)
        
        # Substitute headers
        new_headers, unresolved = VariableSubstitution.substitute_dict(
            headers, self.active_variables, collection_variables, self.extracted_variables
        ) if headers else ({}, [])
        all_unresolved.extend(unresolved)
        
        # Substitute body
        new_body, unresolved = VariableSubstitution.substitute(
            body, self.active_variables, collection_variables, self.extracted_variables
        ) if body else ('', [])
        all_unresolved.extend(unresolved)
        
        # Substitute auth token
        new_auth_token, unresolved = VariableSubstitution.substitute(
            auth_token, self.active_variables, collection_variables, self.extracted_variables
        ) if auth_token else ('', [])
        all_unresolved.extend(unresolved)
        
        # Remove duplicates from unresolved list
        all_unresolved = list(set(all_unresolved))
        
        return {
            'url': new_url,
            'params': new_params,
            'headers': new_headers,
            'body': new_body,
            'auth_token': new_auth_token
        }, all_unresolved


