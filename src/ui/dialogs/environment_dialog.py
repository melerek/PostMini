"""
Environment Management Dialog

This module provides a dialog for managing environments and their variables.
Environments allow teams to switch between different configurations (dev, staging, prod)
and use variable substitution in requests.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QWidget, QSplitter, QStyledItemDelegate
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, Optional

from src.core.database import DatabaseManager


class NoPaddingDelegate(QStyledItemDelegate):
    """Custom delegate to remove padding from table cell editors."""
    
    def createEditor(self, parent, option, index):
        """Create editor with no padding."""
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            # Remove all padding and margins from the editor
            editor.setStyleSheet("""
                QLineEdit {
                    padding: 0px;
                    margin: 0px;
                    border: none;
                }
            """)
        return editor


class EnvironmentDialog(QDialog):
    """
    Dialog for creating, editing, and deleting environments with their variables.
    """
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_environment_id = None
        
        self.setWindowTitle("Manage Environments")
        self.setGeometry(200, 200, 800, 600)
        
        self._init_ui()
        self._load_environments()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Environment Management")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Environments allow you to store variables like {{baseUrl}}, {{apiKey}}, etc.\n"
            "Use {{variableName}} in your requests for automatic substitution."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create splitter for environments list and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Environments list
        left_widget = self._create_environments_list()
        splitter.addWidget(left_widget)
        
        # Right side: Environment editor
        right_widget = self._create_environment_editor()
        splitter.addWidget(right_widget)
        
        splitter.setSizes([250, 550])
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_environments_list(self) -> QWidget:
        """Create the left panel with environments list."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Environments")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # List widget
        self.env_list = QListWidget()
        self.env_list.currentItemChanged.connect(self._on_environment_selected)
        layout.addWidget(self.env_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_environment)
        button_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_environment)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def _create_environment_editor(self) -> QWidget:
        """Create the right panel for editing environment variables."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Environment name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.env_name_input = QLineEdit()
        self.env_name_input.setPlaceholderText("e.g., Development, Production")
        self.env_name_input.textChanged.connect(self._on_name_changed)
        name_layout.addWidget(self.env_name_input)
        layout.addLayout(name_layout)
        
        # Variables title
        var_title = QLabel("Variables")
        var_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(var_title)
        
        # Variables table
        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(2)
        self.variables_table.setHorizontalHeaderLabels(['Variable', 'Value'])
        self.variables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.variables_table.setRowCount(10)  # Start with 10 empty rows
        
        # Apply custom delegate to remove padding from cell editors
        self.variables_table.setItemDelegate(NoPaddingDelegate())
        
        layout.addWidget(self.variables_table)
        
        # Add row button
        add_row_btn = QPushButton("Add Row")
        add_row_btn.clicked.connect(self._add_variable_row)
        layout.addWidget(add_row_btn)
        
        # Save button
        save_btn = QPushButton("Save Environment")
        save_btn.clicked.connect(self._save_environment)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        layout.addWidget(save_btn)
        
        # Initially disable editor
        self._enable_editor(False)
        
        return widget
    
    def _enable_editor(self, enabled: bool):
        """Enable or disable the environment editor."""
        self.env_name_input.setEnabled(enabled)
        self.variables_table.setEnabled(enabled)
    
    def _load_environments(self):
        """Load all environments into the list."""
        self.env_list.clear()
        environments = self.db.get_all_environments()
        
        for env in environments:
            item = self.env_list.addItem(env['name'])
            # Store environment ID in item data
            self.env_list.item(self.env_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, env['id']
            )
    
    def _on_environment_selected(self, current, previous):
        """Handle environment selection from list."""
        if not current:
            self._enable_editor(False)
            return
        
        env_id = current.data(Qt.ItemDataRole.UserRole)
        self.current_environment_id = env_id
        
        # Load environment data
        env = self.db.get_environment(env_id)
        if env:
            self._enable_editor(True)
            self.env_name_input.setText(env['name'])
            self._load_variables(env.get('variables', {}))
    
    def _load_variables(self, variables: Dict):
        """Load variables into the table."""
        self.variables_table.clearContents()
        self.variables_table.setRowCount(max(10, len(variables) + 3))
        
        for i, (key, value) in enumerate(variables.items()):
            self.variables_table.setItem(i, 0, QTableWidgetItem(key))
            self.variables_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def _add_environment(self):
        """Add a new environment."""
        # Create a new environment with default name
        try:
            # Find a unique name
            base_name = "New Environment"
            name = base_name
            counter = 1
            
            existing_names = [self.env_list.item(i).text() 
                            for i in range(self.env_list.count())]
            
            while name in existing_names:
                name = f"{base_name} {counter}"
                counter += 1
            
            env_id = self.db.create_environment(name, {})
            
            # Add to list and select it
            self._load_environments()
            
            # Select the newly created environment
            for i in range(self.env_list.count()):
                if self.env_list.item(i).data(Qt.ItemDataRole.UserRole) == env_id:
                    self.env_list.setCurrentRow(i)
                    break
            
            QMessageBox.information(self, "Success", f"Environment '{name}' created!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create environment: {str(e)}")
    
    def _delete_environment(self):
        """Delete the selected environment."""
        if not self.current_environment_id:
            QMessageBox.warning(self, "Warning", "Please select an environment to delete!")
            return
        
        env = self.db.get_environment(self.current_environment_id)
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the environment '{env['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_environment(self.current_environment_id)
                self.current_environment_id = None
                self._load_environments()
                self._enable_editor(False)
                self.env_name_input.clear()
                self.variables_table.clearContents()
                QMessageBox.information(self, "Success", "Environment deleted!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete environment: {str(e)}")
    
    def _save_environment(self):
        """Save the current environment."""
        if not self.current_environment_id:
            QMessageBox.warning(self, "Warning", "No environment selected!")
            return
        
        name = self.env_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter an environment name!")
            return
        
        # Get variables from table
        variables = self._get_variables_from_table()
        
        try:
            self.db.update_environment(self.current_environment_id, name, variables)
            self._load_environments()
            
            # Reselect the current environment
            for i in range(self.env_list.count()):
                if self.env_list.item(i).data(Qt.ItemDataRole.UserRole) == self.current_environment_id:
                    self.env_list.setCurrentRow(i)
                    break
            
            QMessageBox.information(self, "Success", "Environment saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save environment: {str(e)}")
    
    def _get_variables_from_table(self) -> Dict:
        """Extract variables from the table."""
        variables = {}
        
        for row in range(self.variables_table.rowCount()):
            key_item = self.variables_table.item(row, 0)
            value_item = self.variables_table.item(row, 1)
            
            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                
                if key:  # Only add if key is not empty
                    variables[key] = value
        
        return variables
    
    def _add_variable_row(self):
        """Add a new row to the variables table."""
        current_rows = self.variables_table.rowCount()
        self.variables_table.setRowCount(current_rows + 1)
    
    def _on_name_changed(self, text: str):
        """Handle environment name change."""
        # Could add validation here if needed
        pass

