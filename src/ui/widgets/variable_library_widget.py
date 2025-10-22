"""
Variable Library Widget

This widget displays all extracted variables in a table with options to manage them.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QAction
from datetime import datetime
from typing import List, Dict


class VariableLibraryWidget(QWidget):
    """Widget for viewing and managing extracted variables."""
    
    variable_deleted = pyqtSignal(int)  # variable_id
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.variables = []
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📚 Variable Library")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        clear_all_btn = QPushButton("🗑️ Clear All")
        clear_all_btn.clicked.connect(self._on_clear_all_clicked)
        header_layout.addWidget(clear_all_btn)
        
        layout.addLayout(header_layout)
        
        # Info label
        info = QLabel("💡 Use {{extracted.variableName}} in your requests to reference these variables")
        info.setStyleSheet("padding: 8px; background: #E8F5E9; border-radius: 4px; color: #2E7D32;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Variables table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Variable", "Value", "Source", "Path", "Extracted"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Stats footer
        self.stats_label = QLabel("0 variables")
        self.stats_label.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
        layout.addWidget(self.stats_label)
        
        # Empty state
        self.empty_label = QLabel(
            "📭 No variables extracted yet\n\n"
            "After sending a request, go to the 'Extract Variables' tab\n"
            "to extract values from the response."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #999; font-size: 13px; padding: 40px;")
        layout.addWidget(self.empty_label)
        self.empty_label.hide()
    
    def set_variables(self, variables: List[Dict]):
        """
        Update the table with variables.
        
        Args:
            variables: List of variable dictionaries from database
        """
        self.variables = variables
        self.table.setRowCount(0)
        
        if not variables:
            self.table.hide()
            self.empty_label.show()
            self.stats_label.setText("0 variables")
            return
        
        self.table.show()
        self.empty_label.hide()
        
        for var in variables:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Variable name (bold)
            name_item = QTableWidgetItem(var['name'])
            font = QFont()
            font.setBold(True)
            name_item.setFont(font)
            name_item.setData(Qt.ItemDataRole.UserRole, var['id'])
            self.table.setItem(row, 0, name_item)
            
            # Value (truncated)
            value = str(var['value'])
            if len(value) > 50:
                value = value[:50] + "..."
            value_item = QTableWidgetItem(value)
            value_item.setToolTip(str(var['value']))  # Full value in tooltip
            self.table.setItem(row, 1, value_item)
            
            # Source request
            source = var.get('source_request_name', 'Manual')
            self.table.setItem(row, 2, QTableWidgetItem(source))
            
            # JSON path
            path = var.get('json_path', '')
            path_item = QTableWidgetItem(path)
            path_item.setForeground(Qt.GlobalColor.darkGray)
            self.table.setItem(row, 3, path_item)
            
            # Extracted time
            extracted_at = var.get('extracted_at', '')
            if extracted_at:
                try:
                    dt = datetime.fromisoformat(extracted_at)
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = extracted_at
            else:
                time_str = ""
            self.table.setItem(row, 4, QTableWidgetItem(time_str))
        
        self.stats_label.setText(f"{len(variables)} variable{'s' if len(variables) != 1 else ''}")
    
    def _show_context_menu(self, position):
        """Show context menu for table items."""
        item = self.table.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Get variable ID
        row = item.row()
        name_item = self.table.item(row, 0)
        variable_id = name_item.data(Qt.ItemDataRole.UserRole)
        variable_name = name_item.text()
        value = self.table.item(row, 1).text()
        
        # Copy variable reference
        copy_ref_action = QAction(f"📋 Copy Reference ({{{{extracted.{variable_name}}}}})", self)
        copy_ref_action.triggered.connect(lambda: self._copy_to_clipboard(f"{{{{extracted.{variable_name}}}}}"))
        menu.addAction(copy_ref_action)
        
        # Copy value
        copy_value_action = QAction(f"📋 Copy Value", self)
        copy_value_action.triggered.connect(lambda: self._copy_to_clipboard(value))
        menu.addAction(copy_value_action)
        
        menu.addSeparator()
        
        # Delete
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(lambda: self._delete_variable(variable_id, variable_name))
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
    
    def _delete_variable(self, variable_id: int, variable_name: str):
        """Delete a variable."""
        reply = QMessageBox.question(
            self,
            "Delete Variable",
            f"Are you sure you want to delete variable '{variable_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.variable_deleted.emit(variable_id)
    
    def _on_clear_all_clicked(self):
        """Handle clear all button click."""
        if not self.variables:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear All Variables",
            f"Are you sure you want to delete all {len(self.variables)} variables?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Emit delete for each variable
            for var in self.variables:
                self.variable_deleted.emit(var['id'])

