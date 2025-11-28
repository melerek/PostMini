"""
End-to-end integration test for body type support.

Tests the complete flow: Database → Postman Import → Export → Reimport
"""

import pytest
import json
import os
import tempfile
from src.core.database import DatabaseManager
from src.features.postman_converter import PostmanConverter
from src.features.collection_io import CollectionExporter, CollectionImporter


class TestBodyTypeIntegration:
    """Test complete body type integration."""
    
    @pytest.fixture
    def test_db(self):
        """Create a temporary test database."""
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        yield db
        db.close()
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_postman_import_preserves_body_types(self, test_db):
        """Test that importing a Postman collection preserves all body types."""
        # Create Postman collection with different body types
        postman_collection = {
            "info": {
                "name": "Body Type Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Raw JSON Request",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/json",
                        "body": {
                            "mode": "raw",
                            "raw": '{"name": "test", "value": 123}'
                        },
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ]
                    }
                },
                {
                    "name": "Form Data Request",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/upload",
                        "body": {
                            "mode": "formdata",
                            "formdata": [
                                {"key": "username", "value": "admin", "type": "text"},
                                {"key": "file", "value": "test.txt", "type": "text"}
                            ]
                        }
                    }
                },
                {
                    "name": "URL Encoded Request",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/login",
                        "body": {
                            "mode": "urlencoded",
                            "urlencoded": [
                                {"key": "grant_type", "value": "password"},
                                {"key": "username", "value": "user@example.com"}
                            ]
                        }
                    }
                },
                {
                    "name": "No Body Request",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/users"
                    }
                }
            ]
        }
        
        # Import collection
        internal_format = PostmanConverter.from_postman_format(postman_collection)
        
        # Create collection in database
        collection_id = test_db.create_collection("Body Type Test Collection")
        
        # Import all requests
        for request_data in internal_format['collection']['requests']:
            test_db.create_request(
                collection_id=collection_id,
                name=request_data['name'],
                method=request_data['method'],
                url=request_data['url'],
                headers=request_data.get('headers', {}),
                body=request_data.get('body', ''),
                body_type=request_data.get('body_type', 'raw')
            )
        
        # Verify requests in database
        requests = test_db.get_requests_by_collection(collection_id)
        assert len(requests) == 4
        
        # Check each request has correct body_type
        by_name = {r['name']: r for r in requests}
        
        assert by_name['Raw JSON Request']['body_type'] == 'raw'
        assert by_name['Form Data Request']['body_type'] == 'formdata'
        assert by_name['URL Encoded Request']['body_type'] == 'urlencoded'
        assert by_name['No Body Request']['body_type'] == 'raw'  # Default
        
        # Verify body content is preserved
        assert '{"name": "test"' in by_name['Raw JSON Request']['body']
        form_body = json.loads(by_name['Form Data Request']['body'])
        assert form_body['username'] == 'admin'
        assert form_body['file'] == 'test.txt'
    
    def test_export_import_roundtrip(self, test_db):
        """Test exporting and reimporting preserves body types."""
        # Create collection with different body types
        collection_id = test_db.create_collection("Roundtrip Test")
        
        test_db.create_request(
            collection_id=collection_id,
            name="JSON Request",
            method="POST",
            url="https://api.example.com/json",
            body='{"key": "value"}',
            body_type='raw'
        )
        
        test_db.create_request(
            collection_id=collection_id,
            name="Form Data Request",
            method="POST",
            url="https://api.example.com/form",
            body='{"field1": "value1", "field2": "value2"}',
            body_type='formdata'
        )
        
        test_db.create_request(
            collection_id=collection_id,
            name="URL Encoded Request",
            method="POST",
            url="https://api.example.com/url",
            body='{"grant_type": "password"}',
            body_type='x-www-form-urlencoded'
        )
        
        # Export collection
        exporter = CollectionExporter(test_db)
        export_data = exporter.export_collection(collection_id)
        
        # Verify export includes body_type
        assert all('body_type' in req for req in export_data['collection']['requests'])
        
        # Create new collection for reimport
        collection_id_2 = test_db.create_collection("Reimported Collection")
        
        # Import into new collection
        importer = CollectionImporter(test_db)
        import_data = export_data.copy()
        import_data['collection']['name'] = "Reimported Collection"
        
        # Manually import requests (simulating CollectionImporter logic)
        for req in import_data['collection']['requests']:
            test_db.create_request(
                collection_id=collection_id_2,
                name=req['name'],
                method=req['method'],
                url=req['url'],
                body=req.get('body', ''),
                body_type=req.get('body_type', 'raw')
            )
        
        # Verify reimported requests have correct body types
        reimported_requests = test_db.get_requests_by_collection(collection_id_2)
        assert len(reimported_requests) == 3
        
        by_name = {r['name']: r for r in reimported_requests}
        assert by_name['JSON Request']['body_type'] == 'raw'
        assert by_name['Form Data Request']['body_type'] == 'formdata'
        assert by_name['URL Encoded Request']['body_type'] == 'x-www-form-urlencoded'
    
    def test_default_body_type_for_legacy_data(self, test_db):
        """Test that legacy requests without body_type get 'raw' default."""
        # Create collection
        collection_id = test_db.create_collection("Legacy Collection")
        
        # Create request without explicitly setting body_type (simulates old data)
        request_id = test_db.create_request(
            collection_id=collection_id,
            name="Legacy Request",
            method="POST",
            url="https://api.example.com/test",
            body='{"test": "data"}'
        )
        
        # Retrieve request
        request = test_db.get_request(request_id)
        
        # Should have default 'raw' body_type
        assert request['body_type'] == 'raw'
    
    def test_postman_content_type_headers_set(self, test_db):
        """Test that Postman import auto-sets Content-Type headers."""
        postman_data = {
            "info": {
                "name": "Header Test",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Form Data",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/form",
                        "body": {
                            "mode": "formdata",
                            "formdata": [
                                {"key": "field1", "value": "value1"}
                            ]
                        }
                    }
                },
                {
                    "name": "URL Encoded",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/url",
                        "body": {
                            "mode": "urlencoded",
                            "urlencoded": [
                                {"key": "grant_type", "value": "password"}
                            ]
                        }
                    }
                }
            ]
        }
        
        # Import
        internal_format = PostmanConverter.from_postman_format(postman_data)
        requests = internal_format['collection']['requests']
        
        # Check Content-Type headers are set
        form_request = next(r for r in requests if r['name'] == 'Form Data')
        url_request = next(r for r in requests if r['name'] == 'URL Encoded')
        
        assert form_request['headers']['Content-Type'] == 'multipart/form-data'
        assert url_request['headers']['Content-Type'] == 'application/x-www-form-urlencoded'
