"""
Variable Extraction Widget

This widget provides UI for extracting values from API responses and saving them as variables.
It includes a JSON tree viewer for easy point-and-click extraction.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QComboBox, QTextEdit, QSplitter,
    QMessageBox, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
from typing import Dict, Optional, Any
from src.core.api_client import ApiResponse
from src.features.variable_extractor import VariableExtractor


class VariableExtractionWidget(QWidget):
    """Widget for extracting variables from API responses."""
    
    variable_extracted = pyqtSignal(str, str, str)  # name, value, json_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_response = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Compact header with instructions (hidden initially)
        self.header = QLabel("💡 Click any value in the response below to extract it as a variable")
        self.header.setStyleSheet("padding: 6px 8px; background: #E3F2FD; border-radius: 4px; color: #1976D2; font-size: 12px;")
        self.header.hide()  # Hidden until we have JSON data
        layout.addWidget(self.header)
        
        # === Top Section: Response JSON Tree (takes all available space) ===
        tree_group = QGroupBox("Response JSON Structure")
        tree_layout = QVBoxLayout(tree_group)
        tree_layout.setContentsMargins(8, 8, 8, 8)
        
        # JSON tree viewer
        self.json_tree = QTreeWidget()
        self.json_tree.setHeaderLabels(["Key", "Value", "Type"])
        self.json_tree.setColumnWidth(0, 200)
        self.json_tree.setColumnWidth(1, 300)
        self.json_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.json_tree.setAlternatingRowColors(True)
        tree_layout.addWidget(self.json_tree)
        
        layout.addWidget(tree_group)
        
        # === Bottom Section: Fixed Compact Extraction Form (minimal height) ===
        form_group = QGroupBox("Extract Variable")
        form_group.setMaximumHeight(150)  # Fixed height for compact form
        form_layout = QVBoxLayout(form_group)
        form_layout.setContentsMargins(8, 6, 8, 6)
        form_layout.setSpacing(4)
        
        # Create 2×2 grid layout for better space efficiency
        from PyQt6.QtWidgets import QGridLayout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(6)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Row 1: Variable Name | JSON Path
        grid_layout.addWidget(QLabel("Variable Name:"), 0, 0)
        self.var_name_input = QLineEdit()
        self.var_name_input.setPlaceholderText("e.g., authToken, userId")
        grid_layout.addWidget(self.var_name_input, 0, 1)
        
        grid_layout.addWidget(QLabel("JSON Path:"), 0, 2)
        self.json_path_input = QLineEdit()
        self.json_path_input.setPlaceholderText("e.g., data.token")
        self.json_path_input.setReadOnly(True)
        grid_layout.addWidget(self.json_path_input, 0, 3)
        
        # Row 2: Extracted Value | Description
        grid_layout.addWidget(QLabel("Value:"), 1, 0)
        self.value_preview = QLineEdit()
        self.value_preview.setReadOnly(True)
        self.value_preview.setStyleSheet("font-weight: bold; color: #4CAF50;")
        grid_layout.addWidget(self.value_preview, 1, 1)
        
        grid_layout.addWidget(QLabel("Description:"), 1, 2)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Optional: What is this for?")
        grid_layout.addWidget(self.description_input, 1, 3)
        
        # Set column stretch to make fields expand equally
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)
        
        form_layout.addLayout(grid_layout)
        
        # Compact buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("💾 Save Variable")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_form)
        button_layout.addWidget(clear_btn)
        
        form_layout.addLayout(button_layout)
        
        layout.addWidget(form_group)
        
        # Empty state message
        self.empty_label = QLabel("📭 Send a request to extract variables from the response")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #999; font-size: 14px; padding: 40px;")
        layout.addWidget(self.empty_label)
        
        # Hide tree/form initially
        tree_group.hide()
        form_group.hide()
    
    def set_response(self, response: ApiResponse, request_name: str = ""):
        """
        Load a response for variable extraction.
        
        Args:
            response: API response object
            request_name: Name of the request (for display)
        """
        self.current_response = response
        
        # Try to parse as JSON
        try:
            data = json.loads(response.text)
            self._populate_json_tree(data)
            # self._populate_suggestions()  # Quick Extract disabled
            
            # Show tree/form and header, hide empty state
            self.header.show()
            # Show the tree and form groups (find by class)
            for widget in self.findChildren(QGroupBox):
                widget.show()
            self.empty_label.hide()
        except json.JSONDecodeError:
            # Not JSON, show friendly message in the widget (no popup)
            self.empty_label.setText(
                "⚠️ Response is not valid JSON\n\n"
                "Variable extraction only works with JSON responses.\n"
                "This response appears to be HTML, text, or another format."
            )
            self.empty_label.setStyleSheet("color: #FF9800; font-size: 14px; padding: 40px;")
            self.empty_label.show()
            self.header.hide()
            # Hide the tree and form groups
            for widget in self.findChildren(QGroupBox):
                widget.hide()
    
    def _populate_json_tree(self, data: Any, parent: Optional[QTreeWidgetItem] = None, path: str = ""):
        """
        Populate the tree widget with JSON structure.
        
        Args:
            data: JSON data (dict, list, or primitive)
            parent: Parent tree item (None for root)
            path: Current JSON path
        """
        self.json_tree.clear()
        
        def add_item(key: str, value: Any, parent_item: Optional[QTreeWidgetItem], current_path: str):
            """Recursively add items to tree."""
            item = QTreeWidgetItem()
            item.setText(0, str(key))
            
            if isinstance(value, dict):
                item.setText(1, f"{{...}} ({len(value)} properties)")
                item.setText(2, "Object")
                item.setData(0, Qt.ItemDataRole.UserRole, current_path)
                
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.json_tree.addTopLevelItem(item)
                
                # Add children
                for k, v in value.items():
                    child_path = f"{current_path}.{k}" if current_path else k
                    add_item(k, v, item, child_path)
            
            elif isinstance(value, list):
                item.setText(1, f"[...] ({len(value)} items)")
                item.setText(2, "Array")
                item.setData(0, Qt.ItemDataRole.UserRole, current_path)
                
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.json_tree.addTopLevelItem(item)
                
                # Add first few items
                for idx, v in enumerate(value[:10]):  # Limit to first 10 items
                    child_path = f"{current_path}[{idx}]"
                    add_item(f"[{idx}]", v, item, child_path)
                
                if len(value) > 10:
                    ellipsis = QTreeWidgetItem()
                    ellipsis.setText(0, "...")
                    ellipsis.setText(1, f"({len(value) - 10} more items)")
                    item.addChild(ellipsis)
            
            else:
                # Primitive value
                item.setText(1, str(value))
                item.setText(2, type(value).__name__)
                item.setData(0, Qt.ItemDataRole.UserRole, current_path)
                
                # Make extractable values bold
                if value and current_path:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(1, font)
                    item.setForeground(1, Qt.GlobalColor.darkGreen)
                
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.json_tree.addTopLevelItem(item)
        
        # Start recursion
        if isinstance(data, dict):
            for key, value in data.items():
                add_item(key, value, None, key)
        elif isinstance(data, list):
            for idx, value in enumerate(data):
                add_item(f"[{idx}]", value, None, f"[{idx}]")
        else:
            # Root is primitive
            item = QTreeWidgetItem()
            item.setText(0, "root")
            item.setText(1, str(data))
            item.setText(2, type(data).__name__)
            self.json_tree.addTopLevelItem(item)
        
        # Expand first level
        self.json_tree.expandToDepth(0)
    
    # Disabled - Quick Extract rarely useful and confuses users
    # def _populate_suggestions(self):
    #     """Populate the quick suggestions dropdown."""
    #     self.suggestions_combo.clear()
    #     self.suggestions_combo.addItem("Select a suggested variable...")
    #     
    #     if not self.current_response:
    #         return
    #     
    #     suggestions = VariableExtractor.get_suggested_variables(self.current_response)
    #     
    #     for suggestion in suggestions:
    #         display = f"{suggestion['name']} = {suggestion['value'][:50]}"
    #         self.suggestions_combo.addItem(display, suggestion)
    
    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle tree item click."""
        # Get the JSON path
        json_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not json_path:
            return
        
        # Get the value
        value = item.text(1)
        
        # Check if it's a leaf node (extractable)
        item_type = item.text(2)
        if item_type in ["Object", "Array"]:
            QMessageBox.information(
                self,
                "Cannot Extract",
                "Please select a primitive value (string, number, boolean), not an object or array."
            )
            return
        
        # Populate form
        self.json_path_input.setText(json_path)
        self.value_preview.setText(value)
        
        # Suggest variable name from last key in path
        last_key = json_path.split('.')[-1].replace('[', '').replace(']', '')
        self.var_name_input.setText(last_key)
        
        self.save_button.setEnabled(True)
    
    # Disabled - Quick Extract rarely useful and confuses users
    # def _on_suggestion_selected(self, index: int):
    #     """Handle suggestion selection."""
    #     if index <= 0:
    #         return
    #     
    #     suggestion = self.suggestions_combo.itemData(index)
    #     if suggestion:
    #         self.var_name_input.setText(suggestion['name'])
    #         self.json_path_input.setText(suggestion['path'])
    #         self.value_preview.setText(suggestion['value'])
    #         self.save_button.setEnabled(True)
    
    def _on_save_clicked(self):
        """Handle save button click."""
        var_name = self.var_name_input.text().strip()
        json_path = self.json_path_input.text().strip()
        value = self.value_preview.text().strip()
        
        if not var_name:
            QMessageBox.warning(self, "Missing Name", "Please enter a variable name.")
            return
        
        if not json_path or not value:
            QMessageBox.warning(self, "No Value", "Please select a value from the response tree.")
            return
        
        # Emit signal
        self.variable_extracted.emit(var_name, value, json_path)
        
        # Show success message
        QMessageBox.information(
            self,
            "Variable Saved",
            f"Variable '{var_name}' has been saved!\n\n"
            f"You can now use {{{{extracted.{var_name}}}}} in your requests."
        )
        
        # Clear form
        self._clear_form()
    
    def _clear_form(self):
        """Clear the extraction form."""
        self.var_name_input.clear()
        self.json_path_input.clear()
        self.value_preview.clear()
        self.description_input.clear()
        self.save_button.setEnabled(False)
        # self.suggestions_combo.setCurrentIndex(0)  # Quick Extract disabled

