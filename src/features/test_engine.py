"""
Test Assertion Engine

This module evaluates test assertions against API responses.
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from src.core.api_client import ApiResponse


class TestAssertion:
    """Represents a single test assertion."""
    
    # Assertion Types
    TYPE_STATUS_CODE = "status_code"
    TYPE_RESPONSE_TIME = "response_time"
    TYPE_RESPONSE_SIZE = "response_size"
    TYPE_HEADER = "header"
    TYPE_BODY_CONTAINS = "body_contains"
    TYPE_BODY_EQUALS = "body_equals"
    TYPE_JSON_PATH = "json_path"
    TYPE_JSON_SCHEMA = "json_schema"
    
    # Operators
    OP_EQUALS = "equals"
    OP_NOT_EQUALS = "not_equals"
    OP_GREATER_THAN = "greater_than"
    OP_LESS_THAN = "less_than"
    OP_GREATER_EQUAL = "greater_equal"
    OP_LESS_EQUAL = "less_equal"
    OP_CONTAINS = "contains"
    OP_NOT_CONTAINS = "not_contains"
    OP_MATCHES_REGEX = "matches_regex"
    OP_EXISTS = "exists"
    OP_NOT_EXISTS = "not_exists"
    
    def __init__(self, assertion_id: int, assertion_type: str, operator: str,
                 field: Optional[str] = None, expected_value: Optional[str] = None,
                 enabled: bool = True):
        """Initialize test assertion."""
        self.id = assertion_id
        self.type = assertion_type
        self.operator = operator
        self.field = field
        self.expected_value = expected_value
        self.enabled = enabled
    
    def __repr__(self):
        return f"TestAssertion({self.type}, {self.operator}, {self.field}, {self.expected_value})"


class TestResult:
    """Represents the result of a test assertion."""
    
    def __init__(self, assertion: TestAssertion, passed: bool,
                 actual_value: Any = None, error_message: Optional[str] = None):
        """Initialize test result."""
        self.assertion = assertion
        self.passed = passed
        self.actual_value = actual_value
        self.error_message = error_message
    
    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"TestResult({status}, {self.assertion.type})"


class TestEngine:
    """
    Engine for evaluating test assertions against API responses.
    """
    
    @staticmethod
    def evaluate_assertion(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """
        Evaluate a single assertion against a response.
        
        Args:
            assertion: Test assertion to evaluate
            response: API response to test against
            
        Returns:
            TestResult with pass/fail status
        """
        if not assertion.enabled:
            return TestResult(assertion, True, None, "Assertion disabled")
        
        try:
            if assertion.type == TestAssertion.TYPE_STATUS_CODE:
                return TestEngine._check_status_code(assertion, response)
            
            elif assertion.type == TestAssertion.TYPE_RESPONSE_TIME:
                return TestEngine._check_response_time(assertion, response)
            
            elif assertion.type == TestAssertion.TYPE_RESPONSE_SIZE:
                return TestEngine._check_response_size(assertion, response)
            
            elif assertion.type == TestAssertion.TYPE_HEADER:
                return TestEngine._check_header(assertion, response)
            
            elif assertion.type == TestAssertion.TYPE_BODY_CONTAINS:
                return TestEngine._check_body_contains(assertion, response)
            
            elif assertion.type == TestAssertion.TYPE_BODY_EQUALS:
                return TestEngine._check_body_equals(assertion, response)
            
            elif assertion.type == TestAssertion.TYPE_JSON_PATH:
                return TestEngine._check_json_path(assertion, response)
            
            elif assertion.type == TestAssertion.TYPE_JSON_SCHEMA:
                return TestEngine._check_json_schema(assertion, response)
            
            else:
                return TestResult(assertion, False, None, f"Unknown assertion type: {assertion.type}")
        
        except Exception as e:
            return TestResult(assertion, False, None, f"Error evaluating assertion: {str(e)}")
    
    @staticmethod
    def _check_status_code(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """Check status code assertion."""
        actual = response.status_code
        expected = int(assertion.expected_value) if assertion.expected_value else None
        
        passed = TestEngine._compare_values(actual, expected, assertion.operator)
        
        return TestResult(assertion, passed, actual,
                         None if passed else f"Expected {assertion.operator} {expected}, got {actual}")
    
    @staticmethod
    def _check_response_time(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """Check response time assertion (in milliseconds)."""
        actual = response.elapsed_time * 1000  # Convert to ms
        expected = float(assertion.expected_value) if assertion.expected_value else None
        
        passed = TestEngine._compare_values(actual, expected, assertion.operator)
        
        return TestResult(assertion, passed, f"{actual:.2f}ms",
                         None if passed else f"Expected {assertion.operator} {expected}ms, got {actual:.2f}ms")
    
    @staticmethod
    def _check_response_size(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """Check response size assertion (in bytes)."""
        actual = response.size
        expected = int(assertion.expected_value) if assertion.expected_value else None
        
        passed = TestEngine._compare_values(actual, expected, assertion.operator)
        
        return TestResult(assertion, passed, f"{actual} bytes",
                         None if passed else f"Expected {assertion.operator} {expected} bytes, got {actual} bytes")
    
    @staticmethod
    def _check_header(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """Check response header assertion."""
        header_name = assertion.field
        if not header_name:
            return TestResult(assertion, False, None, "Header name not specified")
        
        actual = response.headers.get(header_name)
        expected = assertion.expected_value
        
        if assertion.operator == TestAssertion.OP_EXISTS:
            passed = actual is not None
            return TestResult(assertion, passed, actual,
                             None if passed else f"Header '{header_name}' does not exist")
        
        elif assertion.operator == TestAssertion.OP_NOT_EXISTS:
            passed = actual is None
            return TestResult(assertion, passed, actual,
                             None if passed else f"Header '{header_name}' exists")
        
        else:
            if actual is None:
                return TestResult(assertion, False, None, f"Header '{header_name}' does not exist")
            
            passed = TestEngine._compare_values(actual, expected, assertion.operator)
            return TestResult(assertion, passed, actual,
                             None if passed else f"Expected {assertion.operator} '{expected}', got '{actual}'")
    
    @staticmethod
    def _check_body_contains(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """Check if response body contains expected text."""
        actual = response.text
        expected = assertion.expected_value
        
        if assertion.operator == TestAssertion.OP_CONTAINS:
            passed = expected in actual if expected else False
            return TestResult(assertion, passed, f"Body length: {len(actual)}",
                             None if passed else f"Body does not contain '{expected}'")
        
        elif assertion.operator == TestAssertion.OP_NOT_CONTAINS:
            passed = expected not in actual if expected else True
            return TestResult(assertion, passed, f"Body length: {len(actual)}",
                             None if passed else f"Body contains '{expected}'")
        
        else:
            return TestResult(assertion, False, actual, f"Invalid operator for body_contains: {assertion.operator}")
    
    @staticmethod
    def _check_body_equals(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """Check if response body equals expected text."""
        actual = response.text
        expected = assertion.expected_value
        
        passed = TestEngine._compare_values(actual, expected, assertion.operator)
        
        return TestResult(assertion, passed, f"{actual[:100]}..." if len(actual) > 100 else actual,
                         None if passed else f"Body does not equal expected value")
    
    @staticmethod
    def _check_json_path(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """Check JSON path value in response."""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return TestResult(assertion, False, None, "Response is not valid JSON")
        
        path = assertion.field
        if not path:
            return TestResult(assertion, False, None, "JSON path not specified")
        
        # Extract value using simple path notation (e.g., "user.name", "items[0].id")
        try:
            actual = TestEngine._extract_json_value(data, path)
        except Exception as e:
            return TestResult(assertion, False, None, f"Failed to extract path '{path}': {str(e)}")
        
        expected = assertion.expected_value
        
        if assertion.operator == TestAssertion.OP_EXISTS:
            passed = actual is not None
            return TestResult(assertion, passed, actual,
                             None if passed else f"Path '{path}' does not exist")
        
        elif assertion.operator == TestAssertion.OP_NOT_EXISTS:
            passed = actual is None
            return TestResult(assertion, passed, actual,
                             None if passed else f"Path '{path}' exists")
        
        else:
            # Convert expected value to same type as actual if possible
            if expected and actual is not None:
                try:
                    if isinstance(actual, bool):
                        expected = expected.lower() == 'true'
                    elif isinstance(actual, int):
                        expected = int(expected)
                    elif isinstance(actual, float):
                        expected = float(expected)
                except (ValueError, AttributeError):
                    pass
            
            passed = TestEngine._compare_values(actual, expected, assertion.operator)
            return TestResult(assertion, passed, str(actual),
                             None if passed else f"Expected {assertion.operator} '{expected}', got '{actual}'")
    
    @staticmethod
    def _check_json_schema(assertion: TestAssertion, response: ApiResponse) -> TestResult:
        """Check if response matches JSON schema."""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return TestResult(assertion, False, None, "Response is not valid JSON")
        
        # Simple schema validation (can be enhanced with jsonschema library)
        # For now, just check if expected fields exist
        expected_schema = assertion.expected_value
        if not expected_schema:
            return TestResult(assertion, False, None, "Schema not specified")
        
        try:
            schema = json.loads(expected_schema)
            errors = TestEngine._validate_simple_schema(data, schema)
            
            if errors:
                return TestResult(assertion, False, None, f"Schema validation failed: {', '.join(errors)}")
            else:
                return TestResult(assertion, True, "Schema valid")
        
        except json.JSONDecodeError:
            return TestResult(assertion, False, None, "Invalid JSON schema")
        except Exception as e:
            return TestResult(assertion, False, None, f"Schema validation error: {str(e)}")
    
    @staticmethod
    def _compare_values(actual: Any, expected: Any, operator: str) -> bool:
        """Compare two values using the specified operator."""
        if operator == TestAssertion.OP_EQUALS:
            return actual == expected
        
        elif operator == TestAssertion.OP_NOT_EQUALS:
            return actual != expected
        
        elif operator == TestAssertion.OP_GREATER_THAN:
            return actual > expected
        
        elif operator == TestAssertion.OP_LESS_THAN:
            return actual < expected
        
        elif operator == TestAssertion.OP_GREATER_EQUAL:
            return actual >= expected
        
        elif operator == TestAssertion.OP_LESS_EQUAL:
            return actual <= expected
        
        elif operator == TestAssertion.OP_CONTAINS:
            return expected in str(actual) if expected else False
        
        elif operator == TestAssertion.OP_NOT_CONTAINS:
            return expected not in str(actual) if expected else True
        
        elif operator == TestAssertion.OP_MATCHES_REGEX:
            try:
                return bool(re.search(str(expected), str(actual)))
            except re.error:
                return False
        
        else:
            return False
    
    @staticmethod
    def _extract_json_value(data: Any, path: str) -> Any:
        """Extract value from JSON using dot notation path."""
        parts = path.split('.')
        current = data
        
        for part in parts:
            # Handle array indexing (e.g., "items[0]")
            if '[' in part and ']' in part:
                field = part[:part.index('[')]
                index = int(part[part.index('[') + 1:part.index(']')])
                
                if field:
                    current = current[field]
                
                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
                
                if current is None:
                    return None
        
        return current
    
    @staticmethod
    def _validate_simple_schema(data: Any, schema: Dict) -> List[str]:
        """Simple JSON schema validation."""
        errors = []
        
        if 'type' in schema:
            expected_type = schema['type']
            actual_type = type(data).__name__
            
            type_map = {
                'string': 'str',
                'number': ('int', 'float'),
                'integer': 'int',
                'boolean': 'bool',
                'array': 'list',
                'object': 'dict',
                'null': 'NoneType'
            }
            
            expected = type_map.get(expected_type, expected_type)
            if isinstance(expected, tuple):
                if actual_type not in expected:
                    errors.append(f"Type mismatch: expected {expected_type}, got {actual_type}")
            else:
                if actual_type != expected:
                    errors.append(f"Type mismatch: expected {expected_type}, got {actual_type}")
        
        if 'properties' in schema and isinstance(data, dict):
            for prop, prop_schema in schema['properties'].items():
                if 'required' in schema and prop in schema['required']:
                    if prop not in data:
                        errors.append(f"Required property '{prop}' is missing")
        
        return errors
    
    @staticmethod
    def evaluate_all(assertions: List[TestAssertion], response: ApiResponse) -> List[TestResult]:
        """
        Evaluate all assertions against a response.
        
        Args:
            assertions: List of test assertions
            response: API response to test
            
        Returns:
            List of test results
        """
        results = []
        for assertion in assertions:
            result = TestEngine.evaluate_assertion(assertion, response)
            results.append(result)
        return results
    
    @staticmethod
    def get_summary(results: List[TestResult]) -> Dict:
        """
        Get summary of test results.
        
        Args:
            results: List of test results
            
        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate
        }

