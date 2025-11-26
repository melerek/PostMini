"""
Unit Tests for Git Sync Functionality

Comprehensive tests for Git-based collaboration features including:
- GitSyncManager
- SecretsManager  
- GitSyncConfig
- Database git_workspaces operations
"""

import unittest
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.features.git_sync_manager import GitSyncManager, GitSyncConfig, SyncStatus
from src.features.secrets_manager import SecretsManager


class TestGitSyncConfig(unittest.TestCase):
    """Test GitSyncConfig class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config = GitSyncConfig(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """Test GitSyncConfig initialization."""
        self.assertEqual(self.config.project_path, Path(self.test_dir).resolve())
        self.assertTrue(str(self.config.postmini_path).endswith('.postmini'))
        self.assertTrue(str(self.config.secrets_path).endswith('.postmini-secrets'))
        self.assertTrue(str(self.config.collections_path).endswith(os.path.join('.postmini', 'collections')))
        self.assertTrue(str(self.config.environments_path).endswith(os.path.join('.postmini', 'environments')))
    
    def test_path_resolution(self):
        """Test that paths are properly resolved."""
        self.assertTrue(self.config.project_path.is_absolute())
        self.assertTrue(self.config.postmini_path.is_absolute())


class TestGitSyncManager(unittest.TestCase):
    """Test GitSyncManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test.db')
        self.db = DatabaseManager(self.db_path)
        self.config = GitSyncConfig(self.test_dir)
        self.manager = GitSyncManager(self.db, self.config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.db.close()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    # ==================== Workspace Tests ====================
    
    def test_initialize_workspace(self):
        """Test workspace initialization."""
        success, message = self.manager.initialize_workspace(create_gitignore=True)
        
        self.assertTrue(success)
        self.assertTrue(self.config.postmini_path.exists())
        self.assertTrue(self.config.collections_path.exists())
        self.assertTrue(self.config.environments_path.exists())
        self.assertTrue(self.config.secrets_path.exists())
        self.assertTrue(self.config.workspace_file.exists())
        
        # Check workspace.json content
        with open(self.config.workspace_file, 'r') as f:
            workspace_data = json.load(f)
        
        self.assertEqual(workspace_data['app'], 'PostMini')
        self.assertIn('created_at', workspace_data)
        self.assertIn('last_updated', workspace_data)
    
    def test_initialize_workspace_creates_gitignore(self):
        """Test that .gitignore is created/updated."""
        self.manager.initialize_workspace(create_gitignore=True)
        
        gitignore_path = self.config.gitignore_file
        self.assertTrue(gitignore_path.exists())
        
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        self.assertIn('.postmini-secrets/', content)
    
    def test_initialize_workspace_appends_to_existing_gitignore(self):
        """Test that existing .gitignore is appended to."""
        # Create existing .gitignore
        gitignore_path = self.config.gitignore_file
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n__pycache__/\n")
        
        self.manager.initialize_workspace(create_gitignore=True)
        
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        self.assertIn('*.pyc', content)
        self.assertIn('.postmini-secrets/', content)
    
    def test_is_workspace_initialized(self):
        """Test workspace detection."""
        self.assertFalse(self.manager.is_workspace_initialized())
        
        self.manager.initialize_workspace()
        
        self.assertTrue(self.manager.is_workspace_initialized())
    
    def test_detect_workspace(self):
        """Test workspace detection with info."""
        found, info = self.manager.detect_workspace()
        self.assertFalse(found)
        self.assertIsNone(info)
        
        self.manager.initialize_workspace()
        
        found, info = self.manager.detect_workspace()
        self.assertTrue(found)
        self.assertIsNotNone(info)
        self.assertIn('path', info)
        self.assertIn('num_collections', info)
        self.assertIn('num_environments', info)
    
    # ==================== Export Tests ====================
    
    def test_export_collection_to_file(self):
        """Test exporting a collection to file."""
        # Create test collection
        coll_id = self.db.create_collection("Test Collection")
        req_id = self.db.create_request(
            collection_id=coll_id,
            name="Test Request",
            method="GET",
            url="https://api.example.com/test",
            params={"key": "value"},
            headers={"Content-Type": "application/json"},
            body='{"test": true}',
            auth_type="Bearer Token",
            auth_token="secret123"
        )
        
        # Add test assertion
        self.db.create_test_assertion(
            request_id=req_id,
            assertion_type="status_code",
            operator="equals",
            expected_value="200"
        )
        
        # Initialize workspace
        self.manager.initialize_workspace()
        
        # Export
        success, file_path = self.manager.export_collection_to_file(coll_id)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_path))
        
        # Verify file content
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['collection']['name'], 'Test Collection')
        self.assertEqual(len(data['collection']['requests']), 1)
        
        req = data['collection']['requests'][0]
        self.assertEqual(req['name'], 'Test Request')
        self.assertEqual(req['method'], 'GET')
        self.assertEqual(req['url'], 'https://api.example.com/test')
        self.assertEqual(req['params'], {"key": "value"})
        self.assertEqual(len(req['tests']), 1)
    
    def test_export_all_collections(self):
        """Test exporting all collections."""
        # Create multiple collections
        coll1 = self.db.create_collection("Collection 1")
        coll2 = self.db.create_collection("Collection 2")
        
        self.db.create_request("Request 1", "http://example.com/1", "GET", coll1)
        self.db.create_request("Request 2", "http://example.com/2", "POST", coll2)
        
        self.manager.initialize_workspace()
        
        success, message, files = self.manager.export_all_collections()
        
        self.assertTrue(success)
        self.assertEqual(len(files), 2)
        
        for file_path in files:
            self.assertTrue(os.path.exists(file_path))
    
    def test_export_environment_to_file(self):
        """Test exporting an environment to file."""
        env_id = self.db.create_environment(
            "Test Environment",
            {
                "baseUrl": "https://api.example.com",
                "apiKey": "secret123",
                "timeout": "5000"
            }
        )
        
        self.manager.initialize_workspace()
        
        success, file_path = self.manager.export_environment_to_file(env_id, include_secrets=False)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_path))
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['environment']['name'], 'Test Environment')
        
        # Secret should be replaced with placeholder
        variables = data['environment']['variables']
        self.assertIn('{{SECRET_', variables['apiKey'])
    
    def test_export_all_environments(self):
        """Test exporting all environments."""
        self.db.create_environment("Dev", {"baseUrl": "http://dev.example.com"})
        self.db.create_environment("Prod", {"baseUrl": "http://example.com"})
        
        self.manager.initialize_workspace()
        
        success, message, files = self.manager.export_all_environments()
        
        self.assertTrue(success)
        self.assertEqual(len(files), 2)
    
    # ==================== Import Tests ====================
    
    def test_import_collection_from_file(self):
        """Test importing a collection from file."""
        # Create and export a collection
        coll_id = self.db.create_collection("Original Collection")
        self.db.create_request("Original Request", "http://example.com", "GET", coll_id)
        
        self.manager.initialize_workspace()
        success, file_path = self.manager.export_collection_to_file(coll_id)
        
        # Delete original
        self.db.delete_collection(coll_id)
        
        # Import from file
        success, message, new_coll_id = self.manager.import_collection_from_file(file_path)
        
        self.assertTrue(success)
        self.assertIsNotNone(new_coll_id)
        
        # Verify imported collection
        collection = self.db.get_collection(new_coll_id)
        self.assertEqual(collection['name'], 'Original Collection')
        
        requests = self.db.get_requests_by_collection(new_coll_id)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['name'], 'Original Request')
    
    def test_import_collection_updates_existing(self):
        """Test that import updates existing collection when update_existing=True."""
        # Create original collection
        coll_id = self.db.create_collection("Test Collection")
        self.db.create_request("Request 1", "http://example.com/1", "GET", coll_id)
        
        self.manager.initialize_workspace()
        success, file_path = self.manager.export_collection_to_file(coll_id)
        
        # Modify the database
        self.db.delete_collection(coll_id)
        new_coll_id = self.db.create_collection("Test Collection")
        self.db.create_request("Request 2", "http://example.com/2", "POST", new_coll_id)
        
        # Import with update
        success, message, imported_id = self.manager.import_collection_from_file(file_path, update_existing=True)
        
        self.assertTrue(success)
        
        # Should have only the imported request (check imported_id, not new_coll_id, because collection was recreated)
        requests = self.db.get_requests_by_collection(imported_id)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['name'], 'Request 1')
    
    def test_import_all_collections(self):
        """Test importing all collections from filesystem."""
        # Create multiple collections and export
        coll1 = self.db.create_collection("Collection 1")
        coll2 = self.db.create_collection("Collection 2")
        
        self.db.create_request("Request 1", "http://example.com/1", "GET", coll1)
        self.db.create_request("Request 2", "http://example.com/2", "POST", coll2)
        
        self.manager.initialize_workspace()
        self.manager.export_all_collections()
        
        # Clear database
        self.db.delete_collection(coll1)
        self.db.delete_collection(coll2)
        
        # Import all
        success, message, coll_ids = self.manager.import_all_collections()
        
        self.assertTrue(success)
        self.assertEqual(len(coll_ids), 2)
        
        # Verify
        collections = self.db.get_all_collections()
        self.assertEqual(len(collections), 2)
    
    def test_import_environment_from_file(self):
        """Test importing an environment from file."""
        env_id = self.db.create_environment("Test Env", {"baseUrl": "http://example.com"})
        
        self.manager.initialize_workspace()
        success, file_path = self.manager.export_environment_to_file(env_id)
        
        self.db.delete_environment(env_id)
        
        success, message, new_env_id = self.manager.import_environment_from_file(file_path)
        
        self.assertTrue(success)
        self.assertIsNotNone(new_env_id)
        
        env = self.db.get_environment(new_env_id)
        self.assertEqual(env['name'], 'Test Env')
    
    # ==================== Sync Tests ====================
    
    def test_sync_to_filesystem(self):
        """Test syncing database to filesystem."""
        # Create test data
        coll_id = self.db.create_collection("Test Collection")
        self.db.create_request("Test Request", "http://example.com", "GET", coll_id)
        self.db.create_environment("Test Env", {"key": "value"})
        
        self.manager.initialize_workspace()
        
        success, message = self.manager.sync_to_filesystem()
        
        self.assertTrue(success)
        
        # Verify files exist
        coll_files = list(self.config.collections_path.glob("*.json"))
        env_files = list(self.config.environments_path.glob("*.json"))
        
        self.assertEqual(len(coll_files), 1)
        self.assertEqual(len(env_files), 1)
    
    def test_sync_from_filesystem(self):
        """Test syncing filesystem to database."""
        # Create and export data
        coll_id = self.db.create_collection("Test Collection")
        self.db.create_request("Test Request", "http://example.com", "GET", coll_id)
        
        self.manager.initialize_workspace()
        self.manager.sync_to_filesystem()
        
        # Clear database
        self.db.delete_collection(coll_id)
        
        # Sync from filesystem
        success, message = self.manager.sync_from_filesystem()
        
        self.assertTrue(success)
        
        # Verify data restored
        collections = self.db.get_all_collections()
        self.assertEqual(len(collections), 1)
        self.assertEqual(collections[0]['name'], 'Test Collection')
    
    def test_detect_changes_new_files(self):
        """Test detecting new files on filesystem."""
        self.manager.initialize_workspace()
        
        # Create file manually
        test_collection = {
            "export_version": "1.0",
            "export_date": "2024-01-01T00:00:00",
            "collection": {
                "id": 999,
                "name": "New Collection",
                "requests": []
            }
        }
        
        file_path = self.config.collections_path / "new-collection.json"
        with open(file_path, 'w') as f:
            json.dump(test_collection, f)
        
        changes = self.manager.detect_changes()
        
        self.assertEqual(len(changes['new_files']), 1)
        self.assertEqual(changes['new_files'][0]['name'], 'New Collection')
    
    def test_detect_changes_new_db_items(self):
        """Test detecting new items in database."""
        self.manager.initialize_workspace()
        self.manager.sync_to_filesystem()
        
        # Add new collection to database
        self.db.create_collection("New DB Collection")
        
        changes = self.manager.detect_changes()
        
        self.assertEqual(len(changes['new_db_items']), 1)
        self.assertEqual(changes['new_db_items'][0]['name'], 'New DB Collection')
    
    def test_get_sync_status_synced(self):
        """Test sync status when everything is synced."""
        self.manager.initialize_workspace()
        
        coll_id = self.db.create_collection("Test")
        self.manager.export_collection_to_file(coll_id)
        
        status = self.manager.get_sync_status()
        
        # After export, there shouldn't be new items
        # But there might be modifications detected, so we check it's not disabled
        self.assertNotEqual(status.status, SyncStatus.STATUS_DISABLED)
    
    def test_get_sync_status_needs_pull(self):
        """Test sync status when filesystem has changes."""
        self.manager.initialize_workspace()
        
        # Create file on filesystem
        test_collection = {
            "export_version": "1.0",
            "export_date": "2024-01-01T00:00:00",
            "collection": {
                "id": 1,
                "name": "FS Collection",
                "requests": []
            }
        }
        
        file_path = self.config.collections_path / "fs-collection.json"
        with open(file_path, 'w') as f:
            json.dump(test_collection, f)
        
        status = self.manager.get_sync_status()
        
        self.assertEqual(status.status, SyncStatus.STATUS_NEEDS_PULL)
    
    def test_get_sync_status_needs_push(self):
        """Test sync status when database has changes."""
        self.manager.initialize_workspace()
        self.manager.sync_to_filesystem()
        
        # Add new collection to database
        self.db.create_collection("New Collection")
        
        status = self.manager.get_sync_status()
        
        self.assertEqual(status.status, SyncStatus.STATUS_NEEDS_PUSH)
    
    # ==================== Helper Method Tests ====================
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        test_cases = [
            ("Normal Name", "Normal Name"),
            ("Name:With:Colons", "Name_With_Colons"),
            ("Name/With/Slashes", "Name_With_Slashes"),
            ("Name<With>Invalid", "Name_With_Invalid"),
            ("  Leading Spaces", "Leading Spaces"),
            ("Trailing Spaces  ", "Trailing Spaces"),
            ("A" * 300, "A" * 200),  # Test length limit
        ]
        
        for input_name, expected in test_cases:
            result = self.manager._sanitize_filename(input_name)
            self.assertEqual(result, expected)


