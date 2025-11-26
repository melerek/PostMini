"""
Variable Inspector Panel

Shows all available variables in current context grouped by scope.
Allows editing and deleting environment and extracted variables.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog,
    QMessageBox, QStyledItemDelegate, QStyle, QApplication, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QCursor, QFont, QAction
from typing import Dict, List, Optional


class EditableCellDelegate(QStyledItemDelegate):
    """Custom delegate to show edit cursor on value column for editable items."""
    
    def editorEvent(self, event, model, option, index):
        """Handle mouse events to show proper cursor."""
        if event.type() == QEvent.Type.MouseMove and index.column() == 1:
            item = index.model().itemFromIndex(index)
            # Only show edit cursor for editable items (not parent categories)
            if item and item.childCount() == 0:
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data and data.get('editable'):
                    QApplication.instance().setOverrideCursor(Qt.CursorShape.IBeamCursor)
                    return True
        return super().editorEvent(event, model, option, index)


class VariableInspectorPanel(QWidget):
    """Panel showing all available variables in current context."""
    
    variable_copied = pyqtSignal(str)  # Emitted when variable syntax is copied
    variable_edited = pyqtSignal(str, str, str)  # scope, name, new_value
    variable_deleted = pyqtSignal(str, str)  # scope, name - MUST match handler signature!
    variable_added = pyqtSignal(str, str)  # name, value
    collection_variable_added = pyqtSignal(int, str, str)  # collection_id, name, value
    refresh_requested = pyqtSignal()  # Request parent to refresh data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_environment_id = None
        self.current_theme = 'dark'  # Default theme
        self.db = None  # Will be set by parent
        self._init_ui()
        print(f"[DEBUG] VariableInspectorPanel initialized, parent: {parent}")
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header - unified style
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(8)
        
        title = QLabel("{{}} Variables")
        title.setStyleSheet("font-size: 13px; font-weight: 600; border: none;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add button with dropdown menu in header
        self.add_var_btn = QPushButton("+ Add")
        self.add_var_btn.setToolTip("Add variable")
        
        # Create dropdown menu with proper styling
        add_menu = QMenu(self.add_var_btn)
        add_menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                color: #ffffff;
                padding: 8px 32px 8px 12px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: rgba(33, 150, 243, 0.2);
            }
            QMenu::item:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Add menu actions
        add_env_var_action = QAction("Add Environment Variable", self)
        add_env_var_action.triggered.connect(self._add_environment_variable)
        add_menu.addAction(add_env_var_action)
        
        add_coll_var_action = QAction("Add Collection Variable", self)
        add_coll_var_action.triggered.connect(self._add_collection_variable)
        add_menu.addAction(add_coll_var_action)
        
        # Attach menu to button
        self.add_var_btn.setMenu(add_menu)
        header_layout.addWidget(self.add_var_btn)
        
        # Apply initial theme to button
        self._update_add_button_style()
        
        layout.addWidget(header)
        
        # Content area
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)
        
        # Info text
        info_label = QLabel(
            "Click to copy • Double-click value to edit • Right-click to delete"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #999; font-size: 11px;")
        content_layout.addWidget(info_label)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter variables...")
        self.search_input.textChanged.connect(self._filter_variables)
        search_layout.addWidget(self.search_input)
        
        content_layout.addLayout(search_layout)
        
        # Tree widget for variables
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["TYPE", "NAME", "VALUE"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setColumnWidth(0, 50)  # Type/Icon column (🌐/🔒/🔐)
        self.tree.setColumnWidth(1, 200)  # Name column
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        # Enable single-click expand/collapse for parent items
        self.tree.setExpandsOnDoubleClick(False)
        # Enable editing for column 1 (VALUE) only
        self.tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)  # We'll handle it manually
        # Enable mouse tracking for hover effects
        self.tree.setMouseTracking(True)
        self.tree.viewport().installEventFilter(self)
        content_layout.addWidget(self.tree)
        
        # Status label
        self.status_label = QLabel("No variables loaded")
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        content_layout.addWidget(self.status_label)
        
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
        self.setMinimumWidth(200)
    
    def load_variables(self, 
                       environment_vars: Dict[str, str] = None,
                       collection_vars: List[Dict] = None,
                       extracted_vars: List[Dict] = None,
                       environment_name: str = None,
                       environment_id: int = None,
                       collection_id: int = None):
        """
        Load and display variables.
        
        Args:
            environment_vars: Dictionary of environment variables
            collection_vars: List of collection variable dictionaries with metadata
            extracted_vars: List of extracted variable dictionaries
            environment_name: Name of active environment
            environment_id: ID of active environment
            collection_id: ID of active collection
        """
        self.tree.clear()
        self.current_environment_id = environment_id
        self.current_collection_id = collection_id
        total_count = 0
        
        # Store current environment for later use in add variable dialogs
        
        # Extracted variables (highest priority)
        if extracted_vars:
            extracted_parent = QTreeWidgetItem(self.tree)
            extracted_parent.setText(0, f"🔗 Extracted ({len(extracted_vars)})")
            extracted_parent.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
            extracted_parent.setExpanded(True)
            extracted_parent.setFirstColumnSpanned(True)
            
            for var in extracted_vars:
                item = QTreeWidgetItem(extracted_parent)
                var_name = var.get('name', '')
                var_value = var.get('value', '')
                var_id = var.get('id')
                source = var.get('source_request_name', 'Unknown')
                
                # Truncate long values
                display_value = self._truncate_value(var_value)
                
                item.setText(0, var_name)
                item.setText(1, display_value)
                item.setToolTip(0, f"Source: {source}")
                item.setToolTip(1, str(var_value))  # Full value in tooltip
                
                # Store full data
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    'name': var_name,
                    'value': var_value,
                    'scope': 'extracted',
                    'id': var_id,
                    'editable': True
                })
                
                # Color code
                item.setForeground(0, QColor("#2196F3"))  # Blue
                
                total_count += 1
        
        # Environment variables
        if environment_vars:
            env_parent = QTreeWidgetItem(self.tree)
            # Get environment sync status for icon
            env_icon = "🔒"  # Default to private
            if environment_id and self.tree.property('db_manager'):
                env = self.tree.property('db_manager').get_environment(environment_id)
                if env and env.get('sync_to_git', 0) == 1:
                    env_icon = "🌐"
            
            env_title = f"{env_icon} Environment: {environment_name or 'Unknown'} ({len(environment_vars)})"
            env_parent.setText(1, env_title)
            env_parent.setFont(1, QFont("Arial", 10, QFont.Weight.Bold))
            env_parent.setExpanded(True)
            env_parent.setFirstColumnSpanned(False)
            
            for var_name, var_value in sorted(environment_vars.items()):
                item = QTreeWidgetItem(env_parent)
                
                # Check if variable is secret
                is_secret = False
                if environment_id and self.tree.property('db_manager'):
                    is_secret = self.tree.property('db_manager').is_variable_secret(environment_id, var_name)
                
                # Type column: 🔐 for secrets, empty for regular
                type_icon = "🔐" if is_secret else ""
                item.setText(0, type_icon)
                
                # Name column
                item.setText(1, var_name)
                item.setForeground(1, QColor("#4CAF50"))  # Green
                
                # Value column: mask if secret
                if is_secret:
                    display_value = "●●●●●●●●●●●●●●●●"  # 16 dots
                    item.setToolTip(2, "Secret variable (value hidden)")
                else:
                    display_value = self._truncate_value(var_value)
                    item.setToolTip(2, str(var_value))
                
                item.setText(2, display_value)
                
                item.setData(1, Qt.ItemDataRole.UserRole, {
                    'name': var_name,
                    'value': var_value,
                    'scope': 'environment',
                    'environment_id': environment_id,
                    'editable': True,
                    'is_secret': is_secret
                })
                
                total_count += 1
        
        # Collection variables
        if collection_vars:
            coll_parent = QTreeWidgetItem(self.tree)
            # Get collection sync status for icon
            coll_icon = "🔒"  # Default to private
            if collection_id and self.tree.property('db_manager'):
                collection = self.tree.property('db_manager').get_collection(collection_id)
                if collection and collection.get('sync_to_git', 0) == 1:
                    coll_icon = "🌐"
            
            coll_parent.setText(0, "")  # Type column empty for parent
            coll_parent.setText(1, f"{coll_icon} Collection ({len(collection_vars)})")
            coll_parent.setFont(1, QFont("Arial", 10, QFont.Weight.Bold))
            coll_parent.setExpanded(True)
            coll_parent.setFirstColumnSpanned(False)
            
            for var in sorted(collection_vars, key=lambda x: x['key']):
                item = QTreeWidgetItem(coll_parent)
                display_value = self._truncate_value(var['value'])
                
                # No secret tracking for collection variables (only environment)
                item.setText(0, "")  # Type column empty
                item.setText(1, var['key'])
                item.setText(2, display_value)
                item.setToolTip(2, str(var['value']))
                
                item.setData(1, Qt.ItemDataRole.UserRole, {
                    'name': var['key'],
                    'value': var['value'],
                    'scope': 'collection',
                    'collection_id': collection_id,
                    'variable_id': var['id'],
                    'editable': True  # Collection vars can be edited
                })
                
                item.setForeground(0, QColor("#FF9800"))  # Orange
                
                total_count += 1
        
        # Dynamic variables (always available)
        dynamic_parent = QTreeWidgetItem(self.tree)
        dynamic_vars = self._get_dynamic_variables()
        dynamic_parent.setText(0, f"⚡ Dynamic ({len(dynamic_vars)})")
        dynamic_parent.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
        dynamic_parent.setExpanded(False)  # Collapsed by default to save space
        dynamic_parent.setFirstColumnSpanned(True)
        
        for var_name, var_desc in dynamic_vars:
            item = QTreeWidgetItem(dynamic_parent)
            item.setText(0, var_name)
            item.setText(1, var_desc)
            
            item.setData(0, Qt.ItemDataRole.UserRole, {
                'name': var_name,
                'value': var_desc,
                'scope': 'dynamic',
                'editable': False
            })
            
            item.setForeground(0, QColor("#9C27B0"))  # Purple
            
            total_count += 1
        
        # Update status
        self.status_label.setText(f"{total_count} variables")
    
    def _get_dynamic_variables(self) -> List[tuple]:
        """Get list of dynamic variables."""
        return [
            ("$timestamp", "Unix timestamp"),
            ("$isoTimestamp", "ISO 8601 timestamp"),
            ("$randomInt", "Random integer"),
            ("$randomUUID", "Random UUID v4"),
            ("$randomEmail", "Random email"),
            ("$randomFirstName", "Random first name"),
            ("$randomLastName", "Random last name"),
            ("$randomFullName", "Random full name"),
            ("$randomStreetAddress", "Random street"),
            ("$randomCity", "Random city"),
            ("$randomCountry", "Random country"),
            ("$randomPhoneNumber", "Random phone"),
            ("$randomIP", "Random IPv4"),
            ("$randomIPv6", "Random IPv6"),
            ("$randomMACAddress", "Random MAC"),
            ("$randomPassword", "Random password"),
            ("$randomLocale", "Random locale"),
            ("$randomUserAgent", "Random user agent"),
            ("$randomUrl", "Random URL"),
            ("$randomDomainName", "Random domain"),
            ("$randomBoolean", "Random boolean"),
            ("$randomHexColor", "Random hex color"),
        ]
    
    def set_theme(self, theme: str):
        """Update theme for the panel."""
        self.current_theme = theme
        self._update_add_button_style()
    
    def _update_add_button_style(self):
        """Update add button style based on current theme."""
        if self.current_theme == 'dark':
            # Dark theme - original style
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
                QPushButton::menu-indicator {
                    width: 0px;
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
                QPushButton::menu-indicator {
                    width: 0px;
                }
            """
        
        self.add_var_btn.setStyleSheet(button_style)
    
    def _truncate_value(self, value: str, max_length: int = 50) -> str:
        """Truncate long values for display."""
        value_str = str(value)
        if len(value_str) > max_length:
            return value_str[:max_length] + "..."
        return value_str
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click - expand/collapse parent items or copy variable syntax for child items."""
        # Check if this is a parent item (category header)
        if item.childCount() > 0:
            # Toggle expand/collapse for parent items
            item.setExpanded(not item.isExpanded())
            return
        
        # For child items (actual variables), copy syntax
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and 'name' in data:
            var_name = data['name']
            scope = data['scope']
            
            # Determine syntax based on scope with new prefix system
            if scope == 'environment':
                syntax = f"{{{{env.{var_name}}}}}"
            elif scope == 'collection':
                syntax = f"{{{{col.{var_name}}}}}"
            elif scope == 'extracted':
                syntax = f"{{{{ext.{var_name}}}}}"
            elif scope == 'dynamic':
                # Dynamic vars: remove $ prefix from name if present, then add in {{$xxx}} format
                clean_name = var_name.lstrip('$')
                syntax = f"{{{{${clean_name}}}}}"
            else:
                # Fallback for unknown scopes
                syntax = f"{{{{{var_name}}}}}"
            
            # Copy to clipboard
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(syntax)
            
            # Show feedback
            self.status_label.setText(f"✓ Copied: {syntax}")
            self.variable_copied.emit(syntax)
            
            # Flash the item
            original_color = item.foreground(0)
            item.setBackground(0, QColor("#FFD700"))
            item.setBackground(1, QColor("#FFD700"))
            
            # Reset after delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(300, lambda: self._reset_item_color(item, original_color))
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click - inline edit for value column on editable items."""
        # Only edit if double-clicking on value column (column 1)
        if column != 1:
            return
        
        # Check if this is a parent item (can't edit categories)
        if item.childCount() > 0:
            return
        
        # Check if item is editable
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or not data.get('editable'):
            return
        
        var_name = data['name']
        current_value = data['value']
        scope = data['scope']
        
        # Use QInputDialog for inline-like editing
        new_value, ok = QInputDialog.getText(
            self,
            "Edit Variable",
            f"Edit value for '{var_name}':",
            QLineEdit.EchoMode.Normal,
            str(current_value)
        )
        
        if ok and new_value != current_value:
            # Emit signal to parent to update in database
            # The parent will call load_variables which will reload everything
            self.variable_edited.emit(scope, var_name, new_value)
            self.status_label.setText(f"✓ Updated: {var_name}")
    
    def _reset_item_color(self, item: QTreeWidgetItem, color):
        """Reset item background color."""
        item.setBackground(0, QColor(Qt.GlobalColor.transparent))
        item.setBackground(1, QColor(Qt.GlobalColor.transparent))
    
    def _show_context_menu(self, position):
        """Show context menu for variable items."""
        print(f"[DEBUG] _show_context_menu called at position: {position}")
        item = self.tree.itemAt(position)
        if not item:
            print(f"[DEBUG] No item at position")
            return
        
        print(f"[DEBUG] Item found: {item.text(1)}")
        data = item.data(1, Qt.ItemDataRole.UserRole)
        if not data or not data.get('editable'):
            print(f"[DEBUG] Item not editable or no data: {data}")
            return
        
        print(f"[DEBUG] Item data: {data}")
        menu = QMenu(self)
        
        # Mark as Secret/Regular action (only for environment variables)
        if data.get('scope') == 'environment' and data.get('environment_id'):
            is_secret = data.get('is_secret', False)
            if is_secret:
                secret_action = menu.addAction("🔓 Mark as Regular")
                secret_action.triggered.connect(lambda: self._toggle_secret_status(item, data, False))
            else:
                secret_action = menu.addAction("🔐 Mark as Secret")
                secret_action.triggered.connect(lambda: self._toggle_secret_status(item, data, True))
            menu.addSeparator()
        
        # Delete action only (edit is via double-click now)
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self._delete_variable(item, data))
        print(f"[DEBUG] Delete action added to menu, showing menu")
        
        menu.exec(self.tree.viewport().mapToGlobal(position))
    
    def _delete_variable(self, item: QTreeWidgetItem, data: dict):
        """Delete variable."""
        var_name = data['name']
        scope = data['scope']
        
        print(f"[DEBUG] _delete_variable called: scope={scope}, name={var_name}")
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Variable",
            f"Delete variable '{var_name}' from {scope}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        print(f"[DEBUG] Confirmation dialog result: {reply}")
        
        if reply == QMessageBox.StandardButton.Yes:
            print(f"[DEBUG] User confirmed deletion, emitting signal: variable_deleted.emit('{scope}', '{var_name}')")
            # Emit signal to parent to delete from database
            # The parent will call _refresh_variable_inspector_panel which will reload everything
            print(f"[DEBUG] Signal object: {self.variable_deleted}")
            self.variable_deleted.emit(scope, var_name)
            print(f"[DEBUG] Signal emitted successfully")
            self.status_label.setText(f"✓ Deleted: {var_name}")
    
    def _toggle_secret_status(self, item: QTreeWidgetItem, data: dict, mark_as_secret: bool):
        """Toggle secret status of an environment variable."""
        var_name = data['name']
        environment_id = data.get('environment_id')
        
        if not environment_id or not self.tree.property('db_manager'):
            return
        
        db = self.tree.property('db_manager')
        if mark_as_secret:
            db.mark_variable_as_secret(environment_id, var_name)
            self.status_label.setText(f"✓ Marked '{var_name}' as secret")
        else:
            db.mark_variable_as_regular(environment_id, var_name)
            self.status_label.setText(f"✓ Marked '{var_name}' as regular")
        
        # Request refresh from parent
        self.refresh_requested.emit()
    
    def set_db_manager(self, db):
        """Set the database manager for accessing secret status."""
        self.db = db
        self.tree.setProperty('db_manager', db)
    
    def _filter_variables(self, text: str):
        """Filter variables based on search text."""
        search_text = text.lower()
        
        # Iterate through all top-level items (categories)
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            visible_children = 0
            
            # Iterate through children (actual variables)
            for j in range(parent.childCount()):
                child = parent.child(j)
                var_name = child.text(0).lower()
                var_value = child.text(1).lower()
                
                # Show if matches search
                matches = search_text in var_name or search_text in var_value
                child.setHidden(not matches)
                
                if matches:
                    visible_children += 1
            
            # Hide category if no visible children
            parent.setHidden(visible_children == 0 and search_text != "")
            
            # Expand categories with matches
            if visible_children > 0 and search_text:
                parent.setExpanded(True)
    
    def _add_environment_variable(self):
        """Add a new variable to an environment."""
        if not self.db:
            QMessageBox.warning(self, "Error", "Database not available.")
            return
        
        # Get all environments
        try:
            environments = self.db.get_all_environments()
            if not environments:
                QMessageBox.warning(self, "No Environments", 
                                  "Please create an environment first before adding variables.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load environments: {str(e)}")
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Environment Variable")
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        # Environment selection
        env_combo = QComboBox()
        for env in environments:
            env_combo.addItem(env['name'], env['id'])
        
        # Set current environment as default if available
        if self.current_environment_id:
            for i in range(env_combo.count()):
                if env_combo.itemData(i) == self.current_environment_id:
                    env_combo.setCurrentIndex(i)
                    break
        
        form_layout.addRow("Environment:", env_combo)
        
        # Name input
        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., baseUrl, apiKey")
        form_layout.addRow("Variable Name:", name_input)
        
        # Value input
        value_input = QLineEdit()
        value_input.setPlaceholderText("e.g., https://api.example.com")
        form_layout.addRow("Value:", value_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_input.text().strip()
            value = value_input.text().strip()
            env_id = env_combo.currentData()
            
            if not name:
                QMessageBox.warning(self, "Invalid Input", "Variable name cannot be empty.")
                return
            
            # Emit signal to parent to add to database
            self.variable_added.emit(name, value)
            self.status_label.setText(f"✓ Added: {name}")
    
    def _add_collection_variable(self):
        """Add a new variable to a collection."""
        if not self.db:
            QMessageBox.warning(self, "Error", "Database not available.")
            return
        
        # Get all collections
        try:
            collections = self.db.get_all_collections()
            if not collections:
                QMessageBox.warning(self, "No Collections", 
                                  "Please create a collection first before adding variables.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load collections: {str(e)}")
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Collection Variable")
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        # Collection selection
        coll_combo = QComboBox()
        for coll in collections:
            coll_combo.addItem(coll['name'], coll['id'])
        
        # Try to set current collection as default if parent has current_collection_id
        parent_window = self.parent()
        if parent_window and hasattr(parent_window, 'current_collection_id') and parent_window.current_collection_id:
            for i in range(coll_combo.count()):
                if coll_combo.itemData(i) == parent_window.current_collection_id:
                    coll_combo.setCurrentIndex(i)
                    break
        
        form_layout.addRow("Collection:", coll_combo)
        
        # Name input
        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., baseUrl, apiKey")
        form_layout.addRow("Variable Name:", name_input)
        
        # Value input
        value_input = QLineEdit()
        value_input.setPlaceholderText("e.g., https://api.example.com")
        form_layout.addRow("Value:", value_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_input.text().strip()
            value = value_input.text().strip()
            coll_id = coll_combo.currentData()
            
            if not name:
                QMessageBox.warning(self, "Invalid Input", "Variable name cannot be empty.")
                return
            
            # Emit signal to parent with collection_id
            self.collection_variable_added.emit(coll_id, name, value)
            self.status_label.setText(f"✓ Added: {name} to collection")
    
    def eventFilter(self, obj, event):
        """Event filter to change cursor on hover over editable value cells."""
        if obj == self.tree.viewport():
            if event.type() == QEvent.Type.MouseMove:
                # Get item at cursor position
                pos = event.pos()
                item = self.tree.itemAt(pos)
                if item:
                    # Check which column
                    column = self.tree.columnAt(pos.x())
                    if column == 1:  # VALUE column
                        # Check if item is editable (not a parent category)
                        if item.childCount() == 0:
                            data = item.data(0, Qt.ItemDataRole.UserRole)
                            if data and data.get('editable'):
                                # Set I-beam cursor for editable cells
                                self.tree.viewport().setCursor(Qt.CursorShape.IBeamCursor)
                                return False
                # Reset to default cursor
                self.tree.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            elif event.type() == QEvent.Type.Leave:
                # Reset cursor when leaving the tree
                self.tree.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        
        return super().eventFilter(obj, event)

