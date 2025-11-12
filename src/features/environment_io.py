"""
Environment Import/Export Module

Handles importing and exporting environments in various formats:
- Internal format (PostMini native)
- Postman Environment Format
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from src.core.database import DatabaseManager
from src.features.postman_environment_converter import PostmanEnvironmentConverter


class EnvironmentExporter:
    """
    Handles exporting environments to files.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize the exporter.
        
        Args:
            db: Database manager instance
        """
        self.db = db
    
    def export_environment(self, environment_id: int, format: str = 'internal', 
                          include_secrets: bool = True) -> Dict:
        """
        Export an environment to a dictionary.
        
        Args:
            environment_id: ID of the environment to export
            format: Export format - 'internal' or 'postman'
            include_secrets: If False, replace secret values with placeholders
            
        Returns:
            Dictionary containing environment data
        """
        environment = self.db.get_environment(environment_id)
        if not environment:
            raise ValueError(f"Environment with ID {environment_id} not found")
        
        # Build internal format
        export_data = {
            "export_version": "1.0",
            "export_date": datetime.now().isoformat(),
            "environment": {
                "id": environment['id'],
                "name": environment['name'],
                "variables": environment.get('variables', {})
            }
        }
        
        # Convert to Postman format if requested
        if format == 'postman':
            export_data = PostmanEnvironmentConverter.to_postman_format(
                export_data, 
                include_secrets=include_secrets
            )
        
        return export_data
    
    def export_environment_to_file(self, environment_id: int, file_path: str, 
                                   format: str = 'internal',
                                   include_secrets: bool = True) -> bool:
        """
        Export an environment to a JSON file.
        
        Args:
            environment_id: ID of the environment to export
            file_path: Path where to save the JSON file
            format: Export format - 'internal' or 'postman'
            include_secrets: If False, replace secret values with placeholders
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = self.export_environment(environment_id, format, include_secrets)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def export_all_environments(self, format: str = 'internal', 
                               include_secrets: bool = True) -> List[Dict]:
        """
        Export all environments.
        
        Args:
            format: Export format - 'internal' or 'postman'
            include_secrets: If False, replace secret values with placeholders
            
        Returns:
            List of exported environment dictionaries
        """
        environments = self.db.get_all_environments()
        exported = []
        
        for environment in environments:
            try:
                export_data = self.export_environment(
                    environment['id'], 
                    format=format,
                    include_secrets=include_secrets
                )
                exported.append(export_data)
            except Exception as e:
                print(f"Failed to export environment {environment['name']}: {e}")
        
        return exported
    
    def export_all_environments_to_directory(self, directory_path: str, 
                                            format: str = 'internal',
                                            include_secrets: bool = True) -> Tuple[int, int]:
        """
        Export all environments to individual files in a directory.
        
        Args:
            directory_path: Directory where to save the files
            format: Export format - 'internal' or 'postman'
            include_secrets: If False, replace secret values with placeholders
            
        Returns:
            Tuple of (success_count, total_count)
        """
        directory = Path(directory_path)
        directory.mkdir(parents=True, exist_ok=True)
        
        environments = self.db.get_all_environments()
        success_count = 0
        
        for environment in environments:
            try:
                # Sanitize filename
                safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                                  for c in environment['name'])
                safe_name = safe_name.strip().replace(' ', '_')
                
                file_path = directory / f"{safe_name}.json"
                
                if self.export_environment_to_file(
                    environment['id'], 
                    str(file_path), 
                    format=format,
                    include_secrets=include_secrets
                ):
                    success_count += 1
            except Exception as e:
                print(f"Failed to export environment {environment['name']}: {e}")
        
        return success_count, len(environments)


class EnvironmentImporter:
    """
    Handles importing environments from files.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize the importer.
        
        Args:
            db: Database manager instance
        """
        self.db = db
    
    def import_environment(self, environment_data: Dict, 
                          update_existing: bool = False) -> Tuple[bool, str, Optional[int]]:
        """
        Import an environment from a dictionary.
        
        Args:
            environment_data: Environment data (auto-detects format)
            update_existing: If True, update environment with same name
            
        Returns:
            Tuple of (success, message, environment_id)
        """
        try:
            # Auto-detect format and convert if needed
            if PostmanEnvironmentConverter.is_postman_format(environment_data):
                # Validate Postman format
                is_valid, error_msg = PostmanEnvironmentConverter.validate_postman_environment(
                    environment_data
                )
                if not is_valid:
                    return False, f"Invalid Postman environment: {error_msg}", None
                
                # Convert to internal format
                environment_data = PostmanEnvironmentConverter.from_postman_format(
                    environment_data
                )
            
            # Extract environment info
            environment = environment_data.get('environment', {})
            env_name = environment.get('name', 'Imported Environment')
            variables = environment.get('variables', {})
            
            # Check if environment with same name exists
            existing_envs = self.db.get_all_environments()
            existing_env = next((e for e in existing_envs if e['name'] == env_name), None)
            
            if existing_env:
                if update_existing:
                    # Update existing environment
                    env_id = existing_env['id']
                    self.db.update_environment(env_id, env_name, variables)
                    return True, f"Updated environment '{env_name}'", env_id
                else:
                    # Generate unique name
                    counter = 1
                    new_name = f"{env_name} ({counter})"
                    while any(e['name'] == new_name for e in existing_envs):
                        counter += 1
                        new_name = f"{env_name} ({counter})"
                    
                    env_id = self.db.create_environment(new_name, variables)
                    return True, f"Imported as '{new_name}' (name conflict resolved)", env_id
            else:
                # Create new environment
                env_id = self.db.create_environment(env_name, variables)
                return True, f"Imported environment '{env_name}'", env_id
        
        except Exception as e:
            return False, f"Import failed: {str(e)}", None
    
    def import_environment_from_file(self, file_path: str, 
                                    update_existing: bool = False) -> Tuple[bool, str, Optional[int]]:
        """
        Import an environment from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            update_existing: If True, update environment with same name
            
        Returns:
            Tuple of (success, message, environment_id)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self.import_environment(data, update_existing)
        
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON file: {str(e)}", None
        except Exception as e:
            return False, f"Import failed: {str(e)}", None
    
    def import_environments_from_directory(self, directory_path: str,
                                          update_existing: bool = False) -> Tuple[int, int, List[str]]:
        """
        Import all JSON environment files from a directory.
        
        Args:
            directory_path: Directory containing environment JSON files
            update_existing: If True, update environments with same names
            
        Returns:
            Tuple of (success_count, total_count, list_of_messages)
        """
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            return 0, 0, [f"Directory not found: {directory_path}"]
        
        json_files = list(directory.glob("*.json"))
        success_count = 0
        messages = []
        
        for file_path in json_files:
            success, message, env_id = self.import_environment_from_file(
                str(file_path), 
                update_existing
            )
            
            if success:
                success_count += 1
                messages.append(f"✓ {file_path.name}: {message}")
            else:
                messages.append(f"✗ {file_path.name}: {message}")
        
        return success_count, len(json_files), messages
    
    def detect_format(self, data: Dict) -> str:
        """
        Detect the format of environment data.
        
        Args:
            data: Environment data dictionary
            
        Returns:
            'postman' or 'internal'
        """
        if PostmanEnvironmentConverter.is_postman_format(data):
            return 'postman'
        return 'internal'
