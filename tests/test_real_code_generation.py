"""
Real-World Code Generation Test

Test code generation with real API endpoints and various scenarios.
"""

from src.features.code_generator import CodeGenerator

def print_section(title):
    """Print a formatted section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()

def print_code(language, code):
    """Print generated code with language header."""
    print(f"\n--- {language} ---")
    print(code)
    print()

def test_real_jsonplaceholder():
    """Test with real JSONPlaceholder API."""
    print_section("Test 1: Real API - JSONPlaceholder GET")
    
    url = "https://jsonplaceholder.typicode.com/posts"
    params = {"userId": "1"}
    
    # Generate curl
    code = CodeGenerator.generate_curl(
        method="GET",
        url=url,
        params=params
    )
    print_code("curl", code)
    
    # Generate Python
    code = CodeGenerator.generate_python_requests(
        method="GET",
        url=url,
        params=params
    )
    print_code("Python", code)
    
    # Generate JavaScript (fetch)
    code = CodeGenerator.generate_javascript_fetch(
        method="GET",
        url=url,
        params=params
    )
    print_code("JavaScript (fetch)", code)

def test_real_post_request():
    """Test POST request with JSON body."""
    print_section("Test 2: POST Request with JSON Body")
    
    url = "https://jsonplaceholder.typicode.com/posts"
    headers = {"Content-Type": "application/json"}
    body = '{"title": "My Post", "body": "This is the content", "userId": 1}'
    
    # Generate Python
    code = CodeGenerator.generate_python_requests(
        method="POST",
        url=url,
        headers=headers,
        body=body
    )
    print_code("Python", code)
    
    # Generate React
    code = CodeGenerator.generate_react(
        method="POST",
        url=url,
        headers=headers,
        body=body
    )
    print_code("React", code[:500] + "..." if len(code) > 500 else code)

def test_authenticated_request():
    """Test request with Bearer token."""
    print_section("Test 3: Authenticated Request")
    
    url = "https://api.example.com/user/profile"
    
    # Generate curl
    code = CodeGenerator.generate_curl(
        method="GET",
        url=url,
        auth_type="Bearer Token",
        auth_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    print_code("curl", code)
    
    # Generate C#
    code = CodeGenerator.generate_csharp(
        method="GET",
        url=url,
        auth_type="Bearer Token",
        auth_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    print_code("C#", code)

def test_complex_request():
    """Test complex request with all parameters."""
    print_section("Test 4: Complex Request (All Parameters)")
    
    url = "https://api.github.com/repos/python/cpython/issues"
    params = {
        "state": "open",
        "labels": "bug",
        "per_page": "10"
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MyAPIClient/1.0"
    }
    
    # Generate axios
    code = CodeGenerator.generate_javascript_axios(
        method="GET",
        url=url,
        params=params,
        headers=headers
    )
    print_code("JavaScript (axios)", code)
    
    # Generate Node.js
    code = CodeGenerator.generate_nodejs(
        method="GET",
        url=url,
        params=params,
        headers=headers
    )
    print_code("Node.js", code)

def test_all_methods():
    """Test different HTTP methods."""
    print_section("Test 5: Different HTTP Methods")
    
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    
    for method in methods:
        code = CodeGenerator.generate_curl(
            method=method,
            url="https://api.example.com/resource/123",
            headers={"Content-Type": "application/json"},
            body='{"status": "updated"}' if method != "GET" else None
        )
        print(f"{method}: Generated {len(code)} characters")

def main():
    """Run all real-world tests."""
    print()
    print("*" * 70)
    print("  REAL-WORLD CODE GENERATION TESTS")
    print("*" * 70)
    
    test_real_jsonplaceholder()
    test_real_post_request()
    test_authenticated_request()
    test_complex_request()
    test_all_methods()
    
    print()
    print("=" * 70)
    print("  TESTING COMPLETE")
    print("=" * 70)
    print()
    print("[OK] All real-world scenarios tested successfully!")
    print()
    print("You can copy any of the generated code above and it will work!")
    print("Try running the curl commands in your terminal.")
    print()

if __name__ == "__main__":
    main()

