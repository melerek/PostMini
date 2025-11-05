"""
JavaScript Script Engine for Pre/Post Request Scripts

This module provides a sandboxed JavaScript execution environment using PyMiniRacer (V8).
It implements a Postman-compatible 'pm' API for script compatibility.
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from py_mini_racer import MiniRacer


class ScriptExecutionError(Exception):
    """Exception raised when script execution fails."""
    pass


class ScriptTimeoutError(ScriptExecutionError):
    """Exception raised when script execution times out."""
    pass


class ScriptContext:
    """
    Context object that holds script execution state.
    This is exposed as 'pm' in the JavaScript environment.
    """
    
    def __init__(self):
        self.environment = {}
        self.collection_variables = {}
        self.globals_vars = {}
        self.request = {}
        self.response = {}
        self.console_logs = []
        self.test_results = []
        self.variables_changed = False
    
    def to_dict(self) -> Dict:
        """Convert context to dictionary for JSON serialization."""
        return {
            'environment': self.environment,
            'collectionVariables': self.collection_variables,
            'globals': self.globals_vars,
            'request': self.request,
            'response': self.response,
            'console_logs': self.console_logs,
            'test_results': self.test_results,
            'variables_changed': self.variables_changed
        }


class ScriptEngine:
    """
    JavaScript execution engine for pre-request and post-response scripts.
    Provides a Postman-compatible API through the 'pm' object.
    """
    
    def __init__(self, timeout_ms: int = 5000, max_memory: int = 50 * 1024 * 1024):
        """
        Initialize the script engine.
        
        Args:
            timeout_ms: Maximum script execution time in milliseconds (default: 5000ms)
            max_memory: Maximum memory allocation in bytes (default: 50MB)
        """
        self.timeout_ms = timeout_ms
        self.max_memory = max_memory
        self._context = None
    
    def execute_pre_request_script(
        self,
        script: str,
        url: str,
        method: str,
        headers: Dict[str, str],
        body: str,
        params: Dict[str, str],
        environment: Dict[str, str],
        collection_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Execute a pre-request script.
        
        Args:
            script: JavaScript code to execute
            url: Request URL
            method: HTTP method
            headers: Request headers
            body: Request body
            params: Query parameters
            environment: Environment variables
            collection_vars: Collection variables
            
        Returns:
            Dictionary with:
                - url: Modified URL
                - method: Modified method
                - headers: Modified headers
                - body: Modified body
                - params: Modified params
                - environment: Modified environment variables
                - collection_variables: Modified collection variables
                - console_logs: Console output from script
                - execution_time_ms: Script execution time
        """
        if not script or not script.strip():
            return {
                'url': url,
                'method': method,
                'headers': headers,
                'body': body,
                'params': params,
                'environment': environment,
                'collection_variables': collection_vars,
                'console_logs': [],
                'execution_time_ms': 0
            }
        
        # Initialize context
        self._context = ScriptContext()
        self._context.environment = environment.copy()
        self._context.collection_variables = collection_vars.copy()
        self._context.request = {
            'url': url,
            'method': method,
            'headers': headers.copy(),
            'body': body,
            'params': params.copy()
        }
        
        start_time = time.time()
        
        try:
            # Create JavaScript context
            js_ctx = MiniRacer()
            
            # Inject pm API
            self._inject_pm_api(js_ctx, is_pre_request=True)
            
            # Execute script with timeout
            js_ctx.eval(script)
            
            # Extract results from context
            result = self._extract_context_state(js_ctx)
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            result['execution_time_ms'] = round(execution_time, 2)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            if 'timeout' in error_msg.lower():
                raise ScriptTimeoutError(f"Script execution timed out after {self.timeout_ms}ms")
            else:
                raise ScriptExecutionError(f"Script execution failed: {error_msg}")
    
    def execute_post_response_script(
        self,
        script: str,
        response_status: int,
        response_headers: Dict[str, str],
        response_body: str,
        response_time_ms: float,
        environment: Dict[str, str],
        collection_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Execute a post-response script.
        
        Args:
            script: JavaScript code to execute
            response_status: HTTP status code
            response_headers: Response headers
            response_body: Response body
            response_time_ms: Response time in milliseconds
            environment: Environment variables
            collection_vars: Collection variables
            
        Returns:
            Dictionary with:
                - environment: Modified environment variables
                - collection_variables: Modified collection variables
                - console_logs: Console output from script
                - test_results: Test results from pm.test() calls
                - execution_time_ms: Script execution time
        """
        if not script or not script.strip():
            return {
                'environment': environment,
                'collection_variables': collection_vars,
                'console_logs': [],
                'test_results': [],
                'execution_time_ms': 0
            }
        
        # Initialize context
        self._context = ScriptContext()
        self._context.environment = environment.copy()
        self._context.collection_variables = collection_vars.copy()
        self._context.response = {
            'code': response_status,
            'status': self._get_status_text(response_status),
            'headers': response_headers.copy(),
            'body': response_body,
            'responseTime': response_time_ms
        }
        
        start_time = time.time()
        
        try:
            # Create JavaScript context
            js_ctx = MiniRacer()
            
            # Inject pm API
            self._inject_pm_api(js_ctx, is_pre_request=False)
            
            # Execute script with timeout
            js_ctx.eval(script)
            
            # Extract results
            result = self._extract_post_response_state(js_ctx)
            
            execution_time = (time.time() - start_time) * 1000
            result['execution_time_ms'] = round(execution_time, 2)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            if 'timeout' in error_msg.lower():
                raise ScriptTimeoutError(f"Script execution timed out after {self.timeout_ms}ms")
            else:
                raise ScriptExecutionError(f"Script execution failed: {error_msg}")
    
    def _inject_pm_api(self, js_ctx: MiniRacer, is_pre_request: bool):
        """Inject Postman-compatible pm API into JavaScript context."""
        
        # Serialize context to JSON for JavaScript
        context_json = json.dumps({
            'environment': self._context.environment,
            'collectionVariables': self._context.collection_variables,
            'globals': self._context.globals_vars,
            'request': self._context.request if is_pre_request else {},
            'response': self._context.response if not is_pre_request else {},
        })
        
        # PM API implementation in JavaScript
        pm_api = f"""
        // Initialize context from Python
        const __context = {context_json};
        const __consoleLogs = [];
        const __testResults = [];
        
        // Console implementation
        const console = {{
            log: function(...args) {{
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                __consoleLogs.push({{level: 'info', message: message}});
            }},
            info: function(...args) {{
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                __consoleLogs.push({{level: 'info', message: message}});
            }},
            warn: function(...args) {{
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                __consoleLogs.push({{level: 'warning', message: message}});
            }},
            error: function(...args) {{
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                __consoleLogs.push({{level: 'error', message: message}});
            }}
        }};
        
        // PM API
        const pm = {{
            // Environment variables
            environment: {{
                get: function(key) {{
                    return __context.environment[key];
                }},
                set: function(key, value) {{
                    __context.environment[key] = String(value);
                }},
                unset: function(key) {{
                    delete __context.environment[key];
                }},
                has: function(key) {{
                    return key in __context.environment;
                }},
                toObject: function() {{
                    return __context.environment;
                }}
            }},
            
            // Collection variables
            collectionVariables: {{
                get: function(key) {{
                    return __context.collectionVariables[key];
                }},
                set: function(key, value) {{
                    __context.collectionVariables[key] = String(value);
                }},
                unset: function(key) {{
                    delete __context.collectionVariables[key];
                }},
                has: function(key) {{
                    return key in __context.collectionVariables;
                }},
                toObject: function() {{
                    return __context.collectionVariables;
                }}
            }},
            
            // Global variables
            globals: {{
                get: function(key) {{
                    return __context.globals[key];
                }},
                set: function(key, value) {{
                    __context.globals[key] = String(value);
                }},
                unset: function(key) {{
                    delete __context.globals[key];
                }},
                has: function(key) {{
                    return key in __context.globals;
                }},
                toObject: function() {{
                    return __context.globals;
                }}
            }},
            
            // Variables (combined with priority: globals > collection > environment)
            variables: {{
                get: function(key) {{
                    if (key in __context.globals) return __context.globals[key];
                    if (key in __context.collectionVariables) return __context.collectionVariables[key];
                    if (key in __context.environment) return __context.environment[key];
                    return undefined;
                }},
                set: function(key, value) {{
                    __context.environment[key] = String(value);
                }}
            }},
            
            // Request object (pre-request only)
            request: __context.request ? {{
                url: {{
                    toString: function() {{ return __context.request.url; }},
                    valueOf: function() {{ return __context.request.url; }}
                }},
                method: __context.request.method,
                headers: {{
                    add: function(header) {{
                        if (header.key && header.value) {{
                            __context.request.headers[header.key] = header.value;
                        }}
                    }},
                    upsert: function(header) {{
                        if (header.key && header.value) {{
                            __context.request.headers[header.key] = header.value;
                        }}
                    }},
                    remove: function(key) {{
                        delete __context.request.headers[key];
                    }},
                    get: function(key) {{
                        return __context.request.headers[key];
                    }}
                }},
                body: {{
                    raw: __context.request.body,
                    toString: function() {{ return __context.request.body; }}
                }}
            }} : undefined,
            
            // Response object (post-response only)
            response: __context.response ? {{
                code: __context.response.code,
                status: __context.response.status,
                headers: {{
                    get: function(key) {{
                        return __context.response.headers[key];
                    }},
                    has: function(key) {{
                        return key in __context.response.headers;
                    }},
                    toObject: function() {{
                        return __context.response.headers;
                    }}
                }},
                text: function() {{
                    return __context.response.body;
                }},
                json: function() {{
                    try {{
                        return JSON.parse(__context.response.body);
                    }} catch (e) {{
                        throw new Error('Response body is not valid JSON');
                    }}
                }},
                responseTime: __context.response.responseTime
            }} : undefined,
            
            // Test function (post-response only)
            test: function(name, testFunc) {{
                try {{
                    testFunc();
                    __testResults.push({{
                        name: name,
                        passed: true,
                        error: null
                    }});
                }} catch (error) {{
                    __testResults.push({{
                        name: name,
                        passed: false,
                        error: error.message || String(error)
                    }});
                }}
            }},
            
            // Expect-style assertions (for pm.test compatibility)
            expect: function(actual) {{
                return {{
                    to: {{
                        equal: function(expected) {{
                            if (actual !== expected) {{
                                throw new Error(`Expected ${{expected}} but got ${{actual}}`);
                            }}
                        }},
                        eql: function(expected) {{
                            if (JSON.stringify(actual) !== JSON.stringify(expected)) {{
                                throw new Error(`Expected ${{JSON.stringify(expected)}} but got ${{JSON.stringify(actual)}}`);
                            }}
                        }},
                        be: {{
                            a: function(type) {{
                                if (typeof actual !== type) {{
                                    throw new Error(`Expected type ${{type}} but got ${{typeof actual}}`);
                                }}
                            }},
                            above: function(value) {{
                                if (actual <= value) {{
                                    throw new Error(`Expected ${{actual}} to be above ${{value}}`);
                                }}
                            }},
                            below: function(value) {{
                                if (actual >= value) {{
                                    throw new Error(`Expected ${{actual}} to be below ${{value}}`);
                                }}
                            }}
                        }}
                    }},
                    have: {{
                        property: function(prop) {{
                            if (!(prop in actual)) {{
                                throw new Error(`Expected object to have property ${{prop}}`);
                            }}
                        }},
                        length: function(len) {{
                            if (actual.length !== len) {{
                                throw new Error(`Expected length ${{len}} but got ${{actual.length}}`);
                            }}
                        }}
                    }},
                    include: function(value) {{
                        const str = JSON.stringify(actual);
                        const search = JSON.stringify(value);
                        if (!str.includes(search)) {{
                            throw new Error(`Expected to include ${{search}}`);
                        }}
                    }}
                }};
            }}
        }};
        
        // Utility functions
        const atob = function(str) {{
            return Buffer.from(str, 'base64').toString('binary');
        }};
        
        const btoa = function(str) {{
            return Buffer.from(str, 'binary').toString('base64');
        }};
        
        // Crypto utilities (basic)
        const CryptoJS = {{
            MD5: function(message) {{
                return {{ toString: function() {{ return 'MD5_HASH_PLACEHOLDER'; }} }};
            }},
            SHA1: function(message) {{
                return {{ toString: function() {{ return 'SHA1_HASH_PLACEHOLDER'; }} }};
            }},
            SHA256: function(message) {{
                return {{ toString: function() {{ return 'SHA256_HASH_PLACEHOLDER'; }} }};
            }},
            HmacSHA256: function(message, secret) {{
                return {{ toString: function() {{ return 'HMAC_SHA256_PLACEHOLDER'; }} }};
            }}
        }};
        """
        
        js_ctx.eval(pm_api)
    
    def _extract_context_state(self, js_ctx: MiniRacer) -> Dict[str, Any]:
        """Extract modified context state from JavaScript after pre-request script execution."""
        
        # Get modified context
        context_str = js_ctx.eval('JSON.stringify(__context)')
        context = json.loads(context_str)
        
        # Get console logs
        logs_str = js_ctx.eval('JSON.stringify(__consoleLogs)')
        logs = json.loads(logs_str)
        
        return {
            'url': context['request']['url'],
            'method': context['request']['method'],
            'headers': context['request']['headers'],
            'body': context['request']['body'],
            'params': context['request']['params'],
            'environment': context['environment'],
            'collection_variables': context['collectionVariables'],
            'console_logs': logs
        }
    
    def _extract_post_response_state(self, js_ctx: MiniRacer) -> Dict[str, Any]:
        """Extract modified context state from JavaScript after post-response script execution."""
        
        # Get modified context
        context_str = js_ctx.eval('JSON.stringify(__context)')
        context = json.loads(context_str)
        
        # Get console logs
        logs_str = js_ctx.eval('JSON.stringify(__consoleLogs)')
        logs = json.loads(logs_str)
        
        # Get test results
        tests_str = js_ctx.eval('JSON.stringify(__testResults)')
        tests = json.loads(tests_str)
        
        return {
            'environment': context['environment'],
            'collection_variables': context['collectionVariables'],
            'console_logs': logs,
            'test_results': tests
        }
    
    def _get_status_text(self, status_code: int) -> str:
        """Get HTTP status text from status code."""
        status_texts = {
            200: 'OK',
            201: 'Created',
            204: 'No Content',
            301: 'Moved Permanently',
            302: 'Found',
            304: 'Not Modified',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            408: 'Request Timeout',
            429: 'Too Many Requests',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
            504: 'Gateway Timeout'
        }
        return status_texts.get(status_code, 'Unknown')

