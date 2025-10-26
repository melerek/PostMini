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
        layout.setSpacing(12)  # 4-point grid
        layout.setContentsMargins(12, 12, 12, 12)  # 4-point grid
        
        # Compact header with title and description
        from PyQt6.QtWidgets import QSizePolicy
        header_widget = QWidget()
        header_widget.setFixedHeight(32)  # Fixed height
        header_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)  # 4-point grid
        
        title = QLabel("Environments")
        title.setStyleSheet("font-size: 14px; font-weight: 600;")  # Primary text, slightly larger
        header_layout.addWidget(title)
        
        # Compact description with lighter styling
        description = QLabel("Store variables like {{baseUrl}}, {{apiKey}} for automatic substitution")
        description.setProperty("class", "tertiary")  # Use tertiary text style
        header_layout.addWidget(description)
        header_layout.addStretch()
        
        layout.addWidget(header_widget, 0)  # 0 = don't stretch
        
        # Create splitter for environments list and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Environments list
        left_widget = self._create_environments_list()
        splitter.addWidget(left_widget)
        
        # Right side: Environment editor
        right_widget = self._create_environment_editor()
        splitter.addWidget(right_widget)
        
        splitter.setSizes([250, 550])
        layout.addWidget(splitter, 1)  # 1 = stretch to fill available space
        
        # Bottom buttons - FIXED HEIGHT
        button_widget = QWidget()
        button_widget.setFixedHeight(40)  # Fixed height for button area
        button_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)  # 4-point grid
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(button_widget, 0)  # 0 = don't stretch
    
    def _create_environments_list(self) -> QWidget:
        """Create the left panel with environments list."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)  # 4-point grid
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Environments")
        title.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout.addWidget(title)
        
        # List widget
        self.env_list = QListWidget()
        self.env_list.currentItemChanged.connect(self._on_environment_selected)
        layout.addWidget(self.env_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  # 4-point grid
        
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
        layout.setSpacing(8)  # 4-point grid
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Environment name
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)  # 4-point grid
        name_label = QLabel("Name:")
        name_label.setProperty("class", "secondary")
        name_layout.addWidget(name_label)
        self.env_name_input = QLineEdit()
        self.env_name_input.setPlaceholderText("e.g., Development, Production")
        self.env_name_input.textChanged.connect(self._on_name_changed)
        name_layout.addWidget(self.env_name_input)
        layout.addLayout(name_layout)
        
        # Variables title
        var_title = QLabel("Variables")
        var_title.setStyleSheet("font-size: 12px; font-weight: 600; margin-top: 8px;")
        layout.addWidget(var_title)
        
        # Variables table
        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(2)
        self.variables_table.setHorizontalHeaderLabels(['VARIABLE', 'VALUE'])
        self.variables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.variables_table.setRowCount(10)  # Start with 10 empty rows
        
        # Apply custom delegate to remove padding from cell editors
        self.variables_table.setItemDelegate(NoPaddingDelegate())
        
        layout.addWidget(self.variables_table)
        
        # Add row button
        add_row_btn = QPushButton("Add Row")
        add_row_btn.clicked.connect(self._add_variable_row)
        layout.addWidget(add_row_btn)
        
        # Save button - PRIMARY CTA
        save_btn = QPushButton("Save Environment")
        save_btn.setObjectName("primaryButton")  # Will be styled by global CSS
        save_btn.setStyleSheet("""
            QPushButton#primaryButton {
                background-color: #3a79d0;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton#primaryButton:hover {
                background-color: #4a89e0;
            }
            QPushButton#primaryButton:pressed {
                background-color: #2a69c0;
            }
        """)
        save_btn.clicked.connect(self._save_environment)
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

