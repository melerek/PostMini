"""
Test Assertions Tab Widget

UI component for managing test assertions in the request editor.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QMessageBox, QGroupBox, QGridLayout, QFormLayout, QScrollArea, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QAction
from typing import List, Dict, Optional

from src.features.test_engine import TestAssertion
from src.ui.widgets.variable_highlight_delegate import HighlightedLineEdit


class TestTabWidget(QWidget):
    """Widget for managing test assertions."""
    
    assertions_changed = pyqtSignal()  # Emitted when assertions are modified
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_request_id = None
        self.environment_manager = None  # Will be set from main window
        self._init_ui()
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution in input fields."""
        self.environment_manager = env_manager
        if hasattr(self, 'field_input'):
            self.field_input.set_environment_manager(env_manager)
        if hasattr(self, 'value_input'):
            self.value_input.set_environment_manager(env_manager)
    
    def set_main_window(self, main_window):
        """Set the main window reference for collection variable resolution."""
        self.main_window = main_window
        if hasattr(self, 'field_input'):
            self.field_input.set_main_window(main_window)
        if hasattr(self, 'value_input'):
            self.value_input.set_main_window(main_window)
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        # Content widget
        content = QWidget()
        content.setObjectName("testTabContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Info label (compact)
        info_label = QLabel(
            "Add test assertions to automatically validate API responses. Tests run after each request."
        )
        info_label.setWordWrap(True)
        info_label.setProperty("class", "secondary-text")
        layout.addWidget(info_label)
        
        # Single-line form
        form_layout = QHBoxLayout()
        form_layout.setSpacing(8)
        
        # Type
        form_layout.addWidget(QLabel("Type:"))
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
        self.type_combo.setMinimumWidth(120)
        self.type_combo.setFixedHeight(24)
        self.type_combo.setStyleSheet("""
            QComboBox {
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                font-size: 11px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 20px;
                padding: 4px 8px;
            }
        """)
        form_layout.addWidget(self.type_combo)
        
        # Field (conditional)
        self.field_label = QLabel("Field:")
        form_layout.addWidget(self.field_label)
        self.field_input = HighlightedLineEdit()
        self.field_input.setPlaceholderText("e.g., Content-Type")
        self.field_input.setMinimumWidth(100)
        form_layout.addWidget(self.field_input)
        
        # Operator
        form_layout.addWidget(QLabel("Op:"))
        self.operator_combo = QComboBox()
        self.operator_combo.setMinimumWidth(100)
        self.operator_combo.setFixedHeight(24)
        self.operator_combo.setStyleSheet("""
            QComboBox {
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                font-size: 11px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 20px;
                padding: 4px 8px;
            }
        """)
        form_layout.addWidget(self.operator_combo)
        
        # Expected
        form_layout.addWidget(QLabel("Expected:"))
        self.value_input = HighlightedLineEdit()
        self.value_input.setPlaceholderText("Value")
        self.value_input.setMinimumWidth(80)
        form_layout.addWidget(self.value_input, 1)  # Stretch
        
        # Add button
        self.add_btn = QPushButton("Add")
        self.add_btn.setProperty("class", "primary")
        self.add_btn.clicked.connect(self._add_assertion)
        form_layout.addWidget(self.add_btn)
        
        layout.addLayout(form_layout)
        
        # Separator (uses theme-aware styling from QSS)
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: palette(mid);")
        layout.addWidget(separator)
        
        # Assertions table header
        header_layout = QHBoxLayout()
        header_label = QLabel("Active Assertions")
        header_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_all_assertions)
        header_layout.addWidget(clear_btn)
        layout.addLayout(header_layout)
        
        # Assertions table
        self.assertions_table = QTableWidget()
        self.assertions_table.setColumnCount(5)
        self.assertions_table.setHorizontalHeaderLabels([
            "Enabled", "Type", "Field", "Operator", "Expected"
        ])
        self.assertions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.assertions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.assertions_table.setAlternatingRowColors(True)
        self.assertions_table.setMinimumHeight(100)  # Reduced for better window sizing
        
        # Enable context menu for right-click actions
        self.assertions_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.assertions_table.customContextMenuRequested.connect(self._show_assertion_context_menu)
        
        layout.addWidget(self.assertions_table, 1)  # Stretch to fill
        
        # Set content in scroll area
        scroll.setWidget(content)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
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
    
    def _delete_assertion(self, row: int):
        """Delete assertion at row."""
        if row >= 0 and row < self.assertions_table.rowCount():
            self.assertions_table.removeRow(row)
            self.assertions_changed.emit()
    
    def _show_assertion_context_menu(self, position):
        """Show context menu for assertion table."""
        row = self.assertions_table.rowAt(position.y())
        if row < 0:
            return
        
        menu = QMenu(self)
        
        delete_action = QAction("🗑️ Delete Assertion", self)
        delete_action.triggered.connect(lambda: self._delete_assertion(row))
        menu.addAction(delete_action)
        
        # Show menu at cursor position
        menu.exec(self.assertions_table.viewport().mapToGlobal(position))
    
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

