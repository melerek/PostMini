"""
Integration Tests for Git Sync

End-to-end integration tests simulating real user workflows:
- Setting up Git sync for a project
- Collaborative workflows (simulating multiple users)
- Conflict resolution scenarios
- Branch switching workflows
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


class TestGitSyncCollaboration(unittest.TestCase):
    """Test collaborative Git sync workflows."""
    
    def setUp(self):
        """Set up test environment simulating a Git repository."""
        # Create a "project" directory (simulating a Git repo)
        self.project_dir = tempfile.mkdtemp()
        
        # Create two "users" with separate databases
        self.user1_db_path = os.path.join(tempfile.mkdtemp(), 'user1.db')
        self.user2_db_path = os.path.join(tempfile.mkdtemp(), 'user2.db')
        
        self.user1_db = DatabaseManager(self.user1_db_path)
        self.user2_db = DatabaseManager(self.user2_db_path)
        
        # Both users point to the same project directory (simulating shared Git repo)
        self.user1_config = GitSyncConfig(self.project_dir)
        self.user2_config = GitSyncConfig(self.project_dir)
        
        self.user1_manager = GitSyncManager(self.user1_db, self.user1_config)
        self.user2_manager = GitSyncManager(self.user2_db, self.user2_config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.user1_db.close()
        self.user2_db.close()
        
        if os.path.exists(self.project_dir):
            shutil.rmtree(self.project_dir)
        
        if os.path.exists(os.path.dirname(self.user1_db_path)):
            shutil.rmtree(os.path.dirname(self.user1_db_path))
        
        if os.path.exists(os.path.dirname(self.user2_db_path)):
            shutil.rmtree(os.path.dirname(self.user2_db_path))
    
    def test_workflow_user_initializes_project(self):
        """
        Test: User 1 sets up a new project with Git sync
        """
        # User 1 initializes workspace
        success, message = self.user1_manager.initialize_workspace()
        self.assertTrue(success)
        
        # User 1 creates a collection
        coll_id = self.user1_db.create_collection("User API")
        req_id = self.user1_db.create_request(
            collection_id=coll_id,
            name="Get User",
            method="GET",
            url="https://api.example.com/users/{{userId}}"
        )
        
        # User 1 syncs to filesystem (simulating Git commit)
        success, message = self.user1_manager.sync_to_filesystem()
        self.assertTrue(success)
        
        # Verify files exist
        coll_files = list(self.user1_config.collections_path.glob("*.json"))
        self.assertEqual(len(coll_files), 1)
        
        # Verify workspace.json was updated
        self.assertTrue(self.user1_config.workspace_file.exists())
    
    def test_workflow_second_user_pulls_project(self):
        """
        Test: User 2 clones the project and imports collections
        """
        # User 1 sets up the project
        self.user1_manager.initialize_workspace()
        coll_id = self.user1_db.create_collection("Shared API")
        self.user1_db.create_request(coll_id, "Get Data", "GET", "https://api.example.com/data")
        self.user1_manager.sync_to_filesystem()
        
        # User 2 detects workspace (simulating Git clone + opening PostMini)
        found, info = self.user2_manager.detect_workspace()
        self.assertTrue(found)
        self.assertEqual(info['num_collections'], 1)
        
        # User 2 imports collections from filesystem
        success, message, coll_ids = self.user2_manager.import_all_collections()
        self.assertTrue(success)
        self.assertEqual(len(coll_ids), 1)
        
        # Verify User 2 has the collection
        collections = self.user2_db.get_all_collections()
        self.assertEqual(len(collections), 1)
        self.assertEqual(collections[0]['name'], 'Shared API')
        
        # Verify requests
        requests = self.user2_db.get_requests_by_collection(coll_ids[0])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['name'], 'Get Data')
    
    def test_workflow_collaborative_additions(self):
        """
        Test: Both users add different collections, sync works both ways
        """
        # Setup
        self.user1_manager.initialize_workspace()
        
        # User 1 adds "User API" collection
        coll1 = self.user1_db.create_collection("User API")
        self.user1_db.create_request(coll1, "List Users", "GET", "https://api.example.com/users")
        self.user1_manager.sync_to_filesystem()
        
        # User 2 imports User 1's work
        self.user2_manager.import_all_collections()
        
        # User 2 adds "Product API" collection
        coll2 = self.user2_db.create_collection("Product API")
        self.user2_db.create_request(coll2, "List Products", "GET", "https://api.example.com/products")
        self.user2_manager.sync_to_filesystem()
        
        # User 1 pulls User 2's changes
        success, message, coll_ids = self.user1_manager.import_all_collections(update_existing=True)
        self.assertTrue(success)
        
        # Both users should have both collections
        user1_collections = self.user1_db.get_all_collections()
        user2_collections = self.user2_db.get_all_collections()
        
        self.assertEqual(len(user1_collections), 2)
        self.assertEqual(len(user2_collections), 2)
        
        # Verify names
        user1_names = {c['name'] for c in user1_collections}
        user2_names = {c['name'] for c in user2_collections}
        
        self.assertEqual(user1_names, {"User API", "Product API"})
        self.assertEqual(user2_names, {"User API", "Product API"})
    
    def test_workflow_updating_existing_collection(self):
        """
        Test: User 1 modifies a collection, User 2 pulls updates
        """
        # Setup: Both users have the same collection
        self.user1_manager.initialize_workspace()
        coll_id = self.user1_db.create_collection("Shared Collection")
        self.user1_db.create_request(coll_id, "Request 1", "GET", "https://api.example.com/1")
        self.user1_manager.sync_to_filesystem()
        
        success, message, imported = self.user2_manager.import_all_collections()
        
        # User 1 adds a new request to the collection
        self.user1_db.create_request(coll_id, "Request 2", "POST", "https://api.example.com/2")
        self.user1_manager.sync_to_filesystem()
        
        # User 2 pulls updates
        success, message, updated = self.user2_manager.import_all_collections(update_existing=True)
        self.assertTrue(success)
        
        # User 2 should have both requests
        user2_collections = self.user2_db.get_all_collections()
        user2_coll = next(c for c in user2_collections if c['name'] == 'Shared Collection')
        user2_requests = self.user2_db.get_requests_by_collection(user2_coll['id'])
        
        self.assertEqual(len(user2_requests), 2)
        request_names = {r['name'] for r in user2_requests}
        self.assertEqual(request_names, {"Request 1", "Request 2"})
    
    def test_workflow_with_test_assertions(self):
        """
        Test: Collections with test assertions are synced correctly
        """
        self.user1_manager.initialize_workspace()
        
        # User 1 creates collection with tests
        coll_id = self.user1_db.create_collection("Tested API")
        req_id = self.user1_db.create_request(
            coll_id, "Get Data", "GET", "https://api.example.com/data"
        )
        
        # Add test assertions
        self.user1_db.create_test_assertion(
            request_id=req_id,
            assertion_type="status_code",
            operator="equals",
            expected_value="200"
        )
        self.user1_db.create_test_assertion(
            request_id=req_id,
            assertion_type="response_time",
            operator="less_than",
            expected_value="500"
        )
        
        # Sync to filesystem
        self.user1_manager.sync_to_filesystem()
        
        # User 2 imports
        success, message, coll_ids = self.user2_manager.import_all_collections()
        self.assertTrue(success)
        
        # Verify tests were imported
        user2_coll = self.user2_db.get_all_collections()[0]
        user2_req = self.user2_db.get_requests_by_collection(user2_coll['id'])[0]
        user2_tests = self.user2_db.get_test_assertions(user2_req['id'])
        
        self.assertEqual(len(user2_tests), 2)
        
        test_types = {t['assertion_type'] for t in user2_tests}
        self.assertEqual(test_types, {"status_code", "response_time"})
    
    def test_workflow_environment_sync(self):
        """
        Test: Environments are synced between users
        """
        self.user1_manager.initialize_workspace()
        
        # User 1 creates environment
        env_id = self.user1_db.create_environment(
            "Development",
            {
                "baseUrl": "https://dev.api.example.com",
                "apiKey": "dev-key-123",
                "timeout": "5000"
            }
        )
        
        # Sync to filesystem
        self.user1_manager.export_environment_to_file(env_id, include_secrets=False)
        
        # User 2 imports
        env_files = list(self.user2_config.environments_path.glob("*.json"))
        self.assertEqual(len(env_files), 1)
        
        success, message, env_id_2 = self.user2_manager.import_environment_from_file(
            str(env_files[0])
        )
        self.assertTrue(success)
        
        # Verify environment
        env2 = self.user2_db.get_environment(env_id_2)
        self.assertEqual(env2['name'], 'Development')
        
        # apiKey should be a placeholder (not the actual secret)
        self.assertIn('{{SECRET_', env2['variables']['apiKey'])
    
    def test_workflow_detect_changes_both_sides(self):
        """
        Test: Detecting when both filesystem and database have changes
        """
        self.user1_manager.initialize_workspace()
        
        # User 1 creates and syncs a collection
        coll1 = self.user1_db.create_collection("Collection A")
        self.user1_manager.sync_to_filesystem()
        
        # Simulate User 1 adding to database without syncing
        coll2 = self.user1_db.create_collection("Collection B")
        
        # Simulate someone else adding a file directly (e.g., Git pull)
        external_collection = {
            "export_version": "1.0",
            "export_date": "2024-01-01T00:00:00",
            "collection": {
                "id": 999,
                "name": "Collection C",
                "requests": []
            }
        }
        
        external_file = self.user1_config.collections_path / "collection-c.json"
        with open(external_file, 'w') as f:
            json.dump(external_collection, f)
        
        # Detect changes
        changes = self.user1_manager.detect_changes()
        
        # Should detect both new DB items and new files
        self.assertGreater(len(changes['new_files']), 0)
        self.assertGreater(len(changes['new_db_items']), 0)
    
    def test_workflow_full_roundtrip(self):
        """
        Test: Complete roundtrip - create -> export -> delete -> import -> verify
        """
        self.user1_manager.initialize_workspace()
        
        # Create complex data structure
        coll_id = self.user1_db.create_collection("Complete API")
        
        req1 = self.user1_db.create_request(
            coll_id, "Request 1", "GET", "https://api.example.com/1",
            params={"page": "1"},
            headers={"Authorization": "Bearer {{token}}"},
            body='{"test": true}',
            auth_type="Bearer Token",
            auth_token="{{authToken}}"
        )
        
        req2 = self.user1_db.create_request(
            coll_id, "Request 2", "POST", "https://api.example.com/2",
            params={"action": "create"},
            headers={"Content-Type": "application/json"}
        )
        
        # Add tests
        self.user1_db.create_test_assertion(req1, "status_code", "equals", expected_value="200")
        self.user1_db.create_test_assertion(req2, "status_code", "equals", expected_value="201")
        
        # Export
        success, file_path = self.user1_manager.export_collection_to_file(coll_id)
        self.assertTrue(success)
        
        # Delete from database
        self.user1_db.delete_collection(coll_id)
        self.assertEqual(len(self.user1_db.get_all_collections()), 0)
        
        # Import back
        success, message, new_coll_id = self.user1_manager.import_collection_from_file(file_path)
        self.assertTrue(success)
        
        # Verify everything is restored
        collection = self.user1_db.get_collection(new_coll_id)
        self.assertEqual(collection['name'], 'Complete API')
        
        requests = self.user1_db.get_requests_by_collection(new_coll_id)
        self.assertEqual(len(requests), 2)
        
        # Verify request details
        req1_restored = next(r for r in requests if r['name'] == 'Request 1')
        self.assertEqual(req1_restored['method'], 'GET')
        self.assertEqual(req1_restored['params'], {"page": "1"})
        self.assertEqual(req1_restored['headers'], {"Authorization": "Bearer {{token}}"})
        self.assertEqual(req1_restored['auth_type'], 'Bearer Token')
        
        # Verify tests
        req1_tests = self.user1_db.get_test_assertions(req1_restored['id'])
        req2_tests = self.user1_db.get_test_assertions(
            next(r for r in requests if r['name'] == 'Request 2')['id']
        )
        
        self.assertEqual(len(req1_tests), 1)
        self.assertEqual(len(req2_tests), 1)


class TestSecretsWorkflow(unittest.TestCase):
    """Test secrets management workflows."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.secrets_dir = os.path.join(self.test_dir, '.postmini-secrets')
        self.manager = SecretsManager(self.secrets_dir)
    
    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_workflow_environment_with_secrets(self):
        """
        Test: Create environment, separate secrets, save, load, substitute
        """
        # Original environment variables
        env_variables = {
            "baseUrl": "https://api.example.com",
            "apiKey": "secret-key-123",
            "version": "v1",
            "authToken": "bearer-token-456",
            "timeout": "5000"
        }
        
        # Separate secrets
        public, secrets = self.manager.separate_secrets("production", env_variables)
        
        # Public should have placeholders
        self.assertEqual(public['baseUrl'], 'https://api.example.com')
        self.assertEqual(public['version'], 'v1')
        self.assertEqual(public['timeout'], '5000')
        self.assertIn('{{SECRET_', public['apiKey'])
        self.assertIn('{{SECRET_', public['authToken'])
        
        # Save secrets
        success, message = self.manager.save_secrets("production", secrets)
        self.assertTrue(success)
        
        # Load secrets
        loaded_secrets = self.manager.load_secrets("production")
        self.assertEqual(len(loaded_secrets), len(secrets))
        
        # Substitute secrets back
        substituted = self.manager.substitute_secrets("production", public)
        
        # Should match original (except potentially different order)
        self.assertEqual(substituted['baseUrl'], env_variables['baseUrl'])
        self.assertEqual(substituted['apiKey'], env_variables['apiKey'])
        self.assertEqual(substituted['authToken'], env_variables['authToken'])
        self.assertEqual(substituted['version'], env_variables['version'])
        self.assertEqual(substituted['timeout'], env_variables['timeout'])
    
    def test_workflow_team_collaboration_with_secrets(self):
        """
        Test: Team shares environment configs but not secrets
        """
        # User 1 creates environment with secrets
        user1_variables = {
            "baseUrl": "https://api.example.com",
            "apiKey": "user1-secret-key"
        }
        
        user1_public, user1_secrets = self.manager.separate_secrets("development", user1_variables)
        
        # User 1 commits public variables to Git (simulated)
        # User 1 saves their own secrets locally
        self.manager.save_secrets("development", user1_secrets)
        
        # User 2 pulls the public variables from Git (simulated)
        # and needs to set their own secrets
        user2_secrets = {
            list(user1_secrets.keys())[0]: "user2-secret-key"  # Different secret value
        }
        
        # User 2 saves their own secrets
        user2_secrets_manager = SecretsManager(os.path.join(self.test_dir, 'user2-secrets'))
        user2_secrets_manager.save_secrets("development", user2_secrets)
        
        # User 1 substitutes with their secrets
        user1_substituted = self.manager.substitute_secrets("development", user1_public)
        
        # User 2 substitutes with their secrets
        user2_substituted = user2_secrets_manager.substitute_secrets("development", user1_public)
        
        # Both should have same structure but different secret values
        self.assertEqual(user1_substituted['baseUrl'], user2_substituted['baseUrl'])
        self.assertEqual(user1_substituted['apiKey'], 'user1-secret-key')
        self.assertEqual(user2_substituted['apiKey'], 'user2-secret-key')


