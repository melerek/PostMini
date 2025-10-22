"""
Test Report Generators

This module provides functionality to export test results in various formats:
- HTML (beautiful, shareable reports)
- JUnit XML (CI/CD integration)
- JSON (machine-readable)
- CSV (spreadsheet-friendly)
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET
from src.features.test_engine import TestResult, TestAssertion


class TestReportGenerator:
    """Base class for test report generation."""
    
    @staticmethod
    def generate_summary(test_results: List[TestResult]) -> Dict:
        """
        Generate summary statistics from test results.
        
        Args:
            test_results: List of TestResult objects
            
        Returns:
            Dictionary with summary stats
        """
        total = len(test_results)
        passed = sum(1 for r in test_results if r.passed)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate
        }


class HTMLReportGenerator(TestReportGenerator):
    """Generate beautiful HTML test reports."""
    
    @staticmethod
    def generate(test_results: List[TestResult], metadata: Optional[Dict] = None) -> str:
        """
        Generate HTML report.
        
        Args:
            test_results: List of TestResult objects
            metadata: Optional metadata (collection_name, environment, etc.)
            
        Returns:
            HTML string
        """
        metadata = metadata or {}
        summary = HTMLReportGenerator.generate_summary(test_results)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Separate passed and failed tests
        passed_tests = [r for r in test_results if r.passed]
        failed_tests = [r for r in test_results if not r.passed]
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {metadata.get('collection_name', 'API Tests')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #F5F7FA;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #F8F9FA;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .stat-card.total .stat-value {{ color: #667eea; }}
        .stat-card.passed .stat-value {{ color: #4CAF50; }}
        .stat-card.failed .stat-value {{ color: #F44336; }}
        .stat-card.rate .stat-value {{ color: #FF9800; }}
        
        .metadata {{
            padding: 20px 30px;
            background: #FFF9E6;
            border-left: 4px solid #FFC107;
            margin: 0 30px 20px;
            border-radius: 4px;
        }}
        
        .metadata-row {{
            display: flex;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        
        .metadata-label {{
            font-weight: 600;
            width: 150px;
            color: #666;
        }}
        
        .metadata-value {{
            color: #333;
        }}
        
        .section {{
            padding: 30px;
        }}
        
        .section-title {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #E0E0E0;
        }}
        
        .test-item {{
            background: #F8F9FA;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 12px;
            border-left: 4px solid #E0E0E0;
        }}
        
        .test-item.passed {{
            border-left-color: #4CAF50;
            background: #E8F5E9;
        }}
        
        .test-item.failed {{
            border-left-color: #F44336;
            background: #FFEBEE;
        }}
        
        .test-header {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .test-icon {{
            font-size: 20px;
            margin-right: 10px;
        }}
        
        .test-name {{
            font-weight: 600;
            font-size: 16px;
            flex: 1;
        }}
        
        .test-details {{
            margin-left: 30px;
            font-size: 14px;
            color: #666;
        }}
        
        .test-detail-row {{
            margin: 4px 0;
        }}
        
        .test-detail-label {{
            display: inline-block;
            width: 100px;
            font-weight: 500;
            color: #888;
        }}
        
        .error-message {{
            background: #FFF3E0;
            border: 1px solid #FFB74D;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #E65100;
        }}
        
        .collapsible {{
            cursor: pointer;
            user-select: none;
        }}
        
        .collapsible:hover {{
            opacity: 0.8;
        }}
        
        .collapsed-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        
        .collapsed-content.expanded {{
            max-height: 2000px;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 13px;
            border-top: 1px solid #E0E0E0;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .badge.success {{ background: #4CAF50; color: white; }}
        .badge.failure {{ background: #F44336; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🎯 {metadata.get('collection_name', 'API Test Report')}</h1>
            <div class="subtitle">Generated on {timestamp}</div>
        </div>
        
        <!-- Summary Statistics -->
        <div class="summary">
            <div class="stat-card total">
                <div class="stat-value">{summary['total']}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card passed">
                <div class="stat-value">{summary['passed']}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-value">{summary['failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card rate">
                <div class="stat-value">{summary['pass_rate']:.1f}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
        </div>
        
        <!-- Metadata -->
        {HTMLReportGenerator._generate_metadata_html(metadata)}
        
        <!-- Failed Tests -->
        {HTMLReportGenerator._generate_failed_tests_html(failed_tests)}
        
        <!-- Passed Tests -->
        {HTMLReportGenerator._generate_passed_tests_html(passed_tests)}
        
        <!-- Footer -->
        <div class="footer">
            Generated by PostMini - Desktop API Client
        </div>
    </div>
    
    <script>
        // Toggle collapsible sections
        document.querySelectorAll('.collapsible').forEach(item => {{
            item.addEventListener('click', function() {{
                const content = this.nextElementSibling;
                content.classList.toggle('expanded');
            }});
        }});
    </script>
</body>
</html>
"""
        return html
    
    @staticmethod
    def _generate_metadata_html(metadata: Dict) -> str:
        """Generate metadata section HTML."""
        if not metadata:
            return ""
        
        rows = []
        if 'collection_name' in metadata:
            rows.append(f'<div class="metadata-row"><span class="metadata-label">Collection:</span><span class="metadata-value">{metadata["collection_name"]}</span></div>')
        if 'environment' in metadata:
            rows.append(f'<div class="metadata-row"><span class="metadata-label">Environment:</span><span class="metadata-value">{metadata["environment"]}</span></div>')
        if 'base_url' in metadata:
            rows.append(f'<div class="metadata-row"><span class="metadata-label">Base URL:</span><span class="metadata-value">{metadata["base_url"]}</span></div>')
        if 'duration' in metadata:
            rows.append(f'<div class="metadata-row"><span class="metadata-label">Duration:</span><span class="metadata-value">{metadata["duration"]:.2f}s</span></div>')
        
        if rows:
            return f'<div class="metadata">{"".join(rows)}</div>'
        return ""
    
    @staticmethod
    def _generate_failed_tests_html(failed_tests: List[TestResult]) -> str:
        """Generate failed tests section HTML."""
        if not failed_tests:
            return ""
        
        html = '<div class="section">'
        html += f'<div class="section-title">❌ Failed Tests ({len(failed_tests)})</div>'
        
        for result in failed_tests:
            assertion = result.assertion
            html += f'''
            <div class="test-item failed">
                <div class="test-header">
                    <span class="test-icon">❌</span>
                    <span class="test-name">{assertion.type}: {assertion.field or assertion.operator}</span>
                    <span class="badge failure">Failed</span>
                </div>
                <div class="test-details">
                    <div class="test-detail-row">
                        <span class="test-detail-label">Type:</span>
                        {assertion.type}
                    </div>
                    <div class="test-detail-row">
                        <span class="test-detail-label">Operator:</span>
                        {assertion.operator}
                    </div>
                    <div class="test-detail-row">
                        <span class="test-detail-label">Expected:</span>
                        {assertion.expected_value or 'N/A'}
                    </div>
                    <div class="test-detail-row">
                        <span class="test-detail-label">Actual:</span>
                        {result.actual_value or 'N/A'}
                    </div>
                </div>
                {f'<div class="error-message">{result.error_message}</div>' if result.error_message else ''}
            </div>
            '''
        
        html += '</div>'
        return html
    
    @staticmethod
    def _generate_passed_tests_html(passed_tests: List[TestResult]) -> str:
        """Generate passed tests section HTML."""
        if not passed_tests:
            return ""
        
        html = '<div class="section">'
        html += f'<div class="section-title collapsible">✅ Passed Tests ({len(passed_tests)}) - Click to expand</div>'
        html += '<div class="collapsed-content">'
        
        for result in passed_tests:
            assertion = result.assertion
            html += f'''
            <div class="test-item passed">
                <div class="test-header">
                    <span class="test-icon">✅</span>
                    <span class="test-name">{assertion.type}: {assertion.field or assertion.operator}</span>
                    <span class="badge success">Passed</span>
                </div>
                <div class="test-details">
                    <div class="test-detail-row">
                        <span class="test-detail-label">Actual:</span>
                        {result.actual_value or 'N/A'}
                    </div>
                </div>
            </div>
            '''
        
        html += '</div></div>'
        return html


