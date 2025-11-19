"""
Security Scan Tab Widget

This widget displays security scan results in the response panel.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTextEdit, QHeaderView,
    QGroupBox, QSplitter, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush
from typing import List, Dict, Optional


class SecurityScanTab(QWidget):
    """Widget for displaying security scan results in response panel."""
    
    export_requested = pyqtSignal()  # Emitted when user clicks export
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_findings = []
        self.current_scan_id = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with summary and export button
        header_widget = QWidget()
        header_widget.setStyleSheet("background: #2C3E50; border-radius: 4px; margin: 8px;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        self.summary_label = QLabel("No security scan performed yet")
        self.summary_label.setStyleSheet("font-weight: 600; color: #ECF0F1;")
        header_layout.addWidget(self.summary_label)
        
        header_layout.addStretch()
        
        self.export_button = QPushButton("Export Report")
        self.export_button.setStyleSheet("font-size: 11px; padding: 4px 12px;")
        self.export_button.clicked.connect(self.export_requested.emit)
        self.export_button.setEnabled(False)
        header_layout.addWidget(self.export_button)
        
        layout.addWidget(header_widget)
        
        # Splitter for findings table and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # ==================== FINDINGS TABLE ====================
        findings_widget = QWidget()
        findings_layout = QVBoxLayout(findings_widget)
        findings_layout.setContentsMargins(8, 0, 8, 4)
        findings_layout.setSpacing(4)
        
        findings_label = QLabel("Security Findings")
        findings_label.setStyleSheet("font-weight: 600; font-size: 12px; margin-top: 4px;")
        findings_layout.addWidget(findings_label)
        
        self.findings_table = QTableWidget()
        self.findings_table.setColumnCount(4)
        self.findings_table.setHorizontalHeaderLabels([
            "Severity", "Title", "CWE", "OWASP"
        ])
        self.findings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.findings_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.findings_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.findings_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.findings_table.itemSelectionChanged.connect(self._on_finding_selected)
        self.findings_table.setAlternatingRowColors(True)
        findings_layout.addWidget(self.findings_table)
        
        splitter.addWidget(findings_widget)
        
        # ==================== FINDING DETAILS ====================
        details_group = QGroupBox("Finding Details")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(8, 8, 8, 8)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        splitter.addWidget(details_group)
        
        # Set initial splitter sizes (60% findings, 40% details)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
    
    def set_scan_results(self, scan_id: int, findings: List[Dict], severity_stats: Dict[str, int]):
        """
        Display security scan results.
        
        Args:
            scan_id: Database ID of the scan
            findings: List of finding dictionaries
            severity_stats: Dictionary of severity counts
        """
        self.current_scan_id = scan_id
        self.current_findings = findings
        
        # Update summary
        summary_parts = []
        if severity_stats.get('critical', 0) > 0:
            summary_parts.append(f"🔴 {severity_stats['critical']} Critical")
        if severity_stats.get('high', 0) > 0:
            summary_parts.append(f"🟠 {severity_stats['high']} High")
        if severity_stats.get('medium', 0) > 0:
            summary_parts.append(f"🟡 {severity_stats['medium']} Medium")
        if severity_stats.get('low', 0) > 0:
            summary_parts.append(f"🔵 {severity_stats['low']} Low")
        if severity_stats.get('info', 0) > 0:
            summary_parts.append(f"ℹ️ {severity_stats['info']} Info")
        
        if summary_parts:
            self.summary_label.setText(" | ".join(summary_parts))
        else:
            self.summary_label.setText("✅ No security issues found")
        
        # Enable export button
        self.export_button.setEnabled(True)
        
        # Display findings
        self._display_findings(findings)
    
    def _display_findings(self, findings: List[Dict]):
        """Display findings in the table."""
        self.findings_table.setRowCount(len(findings))
        
        severity_colors = {
            'critical': QColor("#F44336"),
            'high': QColor("#FF9800"),
            'medium': QColor("#FFC107"),
            'low': QColor("#2196F3"),
            'info': QColor("#9E9E9E")
        }
        
        for row, finding in enumerate(findings):
            # Severity
            severity_item = QTableWidgetItem(finding['severity'].upper())
            severity_item.setData(Qt.ItemDataRole.UserRole, finding['id'])
            severity_item.setForeground(QBrush(severity_colors.get(finding['severity'], QColor("#FFFFFF"))))
            severity_item.setFont(QFont("", -1, QFont.Weight.Bold))
            severity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.findings_table.setItem(row, 0, severity_item)
            
            # Title
            self.findings_table.setItem(row, 1, QTableWidgetItem(finding['title']))
            
            # CWE
            cwe = finding.get('cwe_id', '-')
            self.findings_table.setItem(row, 2, QTableWidgetItem(cwe))
            
            # OWASP
            owasp = finding.get('owasp_category', '-')
            if owasp and len(owasp) > 30:
                owasp = owasp[:27] + "..."
            self.findings_table.setItem(row, 3, QTableWidgetItem(owasp))
        
        # Auto-select first finding
        if len(findings) > 0:
            self.findings_table.selectRow(0)
    
    def _on_finding_selected(self):
        """Handle finding selection in the table."""
        selected_items = self.findings_table.selectedItems()
        if not selected_items:
            self.details_text.clear()
            return
        
        finding_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # Find the finding in current_findings
        finding = next((f for f in self.current_findings if f['id'] == finding_id), None)
        if not finding:
            return
        
        # Format details
        details_html = f"""
        <h3 style='color: #4CAF50; margin-top: 0;'>{finding['title']}</h3>
        
        <p><strong>Check ID:</strong> {finding['check_id']}</p>
        <p><strong>Severity:</strong> <span style='color: {self._get_severity_color(finding['severity'])};'>{finding['severity'].upper()}</span></p>
        
        <h4>Description</h4>
        <p>{finding['description']}</p>
        
        <h4>Recommendation</h4>
        <p style='color: #4CAF50;'>{finding['recommendation']}</p>
        """
        
        if finding.get('evidence'):
            details_html += f"""
            <h4>Evidence</h4>
            <pre style='background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; overflow-x: auto;'>{self._escape_html(finding['evidence'])}</pre>
            """
        
        if finding.get('cwe_id'):
            details_html += f"<p><strong>CWE:</strong> {finding['cwe_id']}</p>"
        
        if finding.get('owasp_category'):
            details_html += f"<p><strong>OWASP Category:</strong> {finding['owasp_category']}</p>"
        
        self.details_text.setHtml(details_html)
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level."""
        colors = {
            'critical': '#F44336',
            'high': '#FF9800',
            'medium': '#FFC107',
            'low': '#2196F3',
            'info': '#9E9E9E'
        }
        return colors.get(severity, '#FFFFFF')
    
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
    
    def clear(self):
        """Clear scan results."""
        self.current_scan_id = None
        self.current_findings = []
        self.findings_table.setRowCount(0)
        self.details_text.clear()
        self.summary_label.setText("No security scan performed yet")
        self.export_button.setEnabled(False)
    
    def show_no_scan_message(self):
        """Show message when no scan was performed."""
        self.clear()
        self.summary_label.setText("💡 Enable 'Perform security scan on each request' in Settings to automatically scan responses")