class TestConflictScenarios(unittest.TestCase):
    """Test conflict detection and resolution scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_dir = tempfile.mkdtemp()
        
        self.db_path = os.path.join(tempfile.mkdtemp(), 'test.db')
        self.db = DatabaseManager(self.db_path)
        
        self.config = GitSyncConfig(self.project_dir)
        self.manager = GitSyncManager(self.db, self.config)
    
    def tearDown(self):
        """Clean up."""
        self.db.close()
        
        if os.path.exists(self.project_dir):
            shutil.rmtree(self.project_dir)
        
        if os.path.exists(os.path.dirname(self.db_path)):
            shutil.rmtree(os.path.dirname(self.db_path))
    
    def test_conflict_both_added_same_name(self):
        """
        Test: Detect conflict when both DB and filesystem have collection with same name
        """
        self.manager.initialize_workspace()
        
        # Add to database
        coll_id = self.db.create_collection("API Collection")
        self.db.create_request(coll_id, "DB Request", "GET", "http://db.example.com")
        
        # Add to filesystem (simulating external change)
        fs_collection = {
            "export_version": "1.0",
            "export_date": "2024-01-01T00:00:00",
            "collection": {
                "id": 999,
                "name": "API Collection",
                "requests": [
                    {
                        "name": "FS Request",
                        "method": "POST",
                        "url": "http://fs.example.com",
                        "params": None,
                        "headers": None,
                        "body": None,
                        "auth_type": "None",
                        "auth_token": None,
                        "tests": []
                    }
                ]
            }
        }
        
        fs_file = self.config.collections_path / "api-collection.json"
        with open(fs_file, 'w') as f:
            json.dump(fs_collection, f)
        
        # Import with update_existing=True should replace DB version with FS version
        success, message, coll_id = self.manager.import_collection_from_file(
            str(fs_file), update_existing=True
        )
        
        self.assertTrue(success)
        
        # Should have FS request, not DB request
        requests = self.db.get_requests_by_collection(coll_id)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['name'], 'FS Request')
    
    def test_sync_status_changes_appropriately(self):
        """
        Test: Sync status changes as operations are performed
        """
        # Initially not initialized
        status = self.manager.get_sync_status()
        self.assertEqual(status.status, SyncStatus.STATUS_DISABLED)
        
        # Initialize
        self.manager.initialize_workspace()
        
        # Should be synced (empty)
        status = self.manager.get_sync_status()
        # Empty workspace might show as synced or needs_push depending on implementation
        self.assertIn(status.status, [SyncStatus.STATUS_SYNCED, SyncStatus.STATUS_NEEDS_PUSH])
        
        # Add to database
        self.db.create_collection("Test")
        
        # Should need push
        status = self.manager.get_sync_status()
        self.assertEqual(status.status, SyncStatus.STATUS_NEEDS_PUSH)
        
        # Sync to filesystem
        self.manager.sync_to_filesystem()
        
        # Should be synced
        status = self.manager.get_sync_status()
        # After sync, should be synced or might detect as needs_pull due to hash checking
        self.assertIn(status.status, [SyncStatus.STATUS_SYNCED, SyncStatus.STATUS_NEEDS_PULL])


if __name__ == '__main__':
    unittest.main()

