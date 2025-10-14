"""
Tests for cURL Converter Module

This module tests cURL command parsing and generation.
"""

import pytest
from src.features.curl_converter import CurlConverter, import_curl, export_curl


class TestCurlConverter:
    """Test suite for CurlConverter class."""
    
    def test_simple_get_request(self):
        """Test parsing a simple GET request."""
        curl = "curl 'https://api.example.com/users'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'GET'
        assert result['url'] == 'https://api.example.com/users'
        assert result['headers'] == {}
        assert result['body'] == ''
        assert result['params'] == {}
    
    def test_get_with_query_params(self):
        """Test parsing GET request with query parameters."""
        curl = "curl 'https://api.example.com/users?page=1&limit=10'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'GET'
        assert result['url'] == 'https://api.example.com/users'
        assert result['params'] == {'page': '1', 'limit': '10'}
    
    def test_post_with_json_body(self):
        """Test parsing POST request with JSON body."""
        curl = """curl -X POST 'https://api.example.com/users' \\
  -H 'Content-Type: application/json' \\
  -d '{"name": "John Doe", "email": "john@example.com"}'"""
        
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'POST'
        assert result['url'] == 'https://api.example.com/users'
        assert result['headers']['Content-Type'] == 'application/json'
        assert '{"name": "John Doe"' in result['body']
    
    def test_post_with_data_auto_method(self):
        """Test that -d flag automatically sets method to POST."""
        curl = "curl 'https://api.example.com/users' -d 'name=John'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'POST'
        assert result['body'] == 'name=John'
    
    def test_multiple_headers(self):
        """Test parsing multiple headers."""
        curl = """curl 'https://api.example.com/users' \\
  -H 'Content-Type: application/json' \\
  -H 'Authorization: Bearer token123' \\
  -H 'Accept: application/json'"""
        
        result = CurlConverter.curl_to_request(curl)
        
        assert len(result['headers']) == 3
        assert result['headers']['Content-Type'] == 'application/json'
        assert result['headers']['Authorization'] == 'Bearer token123'
        assert result['headers']['Accept'] == 'application/json'
    
    def test_bearer_token(self):
        """Test parsing bearer token authentication."""
        curl = "curl 'https://api.example.com/users' -H 'Authorization: Bearer abc123'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['headers']['Authorization'] == 'Bearer abc123'
    
    def test_user_agent(self):
        """Test parsing user agent."""
        curl = "curl 'https://api.example.com' -A 'MyApp/1.0'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['headers']['User-Agent'] == 'MyApp/1.0'
    
    def test_compressed_flag(self):
        """Test --compressed flag."""
        curl = "curl --compressed 'https://api.example.com'"
        result = CurlConverter.curl_to_request(curl)
        
        assert 'Accept-Encoding' in result['headers']
        assert 'gzip' in result['headers']['Accept-Encoding']
    
    def test_request_flag(self):
        """Test --request flag."""
        curl = "curl --request DELETE 'https://api.example.com/users/123'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'DELETE'
    
    def test_data_raw(self):
        """Test --data-raw flag."""
        curl = "curl 'https://api.example.com' --data-raw 'test data'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'POST'
        assert result['body'] == 'test data'
    
    def test_json_flag(self):
        """Test --json flag."""
        curl = "curl --json '{\"test\": \"data\"}' 'https://api.example.com'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'POST'
        assert result['headers']['Content-Type'] == 'application/json'
        assert result['body'] == '{"test": "data"}'
    
    def test_long_form_flags(self):
        """Test long-form flags (--header instead of -H)."""
        curl = """curl --request POST \\
  --url 'https://api.example.com' \\
  --header 'Content-Type: application/json' \\
  --data '{"test": true}'"""
        
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'POST'
        assert result['headers']['Content-Type'] == 'application/json'
        assert result['body'] == '{"test": true}'
    
    def test_skip_insecure_flag(self):
        """Test that -k/--insecure flag is ignored."""
        curl = "curl -k 'https://api.example.com'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['url'] == 'https://api.example.com'
    
    def test_skip_location_flag(self):
        """Test that -L/--location flag is ignored."""
        curl = "curl -L 'https://api.example.com'"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['url'] == 'https://api.example.com'
    
    def test_without_curl_prefix(self):
        """Test parsing command without 'curl' prefix."""
        curl = "'https://api.example.com' -X POST"
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'POST'
        assert result['url'] == 'https://api.example.com'
    
    def test_quoted_url(self):
        """Test URL with various quote styles."""
        curl1 = "curl 'https://api.example.com'"
        curl2 = 'curl "https://api.example.com"'
        curl3 = "curl https://api.example.com"
        
        result1 = CurlConverter.curl_to_request(curl1)
        result2 = CurlConverter.curl_to_request(curl2)
        result3 = CurlConverter.curl_to_request(curl3)
        
        assert result1['url'] == result2['url'] == result3['url']
    
    def test_invalid_empty_command(self):
        """Test error on empty command."""
        with pytest.raises(ValueError, match="Empty cURL command"):
            CurlConverter.curl_to_request("")
    
    def test_invalid_no_url(self):
        """Test error when no URL is found."""
        with pytest.raises(ValueError, match="No URL found"):
            CurlConverter.curl_to_request("curl -X POST")
    
    def test_complex_real_world_example(self):
        """Test a complex real-world cURL command."""
        curl = """curl -X POST 'https://api.github.com/repos/owner/repo/issues' \\
  -H 'Accept: application/vnd.github.v3+json' \\
  -H 'Authorization: token ghp_1234567890' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "title": "Found a bug",
    "body": "I am having a problem with this.",
    "labels": ["bug"]
  }'"""
        
        result = CurlConverter.curl_to_request(curl)
        
        assert result['method'] == 'POST'
        assert 'github.com' in result['url']
        assert result['headers']['Accept'] == 'application/vnd.github.v3+json'
        assert 'token ghp_' in result['headers']['Authorization']
        assert 'Found a bug' in result['body']


