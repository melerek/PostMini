"""
cURL Converter Module

This module handles conversion between cURL commands and PostMini request format.
Supports importing cURL commands and exporting requests as cURL.
"""

import re
import json
import shlex
from typing import Dict, List, Tuple, Optional


class CurlConverter:
    """
    Converts between cURL commands and PostMini request format.
    """
    
    @staticmethod
    def curl_to_request(curl_command: str) -> Dict:
        """
        Parse a cURL command and convert it to PostMini request format.
        
        Args:
            curl_command: cURL command string
            
        Returns:
            Dictionary with request details (method, url, headers, body, params)
            
        Raises:
            ValueError: If cURL command is invalid
        """
        # Remove 'curl' prefix and clean up
        curl_command = curl_command.strip()
        if curl_command.lower().startswith('curl'):
            curl_command = curl_command[4:].strip()
        
        # Handle line continuations (backslash)
        curl_command = curl_command.replace('\\\n', ' ').replace('\\\r\n', ' ')
        
        # Parse command using shlex to handle quotes properly
        try:
            parts = shlex.split(curl_command)
        except ValueError as e:
            raise ValueError(f"Invalid cURL command: {str(e)}")
        
        if not parts:
            raise ValueError("Empty cURL command")
        
        # Initialize request data
        method = "GET"
        url = None
        headers = {}
        body = None
        params = {}
        
        # Parse arguments
        i = 0
        while i < len(parts):
            arg = parts[i]
            
            # Method (-X or --request)
            if arg in ['-X', '--request']:
                if i + 1 < len(parts):
                    method = parts[i + 1].upper()
                    i += 2
                    continue
                    
            # Headers (-H or --header)
            elif arg in ['-H', '--header']:
                if i + 1 < len(parts):
                    header_line = parts[i + 1]
                    if ':' in header_line:
                        key, value = header_line.split(':', 1)
                        headers[key.strip()] = value.strip()
                    i += 2
                    continue
                    
            # Data (-d, --data, --data-raw, --data-binary)
            elif arg in ['-d', '--data', '--data-raw', '--data-binary', '--data-urlencode']:
                if i + 1 < len(parts):
                    body = parts[i + 1]
                    # Auto-set method to POST if not explicitly set
                    if method == "GET":
                        method = "POST"
                    i += 2
                    continue
                    
            # JSON data (--json)
            elif arg == '--json':
                if i + 1 < len(parts):
                    body = parts[i + 1]
                    headers['Content-Type'] = 'application/json'
                    if method == "GET":
                        method = "POST"
                    i += 2
                    continue
                    
            # User agent (-A or --user-agent)
            elif arg in ['-A', '--user-agent']:
                if i + 1 < len(parts):
                    headers['User-Agent'] = parts[i + 1]
                    i += 2
                    continue
                    
            # Referer (-e or --referer)
            elif arg in ['-e', '--referer']:
                if i + 1 < len(parts):
                    headers['Referer'] = parts[i + 1]
                    i += 2
                    continue
                    
            # Basic auth (-u or --user)
            elif arg in ['-u', '--user']:
                if i + 1 < len(parts):
                    auth = parts[i + 1]
                    # Will be handled separately as auth_type
                    headers['Authorization'] = f'Basic {auth}'
                    i += 2
                    continue
                    
            # Compressed (--compressed)
            elif arg == '--compressed':
                headers['Accept-Encoding'] = 'gzip, deflate, br'
                i += 1
                continue
                
            # Insecure (-k or --insecure) - just skip
            elif arg in ['-k', '--insecure']:
                i += 1
                continue
                
            # Location follow (-L or --location) - just skip
            elif arg in ['-L', '--location']:
                i += 1
                continue
                
            # Silent/progress (-s, -S, --silent, --show-error) - skip
            elif arg in ['-s', '-S', '--silent', '--show-error', '--no-progress-meter']:
                i += 1
                continue
                
            # Output (-o or --output) - skip
            elif arg in ['-o', '--output']:
                i += 2  # Skip the filename too
                continue
                
            # If it doesn't start with -, assume it's the URL
            elif not arg.startswith('-'):
                url = arg
                i += 1
                continue
                
            else:
                # Unknown flag, skip it
                i += 1
                continue
        
        # Validate URL
        if not url:
            raise ValueError("No URL found in cURL command")
        
        # Extract query parameters from URL
        if '?' in url:
            base_url, query_string = url.split('?', 1)
            url = base_url
            # Parse query parameters
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
                else:
                    params[param] = ''
        
        return {
            'method': method,
            'url': url,
            'headers': headers,
            'body': body or '',
            'params': params
        }
    
    @staticmethod
    def request_to_curl(method: str, url: str, headers: Dict[str, str] = None,
                       body: str = None, params: Dict[str, str] = None) -> str:
        """
        Convert a PostMini request to cURL command.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Dictionary of headers
            body: Request body (optional)
            params: Query parameters (optional)
            
        Returns:
            cURL command string
        """
        parts = ['curl']
        
        # Add method if not GET
        if method.upper() != 'GET':
            parts.append(f'-X {method.upper()}')
        
        # Build URL with query parameters
        full_url = url
        if params:
            param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
            full_url = f'{url}?{param_str}'
        
        # Quote URL
        parts.append(f"'{full_url}'")
        
        # Add headers
        if headers:
            for key, value in headers.items():
                # Escape single quotes in header values
                escaped_value = value.replace("'", "'\\''")
                parts.append(f"-H '{key}: {escaped_value}'")
        
        # Add body
        if body:
            # Escape single quotes in body
            escaped_body = body.replace("'", "'\\''")
            parts.append(f"-d '{escaped_body}'")
        
        # Join with line continuations for readability
        return ' \\\n  '.join(parts)
    
    @staticmethod
    def is_valid_curl(curl_command: str) -> bool:
        """
        Check if a string appears to be a valid cURL command.
        
        Args:
            curl_command: String to check
            
        Returns:
            True if it looks like a valid cURL command
        """
        curl_command = curl_command.strip().lower()
        return curl_command.startswith('curl') and len(curl_command) > 5


# Convenience functions
def import_curl(curl_command: str) -> Dict:
    """Import a cURL command and return request data."""
    return CurlConverter.curl_to_request(curl_command)


def export_curl(method: str, url: str, headers: Dict = None, 
                body: str = None, params: Dict = None) -> str:
    """Export request data as a cURL command."""
    return CurlConverter.request_to_curl(method, url, headers, body, params)

