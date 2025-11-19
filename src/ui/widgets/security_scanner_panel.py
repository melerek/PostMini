"""
Security Scanner Panel Widget for PostMini API Client.

Displays security scan results and provides vulnerability reporting.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QComboBox, QSplitter, QCheckBox,
    QMessageBox, QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont
from typing import List, Dict, Optional
from datetime import datetime
import json


class SecurityScannerPanel(QWidget):
    """Widget for displaying and managing security scan results."""
    
    scan_requested = pyqtSignal()  # Emitted when user clicks "Scan Now"
    export_requested = pyqtSignal(int)  # Emitted with scan_id when export is requested
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_scan_id = None
        self.current_findings = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(8)
        
        # Title
        header_label = QLabel("🔒 Security Scanner")
        header_label.setStyleSheet("font-size: 13px; font-weight: 600; border: none;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Scan button
        self.scan_button = QPushButton("Scan Now")
        self.scan_button.setStyleSheet("font-size: 11px; padding: 4px 12px;")
        self.scan_button.clicked.connect(self.scan_requested.emit)
        header_layout.addWidget(self.scan_button)
        
        # Export button
        self.export_button = QPushButton("Export Report")
        self.export_button.setStyleSheet("font-size: 11px; padding: 4px 12px;")
        self.export_button.clicked.connect(self._on_export_clicked)
        self.export_button.setEnabled(False)
        header_layout.addWidget(self.export_button)
        
        main_layout.addWidget(header_widget)
        
        # Splitter for scans list and findings details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # ==================== SCANS LIST ====================
        scans_widget = QWidget()
        scans_layout = QVBoxLayout(scans_widget)
        scans_layout.setContentsMargins(12, 12, 12, 6)
        scans_layout.setSpacing(8)
        
        # Scans header
        scans_header_layout = QHBoxLayout()
        scans_header = QLabel("Recent Scans")
        scans_header.setStyleSheet("font-weight: 600;")
        scans_header_layout.addWidget(scans_header)
        
        # Filter combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Scans", None)
        self.filter_combo.addItem("Has Findings", "has_findings")
        self.filter_combo.addItem("Critical Issues", "critical")
        self.filter_combo.addItem("High Issues", "high")
        self.filter_combo.setMaximumWidth(150)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        scans_header_layout.addWidget(self.filter_combo)
        scans_header_layout.addStretch()
        
        scans_layout.addLayout(scans_header_layout)
        
        # Scans table
        self.scans_table = QTableWidget()
        self.scans_table.setColumnCount(6)
        self.scans_table.setHorizontalHeaderLabels([
            "Time", "URL", "Method", "Findings", "Critical", "High"
        ])
        self.scans_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.scans_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.scans_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.scans_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.scans_table.itemSelectionChanged.connect(self._on_scan_selected)
        self.scans_table.setAlternatingRowColors(True)
        scans_layout.addWidget(self.scans_table)
        
        splitter.addWidget(scans_widget)
        
        # ==================== FINDINGS DETAILS ====================
        findings_widget = QWidget()
        findings_layout = QVBoxLayout(findings_widget)
        findings_layout.setContentsMargins(12, 6, 12, 12)
        findings_layout.setSpacing(8)
        
        # Summary bar
        self.summary_label = QLabel("No scan selected")
        self.summary_label.setStyleSheet("font-weight: 600; padding: 6px; background: rgba(255,255,255,0.05); border-radius: 4px;")
        findings_layout.addWidget(self.summary_label)
        
        # Findings table
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
        
        # Finding details
        details_group = QGroupBox("Finding Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        findings_layout.addWidget(details_group)
        
        splitter.addWidget(findings_widget)
        
        # Set initial splitter sizes (60% scans, 40% findings)
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
    
    def load_scans(self, request_id: Optional[int] = None, collection_id: Optional[int] = None):
        """
        Load security scans from database.
        
        Args:
            request_id: Optional filter by request ID
            collection_id: Optional filter by collection ID
        """
        scans = self.db.get_security_scans(request_id, collection_id, limit=100)
        
        # Apply filter
        filter_type = self.filter_combo.currentData()
        if filter_type == "has_findings":
            scans = [s for s in scans if s['findings_count'] > 0]
        elif filter_type == "critical":
            scans = [s for s in scans if s['critical_count'] > 0]
        elif filter_type == "high":
            scans = [s for s in scans if s['high_count'] > 0]
        
        self.scans_table.setRowCount(len(scans))
        
        for row, scan in enumerate(scans):
            # Time
            timestamp = datetime.fromisoformat(scan['timestamp'])
            time_item = QTableWidgetItem(timestamp.strftime("%Y-%m-%d %H:%M"))
            time_item.setData(Qt.ItemDataRole.UserRole, scan['id'])
            self.scans_table.setItem(row, 0, time_item)
            
            # URL
            url = scan['url']
            if len(url) > 50:
                url = url[:47] + "..."
            self.scans_table.setItem(row, 1, QTableWidgetItem(url))
            
            # Method
            method_item = QTableWidgetItem(scan['method'])
            self.scans_table.setItem(row, 2, method_item)
            
            # Findings count
            findings_item = QTableWidgetItem(str(scan['findings_count']))
            findings_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scans_table.setItem(row, 3, findings_item)
            
            # Critical count
            critical_item = QTableWidgetItem(str(scan['critical_count']))
            critical_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if scan['critical_count'] > 0:
                critical_item.setForeground(QBrush(QColor("#F44336")))
                critical_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.scans_table.setItem(row, 4, critical_item)
            
            # High count
            high_item = QTableWidgetItem(str(scan['high_count']))
            high_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if scan['high_count'] > 0:
                high_item.setForeground(QBrush(QColor("#FF9800")))
            self.scans_table.setItem(row, 5, high_item)
        
        # Auto-select first scan if available
        if len(scans) > 0:
            self.scans_table.selectRow(0)
    
    def _on_scan_selected(self):
        """Handle scan selection in the table."""
        selected_items = self.scans_table.selectedItems()
        if not selected_items:
            self.current_scan_id = None
            self.current_findings = []
            self._clear_findings()
            return
        
        # Get scan ID from first column
        scan_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.current_scan_id = scan_id
        
        # Load scan details
        scan = self.db.get_security_scan(scan_id)
        if not scan:
            return
        
        # Update summary
        summary_parts = []
        if scan['critical_count'] > 0:
            summary_parts.append(f"🔴 {scan['critical_count']} Critical")
        if scan['high_count'] > 0:
            summary_parts.append(f"🟠 {scan['high_count']} High")
        if scan['medium_count'] > 0:
            summary_parts.append(f"🟡 {scan['medium_count']} Medium")
        if scan['low_count'] > 0:
            summary_parts.append(f"🔵 {scan['low_count']} Low")
        if scan['info_count'] > 0:
            summary_parts.append(f"ℹ️ {scan['info_count']} Info")
        
        if summary_parts:
            self.summary_label.setText(" | ".join(summary_parts))
        else:
            self.summary_label.setText("✅ No security issues found")
        
        # Enable export button
        self.export_button.setEnabled(True)
        
        # Load findings
        findings = self.db.get_security_findings(scan_id)
        self.current_findings = findings
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
            <pre style='background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; overflow-x: auto;'>{finding['evidence']}</pre>
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
    
    def _clear_findings(self):
        """Clear findings display."""
        self.findings_table.setRowCount(0)
        self.details_text.clear()
        self.summary_label.setText("No scan selected")
        self.export_button.setEnabled(False)
    
    def _on_filter_changed(self):
        """Handle filter combo change."""
        self.load_scans()
    
    def _on_export_clicked(self):
        """Handle export button click."""
        if self.current_scan_id:
            self.export_requested.emit(self.current_scan_id)
    
    def display_scan_results(self, scan_id: int):
        """
        Display specific scan results.
        
        Args:
            scan_id: ID of the scan to display
        """
        # Reload scans to show the new one
        self.load_scans()
        
        # Find and select the row with this scan_id
        for row in range(self.scans_table.rowCount()):
            item = self.scans_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == scan_id:
                self.scans_table.selectRow(row)
                break