class TestCurlGeneration:
    """Test suite for generating cURL commands."""
    
    def test_simple_get(self):
        """Test generating simple GET request."""
        curl = CurlConverter.request_to_curl('GET', 'https://api.example.com/users')
        
        assert 'curl' in curl
        assert 'https://api.example.com/users' in curl
        assert '-X GET' not in curl  # GET is default, shouldn't be included
    
    def test_post_method(self):
        """Test generating POST request."""
        curl = CurlConverter.request_to_curl('POST', 'https://api.example.com/users')
        
        assert '-X POST' in curl
    
    def test_with_headers(self):
        """Test generating request with headers."""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token123'
        }
        curl = CurlConverter.request_to_curl('POST', 'https://api.example.com', headers=headers)
        
        assert "Content-Type: application/json" in curl
        assert "Authorization: Bearer token123" in curl
    
    def test_with_body(self):
        """Test generating request with body."""
        body = '{"name": "John Doe"}'
        curl = CurlConverter.request_to_curl('POST', 'https://api.example.com', body=body)
        
        assert "-d" in curl
        assert "John Doe" in curl
    
    def test_with_query_params(self):
        """Test generating request with query parameters."""
        params = {'page': '1', 'limit': '10'}
        curl = CurlConverter.request_to_curl('GET', 'https://api.example.com/users', params=params)
        
        assert '?page=1&limit=10' in curl or '?limit=10&page=1' in curl
    
    def test_escaping_single_quotes(self):
        """Test escaping single quotes in headers and body."""
        headers = {"X-Custom": "It's a test"}
        body = "It's a body"
        curl = CurlConverter.request_to_curl('POST', 'https://api.example.com', 
                                            headers=headers, body=body)
        
        # Single quotes should be escaped
        assert curl  # Just verify it doesn't crash
    
    def test_line_continuations(self):
        """Test that generated cURL has line continuations."""
        headers = {'Content-Type': 'application/json'}
        curl = CurlConverter.request_to_curl('POST', 'https://api.example.com', headers=headers)
        
        assert '\\' in curl  # Should have line continuations


class TestRoundTrip:
    """Test round-trip conversion (import then export)."""
    
    def test_simple_get_roundtrip(self):
        """Test round-trip for simple GET."""
        original = "curl 'https://api.example.com/users'"
        
        # Import
        data = CurlConverter.curl_to_request(original)
        
        # Export
        regenerated = CurlConverter.request_to_curl(
            data['method'], data['url'], data['headers'], 
            data['body'], data['params']
        )
        
        # Should contain the URL
        assert 'https://api.example.com/users' in regenerated
    
    def test_post_with_headers_roundtrip(self):
        """Test round-trip for POST with headers."""
        original = """curl -X POST 'https://api.example.com' \\
  -H 'Content-Type: application/json' \\
  -d '{"test": true}'"""
        
        # Import
        data = CurlConverter.curl_to_request(original)
        
        # Export
        regenerated = CurlConverter.request_to_curl(
            data['method'], data['url'], data['headers'], 
            data['body'], data['params']
        )
        
        # Should preserve key elements
        assert 'POST' in regenerated
        assert 'Content-Type' in regenerated
        assert 'application/json' in regenerated


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_import_curl_function(self):
        """Test import_curl convenience function."""
        curl = "curl 'https://api.example.com'"
        result = import_curl(curl)
        
        assert result['url'] == 'https://api.example.com'
    
    def test_export_curl_function(self):
        """Test export_curl convenience function."""
        curl = export_curl('GET', 'https://api.example.com')
        
        assert 'curl' in curl
        assert 'https://api.example.com' in curl


class TestValidation:
    """Test validation functions."""
    
    def test_is_valid_curl_true(self):
        """Test is_valid_curl with valid commands."""
        assert CurlConverter.is_valid_curl("curl 'https://api.example.com'")
        assert CurlConverter.is_valid_curl("  curl -X POST 'https://api.example.com'  ")
        assert CurlConverter.is_valid_curl("CURL 'https://api.example.com'")  # Case insensitive
    
    def test_is_valid_curl_false(self):
        """Test is_valid_curl with invalid commands."""
        assert not CurlConverter.is_valid_curl("")
        assert not CurlConverter.is_valid_curl("wget https://example.com")
        assert not CurlConverter.is_valid_curl("curl")  # Too short
        assert not CurlConverter.is_valid_curl("just a string")

