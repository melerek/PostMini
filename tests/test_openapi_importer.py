"""
Tests for OpenAPI/Swagger Import Feature

Tests the OpenAPI spec parsing and collection generation.
"""

import pytest
import json
import yaml
from pathlib import Path
from src.features.openapi_importer import OpenAPIImporter, import_openapi_spec


class TestOpenAPIImporter:
    """Test OpenAPI/Swagger importer."""
    
    @pytest.fixture
    def openapi_30_spec(self, tmp_path):
        """Create a sample OpenAPI 3.0 spec file."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Sample API",
                "version": "1.0.0",
                "description": "A sample API for testing"
            },
            "servers": [
                {"url": "https://api.example.com/v1"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "description": "Get all users",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    },
                    "post": {
                        "summary": "Create user",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Created"}
                        }
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "Get user",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    },
                    "delete": {
                        "summary": "Delete user",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "204": {"description": "No content"}
                        }
                    }
                }
            }
        }
        
        spec_file = tmp_path / "openapi.json"
        with open(spec_file, 'w') as f:
            json.dump(spec, f)
        
        return spec_file
    
    @pytest.fixture
    def swagger_20_spec(self, tmp_path):
        """Create a sample Swagger 2.0 spec file."""
        spec = {
            "swagger": "2.0",
            "info": {
                "title": "Legacy API",
                "version": "2.0.0"
            },
            "host": "api.legacy.com",
            "basePath": "/api",
            "schemes": ["https"],
            "paths": {
                "/products": {
                    "get": {
                        "summary": "List products",
                        "parameters": [
                            {
                                "name": "category",
                                "in": "query",
                                "type": "string"
                            }
                        ],
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            }
        }
        
        spec_file = tmp_path / "swagger.yaml"
        with open(spec_file, 'w') as f:
            yaml.dump(spec, f)
        
        return spec_file
    
    def test_load_json_spec(self, openapi_30_spec):
        """Test loading JSON spec file."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        assert importer.spec is not None
        assert 'openapi' in importer.spec
    
    def test_load_yaml_spec(self, swagger_20_spec):
        """Test loading YAML spec file."""
        importer = OpenAPIImporter(str(swagger_20_spec))
        assert importer.spec is not None
        assert 'swagger' in importer.spec
    
    def test_detect_openapi_30_version(self, openapi_30_spec):
        """Test detecting OpenAPI 3.0 version."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        assert importer.version == '3.0'
    
    def test_detect_swagger_20_version(self, swagger_20_spec):
        """Test detecting Swagger 2.0 version."""
        importer = OpenAPIImporter(str(swagger_20_spec))
        assert importer.version == '2.0'
    
    def test_get_base_url_openapi_30(self, openapi_30_spec):
        """Test getting base URL from OpenAPI 3.0 spec."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        base_url = importer.get_base_url()
        assert base_url == "https://api.example.com/v1"
    
    def test_get_base_url_swagger_20(self, swagger_20_spec):
        """Test getting base URL from Swagger 2.0 spec."""
        importer = OpenAPIImporter(str(swagger_20_spec))
        base_url = importer.get_base_url()
        assert base_url == "https://api.legacy.com/api"
    
    def test_import_collection(self, openapi_30_spec):
        """Test importing OpenAPI spec as collection."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        collection = importer.import_to_collection()
        
        assert collection['name'] == 'Sample API'
        assert collection['description'] == 'A sample API for testing'
        assert collection['version'] == '1.0.0'
        assert collection['base_url'] == 'https://api.example.com/v1'
        assert len(collection['requests']) == 4  # GET /users, POST /users, GET /users/{id}, DELETE /users/{id}
    
    def test_create_get_request(self, openapi_30_spec):
        """Test creating GET request from OpenAPI operation."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        collection = importer.import_to_collection()
        
        # Find GET /users request
        get_users = next(r for r in collection['requests'] if r['method'] == 'GET' and '/users/{id}' not in r['url'])
        
        assert get_users['name'] == 'List users'
        assert get_users['description'] == 'Get all users'
        assert get_users['method'] == 'GET'
        assert 'limit' in get_users['params']
    
    def test_create_post_request(self, openapi_30_spec):
        """Test creating POST request with body."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        collection = importer.import_to_collection()
        
        # Find POST /users request
        post_users = next(r for r in collection['requests'] if r['method'] == 'POST')
        
        assert post_users['name'] == 'Create user'
        assert post_users['method'] == 'POST'
        assert post_users['body'] != ''
        
        # Body should be valid JSON
        body_data = json.loads(post_users['body'])
        assert 'name' in body_data
        assert 'email' in body_data
    
    def test_create_delete_request(self, openapi_30_spec):
        """Test creating DELETE request."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        collection = importer.import_to_collection()
        
        # Find DELETE /users/{id} request
        delete_user = next(r for r in collection['requests'] if r['method'] == 'DELETE')
        
        assert delete_user['name'] == 'Delete user'
        assert delete_user['method'] == 'DELETE'
        assert '/users/{id}' in delete_user['url']
    
    def test_generate_example_from_object_schema(self, openapi_30_spec):
        """Test generating example from object schema."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "active": {"type": "boolean"}
            }
        }
        
        example = importer._generate_from_schema(schema)
        assert isinstance(example, dict)
        assert 'name' in example
        assert 'age' in example
        assert 'active' in example
    
    def test_generate_example_from_array_schema(self, openapi_30_spec):
        """Test generating example from array schema."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        
        example = importer._generate_from_schema(schema)
        assert isinstance(example, list)
        assert len(example) == 1
    
    def test_generate_example_from_string_schema(self, openapi_30_spec):
        """Test generating example from string schema."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        
        # String with email format
        schema = {"type": "string", "format": "email"}
        example = importer._generate_from_schema(schema)
        assert '@' in example
        
        # String with UUID format
        schema = {"type": "string", "format": "uuid"}
        example = importer._generate_from_schema(schema)
        assert len(example) == 36
    
    def test_generate_example_with_provided_example(self, openapi_30_spec):
        """Test using provided example in schema."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        
        schema = {
            "type": "string",
            "example": "custom_example"
        }
        
        example = importer._generate_from_schema(schema)
        assert example == "custom_example"
    
    def test_get_summary(self, openapi_30_spec):
        """Test getting API summary."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        summary = importer.get_summary()
        
        assert summary['title'] == 'Sample API'
        assert summary['version'] == '1.0.0'
        assert summary['openapi_version'] == '3.0'
        assert summary['endpoint_count'] == 4
        assert 'GET' in summary['methods']
        assert 'POST' in summary['methods']
        assert 'DELETE' in summary['methods']
    
    def test_custom_collection_name(self, openapi_30_spec):
        """Test importing with custom collection name."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        collection = importer.import_to_collection(collection_name="My Custom Collection")
        
        assert collection['name'] == 'My Custom Collection'
    
    def test_swagger_20_import(self, swagger_20_spec):
        """Test importing Swagger 2.0 spec."""
        importer = OpenAPIImporter(str(swagger_20_spec))
        collection = importer.import_to_collection()
        
        assert collection['name'] == 'Legacy API'
        assert len(collection['requests']) == 1
        assert collection['base_url'] == 'https://api.legacy.com/api'
    
    def test_convenience_function(self, openapi_30_spec):
        """Test convenience function for importing."""
        collection, summary = import_openapi_spec(str(openapi_30_spec))
        
        assert collection['name'] == 'Sample API'
        assert summary['endpoint_count'] == 4
    
    def test_file_not_found_error(self):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            OpenAPIImporter("non_existent_file.json")
    
    def test_invalid_spec_format(self, tmp_path):
        """Test error handling for invalid spec format."""
        invalid_spec = tmp_path / "invalid.json"
        with open(invalid_spec, 'w') as f:
            f.write("not valid json")
        
        with pytest.raises(ValueError):
            OpenAPIImporter(str(invalid_spec))
    
    def test_spec_without_version_field(self, tmp_path):
        """Test error handling for spec without version."""
        spec = {"info": {"title": "No Version"}}
        spec_file = tmp_path / "no_version.json"
        with open(spec_file, 'w') as f:
            json.dump(spec, f)
        
        with pytest.raises(ValueError):
            OpenAPIImporter(str(spec_file))
    
    def test_nested_object_schema(self, openapi_30_spec):
        """Test generating example from nested object schema."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
        
        example = importer._generate_from_schema(schema)
        assert isinstance(example, dict)
        assert 'user' in example
        assert 'name' in example['user']
        assert 'address' in example['user']
        assert 'street' in example['user']['address']
        assert 'city' in example['user']['address']
    
    def test_array_of_objects_schema(self, openapi_30_spec):
        """Test generating example from array of objects."""
        importer = OpenAPIImporter(str(openapi_30_spec))
        
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                }
            }
        }
        
        example = importer._generate_from_schema(schema)
        assert isinstance(example, list)
        assert len(example) == 1
        assert isinstance(example[0], dict)
        assert 'id' in example[0]
        assert 'name' in example[0]
    
    def test_security_bearer_token(self, tmp_path):
        """Test handling of bearer token security."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Secure API", "version": "1.0.0"},
            "servers": [{"url": "https://api.secure.com"}],
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer"
                    }
                }
            },
            "security": [{"bearerAuth": []}],
            "paths": {
                "/secure": {
                    "get": {
                        "summary": "Secure endpoint",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        spec_file = tmp_path / "secure.json"
        with open(spec_file, 'w') as f:
            json.dump(spec, f)
        
        importer = OpenAPIImporter(str(spec_file))
        collection = importer.import_to_collection()
        
        request = collection['requests'][0]
        assert request['auth_type'] == 'Bearer Token'
        assert 'Authorization' in request['headers']
    
    def test_security_api_key(self, tmp_path):
        """Test handling of API key security."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "API Key API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "components": {
                "securitySchemes": {
                    "apiKey": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    }
                }
            },
            "paths": {
                "/data": {
                    "get": {
                        "summary": "Get data",
                        "security": [{"apiKey": []}],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        spec_file = tmp_path / "apikey.json"
        with open(spec_file, 'w') as f:
            json.dump(spec, f)
        
        importer = OpenAPIImporter(str(spec_file))
        collection = importer.import_to_collection()
        
        request = collection['requests'][0]
        assert 'X-API-Key' in request['headers']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

