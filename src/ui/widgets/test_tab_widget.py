"""
Test Assertions Tab Widget

UI component for managing test assertions in the request editor.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import List, Dict, Optional

from src.features.test_engine import TestAssertion


class TestTabWidget(QWidget):
    """Widget for managing test assertions."""
    
    assertions_changed = pyqtSignal()  # Emitted when assertions are modified
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_request_id = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Info section
        info_group = QGroupBox("Test Assertions")
        info_layout = QVBoxLayout()
        
        info_label = QLabel(
            "Add test assertions to automatically validate API responses. "
            "Tests run after each request and results are saved."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Add assertion section
        add_group = QGroupBox("Add Assertion")
        add_layout = QVBoxLayout()
        
        # Type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Status Code",
            "Response Time",
            "Response Size",
            "Header",
            "Body Contains",
            "Body Equals",
            "JSON Path",
            "JSON Schema"
        ])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo, 1)
        add_layout.addLayout(type_layout)
        
        # Field input (for headers, JSON path)
        field_layout = QHBoxLayout()
        self.field_label = QLabel("Field:")
        field_layout.addWidget(self.field_label)
        self.field_input = QLineEdit()
        self.field_input.setPlaceholderText("e.g., Content-Type or user.name")
        field_layout.addWidget(self.field_input, 1)
        add_layout.addLayout(field_layout)
        
        # Operator selection
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel("Operator:"))
        
        self.operator_combo = QComboBox()
        operator_layout.addWidget(self.operator_combo, 1)
        add_layout.addLayout(operator_layout)
        
        # Expected value input
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Expected:"))
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Expected value")
        value_layout.addWidget(self.value_input, 1)
        add_layout.addLayout(value_layout)
        
        # Add button
        add_btn_layout = QHBoxLayout()
        add_btn_layout.addStretch()
        self.add_btn = QPushButton("➕ Add Assertion")
        self.add_btn.clicked.connect(self._add_assertion)
        self.add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 6px; }")
        add_btn_layout.addWidget(self.add_btn)
        add_layout.addLayout(add_btn_layout)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Assertions table
        assertions_group = QGroupBox("Active Assertions")
        assertions_layout = QVBoxLayout()
        
        self.assertions_table = QTableWidget()
        self.assertions_table.setColumnCount(6)
        self.assertions_table.setHorizontalHeaderLabels([
            "Enabled", "Type", "Field", "Operator", "Expected", "Actions"
        ])
        self.assertions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.assertions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.assertions_table.setAlternatingRowColors(True)
        assertions_layout.addWidget(self.assertions_table)
        
        # Bulk actions
        bulk_layout = QHBoxLayout()
        bulk_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self._clear_all_assertions)
        bulk_layout.addWidget(clear_btn)
        
        assertions_layout.addLayout(bulk_layout)
        
        assertions_group.setLayout(assertions_layout)
        layout.addWidget(assertions_group)
        
        # Update operator options based on initial type
        self._on_type_changed(self.type_combo.currentText())
    
    def _on_type_changed(self, assertion_type: str):
        """Update available operators based on assertion type."""
        self.operator_combo.clear()
        
        # Map display names to internal types
        type_map = {
            "Status Code": TestAssertion.TYPE_STATUS_CODE,
            "Response Time": TestAssertion.TYPE_RESPONSE_TIME,
            "Response Size": TestAssertion.TYPE_RESPONSE_SIZE,
            "Header": TestAssertion.TYPE_HEADER,
            "Body Contains": TestAssertion.TYPE_BODY_CONTAINS,
            "Body Equals": TestAssertion.TYPE_BODY_EQUALS,
            "JSON Path": TestAssertion.TYPE_JSON_PATH,
            "JSON Schema": TestAssertion.TYPE_JSON_SCHEMA
        }
        
        internal_type = type_map.get(assertion_type)
        
        # Show/hide field input based on type
        needs_field = internal_type in [
            TestAssertion.TYPE_HEADER,
            TestAssertion.TYPE_JSON_PATH
        ]
        self.field_input.setVisible(needs_field)
        self.field_label.setVisible(needs_field)
        
        # Set appropriate operators
        if internal_type in [TestAssertion.TYPE_STATUS_CODE, TestAssertion.TYPE_RESPONSE_TIME, TestAssertion.TYPE_RESPONSE_SIZE]:
            self.operator_combo.addItems([
                "equals", "not_equals", "greater_than", "less_than",
                "greater_equal", "less_equal"
            ])
        
        elif internal_type == TestAssertion.TYPE_HEADER:
            self.operator_combo.addItems([
                "equals", "not_equals", "contains", "not_contains",
                "exists", "not_exists", "matches_regex"
            ])
        
        elif internal_type == TestAssertion.TYPE_BODY_CONTAINS:
            self.operator_combo.addItems(["contains", "not_contains"])
        
        elif internal_type == TestAssertion.TYPE_BODY_EQUALS:
            self.operator_combo.addItems(["equals", "not_equals"])
        
        elif internal_type == TestAssertion.TYPE_JSON_PATH:
            self.operator_combo.addItems([
                "equals", "not_equals", "greater_than", "less_than",
                "contains", "exists", "not_exists", "matches_regex"
            ])
        
        elif internal_type == TestAssertion.TYPE_JSON_SCHEMA:
            self.operator_combo.addItems(["equals"])
    
    def _add_assertion(self):
        """Add a new assertion."""
        if not self.current_request_id:
            QMessageBox.warning(self, "No Request", "Please save the request first.")
            return
        
        assertion_type_display = self.type_combo.currentText()
        field = self.field_input.text().strip() if self.field_input.isVisible() else None
        operator = self.operator_combo.currentText()
        expected_value = self.value_input.text().strip()
        
        # Validation
        if not operator:
            QMessageBox.warning(self, "Validation Error", "Please select an operator.")
            return
        
        # Map display to internal type
        type_map = {
            "Status Code": TestAssertion.TYPE_STATUS_CODE,
            "Response Time": TestAssertion.TYPE_RESPONSE_TIME,
            "Response Size": TestAssertion.TYPE_RESPONSE_SIZE,
            "Header": TestAssertion.TYPE_HEADER,
            "Body Contains": TestAssertion.TYPE_BODY_CONTAINS,
            "Body Equals": TestAssertion.TYPE_BODY_EQUALS,
            "JSON Path": TestAssertion.TYPE_JSON_PATH,
            "JSON Schema": TestAssertion.TYPE_JSON_SCHEMA
        }
        
        assertion_type = type_map[assertion_type_display]
        
        # Check if field is required
        if assertion_type in [TestAssertion.TYPE_HEADER, TestAssertion.TYPE_JSON_PATH] and not field:
            QMessageBox.warning(self, "Validation Error", "Field is required for this assertion type.")
            return
        
        # Create assertion object for display
        assertion_data = {
            'type': assertion_type,
            'type_display': assertion_type_display,
            'field': field,
            'operator': operator,
            'expected_value': expected_value,
            'enabled': True
        }
        
        self._add_assertion_to_table(assertion_data)
        
        # Clear inputs
        self.field_input.clear()
        self.value_input.clear()
        
        # Emit signal
        self.assertions_changed.emit()
    
    def _add_assertion_to_table(self, assertion: Dict):
        """Add assertion to the table."""
        row = self.assertions_table.rowCount()
        self.assertions_table.insertRow(row)
        
        # Enabled checkbox
        enabled_widget = QWidget()
        enabled_layout = QHBoxLayout(enabled_widget)
        enabled_layout.setContentsMargins(0, 0, 0, 0)
        enabled_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(assertion.get('enabled', True))
        enabled_checkbox.stateChanged.connect(self.assertions_changed.emit)
        enabled_layout.addWidget(enabled_checkbox)
        self.assertions_table.setCellWidget(row, 0, enabled_widget)
        
        # Type
        type_item = QTableWidgetItem(assertion['type_display'])
        type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.assertions_table.setItem(row, 1, type_item)
        
        # Field
        field_item = QTableWidgetItem(assertion.get('field', '-'))
        field_item.setFlags(field_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.assertions_table.setItem(row, 2, field_item)
        
        # Operator
        operator_item = QTableWidgetItem(assertion['operator'])
        operator_item.setFlags(operator_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.assertions_table.setItem(row, 3, operator_item)
        
        # Expected value
        expected_item = QTableWidgetItem(assertion.get('expected_value', '-'))
        expected_item.setFlags(expected_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.assertions_table.setItem(row, 4, expected_item)
        
        # Actions (delete button)
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 0, 4, 0)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(30)
        delete_btn.setToolTip("Delete assertion")
        delete_btn.clicked.connect(lambda: self._delete_assertion(row))
        actions_layout.addWidget(delete_btn)
        
        self.assertions_table.setCellWidget(row, 5, actions_widget)
    
    def _delete_assertion(self, row: int):
        """Delete assertion at row."""
        self.assertions_table.removeRow(row)
        self.assertions_changed.emit()
    
    def _clear_all_assertions(self):
        """Clear all assertions."""
        if self.assertions_table.rowCount() == 0:
            return
        
        reply = QMessageBox.question(
            self, "Clear All",
            "Are you sure you want to delete all assertions?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.assertions_table.setRowCount(0)
            self.assertions_changed.emit()
    
    def set_request_id(self, request_id: Optional[int]):
        """Set the current request ID."""
        self.current_request_id = request_id
    
    def load_assertions(self, assertions: List[Dict]):
        """Load assertions into the table."""
        self.assertions_table.setRowCount(0)
        
        # Map internal types to display names
        display_map = {
            TestAssertion.TYPE_STATUS_CODE: "Status Code",
            TestAssertion.TYPE_RESPONSE_TIME: "Response Time",
            TestAssertion.TYPE_RESPONSE_SIZE: "Response Size",
            TestAssertion.TYPE_HEADER: "Header",
            TestAssertion.TYPE_BODY_CONTAINS: "Body Contains",
            TestAssertion.TYPE_BODY_EQUALS: "Body Equals",
            TestAssertion.TYPE_JSON_PATH: "JSON Path",
            TestAssertion.TYPE_JSON_SCHEMA: "JSON Schema"
        }
        
        for assertion in assertions:
            assertion_data = {
                'type': assertion['assertion_type'],
                'type_display': display_map.get(assertion['assertion_type'], assertion['assertion_type']),
                'field': assertion.get('field'),
                'operator': assertion['operator'],
                'expected_value': assertion.get('expected_value'),
                'enabled': assertion.get('enabled', True)
            }
            self._add_assertion_to_table(assertion_data)
    
    def get_assertions(self) -> List[Dict]:
        """Get all assertions from the table."""
        assertions = []
        
        # Map display names to internal types
        type_map = {
            "Status Code": TestAssertion.TYPE_STATUS_CODE,
            "Response Time": TestAssertion.TYPE_RESPONSE_TIME,
            "Response Size": TestAssertion.TYPE_RESPONSE_SIZE,
            "Header": TestAssertion.TYPE_HEADER,
            "Body Contains": TestAssertion.TYPE_BODY_CONTAINS,
            "Body Equals": TestAssertion.TYPE_BODY_EQUALS,
            "JSON Path": TestAssertion.TYPE_JSON_PATH,
            "JSON Schema": TestAssertion.TYPE_JSON_SCHEMA
        }
        
        for row in range(self.assertions_table.rowCount()):
            # Get enabled state
            enabled_widget = self.assertions_table.cellWidget(row, 0)
            enabled_checkbox = enabled_widget.findChild(QCheckBox)
            enabled = enabled_checkbox.isChecked() if enabled_checkbox else True
            
            # Get values
            type_display = self.assertions_table.item(row, 1).text()
            field = self.assertions_table.item(row, 2).text()
            field = field if field != '-' else None
            operator = self.assertions_table.item(row, 3).text()
            expected_value = self.assertions_table.item(row, 4).text()
            expected_value = expected_value if expected_value != '-' else None
            
            assertions.append({
                'assertion_type': type_map[type_display],
                'field': field,
                'operator': operator,
                'expected_value': expected_value,
                'enabled': enabled
            })
        
        return assertions
    
    def clear(self):
        """Clear all assertions."""
        self.assertions_table.setRowCount(0)
        self.current_request_id = None

