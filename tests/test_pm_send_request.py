"""
Tests for pm.sendRequest() API

Tests programmatic HTTP requests from within scripts.
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.features.script_engine import ScriptEngine
from src.core.api_client import ApiResponse
import requests


class TestPmSendRequest:
    """Test pm.sendRequest() functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ScriptEngine()
        self.env = {"baseUrl": "https://api.example.com"}
        self.collection_vars = {}
    
    @patch('src.core.api_client.ApiClient.execute_request')
    def test_send_request_simple_url(self, mock_execute):
        """Test pm.sendRequest() with simple URL string."""
        # Mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"success": true}'
        mock_response.content = b'{"success": true}'
        
        api_response = ApiResponse(mock_response, 0.5)
        mock_execute.return_value = api_response
        
        script = """
        let responseData = null;
        pm.sendRequest('https://api.example.com/users', function(err, response) {
            responseData = response.json();
            pm.environment.set('userId', responseData.userId || '123');
        });
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        # Verify request was made
        assert mock_execute.called
        call_args = mock_execute.call_args
        assert call_args[1]['url'] == 'https://api.example.com/users'
        assert call_args[1]['method'] == 'GET'
    
    @patch('src.core.api_client.ApiClient.execute_request')
    def test_send_request_with_options(self, mock_execute):
        """Test pm.sendRequest() with request options object."""
        # Mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 201
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"id": 42, "name": "Test User"}'
        mock_response.content = b'{"id": 42, "name": "Test User"}'
        
        api_response = ApiResponse(mock_response, 0.3)
        mock_execute.return_value = api_response
        
        script = """
        const requestOptions = {
            url: 'https://api.example.com/users',
            method: 'POST',
            header: {
                'Content-Type': 'application/json',
                'X-API-Key': 'test-key'
            },
            body: {
                mode: 'raw',
                raw: JSON.stringify({ name: 'Test User', email: 'test@example.com' })
            }
        };
        
        pm.sendRequest(requestOptions, function(err, response) {
            if (!err) {
                const data = response.json();
                pm.environment.set('createdUserId', String(data.id));
            }
        });
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        # Verify request was made with correct options
        assert mock_execute.called
        call_args = mock_execute.call_args
        assert call_args[1]['url'] == 'https://api.example.com/users'
        assert call_args[1]['method'] == 'POST'
        assert call_args[1]['headers']['X-API-Key'] == 'test-key'
        assert 'Test User' in call_args[1]['body']
        
        # Verify environment variable was set
        assert result['environment'].get('createdUserId') == '42'
    
    @patch('src.core.api_client.ApiClient.execute_request')
    def test_send_request_callback_receives_response_properties(self, mock_execute):
        """Test that callback receives proper response object with all properties."""
        # Mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json', 'X-Rate-Limit': '100'}
        mock_response.text = '{"status": "ok"}'
        mock_response.content = b'{"status": "ok"}'
        
        api_response = ApiResponse(mock_response, 0.25)
        mock_execute.return_value = api_response
        
        script = """
        pm.sendRequest('https://api.example.com/status', function(err, response) {
            // Test all response properties
            pm.environment.set('statusCode', String(response.code));
            pm.environment.set('statusText', response.status);
            pm.environment.set('responseTime', String(response.responseTime));
            pm.environment.set('responseSize', String(response.responseSize));
            pm.environment.set('rateLimit', response.headers['X-Rate-Limit']);
            
            // Test response body methods
            const bodyText = response.text();
            const bodyJson = response.json();
            pm.environment.set('bodyStatus', bodyJson.status);
        });
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        # Verify all response properties were accessible
        assert result['environment'].get('statusCode') == '200'
        assert result['environment'].get('statusText') == 'OK'
        assert result['environment'].get('rateLimit') == '100'
        assert result['environment'].get('bodyStatus') == 'ok'
        # Response time should be set (in ms)
        assert int(result['environment'].get('responseTime', 0)) > 0
    
    @patch('src.core.api_client.ApiClient.execute_request')
    def test_send_request_error_handling(self, mock_execute):
        """Test pm.sendRequest() error handling when request fails."""
        # Mock request failure
        mock_execute.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        script = """
        let errorOccurred = false;
        let errorMessage = '';
        
        pm.sendRequest('https://api.invalid.local/test', function(err, response) {
            if (err) {
                errorOccurred = true;
                errorMessage = err.message;
                pm.environment.set('requestFailed', 'true');
                pm.environment.set('errorMsg', errorMessage);
            } else {
                pm.environment.set('requestFailed', 'false');
            }
        });
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        # Verify error was passed to callback
        assert result['environment'].get('requestFailed') == 'true'
        assert 'Connection refused' in result['environment'].get('errorMsg', '')
    
    @patch('src.core.api_client.ApiClient.execute_request')
    def test_send_request_multiple_sequential(self, mock_execute):
        """Test multiple sequential pm.sendRequest() calls."""
        # Mock responses for different endpoints
        def mock_responses(method, url, **kwargs):
            mock_response = Mock(spec=requests.Response)
            mock_response.headers = {'Content-Type': 'application/json'}
            mock_response.content = b'{}'
            
            if 'auth' in url:
                mock_response.status_code = 200
                mock_response.text = '{"token": "abc123"}'
            elif 'users' in url:
                mock_response.status_code = 200
                mock_response.text = '{"id": 1, "name": "User"}'
            else:
                mock_response.status_code = 404
                mock_response.text = '{"error": "Not found"}'
            
            return ApiResponse(mock_response, 0.1)
        
        mock_execute.side_effect = mock_responses
        
        script = """
        // First request: Get auth token
        pm.sendRequest('https://api.example.com/auth', function(err, response) {
            if (!err) {
                const data = response.json();
                pm.environment.set('authToken', data.token);
            }
        });
        
        // Second request: Get user data (using token from first request)
        pm.sendRequest({
            url: 'https://api.example.com/users/1',
            method: 'GET',
            header: {
                'Authorization': 'Bearer ' + pm.environment.get('authToken')
            }
        }, function(err, response) {
            if (!err) {
                const user = response.json();
                pm.environment.set('userName', user.name);
            }
        });
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        # Verify both requests were made
        assert mock_execute.call_count == 2
        
        # Verify data from both requests was saved
        assert result['environment'].get('authToken') == 'abc123'
        assert result['environment'].get('userName') == 'User'
    
    @patch('src.core.api_client.ApiClient.execute_request')
    def test_send_request_in_post_response_script(self, mock_execute):
        """Test pm.sendRequest() works in post-response scripts."""
        # Mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"verified": true}'
        mock_response.content = b'{"verified": true}'
        
        api_response = ApiResponse(mock_response, 0.2)
        mock_execute.return_value = api_response
        
        script = """
        // After receiving response, verify it with another endpoint
        const originalData = pm.response.json();
        
        pm.sendRequest('https://api.example.com/verify', function(err, response) {
            if (!err) {
                const verification = response.json();
                pm.environment.set('verified', String(verification.verified));
            }
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={'Content-Type': 'application/json'},
            response_body='{"id": 1}',
            response_time_ms=100,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        # Verify request was made and callback executed
        assert mock_execute.called
        assert result['environment'].get('verified') == 'true'
    
    @patch('src.core.api_client.ApiClient.execute_request')
    def test_send_request_use_variables_in_url(self, mock_execute):
        """Test using pm.variables.replaceIn() with pm.sendRequest()."""
        # Mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = 'OK'
        mock_response.content = b'OK'
        
        api_response = ApiResponse(mock_response, 0.1)
        mock_execute.return_value = api_response
        
        script = """
        const url = pm.variables.replaceIn('{{baseUrl}}/users/123');
        
        pm.sendRequest(url, function(err, response) {
            pm.environment.set('requestSent', 'true');
        });
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        # Verify URL was resolved and used
        call_args = mock_execute.call_args
        assert call_args[1]['url'] == 'https://api.example.com/users/123'
        assert result['environment'].get('requestSent') == 'true'


class TestSendRequestIntegration:
    """Integration tests for pm.sendRequest() with other features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ScriptEngine()
    
    @patch('src.core.api_client.ApiClient.execute_request')
    def test_send_request_with_tests(self, mock_execute):
        """Test using pm.sendRequest() results in pm.test() assertions."""
        # Mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"balance": 1000}'
        mock_response.content = b'{"balance": 1000}'
        
        api_response = ApiResponse(mock_response, 0.15)
        mock_execute.return_value = api_response
        
        script = """
        pm.sendRequest('https://api.example.com/account/balance', function(err, response) {
            pm.test("Balance request succeeded", function() {
                pm.expect(err).to.be.null;
                pm.expect(response.code).to.equal(200);
            });
            
            pm.test("Balance is correct", function() {
                const data = response.json();
                pm.expect(data.balance).to.be.greaterThan(0);
            });
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={},
            response_body='{}',
            response_time_ms=100,
            environment={},
            collection_vars={}
        )
        
        # Verify tests were executed
        assert len(result['test_results']) == 2
        assert all(test['passed'] for test in result['test_results'])
        assert result['test_results'][0]['name'] == "Balance request succeeded"
        assert result['test_results'][1]['name'] == "Balance is correct"
