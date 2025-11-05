"""
Environments Panel Widget for PostMini API Client.

Allows users to create, edit, and manage environment configurations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QDialog, QDialogButtonBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from typing import Optional


class AddEnvironmentDialog(QDialog):
    """Dialog for adding a new environment."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Environment")
        self.setModal(True)
        self.setMinimumWidth(350)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Label
        label = QLabel("Environment Name:")
        layout.addWidget(label)
        
        # Input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Development, Staging, Production")
        self.name_input.textChanged.connect(self._validate_input)
        layout.addWidget(self.name_input)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Disable OK button initially
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        
        # Focus on input
        self.name_input.setFocus()
    
    def _validate_input(self):
        """Enable/disable OK button based on input."""
        text = self.name_input.text().strip()
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(len(text) > 0)
    
    def get_environment_name(self) -> str:
        """Get the entered environment name."""
        return self.name_input.text().strip()


class EnvironmentListItem(QWidget):
    """Custom widget for environment list item."""
    
    edit_clicked = pyqtSignal(int)  # environment_id
    delete_clicked = pyqtSignal(int)  # environment_id
    variables_clicked = pyqtSignal(int)  # environment_id - to switch to variables panel
    
    def __init__(self, env_id: int, name: str, var_count: int, parent=None):
        super().__init__(parent)
        self.env_id = env_id
        self.count_label = None  # Store reference for updates
        self._init_ui(name, var_count)
    
    def _init_ui(self, name: str, var_count: int):
        """Initialize the item UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Environment icon
        icon_label = QLabel("🌍")
        icon_label.setStyleSheet("font-size: 16px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Name and variable count
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 12px; font-weight: 500; background: transparent; color: #fff;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        info_layout.addWidget(name_label)
        
        self.count_label = QLabel(f"{var_count} variable{'s' if var_count != 1 else ''}")
        self.count_label.setStyleSheet("font-size: 11px; color: #888; background: transparent;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        info_layout.addWidget(self.count_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Variables button - switch to variables panel with this environment
        vars_btn = QPushButton("Variables")
        vars_btn.setFixedHeight(26)
        vars_btn.setToolTip("View and manage variables for this environment")
        vars_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(33, 150, 243, 0.3);
                border-radius: 3px;
                background: rgba(33, 150, 243, 0.1);
                font-size: 11px;
                color: #64B5F6;
                padding: 0px 10px;
            }
            QPushButton:hover {
                background: rgba(33, 150, 243, 0.2);
                border-color: rgba(33, 150, 243, 0.5);
                color: #90CAF9;
            }
        """)
        vars_btn.clicked.connect(lambda: self.variables_clicked.emit(self.env_id))
        layout.addWidget(vars_btn)
        
        # Edit button - flat style with text
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedHeight(26)
        edit_btn.setToolTip("Rename environment")
        edit_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                background: transparent;
                font-size: 11px;
                color: #ccc;
                padding: 0px 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.25);
                color: #fff;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.env_id))
        layout.addWidget(edit_btn)
        
        # Delete button - flat style with text
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedHeight(26)
        delete_btn.setToolTip("Delete environment")
        delete_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                background: transparent;
                font-size: 11px;
                color: #ccc;
                padding: 0px 10px;
            }
            QPushButton:hover {
                background: rgba(255, 80, 80, 0.15);
                border-color: rgba(255, 80, 80, 0.3);
                color: #ff6b6b;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.env_id))
        layout.addWidget(delete_btn)
        
        # Set transparent background for the widget itself
        self.setStyleSheet("background: transparent;")
    
    def update_variable_count(self, var_count: int):
        """Update the variable count display."""
        if self.count_label:
            self.count_label.setText(f"{var_count} variable{'s' if var_count != 1 else ''}")


class EnvironmentsPanel(QWidget):
    """Panel for managing environments."""
    
    environment_created = pyqtSignal(int)  # environment_id
    environment_deleted = pyqtSignal(int)  # environment_id
    environment_updated = pyqtSignal(int)  # environment_id
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()
        self.refresh()
    
    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header - unified style
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
        
        # Title with icon
        header_label = QLabel("🌍 Environments")
        header_label.setStyleSheet("font-size: 13px; font-weight: 600; border: none;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Add button in header
        add_btn = QPushButton("+ Add")
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 500;
                color: #fff;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        add_btn.clicked.connect(self._add_environment)
        header_layout.addWidget(add_btn)
        
        main_layout.addWidget(header_widget)
        
        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)
        
        # Info section - compact, gray background
        info_text_1 = QLabel(
            "Environments let you organize variables for different contexts "
            "(Development, Staging, Production, etc.). Each environment can have "
            "its own set of variables like API URLs, authentication tokens, and more."
        )
        info_text_1.setWordWrap(True)
        info_text_1.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                color: #999;
                line-height: 1.4;
            }
        """)
        content_layout.addWidget(info_text_1)
        
        info_text_2 = QLabel(
            "📝 To manage variables for each environment, use the <b>Variables</b> panel."
        )
        info_text_2.setWordWrap(True)
        info_text_2.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                color: #999;
            }
        """)
        content_layout.addWidget(info_text_2)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        search_icon = QLabel("🔍")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search environments...")
        self.search_input.textChanged.connect(self._filter_environments)
        search_layout.addWidget(self.search_input)
        
        content_layout.addLayout(search_layout)
        
        # Environment list
        self.env_list = QListWidget()
        self.env_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                margin-bottom: 8px;
                padding: 0px;
            }
            QListWidget::item:hover {
                background: rgba(255, 255, 255, 0.06);
                border-color: rgba(255, 255, 255, 0.15);
            }
            QListWidget::item:selected {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }
        """)
        content_layout.addWidget(self.env_list)
        
        # Empty state
        self.empty_label = QLabel("No environments yet.\nClick '+ Add' to create one.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #666; font-size: 12px; padding: 40px;")
        self.empty_label.setVisible(False)
        content_layout.addWidget(self.empty_label)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        self.setMinimumWidth(250)
        self.setMaximumWidth(400)
    
    def refresh(self):
        """Reload environments from database."""
        self.env_list.clear()
        environments = self.db.get_all_environments()
        
        if not environments:
            self.empty_label.setVisible(True)
            self.env_list.setVisible(False)
        else:
            self.empty_label.setVisible(False)
            self.env_list.setVisible(True)
            
            for env in environments:
                # Count variables
                variables = env.get('variables', {})
                var_count = len(variables) if variables else 0
                
                # Create custom widget
                item_widget = EnvironmentListItem(env['id'], env['name'], var_count)
                item_widget.edit_clicked.connect(self._edit_environment)
                item_widget.delete_clicked.connect(self._delete_environment)
                item_widget.variables_clicked.connect(self._open_variables_panel)
                
                # Create list item
                list_item = QListWidgetItem(self.env_list)
                list_item.setSizeHint(item_widget.sizeHint())
                # Store environment_id in the list item for later retrieval
                list_item.setData(Qt.ItemDataRole.UserRole, env['id'])
                
                # Add to list
                self.env_list.addItem(list_item)
                self.env_list.setItemWidget(list_item, item_widget)
    
    def _filter_environments(self):
        """Filter environments based on search text."""
        search_text = self.search_input.text().lower()
        
        for i in range(self.env_list.count()):
            item = self.env_list.item(i)
            widget = self.env_list.itemWidget(item)
            
            if widget:
                # Get the name from the widget's layout
                info_layout = widget.layout().itemAt(1).layout()
                name_label = info_layout.itemAt(0).widget()
                env_name = name_label.text().lower()
                
                # Show/hide based on match
                item.setHidden(search_text not in env_name)
    
    def _add_environment(self):
        """Show dialog to add a new environment."""
        dialog = AddEnvironmentDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            env_name = dialog.get_environment_name()
            
            if env_name:
                try:
                    # Create environment with empty variables
                    env_id = self.db.create_environment(env_name, {})
                    self.refresh()
                    self.environment_created.emit(env_id)
                    
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Environment '{env_name}' created successfully.\n\n"
                        "Use the Variables panel to add variables to this environment."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to create environment:\n{str(e)}"
                    )
    
    def _edit_environment(self, env_id: int):
        """Show dialog to edit environment name."""
        try:
            env = self.db.get_environment(env_id)
            if not env:
                return
            
            # Show input dialog
            dialog = AddEnvironmentDialog(self)
            dialog.setWindowTitle("Rename Environment")
            dialog.name_input.setText(env['name'])
            dialog.name_input.selectAll()
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_name = dialog.get_environment_name()
                
                if new_name and new_name != env['name']:
                    # Update environment
                    self.db.update_environment(env_id, new_name, env.get('variables', {}))
                    self.refresh()
                    self.environment_updated.emit(env_id)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update environment:\n{str(e)}"
            )
    
    def _delete_environment(self, env_id: int):
        """Delete an environment with confirmation."""
        try:
            env = self.db.get_environment(env_id)
            if not env:
                return
            
            # Count variables
            variables = env.get('variables', {})
            var_count = len(variables) if variables else 0
            
            # If environment has variables, show warning
            if var_count > 0:
                reply = QMessageBox.question(
                    self,
                    "Delete Environment",
                    f"Environment '{env['name']}' has {var_count} variable{'s' if var_count != 1 else ''}.\n\n"
                    "Are you sure you want to delete it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Delete environment
            self.db.delete_environment(env_id)
            self.refresh()
            self.environment_deleted.emit(env_id)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete environment:\n{str(e)}"
            )
    
    def _open_variables_panel(self, env_id: int):
        """Switch to variables panel with the specified environment active."""
        # Get the main window by walking up the parent hierarchy
        main_window = self.parent()
        while main_window and not hasattr(main_window, '_switch_left_panel'):
            main_window = main_window.parent()
        
        if main_window:
            # Find the environment in the combo box and set it as active
            env = self.db.get_environment(env_id)
            if env:
                # Find the index in the environment combo box
                for i in range(main_window.env_combo.count()):
                    if main_window.env_combo.itemData(i) == env_id:
                        main_window.env_combo.setCurrentIndex(i)
                        break
                
                # Switch to variables panel
                main_window._switch_left_panel('variable_inspector')
    
    def update_variable_counts(self):
        """Update variable counts for all environments without full refresh."""
        for i in range(self.env_list.count()):
            item = self.env_list.item(i)
            widget = self.env_list.itemWidget(item)
            env_id = item.data(Qt.ItemDataRole.UserRole)
            
            if widget and env_id:
                # Get updated variable count from database
                env = self.db.get_environment(env_id)
                if env:
                    variables = env.get('variables', {})
                    var_count = len(variables) if variables else 0
                    widget.update_variable_count(var_count)

