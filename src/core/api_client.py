"""
API Client Module

This module handles all HTTP request operations using the requests library.
It provides a clean interface for executing various HTTP methods with
support for headers, parameters, body, and authentication.
"""

import requests
from typing import Dict, Optional, Tuple
import time


class ApiResponse:
    """
    Wrapper class for HTTP responses with additional metadata.
    """
    
    def __init__(self, response: requests.Response, elapsed_time: float):
        """
        Initialize the API response wrapper.
        
        Args:
            response: The requests.Response object
            elapsed_time: Time taken for the request in seconds
        """
        self.response = response
        self.elapsed_time = elapsed_time
        self.status_code = response.status_code
        self.headers = dict(response.headers)
        self.text = response.text
        self.size = len(response.content)
    
    def json(self):
        """
        Parse response as JSON.
        
        Returns:
            Parsed JSON object
            
        Raises:
            ValueError: If response is not valid JSON
        """
        return self.response.json()
    
    def is_json(self) -> bool:
        """
        Check if the response content type is JSON.
        
        Returns:
            True if response is JSON, False otherwise
        """
        content_type = self.headers.get('Content-Type', '')
        return 'application/json' in content_type.lower()


class ApiClient:
    """
    HTTP client for making API requests with support for various methods,
    authentication, headers, and body content.
    """
    
    def __init__(self, timeout: int = 30, verify_ssl: bool = True):
        """
        Initialize the API client.
        
        Args:
            timeout: Default timeout for requests in seconds
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
    
    def execute_request(self, 
                       method: str,
                       url: str,
                       params: Optional[Dict] = None,
                       headers: Optional[Dict] = None,
                       body: Optional[str] = None,
                       auth_type: str = 'None',
                       auth_token: Optional[str] = None) -> ApiResponse:
        """
        Execute an HTTP request with the specified parameters.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
            url: Target URL
            params: Query parameters as dictionary
            headers: Request headers as dictionary
            body: Request body (usually JSON string)
            auth_type: Authentication type ('None', 'Bearer Token')
            auth_token: Authentication token value
            
        Returns:
            ApiResponse object containing the response and metadata
            
        Raises:
            requests.exceptions.RequestException: For network/HTTP errors
            requests.exceptions.Timeout: For timeout errors
            requests.exceptions.ConnectionError: For connection errors
        """
        # Prepare headers
        request_headers = headers.copy() if headers else {}
        
        # Add authentication if specified
        if auth_type == 'Bearer Token' and auth_token:
            request_headers['Authorization'] = f'Bearer {auth_token}'
        
        # Prepare request data
        data = None
        json_data = None
        
        # If body is provided, try to parse as JSON, otherwise send as raw data
        if body:
            # Check if Content-Type suggests JSON
            content_type = request_headers.get('Content-Type', '')
            if 'application/json' in content_type.lower() or self._is_json(body):
                try:
                    import json
                    json_data = json.loads(body)
                except (json.JSONDecodeError, ValueError):
                    # If JSON parsing fails, send as raw data
                    data = body
            else:
                data = body
        
        # Record start time
        start_time = time.time()
        
        # Execute the request
        try:
            # Suppress InsecureRequestWarning if SSL verification is disabled
            if not self.verify_ssl:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                headers=request_headers,
                data=data,
                json=json_data,
                timeout=self.timeout,
                verify=self.verify_ssl,
                allow_redirects=True
            )
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Return wrapped response
            return ApiResponse(response, elapsed_time)
            
        except requests.exceptions.Timeout as e:
            raise requests.exceptions.Timeout(
                f"Request timed out after {self.timeout} seconds"
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise requests.exceptions.ConnectionError(
                f"Failed to connect to {url}"
            ) from e
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Request failed: {str(e)}"
            ) from e
    
    def _is_json(self, text: str) -> bool:
        """
        Check if a string is valid JSON.
        
        Args:
            text: String to check
            
        Returns:
            True if valid JSON, False otherwise
        """
        try:
            import json
            json.loads(text)
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    def get(self, url: str, **kwargs) -> ApiResponse:
        """
        Execute a GET request.
        
        Args:
            url: Target URL
            **kwargs: Additional arguments passed to execute_request
            
        Returns:
            ApiResponse object
        """
        return self.execute_request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> ApiResponse:
        """
        Execute a POST request.
        
        Args:
            url: Target URL
            **kwargs: Additional arguments passed to execute_request
            
        Returns:
            ApiResponse object
        """
        return self.execute_request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> ApiResponse:
        """
        Execute a PUT request.
        
        Args:
            url: Target URL
            **kwargs: Additional arguments passed to execute_request
            
        Returns:
            ApiResponse object
        """
        return self.execute_request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> ApiResponse:
        """
        Execute a DELETE request.
        
        Args:
            url: Target URL
            **kwargs: Additional arguments passed to execute_request
            
        Returns:
            ApiResponse object
        """
        return self.execute_request('DELETE', url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> ApiResponse:
        """
        Execute a PATCH request.
        
        Args:
            url: Target URL
            **kwargs: Additional arguments passed to execute_request
            
        Returns:
            ApiResponse object
        """
        return self.execute_request('PATCH', url, **kwargs)
    
    # ============= Cookie Management Methods =============
    
    def get_cookies(self, domain: str = None):
        """
        Get cookies from the session.
        
        Args:
            domain: Filter cookies by domain (None = all cookies)
            
        Returns:
            List of cookie dictionaries with keys: domain, name, value, path, expires, secure, httponly, samesite
        """
        from http.cookiejar import Cookie
        cookies = []
        
        for cookie in self.session.cookies:
            # Filter by domain if specified
            if domain and not (cookie.domain == domain or cookie.domain == f".{domain}" or domain.endswith(cookie.domain.lstrip('.'))):
                continue
            
            cookie_dict = {
                'domain': cookie.domain,
                'name': cookie.name,
                'value': cookie.value,
                'path': cookie.path or '/',
                'expires': cookie.expires,  # Unix timestamp or None
                'secure': cookie.secure,
                'httponly': cookie.has_nonstandard_attr('HttpOnly') or False,
                'samesite': cookie.get_nonstandard_attr('SameSite', None)
            }
            cookies.append(cookie_dict)
        
        return cookies
    
    def set_cookie(self, domain: str, name: str, value: str, path: str = '/', 
                   expires: int = None, secure: bool = False, httponly: bool = False,
                   samesite: str = None):
        """
        Manually add a cookie to the session.
        
        Args:
            domain: Cookie domain
            name: Cookie name
            value: Cookie value
            path: Cookie path (default: '/')
            expires: Expiration timestamp (None = session cookie)
            secure: Secure flag
            httponly: HttpOnly flag
            samesite: SameSite attribute ('Strict', 'Lax', 'None', or None)
        """
        from http.cookiejar import Cookie
        
        cookie = Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=True,
            domain_initial_dot=domain.startswith('.'),
            path=path,
            path_specified=True,
            secure=secure,
            expires=expires,
            discard=expires is None,
            comment=None,
            comment_url=None,
            rest={'HttpOnly': httponly, 'SameSite': samesite} if (httponly or samesite) else {},
            rfc2109=False
        )
        
        self.session.cookies.set_cookie(cookie)
    
    def clear_cookies(self, domain: str = None):
        """
        Clear cookies from the session.
        
        Args:
            domain: Clear cookies for specific domain (None = clear all)
        """
        if domain:
            # Clear cookies for specific domain
            self.session.cookies.clear(domain=domain)
        else:
            # Clear all cookies
            self.session.cookies.clear()
    
    def load_cookies_from_db(self, db_manager):
        """
        Load cookies from database into session.
        
        Args:
            db_manager: DatabaseManager instance
        """
        cookies = db_manager.get_all_cookies()
        
        for cookie_row in cookies:
            # Convert Row to dict
            cookie = dict(cookie_row) if cookie_row else {}
            if not cookie:
                continue
            
            # Skip expired cookies
            if cookie.get('expires') is not None:
                import time
                if cookie['expires'] < time.time():
                    continue
            
            self.set_cookie(
                domain=cookie.get('domain', ''),
                name=cookie.get('name', ''),
                value=cookie.get('value', ''),
                path=cookie.get('path') or '/',
                expires=cookie.get('expires'),
                secure=bool(cookie.get('secure', 0)),
                httponly=bool(cookie.get('http_only', 0)),
                samesite=cookie.get('same_site')
            )
    
    def save_cookies_to_db(self, db_manager):
        """
        Save current session cookies to database.
        
        Args:
            db_manager: DatabaseManager instance
        """
        cookies = self.get_cookies()
        
        for cookie in cookies:
            db_manager.create_cookie(
                domain=cookie['domain'],
                name=cookie['name'],
                value=cookie['value'],
                path=cookie['path'],
                expires=cookie['expires'],
                secure=cookie['secure'],
                http_only=cookie['httponly'],
                same_site=cookie['samesite']
            )
    
    def close(self):
        """Close the session and clean up resources."""
        self.session.close()

