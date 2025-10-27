"""
Git Sync Manager Module

This module handles Git-based collaboration by syncing collections, environments,
and test suites to/from the file system. Collections are stored in .postmini/ folder
which can be version controlled with Git.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

from src.core.database import DatabaseManager


class GitSyncConfig:
    """Configuration for Git sync."""
    
    POSTMINI_DIR = ".postmini"
    SECRETS_DIR = ".postmini-secrets"
    COLLECTIONS_DIR = "collections"
    ENVIRONMENTS_DIR = "environments"
    TEST_SUITES_DIR = "test-suites"
    WORKSPACE_FILE = "workspace.json"
    GITIGNORE_ENTRY = ".postmini-secrets/"
    
    def __init__(self, project_path: str):
        """
        Initialize Git sync configuration.
        
        Args:
            project_path: Root path of the project
        """
        self.project_path = Path(project_path).resolve()
        self.postmini_path = self.project_path / self.POSTMINI_DIR
        self.secrets_path = self.project_path / self.SECRETS_DIR
        self.collections_path = self.postmini_path / self.COLLECTIONS_DIR
        self.environments_path = self.postmini_path / self.ENVIRONMENTS_DIR
        self.test_suites_path = self.postmini_path / self.TEST_SUITES_DIR
        self.workspace_file = self.postmini_path / self.WORKSPACE_FILE
        self.gitignore_file = self.project_path / ".gitignore"


class SyncStatus:
    """Represents the sync status of the workspace."""
    
    STATUS_SYNCED = "synced"
    STATUS_NEEDS_PULL = "needs_pull"
    STATUS_NEEDS_PUSH = "needs_push"
    STATUS_CONFLICT = "conflict"
    STATUS_ERROR = "error"
    STATUS_DISABLED = "disabled"
    
    def __init__(self, status: str, message: str = "", changes: Optional[Dict] = None):
        """Initialize sync status."""
        self.status = status
        self.message = message
        self.changes = changes or {}
        self.timestamp = datetime.now().isoformat()


class GitSyncManager:
    """
    Manages Git-based collaboration by syncing database contents to file system.
    """
    
    EXPORT_VERSION = "1.0"
    
    def __init__(self, db: DatabaseManager, config: GitSyncConfig):
        """
        Initialize Git sync manager.
        
        Args:
            db: DatabaseManager instance
            config: GitSyncConfig instance
        """
        self.db = db
        self.config = config
        self._last_sync_hashes = {}
    
    # ==================== Workspace Setup ====================
    
    def initialize_workspace(self, create_gitignore: bool = True) -> Tuple[bool, str]:
        """
        Initialize Git sync workspace in the project directory.
        
        Args:
            create_gitignore: Whether to add .postmini-secrets to .gitignore
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create directory structure
            self.config.collections_path.mkdir(parents=True, exist_ok=True)
            self.config.environments_path.mkdir(parents=True, exist_ok=True)
            self.config.test_suites_path.mkdir(parents=True, exist_ok=True)
            self.config.secrets_path.mkdir(parents=True, exist_ok=True)
            
            # Create workspace metadata file
            workspace_data = {
                "version": self.EXPORT_VERSION,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "app": "PostMini",
                "description": "PostMini workspace for API collections and tests"
            }
            
            with open(self.config.workspace_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, indent=2)
            
            # Add to .gitignore
            if create_gitignore:
                self._update_gitignore()
            
            return True, f"Workspace initialized at {self.config.postmini_path}"
            
        except Exception as e:
            return False, f"Failed to initialize workspace: {str(e)}"
    
    def is_workspace_initialized(self) -> bool:
        """
        Check if workspace is already initialized.
        
        Returns:
            True if .postmini/ directory exists with workspace.json
        """
        return (self.config.postmini_path.exists() and 
                self.config.workspace_file.exists())
    
    def detect_workspace(self) -> Tuple[bool, Optional[Dict]]:
        """
        Detect if current directory has a .postmini/ workspace.
        
        Returns:
            Tuple of (found, workspace_info)
        """
        if not self.is_workspace_initialized():
            return False, None
        
        try:
            with open(self.config.workspace_file, 'r', encoding='utf-8') as f:
                workspace_data = json.load(f)
            
            # Count collections, environments
            num_collections = len(list(self.config.collections_path.glob("*.json"))) if self.config.collections_path.exists() else 0
            num_environments = len(list(self.config.environments_path.glob("*.json"))) if self.config.environments_path.exists() else 0
            
            workspace_info = {
                "path": str(self.config.postmini_path),
                "created_at": workspace_data.get("created_at"),
                "last_updated": workspace_data.get("last_updated"),
                "num_collections": num_collections,
                "num_environments": num_environments
            }
            
            return True, workspace_info
            
        except Exception as e:
            return False, None
    
    def _update_gitignore(self):
        """Add .postmini-secrets to .gitignore if not already present."""
        gitignore_content = ""
        
        if self.config.gitignore_file.exists():
            with open(self.config.gitignore_file, 'r', encoding='utf-8') as f:
                gitignore_content = f.read()
        
        # Check if already present
        if GitSyncConfig.GITIGNORE_ENTRY not in gitignore_content:
            # Add entry
            if gitignore_content and not gitignore_content.endswith('\n'):
                gitignore_content += '\n'
            
            gitignore_content += f"\n# PostMini local secrets\n{GitSyncConfig.GITIGNORE_ENTRY}\n"
            
            with open(self.config.gitignore_file, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
    
    # ==================== Export to File System ====================
    
    def export_collection_to_file(self, collection_id: int) -> Tuple[bool, str]:
        """
        Export a single collection to the file system.
        
        Args:
            collection_id: ID of the collection to export
            
        Returns:
            Tuple of (success, message/file_path)
        """
        try:
            collection = self.db.get_collection(collection_id)
            if not collection:
                return False, f"Collection {collection_id} not found"
            
            # Get all requests
            requests = self.db.get_requests_by_collection(collection_id)
            
            # Get test assertions for each request
            requests_with_tests = []
            for request in requests:
                test_assertions = self.db.get_test_assertions(request['id'])
                request_data = {
                    "name": request['name'],
                    "method": request['method'],
                    "url": request['url'],
                    "params": request.get('params'),
                    "headers": request.get('headers'),
                    "body": request.get('body'),
                    "auth_type": request.get('auth_type', 'None'),
                    "auth_token": request.get('auth_token'),
                    "description": request.get('description'),
                    "tests": [
                        {
                            "type": t['assertion_type'],
                            "operator": t['operator'],
                            "field": t.get('field'),
                            "expected_value": t.get('expected_value'),
                            "enabled": t.get('enabled', True)
                        }
                        for t in test_assertions
                    ]
                }
                requests_with_tests.append(request_data)
            
            # Build export data
            export_data = {
                "export_version": self.EXPORT_VERSION,
                "export_date": datetime.now().isoformat(),
                "collection": {
                    "id": collection_id,
                    "name": collection['name'],
                    "requests": requests_with_tests
                }
            }
            
            # Generate filename
            filename = self._sanitize_filename(collection['name']) + ".json"
            file_path = self.config.collections_path / filename
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Update hash
            self._update_hash('collection', collection_id, export_data)
            
            return True, str(file_path)
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"
    
    def export_all_collections(self) -> Tuple[bool, str, List[str]]:
        """
        Export all collections to file system.
        
        Returns:
            Tuple of (success, message, list_of_file_paths)
        """
        collections = self.db.get_all_collections()
        exported_files = []
        failed = []
        
        for collection in collections:
            success, result = self.export_collection_to_file(collection['id'])
            if success:
                exported_files.append(result)
            else:
                failed.append(f"{collection['name']}: {result}")
        
        if failed:
            message = f"Exported {len(exported_files)}/{len(collections)} collections. Failures: {', '.join(failed)}"
            return False, message, exported_files
        else:
            return True, f"Exported {len(exported_files)} collections", exported_files
    
    def export_environment_to_file(self, environment_id: int, include_secrets: bool = False) -> Tuple[bool, str]:
        """
        Export an environment to file system.
        
        Args:
            environment_id: ID of the environment
            include_secrets: If True, include actual secret values (for local secrets file)
            
        Returns:
            Tuple of (success, message/file_path)
        """
        try:
            environment = self.db.get_environment(environment_id)
            if not environment:
                return False, f"Environment {environment_id} not found"
            
            # Separate secrets from regular variables
            variables = environment.get('variables', {})
            public_vars = {}
            secret_placeholders = {}
            
            for key, value in variables.items():
                # Heuristic: keys containing 'secret', 'key', 'token', 'password' are secrets
                is_secret = any(keyword in key.lower() for keyword in ['secret', 'key', 'token', 'password', 'auth'])
                
                if is_secret and not include_secrets:
                    # Replace with placeholder
                    public_vars[key] = f"{{{{SECRET_{key}}}}}"
                    secret_placeholders[f"SECRET_{key}"] = value
                else:
                    public_vars[key] = value
            
            export_data = {
                "export_version": self.EXPORT_VERSION,
                "export_date": datetime.now().isoformat(),
                "environment": {
                    "id": environment_id,
                    "name": environment['name'],
                    "variables": public_vars if not include_secrets else variables
                }
            }
            
            filename = self._sanitize_filename(environment['name']) + ".json"
            file_path = self.config.environments_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Update hash
            self._update_hash('environment', environment_id, export_data)
            
            return True, str(file_path)
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"
    
    def export_all_environments(self) -> Tuple[bool, str, List[str]]:
        """
        Export all environments to file system.
        
        Returns:
            Tuple of (success, message, list_of_file_paths)
        """
        environments = self.db.get_all_environments()
        exported_files = []
        
        for env in environments:
            success, result = self.export_environment_to_file(env['id'])
            if success:
                exported_files.append(result)
        
        return True, f"Exported {len(exported_files)} environments", exported_files
    
    # ==================== Import from File System ====================
    
    def import_collection_from_file(self, file_path: str, update_existing: bool = True) -> Tuple[bool, str, Optional[int]]:
        """
        Import a collection from file system to database.
        
        Args:
            file_path: Path to the JSON file
            update_existing: If True, update existing collection with same name
            
        Returns:
            Tuple of (success, message, collection_id)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collection_data = data['collection']
            collection_name = collection_data['name']
            
            # Check if collection exists
            existing_collections = self.db.get_all_collections()
            existing_collection = next((c for c in existing_collections if c['name'] == collection_name), None)
            
            if existing_collection and update_existing:
                # Update existing collection
                collection_id = existing_collection['id']
                
                # Delete existing requests
                existing_requests = self.db.get_requests_by_collection(collection_id)
                for req in existing_requests:
                    self.db.delete_request(req['id'])
                
            elif existing_collection and not update_existing:
                # Skip
                return False, f"Collection '{collection_name}' already exists (skipped)", None
                
            else:
                # Create new collection
                collection_id = self.db.create_collection(collection_name)
            
            # Import requests
            for request_data in collection_data.get('requests', []):
                request_id = self.db.create_request(
                    name=request_data['name'],
                    url=request_data['url'],
                    method=request_data['method'],
                    collection_id=collection_id,
                    params=request_data.get('params'),
                    headers=request_data.get('headers'),
                    body=request_data.get('body'),
                    auth_type=request_data.get('auth_type', 'None'),
                    auth_token=request_data.get('auth_token'),
                    description=request_data.get('description')
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
            
            # Update hash
            self._update_hash('collection', collection_id, data)
            
            message = f"Imported collection '{collection_name}' with {len(collection_data.get('requests', []))} requests"
            return True, message, collection_id
            
        except Exception as e:
            return False, f"Import failed: {str(e)}", None
    
    def import_all_collections(self, update_existing: bool = True) -> Tuple[bool, str, List[int]]:
        """
        Import all collections from file system.
        
        Args:
            update_existing: If True, update existing collections
            
        Returns:
            Tuple of (success, message, list_of_collection_ids)
        """
        if not self.config.collections_path.exists():
            return False, "Collections directory not found", []
        
        collection_files = list(self.config.collections_path.glob("*.json"))
        imported_ids = []
        messages = []
        
        for file_path in collection_files:
            success, message, coll_id = self.import_collection_from_file(str(file_path), update_existing)
            if success and coll_id:
                imported_ids.append(coll_id)
            messages.append(message)
        
        summary = f"Imported {len(imported_ids)} collections"
        return True, summary, imported_ids
    
    def import_environment_from_file(self, file_path: str, update_existing: bool = True) -> Tuple[bool, str, Optional[int]]:
        """
        Import an environment from file system.
        
        Args:
            file_path: Path to the JSON file
            update_existing: If True, update existing environment with same name
            
        Returns:
            Tuple of (success, message, environment_id)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            env_data = data['environment']
            env_name = env_data['name']
            variables = env_data.get('variables', {})
            
            # Check if environment exists
            existing_envs = self.db.get_all_environments()
            existing_env = next((e for e in existing_envs if e['name'] == env_name), None)
            
            if existing_env and update_existing:
                # Update
                env_id = existing_env['id']
                self.db.update_environment(env_id, env_name, variables)
            elif existing_env and not update_existing:
                return False, f"Environment '{env_name}' already exists (skipped)", None
            else:
                # Create
                env_id = self.db.create_environment(env_name, variables)
            
            # Update hash
            self._update_hash('environment', env_id, data)
            
            return True, f"Imported environment '{env_name}'", env_id
            
        except Exception as e:
            return False, f"Import failed: {str(e)}", None
    
    def import_all_environments(self, update_existing: bool = True) -> Tuple[bool, str, List[int]]:
        """
        Import all environments from file system.
        
        Returns:
            Tuple of (success, message, list_of_environment_ids)
        """
        if not self.config.environments_path.exists():
            return False, "Environments directory not found", []
        
        env_files = list(self.config.environments_path.glob("*.json"))
        imported_ids = []
        
        for file_path in env_files:
            success, message, env_id = self.import_environment_from_file(str(file_path), update_existing)
            if success and env_id:
                imported_ids.append(env_id)
        
        return True, f"Imported {len(imported_ids)} environments", imported_ids
    
    # ==================== Sync Operations ====================
    
    def sync_to_filesystem(self) -> Tuple[bool, str]:
        """
        Sync all database content to file system (push).
        
        Returns:
            Tuple of (success, message)
        """
        if not self.is_workspace_initialized():
            return False, "Workspace not initialized"
        
        try:
            # Export all collections
            coll_success, coll_msg, coll_files = self.export_all_collections()
            
            # Export all environments
            env_success, env_msg, env_files = self.export_all_environments()
            
            # Update workspace metadata
            self._update_workspace_metadata()
            
            message = f"Synced to filesystem: {len(coll_files)} collections, {len(env_files)} environments"
            return True, message
            
        except Exception as e:
            return False, f"Sync failed: {str(e)}"
    
    def sync_from_filesystem(self, update_existing: bool = True) -> Tuple[bool, str]:
        """
        Sync file system content to database (pull).
        
        Args:
            update_existing: If True, update existing items
            
        Returns:
            Tuple of (success, message)
        """
        if not self.is_workspace_initialized():
            return False, "Workspace not initialized"
        
        try:
            # Import all collections
            coll_success, coll_msg, coll_ids = self.import_all_collections(update_existing)
            
            # Import all environments
            env_success, env_msg, env_ids = self.import_all_environments(update_existing)
            
            message = f"Synced from filesystem: {len(coll_ids)} collections, {len(env_ids)} environments"
            return True, message
            
        except Exception as e:
            return False, f"Sync failed: {str(e)}"
    
    def detect_changes(self) -> Dict[str, List[Dict]]:
        """
        Detect changes between database and file system.
        
        Returns:
            Dictionary with changes categorized as:
            - new_files: Files on disk not in database
            - modified_files: Files changed on disk
            - deleted_files: Files in database but not on disk
            - new_db_items: Items in database not on disk
        """
        changes = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "new_db_items": []
        }
        
        if not self.is_workspace_initialized():
            return changes
        
        # Check collections
        db_collections = {c['name']: c for c in self.db.get_all_collections()}
        
        if self.config.collections_path.exists():
            file_collections = {}
            for file_path in self.config.collections_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        coll_name = data['collection']['name']
                        file_collections[coll_name] = {
                            'path': str(file_path),
                            'data': data
                        }
                except Exception:
                    continue
            
            # Detect new files
            for name, info in file_collections.items():
                if name not in db_collections:
                    changes['new_files'].append({
                        'type': 'collection',
                        'name': name,
                        'path': info['path']
                    })
                else:
                    # Check if modified
                    coll_id = db_collections[name]['id']
                    if self._is_modified('collection', coll_id, info['data']):
                        changes['modified_files'].append({
                            'type': 'collection',
                            'name': name,
                            'path': info['path']
                        })
            
            # Detect new db items
            for name, coll in db_collections.items():
                if name not in file_collections:
                    changes['new_db_items'].append({
                        'type': 'collection',
                        'name': name,
                        'id': coll['id']
                    })
        
        return changes
    
    def get_sync_status(self) -> SyncStatus:
        """
        Get current sync status.
        
        Returns:
            SyncStatus object
        """
        if not self.is_workspace_initialized():
            return SyncStatus(SyncStatus.STATUS_DISABLED, "Git sync not enabled")
        
        changes = self.detect_changes()
        
        has_new_files = len(changes['new_files']) > 0 or len(changes['modified_files']) > 0
        has_new_db = len(changes['new_db_items']) > 0
        
        if has_new_files and has_new_db:
            return SyncStatus(
                SyncStatus.STATUS_CONFLICT,
                "Both filesystem and database have changes",
                changes
            )
        elif has_new_files:
            return SyncStatus(
                SyncStatus.STATUS_NEEDS_PULL,
                f"{len(changes['new_files']) + len(changes['modified_files'])} file(s) updated",
                changes
            )
        elif has_new_db:
            return SyncStatus(
                SyncStatus.STATUS_NEEDS_PUSH,
                f"{len(changes['new_db_items'])} item(s) not yet synced",
                changes
            )
        else:
            return SyncStatus(SyncStatus.STATUS_SYNCED, "All changes synced")
    
    # ==================== Helper Methods ====================
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert collection/environment name to safe filename."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        filename = name
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
    
    def _update_workspace_metadata(self):
        """Update workspace.json with current timestamp."""
        if self.config.workspace_file.exists():
            with open(self.config.workspace_file, 'r', encoding='utf-8') as f:
                workspace_data = json.load(f)
            
            workspace_data['last_updated'] = datetime.now().isoformat()
            
            with open(self.config.workspace_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, indent=2)
    
    def _compute_hash(self, data: Dict) -> str:
        """Compute hash of data for change detection."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _update_hash(self, item_type: str, item_id: int, data: Dict):
        """Update stored hash for an item."""
        key = f"{item_type}_{item_id}"
        self._last_sync_hashes[key] = self._compute_hash(data)
    
    def _is_modified(self, item_type: str, item_id: int, current_data: Dict) -> bool:
        """Check if item has been modified since last sync."""
        key = f"{item_type}_{item_id}"
        if key not in self._last_sync_hashes:
            return True
        
        current_hash = self._compute_hash(current_data)
        return current_hash != self._last_sync_hashes[key]
    
    def cleanup_deleted_files(self):
        """Remove files from filesystem for deleted database items."""
        # Get all database collections
        db_collections = {c['name']: c['id'] for c in self.db.get_all_collections()}
        
        # Remove collection files not in database
        if self.config.collections_path.exists():
            for file_path in self.config.collections_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        coll_name = data['collection']['name']
                        
                        if coll_name not in db_collections:
                            file_path.unlink()
                except Exception:
                    pass

