"""
Test Postman Body Type Import Mapping

Verifies that Postman collection imports correctly map body types:
- Postman "urlencoded" → Our "x-www-form-urlencoded"
- Postman "formdata" → Our "form-data"
- Postman "raw" → Our "raw"
"""

import pytest
import json
from src.features.postman_converter import PostmanConverter


def test_postman_urlencoded_body_type_import():
    """Test that Postman 'urlencoded' mode is imported as 'x-www-form-urlencoded'."""
    postman_collection = {
        "info": {
            "_postman_id": "test-id",
            "name": "Test Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "/EVToken - ClientUser",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/x-www-form-urlencoded",
                            "type": "text"
                        }
                    ],
                    "body": {
                        "mode": "urlencoded",
                        "urlencoded": [
                            {
                                "key": "grant_type",
                                "value": "password",
                                "type": "text"
                            },
                            {
                                "key": "username",
                                "value": "Test170_1@test.com",
                                "type": "text"
                            },
                            {
                                "key": "password",
                                "value": "Password@123",
                                "type": "text"
                            }
                        ]
                    },
                    "url": {
                        "raw": "{{EnvironmentAddress}}/EVToken",
                        "host": ["{{EnvironmentAddress}}"],
                        "path": ["EVToken"]
                    }
                }
            }
        ]
    }
    
    # Convert from Postman format
    internal_format = PostmanConverter.from_postman_format(postman_collection)
    
    # Get the request
    requests = internal_format["collection"]["requests"]
    assert len(requests) == 1, "Should have 1 request"
    
    request = requests[0]
    
    # Verify body type is mapped correctly
    assert request["body_type"] == "x-www-form-urlencoded", \
        f"Expected body_type='x-www-form-urlencoded', got '{request['body_type']}'"
    
    # Verify body is stored as JSON
    body_dict = json.loads(request["body"])
    assert body_dict["grant_type"] == "password"
    assert body_dict["username"] == "Test170_1@test.com"
    assert body_dict["password"] == "Password@123"
    
    # Verify Content-Type header is preserved
    assert request["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    
    print("✅ Postman 'urlencoded' correctly imported as 'x-www-form-urlencoded'")


def test_postman_formdata_body_type_import():
    """Test that Postman 'formdata' mode is imported as 'form-data'."""
    postman_collection = {
        "info": {
            "_postman_id": "test-id",
            "name": "Test Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Upload File",
                "request": {
                    "method": "POST",
                    "header": [],
                    "body": {
                        "mode": "formdata",
                        "formdata": [
                            {
                                "key": "file",
                                "value": "document.pdf",
                                "type": "text"
                            },
                            {
                                "key": "description",
                                "value": "Test file",
                                "type": "text"
                            }
                        ]
                    },
                    "url": {
                        "raw": "{{baseUrl}}/upload",
                        "host": ["{{baseUrl}}"],
                        "path": ["upload"]
                    }
                }
            }
        ]
    }
    
    # Convert from Postman format
    internal_format = PostmanConverter.from_postman_format(postman_collection)
    
    # Get the request
    requests = internal_format["collection"]["requests"]
    assert len(requests) == 1, "Should have 1 request"
    
    request = requests[0]
    
    # Verify body type is mapped correctly
    assert request["body_type"] == "form-data", \
        f"Expected body_type='form-data', got '{request['body_type']}'"
    
    # Verify body is stored as JSON
    body_dict = json.loads(request["body"])
    assert body_dict["file"] == "document.pdf"
    assert body_dict["description"] == "Test file"
    
    # Verify Content-Type header is auto-added
    assert request["headers"]["Content-Type"] == "multipart/form-data"
    
    print("✅ Postman 'formdata' correctly imported as 'form-data'")


def test_postman_raw_body_type_import():
    """Test that Postman 'raw' mode is imported as 'raw'."""
    postman_collection = {
        "info": {
            "_postman_id": "test-id",
            "name": "Test Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Create User",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json",
                            "type": "text"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": '{"name": "John Doe", "email": "john@example.com"}'
                    },
                    "url": {
                        "raw": "{{baseUrl}}/users",
                        "host": ["{{baseUrl}}"],
                        "path": ["users"]
                    }
                }
            }
        ]
    }
    
    # Convert from Postman format
    internal_format = PostmanConverter.from_postman_format(postman_collection)
    
    # Get the request
    requests = internal_format["collection"]["requests"]
    assert len(requests) == 1, "Should have 1 request"
    
    request = requests[0]
    
    # Verify body type is mapped correctly
    assert request["body_type"] == "raw", \
        f"Expected body_type='raw', got '{request['body_type']}'"
    
    # Verify body is preserved as-is
    assert request["body"] == '{"name": "John Doe", "email": "john@example.com"}'
    
    # Verify Content-Type header is preserved
    assert request["headers"]["Content-Type"] == "application/json"
    
    print("✅ Postman 'raw' correctly imported as 'raw'")


def test_postman_urlencoded_export_import_roundtrip():
    """Test that x-www-form-urlencoded body type survives export/import roundtrip."""
    # Create internal format request with urlencoded body
    internal_request = {
        "name": "OAuth Token",
        "method": "POST",
        "url": "{{baseUrl}}/token",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "body": json.dumps({
            "grant_type": "password",
            "username": "user@example.com",
            "password": "secret"
        }),
        "body_type": "x-www-form-urlencoded",
        "params": None,
        "auth_type": "None",
        "auth_token": None,
        "pre_request_script": None,
        "post_response_script": None
    }
    
    internal_format = {
        "export_version": "1.0",
        "collection": {
            "name": "Test Collection",
            "description": "",
            "folders": [],
            "variables": [],
            "requests": [internal_request]
        }
    }
    
    # Convert to Postman format
    postman_format = PostmanConverter.to_postman_format(internal_format)
    
    # Verify Postman export has urlencoded mode
    postman_item = postman_format["item"][0]
    assert postman_item["request"]["body"]["mode"] == "urlencoded", \
        f"Expected Postman mode='urlencoded', got '{postman_item['request']['body']['mode']}'"
    
    # Verify urlencoded array structure
    urlencoded_items = postman_item["request"]["body"]["urlencoded"]
    assert len(urlencoded_items) == 3
    assert any(item["key"] == "grant_type" and item["value"] == "password" for item in urlencoded_items)
    
    # Convert back from Postman format
    imported_format = PostmanConverter.from_postman_format(postman_format)
    
    # Verify body type is preserved
    imported_request = imported_format["collection"]["requests"][0]
    assert imported_request["body_type"] == "x-www-form-urlencoded", \
        f"Expected body_type='x-www-form-urlencoded' after roundtrip, got '{imported_request['body_type']}'"
    
    print("✅ x-www-form-urlencoded survives export/import roundtrip")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
