"""
Database Manager Module

This module handles all SQLite database operations for the API client application.
It manages collections, requests, and environments with full CRUD functionality.
"""

import sqlite3
import json
from typing import List, Dict, Optional, Tuple


class DatabaseManager:
    """
    Manages SQLite database operations for collections, requests, and environments.
    """
    
    def __init__(self, db_path: str = "api_client.db"):
        """
        Initialize the database manager and create tables if they don't exist.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish connection to the SQLite database."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Enable column access by name
    
    def _create_tables(self):
        """Create the database schema if tables don't exist."""
        cursor = self.connection.cursor()
        
        # Create collections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        
        # Create requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                params TEXT,
                headers TEXT,
                body TEXT,
                auth_type TEXT DEFAULT 'None',
                auth_token TEXT,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
            )
        """)
        
        # Create environments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS environments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                variables TEXT
            )
        """)
        
        # Create request history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                collection_id INTEGER,
                request_id INTEGER,
                request_name TEXT,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                request_params TEXT,
                request_headers TEXT,
                request_body TEXT,
                request_auth_type TEXT,
                request_auth_token TEXT,
                response_status INTEGER,
                response_headers TEXT,
                response_body TEXT,
                response_time REAL,
                response_size INTEGER,
                error_message TEXT,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL,
                FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE SET NULL
            )
        """)
        
        # Create OAuth configs table
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
        
        # Create OAuth tokens table
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
        
        # Create test assertions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_assertions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                assertion_type TEXT NOT NULL,
                field TEXT,
                operator TEXT NOT NULL,
                expected_value TEXT,
                enabled INTEGER DEFAULT 1,
                FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
            )
        """)
        
        # Create test results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                assertion_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                passed INTEGER NOT NULL,
                actual_value TEXT,
                error_message TEXT,
                FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
                FOREIGN KEY (assertion_id) REFERENCES test_assertions(id) ON DELETE CASCADE
            )
        """)
        
        self.connection.commit()
    
    # ==================== Collection Operations ====================
    
    def create_collection(self, name: str) -> int:
        """
        Create a new collection.
        
        Args:
            name: Name of the collection
            
        Returns:
            ID of the newly created collection
            
        Raises:
            sqlite3.IntegrityError: If collection name already exists
        """
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO collections (name) VALUES (?)", (name,))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_all_collections(self) -> List[Dict]:
        """
        Retrieve all collections from the database.
        
        Returns:
            List of dictionaries containing collection data
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM collections ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_collection(self, collection_id: int) -> Optional[Dict]:
        """
        Retrieve a specific collection by ID.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            Dictionary containing collection data or None if not found
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM collections WHERE id = ?", (collection_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_collection(self, collection_id: int, name: str):
        """
        Update a collection's name.
        
        Args:
            collection_id: ID of the collection to update
            name: New name for the collection
        """
        cursor = self.connection.cursor()
        cursor.execute("UPDATE collections SET name = ? WHERE id = ?", 
                      (name, collection_id))
        self.connection.commit()
    
    def delete_collection(self, collection_id: int):
        """
        Delete a collection and all its associated requests.
        
        Args:
            collection_id: ID of the collection to delete
        """
        cursor = self.connection.cursor()
        # First delete all requests in this collection
        cursor.execute("DELETE FROM requests WHERE collection_id = ?", (collection_id,))
        # Then delete the collection itself
        cursor.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        self.connection.commit()
    
    # ==================== Request Operations ====================
    
    def create_request(self, collection_id: int, name: str, method: str, url: str,
                      params: Optional[Dict] = None, headers: Optional[Dict] = None,
                      body: Optional[str] = None, auth_type: str = 'None',
                      auth_token: Optional[str] = None) -> int:
        """
        Create a new request in a collection.
        
        Args:
            collection_id: ID of the parent collection
            name: Name of the request
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters as dictionary
            headers: Request headers as dictionary
            body: Request body (usually JSON string)
            auth_type: Type of authentication ('None', 'Bearer Token')
            auth_token: Authentication token
            
        Returns:
            ID of the newly created request
        """
        cursor = self.connection.cursor()
        
        # Convert dictionaries to JSON strings
        params_json = json.dumps(params) if params else None
        headers_json = json.dumps(headers) if headers else None
        
        cursor.execute("""
            INSERT INTO requests 
            (collection_id, name, method, url, params, headers, body, auth_type, auth_token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (collection_id, name, method, url, params_json, headers_json, 
              body, auth_type, auth_token))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_requests_by_collection(self, collection_id: int) -> List[Dict]:
        """
        Retrieve all requests for a specific collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            List of dictionaries containing request data
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM requests 
            WHERE collection_id = ? 
            ORDER BY name
        """, (collection_id,))
        rows = cursor.fetchall()
        
        # Convert JSON strings back to dictionaries
        requests = []
        for row in rows:
            request = dict(row)
            if request['params']:
                request['params'] = json.loads(request['params'])
            if request['headers']:
                request['headers'] = json.loads(request['headers'])
            requests.append(request)
        
        return requests
    
    def get_request(self, request_id: int) -> Optional[Dict]:
        """
        Retrieve a specific request by ID.
        
        Args:
            request_id: ID of the request
            
        Returns:
            Dictionary containing request data or None if not found
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        request = dict(row)
        # Parse JSON fields
        if request['params']:
            request['params'] = json.loads(request['params'])
        if request['headers']:
            request['headers'] = json.loads(request['headers'])
        
        return request
    
    def update_request(self, request_id: int, name: str, method: str, url: str,
                      params: Optional[Dict] = None, headers: Optional[Dict] = None,
                      body: Optional[str] = None, auth_type: str = 'None',
                      auth_token: Optional[str] = None):
        """
        Update an existing request.
        
        Args:
            request_id: ID of the request to update
            name: New name for the request
            method: HTTP method
            url: Request URL
            params: Query parameters as dictionary
            headers: Request headers as dictionary
            body: Request body
            auth_type: Type of authentication
            auth_token: Authentication token
        """
        cursor = self.connection.cursor()
        
        # Convert dictionaries to JSON strings
        params_json = json.dumps(params) if params else None
        headers_json = json.dumps(headers) if headers else None
        
        cursor.execute("""
            UPDATE requests 
            SET name = ?, method = ?, url = ?, params = ?, headers = ?, 
                body = ?, auth_type = ?, auth_token = ?
            WHERE id = ?
        """, (name, method, url, params_json, headers_json, body, 
              auth_type, auth_token, request_id))
        
        self.connection.commit()
    
    def delete_request(self, request_id: int):
        """
        Delete a specific request.
        
        Args:
            request_id: ID of the request to delete
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM requests WHERE id = ?", (request_id,))
        self.connection.commit()
    
    # ==================== Environment Operations ====================
    
    def create_environment(self, name: str, variables: Dict) -> int:
        """
        Create a new environment.
        
        Args:
            name: Name of the environment
            variables: Dictionary of environment variables
            
        Returns:
            ID of the newly created environment
        """
        cursor = self.connection.cursor()
        variables_json = json.dumps(variables)
        cursor.execute("INSERT INTO environments (name, variables) VALUES (?, ?)",
                      (name, variables_json))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_all_environments(self) -> List[Dict]:
        """
        Retrieve all environments.
        
        Returns:
            List of dictionaries containing environment data
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM environments ORDER BY name")
        rows = cursor.fetchall()
        
        environments = []
        for row in rows:
            env = dict(row)
            if env['variables']:
                env['variables'] = json.loads(env['variables'])
            environments.append(env)
        
        return environments
    
    def get_environment(self, environment_id: int) -> Optional[Dict]:
        """
        Retrieve a specific environment by ID.
        
        Args:
            environment_id: ID of the environment
            
        Returns:
            Dictionary containing environment data or None if not found
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM environments WHERE id = ?", (environment_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        env = dict(row)
        if env['variables']:
            env['variables'] = json.loads(env['variables'])
        
        return env
    
    def update_environment(self, environment_id: int, name: str, variables: Dict):
        """
        Update an existing environment.
        
        Args:
            environment_id: ID of the environment to update
            name: New name for the environment
            variables: Dictionary of environment variables
        """
        cursor = self.connection.cursor()
        variables_json = json.dumps(variables)
        cursor.execute("UPDATE environments SET name = ?, variables = ? WHERE id = ?",
                      (name, variables_json, environment_id))
        self.connection.commit()
    
    def delete_environment(self, environment_id: int):
        """
        Delete an environment.
        
        Args:
            environment_id: ID of the environment to delete
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM environments WHERE id = ?", (environment_id,))
        self.connection.commit()
    
    # ==================== Request History Operations ====================
    
    def save_request_history(self, timestamp: str, method: str, url: str,
                            collection_id: Optional[int] = None,
                            request_id: Optional[int] = None,
                            request_name: Optional[str] = None,
                            request_params: Optional[Dict] = None,
                            request_headers: Optional[Dict] = None,
                            request_body: Optional[str] = None,
                            request_auth_type: Optional[str] = None,
                            request_auth_token: Optional[str] = None,
                            response_status: Optional[int] = None,
                            response_headers: Optional[Dict] = None,
                            response_body: Optional[str] = None,
                            response_time: Optional[float] = None,
                            response_size: Optional[int] = None,
                            error_message: Optional[str] = None) -> int:
        """
        Save a request execution to history.
        
        Args:
            timestamp: ISO format timestamp
            method: HTTP method
            url: Request URL
            collection_id: ID of the collection (if applicable)
            request_id: ID of the saved request (if applicable)
            request_name: Name of the request
            request_params: Query parameters
            request_headers: Request headers
            request_body: Request body
            request_auth_type: Auth type
            request_auth_token: Auth token
            response_status: HTTP status code
            response_headers: Response headers
            response_body: Response body (truncated if too large)
            response_time: Response time in seconds
            response_size: Response size in bytes
            error_message: Error message if request failed
            
        Returns:
            ID of the history entry
        """
        cursor = self.connection.cursor()
        
        # Convert dicts to JSON
        params_json = json.dumps(request_params) if request_params else None
        req_headers_json = json.dumps(request_headers) if request_headers else None
        resp_headers_json = json.dumps(response_headers) if response_headers else None
        
        # Truncate response body if too large (keep first 100KB)
        if response_body and len(response_body) > 102400:
            response_body = response_body[:102400] + "\n... (truncated)"
        
        cursor.execute("""
            INSERT INTO request_history
            (timestamp, collection_id, request_id, request_name, method, url,
             request_params, request_headers, request_body, request_auth_type,
             request_auth_token, response_status, response_headers, response_body,
             response_time, response_size, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, collection_id, request_id, request_name, method, url,
              params_json, req_headers_json, request_body, request_auth_type,
              request_auth_token, response_status, resp_headers_json, response_body,
              response_time, response_size, error_message))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_request_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Retrieve request history entries.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            List of history entries (most recent first)
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM request_history
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            entry = dict(row)
            # Parse JSON fields
            if entry['request_params']:
                entry['request_params'] = json.loads(entry['request_params'])
            if entry['request_headers']:
                entry['request_headers'] = json.loads(entry['request_headers'])
            if entry['response_headers']:
                entry['response_headers'] = json.loads(entry['response_headers'])
            history.append(entry)
        
        return history
    
    def get_history_entry(self, history_id: int) -> Optional[Dict]:
        """
        Retrieve a specific history entry.
        
        Args:
            history_id: ID of the history entry
            
        Returns:
            Dictionary containing history entry or None
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM request_history WHERE id = ?", (history_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        entry = dict(row)
        # Parse JSON fields
        if entry['request_params']:
            entry['request_params'] = json.loads(entry['request_params'])
        if entry['request_headers']:
            entry['request_headers'] = json.loads(entry['request_headers'])
        if entry['response_headers']:
            entry['response_headers'] = json.loads(entry['response_headers'])
        
        return entry
    
    def get_history_by_collection(self, collection_id: int, limit: int = 50) -> List[Dict]:
        """
        Get history entries for a specific collection.
        
        Args:
            collection_id: ID of the collection
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM request_history
            WHERE collection_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (collection_id, limit))
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            entry = dict(row)
            if entry['request_params']:
                entry['request_params'] = json.loads(entry['request_params'])
            if entry['request_headers']:
                entry['request_headers'] = json.loads(entry['request_headers'])
            if entry['response_headers']:
                entry['response_headers'] = json.loads(entry['response_headers'])
            history.append(entry)
        
        return history
    
    def get_history_by_status(self, status_code: int, limit: int = 50) -> List[Dict]:
        """
        Get history entries by status code.
        
        Args:
            status_code: HTTP status code (e.g., 200, 404, 500)
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM request_history
            WHERE response_status = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (status_code, limit))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_failed_requests(self, limit: int = 50) -> List[Dict]:
        """
        Get history entries for failed requests (4xx and 5xx status codes or errors).
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of failed request entries
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM request_history
            WHERE (response_status >= 400 OR error_message IS NOT NULL)
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def clear_history(self, older_than_days: Optional[int] = None):
        """
        Clear request history.
        
        Args:
            older_than_days: If specified, only clear entries older than this many days
        """
        cursor = self.connection.cursor()
        
        if older_than_days:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=older_than_days)).isoformat()
            cursor.execute("DELETE FROM request_history WHERE timestamp < ?", (cutoff_date,))
        else:
            cursor.execute("DELETE FROM request_history")
        
        self.connection.commit()
    
    def get_history_count(self) -> int:
        """Get total number of history entries."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM request_history")
        return cursor.fetchone()[0]
    
    # ==================== OAuth Operations ====================
    
    def create_oauth_config(self, name: str, flow_type: str, auth_url: Optional[str],
                           token_url: str, client_id: str, client_secret: Optional[str] = None,
                           redirect_uri: Optional[str] = None, scope: Optional[str] = None,
                           state: Optional[str] = None, additional_params: Optional[Dict] = None) -> int:
        """Create a new OAuth configuration."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO oauth_configs (name, flow_type, auth_url, token_url, client_id,
                                      client_secret, redirect_uri, scope, state, additional_params)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, flow_type, auth_url, token_url, client_id, client_secret,
              redirect_uri, scope, state, json.dumps(additional_params) if additional_params else None))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_oauth_config(self, config_id: int) -> Optional[Dict]:
        """Get an OAuth configuration by ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM oauth_configs WHERE id = ?", (config_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'flow_type': row[2],
                'auth_url': row[3],
                'token_url': row[4],
                'client_id': row[5],
                'client_secret': row[6],
                'redirect_uri': row[7],
                'scope': row[8],
                'state': row[9],
                'additional_params': json.loads(row[10]) if row[10] else {}
            }
        return None
    
    def get_oauth_config_by_name(self, name: str) -> Optional[Dict]:
        """Get an OAuth configuration by name."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM oauth_configs WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'flow_type': row[2],
                'auth_url': row[3],
                'token_url': row[4],
                'client_id': row[5],
                'client_secret': row[6],
                'redirect_uri': row[7],
                'scope': row[8],
                'state': row[9],
                'additional_params': json.loads(row[10]) if row[10] else {}
            }
        return None
    
    def get_all_oauth_configs(self) -> List[Dict]:
        """Get all OAuth configurations."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM oauth_configs")
        configs = []
        for row in cursor.fetchall():
            configs.append({
                'id': row[0],
                'name': row[1],
                'flow_type': row[2],
                'auth_url': row[3],
                'token_url': row[4],
                'client_id': row[5],
                'client_secret': row[6],
                'redirect_uri': row[7],
                'scope': row[8],
                'state': row[9],
                'additional_params': json.loads(row[10]) if row[10] else {}
            })
        return configs
    
    def update_oauth_config(self, config_id: int, name: str, flow_type: str,
                           auth_url: Optional[str], token_url: str, client_id: str,
                           client_secret: Optional[str] = None, redirect_uri: Optional[str] = None,
                           scope: Optional[str] = None, state: Optional[str] = None,
                           additional_params: Optional[Dict] = None):
        """Update an OAuth configuration."""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE oauth_configs
            SET name = ?, flow_type = ?, auth_url = ?, token_url = ?, client_id = ?,
                client_secret = ?, redirect_uri = ?, scope = ?, state = ?, additional_params = ?
            WHERE id = ?
        """, (name, flow_type, auth_url, token_url, client_id, client_secret,
              redirect_uri, scope, state, json.dumps(additional_params) if additional_params else None,
              config_id))
        self.connection.commit()
    
    def delete_oauth_config(self, config_id: int):
        """Delete an OAuth configuration and its tokens."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM oauth_configs WHERE id = ?", (config_id,))
        self.connection.commit()
    
    # OAuth Token Operations
    
    def save_oauth_token(self, config_id: int, access_token: str, refresh_token: Optional[str] = None,
                        token_type: Optional[str] = None, expires_at: Optional[str] = None,
                        scope: Optional[str] = None) -> int:
        """Save an OAuth token."""
        from datetime import datetime
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO oauth_tokens (config_id, access_token, refresh_token, token_type,
                                     expires_at, scope, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (config_id, access_token, refresh_token, token_type, expires_at,
              scope, datetime.now().isoformat()))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_oauth_token(self, config_id: int) -> Optional[Dict]:
        """Get the latest OAuth token for a configuration."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM oauth_tokens
            WHERE config_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (config_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'config_id': row[1],
                'access_token': row[2],
                'refresh_token': row[3],
                'token_type': row[4],
                'expires_at': row[5],
                'scope': row[6],
                'created_at': row[7]
            }
        return None
    
    def delete_oauth_token(self, token_id: int):
        """Delete an OAuth token."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM oauth_tokens WHERE id = ?", (token_id,))
        self.connection.commit()
    
    def delete_all_tokens_for_config(self, config_id: int):
        """Delete all tokens for an OAuth configuration."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM oauth_tokens WHERE config_id = ?", (config_id,))
        self.connection.commit()
    
    # ==================== Test Assertions Operations ====================
    
    def create_test_assertion(self, request_id: int, assertion_type: str, operator: str,
                             field: Optional[str] = None, expected_value: Optional[str] = None,
                             enabled: bool = True) -> int:
        """Create a new test assertion for a request."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO test_assertions (request_id, assertion_type, field, operator, expected_value, enabled)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (request_id, assertion_type, field, operator, expected_value, 1 if enabled else 0))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_test_assertions(self, request_id: int) -> List[Dict]:
        """Get all test assertions for a request."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM test_assertions WHERE request_id = ? ORDER BY id", (request_id,))
        assertions = []
        for row in cursor.fetchall():
            assertions.append({
                'id': row[0],
                'request_id': row[1],
                'assertion_type': row[2],
                'field': row[3],
                'operator': row[4],
                'expected_value': row[5],
                'enabled': bool(row[6])
            })
        return assertions
    
    def update_test_assertion(self, assertion_id: int, assertion_type: str, operator: str,
                             field: Optional[str] = None, expected_value: Optional[str] = None,
                             enabled: bool = True):
        """Update a test assertion."""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE test_assertions
            SET assertion_type = ?, field = ?, operator = ?, expected_value = ?, enabled = ?
            WHERE id = ?
        """, (assertion_type, field, operator, expected_value, 1 if enabled else 0, assertion_id))
        self.connection.commit()
    
    def delete_test_assertion(self, assertion_id: int):
        """Delete a test assertion."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM test_assertions WHERE id = ?", (assertion_id,))
        self.connection.commit()
    
    def delete_all_assertions_for_request(self, request_id: int):
        """Delete all test assertions for a request."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM test_assertions WHERE request_id = ?", (request_id,))
        self.connection.commit()
    
    # Test Results Operations
    
    def save_test_result(self, request_id: int, assertion_id: int, passed: bool,
                        actual_value: Optional[str] = None, error_message: Optional[str] = None) -> int:
        """Save a test result."""
        from datetime import datetime
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO test_results (request_id, assertion_id, timestamp, passed, actual_value, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (request_id, assertion_id, datetime.now().isoformat(), 1 if passed else 0, actual_value, error_message))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_test_results(self, request_id: int, limit: int = 50) -> List[Dict]:
        """Get test results for a request."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT tr.*, ta.assertion_type, ta.field, ta.operator, ta.expected_value
            FROM test_results tr
            JOIN test_assertions ta ON tr.assertion_id = ta.id
            WHERE tr.request_id = ?
            ORDER BY tr.timestamp DESC
            LIMIT ?
        """, (request_id, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'request_id': row[1],
                'assertion_id': row[2],
                'timestamp': row[3],
                'passed': bool(row[4]),
                'actual_value': row[5],
                'error_message': row[6],
                'assertion_type': row[7],
                'field': row[8],
                'operator': row[9],
                'expected_value': row[10]
            })
        return results
    
    def get_latest_test_results(self, request_id: int) -> List[Dict]:
        """Get the latest test run results for a request."""
        cursor = self.connection.cursor()
        # Get the most recent timestamp
        cursor.execute("""
            SELECT MAX(timestamp) FROM test_results WHERE request_id = ?
        """, (request_id,))
        latest_timestamp = cursor.fetchone()[0]
        
        if not latest_timestamp:
            return []
        
        # Get all results from that timestamp
        cursor.execute("""
            SELECT tr.*, ta.assertion_type, ta.field, ta.operator, ta.expected_value
            FROM test_results tr
            JOIN test_assertions ta ON tr.assertion_id = ta.id
            WHERE tr.request_id = ? AND tr.timestamp = ?
            ORDER BY tr.id
        """, (request_id, latest_timestamp))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'request_id': row[1],
                'assertion_id': row[2],
                'timestamp': row[3],
                'passed': bool(row[4]),
                'actual_value': row[5],
                'error_message': row[6],
                'assertion_type': row[7],
                'field': row[8],
                'operator': row[9],
                'expected_value': row[10]
            })
        return results
    
    def clear_test_results(self, request_id: Optional[int] = None):
        """Clear test results."""
        cursor = self.connection.cursor()
        if request_id:
            cursor.execute("DELETE FROM test_results WHERE request_id = ?", (request_id,))
        else:
            cursor.execute("DELETE FROM test_results")
        self.connection.commit()
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()

