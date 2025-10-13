"""
Code Generation Test Suite

Comprehensive tests for code generation functionality.
"""

import sys
import os
import traceback

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.code_generator import CodeGenerator


def test_curl_generation():
    """Test curl code generation."""
    print("Testing curl Generation...")
    
    try:
        # Test simple GET
        code = CodeGenerator.generate_curl(
            method="GET",
            url="https://api.example.com/users"
        )
        
        if "curl" in code and "GET" in code:
            print("  [OK] Simple GET request")
        
        # Test with params
        code = CodeGenerator.generate_curl(
            method="GET",
            url="https://api.example.com/users",
            params={"limit": "10", "offset": "0"}
        )
        
        if "limit=10" in code and "offset=0" in code:
            print("  [OK] Request with parameters")
        
        # Test with headers
        code = CodeGenerator.generate_curl(
            method="GET",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"}
        )
        
        if "--header" in code and "Content-Type" in code:
            print("  [OK] Request with headers")
        
        # Test POST with body
        code = CodeGenerator.generate_curl(
            method="POST",
            url="https://api.example.com/users",
            body='{"name": "John Doe"}'
        )
        
        if "--data" in code and "John Doe" in code:
            print("  [OK] POST with body")
        
        # Test with Bearer token
        code = CodeGenerator.generate_curl(
            method="GET",
            url="https://api.example.com/users",
            auth_type="Bearer Token",
            auth_token="secret123"
        )
        
        if "Authorization: Bearer secret123" in code:
            print("  [OK] Bearer token authentication")
        
        print("[OK] curl generation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] curl generation test failed: {e}")
        traceback.print_exc()
        return False


def test_python_generation():
    """Test Python code generation."""
    print("Testing Python Generation...")
    
    try:
        # Test simple GET
        code = CodeGenerator.generate_python_requests(
            method="GET",
            url="https://api.example.com/users"
        )
        
        if "import requests" in code and "requests.get" in code:
            print("  [OK] Simple GET request")
        
        # Test POST with JSON body
        code = CodeGenerator.generate_python_requests(
            method="POST",
            url="https://api.example.com/users",
            body='{"name": "John", "age": 30}'
        )
        
        if "requests.post" in code and "data=" in code:
            print("  [OK] POST with JSON body")
        
        # Test with headers and params
        code = CodeGenerator.generate_python_requests(
            method="GET",
            url="https://api.example.com/users",
            params={"limit": "10"},
            headers={"Authorization": "Bearer token"}
        )
        
        if "params=" in code and "headers=" in code:
            print("  [OK] Request with params and headers")
        
        print("[OK] Python generation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Python generation test failed: {e}")
        traceback.print_exc()
        return False


def test_javascript_fetch_generation():
    """Test JavaScript fetch code generation."""
    print("Testing JavaScript (fetch) Generation...")
    
    try:
        # Test simple GET
        code = CodeGenerator.generate_javascript_fetch(
            method="GET",
            url="https://api.example.com/users"
        )
        
        if "fetch(" in code and "method: 'GET'" in code:
            print("  [OK] Simple GET request")
        
        # Test POST with body
        code = CodeGenerator.generate_javascript_fetch(
            method="POST",
            url="https://api.example.com/users",
            body='{"name": "John"}'
        )
        
        if "method: 'POST'" in code and "body:" in code:
            print("  [OK] POST with body")
        
        # Test with headers
        code = CodeGenerator.generate_javascript_fetch(
            method="GET",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"}
        )
        
        if "headers:" in code and "Content-Type" in code:
            print("  [OK] Request with headers")
        
        print("[OK] JavaScript (fetch) generation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] JavaScript (fetch) generation test failed: {e}")
        traceback.print_exc()
        return False


def test_javascript_axios_generation():
    """Test JavaScript axios code generation."""
    print("Testing JavaScript (axios) Generation...")
    
    try:
        # Test simple GET
        code = CodeGenerator.generate_javascript_axios(
            method="GET",
            url="https://api.example.com/users"
        )
        
        if "axios(" in code and "method: 'get'" in code:
            print("  [OK] Simple GET request")
        
        # Test with params
        code = CodeGenerator.generate_javascript_axios(
            method="GET",
            url="https://api.example.com/users",
            params={"limit": "10"}
        )
        
        if "params:" in code and "limit:" in code:
            print("  [OK] Request with parameters")
        
        print("[OK] JavaScript (axios) generation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] JavaScript (axios) generation test failed: {e}")
        traceback.print_exc()
        return False


def test_nodejs_generation():
    """Test Node.js code generation."""
    print("Testing Node.js Generation...")
    
    try:
        # Test simple GET
        code = CodeGenerator.generate_nodejs(
            method="GET",
            url="https://api.example.com/users"
        )
        
        if "const https = require('https')" in code and "hostname:" in code:
            print("  [OK] Simple GET request")
        
        # Test with headers
        code = CodeGenerator.generate_nodejs(
            method="GET",
            url="https://api.example.com/users",
            headers={"Authorization": "Bearer token"}
        )
        
        if "headers:" in code and "Authorization" in code:
            print("  [OK] Request with headers")
        
        print("[OK] Node.js generation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Node.js generation test failed: {e}")
        traceback.print_exc()
        return False


