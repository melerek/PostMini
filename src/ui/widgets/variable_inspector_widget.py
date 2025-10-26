"""
Variable Inspector Widget

Shows all available variables in current context grouped by scope.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QDialog,
    QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont
from typing import Dict, List, Optional


class VariableInspectorDialog(QDialog):
    """Dialog showing all available variables in current context."""
    
    variable_copied = pyqtSignal(str)  # Emitted when variable syntax is copied
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Variable Inspector")
        self.setMinimumSize(700, 600)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)  # 4-point grid
        layout.setContentsMargins(12, 12, 12, 12)  # 4-point grid
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)  # 4-point grid
        
        title = QLabel("📊 Variable Inspector")
        title.setStyleSheet("font-size: 14px; font-weight: 600;")  # Use Inter from global
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Info text
        info_label = QLabel(
            "Shows all variables available in the current request context. "
            "Click on a variable to copy its syntax ({{variableName}})."
        )
        info_label.setWordWrap(True)
        info_label.setProperty("class", "secondary")  # Secondary text color
        layout.addWidget(info_label)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)  # 4-point grid
        search_label = QLabel("🔍 Search:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter variables...")
        self.search_input.textChanged.connect(self._filter_variables)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Tree widget for variables
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["VARIABLE", "VALUE", "SOURCE"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 300)
        self.tree.setColumnWidth(2, 150)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)
        
        # Status label
        self.status_label = QLabel("No variables loaded")
        self.status_label.setProperty("class", "tertiary")  # Tertiary text
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  # 4-point grid
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_variables(self, 
                       environment_vars: Dict[str, str] = None,
                       collection_vars: Dict[str, str] = None,
                       extracted_vars: List[Dict] = None,
                       environment_name: str = None):
        """
        Load and display variables.
        
        Args:
            environment_vars: Dictionary of environment variables
            collection_vars: Dictionary of collection variables
            extracted_vars: List of extracted variable dictionaries
            environment_name: Name of active environment
        """
        self.tree.clear()
        total_count = 0
        
        # Extracted variables (highest priority)
        if extracted_vars:
            extracted_parent = QTreeWidgetItem(self.tree)
            extracted_parent.setText(0, f"🔗 Extracted Variables ({len(extracted_vars)})")
            extracted_parent.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
            extracted_parent.setExpanded(True)
            extracted_parent.setFirstColumnSpanned(True)
            
            for var in extracted_vars:
                item = QTreeWidgetItem(extracted_parent)
                var_name = var.get('name', '')
                var_value = var.get('value', '')
                source = var.get('source_request_name', 'Unknown')
                
                # Truncate long values
                display_value = self._truncate_value(var_value)
                
                item.setText(0, var_name)
                item.setText(1, display_value)
                item.setText(2, f"Extracted from: {source}")
                item.setToolTip(1, str(var_value))  # Full value in tooltip
                
                # Store full data
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    'name': var_name,
                    'value': var_value,
                    'scope': 'extracted'
                })
                
                # Color code
                item.setForeground(0, QColor("#2196F3"))  # Blue
                
                total_count += 1
        
        # Environment variables
        if environment_vars:
            env_parent = QTreeWidgetItem(self.tree)
            env_title = f"🌍 Environment Variables: {environment_name or 'Unknown'} ({len(environment_vars)})"
            env_parent.setText(0, env_title)
            env_parent.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
            env_parent.setExpanded(True)
            env_parent.setFirstColumnSpanned(True)
            
            for var_name, var_value in sorted(environment_vars.items()):
                item = QTreeWidgetItem(env_parent)
                display_value = self._truncate_value(var_value)
                
                item.setText(0, var_name)
                item.setText(1, display_value)
                item.setText(2, "Environment")
                item.setToolTip(1, str(var_value))
                
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    'name': var_name,
                    'value': var_value,
                    'scope': 'environment'
                })
                
                item.setForeground(0, QColor("#4CAF50"))  # Green
                
                total_count += 1
        
        # Collection variables
        if collection_vars:
            coll_parent = QTreeWidgetItem(self.tree)
            coll_parent.setText(0, f"📦 Collection Variables ({len(collection_vars)})")
            coll_parent.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
            coll_parent.setExpanded(True)
            coll_parent.setFirstColumnSpanned(True)
            
            for var_name, var_value in sorted(collection_vars.items()):
                item = QTreeWidgetItem(coll_parent)
                display_value = self._truncate_value(var_value)
                
                item.setText(0, var_name)
                item.setText(1, display_value)
                item.setText(2, "Collection")
                item.setToolTip(1, str(var_value))
                
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    'name': var_name,
                    'value': var_value,
                    'scope': 'collection'
                })
                
                item.setForeground(0, QColor("#FF9800"))  # Orange
                
                total_count += 1
        
        # Dynamic variables (always available)
        dynamic_parent = QTreeWidgetItem(self.tree)
        dynamic_vars = self._get_dynamic_variables()
        dynamic_parent.setText(0, f"⚡ Dynamic Variables ({len(dynamic_vars)})")
        dynamic_parent.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
        dynamic_parent.setExpanded(True)  # Expanded by default
        dynamic_parent.setFirstColumnSpanned(True)
        
        for var_name, var_desc in dynamic_vars:
            item = QTreeWidgetItem(dynamic_parent)
            item.setText(0, var_name)
            item.setText(1, var_desc)
            item.setText(2, "Dynamic")
            
            item.setData(0, Qt.ItemDataRole.UserRole, {
                'name': var_name,
                'value': var_desc,
                'scope': 'dynamic'
            })
            
            item.setForeground(0, QColor("#9C27B0"))  # Purple
            
            total_count += 1
        
        # Update status
        self.status_label.setText(f"Total: {total_count} variables available")
    
    def _get_dynamic_variables(self) -> List[tuple]:
        """Get list of dynamic variables."""
        return [
            ("$timestamp", "Current Unix timestamp"),
            ("$isoTimestamp", "ISO 8601 timestamp"),
            ("$randomInt", "Random integer"),
            ("$randomUUID", "Random UUID v4"),
            ("$randomEmail", "Random email"),
            ("$randomFirstName", "Random first name"),
            ("$randomLastName", "Random last name"),
            ("$randomFullName", "Random full name"),
            ("$randomStreetAddress", "Random street address"),
            ("$randomCity", "Random city"),
            ("$randomCountry", "Random country"),
            ("$randomPhoneNumber", "Random phone number"),
            ("$randomIP", "Random IPv4 address"),
            ("$randomIPv6", "Random IPv6 address"),
            ("$randomMACAddress", "Random MAC address"),
            ("$randomPassword", "Random password"),
            ("$randomLocale", "Random locale"),
            ("$randomUserAgent", "Random user agent"),
            ("$randomUrl", "Random URL"),
            ("$randomDomainName", "Random domain name"),
            ("$randomBoolean", "Random boolean"),
            ("$randomHexColor", "Random hex color"),
            ("$randomAbbreviation", "Random abbreviation"),
            ("$randomAlphaNumeric", "Random alphanumeric"),
            ("$randomBankAccount", "Random bank account"),
            ("$randomBitcoin", "Random bitcoin address"),
            ("$randomCompanyName", "Random company name"),
            ("$randomCreditCardNumber", "Random credit card"),
            ("$randomCurrencyCode", "Random currency code"),
            ("$randomCurrencyName", "Random currency name"),
            ("$randomDateFuture", "Random future date"),
            ("$randomDatePast", "Random past date"),
            ("$randomDateRecent", "Random recent date"),
            ("$randomFileName", "Random filename"),
            ("$randomFilePath", "Random file path"),
            ("$randomImageUrl", "Random image URL"),
            ("$randomJobTitle", "Random job title"),
            ("$randomMonth", "Random month"),
            ("$randomPrice", "Random price"),
        ]
    
    def _truncate_value(self, value: str, max_length: int = 80) -> str:
        """Truncate long values for display."""
        value_str = str(value)
        if len(value_str) > max_length:
            return value_str[:max_length] + "..."
        return value_str
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click - copy variable syntax."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and 'name' in data:
            var_name = data['name']
            scope = data['scope']
            
            # Determine syntax based on scope
            if scope == 'extracted':
                syntax = f"{{{{extracted.{var_name}}}}}"
            elif scope == 'dynamic':
                syntax = var_name  # Dynamic vars already have $
            else:
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
            item.setBackground(2, QColor("#FFD700"))
            
            # Reset after delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(300, lambda: self._reset_item_color(item, original_color))
    
    def _reset_item_color(self, item: QTreeWidgetItem, color):
        """Reset item background color."""
        item.setBackground(0, QColor(Qt.GlobalColor.transparent))
        item.setBackground(1, QColor(Qt.GlobalColor.transparent))
        item.setBackground(2, QColor(Qt.GlobalColor.transparent))
    
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
    
    def _refresh(self):
        """Refresh variables - emit signal to parent."""
        # Parent (MainWindow) should call load_variables again
        self.status_label.setText("Refreshing...")
        self.parent().refresh_variable_inspector()

