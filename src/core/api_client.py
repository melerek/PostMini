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
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            timeout: Default timeout for requests in seconds
        """
        self.timeout = timeout
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
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                headers=request_headers,
                data=data,
                json=json_data,
                timeout=self.timeout,
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
    
    def close(self):
        """Close the session and clean up resources."""
        self.session.close()

