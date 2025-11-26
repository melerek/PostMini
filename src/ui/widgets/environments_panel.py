"""
Environments Panel Widget for PostMini API Client.

Allows users to create, edit, and manage environment configurations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QDialog, QDialogButtonBox, QScrollArea, QFrame, QFileDialog,
    QRadioButton, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QIcon
from typing import Optional

from src.features.environment_io import EnvironmentExporter, EnvironmentImporter


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
    sync_toggled = pyqtSignal(int, int)  # environment_id, sync_to_git (0 or 1)
    
    def __init__(self, env_id: int, name: str, var_count: int, sync_to_git: int = 0, theme: str = 'dark', parent=None):
        super().__init__(parent)
        self.env_id = env_id
        self.sync_to_git = sync_to_git
        self.count_label = None  # Store reference for updates
        self.sync_btn = None  # Store reference for sync button
        self.theme = theme
        self._init_ui(name, var_count)
    
    def set_theme(self, theme: str):
        """Update button styles based on theme."""
        self.theme = theme
        self._update_button_styles()
    
    def _update_button_styles(self):
        """Update button styles based on current theme."""
        if self.theme == 'dark':
            self.menu_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 3px;
                    background: transparent;
                    font-size: 18px;
                    color: #ccc;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.08);
                    border-color: rgba(255, 255, 255, 0.25);
                    color: #fff;
                }
            """)
        else:
            self.menu_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #9E9E9E;
                    border-radius: 3px;
                    background: #FFFFFF;
                    font-size: 18px;
                    color: #424242;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: #F5F5F5;
                    border-color: #616161;
                    color: #212121;
                }
            """)
    
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
        
        # Name and variable count with sync icon
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add sync status icon (🌐 for public/synced, 🔒 for private/local)
        sync_icon = "🌐" if self.sync_to_git == 1 else "🔒"
        name_label = QLabel(f"{sync_icon} {name}")
        name_label.setStyleSheet("font-size: 12px; font-weight: 500; background: transparent; color: #fff;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        info_layout.addWidget(name_label)
        
        self.count_label = QLabel(f"{var_count} variable{'s' if var_count != 1 else ''}")
        self.count_label.setStyleSheet("font-size: 11px; color: #888; background: transparent;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        info_layout.addWidget(self.count_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Menu button ("...")
        self.menu_btn = QPushButton("⋯")
        self.menu_btn.setFixedSize(32, 26)
        self.menu_btn.setToolTip("Environment actions")
        self.menu_btn.clicked.connect(self._show_menu)
        layout.addWidget(self.menu_btn)
        
        # Apply theme-specific button styles
        self._update_button_styles()
        
        # Set transparent background for the widget itself
        self.setStyleSheet("background: transparent;")
    
    def _show_menu(self):
        """Show context menu with environment actions."""
        menu = QMenu(self)
        
        # Apply theme-specific menu styling
        if self.theme == 'dark':
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2d2d2d;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 6px 20px;
                    color: #e0e0e0;
                    background-color: transparent;
                }
                QMenu::item:selected {
                    background-color: #404040;
                    color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background: #555;
                    margin: 4px 8px;
                }
            """)
        else:
            menu.setStyleSheet("""
                QMenu {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 6px 20px;
                    color: #212121;
                    background-color: transparent;
                }
                QMenu::item:selected {
                    background-color: #e3f2fd;
                    color: #1565C0;
                }
                QMenu::separator {
                    height: 1px;
                    background: #e0e0e0;
                    margin: 4px 8px;
                }
            """)
        
        # Variables action
        vars_action = menu.addAction("📊 Variables")
        vars_action.triggered.connect(lambda: self.variables_clicked.emit(self.env_id))
        
        menu.addSeparator()
        
        # Sync toggle action
        if self.sync_to_git == 1:
            sync_action = menu.addAction("🔒 Make Private")
        else:
            sync_action = menu.addAction("🌐 Make Public")
        sync_action.triggered.connect(self._toggle_sync)
        
        menu.addSeparator()
        
        # Edit action
        edit_action = menu.addAction("✏️ Rename")
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(self.env_id))
        
        # Delete action
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self.delete_clicked.emit(self.env_id))
        
        # Show menu at button position
        menu.exec(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))
    
    def _toggle_sync(self):
        """Toggle sync status and emit signal."""
        new_status = 0 if self.sync_to_git == 1 else 1
        self.sync_toggled.emit(self.env_id, new_status)
    
    def update_sync_status(self, sync_to_git: int):
        """Update the sync status display."""
        self.sync_to_git = sync_to_git
        # No button text to update anymore
    
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
        self.current_theme = 'dark'  # Default theme
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
        
        # Import button in header
        self.import_btn = QPushButton("📥 Import")
        self.import_btn.setToolTip("Import environment from file")
        self.import_btn.clicked.connect(self._import_environment)
        header_layout.addWidget(self.import_btn)
        
        # Export button in header
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.setToolTip("Export selected environment to file")
        self.export_btn.clicked.connect(self._export_environment)
        header_layout.addWidget(self.export_btn)
        
        # Add button in header
        self.add_btn = QPushButton("+ Add")
        self.add_btn.clicked.connect(self._add_environment)
        header_layout.addWidget(self.add_btn)
        
        # Apply initial theme to header buttons
        self._update_header_button_styles()
        
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
        content_layout.addWidget(self.env_list, stretch=1)  # Give list stretch factor to fill space
        
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
        self.setMinimumWidth(200)
        self.setMaximumWidth(450)
    
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
                sync_to_git = env.get('sync_to_git', 0)
                
                # Create custom widget
                item_widget = EnvironmentListItem(env['id'], env['name'], var_count, sync_to_git, self.current_theme)
                item_widget.edit_clicked.connect(self._edit_environment)
                item_widget.delete_clicked.connect(self._delete_environment)
                item_widget.variables_clicked.connect(self._open_variables_panel)
                item_widget.sync_toggled.connect(self._toggle_environment_sync)
                
                # Create list item
                list_item = QListWidgetItem(self.env_list)
                list_item.setSizeHint(item_widget.sizeHint())
                # Store environment_id in the list item for later retrieval
                list_item.setData(Qt.ItemDataRole.UserRole, env['id'])
                
                # Add to list
                self.env_list.addItem(list_item)
                self.env_list.setItemWidget(list_item, item_widget)
    
    def set_theme(self, theme: str):
        """Update theme for all environment list items."""
        self.current_theme = theme
        
        # Update header buttons
        self._update_header_button_styles()
        
        # Update all existing list items
        for i in range(self.env_list.count()):
            item = self.env_list.item(i)
            widget = self.env_list.itemWidget(item)
            if widget and isinstance(widget, EnvironmentListItem):
                widget.set_theme(theme)
    
    def _update_header_button_styles(self):
        """Update header button styles based on current theme."""
        if self.current_theme == 'dark':
            # Dark theme - original styles
            button_style = """
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
            """
        else:
            # Light theme - better contrast
            button_style = """
                QPushButton {
                    background: #FFFFFF;
                    border: 1px solid #9E9E9E;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    color: #212121;
                }
                QPushButton:hover {
                    background: #F5F5F5;
                    border-color: #616161;
                }
            """
        
        self.import_btn.setStyleSheet(button_style)
        self.export_btn.setStyleSheet(button_style)
        self.add_btn.setStyleSheet(button_style)
    
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
    
    def _toggle_environment_sync(self, env_id: int, sync_to_git: int):
        """Toggle sync status of an environment."""
        try:
            self.db.set_environment_sync_status(env_id, sync_to_git)
            status_text = "public (will sync to Git)" if sync_to_git == 1 else "private (local only)"
            env = self.db.get_environment(env_id)
            env_name = env.get('name', 'Environment') if env else 'Environment'
            
            # Get main window to access git_sync_manager
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'git_sync_manager'):
                main_window = main_window.parent()
            
            if main_window and hasattr(main_window, 'git_sync_manager') and main_window.git_sync_manager:
                if sync_to_git == 1:
                    # Making public - export to Git
                    if hasattr(main_window, '_auto_sync_to_filesystem'):
                        main_window._auto_sync_to_filesystem()
                else:
                    # Making private - remove file from Git sync folder
                    success, message = main_window.git_sync_manager.remove_environment_file(env_id)
                    # Don't show error if file doesn't exist, that's fine
            
            # Show success message (you may want to integrate this with main window status bar)
            # For now, just refresh to update UI
            self.refresh()
            
            # Optional: Emit signal to notify main window
            self.environment_updated.emit(env_id)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update sync status: {str(e)}")
    
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
    
    def _import_environment(self):
        """Import an environment from a file."""
        # Ask user to select file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Environment",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Create importer and import
            importer = EnvironmentImporter(self.db)
            success, message, env_id = importer.import_environment_from_file(file_path)
            
            if success:
                # Refresh the list
                self.refresh()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"{message}\n\n"
                    "The environment has been imported successfully."
                )
                
                # Emit signal if needed
                if env_id:
                    self.environment_created.emit(env_id)
            else:
                QMessageBox.critical(
                    self,
                    "Import Failed",
                    f"Failed to import environment:\n\n{message}"
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"An error occurred during import:\n\n{str(e)}"
            )
    
    def _export_environment(self):
        """Export selected environment to a file."""
        # Get selected environment
        selected_items = self.env_list.selectedItems()
        
        if not selected_items:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select an environment to export."
            )
            return
        
        # Get the environment ID from the selected item
        selected_item = selected_items[0]
        env_id = selected_item.data(Qt.ItemDataRole.UserRole)
        
        if not env_id:
            return
        
        # Get environment details
        env = self.db.get_environment(env_id)
        if not env:
            QMessageBox.warning(self, "Warning", "Environment not found!")
            return
        
        # Ask user for export format
        format_dialog = QDialog(self)
        format_dialog.setWindowTitle("Select Export Format")
        format_dialog.setModal(True)
        format_dialog.resize(400, 220)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Choose export format:"))
        
        internal_radio = QRadioButton("Internal Format (PostMini)")
        internal_radio.setChecked(True)
        internal_radio.setToolTip("PostMini's native environment format")
        layout.addWidget(internal_radio)
        
        postman_radio = QRadioButton("Postman Environment Format")
        postman_radio.setToolTip("Compatible with Postman and other API tools")
        layout.addWidget(postman_radio)
        
        layout.addWidget(QLabel(""))  # Spacer
        layout.addWidget(QLabel("Secret Variables:"))
        
        secrets_checkbox = QRadioButton("Include actual values")
        secrets_checkbox.setChecked(True)
        secrets_checkbox.setToolTip("Export with actual secret values")
        layout.addWidget(secrets_checkbox)
        
        secrets_placeholder = QRadioButton("Replace with placeholders")
        secrets_placeholder.setToolTip("Replace secret values with placeholders for sharing")
        layout.addWidget(secrets_placeholder)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(format_dialog.accept)
        buttons.rejected.connect(format_dialog.reject)
        layout.addWidget(buttons)
        
        format_dialog.setLayout(layout)
        
        if format_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Determine format and secret handling
        export_format = 'postman' if postman_radio.isChecked() else 'internal'
        include_secrets = secrets_checkbox.isChecked()
        
        # Generate safe filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                          for c in env['name'])
        safe_name = safe_name.strip().replace(' ', '_')
        
        # Ask user where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Environment",
            safe_name,
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Create exporter and export
            exporter = EnvironmentExporter(self.db)
            success = exporter.export_environment_to_file(
                env_id,
                file_path,
                format=export_format,
                include_secrets=include_secrets
            )
            
            if success:
                format_name = "Postman Environment Format" if export_format == 'postman' else "Internal Format"
                secret_info = "with actual values" if include_secrets else "with placeholders"
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Environment '{env['name']}' exported successfully!\n\n"
                    f"Format: {format_name}\n"
                    f"Secrets: {secret_info}\n"
                    f"Location: {file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export environment '{env['name']}'."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during export:\n\n{str(e)}"
            )


