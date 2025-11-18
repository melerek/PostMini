"""
Cookie Tab Widget

UI component for managing HTTP cookies in requests.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QMessageBox, QMenu, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QAction
from typing import List, Dict, Optional
from datetime import datetime
import time


class CookieTabWidget(QWidget):
    """Widget for managing HTTP cookies."""
    
    cookies_changed = pyqtSignal()  # Emitted when cookies are modified
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self.db_manager = None  # Will be set by MainWindow
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with description and buttons
        header_layout = QHBoxLayout()
        
        header_label = QLabel("🍪 Cookies")
        header_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(header_label)
        
        description_label = QLabel("Manage HTTP cookies for requests")
        description_label.setStyleSheet("color: #9E9E9E; font-size: 11px;")
        header_layout.addWidget(description_label)
        
        header_layout.addStretch()
        
        # Add Cookie button
        self.add_cookie_btn = QPushButton("+ Add Cookie")
        self.add_cookie_btn.setFixedHeight(24)
        self.add_cookie_btn.clicked.connect(self._add_cookie_row)
        header_layout.addWidget(self.add_cookie_btn)
        
        # Clear All button
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.setFixedHeight(24)
        self.clear_all_btn.clicked.connect(self._clear_all_cookies)
        header_layout.addWidget(self.clear_all_btn)
        
        # Delete Expired button
        self.delete_expired_btn = QPushButton("Delete Expired")
        self.delete_expired_btn.setFixedHeight(24)
        self.delete_expired_btn.clicked.connect(self._delete_expired_cookies)
        header_layout.addWidget(self.delete_expired_btn)
        
        layout.addLayout(header_layout)
        
        # Cookie table
        self.cookie_table = self._create_cookie_table()
        layout.addWidget(self.cookie_table)
        
        # Info label
        info_label = QLabel("💡 Cookies are automatically saved from responses and sent with matching requests")
        info_label.setStyleSheet("color: #757575; font-size: 10px; font-style: italic;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
    
    def _create_cookie_table(self) -> QTableWidget:
        """Create the cookie table."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Domain", "Name", "Value", "Path", "Expires", "Secure", "HttpOnly"
        ])
        
        # Set tooltips for headers
        table.horizontalHeaderItem(0).setToolTip("Cookie domain (e.g., example.com or .example.com for subdomains)")
        table.horizontalHeaderItem(1).setToolTip("Cookie name identifier")
        table.horizontalHeaderItem(2).setToolTip("Cookie value")
        table.horizontalHeaderItem(3).setToolTip("Path where cookie is valid (default: /)")
        table.horizontalHeaderItem(4).setToolTip("Expiration date/time (Session = expires when browser closes)")
        table.horizontalHeaderItem(5).setToolTip("Secure flag - cookie only sent over HTTPS")
        table.horizontalHeaderItem(6).setToolTip("HttpOnly flag - cookie not accessible via JavaScript")
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Domain
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Value (expands)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Path
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Expires
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Secure
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # HttpOnly
        
        # Style
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Connect signals
        table.itemChanged.connect(self._on_cookie_edited)
        table.customContextMenuRequested.connect(self._show_context_menu)
        
        return table
    
    def set_db_manager(self, db_manager):
        """Set the database manager."""
        self.db_manager = db_manager
    
    def load_cookies(self, cookies: List[Dict] = None):
        """
        Load cookies into the table.
        
        Args:
            cookies: List of cookie dictionaries (None = load from database)
        """
        # Block signals while loading
        self.cookie_table.blockSignals(True)
        
        try:
            if cookies is None and self.db_manager:
                # Load from database - returns Row objects
                cookies_raw = self.db_manager.get_all_cookies()
                # Convert Row objects to dicts
                cookies = [dict(row) for row in cookies_raw] if cookies_raw else []
            
            if not cookies:
                cookies = []
            
            self.cookie_table.setRowCount(len(cookies))
            
            for row, cookie in enumerate(cookies):
                self._populate_cookie_row(row, cookie)
            
        finally:
            self.cookie_table.blockSignals(False)
    
    def _populate_cookie_row(self, row: int, cookie: Dict):
        """Populate a table row with cookie data."""
        # Domain
        domain_item = QTableWidgetItem(cookie.get('domain', ''))
        self.cookie_table.setItem(row, 0, domain_item)
        
        # Name
        name_item = QTableWidgetItem(cookie.get('name', ''))
        self.cookie_table.setItem(row, 1, name_item)
        
        # Value
        value_item = QTableWidgetItem(cookie.get('value', ''))
        self.cookie_table.setItem(row, 2, value_item)
        
        # Path
        path_item = QTableWidgetItem(cookie.get('path', '/'))
        self.cookie_table.setItem(row, 3, path_item)
        
        # Expires (format timestamp)
        expires = cookie.get('expires')
        if expires:
            try:
                expires_dt = datetime.fromtimestamp(expires)
                expires_str = expires_dt.strftime("%Y-%m-%d %H:%M")
            except:
                expires_str = "Invalid"
        else:
            expires_str = "Session"
        expires_item = QTableWidgetItem(expires_str)
        expires_item.setFlags(expires_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
        self.cookie_table.setItem(row, 4, expires_item)
        
        # Secure checkbox
        secure_widget = QWidget()
        secure_layout = QHBoxLayout(secure_widget)
        secure_layout.setContentsMargins(0, 0, 0, 0)
        secure_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        secure_cb = QCheckBox()
        secure_cb.setChecked(bool(cookie.get('secure', 0)))
        secure_cb.stateChanged.connect(lambda: self._on_checkbox_changed(row))
        secure_layout.addWidget(secure_cb)
        self.cookie_table.setCellWidget(row, 5, secure_widget)
        
        # HttpOnly checkbox
        httponly_widget = QWidget()
        httponly_layout = QHBoxLayout(httponly_widget)
        httponly_layout.setContentsMargins(0, 0, 0, 0)
        httponly_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        httponly_cb = QCheckBox()
        httponly_cb.setChecked(bool(cookie.get('http_only', 0)))
        httponly_cb.stateChanged.connect(lambda: self._on_checkbox_changed(row))
        httponly_layout.addWidget(httponly_cb)
        self.cookie_table.setCellWidget(row, 6, httponly_widget)
        
        # Store cookie ID in row
        if 'id' in cookie:
            domain_item.setData(Qt.ItemDataRole.UserRole, cookie['id'])
    
    def _add_cookie_row(self):
        """Add a new empty cookie row."""
        row = self.cookie_table.rowCount()
        self.cookie_table.insertRow(row)
        
        # Add empty items
        self.cookie_table.setItem(row, 0, QTableWidgetItem(""))  # Domain
        self.cookie_table.setItem(row, 1, QTableWidgetItem(""))  # Name
        self.cookie_table.setItem(row, 2, QTableWidgetItem(""))  # Value
        self.cookie_table.setItem(row, 3, QTableWidgetItem("/"))  # Path
        
        expires_item = QTableWidgetItem("Session")
        expires_item.setFlags(expires_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.cookie_table.setItem(row, 4, expires_item)
        
        # Secure checkbox
        secure_widget = QWidget()
        secure_layout = QHBoxLayout(secure_widget)
        secure_layout.setContentsMargins(0, 0, 0, 0)
        secure_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        secure_cb = QCheckBox()
        secure_cb.stateChanged.connect(lambda: self._on_checkbox_changed(row))
        secure_layout.addWidget(secure_cb)
        self.cookie_table.setCellWidget(row, 5, secure_widget)
        
        # HttpOnly checkbox
        httponly_widget = QWidget()
        httponly_layout = QHBoxLayout(httponly_widget)
        httponly_layout.setContentsMargins(0, 0, 0, 0)
        httponly_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        httponly_cb = QCheckBox()
        httponly_cb.stateChanged.connect(lambda: self._on_checkbox_changed(row))
        httponly_layout.addWidget(httponly_cb)
        self.cookie_table.setCellWidget(row, 6, httponly_widget)
        
        self.cookies_changed.emit()
    
    def _show_context_menu(self, position):
        """Show context menu for cookie table."""
        row = self.cookie_table.rowAt(position.y())
        if row < 0:
            return
        
        menu = QMenu(self)
        delete_action = QAction("🗑️ Delete Cookie", self)
        delete_action.triggered.connect(lambda: self._delete_cookie_row(row))
        menu.addAction(delete_action)
        
        menu.exec(self.cookie_table.viewport().mapToGlobal(position))
    
    def _delete_cookie_row(self, row: int):
        """Delete a cookie row."""
        if row < 0 or row >= self.cookie_table.rowCount():
            return
        
        # Get cookie ID if exists
        domain_item = self.cookie_table.item(row, 0)
        cookie_id = domain_item.data(Qt.ItemDataRole.UserRole) if domain_item else None
        
        # Delete from database if has ID
        if cookie_id and self.db_manager:
            self.db_manager.delete_cookie(cookie_id)
        
        # Remove row from table
        self.cookie_table.removeRow(row)
        self.cookies_changed.emit()
    
    def _clear_all_cookies(self):
        """Clear all cookies."""
        reply = QMessageBox.question(
            self,
            "Clear All Cookies",
            "Are you sure you want to delete all cookies?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager:
                self.db_manager.delete_all_cookies()
            self.cookie_table.setRowCount(0)
            self.cookies_changed.emit()
    
    def _delete_expired_cookies(self):
        """Delete expired cookies."""
        if self.db_manager:
            self.db_manager.delete_expired_cookies()
            self.load_cookies()  # Reload from database
            self.cookies_changed.emit()
    
    def _on_cookie_edited(self, item):
        """Handle cookie cell edit."""
        if not self.db_manager:
            return
        
        row = item.row()
        self._save_cookie_row(row)
        self.cookies_changed.emit()
    
    def _on_checkbox_changed(self, row: int):
        """Handle checkbox state change."""
        self._save_cookie_row(row)
        self.cookies_changed.emit()
    
    def _save_cookie_row(self, row: int):
        """Save a cookie row to database."""
        if not self.db_manager:
            return
        
        # Get values from row
        domain_item = self.cookie_table.item(row, 0)
        name_item = self.cookie_table.item(row, 1)
        value_item = self.cookie_table.item(row, 2)
        path_item = self.cookie_table.item(row, 3)
        
        if not domain_item or not name_item:
            return
        
        domain = domain_item.text().strip()
        name = name_item.text().strip()
        value = value_item.text() if value_item else ""
        path = path_item.text() if path_item else "/"
        
        if not domain or not name:
            return
        
        # Get checkbox values
        secure_widget = self.cookie_table.cellWidget(row, 5)
        httponly_widget = self.cookie_table.cellWidget(row, 6)
        
        secure = False
        httponly = False
        
        if secure_widget:
            secure_cb = secure_widget.findChild(QCheckBox)
            if secure_cb:
                secure = secure_cb.isChecked()
        
        if httponly_widget:
            httponly_cb = httponly_widget.findChild(QCheckBox)
            if httponly_cb:
                httponly = httponly_cb.isChecked()
        
        # Save to database
        cookie_id = self.db_manager.create_cookie(
            domain=domain,
            name=name,
            value=value,
            path=path,
            secure=secure,
            http_only=httponly
        )
        
        # Store ID in item
        domain_item.setData(Qt.ItemDataRole.UserRole, cookie_id)
    
    def get_cookies_as_list(self) -> List[Dict]:
        """
        Get all cookies from table as list of dictionaries.
        
        Returns:
            List of cookie dictionaries
        """
        cookies = []
        
        for row in range(self.cookie_table.rowCount()):
            domain_item = self.cookie_table.item(row, 0)
            name_item = self.cookie_table.item(row, 1)
            value_item = self.cookie_table.item(row, 2)
            path_item = self.cookie_table.item(row, 3)
            
            if not domain_item or not name_item:
                continue
            
            domain = domain_item.text().strip()
            name = name_item.text().strip()
            
            if not domain or not name:
                continue
            
            value = value_item.text() if value_item else ""
            path = path_item.text() if path_item else "/"
            
            # Get checkbox values
            secure_widget = self.cookie_table.cellWidget(row, 5)
            httponly_widget = self.cookie_table.cellWidget(row, 6)
            
            secure = False
            httponly = False
            
            if secure_widget:
                secure_cb = secure_widget.findChild(QCheckBox)
                if secure_cb:
                    secure = secure_cb.isChecked()
            
            if httponly_widget:
                httponly_cb = httponly_widget.findChild(QCheckBox)
                if httponly_cb:
                    httponly = httponly_cb.isChecked()
            
            cookie_id = domain_item.data(Qt.ItemDataRole.UserRole)
            
            cookies.append({
                'id': cookie_id,
                'domain': domain,
                'name': name,
                'value': value,
                'path': path,
                'secure': secure,
                'http_only': httponly
            })
        
        return cookies
    
    def set_theme(self, theme: str):
        """Update theme."""
        self.theme = theme
        # Theme changes are handled by main window's QSS
