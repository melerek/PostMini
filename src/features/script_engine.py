"""
JavaScript Script Engine for Pre/Post Request Scripts

This module provides a sandboxed JavaScript execution environment using PyMiniRacer (V8).
It implements a Postman-compatible 'pm' API for script compatibility.
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from py_mini_racer import MiniRacer
from src.features.dynamic_variables import resolve_dynamic_variable


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
            
            # Handle any pm.sendRequest() calls
            self._handle_pending_requests(js_ctx)
            
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
            
            # Handle any pm.sendRequest() calls
            self._handle_pending_requests(js_ctx)
            
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
        
        # Pre-generate dynamic variables for use in JavaScript
        # This ensures consistent values within a single script execution
        dynamic_vars_map = {}
        from src.features.dynamic_variables import get_all_dynamic_variables
        for var_name in get_all_dynamic_variables():
            dynamic_vars_map[var_name] = resolve_dynamic_variable(var_name)
        
        # Serialize context to JSON for JavaScript
        context_json = json.dumps({
            'environment': self._context.environment,
            'collectionVariables': self._context.collection_variables,
            'globals': self._context.globals_vars,
            'request': self._context.request if is_pre_request else {},
            'response': self._context.response if not is_pre_request else {},
        })
        
        dynamic_vars_json = json.dumps(dynamic_vars_map)
        dynamic_vars_json = json.dumps(dynamic_vars_map)
        
        # PM API implementation in JavaScript
        pm_api = f"""
        // Initialize context from Python
        const __context = {context_json};
        const __consoleLogs = [];
        const __testResults = [];
        const __dynamicVars = {dynamic_vars_json};
        const __localVars = {{}};  // Local/temporary variables (highest priority)
        
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
            
            // Variables (combined with priority: local > globals > collection > environment)
            variables: {{
                get: function(key) {{
                    // Check local variables first (temporary, script-scoped)
                    if (key in __localVars) return __localVars[key];
                    // Then globals
                    if (key in __context.globals) return __context.globals[key];
                    // Then collection variables
                    if (key in __context.collectionVariables) return __context.collectionVariables[key];
                    // Finally environment
                    if (key in __context.environment) return __context.environment[key];
                    return undefined;
                }},
                set: function(key, value) {{
                    // Set as local/temporary variable (highest priority, script-scoped only)
                    __localVars[key] = String(value);
                }},
                has: function(key) {{
                    return key in __localVars || 
                           key in __context.globals || 
                           key in __context.collectionVariables || 
                           key in __context.environment;
                }},
                toObject: function() {{
                    // Merge all scopes with proper priority
                    return {{
                        ...__context.environment,
                        ...__context.collectionVariables,
                        ...__context.globals,
                        ...__localVars
                    }};
                }},
                replaceIn: function(template) {{
                    if (typeof template !== 'string') {{
                        return template;
                    }}
                    
                    // First, replace {{{{variableName}}}} with actual values (double braces)
                    let result = template.replace(/\\{{\\{{\\s*([^}}\\s]+)\\s*\\}}\\}}/g, function(match, varName) {{
                        // Check if it's a dynamic variable (starts with $)
                        if (varName.startsWith('$')) {{
                            if (varName in __dynamicVars) {{
                                return __dynamicVars[varName];
                            }}
                            return match;
                        }}
                        
                        // Check local variables first (highest priority)
                        if (varName in __localVars) {{
                            return __localVars[varName];
                        }}
                        // Then check globals
                        if (varName in __context.globals) {{
                            return __context.globals[varName];
                        }}
                        // Then collection vars
                        if (varName in __context.collectionVariables) {{
                            return __context.collectionVariables[varName];
                        }}
                        // Finally environment
                        if (varName in __context.environment) {{
                            return __context.environment[varName];
                        }}
                        // Return original placeholder if variable not found
                        return match;
                    }});
                    
                    // Also replace $variable syntax (single $ without braces) for Postman compatibility
                    result = result.replace(/\\$([a-zA-Z][a-zA-Z0-9]*)/g, function(match, varName) {{
                        const fullVarName = '$' + varName;
                        if (fullVarName in __dynamicVars) {{
                            return __dynamicVars[fullVarName];
                        }}
                        return match;
                    }});
                    
                    return result;
                }}
            }},
            
            // Request object (pre-request only)
            request: __context.request ? {{
                get url() {{ return __context.request.url; }},
                set url(value) {{ __context.request.url = String(value); }},
                get method() {{ return __context.request.method; }},
                set method(value) {{ __context.request.method = String(value).toUpperCase(); }},
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
                    }},
                    has: function(key) {{
                        return key in __context.request.headers;
                    }},
                    toObject: function() {{
                        return __context.request.headers;
                    }}
                }},
                body: {{
                    get raw() {{ return __context.request.body; }},
                    set raw(value) {{ __context.request.body = String(value); }},
                    toString: function() {{ return __context.request.body; }},
                    // Body mode helpers
                    get mode() {{ return 'raw'; }},
                    update: function(newBody) {{
                        __context.request.body = String(newBody);
                    }}
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
                responseTime: __context.response.responseTime,
                
                // Chai-style assertions for response
                to: {{
                    have: {{
                        status: function(expectedStatus) {{
                            if (__context.response.code !== expectedStatus) {{
                                throw new Error(
                                    `Expected status ${{expectedStatus}} but got ${{__context.response.code}}`
                                );
                            }}
                        }},
                        header: function(headerName, expectedValue) {{
                            const actualValue = __context.response.headers[headerName];
                            if (!actualValue) {{
                                throw new Error(`Expected header "${{headerName}}" to exist`);
                            }}
                            if (expectedValue !== undefined && actualValue !== expectedValue) {{
                                throw new Error(
                                    `Expected header "${{headerName}}" to be "${{expectedValue}}" but got "${{actualValue}}"`
                                );
                            }}
                        }},
                        jsonBody: function(path) {{
                            try {{
                                const body = JSON.parse(__context.response.body);
                                if (path) {{
                                    // Simple path navigation (e.g., "data.user.name")
                                    const parts = path.split('.');
                                    let value = body;
                                    for (const part of parts) {{
                                        if (value && typeof value === 'object' && part in value) {{
                                            value = value[part];
                                        }} else {{
                                            throw new Error(`Path "${{path}}" not found in response body`);
                                        }}
                                    }}
                                }}
                            }} catch (e) {{
                                if (e.message.includes('not found')) throw e;
                                throw new Error('Response body is not valid JSON');
                            }}
                        }}
                    }},
                    be: {{
                        get ok() {{
                            if (__context.response.code < 200 || __context.response.code >= 300) {{
                                throw new Error(
                                    `Expected response to be ok (2xx) but got ${{__context.response.code}}`
                                );
                            }}
                        }},
                        get success() {{
                            if (__context.response.code < 200 || __context.response.code >= 300) {{
                                throw new Error(
                                    `Expected response to be successful (2xx) but got ${{__context.response.code}}`
                                );
                            }}
                        }},
                        get error() {{
                            if (__context.response.code < 400) {{
                                throw new Error(
                                    `Expected response to be error (4xx/5xx) but got ${{__context.response.code}}`
                                );
                            }}
                        }},
                        get clientError() {{
                            if (__context.response.code < 400 || __context.response.code >= 500) {{
                                throw new Error(
                                    `Expected response to be client error (4xx) but got ${{__context.response.code}}`
                                );
                            }}
                        }},
                        get serverError() {{
                            if (__context.response.code < 500 || __context.response.code >= 600) {{
                                throw new Error(
                                    `Expected response to be server error (5xx) but got ${{__context.response.code}}`
                                );
                            }}
                        }}
                    }}
                }}
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
                let shouldNegate = false;
                
                const assert = function(condition, message) {{
                    if (shouldNegate ? condition : !condition) {{
                        throw new Error(message);
                    }}
                }};
                
                const api = {{
                    to: {{
                        equal: function(expected) {{
                            assert(actual === expected, 
                                `Expected ${{expected}} but got ${{actual}}`);
                            return api;
                        }},
                        eql: function(expected) {{
                            assert(JSON.stringify(actual) === JSON.stringify(expected),
                                `Expected ${{JSON.stringify(expected)}} but got ${{JSON.stringify(actual)}}`);
                            return api;
                        }},
                        be: {{
                            a: function(type) {{
                                assert(typeof actual === type,
                                    `Expected type ${{type}} but got ${{typeof actual}}`);
                                return api;
                            }},
                            an: function(type) {{
                                assert(typeof actual === type,
                                    `Expected type ${{type}} but got ${{typeof actual}}`);
                                return api;
                            }},
                            above: function(value) {{
                                assert(actual > value,
                                    `Expected ${{actual}} to be above ${{value}}`);
                                return api;
                            }},
                            below: function(value) {{
                                assert(actual < value,
                                    `Expected ${{actual}} to be below ${{value}}`);
                                return api;
                            }},
                            greaterThan: function(value) {{
                                assert(actual > value,
                                    `Expected ${{actual}} to be greater than ${{value}}`);
                                return api;
                            }},
                            lessThan: function(value) {{
                                assert(actual < value,
                                    `Expected ${{actual}} to be less than ${{value}}`);
                                return api;
                            }},
                            get ok() {{
                                assert(!!actual, `Expected value to be truthy`);
                                return api;
                            }},
                            get true() {{
                                assert(actual === true, `Expected true but got ${{actual}}`);
                                return api;
                            }},
                            get false() {{
                                assert(actual === false, `Expected false but got ${{actual}}`);
                                return api;
                            }},
                            get null() {{
                                assert(actual === null, `Expected null but got ${{actual}}`);
                                return api;
                            }},
                            get undefined() {{
                                assert(actual === undefined, `Expected undefined but got ${{actual}}`);
                                return api;
                            }},
                            oneOf: function(array) {{
                                assert(array.includes(actual),
                                    `Expected ${{actual}} to be one of ${{JSON.stringify(array)}}`);
                                return api;
                            }}
                        }},
                        match: function(regex) {{
                            const pattern = regex instanceof RegExp ? regex : new RegExp(regex);
                            assert(pattern.test(String(actual)),
                                `Expected ${{actual}} to match ${{regex}}`);
                            return api;
                        }},
                        have: {{
                            property: function(prop, value) {{
                                assert(prop in actual,
                                    `Expected object to have property ${{prop}}`);
                                if (value !== undefined) {{
                                    assert(actual[prop] === value,
                                        `Expected property ${{prop}} to equal ${{value}} but got ${{actual[prop]}}`);
                                }}
                                return api;
                            }},
                            length: function(len) {{
                                assert(actual.length === len,
                                    `Expected length ${{len}} but got ${{actual.length}}`);
                                return api;
                            }},
                            lengthOf: function(len) {{
                                assert(actual.length === len,
                                    `Expected length ${{len}} but got ${{actual.length}}`);
                                return api;
                            }},
                            keys: function(...expectedKeys) {{
                                const actualKeys = Object.keys(actual).sort();
                                const expected = expectedKeys.flat().sort();
                                assert(JSON.stringify(actualKeys) === JSON.stringify(expected),
                                    `Expected keys ${{JSON.stringify(expected)}} but got ${{JSON.stringify(actualKeys)}}`);
                                return api;
                            }},
                            members: function(expectedArray) {{
                                const actualSorted = JSON.stringify([...actual].sort());
                                const expectedSorted = JSON.stringify([...expectedArray].sort());
                                assert(actualSorted === expectedSorted,
                                    `Expected members ${{expectedSorted}} but got ${{actualSorted}}`);
                                return api;
                            }}
                        }},
                        include: function(value) {{
                            if (typeof actual === 'string') {{
                                assert(actual.includes(value),
                                    `Expected string to include ${{value}}`);
                            }} else if (Array.isArray(actual)) {{
                                assert(actual.includes(value),
                                    `Expected array to include ${{value}}`);
                            }} else {{
                                const str = JSON.stringify(actual);
                                const search = JSON.stringify(value);
                                assert(str.includes(search),
                                    `Expected to include ${{search}}`);
                            }}
                            return api;
                        }}
                    }},
                    get not() {{
                        shouldNegate = true;
                        return api;
                    }},
                    get and() {{
                        return api;
                    }}
                }};
                
                return api;
            }},
            
            // Info about the current request/script execution
            info: {{
                eventName: {json.dumps("prerequest" if is_pre_request else "test")},
                iteration: 1,
                iterationCount: 1,
                requestName: "Request",
                requestId: "generated-id-" + Date.now()
            }},
            
            // Send programmatic HTTP requests
            sendRequest: function(request, callback) {{
                // Store request for Python to execute
                if (!globalThis.__pendingRequests) {{
                    globalThis.__pendingRequests = [];
                }}
                
                const requestId = '__req_' + globalThis.__pendingRequests.length;
                
                // Normalize request format
                let requestObj;
                if (typeof request === 'string') {{
                    requestObj = {{ url: request }};
                }} else {{
                    requestObj = request;
                }}
                
                // Store the callback and request
                globalThis.__pendingRequests.push({{
                    id: requestId,
                    request: requestObj,
                    callback: callback
                }});
                
                return requestId;
            }},
            
            // Cookies API
            cookies: {{
                __jar: {{}},
                
                get: function(cookieName) {{
                    return this.__jar[cookieName];
                }},
                
                set: function(cookieName, cookieValue) {{
                    this.__jar[cookieName] = String(cookieValue);
                }},
                
                has: function(cookieName) {{
                    return cookieName in this.__jar;
                }},
                
                clear: function(cookieName) {{
                    delete this.__jar[cookieName];
                }},
                
                toObject: function() {{
                    return this.__jar;
                }},
                
                jar: function() {{
                    return this;
                }}
            }}
        }};
        
        // Legacy Postman API (backwards compatibility)
        const postman = {{
            setEnvironmentVariable: function(key, value) {{
                pm.environment.set(key, value);
            }},
            getEnvironmentVariable: function(key) {{
                return pm.environment.get(key);
            }},
            clearEnvironmentVariable: function(key) {{
                pm.environment.unset(key);
            }},
            setGlobalVariable: function(key, value) {{
                pm.globals.set(key, value);
            }},
            getGlobalVariable: function(key) {{
                return pm.globals.get(key);
            }},
            clearGlobalVariable: function(key) {{
                pm.globals.unset(key);
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
        
        // require() function that returns modules
        const require = function(moduleName) {{
            if (moduleName === 'moment') {{
                // Return moment.js-like library for date/time formatting
                return function(dateInput) {{
                    const date = dateInput ? new Date(dateInput) : new Date();
                    
                    return {{
                        format: function(formatStr) {{
                            if (!formatStr) {{
                                return date.toISOString();
                            }}
                            
                            const pad = (n) => n < 10 ? '0' + n : n;
                            const year = date.getFullYear();
                            const month = date.getMonth() + 1;
                            const day = date.getDate();
                            const hours = date.getHours();
                            const minutes = date.getMinutes();
                            const seconds = date.getSeconds();
                            
                            // Support common moment.js format strings
                            return formatStr
                                .replace(/YYYY/g, year)
                                .replace(/MM/g, pad(month))
                                .replace(/DD/g, pad(day))
                                .replace(/HH/g, pad(hours))
                                .replace(/mm/g, pad(minutes))
                                .replace(/SS/g, pad(seconds))
                                .replace(/ss/g, pad(seconds));
                        }},
                        unix: function() {{
                            return Math.floor(date.getTime() / 1000);
                        }},
                        valueOf: function() {{
                            return date.getTime();
                        }},
                        toISOString: function() {{
                            return date.toISOString();
                        }},
                        toString: function() {{
                            return date.toString();
                        }}
                    }};
                }};
            }}
            
            if (moduleName === 'lodash' || moduleName === '_') {{
                // Return lodash-like utility library
                return {{
                    // Array methods
                    chunk: function(array, size) {{
                        const result = [];
                        for (let i = 0; i < array.length; i += size) {{
                            result.push(array.slice(i, i + size));
                        }}
                        return result;
                    }},
                    compact: function(array) {{
                        return array.filter(Boolean);
                    }},
                    uniq: function(array) {{
                        return [...new Set(array)];
                    }},
                    flatten: function(array) {{
                        return array.flat();
                    }},
                    flattenDeep: function(array) {{
                        return array.flat(Infinity);
                    }},
                    difference: function(array, ...values) {{
                        const exclude = new Set(values.flat());
                        return array.filter(item => !exclude.has(item));
                    }},
                    intersection: function(...arrays) {{
                        if (arrays.length === 0) return [];
                        const first = new Set(arrays[0]);
                        return arrays[0].filter(item => 
                            arrays.every(arr => arr.includes(item))
                        );
                    }},
                    union: function(...arrays) {{
                        return [...new Set(arrays.flat())];
                    }},
                    
                    // Collection methods
                    map: function(collection, iteratee) {{
                        // Support property shorthand: _.map(users, 'name')
                        if (typeof iteratee === 'string') {{
                            const prop = iteratee;
                            iteratee = item => item[prop];
                        }}
                        if (Array.isArray(collection)) {{
                            return collection.map(iteratee);
                        }}
                        return Object.values(collection).map(iteratee);
                    }},
                    filter: function(collection, predicate) {{
                        // Support matcher object: _.filter(users, {{active: true}})
                        if (typeof predicate === 'object' && predicate !== null && !Array.isArray(predicate)) {{
                            const matcher = predicate;
                            predicate = item => {{
                                for (const key in matcher) {{
                                    if (item[key] !== matcher[key]) return false;
                                }}
                                return true;
                            }};
                        }}
                        if (Array.isArray(collection)) {{
                            return collection.filter(predicate);
                        }}
                        return Object.values(collection).filter(predicate);
                    }},
                    find: function(collection, predicate) {{
                        // Support matcher object: _.find(users, {{name: 'Alice'}})
                        if (typeof predicate === 'object' && predicate !== null && !Array.isArray(predicate)) {{
                            const matcher = predicate;
                            predicate = item => {{
                                for (const key in matcher) {{
                                    if (item[key] !== matcher[key]) return false;
                                }}
                                return true;
                            }};
                        }}
                        if (Array.isArray(collection)) {{
                            return collection.find(predicate);
                        }}
                        return Object.values(collection).find(predicate);
                    }},
                    forEach: function(collection, iteratee) {{
                        if (Array.isArray(collection)) {{
                            collection.forEach(iteratee);
                        }} else {{
                            Object.entries(collection).forEach(([k, v]) => iteratee(v, k));
                        }}
                    }},
                    reduce: function(collection, iteratee, accumulator) {{
                        if (Array.isArray(collection)) {{
                            return collection.reduce(iteratee, accumulator);
                        }}
                        return Object.values(collection).reduce(iteratee, accumulator);
                    }},
                    size: function(collection) {{
                        if (Array.isArray(collection) || typeof collection === 'string') {{
                            return collection.length;
                        }}
                        return Object.keys(collection).length;
                    }},
                    
                    // Object methods
                    get: function(object, path, defaultValue) {{
                        const keys = typeof path === 'string' ? path.split('.') : path;
                        let result = object;
                        for (const key of keys) {{
                            if (result == null) return defaultValue;
                            result = result[key];
                        }}
                        return result === undefined ? defaultValue : result;
                    }},
                    set: function(object, path, value) {{
                        const keys = typeof path === 'string' ? path.split('.') : path;
                        let current = object;
                        for (let i = 0; i < keys.length - 1; i++) {{
                            const key = keys[i];
                            if (!(key in current)) {{
                                current[key] = {{}};
                            }}
                            current = current[key];
                        }}
                        current[keys[keys.length - 1]] = value;
                        return object;
                    }},
                    has: function(object, path) {{
                        const keys = typeof path === 'string' ? path.split('.') : path;
                        let current = object;
                        for (const key of keys) {{
                            if (current == null || !(key in current)) {{
                                return false;
                            }}
                            current = current[key];
                        }}
                        return true;
                    }},
                    keys: function(object) {{
                        return Object.keys(object);
                    }},
                    values: function(object) {{
                        return Object.values(object);
                    }},
                    pick: function(object, ...keys) {{
                        const result = {{}};
                        keys.flat().forEach(key => {{
                            if (key in object) {{
                                result[key] = object[key];
                            }}
                        }});
                        return result;
                    }},
                    omit: function(object, ...keys) {{
                        const result = {{ ...object }};
                        keys.flat().forEach(key => delete result[key]);
                        return result;
                    }},
                    
                    // String methods
                    capitalize: function(string) {{
                        return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
                    }},
                    upperCase: function(string) {{
                        return string.toUpperCase();
                    }},
                    lowerCase: function(string) {{
                        return string.toLowerCase();
                    }},
                    trim: function(string, chars) {{
                        if (chars === undefined) return string.trim();
                        const pattern = new RegExp(`^[${{chars}}]+|[${{chars}}]+$`, 'g');
                        return string.replace(pattern, '');
                    }},
                    startsWith: function(string, target, position = 0) {{
                        return string.startsWith(target, position);
                    }},
                    endsWith: function(string, target, position) {{
                        return string.endsWith(target, position);
                    }},
                    
                    // Utility methods
                    isArray: function(value) {{
                        return Array.isArray(value);
                    }},
                    isObject: function(value) {{
                        return value !== null && typeof value === 'object';
                    }},
                    isString: function(value) {{
                        return typeof value === 'string';
                    }},
                    isNumber: function(value) {{
                        return typeof value === 'number' && !isNaN(value);
                    }},
                    isBoolean: function(value) {{
                        return typeof value === 'boolean';
                    }},
                    isEmpty: function(value) {{
                        if (value == null) return true;
                        if (Array.isArray(value) || typeof value === 'string') {{
                            return value.length === 0;
                        }}
                        if (typeof value === 'object') {{
                            return Object.keys(value).length === 0;
                        }}
                        return false;
                    }},
                    clone: function(value) {{
                        if (value == null || typeof value !== 'object') return value;
                        return JSON.parse(JSON.stringify(value));
                    }},
                    cloneDeep: function(value) {{
                        if (value == null || typeof value !== 'object') return value;
                        return JSON.parse(JSON.stringify(value));
                    }},
                    random: function(min, max) {{
                        if (max === undefined) {{
                            max = min;
                            min = 0;
                        }}
                        return Math.floor(Math.random() * (max - min + 1)) + min;
                    }}
                }};
            }}
            
            if (moduleName === 'uuid') {{
                // Return uuid library for generating UUIDs
                const uuidV1Impl = function() {{
                    // Generate UUID v1 (timestamp-based)
                    const time = Date.now();
                    const clockSeq = Math.floor(Math.random() * 0x4000);
                    const node = Array.from({{length: 6}}, () => 
                        Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
                    ).join('');
                    
                    // Use >>> 0 to ensure unsigned 32-bit integer
                    const timeLow = ((time & 0xffffffff) >>> 0).toString(16).padStart(8, '0');
                    const timeMid = ((time / 0x100000000 >>> 0) & 0xffff).toString(16).padStart(4, '0');
                    const timeHigh = ((((time / 0x100000000 >>> 0) >> 16) & 0x0fff) | 0x1000).toString(16).padStart(4, '0');
                    const clkSeqHi = ((clockSeq >> 8) | 0x80).toString(16).padStart(2, '0');
                    const clkSeqLow = (clockSeq & 0xff).toString(16).padStart(2, '0');
                    
                    return `${{timeLow}}-${{timeMid}}-${{timeHigh}}-${{clkSeqHi}}${{clkSeqLow}}-${{node}}`;
                }};
                
                const uuidV4Impl = function() {{
                    // Generate UUID v4 (random)
                    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
                        const r = Math.random() * 16 | 0;
                        const v = c === 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    }});
                }};
                
                return {{
                    v1: uuidV1Impl,
                    v4: uuidV4Impl
                }};
            }}
            
            throw new Error(`Module not found: ${{moduleName}}`);
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
            'globals': context['globals'],
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
    
    def _handle_pending_requests(self, js_ctx: MiniRacer):
        """Execute any pending pm.sendRequest() calls and invoke their callbacks."""
        try:
            # Check if there are any pending requests
            has_requests = js_ctx.eval('typeof globalThis.__pendingRequests !== "undefined" && globalThis.__pendingRequests.length > 0')
            
            if not has_requests:
                return
            
            # Get pending requests
            requests_str = js_ctx.eval('JSON.stringify(globalThis.__pendingRequests.map(r => ({id: r.id, request: r.request})))')
            pending_requests = json.loads(requests_str)
            
            # Import ApiClient here to avoid circular imports
            from src.core.api_client import ApiClient
            api_client = ApiClient(timeout=30, verify_ssl=True)
            
            # Execute each request and call its callback
            for req_info in pending_requests:
                request_data = req_info['request']
                request_id = req_info['id']
                
                try:
                    # Normalize request data
                    url = request_data.get('url', '')
                    method = request_data.get('method', 'GET').upper()
                    headers = request_data.get('header', {})
                    body = None
                    
                    # Handle body
                    if 'body' in request_data:
                        body_data = request_data['body']
                        if isinstance(body_data, dict):
                            if body_data.get('mode') == 'raw':
                                body = body_data.get('raw', '')
                            elif 'raw' in body_data:
                                body = body_data['raw']
                        elif isinstance(body_data, str):
                            body = body_data
                    
                    # Execute the HTTP request
                    response = api_client.execute_request(
                        method=method,
                        url=url,
                        headers=headers,
                        body=body
                    )
                    
                    # Build response object for JavaScript
                    response_obj = {
                        'code': response.status_code,
                        'status': self._get_status_text(response.status_code),
                        'headers': response.headers,
                        'responseTime': int(response.elapsed_time * 1000),
                        'responseSize': response.size,
                        'text': lambda: response.text,
                        'json': lambda: response.json() if response.is_json() else None
                    }
                    
                    # Create JavaScript response object and call callback
                    response_json = json.dumps({
                        'code': response_obj['code'],
                        'status': response_obj['status'],
                        'headers': response_obj['headers'],
                        'responseTime': response_obj['responseTime'],
                        'responseSize': response_obj['responseSize'],
                        'body': response.text
                    })
                    
                    # Build and execute callback
                    callback_code = f"""
                    (function() {{
                        const requestObj = globalThis.__pendingRequests.find(r => r.id === '{request_id}');
                        if (requestObj && requestObj.callback) {{
                            const responseData = {response_json};
                            const responseObj = {{
                                code: responseData.code,
                                status: responseData.status,
                                headers: responseData.headers,
                                responseTime: responseData.responseTime,
                                responseSize: responseData.responseSize,
                                text: function() {{ return responseData.body; }},
                                json: function() {{ 
                                    try {{
                                        return JSON.parse(responseData.body);
                                    }} catch(e) {{
                                        return null;
                                    }}
                                }}
                            }};
                            requestObj.callback(null, responseObj);
                        }}
                    }})();
                    """
                    js_ctx.eval(callback_code)
                    
                except Exception as e:
                    # Call callback with error
                    error_msg = str(e).replace("'", "\\'")
                    error_callback = f"""
                    (function() {{
                        const requestObj = globalThis.__pendingRequests.find(r => r.id === '{request_id}');
                        if (requestObj && requestObj.callback) {{
                            requestObj.callback(new Error('{error_msg}'), null);
                        }}
                    }})();
                    """
                    js_ctx.eval(error_callback)
        
        except Exception as e:
            # Silently handle errors in sendRequest processing
            # to avoid breaking the main script execution
            pass
    
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

