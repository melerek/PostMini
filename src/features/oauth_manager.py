"""
OAuth 2.0 Manager

This module handles OAuth 2.0 authentication flows including:
- Authorization Code Flow
- Client Credentials Flow
- Password Grant Flow (Resource Owner Password Credentials)
- Implicit Flow (legacy but supported)
"""

import requests
import secrets
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    
    auth_code = None
    state = None
    error = None
    
    def do_GET(self):
        """Handle GET request from OAuth provider callback."""
        # Parse query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        # Store authorization code and state
        OAuthCallbackHandler.auth_code = params.get('code', [None])[0]
        OAuthCallbackHandler.state = params.get('state', [None])[0]
        OAuthCallbackHandler.error = params.get('error', [None])[0]
        
        # Send response to browser
        if OAuthCallbackHandler.error:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <html>
            <head><title>OAuth Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #f44336;">❌ Authorization Failed</h1>
                <p>Error: {OAuthCallbackHandler.error}</p>
                <p>You can close this window.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>OAuth Success</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #4CAF50;">✅ Authorization Successful</h1>
                <p>You can close this window and return to the application.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress HTTP server log messages."""
        pass


class OAuthManager:
    """
    Manages OAuth 2.0 authentication flows.
    """
    
    # OAuth 2.0 Flow Types
    FLOW_AUTHORIZATION_CODE = "authorization_code"
    FLOW_CLIENT_CREDENTIALS = "client_credentials"
    FLOW_PASSWORD = "password"
    FLOW_IMPLICIT = "implicit"
    
    def __init__(self):
        """Initialize OAuth manager."""
        self.callback_server = None
        self.callback_thread = None
    
    # ==================== Authorization Code Flow ====================
    
    def start_authorization_code_flow(self, auth_url: str, client_id: str,
                                     redirect_uri: str, scope: Optional[str] = None,
                                     state: Optional[str] = None,
                                     additional_params: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Start Authorization Code Flow.
        
        Args:
            auth_url: Authorization endpoint URL
            client_id: Client ID
            redirect_uri: Redirect URI
            scope: OAuth scopes (space-separated)
            state: State parameter for CSRF protection
            additional_params: Additional query parameters
            
        Returns:
            Tuple of (authorization_url, state)
        """
        # Generate state if not provided
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'state': state
        }
        
        if scope:
            params['scope'] = scope
        
        if additional_params:
            params.update(additional_params)
        
        auth_url_with_params = f"{auth_url}?{urlencode(params)}"
        
        return auth_url_with_params, state
    
    def exchange_code_for_token(self, token_url: str, code: str, client_id: str,
                                client_secret: str, redirect_uri: str,
                                additional_params: Optional[Dict] = None) -> Dict:
        """
        Exchange authorization code for access token.
        
        Args:
            token_url: Token endpoint URL
            code: Authorization code
            client_id: Client ID
            client_secret: Client secret
            redirect_uri: Redirect URI (must match the one used in authorization)
            additional_params: Additional form parameters
            
        Returns:
            Token response dictionary
            
        Raises:
            requests.HTTPError: If token exchange fails
        """
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri
        }
        
        if additional_params:
            data.update(additional_params)
        
        response = requests.post(
            token_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        
        return response.json()
    
    def start_local_callback_server(self, port: int = 8080) -> str:
        """
        Start a local HTTP server to receive OAuth callback.
        
        Args:
            port: Port number (default: 8080)
            
        Returns:
            Redirect URI for the local server
        """
        # Reset callback handler state
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.state = None
        OAuthCallbackHandler.error = None
        
        # Create and start server
        self.callback_server = HTTPServer(('localhost', port), OAuthCallbackHandler)
        
        # Run server in a separate thread
        self.callback_thread = threading.Thread(target=self._run_callback_server)
        self.callback_thread.daemon = True
        self.callback_thread.start()
        
        return f"http://localhost:{port}"
    
    def _run_callback_server(self):
        """Run the callback server (internal method)."""
        if self.callback_server:
            self.callback_server.handle_request()  # Handle one request then stop
    
    def wait_for_callback(self, timeout: int = 300) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Wait for OAuth callback.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            Tuple of (code, state, error)
        """
        if self.callback_thread:
            self.callback_thread.join(timeout)
        
        return (
            OAuthCallbackHandler.auth_code,
            OAuthCallbackHandler.state,
            OAuthCallbackHandler.error
        )
    
    def stop_callback_server(self):
        """Stop the callback server."""
        if self.callback_server:
            try:
                self.callback_server.shutdown()
                self.callback_server = None
            except Exception as e:
                # Server may already be stopped, ignore errors
                print(f"Warning: Error stopping callback server: {e}")
    
    # ==================== Client Credentials Flow ====================
    
    def get_client_credentials_token(self, token_url: str, client_id: str,
                                    client_secret: str, scope: Optional[str] = None,
                                    additional_params: Optional[Dict] = None) -> Dict:
        """
        Get access token using Client Credentials Flow.
        
        Args:
            token_url: Token endpoint URL
            client_id: Client ID
            client_secret: Client secret
            scope: OAuth scopes (space-separated)
            additional_params: Additional form parameters
            
        Returns:
            Token response dictionary
            
        Raises:
            requests.HTTPError: If token request fails
        """
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        if scope:
            data['scope'] = scope
        
        if additional_params:
            data.update(additional_params)
        
        response = requests.post(
            token_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        
        return response.json()
    
    # ==================== Password Grant Flow ====================
    
    def get_password_grant_token(self, token_url: str, client_id: str,
                                 client_secret: str, username: str, password: str,
                                 scope: Optional[str] = None,
                                 additional_params: Optional[Dict] = None) -> Dict:
        """
        Get access token using Resource Owner Password Credentials Flow.
        
        Args:
            token_url: Token endpoint URL
            client_id: Client ID
            client_secret: Client secret
            username: Resource owner username
            password: Resource owner password
            scope: OAuth scopes (space-separated)
            additional_params: Additional form parameters
            
        Returns:
            Token response dictionary
            
        Raises:
            requests.HTTPError: If token request fails
        """
        data = {
            'grant_type': 'password',
            'client_id': client_id,
            'client_secret': client_secret,
            'username': username,
            'password': password
        }
        
        if scope:
            data['scope'] = scope
        
        if additional_params:
            data.update(additional_params)
        
        response = requests.post(
            token_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        
        return response.json()
    
    # ==================== Token Refresh ====================
    
    def refresh_access_token(self, token_url: str, refresh_token: str,
                            client_id: str, client_secret: str,
                            scope: Optional[str] = None,
                            additional_params: Optional[Dict] = None) -> Dict:
        """
        Refresh an access token using a refresh token.
        
        Args:
            token_url: Token endpoint URL
            refresh_token: Refresh token
            client_id: Client ID
            client_secret: Client secret
            scope: OAuth scopes (space-separated)
            additional_params: Additional form parameters
            
        Returns:
            Token response dictionary
            
        Raises:
            requests.HTTPError: If token refresh fails
        """
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        if scope:
            data['scope'] = scope
        
        if additional_params:
            data.update(additional_params)
        
        response = requests.post(
            token_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        
        return response.json()
    
    # ==================== Token Utilities ====================
    
    @staticmethod
    def is_token_expired(expires_at: Optional[str]) -> bool:
        """
        Check if a token has expired.
        
        Args:
            expires_at: ISO format expiration datetime string
            
        Returns:
            True if expired, False otherwise
        """
        if not expires_at:
            return False
        
        try:
            expiry_time = datetime.fromisoformat(expires_at)
            # Add 60 second buffer to avoid edge cases
            return datetime.now() >= (expiry_time - timedelta(seconds=60))
        except (ValueError, TypeError) as e:
            # Invalid date format
            return False
    
    @staticmethod
    def calculate_expiry_time(expires_in: int) -> str:
        """
        Calculate token expiry time.
        
        Args:
            expires_in: Seconds until expiration
            
        Returns:
            ISO format datetime string
        """
        expiry_time = datetime.now() + timedelta(seconds=expires_in)
        return expiry_time.isoformat()
    
    @staticmethod
    def format_token_for_header(token: str, token_type: str = "Bearer") -> str:
        """
        Format token for Authorization header.
        
        Args:
            token: Access token
            token_type: Token type (default: Bearer)
            
        Returns:
            Formatted authorization header value
        """
        return f"{token_type} {token}"
    
    # ==================== Helper Methods ====================
    
    def open_browser(self, url: str):
        """
        Open URL in default browser.
        
        Args:
            url: URL to open
        """
        webbrowser.open(url)

