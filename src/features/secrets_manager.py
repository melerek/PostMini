"""
Secrets Manager Module

Manages separation of shared environment configurations from local secrets.
Shared configs are committed to Git, secrets are stored locally and gitignored.
"""

import json
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path


class SecretsManager:
    """
    Manages secrets separation and variable substitution.
    """
    
    # Keywords that indicate a variable contains sensitive data
    SECRET_KEYWORDS = [
        'secret', 'key', 'token', 'password', 'auth', 'credential',
        'api_key', 'apikey', 'access_token', 'refresh_token', 'bearer'
    ]
    
    def __init__(self, secrets_dir: str):
        """
        Initialize secrets manager.
        
        Args:
            secrets_dir: Path to .postmini-secrets directory
        """
        self.secrets_dir = Path(secrets_dir)
        self.secrets_file = self.secrets_dir / "local-secrets.json"
        self._secrets_cache = {}
    
    def is_secret_variable(self, variable_name: str) -> bool:
        """
        Determine if a variable name indicates it contains a secret.
        
        Args:
            variable_name: Name of the variable
            
        Returns:
            True if variable appears to be a secret
        """
        lower_name = variable_name.lower()
        return any(keyword in lower_name for keyword in self.SECRET_KEYWORDS)
    
    def separate_secrets(self, environment_name: str, variables: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Separate variables into public (shareable) and secrets (local only).
        
        Args:
            environment_name: Name of the environment
            variables: Dictionary of all variables
            
        Returns:
            Tuple of (public_variables, secrets)
            - public_variables: Variables safe to commit (with placeholders for secrets)
            - secrets: Secret values to store locally
        """
        public_vars = {}
        secrets = {}
        
        for key, value in variables.items():
            if self.is_secret_variable(key):
                # Replace with placeholder
                placeholder_key = f"SECRET_{environment_name.upper()}_{key.upper()}"
                public_vars[key] = f"{{{{{placeholder_key}}}}}"
                secrets[placeholder_key] = value
            else:
                public_vars[key] = value
        
        return public_vars, secrets
    
    def save_secrets(self, environment_name: str, secrets: Dict[str, str]) -> Tuple[bool, str]:
        """
        Save secrets to local secrets file.
        
        Args:
            environment_name: Name of the environment
            secrets: Dictionary of secret values
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Ensure directory exists
            self.secrets_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing secrets
            all_secrets = {}
            if self.secrets_file.exists():
                with open(self.secrets_file, 'r', encoding='utf-8') as f:
                    all_secrets = json.load(f)
            
            # Update secrets for this environment
            if environment_name not in all_secrets:
                all_secrets[environment_name] = {}
            
            all_secrets[environment_name].update(secrets)
            
            # Save
            with open(self.secrets_file, 'w', encoding='utf-8') as f:
                json.dump(all_secrets, f, indent=2)
            
            # Update cache
            self._secrets_cache = all_secrets
            
            return True, f"Saved {len(secrets)} secrets for '{environment_name}'"
            
        except Exception as e:
            return False, f"Failed to save secrets: {str(e)}"
    
    def load_secrets(self, environment_name: Optional[str] = None) -> Dict[str, str]:
        """
        Load secrets from local file.
        
        Args:
            environment_name: Name of environment, or None for all secrets
            
        Returns:
            Dictionary of secrets
        """
        try:
            if not self.secrets_file.exists():
                return {}
            
            # Check cache
            if self._secrets_cache:
                if environment_name:
                    return self._secrets_cache.get(environment_name, {})
                else:
                    return self._secrets_cache
            
            # Load from file
            with open(self.secrets_file, 'r', encoding='utf-8') as f:
                all_secrets = json.load(f)
            
            self._secrets_cache = all_secrets
            
            if environment_name:
                return all_secrets.get(environment_name, {})
            else:
                return all_secrets
                
        except Exception as e:
            return {}
    
    def get_missing_secrets(self, environment_name: str, variables: Dict[str, str]) -> List[str]:
        """
        Get list of secret placeholders that don't have values set.
        
        Args:
            environment_name: Name of the environment
            variables: Dictionary of variables (may contain placeholders)
            
        Returns:
            List of missing secret placeholder names
        """
        missing = []
        secrets = self.load_secrets(environment_name)
        
        for key, value in variables.items():
            # Check if value is a placeholder
            if isinstance(value, str) and value.startswith("{{SECRET_") and value.endswith("}}"):
                placeholder = value[2:-2]  # Remove {{ and }}
                
                if placeholder not in secrets:
                    missing.append(placeholder)
        
        return missing
    
    def substitute_secrets(self, environment_name: str, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Replace secret placeholders with actual values.
        
        Args:
            environment_name: Name of the environment
            variables: Dictionary of variables with placeholders
            
        Returns:
            Dictionary with secrets substituted
        """
        secrets = self.load_secrets(environment_name)
        substituted = {}
        
        for key, value in variables.items():
            if isinstance(value, str) and value.startswith("{{SECRET_") and value.endswith("}}"):
                placeholder = value[2:-2]  # Remove {{ and }}
                substituted[key] = secrets.get(placeholder, value)  # Use actual value or keep placeholder
            else:
                substituted[key] = value
        
        return substituted
    
    def delete_secrets(self, environment_name: str) -> Tuple[bool, str]:
        """
        Delete secrets for an environment.
        
        Args:
            environment_name: Name of the environment
            
        Returns:
            Tuple of (success, message)
        """
        try:
            all_secrets = self.load_secrets()
            
            if environment_name in all_secrets:
                del all_secrets[environment_name]
                
                # Save
                with open(self.secrets_file, 'w', encoding='utf-8') as f:
                    json.dump(all_secrets, f, indent=2)
                
                # Update cache
                self._secrets_cache = all_secrets
                
                return True, f"Deleted secrets for '{environment_name}'"
            else:
                return False, f"No secrets found for '{environment_name}'"
                
        except Exception as e:
            return False, f"Failed to delete secrets: {str(e)}"
    
    def export_secrets_template(self, environment_name: str, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Create a template showing which secrets need to be set.
        
        Args:
            environment_name: Name of the environment
            variables: Dictionary of variables
            
        Returns:
            Dictionary template with placeholder descriptions
        """
        template = {}
        
        for key, value in variables.items():
            if isinstance(value, str) and value.startswith("{{SECRET_") and value.endswith("}}"):
                placeholder = value[2:-2]
                template[placeholder] = "<enter your secret value here>"
        
        return template
    
    def has_secrets_file(self) -> bool:
        """Check if local secrets file exists."""
        return self.secrets_file.exists()
    
    def get_all_environments_with_secrets(self) -> List[str]:
        """Get list of environment names that have secrets stored."""
        all_secrets = self.load_secrets()
        return list(all_secrets.keys())