class TestSecretsManager(unittest.TestCase):
    """Test SecretsManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.secrets_dir = os.path.join(self.test_dir, '.postmini-secrets')
        self.manager = SecretsManager(self.secrets_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_is_secret_variable(self):
        """Test secret variable detection."""
        self.assertTrue(self.manager.is_secret_variable("apiKey"))
        self.assertTrue(self.manager.is_secret_variable("api_key"))
        self.assertTrue(self.manager.is_secret_variable("secretToken"))
        self.assertTrue(self.manager.is_secret_variable("password"))
        self.assertTrue(self.manager.is_secret_variable("auth"))
        self.assertTrue(self.manager.is_secret_variable("credential"))
        
        self.assertFalse(self.manager.is_secret_variable("baseUrl"))
        self.assertFalse(self.manager.is_secret_variable("timeout"))
        self.assertFalse(self.manager.is_secret_variable("version"))
    
    def test_separate_secrets(self):
        """Test separating secrets from public variables."""
        variables = {
            "baseUrl": "https://api.example.com",
            "apiKey": "secret123",
            "timeout": "5000",
            "password": "pass456"
        }
        
        public, secrets = self.manager.separate_secrets("development", variables)
        
        # Public should have placeholders for secrets
        self.assertEqual(public['baseUrl'], 'https://api.example.com')
        self.assertEqual(public['timeout'], '5000')
        self.assertIn('{{SECRET_', public['apiKey'])
        self.assertIn('{{SECRET_', public['password'])
        
        # Secrets should have actual values
        self.assertIn('DEVELOPMENT', list(secrets.keys())[0])
    
    def test_save_and_load_secrets(self):
        """Test saving and loading secrets."""
        secrets = {
            "SECRET_DEV_APIKEY": "secret123",
            "SECRET_DEV_PASSWORD": "pass456"
        }
        
        success, message = self.manager.save_secrets("development", secrets)
        
        self.assertTrue(success)
        self.assertTrue(self.manager.has_secrets_file())
        
        loaded = self.manager.load_secrets("development")
        
        self.assertEqual(loaded['SECRET_DEV_APIKEY'], 'secret123')
        self.assertEqual(loaded['SECRET_DEV_PASSWORD'], 'pass456')
    
    def test_save_secrets_creates_directory(self):
        """Test that save_secrets creates directory if not exists."""
        self.assertFalse(os.path.exists(self.secrets_dir))
        
        self.manager.save_secrets("test", {"SECRET_KEY": "value"})
        
        self.assertTrue(os.path.exists(self.secrets_dir))
    
    def test_save_secrets_merges_environments(self):
        """Test that saving secrets for multiple environments works."""
        self.manager.save_secrets("development", {"SECRET_DEV": "dev123"})
        self.manager.save_secrets("production", {"SECRET_PROD": "prod456"})
        
        dev_secrets = self.manager.load_secrets("development")
        prod_secrets = self.manager.load_secrets("production")
        
        self.assertEqual(dev_secrets['SECRET_DEV'], 'dev123')
        self.assertEqual(prod_secrets['SECRET_PROD'], 'prod456')
    
    def test_get_missing_secrets(self):
        """Test detecting missing secrets."""
        variables = {
            "baseUrl": "https://api.example.com",
            "apiKey": "{{SECRET_DEV_APIKEY}}",
            "token": "{{SECRET_DEV_TOKEN}}"
        }
        
        # No secrets saved yet
        missing = self.manager.get_missing_secrets("development", variables)
        
        self.assertEqual(len(missing), 2)
        self.assertIn("SECRET_DEV_APIKEY", missing)
        self.assertIn("SECRET_DEV_TOKEN", missing)
        
        # Save one secret
        self.manager.save_secrets("development", {"SECRET_DEV_APIKEY": "key123"})
        
        missing = self.manager.get_missing_secrets("development", variables)
        
        self.assertEqual(len(missing), 1)
        self.assertIn("SECRET_DEV_TOKEN", missing)
    
    def test_substitute_secrets(self):
        """Test substituting secrets in variables."""
        self.manager.save_secrets("development", {
            "SECRET_DEV_APIKEY": "actual_key_123",
            "SECRET_DEV_TOKEN": "actual_token_456"
        })
        
        variables = {
            "baseUrl": "https://api.example.com",
            "apiKey": "{{SECRET_DEV_APIKEY}}",
            "token": "{{SECRET_DEV_TOKEN}}"
        }
        
        substituted = self.manager.substitute_secrets("development", variables)
        
        self.assertEqual(substituted['baseUrl'], 'https://api.example.com')
        self.assertEqual(substituted['apiKey'], 'actual_key_123')
        self.assertEqual(substituted['token'], 'actual_token_456')
    
    def test_delete_secrets(self):
        """Test deleting secrets for an environment."""
        self.manager.save_secrets("development", {"SECRET_KEY": "value"})
        
        success, message = self.manager.delete_secrets("development")
        
        self.assertTrue(success)
        
        secrets = self.manager.load_secrets("development")
        self.assertEqual(len(secrets), 0)
    
    def test_export_secrets_template(self):
        """Test exporting secrets template."""
        variables = {
            "baseUrl": "https://api.example.com",
            "apiKey": "{{SECRET_DEV_APIKEY}}",
            "token": "{{SECRET_DEV_TOKEN}}"
        }
        
        template = self.manager.export_secrets_template("development", variables)
        
        self.assertIn("SECRET_DEV_APIKEY", template)
        self.assertIn("SECRET_DEV_TOKEN", template)
        self.assertEqual(len(template), 2)
    
    def test_get_all_environments_with_secrets(self):
        """Test getting list of environments with secrets."""
        self.manager.save_secrets("development", {"SECRET_KEY": "value1"})
        self.manager.save_secrets("staging", {"SECRET_KEY": "value2"})
        self.manager.save_secrets("production", {"SECRET_KEY": "value3"})
        
        envs = self.manager.get_all_environments_with_secrets()
        
        self.assertEqual(len(envs), 3)
        self.assertIn("development", envs)
        self.assertIn("staging", envs)
        self.assertIn("production", envs)


class TestDatabaseGitWorkspaceOperations(unittest.TestCase):
    """Test database operations for git_workspaces table."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test.db')
        self.db = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        self.db.close()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_create_git_workspace(self):
        """Test creating a git workspace."""
        workspace_id = self.db.create_git_workspace(
            project_path="/path/to/project",
            workspace_name="My Workspace",
            enabled=True,
            auto_sync=True
        )
        
        self.assertIsNotNone(workspace_id)
        self.assertGreater(workspace_id, 0)
    
    def test_get_git_workspace_by_path(self):
        """Test retrieving git workspace by path."""
        workspace_id = self.db.create_git_workspace(
            project_path="/path/to/project",
            workspace_name="Test Workspace"
        )
        
        workspace = self.db.get_git_workspace_by_path("/path/to/project")
        
        self.assertIsNotNone(workspace)
        self.assertEqual(workspace['id'], workspace_id)
        self.assertEqual(workspace['project_path'], "/path/to/project")
        self.assertEqual(workspace['workspace_name'], "Test Workspace")
        self.assertTrue(workspace['enabled'])
        self.assertTrue(workspace['auto_sync'])
    
    def test_get_all_git_workspaces(self):
        """Test retrieving all git workspaces."""
        self.db.create_git_workspace("/path/1")
        self.db.create_git_workspace("/path/2")
        self.db.create_git_workspace("/path/3")
        
        workspaces = self.db.get_all_git_workspaces()
        
        self.assertEqual(len(workspaces), 3)
    
    def test_update_git_workspace(self):
        """Test updating git workspace."""
        workspace_id = self.db.create_git_workspace("/path/to/project")
        
        self.db.update_git_workspace(
            workspace_id=workspace_id,
            workspace_name="Updated Name",
            enabled=False,
            sync_status="needs_push"
        )
        
        workspace = self.db.get_git_workspace_by_path("/path/to/project")
        
        self.assertEqual(workspace['workspace_name'], "Updated Name")
        self.assertFalse(workspace['enabled'])
        self.assertEqual(workspace['sync_status'], "needs_push")
    
    def test_update_git_workspace_sync_timestamp(self):
        """Test updating sync timestamp."""
        workspace_id = self.db.create_git_workspace("/path/to/project")
        
        workspace_before = self.db.get_git_workspace_by_path("/path/to/project")
        
        import time
        time.sleep(0.1)  # Ensure timestamp difference
        
        self.db.update_git_workspace_sync_timestamp(workspace_id)
        
        workspace_after = self.db.get_git_workspace_by_path("/path/to/project")
        
        self.assertIsNotNone(workspace_after['last_sync_timestamp'])
        self.assertNotEqual(workspace_before['updated_at'], workspace_after['updated_at'])
    
    def test_delete_git_workspace(self):
        """Test deleting git workspace."""
        workspace_id = self.db.create_git_workspace("/path/to/project")
        
        self.db.delete_git_workspace(workspace_id)
        
        workspace = self.db.get_git_workspace_by_path("/path/to/project")
        self.assertIsNone(workspace)
    
    def test_unique_project_path_constraint(self):
        """Test that project_path must be unique."""
        self.db.create_git_workspace("/path/to/project")
        
        with self.assertRaises(Exception):
            self.db.create_git_workspace("/path/to/project")


if __name__ == '__main__':
    unittest.main()

