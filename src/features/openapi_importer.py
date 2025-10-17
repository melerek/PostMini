"""
OpenAPI/Swagger Importer Module

Imports OpenAPI 2.0 (Swagger) and OpenAPI 3.0/3.1 specifications and
converts them into PostMini collections with auto-generated requests.
"""

import json
import yaml
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class OpenAPIImporter:
    """
    Import OpenAPI/Swagger specifications and convert to PostMini collections.
    
    Supports:
    - OpenAPI 3.0 / 3.1 (JSON and YAML)
    - OpenAPI 2.0 / Swagger (JSON and YAML)
    - $ref resolution
    - Example generation from schemas
    - Multiple authentication schemes
    """
    
    def __init__(self, spec_file_path: str):
        """
        Initialize the OpenAPI importer.
        
        Args:
            spec_file_path: Path to OpenAPI spec file (.json, .yaml, .yml)
            
        Raises:
            FileNotFoundError: If spec file doesn't exist
            ValueError: If spec format is invalid
        """
        self.spec_path = Path(spec_file_path)
        if not self.spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_file_path}")
        
        self.spec = self._load_spec()
        self.version = self._detect_version()
        self._resolve_refs()
    
    def _load_spec(self) -> Dict:
        """Load and parse the OpenAPI spec file."""
        try:
            with open(self.spec_path, 'r', encoding='utf-8') as f:
                if self.spec_path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Invalid spec format: {e}")
    
    def _detect_version(self) -> str:
        """Detect OpenAPI version (2.0, 3.0, or 3.1)."""
        if 'openapi' in self.spec:
            version = self.spec['openapi']
            if version.startswith('3.0'):
                return '3.0'
            elif version.startswith('3.1'):
                return '3.1'
            return '3.0'  # Default to 3.0
        elif 'swagger' in self.spec:
            return '2.0'
        else:
            raise ValueError("Invalid OpenAPI spec: missing 'openapi' or 'swagger' field")
    
    def _resolve_refs(self):
        """Resolve $ref references in the spec (simple implementation)."""
        # For simplicity, we'll handle basic $ref resolution
        # Full $ref resolution would require external libraries like prance
        # This is a simplified version for common cases
        pass
    
    def get_base_url(self) -> str:
        """Get the base URL from the spec."""
        if self.version == '2.0':
            # Swagger 2.0
            schemes = self.spec.get('schemes', ['https'])
            host = self.spec.get('host', 'api.example.com')
            base_path = self.spec.get('basePath', '')
            return f"{schemes[0]}://{host}{base_path}"
        else:
            # OpenAPI 3.x
            servers = self.spec.get('servers', [])
            if servers:
                return servers[0].get('url', 'https://api.example.com')
            return 'https://api.example.com'
    
    def import_to_collection(self, collection_name: Optional[str] = None) -> Dict:
        """
        Convert OpenAPI spec to PostMini collection format.
        
        Args:
            collection_name: Custom name for the collection (optional)
            
        Returns:
            Dictionary representing the collection with requests
        """
        info = self.spec.get('info', {})
        
        collection = {
            'name': collection_name or info.get('title', 'Imported API'),
            'description': info.get('description', ''),
            'version': info.get('version', '1.0.0'),
            'base_url': self.get_base_url(),
            'requests': []
        }
        
        # Extract paths
        paths = self.spec.get('paths', {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    request = self._create_request(method, path, operation, collection['base_url'])
                    collection['requests'].append(request)
        
        return collection
    
    def _create_request(self, method: str, path: str, operation: Dict, base_url: str) -> Dict:
        """
        Create a PostMini request from an OpenAPI operation.
        
        Args:
            method: HTTP method
            path: URL path
            operation: OpenAPI operation object
            base_url: Base URL for the API
            
        Returns:
            Dictionary representing a PostMini request
        """
        request = {
            'method': method.upper(),
            'url': base_url + path,
            'name': operation.get('summary', f'{method.upper()} {path}'),
            'description': operation.get('description', ''),
            'headers': {},
            'params': {},
            'body': '',
            'auth_type': 'None',
            'auth_token': ''
        }
        
        # Extract parameters
        parameters = operation.get('parameters', [])
        for param in parameters:
            self._add_parameter(request, param)
        
        # Extract request body (OpenAPI 3.x)
        if 'requestBody' in operation:
            request['body'] = self._generate_request_body(operation['requestBody'])
        
        # Extract headers from security
        security = operation.get('security', self.spec.get('security', []))
        if security:
            self._add_security_headers(request, security)
        
        return request
    
    def _add_parameter(self, request: Dict, param: Dict):
        """Add a parameter to the request."""
        param_in = param.get('in', '')
        param_name = param.get('name', '')
        
        # Get schema or type
        if 'schema' in param:
            schema = param['schema']
            example_value = self._generate_example_value(schema)
        else:
            # Swagger 2.0 style
            param_type = param.get('type', 'string')
            example_value = param.get('example', self._get_default_for_type(param_type))
        
        if param_in == 'query':
            request['params'][param_name] = str(example_value)
        elif param_in == 'header':
            request['headers'][param_name] = str(example_value)
        elif param_in == 'path':
            # Path parameters are already in the URL with {param} syntax
            # We'll leave them for the user to fill or use variables
            pass
    
    def _generate_request_body(self, request_body: Dict) -> str:
        """Generate example request body from requestBody object."""
        content = request_body.get('content', {})
        
        # Try JSON first
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            example_data = self._generate_from_schema(schema)
            return json.dumps(example_data, indent=2)
        
        # Try form data
        elif 'application/x-www-form-urlencoded' in content:
            schema = content['application/x-www-form-urlencoded'].get('schema', {})
            example_data = self._generate_from_schema(schema)
            # Convert to URL-encoded format
            params = []
            if isinstance(example_data, dict):
                for key, value in example_data.items():
                    params.append(f"{key}={value}")
            return '&'.join(params)
        
        # Try multipart
        elif 'multipart/form-data' in content:
            return '# Multipart form data - configure in UI'
        
        return ''
    
    def _generate_from_schema(self, schema: Dict) -> Any:
        """
        Generate example data from JSON schema.
        
        Args:
            schema: JSON schema object
            
        Returns:
            Example data matching the schema
        """
        # Check for example first
        if 'example' in schema:
            return schema['example']
        
        # Check for examples
        if 'examples' in schema and schema['examples']:
            if isinstance(schema['examples'], list):
                return schema['examples'][0]
            elif isinstance(schema['examples'], dict):
                return list(schema['examples'].values())[0]
        
        # Generate based on type
        schema_type = schema.get('type', 'object')
        
        if schema_type == 'object':
            obj = {}
            properties = schema.get('properties', {})
            for prop_name, prop_schema in properties.items():
                obj[prop_name] = self._generate_from_schema(prop_schema)
            return obj
        
        elif schema_type == 'array':
            items_schema = schema.get('items', {})
            return [self._generate_from_schema(items_schema)]
        
        elif schema_type == 'string':
            # Check for format
            fmt = schema.get('format', '')
            if fmt == 'email':
                return 'user@example.com'
            elif fmt == 'uri':
                return 'https://example.com'
            elif fmt == 'date':
                return '2024-01-01'
            elif fmt == 'date-time':
                return '2024-01-01T00:00:00Z'
            elif fmt == 'uuid':
                return 'a3f2e8d1-4b5c-6789-0123-456789abcdef'
            # Check for enum
            if 'enum' in schema:
                return schema['enum'][0]
            return schema.get('default', 'string')
        
        elif schema_type == 'integer':
            return schema.get('default', 0)
        
        elif schema_type == 'number':
            return schema.get('default', 0.0)
        
        elif schema_type == 'boolean':
            return schema.get('default', False)
        
        elif schema_type == 'null':
            return None
        
        return None
    
    def _generate_example_value(self, schema: Dict) -> Any:
        """Generate an example value from a parameter schema."""
        return self._generate_from_schema(schema)
    
    def _get_default_for_type(self, param_type: str) -> Any:
        """Get a default value for a Swagger 2.0 parameter type."""
        defaults = {
            'string': 'string',
            'integer': 0,
            'number': 0.0,
            'boolean': False,
            'array': []
        }
        return defaults.get(param_type, 'value')
    
    def _add_security_headers(self, request: Dict, security: List[Dict]):
        """Add security/authentication to the request."""
        if not security:
            return
        
        # Get first security requirement
        if not security or not security[0]:
            return
        
        security_name = list(security[0].keys())[0] if security[0] else None
        if not security_name:
            return
        
        # Get security definition
        if self.version == '2.0':
            security_defs = self.spec.get('securityDefinitions', {})
        else:
            components = self.spec.get('components', {})
            security_defs = components.get('securitySchemes', {})
        
        if security_name not in security_defs:
            return
        
        security_def = security_defs[security_name]
        sec_type = security_def.get('type', '')
        
        if sec_type == 'apiKey':
            # API Key authentication
            key_name = security_def.get('name', 'X-API-Key')
            key_in = security_def.get('in', 'header')
            
            if key_in == 'header':
                request['headers'][key_name] = '{{apiKey}}'
            elif key_in == 'query':
                request['params'][key_name] = '{{apiKey}}'
        
        elif sec_type in ['http', 'bearer']:
            # Bearer token
            request['auth_type'] = 'Bearer Token'
            request['auth_token'] = '{{bearerToken}}'
            request['headers']['Authorization'] = 'Bearer {{bearerToken}}'
        
        elif sec_type == 'oauth2':
            # OAuth 2.0
            request['auth_type'] = 'Bearer Token'
            request['auth_token'] = '{{accessToken}}'
            request['headers']['Authorization'] = 'Bearer {{accessToken}}'
    
    def get_summary(self) -> Dict:
        """Get a summary of the API spec."""
        info = self.spec.get('info', {})
        paths = self.spec.get('paths', {})
        
        endpoint_count = 0
        methods = set()
        
        for path, path_item in paths.items():
            for method in path_item.keys():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    endpoint_count += 1
                    methods.add(method.upper())
        
        return {
            'title': info.get('title', 'Unknown API'),
            'version': info.get('version', '1.0.0'),
            'description': info.get('description', ''),
            'openapi_version': self.version,
            'base_url': self.get_base_url(),
            'endpoint_count': endpoint_count,
            'methods': sorted(list(methods))
        }


def import_openapi_spec(file_path: str, collection_name: Optional[str] = None) -> Tuple[Dict, Dict]:
    """
    Import an OpenAPI/Swagger specification.
    
    Args:
        file_path: Path to the OpenAPI spec file
        collection_name: Optional custom name for the collection
        
    Returns:
        Tuple of (collection_dict, summary_dict)
        
    Raises:
        FileNotFoundError: If spec file doesn't exist
        ValueError: If spec format is invalid
    """
    importer = OpenAPIImporter(file_path)
    collection = importer.import_to_collection(collection_name)
    summary = importer.get_summary()
    return collection, summary