class JUnitXMLGenerator(TestReportGenerator):
    """Generate JUnit XML reports for CI/CD integration."""
    
    @staticmethod
    def generate(test_results: List[TestResult], metadata: Optional[Dict] = None) -> str:
        """
        Generate JUnit XML report.
        
        Args:
            test_results: List of TestResult objects
            metadata: Optional metadata
            
        Returns:
            XML string
        """
        metadata = metadata or {}
        summary = JUnitXMLGenerator.generate_summary(test_results)
        
        # Create root testsuites element
        testsuites = ET.Element('testsuites')
        testsuites.set('tests', str(summary['total']))
        testsuites.set('failures', str(summary['failed']))
        testsuites.set('time', str(metadata.get('duration', 0)))
        
        # Create testsuite element
        testsuite = ET.SubElement(testsuites, 'testsuite')
        testsuite.set('name', metadata.get('collection_name', 'API Tests'))
        testsuite.set('tests', str(summary['total']))
        testsuite.set('failures', str(summary['failed']))
        testsuite.set('time', str(metadata.get('duration', 0)))
        testsuite.set('timestamp', datetime.now().isoformat())
        
        # Add metadata as properties
        properties = ET.SubElement(testsuite, 'properties')
        if 'environment' in metadata:
            prop = ET.SubElement(properties, 'property')
            prop.set('name', 'environment')
            prop.set('value', metadata['environment'])
        if 'base_url' in metadata:
            prop = ET.SubElement(properties, 'property')
            prop.set('name', 'base_url')
            prop.set('value', metadata['base_url'])
        
        # Add test cases
        for result in test_results:
            assertion = result.assertion
            testcase = ET.SubElement(testsuite, 'testcase')
            testcase.set('name', f"{assertion.type}: {assertion.field or assertion.operator}")
            testcase.set('classname', f"{metadata.get('collection_name', 'APITests')}")
            testcase.set('time', '0')
            
            if not result.passed:
                failure = ET.SubElement(testcase, 'failure')
                failure.set('message', result.error_message or 'Assertion failed')
                failure.set('type', assertion.type)
                failure.text = f"Expected: {assertion.expected_value}\nActual: {result.actual_value}"
        
        # Convert to string
        return ET.tostring(testsuites, encoding='unicode', method='xml')


