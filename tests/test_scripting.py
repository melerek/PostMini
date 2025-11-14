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

    def test_variables_replace_in(self):
        """Test that pm.variables.replaceIn() replaces variable placeholders."""
        script = """
        const template = "Hello {{name}}, your token is {{token}}";
        const resolved = pm.variables.replaceIn(template);
        pm.environment.set("resolved", resolved);
        
        // Test with non-existent variable
        const partial = pm.variables.replaceIn("{{existing}} and {{nonExistent}}");
        pm.environment.set("partial", partial);
        
        // Test with non-string input
        const number = pm.variables.replaceIn(123);
        pm.environment.set("number", String(number));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://api.example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment={"name": "Alice", "existing": "found"},
            collection_vars={"token": "abc123"}
        )
        
        # Variables should be replaced with values from environment and collection
        assert result['environment']['resolved'] == "Hello Alice, your token is abc123"
        # Non-existent variables should remain as placeholders
        assert result['environment']['partial'] == "found and {{nonExistent}}"
        # Non-string input should be returned unchanged
        assert result['environment']['number'] == "123"

    def test_dynamic_variables_in_replace_in(self):
        """Test that pm.variables.replaceIn() resolves dynamic variables like $guid, $randomInt."""
        script = """
        const guid = pm.variables.replaceIn('{{$guid}}');
        const randomInt = pm.variables.replaceIn('{{$randomInt}}');
        const randomFirstName = pm.variables.replaceIn('{{$randomFirstName}}');
        const randomLastName = pm.variables.replaceIn('{{$randomLastName}}');
        const randomLoremWord = pm.variables.replaceIn('{{$randomLoremWord}}');
        
        pm.environment.set("guid", guid);
        pm.environment.set("randomInt", randomInt);
        pm.environment.set("randomFirstName", randomFirstName);
        pm.environment.set("randomLastName", randomLastName);
        pm.environment.set("randomLoremWord", randomLoremWord);
        
        // Combined test
        const email = pm.variables.replaceIn('test@{{$randomInt}}{{$randomLoremWord}}.com');
        pm.environment.set("email", email);
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
        
        # Verify all dynamic variables were resolved (not empty and not the placeholder)
        assert result['environment']['guid'] != ""
        assert '{{' not in result['environment']['guid']
        assert '-' in result['environment']['guid']  # UUID format
        
        assert result['environment']['randomInt'] != ""
        assert '{{' not in result['environment']['randomInt']
        assert result['environment']['randomInt'].isdigit()
        
        assert result['environment']['randomFirstName'] != ""
        assert '{{' not in result['environment']['randomFirstName']
        
        assert result['environment']['randomLastName'] != ""
        assert '{{' not in result['environment']['randomLastName']
        
        assert result['environment']['randomLoremWord'] != ""
        assert '{{' not in result['environment']['randomLoremWord']
        
        # Verify combined email has dynamic values resolved
        assert '@' in result['environment']['email']
        assert '.com' in result['environment']['email']
        assert '{{' not in result['environment']['email']

    def test_require_moment(self):
        """Test that require('moment') works for date formatting."""
        script = """
        const moment = require('moment');
        const formatted = moment().format("MM/DD/YYYY_HH:MM:SS");
        pm.environment.set("timestamp", formatted);
        
        // Store in global like the user's script
        pm.globals.set("today", moment().format("MM/DD/YYYY_HH:MM:SS"));
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
        
        # Verify timestamp was formatted correctly
        assert 'timestamp' in result['environment']
        timestamp = result['environment']['timestamp']
        assert '/' in timestamp
        assert '_' in timestamp
        # Check pattern MM/DD/YYYY_HH:MM:SS
        parts = timestamp.split('_')
        assert len(parts) == 2
        date_parts = parts[0].split('/')
        assert len(date_parts) == 3
        
        # Verify global variable was set
        assert 'today' in result['globals']

    def test_user_full_script(self):
        """Test the complete user script with all features combined."""
        script = """
        pm.request.headers.add({key: 'X-Ctx-User-Id', value: 'test-user@services' });
        pm.request.headers.add({key: 'X-Ctx-ScopeType', value: 'TECHNICAL' });
        
        const createOrderId = pm.variables.replaceIn('{{$guid}}');
        pm.collectionVariables.set('createOrderId', createOrderId);
        
        const moment = require('moment');
        pm.globals.set("today", moment().format("MM/DD/YYYY_HH:MM:SS"));
        
        const email = pm.variables.replaceIn('test@{{$randomInt}}{{$randomLoremWord}}.com');
        pm.collectionVariables.set('email', email);
        
        const firstName = pm.variables.replaceIn('{{$randomFirstName}}_{{today}}');
        pm.collectionVariables.set('firstName', firstName);
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://api.example.com",
            method="POST",
            headers={},
            body="",
            params={},
            environment={},
            collection_vars={}
        )
        
        # Verify headers were added
        assert 'X-Ctx-User-Id' in result['headers']
        assert result['headers']['X-Ctx-User-Id'] == 'test-user@services'
        assert 'X-Ctx-ScopeType' in result['headers']
        
        # Verify collection variables
        assert 'createOrderId' in result['collection_variables']
        assert 'email' in result['collection_variables']
        assert 'firstName' in result['collection_variables']
        
        # Verify global variable
        assert 'today' in result['globals']
        
        # Verify dynamic variables were resolved
        assert '{{' not in result['collection_variables']['createOrderId']
        assert '{{' not in result['collection_variables']['email']
        assert '{{' not in result['collection_variables']['firstName']

    def test_local_variables_priority(self):
        """Test that pm.variables.set() creates local variables with highest priority."""
        script = """
        // Set up variables in different scopes with same name
        pm.environment.set("testVar", "from_environment");
        pm.collectionVariables.set("testVar", "from_collection");
        pm.globals.set("testVar", "from_globals");
        pm.variables.set("testVar", "from_local");
        
        // Get should return local value (highest priority)
        const value = pm.variables.get("testVar");
        pm.environment.set("retrieved", value);
        
        // Test replaceIn with local variable
        const replaced = pm.variables.replaceIn("Value is: {{testVar}}");
        pm.environment.set("replaced", replaced);
        
        // Set another local variable
        pm.variables.set("localOnly", "only_in_local");
        const localValue = pm.variables.get("localOnly");
        pm.environment.set("localValue", localValue);
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
        
        # Local variable should have highest priority
        assert result['environment']['retrieved'] == "from_local"
        assert result['environment']['replaced'] == "Value is: from_local"
        
        # Local-only variable should be accessible
        assert result['environment']['localValue'] == "only_in_local"
        
        # But local variables shouldn't persist in environment/collection/globals
        # (they're temporary, script-scoped only)
        assert result['environment']['testVar'] == "from_environment"
        assert result['collection_variables']['testVar'] == "from_collection"
        assert result['globals']['testVar'] == "from_globals"

    def test_variable_scope_isolation(self):
        """Test that different variable scopes are properly isolated."""
        script = """
        // Each scope should maintain its own values
        pm.environment.set("scopeTest", "env_value");
        pm.collectionVariables.set("scopeTest", "coll_value");
        pm.globals.set("scopeTest", "global_value");
        
        // Retrieve from specific scopes
        const envVal = pm.environment.get("scopeTest");
        const collVal = pm.collectionVariables.get("scopeTest");
        const globalVal = pm.globals.get("scopeTest");
        
        pm.environment.set("env_check", envVal);
        pm.environment.set("coll_check", collVal);
        pm.environment.set("global_check", globalVal);
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
        
        # Each scope should have its own value
        assert result['environment']['scopeTest'] == "env_value"
        assert result['collection_variables']['scopeTest'] == "coll_value"
        assert result['globals']['scopeTest'] == "global_value"
        
        # Verification variables
        assert result['environment']['env_check'] == "env_value"
        assert result['environment']['coll_check'] == "coll_value"
        assert result['environment']['global_check'] == "global_value"


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