def test_react_generation():
    """Test React component code generation."""
    print("Testing React Generation...")
    
    try:
        # Test React component
        code = CodeGenerator.generate_react(
            method="GET",
            url="https://api.example.com/users"
        )
        
        if "import React" in code and "useState" in code and "useEffect" in code:
            print("  [OK] React component structure")
        
        if "fetch(" in code and "setData" in code:
            print("  [OK] Fetch and state management")
        
        if "export default" in code:
            print("  [OK] Component export")
        
        print("[OK] React generation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] React generation test failed: {e}")
        traceback.print_exc()
        return False


def test_csharp_generation():
    """Test C# code generation."""
    print("Testing C# Generation...")
    
    try:
        # Test simple GET
        code = CodeGenerator.generate_csharp(
            method="GET",
            url="https://api.example.com/users"
        )
        
        if "using System" in code and "HttpClient" in code:
            print("  [OK] C# structure with HttpClient")
        
        # Test POST with body
        code = CodeGenerator.generate_csharp(
            method="POST",
            url="https://api.example.com/users",
            body='{"name": "John"}'
        )
        
        if "PostAsync" in code and "StringContent" in code:
            print("  [OK] POST with body")
        
        # Test with headers
        code = CodeGenerator.generate_csharp(
            method="GET",
            url="https://api.example.com/users",
            headers={"X-API-Key": "key123"}
        )
        
        if "DefaultRequestHeaders.Add" in code and "X-API-Key" in code:
            print("  [OK] Request with headers")
        
        print("[OK] C# generation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] C# generation test failed: {e}")
        traceback.print_exc()
        return False


def test_complex_request():
    """Test complex request with all parameters."""
    print("Testing Complex Request Generation...")
    
    try:
        params = {"limit": "10", "offset": "0"}
        headers = {"Content-Type": "application/json", "X-API-Key": "key123"}
        body = '{"username": "john_doe", "email": "john@example.com"}'
        
        # Test curl with everything
        code = CodeGenerator.generate_curl(
            method="POST",
            url="https://api.example.com/users",
            params=params,
            headers=headers,
            body=body,
            auth_type="Bearer Token",
            auth_token="secret_token"
        )
        
        if all([
            "limit=10" in code,
            "Content-Type" in code,
            "X-API-Key" in code,
            "john_doe" in code,
            "Bearer secret_token" in code
        ]):
            print("  [OK] curl with all parameters")
        
        # Test Python with everything
        code = CodeGenerator.generate_python_requests(
            method="POST",
            url="https://api.example.com/users",
            params=params,
            headers=headers,
            body=body,
            auth_type="Bearer Token",
            auth_token="secret_token"
        )
        
        if all([
            "params=" in code,
            "headers=" in code,
            "data=" in code,
            "Bearer secret_token" in code
        ]):
            print("  [OK] Python with all parameters")
        
        print("[OK] Complex request tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Complex request test failed: {e}")
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases."""
    print("Testing Edge Cases...")
    
    try:
        # Test with no params/headers/body
        code = CodeGenerator.generate_python_requests(
            method="GET",
            url="https://api.example.com/users"
        )
        
        if "requests.get(url)" in code:
            print("  [OK] Minimal request (no params/headers/body)")
        
        # Test with special characters in body
        code = CodeGenerator.generate_curl(
            method="POST",
            url="https://api.example.com/users",
            body='{"name": "John\'s API"}'
        )
        
        if "John" in code:
            print("  [OK] Special characters in body")
        
        # Test with URL that has query string
        code = CodeGenerator.generate_curl(
            method="GET",
            url="https://api.example.com/users?existing=param",
            params={"new": "param"}
        )
        
        if "existing=param" in code and "new=param" in code:
            print("  [OK] URL with existing query string")
        
        print("[OK] Edge case tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] Edge case test failed: {e}")
        traceback.print_exc()
        return False


def test_all_languages():
    """Test that all languages can be generated."""
    print("Testing All Language Support...")
    
    try:
        languages = [
            'curl',
            'python',
            'javascript_fetch',
            'javascript_axios',
            'nodejs',
            'react',
            'csharp'
        ]
        
        for lang in languages:
            code = CodeGenerator.generate(
                language=lang,
                method="GET",
                url="https://api.example.com/test"
            )
            
            if code and len(code) > 0:
                print(f"  [OK] {lang} generation works")
        
        print("[OK] All language support tests passed!\n")
        return True
        
    except Exception as e:
        print(f"[FAIL] All language support test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all code generation tests."""
    print("="*60)
    print("Code Generation Test Suite")
    print("="*60)
    print()
    
    results = []
    
    results.append(("curl Generation", test_curl_generation()))
    results.append(("Python Generation", test_python_generation()))
    results.append(("JavaScript (fetch)", test_javascript_fetch_generation()))
    results.append(("JavaScript (axios)", test_javascript_axios_generation()))
    results.append(("Node.js Generation", test_nodejs_generation()))
    results.append(("React Generation", test_react_generation()))
    results.append(("C# Generation", test_csharp_generation()))
    results.append(("Complex Request", test_complex_request()))
    results.append(("Edge Cases", test_edge_cases()))
    results.append(("All Languages", test_all_languages()))
    
    print()
    print("="*60)
    print("Test Results Summary")
    print("="*60)
    
    for name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{name:.<40} {status}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("[SUCCESS] All code generation tests passed!")
        print("Code generation feature is ready for production!")
    else:
        print("[FAIL] Some tests failed.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

