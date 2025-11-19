"""
Security Scanner Module

This module provides OWASP-based security scanning for API endpoints.
All checks run locally without any external network calls, ensuring 100% privacy.
"""

import re
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse


class SecurityFinding:
    """Represents a single security vulnerability or issue."""
    
    SEVERITY_CRITICAL = "critical"
    SEVERITY_HIGH = "high"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_LOW = "low"
    SEVERITY_INFO = "info"
    
    def __init__(
        self,
        check_id: str,
        title: str,
        severity: str,
        description: str,
        recommendation: str,
        evidence: Optional[str] = None,
        cwe_id: Optional[str] = None,
        owasp_category: Optional[str] = None
    ):
        self.check_id = check_id
        self.title = title
        self.severity = severity
        self.description = description
        self.recommendation = recommendation
        self.evidence = evidence
        self.cwe_id = cwe_id
        self.owasp_category = owasp_category
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            'check_id': self.check_id,
            'title': self.title,
            'severity': self.severity,
            'description': self.description,
            'recommendation': self.recommendation,
            'evidence': self.evidence,
            'cwe_id': self.cwe_id,
            'owasp_category': self.owasp_category,
            'timestamp': self.timestamp
        }


class SecurityScanner:
    """
    Performs security checks on API requests and responses.
    All checks are performed locally with no external network calls.
    """
    
    def __init__(self):
        """Initialize the security scanner with all check modules."""
        self.checks_enabled = {
            'security_headers': True,
            'insecure_cookies': True,
            'sensitive_data': True,
            'sql_injection_indicators': True,
            'server_disclosure': True,
            'directory_listing': True,
            'error_disclosure': True,
            'http_methods': True,
            'cors_misconfig': True,
            'content_type': True,
        }
    
    def scan_response(
        self,
        method: str,
        url: str,
        request_headers: Dict[str, str],
        response_status: int,
        response_headers: Dict[str, str],
        response_body: str,
        request_secure: bool = True
    ) -> List[SecurityFinding]:
        """
        Perform comprehensive security scan on an API response.
        
        Args:
            method: HTTP method used
            url: Request URL
            request_headers: Request headers sent
            response_status: HTTP status code
            response_headers: Response headers received
            response_body: Response body content
            request_secure: Whether request was made over HTTPS
        
        Returns:
            List of security findings
        """
        findings = []
        
        # Normalize header keys to lowercase for case-insensitive lookup
        response_headers_lower = {k.lower(): v for k, v in response_headers.items()}
        
        # Run all enabled checks
        if self.checks_enabled.get('security_headers'):
            findings.extend(self._check_security_headers(url, response_headers_lower, request_secure))
        
        if self.checks_enabled.get('insecure_cookies'):
            findings.extend(self._check_insecure_cookies(url, response_headers_lower, request_secure))
        
        if self.checks_enabled.get('sensitive_data'):
            findings.extend(self._check_sensitive_data(response_body))
        
        if self.checks_enabled.get('sql_injection_indicators'):
            findings.extend(self._check_sql_injection_indicators(response_body))
        
        if self.checks_enabled.get('server_disclosure'):
            findings.extend(self._check_server_disclosure(response_headers_lower))
        
        if self.checks_enabled.get('directory_listing'):
            findings.extend(self._check_directory_listing(response_body, response_status))
        
        if self.checks_enabled.get('error_disclosure'):
            findings.extend(self._check_error_disclosure(response_body, response_status))
        
        if self.checks_enabled.get('http_methods'):
            findings.extend(self._check_http_methods(response_headers_lower))
        
        if self.checks_enabled.get('cors_misconfig'):
            findings.extend(self._check_cors_misconfig(response_headers_lower))
        
        if self.checks_enabled.get('content_type'):
            findings.extend(self._check_content_type(response_headers_lower, response_body))
        
        return findings
    
    def _check_security_headers(
        self,
        url: str,
        headers: Dict[str, str],
        is_https: bool
    ) -> List[SecurityFinding]:
        """Check for missing security headers."""
        findings = []
        parsed_url = urlparse(url)
        is_https_url = parsed_url.scheme == 'https'
        
        # HSTS check (only for HTTPS)
        if is_https_url and 'strict-transport-security' not in headers:
            findings.append(SecurityFinding(
                check_id='SEC001',
                title='Missing Strict-Transport-Security Header',
                severity=SecurityFinding.SEVERITY_MEDIUM,
                description='The HTTP Strict-Transport-Security (HSTS) header is missing. This header forces browsers to use HTTPS connections only.',
                recommendation='Add the header: Strict-Transport-Security: max-age=31536000; includeSubDomains',
                cwe_id='CWE-319',
                owasp_category='A05:2021 – Security Misconfiguration'
            ))
        
        # X-Frame-Options check
        if 'x-frame-options' not in headers and 'content-security-policy' not in headers:
            findings.append(SecurityFinding(
                check_id='SEC002',
                title='Missing X-Frame-Options Header',
                severity=SecurityFinding.SEVERITY_MEDIUM,
                description='The X-Frame-Options header is missing. This exposes the application to clickjacking attacks.',
                recommendation='Add the header: X-Frame-Options: DENY or X-Frame-Options: SAMEORIGIN',
                cwe_id='CWE-1021',
                owasp_category='A05:2021 – Security Misconfiguration'
            ))
        
        # X-Content-Type-Options check
        if 'x-content-type-options' not in headers:
            findings.append(SecurityFinding(
                check_id='SEC003',
                title='Missing X-Content-Type-Options Header',
                severity=SecurityFinding.SEVERITY_LOW,
                description='The X-Content-Type-Options header is missing. This can allow MIME-sniffing attacks.',
                recommendation='Add the header: X-Content-Type-Options: nosniff',
                cwe_id='CWE-16',
                owasp_category='A05:2021 – Security Misconfiguration'
            ))
        
        # Content-Security-Policy check
        if 'content-security-policy' not in headers:
            findings.append(SecurityFinding(
                check_id='SEC004',
                title='Missing Content-Security-Policy Header',
                severity=SecurityFinding.SEVERITY_MEDIUM,
                description='The Content-Security-Policy (CSP) header is missing. CSP helps prevent XSS and other code injection attacks.',
                recommendation="Add a restrictive CSP header, e.g.: Content-Security-Policy: default-src 'self'",
                cwe_id='CWE-1021',
                owasp_category='A03:2021 – Injection'
            ))
        
        # X-XSS-Protection check (deprecated but still useful for older browsers)
        if 'x-xss-protection' not in headers:
            findings.append(SecurityFinding(
                check_id='SEC005',
                title='Missing X-XSS-Protection Header',
                severity=SecurityFinding.SEVERITY_LOW,
                description='The X-XSS-Protection header is missing. While deprecated in favor of CSP, it still provides protection for older browsers.',
                recommendation='Add the header: X-XSS-Protection: 1; mode=block',
                cwe_id='CWE-79',
                owasp_category='A03:2021 – Injection'
            ))
        
        # Referrer-Policy check
        if 'referrer-policy' not in headers:
            findings.append(SecurityFinding(
                check_id='SEC006',
                title='Missing Referrer-Policy Header',
                severity=SecurityFinding.SEVERITY_INFO,
                description='The Referrer-Policy header is missing. This controls how much referrer information is sent with requests.',
                recommendation='Add the header: Referrer-Policy: strict-origin-when-cross-origin',
                cwe_id='CWE-200',
                owasp_category='A01:2021 – Broken Access Control'
            ))
        
        return findings
    
    def _check_insecure_cookies(
        self,
        url: str,
        headers: Dict[str, str],
        is_https: bool
    ) -> List[SecurityFinding]:
        """Check for insecure cookie configurations."""
        findings = []
        parsed_url = urlparse(url)
        is_https_url = parsed_url.scheme == 'https'
        
        set_cookie_headers = []
        for key, value in headers.items():
            if key == 'set-cookie':
                set_cookie_headers.append(value)
        
        for cookie_header in set_cookie_headers:
            cookie_lower = cookie_header.lower()
            
            # Extract cookie name
            cookie_name = cookie_header.split('=')[0].strip() if '=' in cookie_header else 'unknown'
            
            # Check for HttpOnly flag
            if 'httponly' not in cookie_lower:
                findings.append(SecurityFinding(
                    check_id='SEC007',
                    title=f'Cookie Missing HttpOnly Flag: {cookie_name}',
                    severity=SecurityFinding.SEVERITY_MEDIUM,
                    description=f'The cookie "{cookie_name}" is missing the HttpOnly flag. This makes it accessible to JavaScript and vulnerable to XSS attacks.',
                    recommendation='Add the HttpOnly flag to all session/authentication cookies.',
                    evidence=cookie_header[:100],
                    cwe_id='CWE-1004',
                    owasp_category='A05:2021 – Security Misconfiguration'
                ))
            
            # Check for Secure flag (only for HTTPS sites)
            if is_https_url and 'secure' not in cookie_lower:
                findings.append(SecurityFinding(
                    check_id='SEC008',
                    title=f'Cookie Missing Secure Flag: {cookie_name}',
                    severity=SecurityFinding.SEVERITY_HIGH,
                    description=f'The cookie "{cookie_name}" is missing the Secure flag on an HTTPS site. This allows the cookie to be transmitted over unencrypted HTTP.',
                    recommendation='Add the Secure flag to all cookies on HTTPS sites.',
                    evidence=cookie_header[:100],
                    cwe_id='CWE-614',
                    owasp_category='A05:2021 – Security Misconfiguration'
                ))
            
            # Check for SameSite attribute
            if 'samesite' not in cookie_lower:
                findings.append(SecurityFinding(
                    check_id='SEC009',
                    title=f'Cookie Missing SameSite Attribute: {cookie_name}',
                    severity=SecurityFinding.SEVERITY_MEDIUM,
                    description=f'The cookie "{cookie_name}" is missing the SameSite attribute. This makes it vulnerable to CSRF attacks.',
                    recommendation='Add the SameSite attribute: SameSite=Strict or SameSite=Lax',
                    evidence=cookie_header[:100],
                    cwe_id='CWE-352',
                    owasp_category='A01:2021 – Broken Access Control'
                ))
        
        return findings
    
    def _check_sensitive_data(self, response_body: str) -> List[SecurityFinding]:
        """Check for sensitive data exposure in response."""
        findings = []
        
        if not response_body:
            return findings
        
        # Credit card pattern (simple check for card-like numbers)
        cc_pattern = r'\b(?:\d[ -]*?){13,19}\b'
        cc_matches = re.findall(cc_pattern, response_body)
        if cc_matches:
            findings.append(SecurityFinding(
                check_id='SEC010',
                title='Potential Credit Card Number in Response',
                severity=SecurityFinding.SEVERITY_CRITICAL,
                description=f'Found {len(cc_matches)} potential credit card number(s) in the response body.',
                recommendation='Remove sensitive payment information from API responses. Use tokenization or masking.',
                evidence=cc_matches[0][:20] + '...' if cc_matches else None,
                cwe_id='CWE-359',
                owasp_category='A02:2021 – Cryptographic Failures'
            ))
        
        # Social Security Number pattern (US)
        ssn_pattern = r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
        ssn_matches = re.findall(ssn_pattern, response_body)
        if ssn_matches:
            findings.append(SecurityFinding(
                check_id='SEC011',
                title='Potential Social Security Number in Response',
                severity=SecurityFinding.SEVERITY_CRITICAL,
                description=f'Found {len(ssn_matches)} potential SSN(s) in the response body.',
                recommendation='Remove PII (Personally Identifiable Information) from API responses.',
                evidence=ssn_matches[0][:5] + '...' if ssn_matches else None,
                cwe_id='CWE-359',
                owasp_category='A02:2021 – Cryptographic Failures'
            ))
        
        # API key patterns (common formats)
        api_key_patterns = [
            (r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'API Key'),
            (r'["\']?secret[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'Secret Key'),
            (r'Bearer\s+([a-zA-Z0-9_\-\.]{20,})', 'Bearer Token'),
            (r'["\']?access[_-]?token["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'Access Token'),
        ]
        
        for pattern, key_type in api_key_patterns:
            matches = re.findall(pattern, response_body, re.IGNORECASE)
            if matches:
                findings.append(SecurityFinding(
                    check_id='SEC012',
                    title=f'Potential {key_type} Exposed in Response',
                    severity=SecurityFinding.SEVERITY_HIGH,
                    description=f'Found potential {key_type}(s) in the response body. Exposing API keys can lead to unauthorized access.',
                    recommendation='Never return API keys or secrets in responses. Use secure key management.',
                    evidence=matches[0][:15] + '...' if matches and isinstance(matches[0], str) else None,
                    cwe_id='CWE-798',
                    owasp_category='A02:2021 – Cryptographic Failures'
                ))
        
        # Email addresses (might indicate PII leak)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, response_body)
        if len(email_matches) > 5:  # Only flag if many emails found
            findings.append(SecurityFinding(
                check_id='SEC013',
                title='Multiple Email Addresses in Response',
                severity=SecurityFinding.SEVERITY_LOW,
                description=f'Found {len(email_matches)} email addresses in the response. This may indicate PII exposure.',
                recommendation='Verify that email addresses should be exposed. Consider pagination or filtering.',
                evidence=f'{len(email_matches)} emails found',
                cwe_id='CWE-359',
                owasp_category='A02:2021 – Cryptographic Failures'
            ))
        
        # AWS Access Key pattern
        aws_key_pattern = r'AKIA[0-9A-Z]{16}'
        aws_matches = re.findall(aws_key_pattern, response_body)
        if aws_matches:
            findings.append(SecurityFinding(
                check_id='SEC014',
                title='AWS Access Key Exposed in Response',
                severity=SecurityFinding.SEVERITY_CRITICAL,
                description='Found AWS access key in the response body. This can lead to complete AWS account compromise.',
                recommendation='Immediately rotate the exposed AWS key. Never include credentials in responses.',
                evidence=aws_matches[0][:10] + '...',
                cwe_id='CWE-798',
                owasp_category='A02:2021 – Cryptographic Failures'
            ))
        
        # Private key patterns
        private_key_indicators = ['BEGIN RSA PRIVATE KEY', 'BEGIN PRIVATE KEY', 'BEGIN EC PRIVATE KEY']
        for indicator in private_key_indicators:
            if indicator in response_body:
                findings.append(SecurityFinding(
                    check_id='SEC015',
                    title='Private Key Exposed in Response',
                    severity=SecurityFinding.SEVERITY_CRITICAL,
                    description='Found a private key in the response body. This is a critical security issue.',
                    recommendation='Immediately revoke and rotate the exposed key. Investigate how it was exposed.',
                    evidence=indicator,
                    cwe_id='CWE-798',
                    owasp_category='A02:2021 – Cryptographic Failures'
                ))
        
        return findings
    
    def _check_sql_injection_indicators(self, response_body: str) -> List[SecurityFinding]:
        """Check for SQL error messages indicating possible injection vulnerability."""
        findings = []
        
        if not response_body:
            return findings
        
        # Common SQL error patterns
        sql_error_patterns = [
            (r'SQL syntax.*?MySQL', 'MySQL'),
            (r'Warning.*?\Wmysqli?_', 'MySQL'),
            (r'MySQLSyntaxErrorException', 'MySQL'),
            (r'valid MySQL result', 'MySQL'),
            (r'PostgreSQL.*?ERROR', 'PostgreSQL'),
            (r'Warning.*?\Wpg_', 'PostgreSQL'),
            (r'valid PostgreSQL result', 'PostgreSQL'),
            (r'Npgsql\.', 'PostgreSQL'),
            (r'Driver.*? SQL[\-\_\ ]*Server', 'SQL Server'),
            (r'OLE DB.*? SQL Server', 'SQL Server'),
            (r'SQLServer JDBC Driver', 'SQL Server'),
            (r'\bORA-\d{5}', 'Oracle'),
            (r'Oracle error', 'Oracle'),
            (r'Oracle.*?Driver', 'Oracle'),
            (r'Warning.*?\Woci_', 'Oracle'),
            (r'SQLite/JDBCDriver', 'SQLite'),
            (r'SQLite.Exception', 'SQLite'),
            (r'System.Data.SQLite.SQLiteException', 'SQLite'),
            (r'sqlite3.OperationalError', 'SQLite'),
            (r'SQLSTATE\[\d+\]', 'Generic SQL'),
            (r'syntax error.*?SQL', 'Generic SQL'),
        ]
        
        for pattern, db_type in sql_error_patterns:
            if re.search(pattern, response_body, re.IGNORECASE):
                findings.append(SecurityFinding(
                    check_id='SEC016',
                    title=f'SQL Error Message Detected ({db_type})',
                    severity=SecurityFinding.SEVERITY_HIGH,
                    description=f'The response contains a {db_type} error message. This may indicate a SQL injection vulnerability and reveals database information.',
                    recommendation='Implement proper input validation, use parameterized queries, and suppress detailed error messages in production.',
                    evidence=re.search(pattern, response_body, re.IGNORECASE).group()[:100] if re.search(pattern, response_body, re.IGNORECASE) else None,
                    cwe_id='CWE-89',
                    owasp_category='A03:2021 – Injection'
                ))
                break  # Only report once
        
        return findings
    
    def _check_server_disclosure(self, headers: Dict[str, str]) -> List[SecurityFinding]:
        """Check for server version disclosure."""
        findings = []
        
        # Server header disclosure
        if 'server' in headers:
            server_value = headers['server']
            # Check if version numbers are included
            if re.search(r'\d+\.\d+', server_value):
                findings.append(SecurityFinding(
                    check_id='SEC017',
                    title='Server Version Disclosure',
                    severity=SecurityFinding.SEVERITY_LOW,
                    description='The Server header reveals version information about the web server software.',
                    recommendation='Remove or obfuscate version information from the Server header.',
                    evidence=server_value,
                    cwe_id='CWE-200',
                    owasp_category='A05:2021 – Security Misconfiguration'
                ))
        
        # X-Powered-By header disclosure
        if 'x-powered-by' in headers:
            powered_by = headers['x-powered-by']
            findings.append(SecurityFinding(
                check_id='SEC018',
                title='X-Powered-By Header Disclosure',
                severity=SecurityFinding.SEVERITY_LOW,
                description='The X-Powered-By header reveals technology stack information.',
                recommendation='Remove the X-Powered-By header to reduce information leakage.',
                evidence=powered_by,
                cwe_id='CWE-200',
                owasp_category='A05:2021 – Security Misconfiguration'
            ))
        
        # X-AspNet-Version header
        if 'x-aspnet-version' in headers:
            asp_version = headers['x-aspnet-version']
            findings.append(SecurityFinding(
                check_id='SEC019',
                title='ASP.NET Version Disclosure',
                severity=SecurityFinding.SEVERITY_LOW,
                description='The X-AspNet-Version header reveals ASP.NET version information.',
                recommendation='Disable the X-AspNet-Version header in web.config.',
                evidence=asp_version,
                cwe_id='CWE-200',
                owasp_category='A05:2021 – Security Misconfiguration'
            ))
        
        return findings
    
    def _check_directory_listing(self, response_body: str, status_code: int) -> List[SecurityFinding]:
        """Check for directory listing exposure."""
        findings = []
        
        if not response_body or status_code != 200:
            return findings
        
        # Common directory listing indicators
        directory_patterns = [
            r'<title>Index of /',
            r'<h1>Index of /',
            r'Directory Listing For',
            r'Parent Directory</a>',
            r'\[To Parent Directory\]',
        ]
        
        for pattern in directory_patterns:
            if re.search(pattern, response_body, re.IGNORECASE):
                findings.append(SecurityFinding(
                    check_id='SEC020',
                    title='Directory Listing Enabled',
                    severity=SecurityFinding.SEVERITY_MEDIUM,
                    description='The server is configured to display directory listings, which can reveal sensitive file and directory structure.',
                    recommendation='Disable directory listing on the web server. Add index files or configure proper access controls.',
                    evidence=re.search(pattern, response_body, re.IGNORECASE).group()[:100] if re.search(pattern, response_body, re.IGNORECASE) else None,
                    cwe_id='CWE-548',
                    owasp_category='A05:2021 – Security Misconfiguration'
                ))
                break
        
        return findings
    
    def _check_error_disclosure(self, response_body: str, status_code: int) -> List[SecurityFinding]:
        """Check for detailed error message disclosure."""
        findings = []
        
        if not response_body:
            return findings
        
        # Stack trace patterns
        stack_trace_patterns = [
            (r'at\s+[\w\.]+\([\w\.\:]+:\d+\)', 'Stack Trace'),
            (r'Traceback \(most recent call last\)', 'Python Stack Trace'),
            (r'Exception in thread', 'Java Stack Trace'),
            (r'\.php on line \d+', 'PHP Error'),
            (r'Warning: .+ in .+\.php', 'PHP Warning'),
            (r'Fatal error:', 'PHP Fatal Error'),
            (r'System\..*?Exception', '.NET Exception'),
        ]
        
        for pattern, error_type in stack_trace_patterns:
            if re.search(pattern, response_body, re.IGNORECASE):
                findings.append(SecurityFinding(
                    check_id='SEC021',
                    title=f'Verbose Error Messages ({error_type})',
                    severity=SecurityFinding.SEVERITY_MEDIUM,
                    description='The response contains detailed error messages or stack traces that reveal internal implementation details.',
                    recommendation='Configure the application to display generic error messages in production. Log detailed errors server-side.',
                    evidence=re.search(pattern, response_body, re.IGNORECASE).group()[:150] if re.search(pattern, response_body, re.IGNORECASE) else None,
                    cwe_id='CWE-209',
                    owasp_category='A05:2021 – Security Misconfiguration'
                ))
                break
        
        return findings
    
    def _check_http_methods(self, headers: Dict[str, str]) -> List[SecurityFinding]:
        """Check for dangerous HTTP methods allowed."""
        findings = []
        
        if 'allow' in headers:
            allowed_methods = headers['allow'].upper()
            dangerous_methods = ['PUT', 'DELETE', 'TRACE', 'CONNECT']
            
            found_dangerous = [method for method in dangerous_methods if method in allowed_methods]
            
            if found_dangerous:
                findings.append(SecurityFinding(
                    check_id='SEC022',
                    title='Dangerous HTTP Methods Allowed',
                    severity=SecurityFinding.SEVERITY_MEDIUM,
                    description=f'The server allows potentially dangerous HTTP methods: {", ".join(found_dangerous)}',
                    recommendation='Disable unnecessary HTTP methods. Only allow GET, POST, and other methods that are actually needed.',
                    evidence=allowed_methods,
                    cwe_id='CWE-749',
                    owasp_category='A05:2021 – Security Misconfiguration'
                ))
        
        return findings
    
    def _check_cors_misconfig(self, headers: Dict[str, str]) -> List[SecurityFinding]:
        """Check for CORS misconfiguration."""
        findings = []
        
        if 'access-control-allow-origin' in headers:
            cors_value = headers['access-control-allow-origin']
            
            # Wildcard CORS with credentials is dangerous
            if cors_value == '*':
                if headers.get('access-control-allow-credentials', '').lower() == 'true':
                    findings.append(SecurityFinding(
                        check_id='SEC023',
                        title='Insecure CORS Configuration',
                        severity=SecurityFinding.SEVERITY_HIGH,
                        description='The API allows all origins (*) with credentials enabled. This is a critical security misconfiguration.',
                        recommendation='Specify allowed origins explicitly. Never use wildcard (*) with credentials.',
                        evidence=f'Access-Control-Allow-Origin: {cors_value}',
                        cwe_id='CWE-346',
                        owasp_category='A05:2021 – Security Misconfiguration'
                    ))
                else:
                    findings.append(SecurityFinding(
                        check_id='SEC024',
                        title='Overly Permissive CORS Policy',
                        severity=SecurityFinding.SEVERITY_MEDIUM,
                        description='The API allows requests from all origins (*). This may be acceptable for public APIs but should be reviewed.',
                        recommendation='Restrict CORS to specific trusted origins if the API is not intended to be public.',
                        evidence=f'Access-Control-Allow-Origin: {cors_value}',
                        cwe_id='CWE-346',
                        owasp_category='A05:2021 – Security Misconfiguration'
                    ))
        
        return findings
    
    def _check_content_type(self, headers: Dict[str, str], response_body: str) -> List[SecurityFinding]:
        """Check for content-type mismatches and issues."""
        findings = []
        
        content_type = headers.get('content-type', '').lower()
        
        # Check if JSON response has correct content-type
        if response_body and response_body.strip().startswith(('{', '[')):
            try:
                json.loads(response_body[:1000])  # Verify it's valid JSON
                if 'application/json' not in content_type:
                    findings.append(SecurityFinding(
                        check_id='SEC025',
                        title='Incorrect Content-Type for JSON Response',
                        severity=SecurityFinding.SEVERITY_LOW,
                        description='The response appears to be JSON but the Content-Type header is not set to application/json.',
                        recommendation='Set the correct Content-Type header to application/json for JSON responses.',
                        evidence=f'Content-Type: {content_type or "missing"}',
                        cwe_id='CWE-345',
                        owasp_category='A05:2021 – Security Misconfiguration'
                    ))
            except (json.JSONDecodeError, ValueError):
                pass  # Not valid JSON
        
        return findings
    
    def get_severity_stats(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Get count of findings by severity."""
        stats = {
            SecurityFinding.SEVERITY_CRITICAL: 0,
            SecurityFinding.SEVERITY_HIGH: 0,
            SecurityFinding.SEVERITY_MEDIUM: 0,
            SecurityFinding.SEVERITY_LOW: 0,
            SecurityFinding.SEVERITY_INFO: 0,
        }
        
        for finding in findings:
            stats[finding.severity] = stats.get(finding.severity, 0) + 1
        
        return stats
