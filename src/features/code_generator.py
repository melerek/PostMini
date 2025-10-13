"""
Code Generator Module

This module generates code snippets in various programming languages
from API request configurations.
"""

import json
from typing import Dict, Optional
from urllib.parse import urlencode


class CodeGenerator:
    """
    Generates code snippets for API requests in various languages.
    """
    
    @staticmethod
    def generate_curl(method: str, url: str, 
                     params: Optional[Dict] = None,
                     headers: Optional[Dict] = None,
                     body: Optional[str] = None,
                     auth_type: str = 'None',
                     auth_token: Optional[str] = None) -> str:
        """
        Generate curl command.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            headers: Request headers
            body: Request body
            auth_type: Authentication type
            auth_token: Authentication token
            
        Returns:
            curl command string
        """
        # Build URL with params
        full_url = url
        if params:
            query_string = urlencode(params)
            separator = '&' if '?' in url else '?'
            full_url = f"{url}{separator}{query_string}"
        
        # Start command
        lines = [f"curl --request {method}"]
        lines.append(f"  --url '{full_url}'")
        
        # Add headers
        if headers:
            for key, value in headers.items():
                lines.append(f"  --header '{key}: {value}'")
        
        # Add auth header
        if auth_type == 'Bearer Token' and auth_token:
            lines.append(f"  --header 'Authorization: Bearer {auth_token}'")
        
        # Add body
        if body:
            # Escape single quotes in body
            escaped_body = body.replace("'", "'\"'\"'")
            lines.append(f"  --data '{escaped_body}'")
        
        return " \\\n".join(lines)
    
    @staticmethod
    def generate_python_requests(method: str, url: str,
                                 params: Optional[Dict] = None,
                                 headers: Optional[Dict] = None,
                                 body: Optional[str] = None,
                                 auth_type: str = 'None',
                                 auth_token: Optional[str] = None) -> str:
        """Generate Python code using requests library."""
        lines = ["import requests", "", ""]
        
        # URL
        lines.append(f'url = "{url}"')
        lines.append("")
        
        # Params
        if params:
            lines.append("params = {")
            for key, value in params.items():
                lines.append(f'    "{key}": "{value}",')
            lines.append("}")
            lines.append("")
        
        # Headers
        headers_dict = headers.copy() if headers else {}
        if auth_type == 'Bearer Token' and auth_token:
            headers_dict['Authorization'] = f'Bearer {auth_token}'
        
        if headers_dict:
            lines.append("headers = {")
            for key, value in headers_dict.items():
                lines.append(f'    "{key}": "{value}",')
            lines.append("}")
            lines.append("")
        
        # Body
        if body:
            # Try to format as JSON
            try:
                parsed = json.loads(body)
                lines.append("data = " + json.dumps(parsed, indent=4))
                lines.append("")
            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, use as plain string
                lines.append(f'data = """{body}"""')
                lines.append("")
        
        # Request
        method_lower = method.lower()
        request_line = f'response = requests.{method_lower}(url'
        
        if params:
            request_line += ', params=params'
        if headers_dict:
            request_line += ', headers=headers'
        if body:
            request_line += ', data=data'
        
        request_line += ')'
        lines.append(request_line)
        lines.append("")
        
        # Response handling
        lines.append("print(f'Status Code: {response.status_code}')")
        lines.append("print(f'Response: {response.text}')")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_javascript_fetch(method: str, url: str,
                                  params: Optional[Dict] = None,
                                  headers: Optional[Dict] = None,
                                  body: Optional[str] = None,
                                  auth_type: str = 'None',
                                  auth_token: Optional[str] = None) -> str:
        """Generate JavaScript code using fetch API."""
        # Build URL with params
        full_url = url
        if params:
            query_string = urlencode(params)
            separator = '&' if '?' in url else '?'
            full_url = f"{url}{separator}{query_string}"
        
        lines = [f"const url = '{full_url}';", ""]
        
        # Options object
        lines.append("const options = {")
        lines.append(f"  method: '{method}',")
        
        # Headers
        headers_dict = headers.copy() if headers else {}
        if auth_type == 'Bearer Token' and auth_token:
            headers_dict['Authorization'] = f'Bearer {auth_token}'
        
        if headers_dict:
            lines.append("  headers: {")
            for key, value in headers_dict.items():
                lines.append(f"    '{key}': '{value}',")
            lines.append("  },")
        
        # Body
        if body:
            try:
                # Try to parse as JSON
                parsed = json.loads(body)
                json_str = json.dumps(parsed, indent=4)
                indented = "\n".join("  " + line for line in json_str.split("\n"))
                lines.append(f"  body: JSON.stringify({indented}),")
            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, use as plain string
                escaped_body = body.replace("'", "\\'")
                lines.append(f"  body: '{escaped_body}',")
        
        lines.append("};")
        lines.append("")
        
        # Fetch call
        lines.append("fetch(url, options)")
        lines.append("  .then(response => response.json())")
        lines.append("  .then(data => console.log(data))")
        lines.append("  .catch(error => console.error('Error:', error));")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_javascript_axios(method: str, url: str,
                                 params: Optional[Dict] = None,
                                 headers: Optional[Dict] = None,
                                 body: Optional[str] = None,
                                 auth_type: str = 'None',
                                 auth_token: Optional[str] = None) -> str:
        """Generate JavaScript code using axios library."""
        lines = ["const axios = require('axios');", ""]
        
        # Config object
        lines.append("const config = {")
        lines.append(f"  method: '{method.lower()}',")
        lines.append(f"  url: '{url}',")
        
        # Params
        if params:
            lines.append("  params: {")
            for key, value in params.items():
                lines.append(f"    {key}: '{value}',")
            lines.append("  },")
        
        # Headers
        headers_dict = headers.copy() if headers else {}
        if auth_type == 'Bearer Token' and auth_token:
            headers_dict['Authorization'] = f'Bearer {auth_token}'
        
        if headers_dict:
            lines.append("  headers: {")
            for key, value in headers_dict.items():
                lines.append(f"    '{key}': '{value}',")
            lines.append("  },")
        
        # Body
        if body:
            try:
                parsed = json.loads(body)
                json_str = json.dumps(parsed, indent=4)
                indented = "\n".join("  " + line for line in json_str.split("\n"))
                lines.append(f"  data: {indented},")
            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, use as plain string
                escaped_body = body.replace("'", "\\'")
                lines.append(f"  data: '{escaped_body}',")
        
        lines.append("};")
        lines.append("")
        
        # Axios call
        lines.append("axios(config)")
        lines.append("  .then(response => {")
        lines.append("    console.log(JSON.stringify(response.data));")
        lines.append("  })")
        lines.append("  .catch(error => {")
        lines.append("    console.log(error);")
        lines.append("  });")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_nodejs(method: str, url: str,
                       params: Optional[Dict] = None,
                       headers: Optional[Dict] = None,
                       body: Optional[str] = None,
                       auth_type: str = 'None',
                       auth_token: Optional[str] = None) -> str:
        """Generate Node.js code using https module."""
        from urllib.parse import urlparse
        
        # Parse URL
        parsed_url = urlparse(url)
        
        # Build path with params
        path = parsed_url.path or '/'
        if params:
            query_string = urlencode(params)
            path = f"{path}?{query_string}"
        
        lines = ["const https = require('https');", ""]
        
        # Options
        lines.append("const options = {")
        lines.append(f"  hostname: '{parsed_url.netloc}',")
        lines.append(f"  port: {parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)},")
        lines.append(f"  path: '{path}',")
        lines.append(f"  method: '{method}',")
        
        # Headers
        headers_dict = headers.copy() if headers else {}
        if auth_type == 'Bearer Token' and auth_token:
            headers_dict['Authorization'] = f'Bearer {auth_token}'
        
        if headers_dict:
            lines.append("  headers: {")
            for key, value in headers_dict.items():
                lines.append(f"    '{key}': '{value}',")
            lines.append("  },")
        
        lines.append("};")
        lines.append("")
        
        # Request
        lines.append("const req = https.request(options, (res) => {")
        lines.append("  let data = '';")
        lines.append("")
        lines.append("  res.on('data', (chunk) => {")
        lines.append("    data += chunk;")
        lines.append("  });")
        lines.append("")
        lines.append("  res.on('end', () => {")
        lines.append("    console.log(JSON.parse(data));")
        lines.append("  });")
        lines.append("});")
        lines.append("")
        lines.append("req.on('error', (error) => {")
        lines.append("  console.error(error);")
        lines.append("});")
        lines.append("")
        
        # Write body if present
        if body:
            lines.append(f"req.write('{body}');")
        
        lines.append("req.end();")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_react(method: str, url: str,
                      params: Optional[Dict] = None,
                      headers: Optional[Dict] = None,
                      body: Optional[str] = None,
                      auth_type: str = 'None',
                      auth_token: Optional[str] = None) -> str:
        """Generate React component with fetch."""
        # Build URL with params
        full_url = url
        if params:
            query_string = urlencode(params)
            separator = '&' if '?' in url else '?'
            full_url = f"{url}{separator}{query_string}"
        
        lines = ["import React, { useState, useEffect } from 'react';", ""]
        lines.append("function ApiComponent() {")
        lines.append("  const [data, setData] = useState(null);")
        lines.append("  const [loading, setLoading] = useState(true);")
        lines.append("  const [error, setError] = useState(null);")
        lines.append("")
        lines.append("  useEffect(() => {")
        lines.append("    const fetchData = async () => {")
        lines.append("      try {")
        lines.append(f"        const response = await fetch('{full_url}', {{")
        lines.append(f"          method: '{method}',")
        
        # Headers
        headers_dict = headers.copy() if headers else {}
        if auth_type == 'Bearer Token' and auth_token:
            headers_dict['Authorization'] = f'Bearer {auth_token}'
        
        if headers_dict:
            lines.append("          headers: {")
            for key, value in headers_dict.items():
                lines.append(f"            '{key}': '{value}',")
            lines.append("          },")
        
        # Body
        if body:
            try:
                parsed = json.loads(body)
                json_str = json.dumps(parsed)
                lines.append(f"          body: JSON.stringify({json_str}),")
            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, use as plain string
                escaped_body = body.replace("'", "\\'")
                lines.append(f"          body: '{escaped_body}',")
        
        lines.append("        });")
        lines.append("")
        lines.append("        if (!response.ok) {")
        lines.append("          throw new Error('Network response was not ok');")
        lines.append("        }")
        lines.append("")
        lines.append("        const result = await response.json();")
        lines.append("        setData(result);")
        lines.append("      } catch (err) {")
        lines.append("        setError(err.message);")
        lines.append("      } finally {")
        lines.append("        setLoading(false);")
        lines.append("      }")
        lines.append("    };")
        lines.append("")
        lines.append("    fetchData();")
        lines.append("  }, []);")
        lines.append("")
        lines.append("  if (loading) return <div>Loading...</div>;")
        lines.append("  if (error) return <div>Error: {error}</div>;")
        lines.append("")
        lines.append("  return (")
        lines.append("    <div>")
        lines.append("      <h2>API Response</h2>")
        lines.append("      <pre>{JSON.stringify(data, null, 2)}</pre>")
        lines.append("    </div>")
        lines.append("  );")
        lines.append("}")
        lines.append("")
        lines.append("export default ApiComponent;")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_csharp(method: str, url: str,
                       params: Optional[Dict] = None,
                       headers: Optional[Dict] = None,
                       body: Optional[str] = None,
                       auth_type: str = 'None',
                       auth_token: Optional[str] = None) -> str:
        """Generate C# code using HttpClient."""
        # Build URL with params
        full_url = url
        if params:
            query_string = urlencode(params)
            separator = '&' if '?' in url else '?'
            full_url = f"{url}{separator}{query_string}"
        
        lines = ["using System;"]
        lines.append("using System.Net.Http;")
        lines.append("using System.Text;")
        lines.append("using System.Threading.Tasks;")
        lines.append("")
        lines.append("class Program")
        lines.append("{")
        lines.append("    static async Task Main()")
        lines.append("    {")
        lines.append("        using (var client = new HttpClient())")
        lines.append("        {")
        
        # Headers
        if headers:
            for key, value in headers.items():
                lines.append(f'            client.DefaultRequestHeaders.Add("{key}", "{value}");')
        
        # Auth
        if auth_type == 'Bearer Token' and auth_token:
            lines.append(f'            client.DefaultRequestHeaders.Add("Authorization", "Bearer {auth_token}");')
        
        if headers or (auth_type == 'Bearer Token' and auth_token):
            lines.append("")
        
        # Request
        if method in ['GET', 'DELETE']:
            lines.append(f'            var response = await client.{method.capitalize()}Async("{full_url}");')
        elif method in ['POST', 'PUT', 'PATCH']:
            if body:
                lines.append(f'            var content = new StringContent(@"{body}", Encoding.UTF8, "application/json");')
                lines.append(f'            var response = await client.{method.capitalize()}Async("{full_url}", content);')
            else:
                lines.append(f'            var response = await client.{method.capitalize()}Async("{full_url}", null);')
        
        lines.append("")
        lines.append("            var responseBody = await response.Content.ReadAsStringAsync();")
        lines.append('            Console.WriteLine($"Status: {response.StatusCode}");')
        lines.append('            Console.WriteLine($"Response: {responseBody}");')
        lines.append("        }")
        lines.append("    }")
        lines.append("}")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate(language: str, method: str, url: str,
                params: Optional[Dict] = None,
                headers: Optional[Dict] = None,
                body: Optional[str] = None,
                auth_type: str = 'None',
                auth_token: Optional[str] = None) -> str:
        """
        Generate code snippet for the specified language.
        
        Args:
            language: Target language
            method: HTTP method
            url: Request URL
            params: Query parameters
            headers: Request headers
            body: Request body
            auth_type: Authentication type
            auth_token: Authentication token
            
        Returns:
            Generated code snippet
        """
        generators = {
            'curl': CodeGenerator.generate_curl,
            'python': CodeGenerator.generate_python_requests,
            'javascript_fetch': CodeGenerator.generate_javascript_fetch,
            'javascript_axios': CodeGenerator.generate_javascript_axios,
            'nodejs': CodeGenerator.generate_nodejs,
            'react': CodeGenerator.generate_react,
            'csharp': CodeGenerator.generate_csharp,
        }
        
        generator = generators.get(language.lower())
        if not generator:
            raise ValueError(f"Unsupported language: {language}")
        
        return generator(method, url, params, headers, body, auth_type, auth_token)

