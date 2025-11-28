"""
Test comprehensive body type support (Postman compatibility).

This test verifies that PostMini properly handles all Postman body types:
- none: No body
- raw: Text/JSON/XML/HTML etc
- formdata: multipart/form-data (file uploads)
- urlencoded: application/x-www-form-urlencoded  
- binary: Binary file upload
- graphql: GraphQL queries
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.core.api_client import ApiClient
from src.features.postman_converter import PostmanConverter


class TestBodyTypeSupport:
    """Test handling of all Postman body types."""
    
    def test_formdata_body_type_handling(self):
        """Test multipart/form-data body type."""
        client = ApiClient()
        
        # Prepare form-data body (stored as JSON internally)
        body_dict = {
            "username": "testuser",
            "email": "test@example.com",
            "age": "25"
        }
        body_json = json.dumps(body_dict)
        headers = {
            "Content-Type": "multipart/form-data"
        }
        
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = 'OK'
            mock_response.content = b'OK'
            mock_request.return_value = mock_response
            
            client.execute_request(
                method='POST',
                url='https://api.example.com/users',
                headers=headers,
                body=body_json
            )
            
            call_kwargs = mock_request.call_args[1]
            
            # Should send as data dict (not JSON)
            assert call_kwargs.get('data') == body_dict
            assert call_kwargs.get('json') is None
            # Content-Type should be removed (requests sets it with boundary)
            assert 'Content-Type' not in call_kwargs['headers']
    
    def test_urlencoded_body_type_handling(self):
        """Test application/x-www-form-urlencoded body type."""
        client = ApiClient()
        
        body_dict = {
            "grant_type": "password",
            "username": "admin@test.com",
            "password": "secret123"
        }
        body_json = json.dumps(body_dict)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = 'OK'
            mock_response.content = b'OK'
            mock_request.return_value = mock_response
            
            client.execute_request(
                method='POST',
                url='https://api.example.com/token',
                headers=headers,
                body=body_json
            )
            
            call_kwargs = mock_request.call_args[1]
            
            # Should be URL-encoded string
            assert 'grant_type=password' in call_kwargs['data']
            assert 'username=admin%40test.com' in call_kwargs['data']
            assert call_kwargs.get('json') is None
    
    def test_raw_json_body_type_handling(self):
        """Test raw JSON body type."""
        client = ApiClient()
        
        body_dict = {"name": "Test", "value": 123}
        body_json = json.dumps(body_dict)
        headers = {
            "Content-Type": "application/json"
        }
        
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = 'OK'
            mock_response.content = b'OK'
            mock_request.return_value = mock_response
            
            client.execute_request(
                method='POST',
                url='https://api.example.com/api',
                headers=headers,
                body=body_json
            )
            
            call_kwargs = mock_request.call_args[1]
            
            # Should send as JSON
            assert call_kwargs.get('json') == body_dict
            assert call_kwargs.get('data') is None
    
    def test_postman_formdata_import(self):
        """Test importing Postman collection with formdata body."""
        postman_data = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Upload File",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/upload",
                        "body": {
                            "mode": "formdata",
                            "formdata": [
                                {"key": "file", "value": "test.txt", "type": "text"},
                                {"key": "description", "value": "Test file", "type": "text"}
                            ]
                        }
                    }
                }
            ]
        }
        
        collection = PostmanConverter.from_postman_format(postman_data)
        request = collection['collection']['requests'][0]
        
        # Body should be stored as JSON dict
        body_dict = json.loads(request['body'])
        assert body_dict['file'] == 'test.txt'
        assert body_dict['description'] == 'Test file'
        
        # Body type should be preserved
        assert request['body_type'] == 'formdata'
        
        # Content-Type header should be set
        assert request['headers']['Content-Type'] == 'multipart/form-data'
    
    def test_postman_urlencoded_import(self):
        """Test importing Postman collection with urlencoded body."""
        postman_data = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Login",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/login",
                        "body": {
                            "mode": "urlencoded",
                            "urlencoded": [
                                {"key": "username", "value": "admin"},
                                {"key": "password", "value": "secret"}
                            ]
                        }
                    }
                }
            ]
        }
        
        collection = PostmanConverter.from_postman_format(postman_data)
        request = collection['collection']['requests'][0]
        
        # Body should be stored as JSON dict
        body_dict = json.loads(request['body'])
        assert body_dict['username'] == 'admin'
        assert body_dict['password'] == 'secret'
        
        # Body type should be preserved
        assert request['body_type'] == 'urlencoded'
        
        # Content-Type header should be set
        assert request['headers']['Content-Type'] == 'application/x-www-form-urlencoded'
    
    def test_postman_graphql_import(self):
        """Test importing Postman collection with GraphQL body."""
        postman_data = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "GraphQL Query",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/graphql",
                        "body": {
                            "mode": "graphql",
                            "graphql": {
                                "query": "{ users { id name } }",
                                "variables": "{}"
                            }
                        }
                    }
                }
            ]
        }
        
        collection = PostmanConverter.from_postman_format(postman_data)
        request = collection['collection']['requests'][0]
        
        # Body should be stored as JSON
        body_dict = json.loads(request['body'])
        assert 'query' in body_dict
        assert body_dict['query'] == '{ users { id name } }'
        
        # Body type should be preserved
        assert request['body_type'] == 'graphql'
    
    def test_postman_disabled_form_fields(self):
        """Test that disabled form fields are excluded."""
        postman_data = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Test Request",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/test",
                        "body": {
                            "mode": "formdata",
                            "formdata": [
                                {"key": "enabled_field", "value": "value1", "disabled": False},
                                {"key": "disabled_field", "value": "value2", "disabled": True}
                            ]
                        }
                    }
                }
            ]
        }
        
        collection = PostmanConverter.from_postman_format(postman_data)
        request = collection['collection']['requests'][0]
        
        body_dict = json.loads(request['body'])
        # Enabled field should be present
        assert 'enabled_field' in body_dict
        # Disabled field should NOT be present
        assert 'disabled_field' not in body_dict
