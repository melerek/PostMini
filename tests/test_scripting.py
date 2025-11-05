"""
Test Suite for JavaScript Scripting Feature

Tests for pre-request and post-response script execution.
"""

import pytest
import sys
import os

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.script_engine import ScriptEngine, ScriptExecutionError, ScriptTimeoutError


class TestScriptEngine:
    """Test the JavaScript script execution engine."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = ScriptEngine(timeout_ms=5000)
    
    def test_pre_request_script_basic(self):
        """Test basic pre-request script execution."""
        script = """
        console.log("Test script executed");
        pm.environment.set("testVar", "testValue");
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://api.example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment={},
            collection_vars={}
        )
        
        assert result['environment']['testVar'] == "testValue"
        assert len(result['console_logs']) > 0
        assert result['console_logs'][0]['message'] == "Test script executed"
    
    def test_pre_request_modify_url(self):
        """Test modifying URL in pre-request script."""
        script = """
        pm.request.url = "https://modified.example.com";
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://api.example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment={},
            collection_vars={}
        )
        
        assert result['url'] == "https://modified.example.com"
    
    def test_pre_request_modify_headers(self):
        """Test modifying headers in pre-request script."""
        script = """
        pm.request.headers.add({key: "X-Custom-Header", value: "test-value"});
        pm.request.headers.upsert({key: "Authorization", value: "Bearer token123"});
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://api.example.com",
            method="GET",
            headers={"Content-Type": "application/json"},
            body="",
            params={},
            environment={},
            collection_vars={}
        )
        
        assert result['headers']['X-Custom-Header'] == "test-value"
        assert result['headers']['Authorization'] == "Bearer token123"
        assert result['headers']['Content-Type'] == "application/json"
    
    def test_pre_request_collection_variables(self):
        """Test setting collection variables."""
        script = """
        pm.collectionVariables.set("apiKey", "abc123");
        pm.collectionVariables.set("baseUrl", "https://api.test.com");
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://api.example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment={},
            collection_vars={}
        )
        
        assert result['collection_variables']['apiKey'] == "abc123"
        assert result['collection_variables']['baseUrl'] == "https://api.test.com"
    
    def test_post_response_script_basic(self):
        """Test basic post-response script execution."""
        script = """
        console.log("Response received");
        const responseCode = pm.response.code;
        pm.environment.set("lastStatusCode", responseCode.toString());
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={"Content-Type": "application/json"},
            response_body='{"status": "ok"}',
            response_time_ms=150.5,
            environment={},
            collection_vars={}
        )
        
        assert result['environment']['lastStatusCode'] == "200"
        assert len(result['console_logs']) > 0
    
    def test_post_response_parse_json(self):
        """Test parsing JSON response in post-response script."""
        script = """
        const data = pm.response.json();
        pm.environment.set("userId", data.user.id);
        pm.environment.set("userName", data.user.name);
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={"Content-Type": "application/json"},
            response_body='{"user": {"id": "123", "name": "John Doe"}}',
            response_time_ms=150.5,
            environment={},
            collection_vars={}
        )
        
        assert result['environment']['userId'] == "123"
        assert result['environment']['userName'] == "John Doe"
    
    def test_post_response_tests(self):
        """Test pm.test() assertions in post-response script."""
        script = """
        pm.test("Status code is 200", function() {
            pm.expect(pm.response.code).to.equal(200);
        });
        
        pm.test("Response has data", function() {
            const data = pm.response.json();
            pm.expect(data).to.have.property("status");
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={"Content-Type": "application/json"},
            response_body='{"status": "ok"}',
            response_time_ms=150.5,
            environment={},
            collection_vars={}
        )
        
        assert len(result['test_results']) == 2
        assert result['test_results'][0]['passed'] == True
        assert result['test_results'][0]['name'] == "Status code is 200"
        assert result['test_results'][1]['passed'] == True
    
    def test_post_response_failed_test(self):
        """Test failed assertion in post-response script."""
        script = """
        pm.test("Status code is 404", function() {
            pm.expect(pm.response.code).to.equal(404);
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={},
            response_body="",
            response_time_ms=100,
            environment={},
            collection_vars={}
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] == False
        assert "Expected 404 but got 200" in result['test_results'][0]['error']
    
    def test_script_error_handling(self):
        """Test script execution error handling."""
        script = """
        throw new Error("Test error");
        """
        
        with pytest.raises(ScriptExecutionError):
            self.engine.execute_pre_request_script(
                script=script,
                url="https://api.example.com",
                method="GET",
                headers={},
                body="",
                params={},
                environment={},
                collection_vars={}
            )
    
    def test_empty_script(self):
        """Test that empty scripts return unmodified data."""
        result = self.engine.execute_pre_request_script(
            script="",
            url="https://api.example.com",
            method="GET",
            headers={"X-Test": "value"},
            body="test body",
            params={"key": "value"},
            environment={"env_var": "env_value"},
            collection_vars={"coll_var": "coll_value"}
        )
        
        assert result['url'] == "https://api.example.com"
        assert result['method'] == "GET"
        assert result['headers']['X-Test'] == "value"
        assert result['body'] == "test body"
        assert result['params']['key'] == "value"
        assert result['environment']['env_var'] == "env_value"
        assert result['collection_variables']['coll_var'] == "coll_value"
    
    def test_console_log_levels(self):
        """Test different console log levels."""
        script = """
        console.log("Info message");
        console.info("Info message 2");
        console.warn("Warning message");
        console.error("Error message");
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://api.example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment={},
            collection_vars={}
        )
        
        logs = result['console_logs']
        assert len(logs) == 4
        assert logs[0]['level'] == 'info'
        assert logs[1]['level'] == 'info'
        assert logs[2]['level'] == 'warning'
        assert logs[3]['level'] == 'error'
    
    def test_variable_priority(self):
        """Test that pm.variables.get() respects priority: globals > collection > environment."""
        script = """
        const envVar = pm.environment.get("testVar");
        const collVar = pm.collectionVariables.get("testVar");
        const globalVar = pm.globals.get("testVar");
        const anyVar = pm.variables.get("testVar");
        
        pm.environment.set("retrieved_env", envVar || "undefined");
        pm.environment.set("retrieved_coll", collVar || "undefined");
        pm.environment.set("retrieved_global", globalVar || "undefined");
        pm.environment.set("retrieved_any", anyVar);
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://api.example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment={"testVar": "from_env"},
            collection_vars={"testVar": "from_coll"}
        )
        
        # pm.variables.get should return collection value (collection > environment)
        assert result['environment']['retrieved_env'] == "from_env"
        assert result['environment']['retrieved_coll'] == "from_coll"
        assert result['environment']['retrieved_global'] == "undefined"
        assert result['environment']['retrieved_any'] == "from_coll"


class TestScriptSnippets:
    """Test script snippets library."""
    
    def test_snippets_available(self):
        """Test that script snippets are available."""
        from src.features.script_snippets import ScriptSnippets
        
        pre_snippets = ScriptSnippets.get_pre_request_snippets()
        post_snippets = ScriptSnippets.get_post_response_snippets()
        
        assert len(pre_snippets) > 0
        assert len(post_snippets) > 0
        
        # Check specific snippets exist
        assert "Set Timestamp" in pre_snippets
        assert "Extract JSON Token" in post_snippets
    
    def test_get_snippet_names(self):
        """Test getting snippet names."""
        from src.features.script_snippets import ScriptSnippets
        
        pre_names = ScriptSnippets.get_snippet_names("pre_request")
        post_names = ScriptSnippets.get_snippet_names("post_response")
        
        assert len(pre_names) > 0
        assert len(post_names) > 0
        assert isinstance(pre_names, list)
        assert isinstance(post_names, list)
    
    def test_get_specific_snippet(self):
        """Test getting a specific snippet."""
        from src.features.script_snippets import ScriptSnippets
        
        snippet = ScriptSnippets.get_snippet("Set Timestamp", "pre_request")
        
        assert 'description' in snippet
        assert 'code' in snippet
        assert len(snippet['code']) > 0
        assert 'Date.now()' in snippet['code']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

