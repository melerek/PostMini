"""
Request History Panel Widget

This module provides a panel widget for viewing and managing request history.
Converted from HistoryDialog to be used as a floating panel.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QHeaderView, QComboBox,
    QTextEdit, QSplitter, QTabWidget, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from typing import Dict, Optional, List
from datetime import datetime
import json

from src.core.database import DatabaseManager
from src.features.security_scanner import SecurityFinding


class HistoryPanelWidget(QWidget):
    """
    Widget for viewing and managing request history.
    Designed to be used as a floating right panel.
    """
    
    # Signal emitted when user wants to replay a request
    replay_requested = pyqtSignal(dict)  # Emits history entry
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_entry_id = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with modern styling (similar to RecentRequestsWidget)
        header_widget = QWidget()
        header_widget.setObjectName("historyPanelHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 12, 12, 12)  # 4-point grid
        header_layout.setSpacing(8)  # 4-point grid
        
        # Title
        title = QLabel("Request History")
        title.setObjectName("historyPanelTitle")
        title.setStyleSheet("font-size: 14px; font-weight: 600;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Stats label
        self.stats_label = QLabel()
        self.stats_label.setProperty("class", "secondary")
        header_layout.addWidget(self.stats_label)
        
        # Close button
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("historyPanelCloseButton")
        self.close_btn.setText("✕")
        self.close_btn.setMaximumWidth(28)
        self.close_btn.setMaximumHeight(28)
        self.close_btn.setToolTip("Close history panel")
        header_layout.addWidget(self.close_btn)
        
        layout.addWidget(header_widget)
        
        # Content area with scroll support
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(12, 12, 12, 12)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        
        filter_label = QLabel("Filter:")
        filter_label.setProperty("class", "secondary")
        filter_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Requests",
            "Successful (2xx)",
            "Client Errors (4xx)",
            "Server Errors (5xx)",
            "Failed Requests"
        ])
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_history)
        filter_layout.addWidget(refresh_btn)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self._clear_history)
        filter_layout.addWidget(clear_btn)
        
        content_layout.addLayout(filter_layout)
        
        # Create splitter for table and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            'TIME', 'REQUEST', 'STATUS', 'TIME (S)', 'SIZE', 'COLLECTION'
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.history_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.history_table.doubleClicked.connect(self._on_double_click)
        
        # Enable horizontal scrolling
        self.history_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.history_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Style table for smaller text and compact headers
        self.history_table.setStyleSheet("""
            QTableWidget {
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 2px 4px;
            }
            QHeaderView::section {
                padding: 4px 6px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        
        # Hide TIME (S) and SIZE columns to save space
        self.history_table.setColumnHidden(3, True)  # TIME (S)
        self.history_table.setColumnHidden(4, True)  # SIZE
        
        splitter.addWidget(self.history_table)
        
        # Details panel
        details_widget = self._create_details_panel()
        splitter.addWidget(details_widget)
        
        splitter.setSizes([400, 300])
        content_layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.replay_btn = QPushButton("Replay Request")
        self.replay_btn.setEnabled(False)
        self.replay_btn.clicked.connect(self._replay_request)
        button_layout.addWidget(self.replay_btn)
        
        content_layout.addLayout(button_layout)
        
        # Add content to main layout
        layout.addWidget(content_widget)
        
        # Set minimum width for proper display
        self.setMinimumWidth(700)
    
    def _create_details_panel(self) -> QWidget:
        """Create the details panel for showing request/response details with tabs."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Request Details")
        details_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout.addWidget(details_label)
        
        # Tabs for different views (Request Details first, then response tabs)
        self.details_tabs = QTabWidget()
        
        # Request Details tab (FIRST - default)
        self.request_details_viewer = QTextEdit()
        self.request_details_viewer.setReadOnly(True)
        self.request_details_viewer.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.request_details_viewer.setFont(QFont("JetBrains Mono", 10))
        self.details_tabs.addTab(self.request_details_viewer, "Request Details")
        
        # Response Body tab
        self.response_body_viewer = QTextEdit()
        self.response_body_viewer.setReadOnly(True)
        self.response_body_viewer.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.response_body_viewer.setFont(QFont("JetBrains Mono", 10))
        self.details_tabs.addTab(self.response_body_viewer, "Response Body")
        
        # Response Headers tab
        self.response_headers_table = QTableWidget()
        self.response_headers_table.setColumnCount(2)
        self.response_headers_table.setHorizontalHeaderLabels(['Header', 'Value'])
        self.response_headers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.response_headers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.response_headers_table.verticalHeader().setVisible(False)
        self.details_tabs.addTab(self.response_headers_table, "Response Headers")
        
        # Security Scan tab (will be populated if scan_id exists)
        security_widget = QWidget()
        security_layout = QVBoxLayout(security_widget)
        security_layout.setContentsMargins(0, 0, 0, 0)
        
        # Security findings table
        self.security_findings_table = QTableWidget()
        self.security_findings_table.setColumnCount(3)
        self.security_findings_table.setHorizontalHeaderLabels(['Severity', 'Title', 'Category'])
        self.security_findings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.security_findings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.security_findings_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.security_findings_table.itemSelectionChanged.connect(self._on_security_finding_selected)
        security_layout.addWidget(self.security_findings_table, 2)
        
        # Security finding details
        self.security_details_viewer = QTextEdit()
        self.security_details_viewer.setReadOnly(True)
        self.security_details_viewer.setMaximumHeight(150)
        security_layout.addWidget(self.security_details_viewer, 1)
        
        self.details_tabs.addTab(security_widget, "Security Scan")
        self.security_scan_tab_index = self.details_tabs.count() - 1
        
        layout.addWidget(self.details_tabs)
        
        return widget
    
    def load_history(self):
        """Public method to load/refresh history when panel is shown."""
        self._load_history()
    
    def _load_history(self, filter_type: str = "All Requests"):
        """Load history entries based on filter."""
        try:
            # Get current filter if not specified
            if filter_type == "All Requests" and hasattr(self, 'filter_combo'):
                filter_type = self.filter_combo.currentText()
            
            # Get history based on filter
            if filter_type == "All Requests":
                history = self.db.get_request_history(limit=200)
            elif filter_type == "Successful (2xx)":
                history = []
                for entry in self.db.get_request_history(limit=200):
                    if entry.get('response_status') and 200 <= entry['response_status'] < 300:
                        history.append(entry)
            elif filter_type == "Client Errors (4xx)":
                history = []
                for entry in self.db.get_request_history(limit=200):
                    if entry.get('response_status') and 400 <= entry['response_status'] < 500:
                        history.append(entry)
            elif filter_type == "Server Errors (5xx)":
                history = []
                for entry in self.db.get_request_history(limit=200):
                    if entry.get('response_status') and 500 <= entry['response_status'] < 600:
                        history.append(entry)
            elif filter_type == "Failed Requests":
                history = self.db.get_failed_requests(limit=200)
            else:
                history = self.db.get_request_history(limit=200)
            
            # Update stats
            total_count = self.db.get_history_count()
            self.stats_label.setText(f"Total: {total_count} | Showing: {len(history)}")
            
            # Populate table
            self.history_table.setRowCount(len(history))
            
            for i, entry in enumerate(history):
                # Parse timestamp
                try:
                    dt = datetime.fromisoformat(entry['timestamp'])
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    # Invalid timestamp format, use as-is
                    time_str = entry['timestamp'][:16] if entry['timestamp'] else "N/A"
                
                # Time
                self.history_table.setItem(i, 0, QTableWidgetItem(time_str))
                
                # Request (METHOD + Request Name)
                request_name = entry.get('request_name', 'Untitled Request')
                if not request_name or request_name == '-':
                    request_name = 'Untitled Request'
                request_str = f"{entry['method']} {request_name}"
                request_item = QTableWidgetItem(request_str)
                request_item.setData(Qt.ItemDataRole.UserRole, entry['id'])
                self.history_table.setItem(i, 1, request_item)
                
                # Status
                status = entry.get('response_status')
                if status:
                    status_item = QTableWidgetItem(str(status))
                    # Color code status
                    if 200 <= status < 300:
                        status_item.setForeground(QColor(0, 150, 0))
                    elif 300 <= status < 400:
                        status_item.setForeground(QColor(0, 100, 200))
                    elif 400 <= status < 500:
                        status_item.setForeground(QColor(200, 100, 0))
                    elif status >= 500:
                        status_item.setForeground(QColor(200, 0, 0))
                    self.history_table.setItem(i, 2, status_item)
                else:
                    error_item = QTableWidgetItem("Error")
                    error_item.setForeground(QColor(200, 0, 0))
                    self.history_table.setItem(i, 2, error_item)
                
                # Response time
                resp_time = entry.get('response_time')
                if resp_time is not None:
                    self.history_table.setItem(i, 3, QTableWidgetItem(f"{resp_time:.3f}"))
                else:
                    self.history_table.setItem(i, 3, QTableWidgetItem("-"))
                
                # Size
                size = entry.get('response_size')
                if size is not None:
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    self.history_table.setItem(i, 4, QTableWidgetItem(size_str))
                else:
                    self.history_table.setItem(i, 4, QTableWidgetItem("-"))
                
                # Collection (get collection name from collection_id)
                collection_name = '-'
                collection_id = entry.get('collection_id')
                if collection_id:
                    collection = self.db.get_collection(collection_id)
                    if collection:
                        collection_name = collection['name']
                self.history_table.setItem(i, 5, QTableWidgetItem(collection_name))
            
            # Resize columns
            self.history_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load history: {str(e)}")
    
    def _on_filter_changed(self, filter_type: str):
        """Handle filter change."""
        self._load_history(filter_type)
    
    def _on_selection_changed(self):
        """Handle selection change in history table."""
        selected = self.history_table.selectedItems()
        if not selected:
            self.replay_btn.setEnabled(False)
            return
        
        # Get the history ID from the first column
        row = selected[0].row()
        method_item = self.history_table.item(row, 1)
        history_id = method_item.data(Qt.ItemDataRole.UserRole)
        
        self.current_entry_id = history_id
        self.replay_btn.setEnabled(True)
        
        # Load and display details
        self._load_entry_details(history_id)
    
    def _load_entry_details(self, history_id: int):
        """Load and display details for a history entry in all tabs."""
        try:
            entry = self.db.get_history_entry(history_id)
            if not entry:
                return
            
            # ===== Response Body Tab =====
            response_body = entry.get('response_body', '')
            if response_body:
                self.response_body_viewer.setPlainText(response_body)
            else:
                self.response_body_viewer.setPlainText("(No response body)")
            
            # ===== Response Headers Tab =====
            response_headers = entry.get('response_headers')
            if response_headers and isinstance(response_headers, dict):
                self.response_headers_table.setRowCount(len(response_headers))
                for i, (key, value) in enumerate(response_headers.items()):
                    self.response_headers_table.setItem(i, 0, QTableWidgetItem(key))
                    self.response_headers_table.setItem(i, 1, QTableWidgetItem(str(value)))
            else:
                self.response_headers_table.setRowCount(0)
            
            # ===== Request Details Tab =====
            request_text = f"Method: {entry['method']}\n"
            request_text += f"URL: {entry['url']}\n"
            
            if entry.get('response_status'):
                request_text += f"Status: {entry['response_status']}\n"
            
            if entry.get('response_time'):
                request_text += f"Response Time: {entry['response_time']:.3f}s\n"
            
            if entry.get('response_size'):
                size = entry['response_size']
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/(1024*1024):.1f} MB"
                request_text += f"Response Size: {size_str}\n"
            
            if entry.get('request_params'):
                request_text += "\nQuery Parameters:\n"
                for key, value in entry['request_params'].items():
                    request_text += f"  {key}: {value}\n"
            
            if entry.get('request_headers'):
                request_text += "\nRequest Headers:\n"
                for key, value in entry['request_headers'].items():
                    request_text += f"  {key}: {value}\n"
            
            if entry.get('request_body'):
                request_text += f"\nRequest Body:\n{entry['request_body']}\n"
            
            if entry.get('request_auth_type') and entry['request_auth_type'] != 'None':
                request_text += f"\nAuth Type: {entry['request_auth_type']}\n"
            
            if entry.get('error_message'):
                request_text += f"\n=== ERROR ===\n{entry['error_message']}\n"
            
            self.request_details_viewer.setPlainText(request_text)
            
            # ===== Security Scan Tab =====
            scan_id = entry.get('scan_id')
            if scan_id:
                # Load security findings
                findings = self.db.get_security_findings(scan_id)
                if findings:
                    self._populate_security_findings(findings)
                    # Update tab text to show finding count
                    self.details_tabs.setTabText(self.security_scan_tab_index, f"Security Scan ({len(findings)} findings)")
                else:
                    self._clear_security_findings()
                    self.details_tabs.setTabText(self.security_scan_tab_index, "Security Scan ✓")
            else:
                self._clear_security_findings()
                self.details_tabs.setTabText(self.security_scan_tab_index, "Security Scan")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load details: {str(e)}")
    
    def _populate_security_findings(self, findings: List[Dict]):
        """Populate security findings table."""
        self.security_findings_table.setRowCount(len(findings))
        
        severity_colors = {
            'Critical': QColor(244, 67, 54),    # Red
            'High': QColor(255, 152, 0),        # Orange
            'Medium': QColor(255, 193, 7),      # Yellow
            'Low': QColor(33, 150, 243),        # Blue
            'Info': QColor(158, 158, 158)       # Gray
        }
        
        for i, finding in enumerate(findings):
            # Severity
            severity_item = QTableWidgetItem(finding['severity'])
            severity_color = severity_colors.get(finding['severity'], QColor(158, 158, 158))
            severity_item.setForeground(severity_color)
            severity_item.setFont(QFont("", -1, QFont.Weight.Bold))
            severity_item.setData(Qt.ItemDataRole.UserRole, finding)  # Store full finding
            self.security_findings_table.setItem(i, 0, severity_item)
            
            # Title
            self.security_findings_table.setItem(i, 1, QTableWidgetItem(finding['title']))
            
            # Category
            self.security_findings_table.setItem(i, 2, QTableWidgetItem(finding.get('check_id', 'Unknown')))
        
        self.security_findings_table.resizeColumnsToContents()
        self.security_details_viewer.setPlainText("Select a finding to view details")
    
    def _clear_security_findings(self):
        """Clear security findings table and details."""
        self.security_findings_table.setRowCount(0)
        self.security_details_viewer.setPlainText("No security scan performed for this request")
    
    def _on_security_finding_selected(self):
        """Handle security finding selection."""
        selected = self.security_findings_table.selectedItems()
        if not selected:
            return
        
        # Get finding data from first column
        row = selected[0].row()
        severity_item = self.security_findings_table.item(row, 0)
        finding = severity_item.data(Qt.ItemDataRole.UserRole)
        
        if finding:
            # Format finding details
            details = f"Severity: {finding['severity']}\n"
            details += f"Category: {finding.get('check_id', 'Unknown')}\n"
            details += f"Title: {finding['title']}\n\n"
            details += f"Description:\n{finding['description']}\n\n"
            details += f"Recommendation:\n{finding['recommendation']}\n"
            
            if finding.get('evidence'):
                details += f"\nEvidence:\n{finding['evidence']}\n"
            
            if finding.get('cwe_id'):
                details += f"\nCWE: {finding['cwe_id']}\n"
            
            if finding.get('owasp_category'):
                details += f"OWASP: {finding['owasp_category']}\n"
            
            self.security_details_viewer.setPlainText(details)
    
    def _on_double_click(self):
        """Handle double-click on history entry (replay)."""
        if self.current_entry_id:
            self._replay_request()
    
    def _replay_request(self):
        """Replay the selected request."""
        if not self.current_entry_id:
            return
        
        try:
            entry = self.db.get_history_entry(self.current_entry_id)
            if entry:
                # Emit signal to replay
                self.replay_requested.emit(entry)
                # Don't close the panel - user might want to replay more
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to replay request: {str(e)}")
    
    def _clear_history(self):
        """Clear request history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all request history?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.clear_history()
                self._load_history()
                QMessageBox.information(self, "Success", "History cleared successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear history: {str(e)}")

