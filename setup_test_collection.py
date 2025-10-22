import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('api_client.db')
cursor = conn.cursor()

# Create collection
cursor.execute("INSERT INTO collections (name) VALUES (?)", ("QA Demo with Working Tests",))
collection_id = cursor.lastrowid

# Create request 1: Get All Posts
cursor.execute("""
    INSERT INTO requests (collection_id, name, method, url, params, headers, body, auth_type, auth_token, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    collection_id,
    "1. Get All Posts",
    "GET",
    "https://jsonplaceholder.typicode.com/posts",
    "{}",
    "{}",
    "",
    "None",
    "",
    "Simple GET request with 2 tests"
))
request1_id = cursor.lastrowid

# Add tests for request 1
cursor.execute("""
    INSERT INTO test_assertions (request_id, assertion_type, operator, expected_value, enabled)
    VALUES (?, ?, ?, ?, ?)
""", (request1_id, "status_code", "equals", "200", 1))

cursor.execute("""
    INSERT INTO test_assertions (request_id, assertion_type, operator, expected_value, enabled)
    VALUES (?, ?, ?, ?, ?)
""", (request1_id, "response_time", "less_than", "3000", 1))

# Create request 2: Get Single Post
cursor.execute("""
    INSERT INTO requests (collection_id, name, method, url, params, headers, body, auth_type, auth_token, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    collection_id,
    "2. Get Single Post",
    "GET",
    "https://jsonplaceholder.typicode.com/posts/1",
    "{}",
    "{}",
    "",
    "None",
    "",
    "GET single post with 3 tests"
))
request2_id = cursor.lastrowid

# Add tests for request 2
cursor.execute("""
    INSERT INTO test_assertions (request_id, assertion_type, field, operator, expected_value, enabled)
    VALUES (?, ?, ?, ?, ?, ?)
""", (request2_id, "status_code", None, "equals", "200", 1))

cursor.execute("""
    INSERT INTO test_assertions (request_id, assertion_type, field, operator, expected_value, enabled)
    VALUES (?, ?, ?, ?, ?, ?)
""", (request2_id, "json_path", "id", "equals", "1", 1))

cursor.execute("""
    INSERT INTO test_assertions (request_id, assertion_type, field, operator, expected_value, enabled)
    VALUES (?, ?, ?, ?, ?, ?)
""", (request2_id, "json_path", "userId", "exists", "", 1))

# Create request 3: Get User
cursor.execute("""
    INSERT INTO requests (collection_id, name, method, url, params, headers, body, auth_type, auth_token, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    collection_id,
    "3. Get User Details",
    "GET",
    "https://jsonplaceholder.typicode.com/users/1",
    "{}",
    "{}",
    "",
    "None",
    "",
    "GET user with 3 tests for nested JSON"
))
request3_id = cursor.lastrowid

# Add tests for request 3
cursor.execute("""
    INSERT INTO test_assertions (request_id, assertion_type, field, operator, expected_value, enabled)
    VALUES (?, ?, ?, ?, ?, ?)
""", (request3_id, "status_code", None, "equals", "200", 1))

cursor.execute("""
    INSERT INTO test_assertions (request_id, assertion_type, field, operator, expected_value, enabled)
    VALUES (?, ?, ?, ?, ?, ?)
""", (request3_id, "json_path", "name", "exists", "", 1))

cursor.execute("""
    INSERT INTO test_assertions (request_id, assertion_type, field, operator, expected_value, enabled)
    VALUES (?, ?, ?, ?, ?, ?)
""", (request3_id, "json_path", "email", "exists", "", 1))

# Commit and close
conn.commit()
conn.close()

print("[SUCCESS] Test collection created successfully!")
print("")
print("   Collection: 'QA Demo with Working Tests'")
print("   Requests: 3")
print("   Total Tests: 8")
print("")
print("Now:")
print("1. Start (or restart) PostMini")
print("2. Find 'QA Test Demo' collection in the sidebar")
print("3. Right-click -> 'Run Tests'")
print("4. After tests complete, click 'Export HTML'")
print("5. Beautiful report opens in browser!")
print("")
print("All 8 tests should PASS!")

