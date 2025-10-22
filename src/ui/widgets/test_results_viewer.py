"""
Test Results Viewer

UI component for displaying test execution results.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import List, Dict


class TestResultsViewer(QWidget):
    """Widget for displaying test results."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_collapsed = False
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with collapse icon
        header_frame = QFrame()
        header_frame.setProperty("class", "section-header")
        header_frame.setFixedHeight(32)
        header_frame.setCursor(Qt.CursorShape.PointingHandCursor)  # Clickable cursor
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(8)
        
        # Collapse icon (clickable)
        self.collapse_icon = QLabel("▼")
        self.collapse_icon.setFont(QFont("Arial", 10))
        self.collapse_icon.setFixedWidth(16)
        header_layout.addWidget(self.collapse_icon)
        
        # Header label
        header_label = QLabel("Test Results")
        header_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Make entire header clickable
        header_frame.mousePressEvent = lambda event: self._toggle_collapse()
        
        layout.addWidget(header_frame)
        
        # Content container (collapsible)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Summary section
        self.summary_group = QGroupBox("Test Summary")
        summary_layout = QVBoxLayout()
        
        self.summary_label = QLabel("No tests run yet")
        self.summary_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        summary_layout.addWidget(self.summary_label)
        
        # Stats
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total: 0")
        stats_layout.addWidget(self.total_label)
        
        self.passed_label = QLabel("✓ Passed: 0")
        self.passed_label.setProperty("class", "success-text")
        stats_layout.addWidget(self.passed_label)
        
        self.failed_label = QLabel("✗ Failed: 0")
        self.failed_label.setProperty("class", "error-text")
        stats_layout.addWidget(self.failed_label)
        
        self.pass_rate_label = QLabel("Pass Rate: 0%")
        stats_layout.addWidget(self.pass_rate_label)
        
        stats_layout.addStretch()
        summary_layout.addLayout(stats_layout)
        
        self.summary_group.setLayout(summary_layout)
        content_layout.addWidget(self.summary_group)
        
        # Results table
        results_group = QGroupBox("Test Results")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Status", "Type", "Field", "Expected", "Actual"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        content_layout.addWidget(results_group)
        
        layout.addWidget(self.content_widget)
        
        # Hide by default
        self.setVisible(False)
    
    def _toggle_collapse(self):
        """Toggle collapse/expand state of the test results."""
        self._is_collapsed = not self._is_collapsed
        
        if self._is_collapsed:
            self.content_widget.hide()
            self.collapse_icon.setText("▶")
        else:
            self.content_widget.show()
            self.collapse_icon.setText("▼")
    
    def display_results(self, results: List[Dict], summary: Dict):
        """
        Display test results.
        
        Args:
            results: List of test result dictionaries
            summary: Summary statistics dictionary
        """
        if not results:
            self.setVisible(False)
            return
        
        self.setVisible(True)
        
        # Ensure content is expanded when showing new results
        if self._is_collapsed:
            self._toggle_collapse()
        
        # Update summary
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        pass_rate = summary.get('pass_rate', 0)
        
        if passed == total:
            self.summary_label.setText("✅ All tests passed!")
            self.summary_label.setProperty("class", "success-text")
            self.summary_label.style().unpolish(self.summary_label)
            self.summary_label.style().polish(self.summary_label)
        elif failed == total:
            self.summary_label.setText("❌ All tests failed!")
            self.summary_label.setProperty("class", "error-text")
            self.summary_label.style().unpolish(self.summary_label)
            self.summary_label.style().polish(self.summary_label)
        else:
            self.summary_label.setText("⚠️ Some tests failed")
            self.summary_label.setProperty("class", "warning-text")
            self.summary_label.style().unpolish(self.summary_label)
            self.summary_label.style().polish(self.summary_label)
        
        self.total_label.setText(f"Total: {total}")
        self.passed_label.setText(f"✓ Passed: {passed}")
        self.failed_label.setText(f"✗ Failed: {failed}")
        self.pass_rate_label.setText(f"Pass Rate: {pass_rate:.1f}%")
        
        # Update results table
        self.results_table.setRowCount(0)
        
        for result in results:
            self._add_result_to_table(result)
    
    def _add_result_to_table(self, result: Dict):
        """Add a test result to the table."""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Status
        passed = result.get('passed', False)
        status_item = QTableWidgetItem("✓ PASS" if passed else "✗ FAIL")
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        if passed:
            status_item.setForeground(QColor("#4CAF50"))
            status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        else:
            status_item.setForeground(QColor("#f44336"))
            status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        self.results_table.setItem(row, 0, status_item)
        
        # Type
        assertion_type = result.get('assertion_type', '').replace('_', ' ').title()
        type_item = QTableWidgetItem(assertion_type)
        type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.results_table.setItem(row, 1, type_item)
        
        # Field
        field = result.get('field', '-')
        field_item = QTableWidgetItem(field if field else '-')
        field_item.setFlags(field_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.results_table.setItem(row, 2, field_item)
        
        # Expected
        operator = result.get('operator', '')
        expected = result.get('expected_value', '-')
        expected_text = f"{operator} {expected}" if expected and expected != '-' else operator
        expected_item = QTableWidgetItem(expected_text)
        expected_item.setFlags(expected_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.results_table.setItem(row, 3, expected_item)
        
        # Actual
        if passed:
            actual_text = str(result.get('actual_value', 'OK'))
        else:
            error = result.get('error_message')
            if error:
                actual_text = error
            else:
                actual_text = str(result.get('actual_value', 'Failed'))
        
        actual_item = QTableWidgetItem(actual_text)
        actual_item.setFlags(actual_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if not passed:
            actual_item.setForeground(QColor("#f44336"))
        self.results_table.setItem(row, 4, actual_item)
    
    def clear(self):
        """Clear all results."""
        self.results_table.setRowCount(0)
        self.summary_label.setText("No tests run yet")
        self.summary_label.setProperty("class", "")
        self.summary_label.style().unpolish(self.summary_label)
        self.summary_label.style().polish(self.summary_label)
        self.total_label.setText("Total: 0")
        self.passed_label.setText("✓ Passed: 0")
        self.failed_label.setText("✗ Failed: 0")
        self.pass_rate_label.setText("Pass Rate: 0%")
        self.setVisible(False)

