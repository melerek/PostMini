"""
Tests for Selective Git Sync feature.

Tests database methods, export filtering, and secret variable tracking.
"""

import pytest
import os
import tempfile
import shutil
from src.core.database import DatabaseManager
from src.features.git_sync_manager import GitSyncManager, GitSyncConfig


@pytest.fixture
def db():
    """Create a test database."""
    # Create temp file for database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_file.close()
    
    db = DatabaseManager(db_file.name)
    yield db
    
    # Cleanup
    db.close()
    os.unlink(db_file.name)


@pytest.fixture
def git_sync(db):
    """Create a test GitSyncManager."""
    # Create temp directory for sync
    sync_dir = tempfile.mkdtemp()
    config = GitSyncConfig(sync_dir)
    
    # Initialize the workspace (creates necessary directories)
    manager = GitSyncManager(db, config)
    manager.initialize_workspace()
    
    yield manager
    
    # Cleanup
    shutil.rmtree(sync_dir, ignore_errors=True)


def test_collection_sync_status_default(db):
    """Test that new collections default to private (sync_to_git=0)."""
    collection_id = db.create_collection("Test Collection")
    collection = db.get_collection(collection_id)
    
    assert collection is not None
    assert collection.get('sync_to_git', 0) == 0  # Default is private


def test_set_collection_sync_status(db):
    """Test setting collection sync status."""
    collection_id = db.create_collection("Test Collection")
    
    # Make public
    db.set_collection_sync_status(collection_id, 1)
    collection = db.get_collection(collection_id)
    assert collection['sync_to_git'] == 1
    
    # Make private again
    db.set_collection_sync_status(collection_id, 0)
    collection = db.get_collection(collection_id)
    assert collection['sync_to_git'] == 0


def test_get_public_collections(db):
    """Test filtering public collections."""
    # Create collections with different sync statuses
    col1_id = db.create_collection("Public Collection 1")
    col2_id = db.create_collection("Private Collection")
    col3_id = db.create_collection("Public Collection 2")
    
    db.set_collection_sync_status(col1_id, 1)  # Public
    db.set_collection_sync_status(col2_id, 0)  # Private
    db.set_collection_sync_status(col3_id, 1)  # Public
    
    public_collections = db.get_public_collections()
    public_names = [c['name'] for c in public_collections]
    
    assert len(public_collections) == 2
    assert "Public Collection 1" in public_names
    assert "Public Collection 2" in public_names
    assert "Private Collection" not in public_names


def test_environment_sync_status_default(db):
    """Test that new environments default to private (sync_to_git=0)."""
    env_id = db.create_environment("Test Environment", {})
    env = db.get_environment(env_id)
    
    assert env is not None
    assert env.get('sync_to_git', 0) == 0  # Default is private


def test_set_environment_sync_status(db):
    """Test setting environment sync status."""
    env_id = db.create_environment("Test Environment", {"key": "value"})
    
    # Make public
    db.set_environment_sync_status(env_id, 1)
    env = db.get_environment(env_id)
    assert env['sync_to_git'] == 1
    
    # Make private again
    db.set_environment_sync_status(env_id, 0)
    env = db.get_environment(env_id)
    assert env['sync_to_git'] == 0


def test_get_public_environments(db):
    """Test filtering public environments."""
    # Create environments with different sync statuses
    env1_id = db.create_environment("Public Env 1", {})
    env2_id = db.create_environment("Private Env", {})
    env3_id = db.create_environment("Public Env 2", {})
    
    db.set_environment_sync_status(env1_id, 1)  # Public
    db.set_environment_sync_status(env2_id, 0)  # Private
    db.set_environment_sync_status(env3_id, 1)  # Public
    
    public_envs = db.get_public_environments()
    public_names = [e['name'] for e in public_envs]
    
    assert len(public_envs) == 2
    assert "Public Env 1" in public_names
    assert "Public Env 2" in public_names
    assert "Private Env" not in public_names


def test_secret_variable_tracking(db):
    """Test marking variables as secret."""
    env_id = db.create_environment("Test Env", {
        "apiKey": "secret123",
        "baseUrl": "https://api.example.com",
        "token": "token456"
    })
    
    # Mark apiKey and token as secrets
    db.mark_variable_as_secret(env_id, "apiKey")
    db.mark_variable_as_secret(env_id, "token")
    
    # Check secret status
    assert db.is_variable_secret(env_id, "apiKey") is True
    assert db.is_variable_secret(env_id, "token") is True
    assert db.is_variable_secret(env_id, "baseUrl") is False
    
    # Get all secrets
    secret_keys = db.get_secret_variables(env_id)
    assert len(secret_keys) == 2
    assert "apiKey" in secret_keys
    assert "token" in secret_keys
    
    # Mark apiKey as regular
    db.mark_variable_as_regular(env_id, "apiKey")
    assert db.is_variable_secret(env_id, "apiKey") is False
    
    secret_keys = db.get_secret_variables(env_id)
    assert len(secret_keys) == 1
    assert "token" in secret_keys


