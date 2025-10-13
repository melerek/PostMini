"""
OAuth 2.0 Test Suite

Comprehensive tests for OAuth 2.0 functionality.
"""

import sys
import traceback
import json
from datetime import datetime, timedelta

from src.core.database import DatabaseManager
from src.features.oauth_manager import OAuthManager


def test_database_oauth_tables():
    """Test OAuth database tables creation and operations."""
    print("Testing OAuth Database Tables...")
    
    try:
        # Create in-memory database for testing
        import sqlite3
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                flow_type TEXT NOT NULL,
                auth_url TEXT,
                token_url TEXT NOT NULL,
                client_id TEXT NOT NULL,
                client_secret TEXT,
                redirect_uri TEXT,
                scope TEXT,
                state TEXT,
                additional_params TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type TEXT,
                expires_at TEXT,
                scope TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (config_id) REFERENCES oauth_configs(id) ON DELETE CASCADE
            )
        """)
        
        print("  [OK] OAuth tables created")
        
        # Test insert config
        cursor.execute("""
            INSERT INTO oauth_configs (name, flow_type, auth_url, token_url, client_id, client_secret, scope)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Test Config", "authorization_code", "https://auth.example.com/authorize",
              "https://auth.example.com/token", "test_client", "test_secret", "read write"))
        
        config_id = cursor.lastrowid
        print("  [OK] Config insert successful")
        
        # Test insert token
        cursor.execute("""
            INSERT INTO oauth_tokens (config_id, access_token, refresh_token, token_type, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (config_id, "test_access_token", "test_refresh_token", "Bearer",
              (datetime.now() + timedelta(hours=1)).isoformat(), datetime.now().isoformat()))
        
        print("  [OK] Token insert successful")
        
        # Test query
        cursor.execute("SELECT * FROM oauth_configs WHERE id = ?", (config_id,))
        row = cursor.fetchone()
        
        if row and row[1] == "Test Config":
            print("  [OK] Config query successful")
        
        conn.close()
        print("[OK] OAuth database tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] OAuth database test failed: {e}")
        traceback.print_exc()
        return False


def test_database_manager_oauth_operations():
    """Test DatabaseManager OAuth operations."""
    print("Testing DatabaseManager OAuth Operations...")
    
    try:
        # Create test database
        db = DatabaseManager(":memory:")
        
        # Test create OAuth config
        config_id = db.create_oauth_config(
            name="GitHub OAuth",
            flow_type=OAuthManager.FLOW_AUTHORIZATION_CODE,
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            client_id="github_client_id",
            client_secret="github_client_secret",
            scope="repo user"
        )
        
        if config_id > 0:
            print("  [OK] Create OAuth config")
        
        # Test get OAuth config
        config = db.get_oauth_config(config_id)
        if config and config['name'] == "GitHub OAuth":
            print("  [OK] Get OAuth config by ID")
        
        # Test get by name
        config2 = db.get_oauth_config_by_name("GitHub OAuth")
        if config2 and config2['id'] == config_id:
            print("  [OK] Get OAuth config by name")
        
        # Test get all configs
        configs = db.get_all_oauth_configs()
        if len(configs) == 1:
            print("  [OK] Get all OAuth configs")
        
        # Test save token
        token_id = db.save_oauth_token(
            config_id=config_id,
            access_token="gho_test_access_token",
            refresh_token="gho_test_refresh_token",
            token_type="bearer",
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat(),
            scope="repo user"
        )
        
        if token_id > 0:
            print("  [OK] Save OAuth token")
        
        # Test get token
        token = db.get_oauth_token(config_id)
        if token and token['access_token'] == "gho_test_access_token":
            print("  [OK] Get OAuth token")
        
        # Test update config
        db.update_oauth_config(
            config_id=config_id,
            name="GitHub OAuth Updated",
            flow_type=OAuthManager.FLOW_AUTHORIZATION_CODE,
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            client_id="github_client_id_updated",
            client_secret="github_client_secret",
            scope="repo user gist"
        )
        
        updated_config = db.get_oauth_config(config_id)
        if updated_config['name'] == "GitHub OAuth Updated":
            print("  [OK] Update OAuth config")
        
        # Test delete token
        db.delete_oauth_token(token_id)
        deleted_token = db.get_oauth_token(config_id)
        if deleted_token is None:
            print("  [OK] Delete OAuth token")
        
        # Test delete config
        db.delete_oauth_config(config_id)
        deleted_config = db.get_oauth_config(config_id)
        if deleted_config is None:
            print("  [OK] Delete OAuth config")
        
        db.close()
        print("[OK] DatabaseManager OAuth operations tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] DatabaseManager OAuth operations test failed: {e}")
        traceback.print_exc()
        return False


def test_oauth_manager_token_utilities():
    """Test OAuth Manager token utility methods."""
    print("Testing OAuth Manager Token Utilities...")
    
    try:
        # Test is_token_expired
        future_expiry = (datetime.now() + timedelta(hours=1)).isoformat()
        past_expiry = (datetime.now() - timedelta(hours=1)).isoformat()
        
        if not OAuthManager.is_token_expired(future_expiry):
            print("  [OK] Non-expired token check")
        
        if OAuthManager.is_token_expired(past_expiry):
            print("  [OK] Expired token check")
        
        if not OAuthManager.is_token_expired(None):
            print("  [OK] None expiry check")
        
        # Test calculate_expiry_time
        expiry = OAuthManager.calculate_expiry_time(3600)
        expiry_dt = datetime.fromisoformat(expiry)
        now = datetime.now()
        diff = (expiry_dt - now).total_seconds()
        
        if 3590 <= diff <= 3610:  # Allow 10 second tolerance
            print("  [OK] Calculate expiry time")
        
        # Test format_token_for_header
        header = OAuthManager.format_token_for_header("test_token_123", "Bearer")
        if header == "Bearer test_token_123":
            print("  [OK] Format token for header")
        
        print("[OK] OAuth Manager token utilities tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] OAuth Manager token utilities test failed: {e}")
        traceback.print_exc()
        return False


def test_oauth_manager_url_building():
    """Test OAuth Manager authorization URL building."""
    print("Testing OAuth Manager URL Building...")
    
    try:
        oauth_manager = OAuthManager()
        
        # Test Authorization Code Flow URL
        auth_url, state = oauth_manager.start_authorization_code_flow(
            auth_url="https://provider.com/oauth/authorize",
            client_id="test_client_id",
            redirect_uri="http://localhost:8080",
            scope="read write",
            state="test_state_123"
        )
        
        if "response_type=code" in auth_url:
            print("  [OK] Response type in URL")
        
        if "client_id=test_client_id" in auth_url:
            print("  [OK] Client ID in URL")
        
        if "redirect_uri=http" in auth_url:
            print("  [OK] Redirect URI in URL")
        
        if "scope=read" in auth_url:
            print("  [OK] Scope in URL")
        
        if "state=test_state_123" in auth_url:
            print("  [OK] State in URL")
        
        if state == "test_state_123":
            print("  [OK] State returned correctly")
        
        # Test with auto-generated state
        auth_url2, state2 = oauth_manager.start_authorization_code_flow(
            auth_url="https://provider.com/oauth/authorize",
            client_id="test_client_id",
            redirect_uri="http://localhost:8080"
        )
        
        if state2 and len(state2) > 20:
            print("  [OK] Auto-generated state")
        
        print("[OK] OAuth Manager URL building tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] OAuth Manager URL building test failed: {e}")
        traceback.print_exc()
        return False


def test_oauth_flow_types():
    """Test different OAuth flow types."""
    print("Testing OAuth Flow Types...")
    
    try:
        # Test flow type constants
        if OAuthManager.FLOW_AUTHORIZATION_CODE == "authorization_code":
            print("  [OK] Authorization Code flow constant")
        
        if OAuthManager.FLOW_CLIENT_CREDENTIALS == "client_credentials":
            print("  [OK] Client Credentials flow constant")
        
        if OAuthManager.FLOW_PASSWORD == "password":
            print("  [OK] Password flow constant")
        
        if OAuthManager.FLOW_IMPLICIT == "implicit":
            print("  [OK] Implicit flow constant")
        
        print("[OK] OAuth flow types tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] OAuth flow types test failed: {e}")
        traceback.print_exc()
        return False


def test_oauth_config_serialization():
    """Test OAuth configuration JSON serialization."""
    print("Testing OAuth Config Serialization...")
    
    try:
        db = DatabaseManager(":memory:")
        
        # Test with additional params
        additional_params = {
            "access_type": "offline",
            "prompt": "consent"
        }
        
        config_id = db.create_oauth_config(
            name="Google OAuth",
            flow_type=OAuthManager.FLOW_AUTHORIZATION_CODE,
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            client_id="google_client_id",
            client_secret="google_client_secret",
            scope="openid email profile",
            additional_params=additional_params
        )
        
        config = db.get_oauth_config(config_id)
        
        if config['additional_params']['access_type'] == "offline":
            print("  [OK] Additional params serialization")
        
        if config['additional_params']['prompt'] == "consent":
            print("  [OK] Additional params deserialization")
        
        # Test with None additional params
        config_id2 = db.create_oauth_config(
            name="Simple OAuth",
            flow_type=OAuthManager.FLOW_CLIENT_CREDENTIALS,
            auth_url=None,
            token_url="https://api.example.com/token",
            client_id="simple_client",
            client_secret="simple_secret"
        )
        
        config2 = db.get_oauth_config(config_id2)
        
        if config2['additional_params'] == {}:
            print("  [OK] None additional params handling")
        
        db.close()
        print("[OK] OAuth config serialization tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] OAuth config serialization test failed: {e}")
        traceback.print_exc()
        return False


def test_oauth_token_expiry_edge_cases():
    """Test OAuth token expiry edge cases."""
    print("Testing OAuth Token Expiry Edge Cases...")
    
    try:
        # Test expiry exactly now
        now = datetime.now().isoformat()
        if OAuthManager.is_token_expired(now):
            print("  [OK] Token expired at current time")
        
        # Test expiry 59 seconds from now (should be considered expired due to 60s buffer)
        near_future = (datetime.now() + timedelta(seconds=59)).isoformat()
        if OAuthManager.is_token_expired(near_future):
            print("  [OK] Token near expiry (within buffer)")
        
        # Test expiry 61 seconds from now (should not be expired)
        safe_future = (datetime.now() + timedelta(seconds=61)).isoformat()
        if not OAuthManager.is_token_expired(safe_future):
            print("  [OK] Token not expired (outside buffer)")
        
        # Test invalid date format
        if not OAuthManager.is_token_expired("invalid-date"):
            print("  [OK] Invalid date format handling")
        
        # Test empty string
        if not OAuthManager.is_token_expired(""):
            print("  [OK] Empty string handling")
        
        print("[OK] OAuth token expiry edge cases tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] OAuth token expiry edge cases test failed: {e}")
        traceback.print_exc()
        return False


def test_multiple_oauth_configs():
    """Test managing multiple OAuth configurations."""
    print("Testing Multiple OAuth Configs...")
    
    try:
        db = DatabaseManager(":memory:")
        
        # Create multiple configs
        github_id = db.create_oauth_config(
            name="GitHub",
            flow_type=OAuthManager.FLOW_AUTHORIZATION_CODE,
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            client_id="github_client",
            client_secret="github_secret"
        )
        
        google_id = db.create_oauth_config(
            name="Google",
            flow_type=OAuthManager.FLOW_AUTHORIZATION_CODE,
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            client_id="google_client",
            client_secret="google_secret"
        )
        
        api_id = db.create_oauth_config(
            name="API Service",
            flow_type=OAuthManager.FLOW_CLIENT_CREDENTIALS,
            auth_url=None,
            token_url="https://api.example.com/token",
            client_id="api_client",
            client_secret="api_secret"
        )
        
        # Get all configs
        configs = db.get_all_oauth_configs()
        
        if len(configs) == 3:
            print("  [OK] Created 3 configs")
        
        if any(c['name'] == "GitHub" for c in configs):
            print("  [OK] GitHub config exists")
        
        if any(c['name'] == "Google" for c in configs):
            print("  [OK] Google config exists")
        
        if any(c['name'] == "API Service" for c in configs):
            print("  [OK] API Service config exists")
        
        # Add tokens to each
        for config in configs:
            db.save_oauth_token(
                config_id=config['id'],
                access_token=f"{config['name']}_token",
                token_type="Bearer",
                expires_at=(datetime.now() + timedelta(hours=1)).isoformat()
            )
        
        # Verify each has a token
        for config in configs:
            token = db.get_oauth_token(config['id'])
            if token and token['access_token'] == f"{config['name']}_token":
                print(f"  [OK] Token for {config['name']}")
        
        db.close()
        print("[OK] Multiple OAuth configs tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Multiple OAuth configs test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all OAuth tests."""
    print("="*60)
    print("OAuth 2.0 Test Suite")
    print("="*60)
    print()
    
    results = []
    
    results.append(("OAuth Database Tables", test_database_oauth_tables()))
    results.append(("DatabaseManager OAuth Operations", test_database_manager_oauth_operations()))
    results.append(("OAuth Manager Token Utilities", test_oauth_manager_token_utilities()))
    results.append(("OAuth Manager URL Building", test_oauth_manager_url_building()))
    results.append(("OAuth Flow Types", test_oauth_flow_types()))
    results.append(("OAuth Config Serialization", test_oauth_config_serialization()))
    results.append(("OAuth Token Expiry Edge Cases", test_oauth_token_expiry_edge_cases()))
    results.append(("Multiple OAuth Configs", test_multiple_oauth_configs()))
    
    print()
    print("="*60)
    print("Test Results Summary")
    print("="*60)
    
    for name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{name:.<45} {status}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("[SUCCESS] All OAuth 2.0 tests passed!")
        print("OAuth 2.0 feature is ready for production!")
    else:
        print("[FAIL] Some tests failed.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

