"""
Tests for pm.response.to.have.* matchers

Tests cleaner assertion syntax for response validation.
"""

import pytest
from src.features.script_engine import ScriptEngine


class TestResponseMatchers:
    """Test pm.response.to.have.* matchers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ScriptEngine()
        self.env = {}
        self.collection_vars = {}
    
    def test_response_to_have_status(self):
        """Test pm.response.to.have.status() matcher."""
        script = """
        pm.test("Status is 200", function() {
            pm.response.to.have.status(200);
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={},
            response_body='{"success": true}',
            response_time_ms=100,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
    
    def test_response_to_have_status_failure(self):
        """Test pm.response.to.have.status() matcher failure."""
        script = """
        pm.test("Status should be 200", function() {
            pm.response.to.have.status(200);
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=404,
            response_headers={},
            response_body='{"error": "Not found"}',
            response_time_ms=100,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is False
        assert '200' in result['test_results'][0]['error']
        assert '404' in result['test_results'][0]['error']
    
    def test_response_to_have_header(self):
        """Test pm.response.to.have.header() matcher."""
        script = """
        pm.test("Has Content-Type header", function() {
            pm.response.to.have.header('Content-Type');
        });
        
        pm.test("Content-Type is JSON", function() {
            pm.response.to.have.header('Content-Type', 'application/json');
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={'Content-Type': 'application/json'},
            response_body='{}',
            response_time_ms=50,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 2
        assert all(test['passed'] for test in result['test_results'])
    
    def test_response_to_have_header_missing(self):
        """Test pm.response.to.have.header() with missing header."""
        script = """
        pm.test("Has X-Custom-Header", function() {
            pm.response.to.have.header('X-Custom-Header');
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={'Content-Type': 'text/plain'},
            response_body='OK',
            response_time_ms=50,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is False
        assert 'X-Custom-Header' in result['test_results'][0]['error']
    
    def test_response_to_have_jsonBody(self):
        """Test pm.response.to.have.jsonBody() matcher."""
        script = """
        pm.test("Response is valid JSON", function() {
            pm.response.to.have.jsonBody();
        });
        
        pm.test("Response has user.name", function() {
            pm.response.to.have.jsonBody('user.name');
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={'Content-Type': 'application/json'},
            response_body='{"user": {"name": "John", "id": 123}}',
            response_time_ms=75,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 2
        assert all(test['passed'] for test in result['test_results'])
    
    def test_response_to_have_jsonBody_invalid_path(self):
        """Test pm.response.to.have.jsonBody() with invalid path."""
        script = """
        pm.test("Response has user.email", function() {
            pm.response.to.have.jsonBody('user.email');
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={},
            response_body='{"user": {"name": "John"}}',
            response_time_ms=50,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is False
        assert 'not found' in result['test_results'][0]['error'].lower()
    
    def test_response_to_be_ok(self):
        """Test pm.response.to.be.ok getter."""
        script = """
        pm.test("Response is OK", function() {
            pm.response.to.be.ok;
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={},
            response_body='Success',
            response_time_ms=50,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
    
    def test_response_to_be_ok_with_201(self):
        """Test pm.response.to.be.ok with 201 status."""
        script = """
        pm.test("Response is OK (201)", function() {
            pm.response.to.be.ok;
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=201,
            response_headers={},
            response_body='Created',
            response_time_ms=50,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
    
    def test_response_to_be_ok_failure(self):
        """Test pm.response.to.be.ok with error status."""
        script = """
        pm.test("Response is OK", function() {
            pm.response.to.be.ok;
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=404,
            response_headers={},
            response_body='Not Found',
            response_time_ms=50,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is False
        assert '404' in result['test_results'][0]['error']
    
    def test_response_to_be_success(self):
        """Test pm.response.to.be.success getter (alias for ok)."""
        script = """
        pm.test("Response is successful", function() {
            pm.response.to.be.success;
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=204,
            response_headers={},
            response_body='',
            response_time_ms=30,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
    
    def test_response_to_be_error(self):
        """Test pm.response.to.be.error getter."""
        script = """
        pm.test("Response is error", function() {
            pm.response.to.be.error;
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=500,
            response_headers={},
            response_body='Internal Server Error',
            response_time_ms=100,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
    
    def test_response_to_be_clientError(self):
        """Test pm.response.to.be.clientError getter."""
        script = """
        pm.test("Response is client error", function() {
            pm.response.to.be.clientError;
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=400,
            response_headers={},
            response_body='Bad Request',
            response_time_ms=50,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
    
    def test_response_to_be_serverError(self):
        """Test pm.response.to.be.serverError getter."""
        script = """
        pm.test("Response is server error", function() {
            pm.response.to.be.serverError;
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=503,
            response_headers={},
            response_body='Service Unavailable',
            response_time_ms=150,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
    
    def test_multiple_response_matchers(self):
        """Test combining multiple response matchers."""
        script = """
        pm.test("Complete response validation", function() {
            pm.response.to.have.status(200);
            pm.response.to.be.ok;
            pm.response.to.have.header('Content-Type', 'application/json');
            pm.response.to.have.jsonBody('data');
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={'Content-Type': 'application/json'},
            response_body='{"data": {"items": []}}',
            response_time_ms=80,
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True


class TestResponseMatchersWithExpect:
    """Test combining pm.response matchers with pm.expect()."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ScriptEngine()
    
    def test_response_and_expect_together(self):
        """Test using both pm.response.to.have.* and pm.expect()."""
        script = """
        pm.test("Full API validation", function() {
            // Use response matchers
            pm.response.to.have.status(200);
            pm.response.to.be.ok;
            pm.response.to.have.header('Content-Type');
            
            // Use expect for body validation
            const body = pm.response.json();
            pm.expect(body).to.have.property('success');
            pm.expect(body.success).to.be.true;
            pm.expect(body.data).to.have.lengthOf(3);
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={'Content-Type': 'application/json'},
            response_body='{"success": true, "data": [1, 2, 3]}',
            response_time_ms=100,
            environment={},
            collection_vars={}
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