class JSONReportGenerator(TestReportGenerator):
    """Generate JSON reports for machine-readable output."""
    
    @staticmethod
    def generate(test_results: List[TestResult], metadata: Optional[Dict] = None) -> str:
        """
        Generate JSON report.
        
        Args:
            test_results: List of TestResult objects
            metadata: Optional metadata
            
        Returns:
            JSON string
        """
        metadata = metadata or {}
        summary = JSONReportGenerator.generate_summary(test_results)
        
        report = {
            'summary': summary,
            'metadata': {
                'collection_name': metadata.get('collection_name', ''),
                'environment': metadata.get('environment', ''),
                'base_url': metadata.get('base_url', ''),
                'duration': metadata.get('duration', 0),
                'timestamp': datetime.now().isoformat()
            },
            'tests': []
        }
        
        for result in test_results:
            assertion = result.assertion
            report['tests'].append({
                'name': f"{assertion.type}: {assertion.field or assertion.operator}",
                'passed': result.passed,
                'type': assertion.type,
                'operator': assertion.operator,
                'field': assertion.field,
                'expected_value': assertion.expected_value,
                'actual_value': str(result.actual_value) if result.actual_value is not None else None,
                'error_message': result.error_message
            })
        
        return json.dumps(report, indent=2)


class CSVReportGenerator(TestReportGenerator):
    """Generate CSV reports for spreadsheet analysis."""
    
    @staticmethod
    def generate(test_results: List[TestResult], metadata: Optional[Dict] = None) -> str:
        """
        Generate CSV report.
        
        Args:
            test_results: List of TestResult objects
            metadata: Optional metadata
            
        Returns:
            CSV string
        """
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Test Name', 'Status', 'Type', 'Operator', 'Field', 'Expected', 'Actual', 'Error'])
        
        # Write test results
        for result in test_results:
            assertion = result.assertion
            writer.writerow([
                f"{assertion.type}: {assertion.field or assertion.operator}",
                'PASS' if result.passed else 'FAIL',
                assertion.type,
                assertion.operator,
                assertion.field or '',
                assertion.expected_value or '',
                str(result.actual_value) if result.actual_value is not None else '',
                result.error_message or ''
            ])
        
        return output.getvalue()

