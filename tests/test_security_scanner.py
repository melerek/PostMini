"""
Test Security Scanner Functionality

Tests the OWASP-based security scanner module.
"""

import pytest
from src.features.security_scanner import SecurityScanner, SecurityFinding


class TestSecurityScanner:
    """Test security scanner checks."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scanner = SecurityScanner()
    
    def test_scanner_initialization(self):
        """Test scanner initializes with checks enabled."""
        assert self.scanner.checks_enabled['security_headers'] is True
        assert self.scanner.checks_enabled['insecure_cookies'] is True
        assert self.scanner.checks_enabled['sensitive_data'] is True
    
    def test_missing_security_headers(self):
        """Test detection of missing security headers."""
        findings = self.scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=200,
            response_headers={'content-type': 'application/json'},
            response_body='{"data": "test"}',
            request_secure=True
        )
        
        # Should find multiple missing headers
        assert len(findings) > 0
        
        # Check for specific missing headers
        finding_titles = [f.title for f in findings]
        assert any('HSTS' in title or 'Strict-Transport-Security' in title for title in finding_titles)
        assert any('X-Frame-Options' in title for title in finding_titles)
        assert any('X-Content-Type-Options' in title for title in finding_titles)
    
    def test_insecure_cookies(self):
        """Test detection of insecure cookie configurations."""
        findings = self.scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=200,
            response_headers={
                'set-cookie': 'sessionid=abc123; Path=/',
                'content-type': 'application/json'
            },
            response_body='{"data": "test"}',
            request_secure=True
        )
        
        # Should find missing HttpOnly, Secure, and SameSite flags
        cookie_findings = [f for f in findings if 'Cookie' in f.title]
        assert len(cookie_findings) >= 3  # At least HttpOnly, Secure, SameSite
        
        # Check severities
        high_findings = [f for f in cookie_findings if f.severity == SecurityFinding.SEVERITY_HIGH]
        assert len(high_findings) > 0  # Missing Secure flag on HTTPS is HIGH
    
    def test_sensitive_data_credit_card(self):
        """Test detection of credit card numbers."""
        findings = self.scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=200,
            response_headers={'content-type': 'application/json'},
            response_body='{"card": "4532-1234-5678-9010", "data": "test"}',
            request_secure=True
        )
        
        # Should find potential credit card number
        cc_findings = [f for f in findings if 'Credit Card' in f.title]
        assert len(cc_findings) > 0
        assert cc_findings[0].severity == SecurityFinding.SEVERITY_CRITICAL
    
    def test_sensitive_data_api_key(self):
        """Test detection of API keys in response."""
        findings = self.scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=200,
            response_headers={'content-type': 'application/json'},
            response_body='{"api_key": "test_key_1234567890abcdefghijklmnop"}',
            request_secure=True
        )
        
        # Should find API key exposure
        key_findings = [f for f in findings if 'API Key' in f.title or 'Secret' in f.title]
        assert len(key_findings) > 0
        assert key_findings[0].severity == SecurityFinding.SEVERITY_HIGH
    
    def test_sql_injection_indicators(self):
        """Test detection of SQL error messages."""
        findings = self.scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=500,
            response_headers={'content-type': 'text/html'},
            response_body='<html>SQL syntax error near WHERE clause at line 42 in MySQL</html>',
            request_secure=True
        )
        
        # Should find SQL error message
        sql_findings = [f for f in findings if 'SQL' in f.title]
        assert len(sql_findings) > 0
        assert sql_findings[0].severity == SecurityFinding.SEVERITY_HIGH
        assert sql_findings[0].cwe_id == 'CWE-89'
    
    def test_server_disclosure(self):
        """Test detection of server version disclosure."""
        findings = self.scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=200,
            response_headers={
                'server': 'Apache/2.4.41 (Ubuntu)',
                'x-powered-by': 'PHP/7.4.3',
                'content-type': 'application/json'
            },
            response_body='{"data": "test"}',
            request_secure=True
        )
        
        # Should find server version disclosure
        disclosure_findings = [f for f in findings if 'Disclosure' in f.title or 'X-Powered-By' in f.title]
        assert len(disclosure_findings) >= 2  # Server and X-Powered-By
    
    def test_cors_misconfiguration(self):
        """Test detection of CORS misconfigurations."""
        findings = self.scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=200,
            response_headers={
                'access-control-allow-origin': '*',
                'access-control-allow-credentials': 'true',
                'content-type': 'application/json'
            },
            response_body='{"data": "test"}',
            request_secure=True
        )
        
        # Should find insecure CORS with credentials
        cors_findings = [f for f in findings if 'CORS' in f.title]
        assert len(cors_findings) > 0
        assert cors_findings[0].severity == SecurityFinding.SEVERITY_HIGH
    
    def test_no_findings_secure_response(self):
        """Test that secure responses generate no findings."""
        findings = self.scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=200,
            response_headers={
                'content-type': 'application/json',
                'strict-transport-security': 'max-age=31536000; includeSubDomains',
                'x-frame-options': 'DENY',
                'x-content-type-options': 'nosniff',
                'content-security-policy': "default-src 'self'",
                'x-xss-protection': '1; mode=block',
                'referrer-policy': 'strict-origin-when-cross-origin',
                'set-cookie': 'sessionid=abc123; Path=/; HttpOnly; Secure; SameSite=Strict'
            },
            response_body='{"data": "test"}',
            request_secure=True
        )
        
        # Should have very few findings (maybe some info-level ones)
        critical_high = [f for f in findings if f.severity in [SecurityFinding.SEVERITY_CRITICAL, SecurityFinding.SEVERITY_HIGH]]
        assert len(critical_high) == 0
    
    def test_severity_stats(self):
        """Test severity statistics calculation."""
        findings = [
            SecurityFinding('T001', 'Test Critical', SecurityFinding.SEVERITY_CRITICAL, 'Desc', 'Rec'),
            SecurityFinding('T002', 'Test High', SecurityFinding.SEVERITY_HIGH, 'Desc', 'Rec'),
            SecurityFinding('T003', 'Test High 2', SecurityFinding.SEVERITY_HIGH, 'Desc', 'Rec'),
            SecurityFinding('T004', 'Test Medium', SecurityFinding.SEVERITY_MEDIUM, 'Desc', 'Rec'),
            SecurityFinding('T005', 'Test Low', SecurityFinding.SEVERITY_LOW, 'Desc', 'Rec'),
        ]
        
        stats = self.scanner.get_severity_stats(findings)
        
        assert stats[SecurityFinding.SEVERITY_CRITICAL] == 1
        assert stats[SecurityFinding.SEVERITY_HIGH] == 2
        assert stats[SecurityFinding.SEVERITY_MEDIUM] == 1
        assert stats[SecurityFinding.SEVERITY_LOW] == 1
        assert stats[SecurityFinding.SEVERITY_INFO] == 0
    
    def test_finding_to_dict(self):
        """Test finding serialization to dictionary."""
        finding = SecurityFinding(
            check_id='SEC001',
            title='Test Finding',
            severity=SecurityFinding.SEVERITY_HIGH,
            description='Test description',
            recommendation='Test recommendation',
            evidence='Test evidence',
            cwe_id='CWE-123',
            owasp_category='A01:2021'
        )
        
        result = finding.to_dict()
        
        assert result['check_id'] == 'SEC001'
        assert result['title'] == 'Test Finding'
        assert result['severity'] == SecurityFinding.SEVERITY_HIGH
        assert result['evidence'] == 'Test evidence'
        assert result['cwe_id'] == 'CWE-123'
        assert result['owasp_category'] == 'A01:2021'
        assert 'timestamp' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
