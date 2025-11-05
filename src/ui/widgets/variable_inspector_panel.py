"""
Variable Inspector Panel

Shows all available variables in current context grouped by scope.
Allows editing and deleting environment and extracted variables.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog,
    QMessageBox, QStyledItemDelegate, QStyle, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QCursor, QFont
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
    refresh_requested = pyqtSignal()  # Request parent to refresh data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_environment_id = None
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
        
        title = QLabel("{{}} Variables")
        title.setStyleSheet("font-size: 13px; font-weight: 600; border: none;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
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
        
        # Search box with Add button
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter variables...")
        self.search_input.textChanged.connect(self._filter_variables)
        search_layout.addWidget(self.search_input)
        
        # Add Variable button
        self.add_var_btn = QPushButton("➕")
        self.add_var_btn.setToolTip("Add variable to current environment")
        self.add_var_btn.setFixedSize(32, 32)
        self.add_var_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(255, 255, 255, 0.3);
                background: rgba(33, 150, 243, 0.2);
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(33, 150, 243, 0.4);
            }
            QPushButton:disabled {
                background: rgba(100, 100, 100, 0.2);
                border-color: rgba(100, 100, 100, 0.3);
                color: #666;
            }
        """)
        self.add_var_btn.clicked.connect(self._add_variable)
        self.add_var_btn.setEnabled(False)  # Disabled by default
        search_layout.addWidget(self.add_var_btn)
        
        content_layout.addLayout(search_layout)
        
        # Tree widget for variables
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["NAME", "VALUE"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 200)
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
        self.setMinimumWidth(300)
    
    def load_variables(self, 
                       environment_vars: Dict[str, str] = None,
                       collection_vars: Dict[str, str] = None,
                       extracted_vars: List[Dict] = None,
                       environment_name: str = None,
                       environment_id: int = None):
        """
        Load and display variables.
        
        Args:
            environment_vars: Dictionary of environment variables
            collection_vars: Dictionary of collection variables
            extracted_vars: List of extracted variable dictionaries
            environment_name: Name of active environment
            environment_id: ID of active environment
        """
        self.tree.clear()
        self.current_environment_id = environment_id
        total_count = 0
        
        # Enable/disable Add button based on whether environment is selected
        if environment_id:
            self.add_var_btn.setEnabled(True)
            self.add_var_btn.setToolTip(f"Add variable to environment: {environment_name}")
        else:
            self.add_var_btn.setEnabled(False)
            self.add_var_btn.setToolTip("Select an environment to add variables")
        
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
            env_title = f"🌍 Environment: {environment_name or 'Unknown'} ({len(environment_vars)})"
            env_parent.setText(0, env_title)
            env_parent.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
            env_parent.setExpanded(True)
            env_parent.setFirstColumnSpanned(True)
            
            for var_name, var_value in sorted(environment_vars.items()):
                item = QTreeWidgetItem(env_parent)
                display_value = self._truncate_value(var_value)
                
                item.setText(0, var_name)
                item.setText(1, display_value)
                item.setToolTip(1, str(var_value))
                
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    'name': var_name,
                    'value': var_value,
                    'scope': 'environment',
                    'environment_id': environment_id,
                    'editable': True
                })
                
                item.setForeground(0, QColor("#4CAF50"))  # Green
                
                total_count += 1
        
        # Collection variables
        if collection_vars:
            coll_parent = QTreeWidgetItem(self.tree)
            coll_parent.setText(0, f"📦 Collection ({len(collection_vars)})")
            coll_parent.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
            coll_parent.setExpanded(True)
            coll_parent.setFirstColumnSpanned(True)
            
            for var_name, var_value in sorted(collection_vars.items()):
                item = QTreeWidgetItem(coll_parent)
                display_value = self._truncate_value(var_value)
                
                item.setText(0, var_name)
                item.setText(1, display_value)
                item.setToolTip(1, str(var_value))
                
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    'name': var_name,
                    'value': var_value,
                    'scope': 'collection',
                    'editable': False  # Collection vars can't be edited here
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
        
        print(f"[DEBUG] Item found: {item.text(0)}")
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or not data.get('editable'):
            print(f"[DEBUG] Item not editable or no data: {data}")
            return
        
        print(f"[DEBUG] Item data: {data}")
        menu = QMenu(self)
        
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
    
    def _add_variable(self):
        """Add a new variable to the current environment."""
        if not self.current_environment_id:
            QMessageBox.warning(self, "No Environment", "Please select an environment first.")
            return
        
        # Create a dialog for adding variable
        from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Environment Variable")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
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
            
            if not name:
                QMessageBox.warning(self, "Invalid Input", "Variable name cannot be empty.")
                return
            
            # Emit signal to parent to add to database
            self.variable_added.emit(name, value)
            self.status_label.setText(f"✓ Added: {name}")
    
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

