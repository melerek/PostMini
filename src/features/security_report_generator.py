"""
Security Report Generator Module

Generates HTML and JSON reports for security scan results.
"""

from typing import List, Dict, Optional
from datetime import datetime
import json


class SecurityReportGenerator:
    """Generates security scan reports in various formats."""
    
    def __init__(self, db):
        """
        Initialize the report generator.
        
        Args:
            db: DatabaseManager instance
        """
        self.db = db
    
    def generate_html_report(self, scan_id: int) -> str:
        """
        Generate an HTML report for a security scan.
        
        Args:
            scan_id: ID of the security scan
        
        Returns:
            HTML report as string
        """
        scan = self.db.get_security_scan(scan_id)
        if not scan:
            return "<html><body><h1>Error: Scan not found</h1></body></html>"
        
        findings = self.db.get_security_findings(scan_id)
        
        # Generate report
        html = self._generate_html_template(scan, findings)
        return html
    
    def generate_json_report(self, scan_id: int) -> str:
        """
        Generate a JSON report for a security scan.
        
        Args:
            scan_id: ID of the security scan
        
        Returns:
            JSON report as string
        """
        scan = self.db.get_security_scan(scan_id)
        if not scan:
            return json.dumps({"error": "Scan not found"}, indent=2)
        
        findings = self.db.get_security_findings(scan_id)
        
        report = {
            "scan_info": {
                "scan_id": scan['id'],
                "timestamp": scan['timestamp'],
                "url": scan['url'],
                "method": scan['method'],
                "scan_name": scan.get('scan_name', 'Unnamed Scan')
            },
            "summary": {
                "total_findings": scan['findings_count'],
                "critical": scan['critical_count'],
                "high": scan['high_count'],
                "medium": scan['medium_count'],
                "low": scan['low_count'],
                "info": scan['info_count']
            },
            "findings": [
                {
                    "check_id": f['check_id'],
                    "title": f['title'],
                    "severity": f['severity'],
                    "description": f['description'],
                    "recommendation": f['recommendation'],
                    "evidence": f.get('evidence'),
                    "cwe_id": f.get('cwe_id'),
                    "owasp_category": f.get('owasp_category'),
                    "timestamp": f['timestamp']
                }
                for f in findings
            ]
        }
        
        return json.dumps(report, indent=2)
    
    def _generate_html_template(self, scan: Dict, findings: List[Dict]) -> str:
        """Generate HTML report template."""
        
        timestamp = datetime.fromisoformat(scan['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        
        # Build findings HTML
        findings_html = ""
        
        if not findings:
            findings_html = """
            <div class="finding-card success">
                <h3>✅ No Security Issues Found</h3>
                <p>The security scan did not detect any vulnerabilities in this API endpoint.</p>
            </div>
            """
        else:
            for finding in findings:
                severity_class = finding['severity']
                severity_icon = self._get_severity_icon(finding['severity'])
                
                evidence_html = ""
                if finding.get('evidence'):
                    evidence_html = f"""
                    <div class="evidence">
                        <strong>Evidence:</strong>
                        <pre>{self._escape_html(finding['evidence'][:500])}</pre>
                    </div>
                    """
                
                metadata_html = ""
                if finding.get('cwe_id') or finding.get('owasp_category'):
                    metadata_parts = []
                    if finding.get('cwe_id'):
                        metadata_parts.append(f"<span class='badge'>{finding['cwe_id']}</span>")
                    if finding.get('owasp_category'):
                        metadata_parts.append(f"<span class='badge'>{finding['owasp_category']}</span>")
                    metadata_html = f"<div class='metadata'>{' '.join(metadata_parts)}</div>"
                
                findings_html += f"""
                <div class="finding-card {severity_class}">
                    <div class="finding-header">
                        <h3>{severity_icon} {finding['title']}</h3>
                        <span class="severity-badge {severity_class}">{finding['severity'].upper()}</span>
                    </div>
                    <p class="check-id">Check ID: {finding['check_id']}</p>
                    {metadata_html}
                    <div class="finding-section">
                        <strong>Description:</strong>
                        <p>{finding['description']}</p>
                    </div>
                    <div class="finding-section recommendation">
                        <strong>Recommendation:</strong>
                        <p>{finding['recommendation']}</p>
                    </div>
                    {evidence_html}
                </div>
                """
        
        # Build summary statistics
        summary_cards = ""
        stats = [
            ('critical', scan['critical_count'], '#F44336', '🔴'),
            ('high', scan['high_count'], '#FF9800', '🟠'),
            ('medium', scan['medium_count'], '#FFC107', '🟡'),
            ('low', scan['low_count'], '#2196F3', '🔵'),
            ('info', scan['info_count'], '#9E9E9E', 'ℹ️')
        ]
        
        for severity, count, color, icon in stats:
            summary_cards += f"""
            <div class="summary-card" style="border-left-color: {color};">
                <div class="summary-icon">{icon}</div>
                <div class="summary-content">
                    <div class="summary-count">{count}</div>
                    <div class="summary-label">{severity.capitalize()}</div>
                </div>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Security Scan Report - {scan['url']}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: #f5f5f5;
                    color: #333;
                    line-height: 1.6;
                    padding: 20px;
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
                    padding: 40px 30px;
                }}
                
                .header h1 {{
                    font-size: 28px;
                    margin-bottom: 10px;
                }}
                
                .header .subtitle {{
                    opacity: 0.9;
                    font-size: 14px;
                }}
                
                .scan-info {{
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 6px;
                    margin-top: 20px;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                }}
                
                .scan-info-item {{
                    display: flex;
                    flex-direction: column;
                }}
                
                .scan-info-label {{
                    font-size: 12px;
                    opacity: 0.8;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                .scan-info-value {{
                    font-size: 16px;
                    font-weight: 600;
                    margin-top: 5px;
                }}
                
                .summary {{
                    padding: 30px;
                    border-bottom: 1px solid #eee;
                }}
                
                .summary h2 {{
                    margin-bottom: 20px;
                    color: #667eea;
                }}
                
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                }}
                
                .summary-card {{
                    background: #f9f9f9;
                    border-left: 4px solid;
                    padding: 20px;
                    border-radius: 6px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }}
                
                .summary-icon {{
                    font-size: 32px;
                }}
                
                .summary-content {{
                    flex: 1;
                }}
                
                .summary-count {{
                    font-size: 28px;
                    font-weight: 700;
                    line-height: 1;
                }}
                
                .summary-label {{
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-top: 5px;
                }}
                
                .findings {{
                    padding: 30px;
                }}
                
                .findings h2 {{
                    margin-bottom: 20px;
                    color: #667eea;
                }}
                
                .finding-card {{
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-left: 4px solid;
                    border-radius: 6px;
                    padding: 25px;
                    margin-bottom: 20px;
                }}
                
                .finding-card.critical {{
                    border-left-color: #F44336;
                }}
                
                .finding-card.high {{
                    border-left-color: #FF9800;
                }}
                
                .finding-card.medium {{
                    border-left-color: #FFC107;
                }}
                
                .finding-card.low {{
                    border-left-color: #2196F3;
                }}
                
                .finding-card.info {{
                    border-left-color: #9E9E9E;
                }}
                
                .finding-card.success {{
                    border-left-color: #4CAF50;
                    background: #f1f8f4;
                }}
                
                .finding-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 15px;
                }}
                
                .finding-header h3 {{
                    flex: 1;
                    font-size: 18px;
                    color: #333;
                }}
                
                .severity-badge {{
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                    color: white;
                }}
                
                .severity-badge.critical {{
                    background: #F44336;
                }}
                
                .severity-badge.high {{
                    background: #FF9800;
                }}
                
                .severity-badge.medium {{
                    background: #FFC107;
                    color: #333;
                }}
                
                .severity-badge.low {{
                    background: #2196F3;
                }}
                
                .severity-badge.info {{
                    background: #9E9E9E;
                }}
                
                .check-id {{
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 10px;
                }}
                
                .metadata {{
                    margin-bottom: 15px;
                }}
                
                .badge {{
                    display: inline-block;
                    background: #e0e0e0;
                    color: #666;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                    margin-right: 8px;
                }}
                
                .finding-section {{
                    margin: 15px 0;
                }}
                
                .finding-section strong {{
                    display: block;
                    color: #667eea;
                    margin-bottom: 8px;
                    font-size: 14px;
                }}
                
                .finding-section p {{
                    color: #555;
                    line-height: 1.6;
                }}
                
                .recommendation {{
                    background: #f1f8f4;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 3px solid #4CAF50;
                }}
                
                .recommendation strong {{
                    color: #4CAF50;
                }}
                
                .evidence {{
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 6px;
                    margin-top: 15px;
                }}
                
                .evidence pre {{
                    background: #2d2d2d;
                    color: #f8f8f2;
                    padding: 12px;
                    border-radius: 4px;
                    overflow-x: auto;
                    font-size: 12px;
                    margin-top: 8px;
                }}
                
                .footer {{
                    padding: 20px 30px;
                    background: #f9f9f9;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
                
                @media print {{
                    body {{
                        background: white;
                        padding: 0;
                    }}
                    
                    .container {{
                        box-shadow: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Security Scan Report</h1>
                    <p class="subtitle">Generated by PostMini API Client</p>
                    
                    <div class="scan-info">
                        <div class="scan-info-item">
                            <div class="scan-info-label">Endpoint</div>
                            <div class="scan-info-value">{scan['url']}</div>
                        </div>
                        <div class="scan-info-item">
                            <div class="scan-info-label">Method</div>
                            <div class="scan-info-value">{scan['method']}</div>
                        </div>
                        <div class="scan-info-item">
                            <div class="scan-info-label">Scan Time</div>
                            <div class="scan-info-value">{timestamp}</div>
                        </div>
                        <div class="scan-info-item">
                            <div class="scan-info-label">Total Findings</div>
                            <div class="scan-info-value">{scan['findings_count']}</div>
                        </div>
                    </div>
                </div>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <div class="summary-grid">
                        {summary_cards}
                    </div>
                </div>
                
                <div class="findings">
                    <h2>Findings Details</h2>
                    {findings_html}
                </div>
                
                <div class="footer">
                    <p>Report generated by PostMini Security Scanner | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p>All checks performed locally without external network calls</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_severity_icon(self, severity: str) -> str:
        """Get emoji icon for severity level."""
        icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': 'ℹ️'
        }
        return icons.get(severity, '❓')
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))
