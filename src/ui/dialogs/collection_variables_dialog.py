"""
Collection Variables Dialog

This module provides a dialog for managing collection-level variables.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


class CollectionVariablesDialog(QDialog):
    """Dialog for managing collection variables."""
    
    def __init__(self, parent, db, collection_id: int, collection_name: str):
        """
        Initialize the collection variables dialog.
        
        Args:
            parent: Parent widget
            db: DatabaseManager instance
            collection_id: ID of the collection
            collection_name: Name of the collection
        """
        super().__init__(parent)
        self.db = db
        self.collection_id = collection_id
        self.collection_name = collection_name
        
        self.setWindowTitle(f"Collection Variables - {collection_name}")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        self._init_ui()
        self._load_variables()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel(f"<h3>Variables for collection: {self.collection_name}</h3>")
        layout.addWidget(header_label)
        
        info_label = QLabel(
            "Collection variables can be referenced using {{variable_name}} in your requests.\n"
            "They have precedence over environment variables."
        )
        info_label.setStyleSheet("color: #757575; padding: 10px 0;")
        layout.addWidget(info_label)
        
        # Table
        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(3)
        self.variables_table.setHorizontalHeaderLabels(["Key", "Value", "Description"])
        
        # Set column widths
        header = self.variables_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.variables_table.setColumnWidth(0, 200)
        self.variables_table.setColumnWidth(1, 250)
        
        layout.addWidget(self.variables_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("➕ Add Variable")
        add_button.clicked.connect(self._add_variable)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("✏️ Edit Variable")
        edit_button.clicked.connect(self._edit_variable)
        button_layout.addWidget(edit_button)
        
        delete_button = QPushButton("🗑️ Delete Variable")
        delete_button.clicked.connect(self._delete_variable)
        button_layout.addWidget(delete_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _load_variables(self):
        """Load variables from database and populate the table."""
        self.variables_table.setRowCount(0)
        
        variables = self.db.get_collection_variables_with_metadata(self.collection_id)
        
        for var in variables:
            row = self.variables_table.rowCount()
            self.variables_table.insertRow(row)
            
            # Store variable ID in the first column's item
            key_item = QTableWidgetItem(var['key'])
            key_item.setData(Qt.ItemDataRole.UserRole, var['id'])
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            value_item = QTableWidgetItem(var['value'])
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            desc_item = QTableWidgetItem(var['description'])
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.variables_table.setItem(row, 0, key_item)
            self.variables_table.setItem(row, 1, value_item)
            self.variables_table.setItem(row, 2, desc_item)
    
    def _add_variable(self):
        """Add a new variable."""
        key, ok = QInputDialog.getText(self, "Add Variable", "Variable key (name):")
        if not ok or not key.strip():
            return
        
        value, ok = QInputDialog.getText(self, "Add Variable", "Variable value:")
        if not ok:
            return
        
        description, ok = QInputDialog.getText(self, "Add Variable", "Description (optional):")
        if not ok:
            description = ""
        
        try:
            self.db.create_collection_variable(
                self.collection_id,
                key.strip(),
                value,
                description
            )
            self._load_variables()
            QMessageBox.information(self, "Success", f"Variable '{key}' added")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add variable: {str(e)}")
    
    def _edit_variable(self):
        """Edit the selected variable."""
        current_row = self.variables_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a variable to edit")
            return
        
        key_item = self.variables_table.item(current_row, 0)
        variable_id = key_item.data(Qt.ItemDataRole.UserRole)
        current_key = key_item.text()
        current_value = self.variables_table.item(current_row, 1).text()
        current_desc = self.variables_table.item(current_row, 2).text()
        
        # Edit key
        key, ok = QInputDialog.getText(
            self, "Edit Variable", "Variable key (name):", text=current_key
        )
        if not ok:
            return
        
        # Edit value
        value, ok = QInputDialog.getText(
            self, "Edit Variable", "Variable value:", text=current_value
        )
        if not ok:
            return
        
        # Edit description
        description, ok = QInputDialog.getText(
            self, "Edit Variable", "Description (optional):", text=current_desc
        )
        if not ok:
            description = current_desc
        
        try:
            self.db.update_collection_variable(
                variable_id,
                key=key.strip() if key.strip() != current_key else None,
                value=value if value != current_value else None,
                description=description if description != current_desc else None
            )
            self._load_variables()
            QMessageBox.information(self, "Success", f"Variable '{key}' updated")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update variable: {str(e)}")
    
    def _delete_variable(self):
        """Delete the selected variable."""
        current_row = self.variables_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a variable to delete")
            return
        
        key_item = self.variables_table.item(current_row, 0)
        variable_id = key_item.data(Qt.ItemDataRole.UserRole)
        variable_key = key_item.text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete variable '{variable_key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_collection_variable(variable_id)
                self._load_variables()
                QMessageBox.information(self, "Success", f"Variable '{variable_key}' deleted")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete variable: {str(e)}")