def test_export_only_public_collections(db, git_sync):
    """Test that GitSync only exports public collections."""
    # Create collections
    col1_id = db.create_collection("Public Collection")
    col2_id = db.create_collection("Private Collection")
    
    # Add a request to each
    db.create_request(col1_id, "Public Request", "GET", "https://api.example.com/public", {}, {}, None, None, None, None)
    db.create_request(col2_id, "Private Request", "GET", "https://api.example.com/private", {}, {}, None, None, None, None)
    
    # Make only col1 public
    db.set_collection_sync_status(col1_id, 1)
    
    # Export collections
    success, message, files = git_sync.export_all_collections()
    
    assert success is True
    assert len(files) == 1  # Only public collection exported
    assert "Public Collection" in files[0]
    assert "Private Collection" not in str(files)


def test_export_only_public_environments(db, git_sync):
    """Test that GitSync only exports public environments."""
    # Create environments
    env1_id = db.create_environment("Public Env", {"key1": "value1"})
    env2_id = db.create_environment("Private Env", {"key2": "value2"})
    
    # Make only env1 public
    db.set_environment_sync_status(env1_id, 1)
    
    # Export environments
    success, message, files = git_sync.export_all_environments()
    
    assert success is True
    assert len(files) == 1  # Only public environment exported
    assert "Public Env" in files[0]
    assert "Private Env" not in str(files)


def test_export_environment_with_secrets(db, git_sync):
    """Test that secret variables are exported with placeholders."""
    import json
    
    # Create environment with secrets
    env_id = db.create_environment("Test Env", {
        "apiKey": "secret123",
        "baseUrl": "https://api.example.com"
    })
    
    # Mark apiKey as secret
    db.mark_variable_as_secret(env_id, "apiKey")
    
    # Make environment public
    db.set_environment_sync_status(env_id, 1)
    
    # Export environment
    success, file_path = git_sync.export_environment_to_file(env_id)
    
    assert success is True
    assert os.path.exists(file_path)
    
    # Read exported file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check that secret is replaced with placeholder
    env_data = data['environment']
    assert '{{SECRET_apiKey}}' in str(env_data['variables']['apiKey'])
    assert env_data['variables']['baseUrl'] == "https://api.example.com"
    
    # Check that secret_keys field exists
    assert 'secret_keys' in env_data
    assert 'apiKey' in env_data['secret_keys']


def test_import_collection_marks_as_public(db, git_sync):
    """Test that importing from Git marks collection as public."""
    # Create and export a public collection
    col_id = db.create_collection("Test Collection")
    db.set_collection_sync_status(col_id, 1)
    db.create_request(col_id, "Test Request", "GET", "https://api.example.com", {}, {}, None, None, None, None)
    
    success, file_path = git_sync.export_collection_to_file(col_id)
    assert success is True
    
    # Delete the collection
    db.delete_collection(col_id)
    
    # Import it back
    success, message, imported_id = git_sync.import_collection_from_file(file_path)
    
    assert success is True
    assert imported_id is not None
    
    # Verify it's marked as public
    imported_collection = db.get_collection(imported_id)
    assert imported_collection['sync_to_git'] == 1


def test_import_environment_restores_secrets(db, git_sync):
    """Test that importing environment restores secret variable tracking."""
    import json
    
    # Create environment with secrets
    env_id = db.create_environment("Test Env", {
        "apiKey": "secret123",
        "baseUrl": "https://api.example.com"
    })
    db.mark_variable_as_secret(env_id, "apiKey")
    db.set_environment_sync_status(env_id, 1)
    
    # Export environment
    success, file_path = git_sync.export_environment_to_file(env_id)
    assert success is True
    
    # Delete the environment
    db.delete_environment(env_id)
    
    # Import it back
    success, message, imported_id = git_sync.import_environment_from_file(file_path)
    
    assert success is True
    assert imported_id is not None
    
    # Verify sync status
    imported_env = db.get_environment(imported_id)
    assert imported_env['sync_to_git'] == 1
    
    # Verify secret tracking is restored
    assert db.is_variable_secret(imported_id, "apiKey") is True
    assert db.is_variable_secret(imported_id, "baseUrl") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
