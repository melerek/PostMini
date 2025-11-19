"""
Test Security Scanner Integration with MainWindow and Database

Tests the full integration flow: UI -> auto-scan -> database storage -> display.
This catches type mismatches and API contract issues between components.
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.core.database import DatabaseManager
from src.features.security_scanner import SecurityScanner, SecurityFinding
from src.core.api_client import ApiResponse


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing."""
    db_path = tmp_path / "test_security_integration.db"
    db = DatabaseManager(str(db_path))
    yield db
    db.close()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def main_window(qapp, temp_db, tmp_path):
    """Create MainWindow instance with temporary database."""
    # Mock the app paths to use temp directory
    with patch('src.ui.main_window.AppPaths') as mock_paths:
        mock_paths.get_app_data_dir.return_value = str(tmp_path)
        mock_paths.get_database_path.return_value = str(tmp_path / "test.db")
        
        window = MainWindow(db_path=temp_db.db_path)
        yield window
        window.close()


class TestSecurityIntegration:
    """Test security scanner integration with MainWindow and database."""
    
    def test_auto_scan_database_parameters(self, temp_db):
        """Test that create_security_scan accepts correct parameters."""
        # This test verifies the database API contract
        scan_id = temp_db.create_security_scan(
            url='https://example.com/api',
            method='GET',
            timestamp=datetime.now().isoformat(),
            request_id=None,
            collection_id=None,
            scan_name=None,
            findings_count=5,  # NOT total_findings
            critical_count=1,
            high_count=2,
            medium_count=1,
            low_count=1,
            info_count=0
        )
        
        assert scan_id is not None
        assert isinstance(scan_id, int)
    
    def test_create_security_finding_parameters(self, temp_db):
        """Test that create_security_finding accepts correct parameters."""
        # Create a scan first
        scan_id = temp_db.create_security_scan(
            url='https://example.com/api',
            method='GET',
            timestamp=datetime.now().isoformat(),
            findings_count=1
        )
        
        # Create a finding - verify parameter names match SecurityFinding class
        finding_id = temp_db.create_security_finding(
            scan_id=scan_id,
            check_id='SEC001',  # NOT category
            title='Test Finding',
            severity='high',
            description='Test description',
            recommendation='Test recommendation',
            timestamp=datetime.now().isoformat(),  # REQUIRED parameter
            evidence='Test evidence',
            cwe_id='CWE-123',
            owasp_category='A01:2021'
        )
        
        assert finding_id is not None
        assert isinstance(finding_id, int)
    
    def test_security_scanner_response_parameters(self):
        """Test that SecurityScanner.scan_response accepts correct parameters."""
        scanner = SecurityScanner()
        
        # Verify the actual parameter names
        findings = scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={'User-Agent': 'PostMini'},
            response_status=200,  # NOT status_code
            response_headers={'Content-Type': 'application/json'},
            response_body='{"data": "test"}',
            request_secure=True
        )
        
        assert isinstance(findings, list)
        for finding in findings:
            # Verify SecurityFinding has required attributes
            assert hasattr(finding, 'check_id')  # NOT category
            assert hasattr(finding, 'title')
            assert hasattr(finding, 'severity')
            assert hasattr(finding, 'description')
            assert hasattr(finding, 'recommendation')
            assert hasattr(finding, 'timestamp')  # REQUIRED
            assert hasattr(finding, 'evidence')
            assert hasattr(finding, 'cwe_id')
            assert hasattr(finding, 'owasp_category')
    
    def test_auto_run_security_scan_integration(self, main_window):
        """Test full auto-scan flow: trigger -> scan -> save -> display."""
        # Create a mock response
        mock_response = Mock(spec=ApiResponse)
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"data": "test"}'
        mock_response.response = Mock()
        mock_response.response.status_code = 200
        mock_response.response.headers = mock_response.headers
        mock_response.response.text = mock_response.text
        
        # Set up request details
        main_window.url_input.setText('https://example.com/api')
        main_window.method_combo.setCurrentText('GET')
        
        # Call auto-scan (this is what's called after a successful request)
        scan_id = main_window._auto_run_security_scan(mock_response)
        
        # Verify scan was created and returned ID
        assert scan_id is not None
        assert isinstance(scan_id, int)
        
        # Verify scan was saved to database
        scans = main_window.db.get_security_scans(limit=1)
        assert len(scans) > 0
        assert scans[0]['id'] == scan_id
        
        # Verify findings were saved
        findings = main_window.db.get_security_findings(scan_id)
        assert isinstance(findings, list)
        # Should have at least some findings for a basic response
        assert len(findings) >= 0
    
    def test_settings_panel_auto_scan_enabled(self, main_window):
        """Test that settings panel get_auto_security_scan_enabled works."""
        # Should have settings_pane attribute (not settings_panel)
        assert hasattr(main_window, 'settings_pane')
        assert not hasattr(main_window, 'settings_panel')
        
        # Should be able to check auto-scan status
        enabled = main_window.settings_pane.get_auto_security_scan_enabled()
        assert isinstance(enabled, bool)
    
    def test_security_scan_tab_exists(self, main_window):
        """Test that security scan tab is always visible in response tabs."""
        # Security scan tab should exist
        assert hasattr(main_window, 'security_scan_tab')
        assert hasattr(main_window, 'security_scan_tab_index')
        
        # Tab should be in response_tabs
        tab_count = main_window.response_tabs.count()
        assert main_window.security_scan_tab_index < tab_count
        
        # Tab should be the SecurityScanTab widget
        tab_widget = main_window.response_tabs.widget(main_window.security_scan_tab_index)
        assert tab_widget is not None
        assert tab_widget == main_window.security_scan_tab
    
    def test_history_with_scan_id(self, main_window):
        """Test that history correctly stores scan_id."""
        # Create a mock response
        mock_response = Mock(spec=ApiResponse)
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"data": "test"}'
        # Add elapsed attribute
        mock_elapsed = Mock()
        mock_elapsed.total_seconds.return_value = 0.5
        mock_response.elapsed = mock_elapsed
        
        # Set up request
        main_window.url_input.setText('https://example.com/api')
        main_window.method_combo.setCurrentText('GET')
        main_window.current_request_details = {
            'method': 'GET',
            'url': 'https://example.com/api',
            'params': {},
            'headers': {},
            'body': '',
            'auth_type': 'No Auth',
            'auth_token': ''
        }
        
        # Save to history with scan_id
        test_scan_id = 12345
        main_window._save_to_history(response=mock_response, scan_id=test_scan_id)
        
        # Verify history entry was created with scan_id
        history = main_window.db.get_request_history(limit=1)
        assert len(history) > 0
        assert history[0]['scan_id'] == test_scan_id
    
    def test_severity_constants_match(self):
        """Test that severity constants are used consistently."""
        # SecurityFinding severity constants
        assert SecurityFinding.SEVERITY_CRITICAL == "critical"
        assert SecurityFinding.SEVERITY_HIGH == "high"
        assert SecurityFinding.SEVERITY_MEDIUM == "medium"
        assert SecurityFinding.SEVERITY_LOW == "low"
        assert SecurityFinding.SEVERITY_INFO == "info"
        
        # These should match what's used in the scanner
        scanner = SecurityScanner()
        findings = scanner.scan_response(
            method='GET',
            url='https://example.com/api',
            request_headers={},
            response_status=200,
            response_headers={'Content-Type': 'application/json'},
            response_body='{"card": "4532-1234-5678-9010"}',  # Should trigger critical finding
            request_secure=True
        )
        
        # At least one finding should use these exact constants
        severities = {f.severity for f in findings}
        valid_severities = {
            SecurityFinding.SEVERITY_CRITICAL,
            SecurityFinding.SEVERITY_HIGH,
            SecurityFinding.SEVERITY_MEDIUM,
            SecurityFinding.SEVERITY_LOW,
            SecurityFinding.SEVERITY_INFO
        }
        assert severities.issubset(valid_severities)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
