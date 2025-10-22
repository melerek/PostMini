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
        
        # Add description column to requests table if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN description TEXT")
            self.connection.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
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
        
        # Create git workspaces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS git_workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL UNIQUE,
                workspace_name TEXT,
                enabled INTEGER DEFAULT 1,
                auto_sync INTEGER DEFAULT 1,
                last_sync_timestamp TEXT,
                sync_status TEXT DEFAULT 'synced',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create folders table for organizing requests within collections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                parent_id INTEGER,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES folders(id) ON DELETE CASCADE
            )
        """)
        
        # Create collection variables table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                description TEXT,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
                UNIQUE(collection_id, key)
            )
        """)
        
        # Add folder_id column to requests table if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL")
            self.connection.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
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
    
    def create_request(self, name: str, url: str, method: str, collection_id: int,
                      params: Optional[Dict] = None, headers: Optional[Dict] = None,
                      body: Optional[str] = None, auth_type: str = 'None',
                      auth_token: Optional[str] = None, description: Optional[str] = None,
                      folder_id: Optional[int] = None) -> int:
        """
        Create a new request in a collection.
        
        Args:
            name: Name of the request
            url: Request URL
            method: HTTP method (GET, POST, etc.)
            collection_id: ID of the parent collection
            params: Query parameters as dictionary
            headers: Request headers as dictionary
            body: Request body (usually JSON string)
            auth_type: Type of authentication ('None', 'Bearer Token')
            auth_token: Authentication token
            description: Optional description/notes for the request
            folder_id: Optional ID of the parent folder
            
        Returns:
            ID of the newly created request
        """
        cursor = self.connection.cursor()
        
        # Convert dictionaries to JSON strings
        params_json = json.dumps(params) if params else None
        headers_json = json.dumps(headers) if headers else None
        
        cursor.execute("""
            INSERT INTO requests 
            (collection_id, name, method, url, params, headers, body, auth_type, auth_token, description, folder_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (collection_id, name, method, url, params_json, headers_json, 
              body, auth_type, auth_token, description, folder_id))
        
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
                      auth_token: Optional[str] = None, description: Optional[str] = None):
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
            description: Optional description/notes for the request
        """
        cursor = self.connection.cursor()
        
        # Convert dictionaries to JSON strings
        params_json = json.dumps(params) if params else None
        headers_json = json.dumps(headers) if headers else None
        
        cursor.execute("""
            UPDATE requests 
            SET name = ?, method = ?, url = ?, params = ?, headers = ?, 
                body = ?, auth_type = ?, auth_token = ?, description = ?
            WHERE id = ?
        """, (name, method, url, params_json, headers_json, body, 
              auth_type, auth_token, description, request_id))
        
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
    
    # ==================== Git Workspace Operations ====================
    
    def create_git_workspace(self, project_path: str, workspace_name: Optional[str] = None,
                            enabled: bool = True, auto_sync: bool = True) -> int:
        """Create a new Git workspace configuration."""
        from datetime import datetime
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO git_workspaces (project_path, workspace_name, enabled, auto_sync,
                                       created_at, updated_at, sync_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_path, workspace_name, 1 if enabled else 0, 1 if auto_sync else 0,
              now, now, 'synced'))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_git_workspace_by_path(self, project_path: str) -> Optional[Dict]:
        """Get Git workspace by project path."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM git_workspaces WHERE project_path = ?", (project_path,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'project_path': row[1],
                'workspace_name': row[2],
                'enabled': bool(row[3]),
                'auto_sync': bool(row[4]),
                'last_sync_timestamp': row[5],
                'sync_status': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            }
        return None
    
    def get_all_git_workspaces(self) -> List[Dict]:
        """Get all Git workspaces."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM git_workspaces ORDER BY updated_at DESC")
        workspaces = []
        for row in cursor.fetchall():
            workspaces.append({
                'id': row[0],
                'project_path': row[1],
                'workspace_name': row[2],
                'enabled': bool(row[3]),
                'auto_sync': bool(row[4]),
                'last_sync_timestamp': row[5],
                'sync_status': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            })
        return workspaces
    
    def update_git_workspace(self, workspace_id: int, workspace_name: Optional[str] = None,
                           enabled: Optional[bool] = None, auto_sync: Optional[bool] = None,
                           sync_status: Optional[str] = None):
        """Update Git workspace configuration."""
        from datetime import datetime
        cursor = self.connection.cursor()
        
        # Build update query dynamically
        updates = []
        params = []
        
        if workspace_name is not None:
            updates.append("workspace_name = ?")
            params.append(workspace_name)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if auto_sync is not None:
            updates.append("auto_sync = ?")
            params.append(1 if auto_sync else 0)
        if sync_status is not None:
            updates.append("sync_status = ?")
            params.append(sync_status)
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        params.append(workspace_id)
        
        query = f"UPDATE git_workspaces SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        self.connection.commit()
    
    def update_git_workspace_sync_timestamp(self, workspace_id: int):
        """Update last sync timestamp for a workspace."""
        from datetime import datetime
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE git_workspaces SET last_sync_timestamp = ?, updated_at = ?
            WHERE id = ?
        """, (now, now, workspace_id))
        self.connection.commit()
    
    def delete_git_workspace(self, workspace_id: int):
        """Delete a Git workspace configuration."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM git_workspaces WHERE id = ?", (workspace_id,))
        self.connection.commit()
    
    # ==================== Folder Operations ====================
    
    def create_folder(self, collection_id: int, name: str, parent_id: Optional[int] = None) -> int:
        """
        Create a new folder within a collection.
        
        Args:
            collection_id: ID of the collection
            name: Name of the folder
            parent_id: ID of the parent folder (for nesting), or None for root level
            
        Returns:
            ID of the newly created folder
        """
        from datetime import datetime
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO folders (collection_id, parent_id, name, created_at)
            VALUES (?, ?, ?, ?)
        """, (collection_id, parent_id, name, now))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_folders_by_collection(self, collection_id: int) -> List[Dict]:
        """
        Get all folders in a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            List of folder dictionaries
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, collection_id, parent_id, name, created_at
            FROM folders
            WHERE collection_id = ?
            ORDER BY name
        """, (collection_id,))
        
        folders = []
        for row in cursor.fetchall():
            folders.append({
                'id': row[0],
                'collection_id': row[1],
                'parent_id': row[2],
                'name': row[3],
                'created_at': row[4]
            })
        return folders
    
    def get_folder(self, folder_id: int) -> Optional[Dict]:
        """
        Get a folder by ID.
        
        Args:
            folder_id: ID of the folder
            
        Returns:
            Folder dictionary or None if not found
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, collection_id, parent_id, name, created_at
            FROM folders
            WHERE id = ?
        """, (folder_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'collection_id': row[1],
                'parent_id': row[2],
                'name': row[3],
                'created_at': row[4]
            }
        return None
    
    def update_folder(self, folder_id: int, name: Optional[str] = None, parent_id: Optional[int] = None):
        """
        Update a folder's name or parent.
        
        Args:
            folder_id: ID of the folder to update
            name: New name (if changing)
            parent_id: New parent ID (if moving), use -1 to set to None (root level)
        """
        cursor = self.connection.cursor()
        
        if name is not None:
            cursor.execute("UPDATE folders SET name = ? WHERE id = ?", (name, folder_id))
        
        if parent_id is not None:
            # Allow -1 to explicitly set parent_id to NULL (move to root)
            actual_parent_id = None if parent_id == -1 else parent_id
            cursor.execute("UPDATE folders SET parent_id = ? WHERE id = ?", (actual_parent_id, folder_id))
        
        self.connection.commit()
    
    def delete_folder(self, folder_id: int):
        """
        Delete a folder. Child folders and requests will be handled by CASCADE.
        
        Args:
            folder_id: ID of the folder to delete
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        self.connection.commit()
    
    def move_request_to_folder(self, request_id: int, folder_id: Optional[int]):
        """
        Move a request to a folder (or to collection root if folder_id is None).
        
        Args:
            request_id: ID of the request to move
            folder_id: ID of the destination folder, or None for collection root
        """
        cursor = self.connection.cursor()
        cursor.execute("UPDATE requests SET folder_id = ? WHERE id = ?", (folder_id, request_id))
        self.connection.commit()
    
    def get_requests_by_folder(self, folder_id: Optional[int], collection_id: int) -> List[Dict]:
        """
        Get all requests in a folder (or in collection root if folder_id is None).
        
        Args:
            folder_id: ID of the folder, or None for collection root
            collection_id: ID of the collection
            
        Returns:
            List of request dictionaries
        """
        cursor = self.connection.cursor()
        
        if folder_id is None:
            # Get requests at collection root (no folder)
            cursor.execute("""
                SELECT id, collection_id, folder_id, name, method, url, params, 
                       headers, body, auth_type, auth_token, description
                FROM requests
                WHERE collection_id = ? AND folder_id IS NULL
                ORDER BY name
            """, (collection_id,))
        else:
            # Get requests in specific folder
            cursor.execute("""
                SELECT id, collection_id, folder_id, name, method, url, params, 
                       headers, body, auth_type, auth_token, description
                FROM requests
                WHERE folder_id = ?
                ORDER BY name
            """, (folder_id,))
        
        requests = []
        for row in cursor.fetchall():
            requests.append({
                'id': row[0],
                'collection_id': row[1],
                'folder_id': row[2],
                'name': row[3],
                'method': row[4],
                'url': row[5],
                'params': json.loads(row[6]) if row[6] else {},
                'headers': json.loads(row[7]) if row[7] else {},
                'body': row[8] or '',
                'auth_type': row[9] or 'None',
                'auth_token': row[10] or '',
                'description': row[11] or ''
            })
        return requests
    
    # ==================== Collection Variables Operations ====================
    
    def create_collection_variable(self, collection_id: int, key: str, value: str, description: str = "") -> int:
        """
        Create or update a collection variable.
        
        Args:
            collection_id: ID of the collection
            key: Variable key/name
            value: Variable value
            description: Optional description
            
        Returns:
            ID of the variable
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO collection_variables (collection_id, key, value, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(collection_id, key) DO UPDATE SET
                value = excluded.value,
                description = excluded.description
        """, (collection_id, key, value, description))
        self.connection.commit()
        return cursor.lastrowid
    
    def get_collection_variables(self, collection_id: int) -> Dict[str, str]:
        """
        Get all variables for a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            Dictionary of key-value pairs
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT key, value
            FROM collection_variables
            WHERE collection_id = ?
            ORDER BY key
        """, (collection_id,))
        
        variables = {}
        for row in cursor.fetchall():
            variables[row[0]] = row[1]
        return variables
    
    def get_collection_variables_with_metadata(self, collection_id: int) -> List[Dict]:
        """
        Get all variables for a collection with full metadata.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            List of variable dictionaries with id, key, value, and description
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, key, value, description
            FROM collection_variables
            WHERE collection_id = ?
            ORDER BY key
        """, (collection_id,))
        
        variables = []
        for row in cursor.fetchall():
            variables.append({
                'id': row[0],
                'key': row[1],
                'value': row[2],
                'description': row[3] or ''
            })
        return variables
    
    def update_collection_variable(self, variable_id: int, key: Optional[str] = None, 
                                  value: Optional[str] = None, description: Optional[str] = None):
        """
        Update a collection variable.
        
        Args:
            variable_id: ID of the variable to update
            key: New key (if changing)
            value: New value (if changing)
            description: New description (if changing)
        """
        cursor = self.connection.cursor()
        
        updates = []
        params = []
        
        if key is not None:
            updates.append("key = ?")
            params.append(key)
        if value is not None:
            updates.append("value = ?")
            params.append(value)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if updates:
            params.append(variable_id)
            query = f"UPDATE collection_variables SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            self.connection.commit()
    
    def delete_collection_variable(self, variable_id: int):
        """
        Delete a collection variable.
        
        Args:
            variable_id: ID of the variable to delete
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM collection_variables WHERE id = ?", (variable_id,))
        self.connection.commit()
    
    def delete_collection_variables_by_collection(self, collection_id: int):
        """
        Delete all variables for a collection.
        
        Args:
            collection_id: ID of the collection
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM collection_variables WHERE collection_id = ?", (collection_id,))
        self.connection.commit()
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()

