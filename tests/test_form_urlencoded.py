"""
Test form-urlencoded content type handling.

This test verifies that JSON body is correctly converted to URL-encoded format
when Content-Type is application/x-www-form-urlencoded.
"""

import pytest
import json
from src.core.api_client import ApiClient
from unittest.mock import Mock, patch


class TestFormUrlEncoded:
    """Test handling of application/x-www-form-urlencoded content type."""
    
    def test_json_body_converted_to_urlencoded(self):
        """Test that JSON body is converted to URL-encoded format."""
        client = ApiClient()
        
        # Prepare request data
        body_dict = {
            "grant_type": "password",
            "username": "admin@ecovadis.com",
            "password": "Password@123"
        }
        body_json = json.dumps(body_dict)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Mock the session.request method
        with patch.object(client.session, 'request') as mock_request:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'application/json'}
            mock_response.text = '{"access_token": "test_token"}'
            mock_response.content = b'{"access_token": "test_token"}'
            mock_request.return_value = mock_response
            
            # Execute request
            client.execute_request(
                method='POST',
                url='https://api.example.com/token',
                headers=headers,
                body=body_json
            )
            
            # Verify that request was called with URL-encoded data
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            
            # Check that data parameter is URL-encoded string
            assert 'data' in call_kwargs
            assert call_kwargs['data'] is not None
            assert 'grant_type=password' in call_kwargs['data']
            assert 'username=admin%40ecovadis.com' in call_kwargs['data']
            assert 'password=Password%40123' in call_kwargs['data']
            
            # Check that json parameter is None (not sending as JSON)
            assert call_kwargs.get('json') is None
    
    def test_already_urlencoded_body_passed_through(self):
        """Test that already URL-encoded body is passed through unchanged."""
        client = ApiClient()
        
        # Prepare already URL-encoded body
        body_urlencoded = "grant_type=password&username=test@example.com&password=pass123"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Mock the session.request method
        with patch.object(client.session, 'request') as mock_request:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'application/json'}
            mock_response.text = '{"success": true}'
            mock_response.content = b'{"success": true}'
            mock_request.return_value = mock_response
            
            # Execute request
            client.execute_request(
                method='POST',
                url='https://api.example.com/token',
                headers=headers,
                body=body_urlencoded
            )
            
            # Verify that request was called with the same URL-encoded data
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            
            # Check that data parameter is the same URL-encoded string
            assert call_kwargs['data'] == body_urlencoded
    
    def test_json_content_type_still_sends_json(self):
        """Test that application/json content type still sends JSON correctly."""
        client = ApiClient()
        
        # Prepare request data
        body_dict = {"key": "value", "number": 123}
        body_json = json.dumps(body_dict)
        headers = {
            "Content-Type": "application/json"
        }
        
        # Mock the session.request method
        with patch.object(client.session, 'request') as mock_request:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'application/json'}
            mock_response.text = '{"success": true}'
            mock_response.content = b'{"success": true}'
            mock_request.return_value = mock_response
            
            # Execute request
            client.execute_request(
                method='POST',
                url='https://api.example.com/api',
                headers=headers,
                body=body_json
            )
            
            # Verify that request was called with JSON data
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            
            # Check that json parameter is set (proper JSON handling)
            assert 'json' in call_kwargs
            assert call_kwargs['json'] == body_dict
            
            # Check that data parameter is None
            assert call_kwargs.get('data') is None
    
    def test_no_content_type_with_json_body(self):
        """Test JSON body without Content-Type header (auto-detect JSON)."""
        client = ApiClient()
        
        # Prepare request data
        body_dict = {"test": "data"}
        body_json = json.dumps(body_dict)
        headers = {}  # No Content-Type header
        
        # Mock the session.request method
        with patch.object(client.session, 'request') as mock_request:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = 'OK'
            mock_response.content = b'OK'
            mock_request.return_value = mock_response
            
            # Execute request
            client.execute_request(
                method='POST',
                url='https://api.example.com/api',
                headers=headers,
                body=body_json
            )
            
            # Verify that request was called with JSON data (auto-detected)
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            
            # Should auto-detect as JSON
            assert call_kwargs.get('json') == body_dict
            assert call_kwargs.get('data') is None
