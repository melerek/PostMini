"""
Main Window Module

This module contains the MainWindow class which defines the complete UI layout
and connects all UI elements to the application logic. It provides a three-pane
interface similar to Postman with collections, request editor, and response viewer.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit,
    QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem, QLabel,
    QMessageBox, QInputDialog, QHeaderView, QToolBar, QFileDialog, QApplication,
    QSizePolicy, QDialog, QStyledItemDelegate, QMenu, QGroupBox, QTabBar, QTreeWidgetItemIterator,
    QDialogButtonBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QAction, QKeySequence, QShortcut, QBrush, QColor, QPalette, QPainter, QPen
import json
from typing import Dict, Optional

from src.core.database import DatabaseManager
from src.core.api_client import ApiClient, ApiResponse
from src.core.app_paths import AppPaths
from src.features.variable_substitution import EnvironmentManager
from src.features.collection_io import CollectionExporter, CollectionImporter, get_safe_filename
from src.features.script_engine import ScriptEngine, ScriptExecutionError, ScriptTimeoutError
from src.ui.dialogs.code_snippet_dialog import CodeSnippetDialog
from src.ui.widgets.history_panel_widget import HistoryPanelWidget
from src.ui.dialogs.oauth_dialog import OAuthConfigDialog
from src.ui.dialogs.update_dialog import UpdateAvailableDialog, UpdateProgressDialog, NoUpdateDialog
from src.features.oauth_manager import OAuthManager
from src.features.auto_updater import UpdateChecker, UpdateDownloader, UpdateInstaller
from src.ui.widgets.test_tab_widget import TestTabWidget
from src.ui.widgets.test_results_viewer import TestResultsViewer
from src.ui.widgets.script_tab_widget import ScriptTabWidget
from src.ui.widgets.cookie_tab_widget import CookieTabWidget
from src.ui.widgets.syntax_highlighter import apply_syntax_highlighting
from src.ui.widgets.recent_requests_widget import RecentRequestsWidget
from src.ui.widgets.method_badge import MethodBadge, StatusBadge
from src.ui.widgets.variable_extraction_widget import VariableExtractionWidget
from src.ui.widgets.security_scan_tab import SecurityScanTab
from src.ui.widgets.variable_inspector_widget import VariableInspectorDialog
from src.ui.widgets.settings_panel import SettingsPanel
from src.ui.widgets.git_sync_panel import GitSyncPanel
from src.ui.widgets.variable_inspector_panel import VariableInspectorPanel
from src.ui.widgets.environments_panel import EnvironmentsPanel
from src.ui.widgets.variable_library_widget import VariableLibraryWidget
from src.ui.widgets.variable_highlight_delegate import VariableSyntaxHighlighter, VariableHighlightDelegate, HighlightedLineEdit
from src.ui.widgets.empty_state import NoRequestEmptyState, NoResponseEmptyState, NoCollectionsEmptyState
from src.features.test_engine import TestEngine, TestAssertion
from src.features.security_scanner import SecurityScanner
from src.features.security_report_generator import SecurityReportGenerator
from src.ui.dialogs.collection_test_runner import CollectionTestRunnerDialog
from src.ui.dialogs.git_sync_dialog import GitSyncDialog
from src.ui.dialogs.conflict_resolution_dialog import ConflictResolutionDialog
from src.ui.dialogs.curl_import_dialog import CurlImportDialog
from src.features.git_sync_manager import GitSyncManager, GitSyncConfig, SyncStatus
from src.features.secrets_manager import SecretsManager
from src.features.curl_converter import CurlConverter
from datetime import datetime
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class ReorderableTreeWidget(QTreeWidget):
    """Custom QTreeWidget that handles drag & drop reordering."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None  # Will be set by MainWindow
        self._dragged_item = None
        self._dragged_data = None
    
    def startDrag(self, supportedActions):
        """Store dragged item info before drag starts."""
        self._dragged_item = self.currentItem()
        if self._dragged_item:
            self._dragged_data = self._dragged_item.data(0, Qt.ItemDataRole.UserRole)
        super().startDrag(supportedActions)
    
    def dropMimeData(self, parent, index, data, action):
        """Validate drop operations before allowing them."""
        if not self._dragged_item or not self._dragged_data:
            return False
        
        dragged_type = self._dragged_data.get('type')
        drop_indicator = self.dropIndicatorPosition()
        
        # Get target item (where we're dropping)
        target_item = parent
        target_data = target_item.data(0, Qt.ItemDataRole.UserRole) if target_item else None
        target_type = target_data.get('type') if target_data else None
        
        print(f"[DROP MIME] Dragged: {dragged_type}, Target: {target_type}, Indicator: {drop_indicator}")
        
        # Validation rules (Postman-style):
        # 1. Collections are TOP-LEVEL ONLY - cannot be nested inside anything
        # 2. Folders can be dropped on collections or other folders (not on requests)
        # 3. Requests can be dropped on folders or collections (not on other requests)
        
        if dragged_type == 'collection':
            # Collections must stay at root level - cannot be nested
            # Block if trying to drop ON any item
            if drop_indicator == QTreeWidget.DropIndicatorPosition.OnItem:
                print(f"[DROP BLOCKED in dropMimeData] Cannot nest collections")
                return False
            # Block if target has a parent (is not at root level)
            # Collections can only be dropped at root - next to other collections
            if target_item is not None:
                # Check if target item has a parent (not at root)
                if target_item.parent() is not None:
                    print(f"[DROP BLOCKED in dropMimeData] Collections can only be reordered at root level")
                    return False
                # If target is not a collection, block (collections can only be next to other collections)
                if target_type != 'collection':
                    print(f"[DROP BLOCKED in dropMimeData] Collections can only be dropped next to other collections")
                    return False
        
        elif dragged_type == 'folder':
            # Get the collection ID of the dragged folder
            dragged_collection_id = self._dragged_data.get('collection_id')
            
            # Folders must ALWAYS be inside a collection or folder, never at root level
            if target_item is None:
                print(f"[DROP BLOCKED in dropMimeData] Folders cannot be at root level")
                return False
            
            # Determine the target collection ID
            target_collection_id = None
            if target_item:
                if target_type == 'collection':
                    target_collection_id = target_data.get('id')
                elif target_type in ('folder', 'request'):
                    target_collection_id = target_data.get('collection_id')
            
            # Block if trying to move folder to a different collection
            if target_collection_id and target_collection_id != dragged_collection_id:
                print(f"[DROP BLOCKED in dropMimeData] Cannot move folder between collections")
                return False
            
            # Folders can be dropped on collections or folders, but not on requests
            if target_type == 'request' and drop_indicator == QTreeWidget.DropIndicatorPosition.OnItem:
                print(f"[DROP BLOCKED in dropMimeData] Cannot drop folder on request")
                return False
            
            # Prevent circular references: folder cannot be dropped into itself or its descendants
            if drop_indicator == QTreeWidget.DropIndicatorPosition.OnItem and target_type == 'folder':
                dragged_folder_id = self._dragged_data.get('id')
                target_folder_id = target_data.get('id')
                
                # Check if target is the dragged folder itself
                if dragged_folder_id == target_folder_id:
                    print(f"[DROP BLOCKED in dropMimeData] Cannot drop folder into itself")
                    return False
                
                # Check if target is a descendant of dragged folder
                def is_descendant(potential_descendant_id, ancestor_id):
                    """Check if potential_descendant_id is a descendant of ancestor_id."""
                    current = target_item
                    while current:
                        current_data = current.data(0, Qt.ItemDataRole.UserRole)
                        if current_data and current_data.get('type') == 'folder':
                            if current_data.get('id') == ancestor_id:
                                return True
                        current = current.parent()
                    return False
                
                if is_descendant(target_folder_id, dragged_folder_id):
                    print(f"[DROP BLOCKED in dropMimeData] Cannot drop folder into its own descendant")
                    return False
        
        elif dragged_type == 'request':
            # Requests can be dropped on collections or folders, but not on other requests
            if target_type == 'request' and drop_indicator == QTreeWidget.DropIndicatorPosition.OnItem:
                print(f"[DROP BLOCKED in dropMimeData] Cannot drop request on request")
                return False
        
        print(f"[DROP ALLOWED in dropMimeData]")
        # Allow the drop
        return super().dropMimeData(parent, index, data, action)
    
    def dropEvent(self, event):
        """Handle drop events to reorder items in the database."""
        # Use stored dragged item (more reliable than currentItem during drop)
        if not self._dragged_item or not self._dragged_data:
            event.ignore()
            return
        
        # Get drop position and target
        drop_position = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        target_item = self.itemAt(drop_position)
        drop_indicator = self.dropIndicatorPosition()
        
        # Get dragged and target types
        dragged_type = self._dragged_data.get('type')
        target_data = target_item.data(0, Qt.ItemDataRole.UserRole) if target_item else None
        target_type = target_data.get('type') if target_data else None
        
        print(f"[DROP EVENT] Dragged: {dragged_type}, Target: {target_type}, Indicator: {drop_indicator}")
        
        # Validation: Block invalid drops based on drop indicator position
        should_block = False
        
        # Rule 1: Cannot drop request ON another request
        if dragged_type == 'request' and target_type == 'request':
            if drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                print("[BLOCK] Cannot drop request ON another request")
                should_block = True
        
        # Rule 2: Collections can ONLY be reordered at root level
        # Block ANY drop of collection ON any item (collection must stay at root)
        if dragged_type == 'collection':
            if drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                print("[BLOCK] Cannot drop collection ON anything (must stay at root level)")
                should_block = True
            # Also block if target is not at root level or is not a collection
            if target_item is not None:
                if target_item.parent() is not None:
                    print("[BLOCK] Collections can only be reordered at root level")
                    should_block = True
                elif target_type != 'collection':
                    print("[BLOCK] Collections can only be dropped next to other collections")
                    should_block = True
        
        # Rule 3: Folders cannot be at root level
        if dragged_type == 'folder':
            # Check if dropping at root level (target_item is None or has no parent)
            if target_item is None or (target_item.parent() is None and target_type != 'collection'):
                print("[BLOCK] Folders cannot be at root level")
                should_block = True
        
        # Rule 4: Cannot move folders between collections
        if dragged_type == 'folder' and not should_block:
            # Get the collection ID of the dragged folder
            dragged_collection_id = self._dragged_data.get('collection_id')
            
            # Determine the target collection ID
            target_collection_id = None
            if target_item:
                if target_type == 'collection':
                    target_collection_id = target_data.get('id')
                elif target_type in ('folder', 'request'):
                    target_collection_id = target_data.get('collection_id')
            
            # Block if trying to move folder to a different collection
            if target_collection_id and target_collection_id != dragged_collection_id:
                print("[BLOCK] Cannot move folder between collections")
                should_block = True
        
        # Rule 5: Cannot drop folder ON request or into itself/descendants
        if dragged_type == 'folder' and target_type == 'request':
            if drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                print("[BLOCK] Cannot drop folder ON request")
                should_block = True
        
        # Rule 6: Prevent circular folder references
        if dragged_type == 'folder' and target_type == 'folder':
            if drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                dragged_folder_id = self._dragged_data.get('id')
                target_folder_id = target_data.get('id')
                
                # Check if target is the dragged folder itself
                if dragged_folder_id == target_folder_id:
                    print("[BLOCK] Cannot drop folder into itself")
                    should_block = True
                else:
                    # Check if target is a descendant of dragged folder
                    current = target_item
                    while current and not should_block:
                        current_data = current.data(0, Qt.ItemDataRole.UserRole)
                        if current_data and current_data.get('type') == 'folder':
                            if current_data.get('id') == dragged_folder_id:
                                print("[BLOCK] Cannot drop folder into its own descendant")
                                should_block = True
                                break
                        current = current.parent()
        
        if should_block:
            event.ignore()
            self._dragged_item = None
            self._dragged_data = None
            return
        
        # Store the data before Qt modifies the tree
        dragged_data = self._dragged_data
        
        # Additional validation: check if dragged item still exists and has valid parent
        dragged_type = dragged_data.get('type')
        
        # Allow Qt to handle the visual drop
        super().dropEvent(event)
        
        # Verify the item didn't disappear (check if it still exists in tree)
        if self._dragged_item and self.indexFromItem(self._dragged_item).isValid():
            # Now update the database order
            if self.main_window:
                try:
                    self.main_window._handle_tree_reorder(self._dragged_item, dragged_data)
                except Exception as e:
                    print(f"Error during reorder: {e}")
                    # Reload tree to restore correct state
                    if self.main_window:
                        self.main_window._load_collections()
        else:
            # Item disappeared - this shouldn't happen with our validation, but reload to be safe
            print("Warning: Dragged item disappeared after drop. Reloading tree...")
            if self.main_window:
                self.main_window._load_collections()
        
        # Clear stored data
        self._dragged_item = None
        self._dragged_data = None



class RequestTreeItemDelegate(QStyledItemDelegate):
    """Custom delegate to render request items with colored method badges."""
    
    def paint(self, painter, option, index):
        """Custom paint method to color the method name and make it bold."""
        from PyQt6.QtGui import QPen, QFontMetrics, QIcon, QFont
        from PyQt6.QtCore import QRect, QSize
        
        # Get the text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text or not isinstance(text, str):
            super().paint(painter, option, index)
            return
        
        # Check if this is a request item (has method like "GET ", "POST ", etc.)
        # Valid HTTP methods followed by a space
        http_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        method = None
        request_name = text
        
        for m in http_methods:
            if text.startswith(m + ' '):
                method = m
                request_name = text[len(m) + 1:]  # Everything after "METHOD "
                break
        
        if method:
            painter.save()
            
            # Get method color
            method_colors = {
                'GET': '#4EC9B0',      # Teal
                'POST': '#FF9800',     # Orange
                'PUT': '#2196F3',      # Blue
                'PATCH': '#FFC107',    # Yellow
                'DELETE': '#F44336',   # Red
                'HEAD': '#9E9E9E',     # Gray
                'OPTIONS': '#9C27B0'   # Purple
            }
            method_color = method_colors.get(method, '#FFFFFF')
            
            # Get font from item (respects bold if set)
            item_font = index.data(Qt.ItemDataRole.FontRole)
            if item_font and isinstance(item_font, QFont):
                font = item_font
            else:
                font = option.font
            
            # Create bold font for method (slightly smaller)
            bold_font = QFont(font)
            bold_font.setBold(True)
            bold_font.setPointSizeF(font.pointSizeF() * 0.92)  # 92% of normal size
            
            painter.setFont(bold_font)
            fm_bold = QFontMetrics(bold_font)
            
            painter.setFont(font)
            fm = QFontMetrics(font)
            
            # Get icon (arrow or dot for active/open requests)
            icon = index.data(Qt.ItemDataRole.DecorationRole)
            
            # Calculate text positions
            text_rect = option.rect
            x = text_rect.x() + 3  # Small left padding
            
            # Draw icon if present (arrow or dot)
            icon_width = 0
            if icon and isinstance(icon, QIcon) and not icon.isNull():
                icon_size = 16
                icon_rect = QRect(x, text_rect.y() + (text_rect.height() - icon_size) // 2, icon_size, icon_size)
                icon.paint(painter, icon_rect)
                icon_width = icon_size + 3  # Icon width + spacing
                x += icon_width
            
            # Calculate y position for text (adjust slightly for smaller method font)
            y = text_rect.y() + text_rect.height() // 2 + fm.ascent() // 2 - 1
            
            # Draw the method in bold, smaller, and colored
            painter.setFont(bold_font)
            painter.setPen(QPen(QColor(method_color)))
            painter.drawText(x, y, method)
            
            # Move x position for request name (method width + spacing)
            method_width = fm_bold.horizontalAdvance(method)
            # Add fixed spacing (6 pixels) - reduced since method is now smaller
            x += method_width + 6
            
            # Draw the request name in normal font with better visibility
            # Use stylesheet color for consistency with folders/collections
            painter.setFont(font)
            is_dark_theme = option.palette.color(QPalette.ColorRole.Window).lightness() < 128
            text_color = '#CCCCCC' if is_dark_theme else '#424242'
            painter.setPen(QPen(QColor(text_color)))
            painter.drawText(x, y, request_name)
            
            painter.restore()
        else:
            # Not a request item, use default painting
            super().paint(painter, option, index)


class RequestThread(QThread):
    """
    Thread for executing HTTP requests without blocking the UI.
    """
    finished = pyqtSignal(object)  # Emits ApiResponse
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, api_client: ApiClient, method: str, url: str, 
                 params: Dict, headers: Dict, body: str, auth_type: str, auth_token: str):
        super().__init__()
        self.api_client = api_client
        self.method = method
        self.url = url
        self.params = params
        self.headers = headers
        self.body = body
        self.auth_type = auth_type
        self.auth_token = auth_token
    
    def run(self):
        """Execute the HTTP request in a separate thread."""
        try:
            response = self.api_client.execute_request(
                method=self.method,
                url=self.url,
                params=self.params if self.params else None,
                headers=self.headers if self.headers else None,
                body=self.body if self.body else None,
                auth_type=self.auth_type,
                auth_token=self.auth_token
            )
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class NoPaddingDelegate(QStyledItemDelegate):
    """Custom delegate to remove padding from table cell editors and highlight variables."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self.var_highlighter_delegate = VariableHighlightDelegate(parent, theme)
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution."""
        self.var_highlighter_delegate.set_environment_manager(env_manager)
    
    def set_main_window(self, main_window):
        """Set the main window reference for accessing collection variables."""
        self.var_highlighter_delegate.set_main_window(main_window)
    
    def createEditor(self, parent, option, index):
        """Create editor using variable highlighting delegate."""
        return self.var_highlighter_delegate.createEditor(parent, option, index)
    
    def paint(self, painter, option, index):
        """Use variable highlighting delegate's paint method."""
        self.var_highlighter_delegate.paint(painter, option, index)
    
    def helpEvent(self, event, view, option, index):
        """Forward help events to variable highlighting delegate for tooltips."""
        return self.var_highlighter_delegate.helpEvent(event, view, option, index)
    
    def set_theme(self, theme):
        """Update theme."""
        self.theme = theme
        self.var_highlighter_delegate.set_theme(theme)




class ColoredTabBar(QTabBar):
    """Custom tab bar that renders method names with colors."""
    
    METHOD_COLORS = {
        'GET': '#4EC9B0',      # Teal
        'POST': '#FF9800',     # Orange
        'PUT': '#2196F3',      # Blue
        'PATCH': '#FFC107',    # Yellow
        'DELETE': '#F44336',   # Red
        'HEAD': '#9E9E9E',     # Gray
        'OPTIONS': '#9C27B0'   # Purple
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_data = {}  # Store method/name for each tab index
        self.setDrawBase(False)  # Don't draw the base line
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Show pointer cursor
        self.hovered_tab = -1  # Track which tab is hovered
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def set_tab_data(self, index: int, method: str, name: str, has_changes: bool = False, is_temporary: bool = False):
        """Store tab data for custom rendering."""
        self.tab_data[index] = {
            'method': method,
            'name': name,
            'has_changes': has_changes,
            'is_temporary': is_temporary
        }
        self.update()
    
    def tabSizeHint(self, index: int):
        """Calculate tab size based on content - Cursor style."""
        if index not in self.tab_data:
            # Provide a reasonable default size for tabs without data yet
            return QSize(120, 35)
        
        data = self.tab_data[index]
        method = data['method']
        name = data['name']
        has_changes = data['has_changes']
        
        # Calculate text width with proper font metrics
        fm = self.fontMetrics()
        
        # Medium-weight font for method (uppercase)
        method_upper = method.upper()
        method_width = fm.horizontalAdvance(method_upper) + 4  # Add minimal extra for medium weight
        
        space_width = 8  # Space between method and name
        name_width = fm.horizontalAdvance(name)
        changes_width = fm.horizontalAdvance(" •") if has_changes else 0
        close_btn_width = 20  # Space for close button (24px actual + small margin)
        
        # Add padding (8px left + 20px right for close button)
        total_width = 8 + method_width + space_width + name_width + changes_width + close_btn_width
        
        # Cursor-style sizing: more compact, allow natural sizing
        return QSize(min(max(total_width, 80), 300), 35)
    
    def mouseMoveEvent(self, event):
        """Track which tab is being hovered."""
        old_hovered = self.hovered_tab
        self.hovered_tab = self.tabAt(event.pos())
        
        # Update close button visibility when hover changes
        if old_hovered != self.hovered_tab:
            self._update_close_button_visibility()
        
        super().mouseMoveEvent(event)
        self.update()  # Trigger repaint for hover effects
    
    def leaveEvent(self, event):
        """Clear hover state when mouse leaves the tab bar."""
        if self.hovered_tab != -1:
            self.hovered_tab = -1
            self._update_close_button_visibility()
            self.update()
        super().leaveEvent(event)
    
    def _update_close_button_visibility(self):
        """Update close button visibility based on hover state."""
        for index in range(self.count()):
            button = self.tabButton(index, QTabBar.ButtonPosition.RightSide)
            if button:
                # Show close button only for hovered tab
                button.setVisible(index == self.hovered_tab)
    
    def _show_context_menu(self, pos):
        """Show context menu for tab operations."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QCursor, QAction
        
        # Get the tab index at the click position
        tab_index = self.tabAt(pos)
        if tab_index == -1:
            return  # No tab at this position
        
        # Walk up the parent chain to find the MainWindow
        main_window = self.parent()
        while main_window and not isinstance(main_window, MainWindow):
            main_window = main_window.parent()
        
        if not main_window:
            return
        
        # Get tab state
        tab_state = main_window.tab_states.get(tab_index, {})
        request_id = tab_state.get('request_id')
        
        # Create context menu
        menu = QMenu(self)
        
        # Add New Request
        new_request_action = menu.addAction("➕ New Request")
        
        # Duplicate Request (only if request is saved)
        duplicate_action = None
        if request_id:
            duplicate_action = menu.addAction("📋 Duplicate Request")
        
        menu.addSeparator()
        
        # Pin/Unpin Request (only if request is saved/persisted)
        pin_action = None
        unpin_action = None
        if request_id and not tab_state.get('is_temporary', False):
            # Check if request is already pinned
            is_pinned = main_window._is_request_pinned(request_id)
            if is_pinned:
                unpin_action = menu.addAction("📍 Unpin Request")
            else:
                pin_action = menu.addAction("📌 Pin Request")
            menu.addSeparator()
        
        # Close operations
        close_others_action = menu.addAction("Close All But This")
        
        # Close tabs on the left (only if there are tabs on the left)
        close_left_action = None
        if tab_index > 0:
            close_left_action = menu.addAction("Close All to the Left")
        
        # Close tabs on the right (only if there are tabs on the right)
        close_right_action = None
        if tab_index < self.count() - 1:
            close_right_action = menu.addAction("Close All to the Right")
        
        close_all_action = menu.addAction("Close All")
        
        # Show menu and get selected action
        action = menu.exec(QCursor.pos())
        
        # Handle the selected action
        if action == new_request_action:
            main_window._create_new_request()
        elif action == duplicate_action:
            main_window._duplicate_request_to_temp_tab(request_id)
        elif action == pin_action:
            main_window._pin_request_from_tab(request_id)
        elif action == unpin_action:
            main_window._unpin_request_from_tab(request_id)
        elif action == close_others_action:
            main_window._close_all_tabs_except(tab_index)
        elif action == close_left_action:
            main_window._close_tabs_on_left(tab_index)
        elif action == close_right_action:
            main_window._close_tabs_on_right(tab_index)
        elif action == close_all_action:
            main_window._close_all_tabs()
    
    def tabInserted(self, index: int):
        """Called when a tab is inserted - hide close button initially."""
        super().tabInserted(index)
        # Hide close button by default for newly inserted tabs
        self._update_close_button_visibility()
    
    def paintEvent(self, event):
        """Custom paint event to draw colored method names."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for index in range(self.count()):
            if index not in self.tab_data:
                continue
            
            data = self.tab_data[index]
            method = data['method']
            name = data['name']
            has_changes = data['has_changes']
            is_temporary = data.get('is_temporary', False)
            
            # Get tab rect
            rect = self.tabRect(index)
            is_selected = (index == self.currentIndex())
            is_hovered = rect.contains(self.mapFromGlobal(self.cursor().pos()))
            is_dark_theme = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
            
            # Draw background - Cursor style
            if is_selected:
                # Selected tab matches content area
                painter.fillRect(rect, QColor('#1E1E1E' if is_dark_theme else '#FFFFFF'))
            # No hover background - only text color changes (handled below)
            
            # Draw subtle vertical separator (right border) - gray color
            separator_color = QColor('#3F3F3F' if is_dark_theme else '#D0D0D0')
            painter.setPen(QPen(separator_color, 1))
            painter.drawLine(rect.topRight().x(), rect.top(), rect.bottomRight().x(), rect.bottom())
            
            # Draw bottom border (underline) for selected tab - Cursor blue
            if is_selected:
                painter.setPen(QPen(QColor('#007ACC'), 2))
                painter.drawLine(rect.bottomLeft().x(), rect.bottom() - 1, 
                               rect.bottomRight().x(), rect.bottom() - 1)
            
            # Start position for text (with some padding)
            x = rect.x() + 8  # Reduced left padding for more text space
            y = rect.center().y() + 5  # Center vertically
            
            # Draw method with color (uppercase)
            method_upper = method.upper()
            method_color = QColor(self.METHOD_COLORS.get(method, '#FFFFFF'))
            painter.setPen(QPen(method_color))
            font = painter.font()
            font.setWeight(QFont.Weight.Medium)  # Medium weight instead of bold - VS Code style
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(x, y, method_upper)
            
            # Calculate width of method text
            method_width = painter.fontMetrics().horizontalAdvance(method_upper)
            x += method_width
            
            # Add 8px space between method and name (no bullet separator)
            x += 8
            
            # Draw name (truncate if needed)
            # Reset to regular weight for name text
            font.setWeight(QFont.Weight.Normal)
            # Set italic font for temporary tabs
            if is_temporary:
                font.setItalic(True)
            painter.setFont(font)
            
            max_name_width = rect.width() - (x - rect.x()) - 20  # Optimized space for close button
            name_display = name
            name_width = painter.fontMetrics().horizontalAdvance(name)
            
            if name_width > max_name_width:
                # Truncate with ellipsis
                while name_width > max_name_width - painter.fontMetrics().horizontalAdvance("...") and len(name_display) > 0:
                    name_display = name_display[:-1]
                    name_width = painter.fontMetrics().horizontalAdvance(name_display)
                name_display += "..."
            
            # Apply text hierarchy - Cursor style (more contrast)
            if is_selected:
                painter.setPen(QPen(QColor('#FFFFFF' if is_dark_theme else '#212121')))  # High contrast for selected
            elif is_hovered:
                painter.setPen(QPen(QColor('#CCCCCC' if is_dark_theme else '#212121')))  # Brighter on hover
            else:
                painter.setPen(QPen(QColor('#969696' if is_dark_theme else '#616161')))  # Muted for inactive
            
            painter.drawText(x, y, name_display)
            
            # Reset italic font for next tab
            if is_temporary:
                font.setItalic(False)
                painter.setFont(font)
            x += painter.fontMetrics().horizontalAdvance(name_display) + 6
            
            # Draw unsaved indicator
            if has_changes:
                painter.drawText(x, y, "•")


class MainWindow(QMainWindow):
    """
    Main application window with collections tree, request editor, and response viewer.
    """
    
    def __init__(self, db_path: str = "api_client.db", theme: str = 'dark'):
        super().__init__()
        
        # Initialize database and API client
        self.db = DatabaseManager(db_path=db_path)
        self.api_client = ApiClient()
        
        # Initialize script engine
        self.script_engine = ScriptEngine(timeout_ms=5000)
        
        # Initialize security scanner
        self.security_scanner = SecurityScanner()
        self.security_report_generator = SecurityReportGenerator(self.db)
        
        # Initialize environment manager with database reference for variable persistence
        self.env_manager = EnvironmentManager(db=self.db)
        
        # Initialize import/export
        self.exporter = CollectionExporter(self.db)
        self.importer = CollectionImporter(self.db)
        
        # Initialize Git sync
        self.git_sync_manager = None
        self.secrets_manager = None
        self.git_workspace = None
        
        # Git sync status refresh timer
        from PyQt6.QtCore import QTimer
        self.git_sync_timer = QTimer()
        self.git_sync_timer.timeout.connect(self._update_git_sync_status)
        self.git_sync_timer.setInterval(30000)  # Refresh every 30 seconds
        
        # Theme management
        self.current_theme = theme  # Initialize with provided theme
        
        # Track current selection
        self.current_collection_id = None
        self.current_request_id = None
        self.current_request_name = None
        self.current_collection_name = None
        self.current_folder_id = None  # Track current folder
        self._current_description = ""  # Track current request description (popup-based)
        
        # Track unsaved changes
        self.has_unsaved_changes = False
        self.original_request_data = {}
        
        # URL-Params sync flag (prevent infinite loop)
        self._syncing_params = False
        
        # Track active threads
        self.request_thread = None
        self.update_checker_thread = None
        self.update_downloader_thread = None
        
        # UI state tracking
        self.response_panel_collapsed = False
        
        # Search tracking
        self.search_matches = []
        self.current_match_index = -1
        
        # Setup UI
        self.setWindowTitle("PostMini - Desktop API Client")
        self.setGeometry(100, 100, 1400, 750)  # Reduced height for better fit on 1920x1080 screens
        
        self._init_ui()
        
        # Connect environment manager to URL input for variable highlighting
        self.url_input.set_environment_manager(self.env_manager)
        self.url_input.set_main_window(self)  # Set main window for collection variable resolution
        
        # Connect environment manager to table delegates for variable tooltips
        if hasattr(self, 'params_table') and hasattr(self.params_table, '_custom_delegate'):
            self.params_table._custom_delegate.set_environment_manager(self.env_manager)
            self.params_table._custom_delegate.set_main_window(self)
        if hasattr(self, 'headers_table') and hasattr(self.headers_table, '_custom_delegate'):
            self.headers_table._custom_delegate.set_environment_manager(self.env_manager)
            self.headers_table._custom_delegate.set_main_window(self)
        
        # Connect environment manager to test tab for variable highlighting in test fields
        if hasattr(self, 'test_tab'):
            self.test_tab.set_environment_manager(self.env_manager)
            self.test_tab.set_main_window(self)
        
        self._setup_shortcuts()
        self._load_collections()
        self._load_environments()
        self._load_extracted_variables()  # Load extracted variables into env_manager
        self._init_git_sync()
        
        # Initialize button styles for current theme (must be after UI is created)
        self._update_collection_header_button_styles()
        self._update_tab_bar_button_styles()
        self._update_save_button_style()
        self._update_env_combo_style()
        self._update_response_buttons_style()
        
        # Initialize method combo styling
        self._update_method_style('GET')
        
        # Use QTimer to set splitter sizes AFTER the window is shown
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._fix_splitter_sizes)
        
        # Check for updates on startup (after 5 seconds) if enabled
        if self.settings_pane.should_auto_check_updates():
            QTimer.singleShot(5000, lambda: self._check_for_updates(silent=True))
    
    def _fix_splitter_sizes(self):
        """Fix splitter sizes after window is shown."""
        print(f"[DEBUG] _fix_splitter_sizes called after window shown")
        if hasattr(self, 'main_splitter'):
            self.main_splitter.setSizes([400, 0, 0, 0, 0, 1000])
            actual = self.main_splitter.sizes()
            print(f"[DEBUG] Splitter sizes fixed to: [400, 0, 0, 0, 0, 1000]")
            print(f"[DEBUG] Actual sizes after fix: {actual}")
    
    def _get_icon_path(self, icon_name: str) -> str:
        """
        Get the full path to an icon file.
        
        Args:
            icon_name: Name of the icon file (e.g., 'collection-icon.svg')
            
        Returns:
            Full path to the icon file
        """
        resources_dir = AppPaths.get_resources_dir()
        icon_path = resources_dir / "assets" / "icons" / icon_name
        return str(icon_path)
    
    def _init_ui(self):
        """Initialize the user interface with all components."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ==================== VERTICAL ICON BAR (LEFT EDGE) ====================
        icon_bar = QWidget()
        icon_bar.setObjectName("leftIconBar")
        icon_bar.setFixedWidth(50)
        icon_bar_layout = QVBoxLayout(icon_bar)
        icon_bar_layout.setContentsMargins(0, 0, 0, 0)
        icon_bar_layout.setSpacing(0)
        
        # Collections toggle button
        self.collections_toggle_btn = QPushButton("📁")
        self.collections_toggle_btn.setToolTip("Collections [Alt+C]")
        self.collections_toggle_btn.setCheckable(True)
        self.collections_toggle_btn.setChecked(True)  # Visible by default
        self.collections_toggle_btn.setFixedSize(50, 50)
        self.collections_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
                font-size: 24px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background: rgba(33, 150, 243, 0.15);
                border-left: 3px solid #2196F3;
            }
        """)
        self.collections_toggle_btn.clicked.connect(lambda: self._switch_left_panel('collections'))
        icon_bar_layout.addWidget(self.collections_toggle_btn)
        
        # Git Sync toggle button
        self.git_sync_toggle_btn = QPushButton("🔄")
        self.git_sync_toggle_btn.setToolTip("Git Sync [Alt+G]")
        self.git_sync_toggle_btn.setCheckable(True)
        self.git_sync_toggle_btn.setChecked(False)
        self.git_sync_toggle_btn.setFixedSize(50, 50)
        self.git_sync_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
                font-size: 24px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background: rgba(33, 150, 243, 0.15);
                border-left: 3px solid #2196F3;
            }
        """)
        self.git_sync_toggle_btn.clicked.connect(lambda: self._switch_left_panel('git_sync'))
        icon_bar_layout.addWidget(self.git_sync_toggle_btn)
        
        # Variable Inspector toggle button
        self.variable_inspector_toggle_btn = QPushButton("{{}}")
        self.variable_inspector_toggle_btn.setToolTip("Variables [Alt+V]")
        self.variable_inspector_toggle_btn.setCheckable(True)
        self.variable_inspector_toggle_btn.setChecked(False)
        self.variable_inspector_toggle_btn.setFixedSize(50, 50)
        self.variable_inspector_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background: rgba(33, 150, 243, 0.15);
                border-left: 3px solid #2196F3;
            }
        """)
        self.variable_inspector_toggle_btn.clicked.connect(lambda: self._switch_left_panel('variable_inspector'))
        icon_bar_layout.addWidget(self.variable_inspector_toggle_btn)
        
        # Environments toggle button
        self.environments_toggle_btn = QPushButton("🌍")
        self.environments_toggle_btn.setToolTip("Environments [Alt+E]")
        self.environments_toggle_btn.setCheckable(True)
        self.environments_toggle_btn.setChecked(False)
        self.environments_toggle_btn.setFixedSize(50, 50)
        self.environments_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
                font-size: 24px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background: rgba(33, 150, 243, 0.15);
                border-left: 3px solid #2196F3;
            }
        """)
        self.environments_toggle_btn.clicked.connect(lambda: self._switch_left_panel('environments'))
        icon_bar_layout.addWidget(self.environments_toggle_btn)
        
        # History button (toggle history panel)
        self.history_btn = QPushButton("📋")
        self.history_btn.setToolTip("Request History [Alt+H]")
        self.history_btn.setCheckable(True)
        self.history_btn.setChecked(False)
        self.history_btn.setFixedSize(50, 50)
        self.history_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
                font-size: 24px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background: rgba(33, 150, 243, 0.15);
                border-left: 3px solid #2196F3;
            }
        """)
        self.history_btn.clicked.connect(self._toggle_history_panel)
        icon_bar_layout.addWidget(self.history_btn)
        
        icon_bar_layout.addStretch()  # Push buttons to top
        
        # Settings toggle button (at bottom)
        self.settings_toggle_btn = QPushButton("⚙️")
        self.settings_toggle_btn.setToolTip("Settings")
        self.settings_toggle_btn.setCheckable(True)
        self.settings_toggle_btn.setChecked(False)
        self.settings_toggle_btn.setFixedSize(50, 50)
        self.settings_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
                font-size: 24px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background: rgba(33, 150, 243, 0.15);
                border-left: 3px solid #2196F3;
            }
        """)
        self.settings_toggle_btn.clicked.connect(lambda: self._switch_left_panel('settings'))
        icon_bar_layout.addWidget(self.settings_toggle_btn)
        
        main_layout.addWidget(icon_bar)
        
        # Create main splitter (left pane | center pane | right pane)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(1)  # Thin splitter handle
        
        # ==================== LEFT PANE: Collections ====================
        self.collections_pane = self._create_collections_pane()
        main_splitter.addWidget(self.collections_pane)
        
        # ==================== LEFT PANE: Settings ====================
        self.settings_pane = SettingsPanel(self.db)
        self.settings_pane.setVisible(False)  # Hidden by default
        self.settings_pane.check_updates_requested.connect(self._check_for_updates)
        main_splitter.addWidget(self.settings_pane)
        
        # ==================== LEFT PANE: Git Sync ====================
        self.git_sync_pane = GitSyncPanel(self.db, self)
        self.git_sync_pane.setVisible(False)  # Hidden by default
        main_splitter.addWidget(self.git_sync_pane)
        
        # Connect Git sync panel signals
        self.git_sync_pane.sync_enabled.connect(self._on_git_sync_enabled)
        self.git_sync_pane.sync_disabled.connect(self._on_git_sync_disabled)
        self.git_sync_pane.sync_performed.connect(self._on_sync_performed)
        
        # ==================== LEFT PANE: Variable Inspector ====================
        self.variable_inspector_pane = VariableInspectorPanel(self)
        self.variable_inspector_pane.setVisible(False)  # Hidden by default
        self.variable_inspector_pane.db = self.db  # Set database reference
        self.variable_inspector_pane.set_db_manager(self.db)  # Set database manager for secret tracking
        self.variable_inspector_pane.set_theme(self.current_theme)  # Set initial theme
        main_splitter.addWidget(self.variable_inspector_pane)
        
        # Connect variable inspector panel signals
        print(f"[DEBUG] About to connect variable inspector signals")
        self.variable_inspector_pane.refresh_requested.connect(self._refresh_variable_inspector_panel)
        print(f"[DEBUG] refresh_requested connected")
        self.variable_inspector_pane.variable_edited.connect(self._on_variable_edited)
        print(f"[DEBUG] variable_edited connected")
        
        # Connect variable_deleted signal
        print(f"[DEBUG] Attempting to connect variable_deleted signal...")
        print(f"[DEBUG] Signal signature: variable_deleted(str, str)")
        print(f"[DEBUG] Handler signature: _on_variable_deleted(scope: str, name: str)")
        
        # Try using lambda to ensure proper connection
        self.variable_inspector_pane.variable_deleted.connect(
            lambda scope, name: self._handle_variable_deleted(scope, name)
        )
        print(f"[DEBUG] variable_deleted connected via lambda wrapper")
        
        # Test the connection immediately (status bar is now available)
        print(f"[DEBUG] Testing connection by emitting test signal")
        self.variable_inspector_pane.variable_deleted.emit("test_scope", "test_name")
        print(f"[DEBUG] Test signal emitted")
        
        self.variable_inspector_pane.variable_added.connect(self._on_variable_added)
        print(f"[DEBUG] variable_added connected")
        self.variable_inspector_pane.collection_variable_added.connect(self._on_collection_variable_added)
        print(f"[DEBUG] collection_variable_added connected")
        
        # Connect variable changes to update environments panel variable counts
        self.variable_inspector_pane.variable_added.connect(self._update_environments_var_counts)
        self.variable_inspector_pane.collection_variable_added.connect(lambda c, n, v: self._update_environments_var_counts())
        self.variable_inspector_pane.variable_edited.connect(lambda s, n, v: self._update_environments_var_counts())
        self.variable_inspector_pane.variable_deleted.connect(lambda s, n: self._update_environments_var_counts())
        print(f"[DEBUG] Variable inspector signals connected to environments panel updates")
        
        print(f"[DEBUG] Variable inspector signals connected successfully")
        
        # ==================== LEFT PANE: Environments ====================
        self.environments_pane = EnvironmentsPanel(self.db, self)
        self.environments_pane.setVisible(False)  # Hidden by default
        self.environments_pane.set_theme(self.current_theme)  # Set initial theme
        main_splitter.addWidget(self.environments_pane)
        
        # Connect environment panel signals
        self.environments_pane.environment_created.connect(self._on_environment_changed_refresh)
        self.environments_pane.environment_deleted.connect(self._on_environment_changed_refresh)
        self.environments_pane.environment_updated.connect(self._on_environment_changed_refresh)
        
        # Track current left panel
        self.current_left_panel = 'collections'
        
        # ==================== CENTER PANE: Request Editor & Response ====================
        # Create a container for the entire center area
        center_container = QWidget()
        center_container_layout = QVBoxLayout(center_container)
        center_container_layout.setContentsMargins(0, 0, 0, 0)
        center_container_layout.setSpacing(0)
        
        # Create horizontal container for tab bar + recent button (always visible)
        tab_bar_container = QWidget()
        tab_bar_container.setMaximumHeight(35)  # Restored for proper button display
        tab_bar_container.setMinimumHeight(35)
        tab_bar_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tab_bar_layout = QHBoxLayout(tab_bar_container)
        tab_bar_layout.setContentsMargins(0, 0, 0, 0)
        tab_bar_layout.setSpacing(0)
        
        # Tab bar for multiple requests
        self.request_tabs = QTabWidget()
        self.request_tabs.setTabBar(ColoredTabBar())  # Use custom tab bar
        self.request_tabs.setTabsClosable(True)
        self.request_tabs.setMovable(True)
        self.request_tabs.setDocumentMode(True)
        self.request_tabs.tabCloseRequested.connect(self._close_tab)
        self.request_tabs.currentChanged.connect(self._on_tab_changed)
        self.request_tabs.setMaximumHeight(35)  # Restored for proper button display
        self.request_tabs.setObjectName("requestTabs")  # For specific styling
        tab_bar_layout.addWidget(self.request_tabs)
        
        # Add New Request button - independent of tabs, always visible
        self.new_request_btn = QPushButton("➕")
        self.new_request_btn.setToolTip("Create new request (Ctrl+N)")
        self.new_request_btn.setFixedHeight(35)  # Match tab bar height
        self.new_request_btn.setFixedWidth(40)
        self.new_request_btn.clicked.connect(self._create_new_request)
        tab_bar_layout.addWidget(self.new_request_btn)
        
        # Add Recent button - independent of tabs, always visible
        self.recent_requests_btn = QPushButton("Recent")
        self.recent_requests_btn.setToolTip("Recent [Alt+R]")
        self.recent_requests_btn.setCheckable(True)
        self.recent_requests_btn.setFixedHeight(35)  # Match tab bar height
        self.recent_requests_btn.setMinimumWidth(70)
        self.recent_requests_btn.clicked.connect(self._toggle_recent_requests)
        tab_bar_layout.addWidget(self.recent_requests_btn)
        
        # Apply initial theme to these buttons
        self._update_tab_bar_button_styles()
        
        # Add tab bar container to the top of center area (always visible, fixed height)
        center_container_layout.addWidget(tab_bar_container, 0)  # Stretch factor 0 = fixed height
        
        # Install event filter on tab bar for middle-click detection
        self.request_tabs.tabBar().installEventFilter(self)
        
        # Use stacked widget to show empty state or workspace (below the tab bar)
        from PyQt6.QtWidgets import QStackedWidget
        self.center_stack = QStackedWidget()
        
        # Empty state for no request selected
        self.no_request_empty_state = NoRequestEmptyState()
        self.center_stack.addWidget(self.no_request_empty_state)
        
        # Create container for workspace only
        tabs_container = QWidget()
        tabs_layout = QVBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(0)
        
        # Hide the tab widget content area (we'll show workspace below)
        # No inline style - will use stylesheet
        
        # Tab state storage: {tab_index: {request_id, ui_state, has_changes, is_temporary}}
        self.tab_states = {}
        self.next_untitled_num = 1
        self.previous_tab_index = None  # Track previous tab for state saving
        self._last_double_click_time = 0  # Track last double-click to prevent duplicates
        self._last_double_click_request_id = None
        self._last_single_click_time = 0  # Track last single-click to prevent duplicates
        self._last_single_click_request_id = None
        self.temporary_tab_index = None  # Track the current temporary tab (only one can exist)
        
        # Don't create any initial tab - start with empty state
        # Tabs will be created when user opens a request
        
        # Actual workspace pane (shared, state is captured/restored)
        self.workspace_pane = self._create_workspace_pane()
        
        # Add workspace to tabs container (not the tab bar)
        tabs_layout.addWidget(self.workspace_pane)
        
        # Store reference for easy access
        self.tabs_container = tabs_container
        self.center_stack.addWidget(tabs_container)
        
        # Add the stacked widget to the center container (below the tab bar)
        center_container_layout.addWidget(self.center_stack)
        
        # Show empty state by default
        print(f"[DEBUG] Setting empty state as current widget during init")
        print(f"[DEBUG] center_stack widget count: {self.center_stack.count()}")
        print(f"[DEBUG] Widget 0 (empty state): {self.center_stack.widget(0)}")
        print(f"[DEBUG] Widget 1 (tabs container): {self.center_stack.widget(1)}")
        
        # Use setCurrentIndex to ensure empty state (index 0) is shown
        self.center_stack.setCurrentIndex(0)
        print(f"[DEBUG] Current index after setting: {self.center_stack.currentIndex()}")
        print(f"[DEBUG] Current widget: {self.center_stack.currentWidget()}")
        print(f"[DEBUG] Request tabs count: {self.request_tabs.count()}")
        
        # Add center container to main splitter
        main_splitter.addWidget(center_container)
        
        # ==================== RIGHT PANE: Recent Requests (OVERLAY) ====================
        # Create the recent requests widget as an overlay on top of center_container
        # instead of adding it to the splitter
        self.recent_requests_widget = RecentRequestsWidget(self.db)
        self.recent_requests_widget.request_selected.connect(self._load_request_persistent)  # Single click - persistent tab
        self.recent_requests_widget.close_btn.clicked.connect(self._toggle_recent_requests)  # Connect close button
        
        # Set parent to center_container to make it an overlay
        self.recent_requests_widget.setParent(center_container)
        self.recent_requests_widget.setVisible(False)  # Hidden by default
        
        # Raise the widget to ensure it's on top
        self.recent_requests_widget.raise_()
        
        # Apply styling for overlay appearance with shadow effect
        self.recent_requests_widget.setStyleSheet("""
            RecentRequestsWidget {
                background: #1E1E1E;
                border-left: 2px solid rgba(33, 150, 243, 0.3);
                border-radius: 0px;
            }
        """)
        
        # Add a drop shadow effect for better visual separation
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(-3, 0)
        self.recent_requests_widget.setGraphicsEffect(shadow)
        
        # ==================== RIGHT PANE: History Panel (OVERLAY) ====================
        # Create the history panel widget as an overlay on top of center_container
        self.history_panel_widget = HistoryPanelWidget(self.db)
        self.history_panel_widget.replay_requested.connect(self._replay_from_history)
        self.history_panel_widget.close_btn.clicked.connect(self._toggle_history_panel)  # Connect close button
        
        # Set parent to center_container to make it an overlay
        self.history_panel_widget.setParent(center_container)
        self.history_panel_widget.setVisible(False)  # Hidden by default
        
        # Raise the widget to ensure it's on top
        self.history_panel_widget.raise_()
        
        # Apply styling for overlay appearance with shadow effect
        self.history_panel_widget.setStyleSheet("""
            HistoryPanelWidget {
                background: #1E1E1E;
                border-left: 2px solid rgba(33, 150, 243, 0.3);
                border-radius: 0px;
            }
        """)
        
        # Add a drop shadow effect for better visual separation
        history_shadow = QGraphicsDropShadowEffect()
        history_shadow.setBlurRadius(20)
        history_shadow.setColor(QColor(0, 0, 0, 180))
        history_shadow.setOffset(-3, 0)
        self.history_panel_widget.setGraphicsEffect(history_shadow)
        
        # Set splitter sizes for ALL widgets (including hidden ones)
        # Splitter now has 7 widgets: collections(0), settings(1), git(2), variables(3), environments(4), security(5), center(6)
        # Set size to 0 for hidden widgets, proper sizes for visible ones
        print(f"[DEBUG] main_splitter widget count: {main_splitter.count()}")
        for i in range(main_splitter.count()):
            widget = main_splitter.widget(i)
            print(f"[DEBUG] Splitter widget {i}: {widget.__class__.__name__}, visible: {widget.isVisibleTo(main_splitter)}")
        
        # Store reference to main splitter for later size adjustment
        self.main_splitter = main_splitter
        
        # Store reference to center_container for overlay positioning
        self.center_container = center_container
        
        # Set initial sizes (Qt may adjust these until window is shown)
        # Now 6 widgets: collections(0), settings(1), git(2), variables(3), environments(4), center(5)
        main_splitter.setSizes([400, 0, 0, 0, 0, 1000])
        actual_sizes = main_splitter.sizes()
        print(f"[DEBUG] Splitter sizes set to: [400, 0, 0, 0, 0, 1000]")
        print(f"[DEBUG] Actual splitter sizes after set: {actual_sizes}")
        
        main_layout.addWidget(main_splitter)
        
        # Create status bar
        self._create_status_bar()
        
        # Connect environment change to auto-refresh variables panel (after status bar creation)
        self.env_combo.currentIndexChanged.connect(self._on_env_change_refresh_vars)
    
    def _create_status_bar(self):
        """Create the bottom status bar with save status and Git sync info."""
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background: rgba(255, 255, 255, 0.03);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                color: #999;
                font-size: 11px;
            }
            QStatusBar QLabel {
                color: #999;
                font-size: 11px;
            }
            QStatusBar::item {
                border: none;
            }
        """)
        
        # Save status widget
        self.save_status_label = QLabel("Ready")
        self.save_status_label.setStyleSheet("padding: 0 12px; color: #2196F3;")
        status_bar.addWidget(self.save_status_label)
        
        # Git sync status indicator
        self.git_sync_status_label = QLabel("Git: Not Enabled")
        self.git_sync_status_label.setStyleSheet("padding: 0 12px; color: #999;")
        status_bar.addWidget(self.git_sync_status_label)
        
        # Environment label and selector
        env_label = QLabel("Environment:")
        env_label.setStyleSheet("padding: 0 8px 0 12px; color: #999;")
        status_bar.addWidget(env_label)
        
        self.env_combo = QComboBox()
        self.env_combo.setMinimumWidth(150)
        self.env_combo.setMaximumHeight(22)
        self.env_combo.addItem("No Environment", None)
        self.env_combo.currentIndexChanged.connect(self._on_environment_changed)
        status_bar.addWidget(self.env_combo)
        
        # Apply initial theme to environment combo
        self._update_env_combo_style()
        
        # Add spacer - use addPermanentWidget with empty label to push right side
        spacer_label = QLabel()
        spacer_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        status_bar.addWidget(spacer_label)
        
        # Theme toggle button (on the right side, before help hint)
        self.theme_toggle_btn = QPushButton()
        self.theme_toggle_btn.setFixedSize(28, 22)
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)
        self.theme_toggle_btn.setToolTip("Toggle light/dark theme")
        self._update_theme_button()
        status_bar.addPermanentWidget(self.theme_toggle_btn)
        
        # Help hint (on the right side)
        help_hint = QLabel("💡 Ctrl+/ for shortcuts")
        help_hint.setStyleSheet("color: #2196F3; font-size: 11px; padding: 0 12px;")
        help_hint.setToolTip("Show keyboard shortcuts help")
        status_bar.addPermanentWidget(help_hint)
        
        # Set initial icon bar hover colors based on current theme
        self._update_icon_bar_hover_colors()
    
    def _update_save_status(self, message: str, duration: int = 3000):
        """Update the status bar with a save status message."""
        self.save_status_label.setText(message)
        if duration > 0:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(duration, lambda: self.save_status_label.setText("Ready"))
    
    def _show_status(self, message: str, status_type: str = "info", duration: int = 5000):
        """
        Show a status message in the status bar with appropriate color coding.
        
        Args:
            message: The message to display
            status_type: Type of message - "success", "error", "warning", or "info"
            duration: How long to show the message (milliseconds), 0 for permanent
        """
        # Color mapping matching toast notification colors
        colors = {
            "success": "#4CAF50",  # Green
            "error": "#F44336",    # Red
            "warning": "#FF9800",  # Orange
            "info": "#2196F3"      # Blue
        }
        
        color = colors.get(status_type, colors["info"])
        self.save_status_label.setStyleSheet(f"padding: 0 12px; color: {color}; font-weight: 500;")
        self.save_status_label.setText(message)
        
        if duration > 0:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(duration, lambda: self._reset_status())
    
    def _reset_status(self):
        """Reset status bar to default state."""
        self.save_status_label.setStyleSheet("padding: 0 12px; color: #2196F3;")
        self.save_status_label.setText("Ready")
    
    def _update_status_bar(self):
        """Update status bar with current state."""
        # Update Git sync status - consolidate into single label
        if self.git_workspace:
            self.git_sync_status_label.setText(f"📁 Git: {self.git_workspace['name']}")
        else:
            self.git_sync_status_label.setText("Git: Not Enabled")
    
    def resizeEvent(self, event):
        """Handle window resize to reposition the overlay panel."""
        super().resizeEvent(event)
        
        # Reposition the recent requests overlay if it's visible
        if hasattr(self, 'recent_requests_widget') and self.recent_requests_widget.isVisible():
            container_width = self.center_container.width()
            overlay_width = 350
            
            self.recent_requests_widget.setGeometry(
                container_width - overlay_width,
                0,
                overlay_width,
                self.center_container.height()
            )
    
    # ==================== TAB MANAGEMENT ====================
    
    def _find_tab_with_request(self, request_id: int) -> int:
        """Find if a request is already open in a tab. Returns tab index or -1 if not found."""
        for tab_idx, state in self.tab_states.items():
            if state.get('request_id') == request_id:
                return tab_idx
        return -1
    
    def _capture_current_tab_state(self) -> Dict:
        """Capture the current UI state for saving to a tab."""
        # Capture response data if available
        response_data = None
        if hasattr(self, 'current_response') and self.current_response:
            try:
                response_data = {
                    'status_code': self.current_response.status_code if hasattr(self.current_response, 'status_code') else 0,
                    'headers': self.current_response.headers if hasattr(self.current_response, 'headers') else {},
                    'text': self.current_response.text if hasattr(self.current_response, 'text') else '',
                    'size': self.current_response.size if hasattr(self.current_response, 'size') else 0,
                    'elapsed_time': self.current_response.elapsed_time if hasattr(self.current_response, 'elapsed_time') else 0
                }
            except AttributeError as e:
                print(f"[ERROR] Could not capture response data: {e}")
                response_data = None
            if response_data:
                print(f"[DEBUG] Captured response: status={response_data['status_code']}, size={response_data['size']}")
        
        # Capture test results if available
        test_results_data = None
        if hasattr(self, 'test_results_viewer') and self.test_results_viewer is not None:
            # Check if test results are visible (meaning tests have been run)
            if self.test_results_viewer.isVisible():
                # We need to store the data that was passed to display_results()
                # This is stored when tests are run
                test_results_data = getattr(self, '_current_test_results', None)
                if test_results_data:
                    print(f"[DEBUG] Captured test results: {test_results_data.get('summary', {})}")
        
        # Capture script content (pre-request and post-response scripts)
        scripts_data = None
        if hasattr(self, 'scripts_tab') and self.scripts_tab is not None:
            scripts_data = {
                'pre_request_script': self.scripts_tab.get_pre_request_script(),
                'post_response_script': self.scripts_tab.get_post_response_script()
            }
            print(f"[DEBUG] Captured scripts: pre={len(scripts_data['pre_request_script'])} chars, post={len(scripts_data['post_response_script'])} chars")
        
        # Capture test assertions (from the Tests tab)
        test_assertions_data = None
        if hasattr(self, 'test_tab') and self.test_tab is not None:
            test_assertions_data = self.test_tab.get_assertions()
            print(f"[DEBUG] Captured test assertions: {len(test_assertions_data)} assertions")
        
        # Capture UI state: active tabs and view modes
        ui_preferences = {
            'active_inner_tab': self.inner_tabs.currentIndex() if hasattr(self, 'inner_tabs') else 0,
            'active_response_tab': self.response_tabs.currentIndex() if hasattr(self, 'response_tabs') else 0,
            'response_view_mode': 'pretty' if self.is_pretty_mode else 'raw'
            # Removed description_visible - description now accessed via popup button
        }
        print(f"[DEBUG] Captured UI preferences: inner_tab={ui_preferences['active_inner_tab']}, response_tab={ui_preferences['active_response_tab']}, view_mode={ui_preferences['response_view_mode']}")
        
        return {
            'request_id': self.current_request_id,
            'collection_id': self.current_collection_id,
            'method': self.method_combo.currentText(),
            'url': self.url_input.text(),
            'params': self._get_table_as_dict(self.params_table),
            'headers': self._get_table_as_dict(self.headers_table),
            'body': self.body_input.toPlainText(),
            'body_type': self.body_type_combo.currentText(),
            'auth_type': self.auth_type_combo.currentText(),
            'auth_token': self.auth_token_input.text(),
            'description': self._current_description,  # Use string instead of widget
            'request_name': self.current_request_name or 'Untitled',
            'has_changes': self.has_unsaved_changes,
            'response': response_data,  # Response data
            'test_results': test_results_data,  # Test results from execution
            'scripts': scripts_data,  # Script content
            'test_assertions': test_assertions_data,  # Test assertions (editor content)
            'ui_preferences': ui_preferences  # UI state (active tabs, view modes)
        }
    
    def _restore_tab_state(self, state: Dict):
        """Restore UI state from a tab's saved state."""
        print(f"[DEBUG] Restoring tab state for request_id={state.get('request_id')}")
        
        # Block all signals during restoration to prevent marking as modified
        self.method_combo.blockSignals(True)
        self.url_input.blockSignals(True)
        self.params_table.blockSignals(True)
        self.headers_table.blockSignals(True)
        self.body_input.blockSignals(True)
        self.body_type_combo.blockSignals(True)
        self.auth_type_combo.blockSignals(True)
        self.auth_token_input.blockSignals(True)
        # description_input removed - now using _current_description string
        self.test_tab.blockSignals(True)
        self.scripts_tab.blockSignals(True)
        
        try:
            # Load basic info
            self.current_request_id = state.get('request_id')
            self.current_collection_id = state.get('collection_id')
            self.current_request_name = state.get('request_name', 'Untitled')
            
            self.method_combo.setCurrentText(state.get('method', 'GET'))
            self._update_method_style(state.get('method', 'GET'))
            self.url_input.setText(state.get('url', ''))
            
            # Load params
            self._load_dict_to_table(state.get('params', {}), self.params_table)
            
            # Load headers
            self._load_dict_to_table(state.get('headers', {}), self.headers_table)
            
            # Load body and body type
            self.body_input.setPlainText(state.get('body', ''))
            body_type = state.get('body_type', 'raw')
            self.body_type_combo.setCurrentText(body_type)
            self._update_body_editor_for_type(body_type)
            
            # Load auth
            auth_type = state.get('auth_type', 'None')
            self.auth_type_combo.setCurrentText(auth_type)
            self.auth_token_input.setText(state.get('auth_token', ''))
            # Manually update widget visibility since signals are blocked
            self.bearer_token_widget.setVisible(auth_type == 'Bearer Token')
            self.oauth_widget.setVisible(auth_type == 'OAuth 2.0')
            
            # Load description
            self._current_description = state.get('description', '')
            self._update_description_button_style()
            
            # Load test assertions from saved state (if available) or database
            test_assertions_data = state.get('test_assertions')
            if test_assertions_data is not None:  # Check for None explicitly (empty list is valid)
                print(f"[DEBUG] Restoring test assertions from tab state: {len(test_assertions_data)} assertions")
                self.test_tab.load_assertions(test_assertions_data)
                if self.current_request_id:
                    self.test_tab.set_request_id(self.current_request_id)
                else:
                    self.test_tab.clear()
            elif self.current_request_id:
                # No saved test assertions, load from database
                print(f"[DEBUG] Loading test assertions from database for request_id={self.current_request_id}")
                self._load_test_assertions(self.current_request_id)
            else:
                self.test_tab.clear()
            
            # Load scripts from saved state (if available)
            scripts_data = state.get('scripts')
            if scripts_data is not None:  # Check for None explicitly (empty dict is valid)
                print(f"[DEBUG] Restoring scripts from tab state")
                self.scripts_tab.load_scripts(
                    scripts_data.get('pre_request_script', ''),
                    scripts_data.get('post_response_script', '')
                )
            elif self.current_request_id:
                # No saved script state, load from database
                print(f"[DEBUG] Loading scripts from database for request_id={self.current_request_id}")
                request = self.db.get_request(self.current_request_id)
                if request:
                    self.scripts_tab.load_scripts(
                        request.get('pre_request_script', '') or '',
                        request.get('post_response_script', '') or ''
                    )
            else:
                # No request ID and no scripts - clear
                self.scripts_tab.load_scripts('', '')
            
            # Always clear console when switching tabs
            self.scripts_tab._clear_console()
            
            # Restore UI preferences (active tabs, view modes)
            ui_preferences = state.get('ui_preferences', {})
            if ui_preferences:
                print(f"[DEBUG] Restoring UI preferences: {ui_preferences}")
                
                # Restore active inner tab (Params, Headers, Body, Tests, Scripts, etc.)
                active_inner_tab = ui_preferences.get('active_inner_tab', 0)
                if hasattr(self, 'inner_tabs') and 0 <= active_inner_tab < self.inner_tabs.count():
                    self.inner_tabs.setCurrentIndex(active_inner_tab)
                
                # Description visibility removed - description now accessed via popup button
            
            # Clear response viewer for new requests (no response data yet)
            if state.get('is_new_request') or not self.current_request_id:
                self._clear_response_viewer()
            
            # Restore change state
            self.has_unsaved_changes = state.get('has_changes', False)
            self._update_request_title()
            
        finally:
            # Always unblock signals
            self.method_combo.blockSignals(False)
            self.url_input.blockSignals(False)
            self.params_table.blockSignals(False)
            self.headers_table.blockSignals(False)
            self.body_input.blockSignals(False)
            self.body_type_combo.blockSignals(False)
            self.auth_type_combo.blockSignals(False)
            self.auth_token_input.blockSignals(False)
            # description_input removed - now using _current_description string
            self.test_tab.blockSignals(False)
            self.scripts_tab.blockSignals(False)
        
        # Update tab counts after restoration (FIX: Update counts for all inner tabs)
        self._update_tab_counts()
        
        # Restore response if available
        response_data = state.get('response')
        if response_data:
            print(f"[DEBUG] Restoring response: status={response_data.get('status_code')}, size={response_data.get('size')}")
            self._restore_response(response_data)
            
            # Restore response UI preferences (response tab and view mode)
            if ui_preferences:
                # Restore active response tab (Body, Headers, Extract Variables)
                active_response_tab = ui_preferences.get('active_response_tab', 0)
                if hasattr(self, 'response_tabs') and 0 <= active_response_tab < self.response_tabs.count():
                    self.response_tabs.setCurrentIndex(active_response_tab)
                
                # Restore response view mode (Pretty/Raw)
                response_view_mode = ui_preferences.get('response_view_mode', 'pretty')
                if response_view_mode == 'pretty':
                    self.is_pretty_mode = True
                    if hasattr(self, 'pretty_raw_btn'):
                        self.pretty_raw_btn.setChecked(True)
                        self.pretty_raw_btn.setText("Pretty")
                    if hasattr(self, 'response_body') and hasattr(self, 'current_response_pretty'):
                        self.response_body.setPlainText(self.current_response_pretty)
                else:
                    self.is_pretty_mode = False
                    if hasattr(self, 'pretty_raw_btn'):
                        self.pretty_raw_btn.setChecked(False)
                        self.pretty_raw_btn.setText("Raw")
                    if hasattr(self, 'response_body') and hasattr(self, 'current_response_raw'):
                        self.response_body.setPlainText(self.current_response_raw)
        else:
            print("[DEBUG] No response to restore")
            # Clear response viewer
            self._clear_response_viewer()
        
        # Restore test results if available
        test_results_data = state.get('test_results')
        if test_results_data and hasattr(self, 'test_results_viewer') and self.test_results_viewer is not None:
            # Restore the test results display
            print(f"[DEBUG] Restoring test results: {test_results_data.get('summary', {})}")
            try:
                self.test_results_viewer.display_results(
                    test_results_data.get('results', []),
                    test_results_data.get('summary', {})
                )
                # Store for future captures
                self._current_test_results = test_results_data
                
                # Show test results tab when restoring test results
                if hasattr(self, 'test_results_tab_index'):
                    self.response_tabs.setTabVisible(self.test_results_tab_index, True)
            except Exception as e:
                print(f"[DEBUG] Failed to restore test results: {e}")
                # If restoration fails, just clear
                self.test_results_viewer.clear()
                self._current_test_results = None
                # Hide test results tab if restoration failed
                if hasattr(self, 'test_results_tab_index'):
                    self.response_tabs.setTabVisible(self.test_results_tab_index, False)
        else:
            print("[DEBUG] No test results to restore")
            # No test results - clear the viewer
            if hasattr(self, 'test_results_viewer') and self.test_results_viewer is not None:
                self.test_results_viewer.clear()
            self._current_test_results = None
            # Hide test results tab when no results
            if hasattr(self, 'test_results_tab_index'):
                self.response_tabs.setTabVisible(self.test_results_tab_index, False)
    
    def _on_tab_changed(self, index: int):
        """Handle tab switching."""
        if index < 0:
            print(f"[DEBUG] Tab changed to invalid index: {index}")
            return
        
        print(f"[DEBUG] Tab changed: from {self.previous_tab_index} to {index}")
        print(f"[DEBUG] Tab states keys: {list(self.tab_states.keys())}")
        
        # Save the previous tab's state (if there was one)
        if self.previous_tab_index is not None and self.previous_tab_index in self.tab_states:
            print(f"[DEBUG] Saving state for tab {self.previous_tab_index}")
            self.tab_states[self.previous_tab_index]['ui_state'] = self._capture_current_tab_state()
            self.tab_states[self.previous_tab_index]['has_changes'] = self.has_unsaved_changes
        
        # Update the previous tab index for next time
        self.previous_tab_index = index
        
        # Load new tab state
        if index in self.tab_states:
            tab_state = self.tab_states[index]
            print(f"[DEBUG] Tab {index} state: request_id={tab_state.get('request_id')}, has_ui_state={bool(tab_state.get('ui_state'))}")
            
            # Check if we have a UI state already
            if 'ui_state' in tab_state and tab_state['ui_state']:
                # UI state exists - restore it
                print(f"[DEBUG] Restoring UI state for tab {index}")
                self._restore_tab_state(tab_state['ui_state'])
                # Update highlight after restore
                self._update_current_request_highlight()
                # Ensure request is visible in tree
                if tab_state.get('request_id'):
                    self._ensure_request_visible_in_tree(tab_state['request_id'])
            elif tab_state.get('request_id'):
                # No UI state but has request_id - load from database directly
                print(f"[DEBUG] Loading request data from DB for tab {index}")
                self._load_request_data(tab_state['request_id'])  # Use _load_request_data instead of _load_request
                # _load_request_data will call _update_current_request_highlight() at its end
                # Ensure request is visible in tree
                self._ensure_request_visible_in_tree(tab_state['request_id'])
            else:
                # Empty tab - clear editor (this also clears scripts and console)
                print(f"[DEBUG] Clearing editor for empty tab {index}")
                self._clear_request_editor()
                # Update highlight for empty tab
                self._update_current_request_highlight()
            
            # Update tab title
            self._update_tab_title(index)
            
            # Refresh variable inspector panel to show correct collection variables
            self._refresh_variable_inspector_panel()
        else:
            print(f"[DEBUG] WARNING: Tab {index} not found in tab_states!")
    
    def _close_tab(self, index: int):
        """Handle tab close request."""
        # Check for unsaved changes
        if index in self.tab_states:
            state = self.tab_states[index]
            if state.get('has_changes', False):
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"Tab has unsaved changes. Close anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # Remove tab
        self.request_tabs.removeTab(index)
        
        # Remove from state storage
        if index in self.tab_states:
            del self.tab_states[index]
        
        # Reindex remaining tabs
        new_states = {}
        for i, state in self.tab_states.items():
            if i > index:
                new_states[i - 1] = state
            else:
                new_states[i] = state
        self.tab_states = new_states
        
        # Reset previous_tab_index since tabs were reindexed
        # The _on_tab_changed will be called next and will set it properly
        self.previous_tab_index = None
        
        # If no tabs left, show empty state
        if self.request_tabs.count() == 0:
            print(f"[DEBUG] No tabs left, switching center_stack to empty state")
            self.center_stack.setCurrentWidget(self.no_request_empty_state)
            # Clear all editor fields to prevent stale data
            self._clear_request_editor()
        else:
            # Switch to the current tab
            self._on_tab_changed(self.request_tabs.currentIndex())
        
        # Update collections tree highlighting after closing tab
        self._update_current_request_highlight()
    
    def _close_temporary_tab(self):
        """Close the current temporary tab without confirmation."""
        if self.temporary_tab_index is not None and self.temporary_tab_index in self.tab_states:
            temp_index = self.temporary_tab_index
            
            # Remove tab
            self.request_tabs.removeTab(temp_index)
            
            # Remove from state storage
            if temp_index in self.tab_states:
                del self.tab_states[temp_index]
            
            # Reindex remaining tabs
            new_states = {}
            for i, state in self.tab_states.items():
                if i > temp_index:
                    new_states[i - 1] = state
                else:
                    new_states[i] = state
            self.tab_states = new_states
            
            # Clear temporary tab tracking
            self.temporary_tab_index = None
            
            # If temporary tab was removed and there are other tabs, adjust temporary_tab_index
            # for any tabs that were after it
            if self.temporary_tab_index is not None and self.temporary_tab_index > temp_index:
                self.temporary_tab_index -= 1
            
            # If no tabs left, show empty state
            if self.request_tabs.count() == 0:
                print(f"[DEBUG] No tabs left after closing temporary tab, switching to empty state")
                self.center_stack.setCurrentWidget(self.no_request_empty_state)
                self._clear_request_editor()
    
    def _convert_temporary_to_persistent(self):
        """Convert the current temporary tab to persistent."""
        current_index = self.request_tabs.currentIndex()
        if (current_index >= 0 and 
            current_index in self.tab_states and 
            self.tab_states[current_index].get('is_temporary', False)):
            
            # Mark as persistent
            self.tab_states[current_index]['is_temporary'] = False
            
            # Update tab bar display
            tab_bar = self.request_tabs.tabBar()
            if isinstance(tab_bar, ColoredTabBar) and current_index in tab_bar.tab_data:
                data = tab_bar.tab_data[current_index]
                tab_bar.set_tab_data(
                    current_index,
                    data['method'],
                    data['name'],
                    data['has_changes'],
                    is_temporary=False
                )
            
            # Clear temporary tab tracking if this was the temporary tab
            if self.temporary_tab_index == current_index:
                self.temporary_tab_index = None
    
    def _close_all_tabs_except(self, keep_index: int):
        """Close all tabs except the specified one."""
        # Check for unsaved changes in any tab (except the one we're keeping)
        has_unsaved = False
        for i in range(self.request_tabs.count()):
            if i != keep_index and i in self.tab_states and self.tab_states[i].get('has_changes', False):
                has_unsaved = True
                break
        
        # Confirm if there are unsaved changes
        if has_unsaved:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Some tabs have unsaved changes. Close them anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Save the state of the tab we want to keep
        keep_state = self.tab_states.get(keep_index)
        
        # Block signals to avoid triggering multiple updates
        self.request_tabs.blockSignals(True)
        
        # Close all tabs from the end to avoid index shifting issues
        # Start from the last tab and work backwards
        for i in range(self.request_tabs.count() - 1, -1, -1):
            if i != keep_index:
                self.request_tabs.removeTab(i)
        
        self.request_tabs.blockSignals(False)
        
        # Now only one tab remains at index 0
        # Update tab states
        if keep_state:
            self.tab_states = {0: keep_state}
            
            # Update tab bar data
            method = keep_state.get('ui_state', {}).get('method', 'GET')
            name = keep_state.get('name', 'Untitled')
            self.request_tabs.tabBar().set_tab_data(0, method, name, keep_state.get('has_changes', False))
        else:
            self.tab_states = {}
        
        # Reset previous tab index
        self.previous_tab_index = None
        
        # Ensure the remaining tab is selected and its state is restored
        self.request_tabs.setCurrentIndex(0)
        self._on_tab_changed(0)
    
    def _close_all_tabs(self):
        """Close all tabs."""
        # Check for unsaved changes in any tab
        has_unsaved = False
        for state in self.tab_states.values():
            if state.get('has_changes', False):
                has_unsaved = True
                break
        
        # Confirm if there are unsaved changes
        if has_unsaved:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Some tabs have unsaved changes. Close them anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Close all tabs
        self.request_tabs.blockSignals(True)
        while self.request_tabs.count() > 0:
            self.request_tabs.removeTab(0)
        self.request_tabs.blockSignals(False)
        
        # Clear tab states
        self.tab_states = {}
        self.previous_tab_index = None
        
        # Show empty state
        self.center_stack.setCurrentWidget(self.no_request_empty_state)
        self._clear_request_editor()
    
    def _close_tabs_on_left(self, tab_index: int):
        """Close all tabs to the left of the specified tab."""
        if tab_index <= 0:
            return  # No tabs on the left
        
        # Check for unsaved changes in tabs on the left
        has_unsaved = False
        for i in range(tab_index):
            if i in self.tab_states and self.tab_states[i].get('has_changes', False):
                has_unsaved = True
                break
        
        # Confirm if there are unsaved changes
        if has_unsaved:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Some tabs have unsaved changes. Close them anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Block signals to avoid triggering multiple updates
        self.request_tabs.blockSignals(True)
        
        # Close tabs from left to the target (working backwards to avoid index shifting)
        for i in range(tab_index - 1, -1, -1):
            self.request_tabs.removeTab(i)
        
        self.request_tabs.blockSignals(False)
        
        # Update tab states (shift indices down)
        new_states = {}
        for old_index, state in self.tab_states.items():
            if old_index >= tab_index:
                new_index = old_index - tab_index
                new_states[new_index] = state
        self.tab_states = new_states
        
        # Update tab bar data for all remaining tabs
        for index, state in self.tab_states.items():
            method = state.get('method', 'GET')
            name = state.get('name', 'Untitled')
            has_changes = state.get('has_changes', False)
            is_temporary = state.get('is_temporary', False)
            tab_bar = self.request_tabs.tabBar()
            if isinstance(tab_bar, ColoredTabBar):
                tab_bar.set_tab_data(index, method, name, has_changes, is_temporary)
        
        # Ensure correct tab is selected (the target tab is now at index 0)
        self.request_tabs.setCurrentIndex(0)
    
    def _close_tabs_on_right(self, tab_index: int):
        """Close all tabs to the right of the specified tab."""
        if tab_index >= self.request_tabs.count() - 1:
            return  # No tabs on the right
        
        # Check for unsaved changes in tabs on the right
        has_unsaved = False
        for i in range(tab_index + 1, self.request_tabs.count()):
            if i in self.tab_states and self.tab_states[i].get('has_changes', False):
                has_unsaved = True
                break
        
        # Confirm if there are unsaved changes
        if has_unsaved:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Some tabs have unsaved changes. Close them anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Block signals to avoid triggering multiple updates
        self.request_tabs.blockSignals(True)
        
        # Close tabs from right to left (working backwards)
        for i in range(self.request_tabs.count() - 1, tab_index, -1):
            self.request_tabs.removeTab(i)
        
        self.request_tabs.blockSignals(False)
        
        # Update tab states (only keep states up to tab_index)
        new_states = {}
        for old_index, state in self.tab_states.items():
            if old_index <= tab_index:
                new_states[old_index] = state
        self.tab_states = new_states
        
        # Ensure correct tab is selected
        if tab_index in self.tab_states:
            self.request_tabs.setCurrentIndex(tab_index)
        
        # Update collections tree highlighting
        self._update_current_request_highlight()
    
    def _create_new_tab(self, request_id: Optional[int] = None, request_data: Optional[Dict] = None):
        """Create a new tab."""
        # Save current tab state first
        current_index = self.request_tabs.currentIndex()
        if current_index >= 0 and current_index in self.tab_states:
            self.tab_states[current_index]['ui_state'] = self._capture_current_tab_state()
            self.tab_states[current_index]['has_changes'] = self.has_unsaved_changes
        
        # Determine tab name and method
        if request_data:
            name = request_data.get('name', 'Untitled')
            method = request_data.get('method', 'GET')
        else:
            name = f'Untitled {self.next_untitled_num}'
            self.next_untitled_num += 1
            method = 'GET'
        
        # Add new tab with empty widget (tabs are just for visual representation)
        tab_index = self.request_tabs.addTab(QWidget(), "")  # Empty text initially
        
        # Set tab data for custom rendering
        tab_bar = self.request_tabs.tabBar()
        if isinstance(tab_bar, ColoredTabBar):
            tab_bar.set_tab_data(tab_index, method, name, has_changes=False)
            # Force tab bar to recalculate tab sizes after data is set
            tab_bar.update()
            self.request_tabs.update()
        
        # Store tab state
        self.tab_states[tab_index] = {
            'request_id': request_id,
            'has_changes': False,
            'name': name,
            'method': method,
            'ui_state': request_data or {}
        }
        
        # Set tooltip
        self.request_tabs.setTabToolTip(tab_index, f"{method} • {name}")
        
        # Switch to new tab (this will trigger _on_tab_changed)
        self.request_tabs.setCurrentIndex(tab_index)
        
        # Return the tab index
        return tab_index
        
        # Show tabs view
        self.center_stack.setCurrentWidget(self.tabs_container)
    
    def _open_request_in_new_tab(self, request_id: int, is_temporary: bool = False):
        """Open an existing request in a new tab."""
        print(f"[DEBUG] _open_request_in_new_tab called with request_id={request_id}, is_temporary={is_temporary}")
        
        # Check if this request is already open in a tab
        existing_tab = self._find_tab_with_request(request_id)
        if existing_tab >= 0:
            # Request is already open - switch to that tab instead of creating a new one
            print(f"[DEBUG] Request {request_id} already open in tab {existing_tab}, switching to it")
            self.request_tabs.setCurrentIndex(existing_tab)
            print(f"[DEBUG] Switching center_stack to tabs_container (request already open)")
            self.center_stack.setCurrentWidget(self.tabs_container)
            # If it was supposed to be persistent (double-click), make it persistent
            if not is_temporary and existing_tab in self.tab_states:
                if self.tab_states[existing_tab].get('is_temporary', False):
                    print(f"[DEBUG] Converting temporary tab {existing_tab} to permanent")
                    self.tab_states[existing_tab]['is_temporary'] = False
                    # Update tab bar to remove italic styling
                    tab_bar = self.request_tabs.tabBar()
                    if isinstance(tab_bar, ColoredTabBar):
                        state = self.tab_states[existing_tab]
                        tab_bar.set_tab_data(
                            existing_tab,
                            state.get('method', 'GET'),
                            state.get('name', 'Untitled'),
                            state.get('has_changes', False),
                            is_temporary=False
                        )
                    self._update_tab_title(existing_tab)
                    if self.temporary_tab_index == existing_tab:
                        self.temporary_tab_index = None
            return
        
        # If opening in temporary mode and a temporary tab already exists, close it
        if is_temporary and self.temporary_tab_index is not None:
            print(f"[DEBUG] Closing existing temporary tab {self.temporary_tab_index}")
            self._close_temporary_tab()
        
        # Load the request data from database
        request_data = self.db.get_request(request_id)
        if not request_data:
            QMessageBox.warning(self, "Error", "Failed to load request!")
            return
        
        # Save current tab state first (if not closing a temporary tab)
        current_index = self.request_tabs.currentIndex()
        print(f"[DEBUG] Current tab index before creating new tab: {current_index}")
        if current_index >= 0 and current_index in self.tab_states:
            self.tab_states[current_index]['ui_state'] = self._capture_current_tab_state()
            self.tab_states[current_index]['has_changes'] = self.has_unsaved_changes
        
        # Prepare request data for new tab
        name = request_data['name']
        method = request_data['method']
        
        # Block signals to prevent premature _on_tab_changed call
        print(f"[DEBUG] Blocking signals, about to add tab")
        self.request_tabs.blockSignals(True)
        
        # Add new tab
        tab_index = self.request_tabs.addTab(QWidget(), f"{method} • {name}")  # Added bullet separator
        print(f"[DEBUG] Added tab at index: {tab_index}, total tabs: {self.request_tabs.count()}")
        
        # Store tab state with request data BEFORE unblocking signals
        self.tab_states[tab_index] = {
            'request_id': request_id,
            'has_changes': False,
            'name': name,
            'method': method,
            'is_temporary': is_temporary,
            'ui_state': {}  # Will be populated when tab is activated
        }
        print(f"[DEBUG] Stored tab state for index {tab_index}, is_temporary={is_temporary}, all tab_states keys: {list(self.tab_states.keys())}")
        
        # Track temporary tab
        if is_temporary:
            self.temporary_tab_index = tab_index
        
        # Unblock signals
        self.request_tabs.blockSignals(False)
        print(f"[DEBUG] Unblocked signals, about to switch to tab {tab_index}")
        
        # Switch to new tab (this will NOW trigger _on_tab_changed which loads the request)
        old_index = self.request_tabs.currentIndex()
        print(f"[DEBUG] Current index before setCurrentIndex: {old_index}")
        self.request_tabs.setCurrentIndex(tab_index)
        
        # If the index didn't change (e.g., switching to first tab 0 from no tabs),
        # manually trigger the tab changed logic
        if old_index == tab_index:
            print(f"[DEBUG] Index didn't change ({old_index} -> {tab_index}), manually triggering _on_tab_changed")
            self._on_tab_changed(tab_index)
        
        # Show tabs view
        print(f"[DEBUG] Switching center_stack to tabs_container (after creating new tab)")
        self.center_stack.setCurrentWidget(self.tabs_container)
    
    def _update_tab_title(self, index: int):
        """Update tab title with method and name."""
        if index not in self.tab_states:
            return
        
        state = self.tab_states[index]
        method = state.get('method', 'GET')
        name = state.get('name', 'Untitled')
        has_changes = state.get('has_changes', False)
        is_temporary = state.get('is_temporary', False)
        
        # Update tab data for custom rendering
        tab_bar = self.request_tabs.tabBar()
        if isinstance(tab_bar, ColoredTabBar):
            tab_bar.set_tab_data(index, method, name, has_changes, is_temporary)
            # Force tab bar to recalculate tab sizes after data is set
            tab_bar.update()
            self.request_tabs.update()
        
        # Set tooltip to show full request name
        tooltip = f"{method} • {name}"
        if has_changes:
            tooltip += " (unsaved changes)"
        self.request_tabs.setTabToolTip(index, tooltip)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions."""
        # Send request (Ctrl+Enter or Ctrl+Return)
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        send_shortcut.activated.connect(self._send_request)
        
        # Save request (Ctrl+S)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._save_request)
        
        # New request (Ctrl+N)
        new_request_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_request_shortcut.activated.connect(self._create_new_request)
        
        # Focus URL bar (Ctrl+L)
        url_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        url_shortcut.activated.connect(lambda: self.url_input.setFocus())
        
        # Generate code (Ctrl+Shift+C)
        code_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        code_shortcut.activated.connect(self._generate_code)
        
        # Close tab (Ctrl+W)
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(lambda: self._close_tab(self.request_tabs.currentIndex()))
        
        # Delete selected item (Delete key)
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._delete_selected)
        
        # Show keyboard shortcuts help (Ctrl+/)
        help_shortcut = QShortcut(QKeySequence("Ctrl+/"), self)
        help_shortcut.activated.connect(self._show_shortcuts_help)
        
        # Panel toggle shortcuts (Alt+key)
        # Alt+E - Toggle Environments panel
        env_shortcut = QShortcut(QKeySequence("Alt+E"), self)
        env_shortcut.activated.connect(lambda: self._switch_left_panel('environments'))
        
        # Alt+C - Toggle Collections panel
        collections_shortcut = QShortcut(QKeySequence("Alt+C"), self)
        collections_shortcut.activated.connect(lambda: self._switch_left_panel('collections'))
        
        # Alt+H - Toggle History panel
        history_shortcut = QShortcut(QKeySequence("Alt+H"), self)
        history_shortcut.activated.connect(self._toggle_history_panel)
        
        # Alt+V - Toggle Variables (Variable Inspector) panel
        variables_shortcut = QShortcut(QKeySequence("Alt+V"), self)
        variables_shortcut.activated.connect(lambda: self._switch_left_panel('variable_inspector'))
        
        # Alt+G - Toggle Git Sync panel
        git_shortcut = QShortcut(QKeySequence("Alt+G"), self)
        git_shortcut.activated.connect(lambda: self._switch_left_panel('git_sync'))
        
        # Alt+R - Toggle Recent requests panel
        recent_shortcut = QShortcut(QKeySequence("Alt+R"), self)
        recent_shortcut.activated.connect(self._toggle_recent_requests)
    
    def _create_collections_pane(self) -> QWidget:
        """Create the left pane containing the collections tree."""
        pane = QWidget()
        layout = QVBoxLayout(pane)
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
        
        title = QLabel("📁 Collections")
        title.setStyleSheet("font-size: 13px; font-weight: 600; border: none;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Add Collection button in header
        self.add_collection_btn = QPushButton("+ Add")
        self.add_collection_btn.setToolTip("Add a new collection")
        self.add_collection_btn.clicked.connect(self._add_collection)
        header_layout.addWidget(self.add_collection_btn)
        
        # Import button with dropdown menu in header
        self.import_collection_menu_btn = QPushButton("📥 Import")
        self.import_collection_menu_btn.setToolTip("Import collections, cURL commands, or OpenAPI specs")
        
        # Create dropdown menu with proper styling
        import_menu = QMenu(self.import_collection_menu_btn)
        import_menu.setStyleSheet("""
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
        import_collection_action = QAction("📄 Import Collection (JSON)", self)
        import_collection_action.setToolTip("Import a collection from JSON file")
        import_collection_action.triggered.connect(self._import_collection)
        import_menu.addAction(import_collection_action)
        
        import_curl_action = QAction("🔗 Import cURL Command", self)
        import_curl_action.setToolTip("Import a cURL command as a new request")
        import_curl_action.triggered.connect(self._import_curl)
        import_menu.addAction(import_curl_action)
        
        import_openapi_action = QAction("📋 Import OpenAPI/Swagger", self)
        import_openapi_action.setToolTip("Import OpenAPI/Swagger specification")
        import_openapi_action.triggered.connect(self._import_openapi)
        import_menu.addAction(import_openapi_action)
        
        # Attach menu to button
        self.import_collection_menu_btn.setMenu(import_menu)
        header_layout.addWidget(self.import_collection_menu_btn)
        
        # Apply initial theme to collection header buttons
        self._update_collection_header_button_styles()
        
        layout.addWidget(header)
        
        # Collections tree
        self.collections_tree = ReorderableTreeWidget()
        self.collections_tree.main_window = self  # Give it access to main window
        self.collections_tree.setHeaderHidden(True)  # Hide "Name" header
        self.collections_tree.setIconSize(QSize(16, 16))  # Standardize icon size to 16px
        # Set custom delegate for colored method badges
        self.collections_tree.setItemDelegate(RequestTreeItemDelegate())
        # Single-click on collections/folders to expand/collapse, single-click on requests to open
        self.collections_tree.itemClicked.connect(self._on_tree_item_clicked)
        # Double-click on requests also opens them (for users who prefer double-click)
        self.collections_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        # Connect expand/collapse signals for folder icon updates
        self.collections_tree.itemExpanded.connect(self._on_tree_item_expanded)
        self.collections_tree.itemCollapsed.connect(self._on_tree_item_collapsed)
        # Enable selection for drag & drop (but single selection only)
        self.collections_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.collections_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.collections_tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        
        # Enable drag & drop for reordering
        self.collections_tree.setDragEnabled(True)
        self.collections_tree.setAcceptDrops(True)
        self.collections_tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.collections_tree.setDropIndicatorShown(True)
        self.collections_tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        layout.addWidget(self.collections_tree)
        
        return pane
    
    def _create_workspace_pane(self) -> QWidget:
        """Create the right pane with request editor and response viewer."""
        pane = QWidget()
        layout = QVBoxLayout(pane)
        
        # Create vertical splitter (request editor | response viewer)
        self.request_response_splitter = QSplitter(Qt.Orientation.Vertical)
        self.request_response_splitter.setChildrenCollapsible(False)  # Prevent panels from collapsing
        
        # Top section: Request Editor
        request_editor = self._create_request_editor()
        self.request_response_splitter.addWidget(request_editor)
        
        # Bottom section: Response Viewer
        response_viewer = self._create_response_viewer()
        self.request_response_splitter.addWidget(response_viewer)
        
        # Set splitter sizes to 50/50 split (equal space for request and response)
        # This will maintain proper proportions when window is maximized
        self.request_response_splitter.setStretchFactor(0, 1)  # Request editor - 50%
        self.request_response_splitter.setStretchFactor(1, 1)  # Response viewer - 50%
        
        layout.addWidget(self.request_response_splitter)
        
        # Set initial sizes to 50/50 split after window is shown
        # This will be calculated based on actual available height
        
        return pane
    
    def _create_request_editor(self) -> QWidget:
        """Create the request editor section."""
        editor = QWidget()
        layout = QVBoxLayout(editor)
        layout.setSpacing(2)  # Minimal spacing for compact layout
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for tight fit
        
        # Dynamic request title header (fixed height, no stretch) - ENHANCED
        # Create a container for the title label and rename button
        title_container = QWidget()
        title_container.setMaximumHeight(32)
        title_container.setMinimumHeight(32)
        title_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(8, 3, 8, 3)  # Reduced margins for compact layout
        title_layout.setSpacing(4)  # Reduced spacing
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Vertical center alignment
        
        self.request_title_label = QLabel("New Request (not saved)")
        self.request_title_label.setObjectName("requestTitleLabel")
        self.request_title_label.setStyleSheet("font-size: 13px; font-weight: 500;")  # Use consistent font sizing
        self.request_title_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)  # Changed to Minimum so it doesn't expand
        self.request_title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Vertical center
        title_layout.addWidget(self.request_title_label)
        
        # Add rename button with pencil icon - inline with text
        self.rename_request_btn = QPushButton("✏️")
        self.rename_request_btn.setObjectName("renameRequestBtn")
        self.rename_request_btn.setFixedSize(22, 22)  # Smaller, more delicate
        self.rename_request_btn.setToolTip("Rename request")
        self.rename_request_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rename_request_btn.setVisible(False)  # Hidden by default, shown when request is loaded
        self.rename_request_btn.clicked.connect(self._rename_current_request)
        # Theme-aware styling will be applied via method
        self._update_rename_button_style()
        title_layout.addWidget(self.rename_request_btn, 0, Qt.AlignmentFlag.AlignVCenter)  # Add with vertical center alignment
        
        # Add description button with comment icon - inline with text
        self.description_btn = QPushButton("💬")  # Comment icon
        self.description_btn.setObjectName("descriptionBtn")
        self.description_btn.setFixedSize(22, 22)  # Same size as rename button
        self.description_btn.setToolTip("Add/edit description (empty)")
        self.description_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.description_btn.setVisible(False)  # Hidden by default, shown when request is loaded
        self.description_btn.clicked.connect(self._edit_description)
        # Theme-aware styling will be applied via method
        self._update_description_button_style()
        title_layout.addWidget(self.description_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # Description is tracked via self._current_description (initialized in __init__)
        
        # Add stretch to push everything to the left
        title_layout.addStretch()
        
        layout.addWidget(title_container, 0)  # Stretch factor 0 = fixed
        
        # Method and URL row (fixed height, no stretch)
        # Wrap in a container widget to enforce fixed height
        url_container = QWidget()
        url_container.setMaximumHeight(40)  # Reduced for better screen fit
        url_container.setMinimumHeight(40)
        url_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        url_layout = QHBoxLayout(url_container)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(0)  # No spacing - buttons will be connected
        
        # HTTP Method Combo with improved styling
        self.method_combo = QComboBox()
        self.method_combo.addItems(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
        self.method_combo.setObjectName("methodCombo")  # For stylesheet targeting
        self.method_combo.setMaximumWidth(100)
        self.method_combo.setMinimumHeight(32)  # Reduced for compact layout
        self.method_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Apply method-specific colors via styleSheet update on change
        self.method_combo.currentTextChanged.connect(self._update_method_style)
        url_layout.addWidget(self.method_combo)
        url_layout.addSpacing(12)  # Spacing after method combo
        
        self.url_input = HighlightedLineEdit(theme=self.current_theme)
        self.url_input.setPlaceholderText("Enter request URL or paste text")
        self.url_input.returnPressed.connect(self._send_request)  # Enter key sends request
        self.url_input.textChanged.connect(self._sync_url_to_params)  # Live sync URL to params
        self.url_input.setMinimumHeight(32)  # Reduced for compact layout
        self.url_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        url_layout.addWidget(self.url_input)
        url_layout.addSpacing(12)  # Spacing after URL input
        
        # IMPROVED: Larger, more prominent Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")  # For stylesheet targeting
        self.send_btn.setProperty("class", "primary")
        self.send_btn.setProperty("primary", "true")  # For QSS targeting
        self.send_btn.setMinimumWidth(100)  # Increased from 80
        self.send_btn.setMinimumHeight(32)  # Reduced for compact layout
        self.send_btn.clicked.connect(self._send_request)
        self.send_btn.setToolTip("Send request (Ctrl+Enter)")
        self.send_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Set font to make it more prominent
        send_font = QFont()
        send_font.setBold(True)
        send_font.setPixelSize(14)
        self.send_btn.setFont(send_font)
        url_layout.addWidget(self.send_btn)
        url_layout.addSpacing(12)  # Spacing after Send button
        
        # Create a container for the connected button group - ZERO spacing
        button_group = QWidget()
        button_group.setStyleSheet("QWidget { background: transparent; }")
        button_group_layout = QHBoxLayout(button_group)
        button_group_layout.setContentsMargins(0, 0, 0, 0)
        button_group_layout.setSpacing(0)
        
        # Save button with rounded corners only on the left
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedSize(80, 32)  # Reduced for compact layout
        self.save_btn.clicked.connect(self._save_request)
        self.save_btn.setToolTip("Save request (Ctrl+S)")
        button_group_layout.addWidget(self.save_btn)
        
        # Apply initial theme to save button
        self._update_save_button_style()
        
        # Menu button with down arrow
        self.menu_btn = QPushButton("▼")
        self.menu_btn.setFixedSize(28, 32)  # Reduced for compact layout
        self.menu_btn.setToolTip("More options")
        self.menu_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #444444;
                border-left: none;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: transparent;
                color: #E0E0E0;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                border-color: #555555;
                border-left: none;
            }
            QPushButton:pressed {
                background-color: #2D2D2D;
            }
        """)
        
        # Style the arrow
        menu_font = QFont()
        menu_font.setPixelSize(7)
        self.menu_btn.setFont(menu_font)
        button_group_layout.addWidget(self.menu_btn)
        
        # Add the button group to url_layout
        url_layout.addWidget(button_group)
        
        # Create menu for the button
        self.options_menu = QMenu(self)
        
        # Code action
        code_action = QAction("💻 Code", self)
        code_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        code_action.triggered.connect(self._generate_code)
        code_action.setToolTip("Generate code snippet")
        self.options_menu.addAction(code_action)
        
        # Copy as cURL action
        curl_action = QAction("📋 Copy as cURL", self)
        curl_action.triggered.connect(self._copy_as_curl)
        curl_action.setToolTip("Copy request as cURL command")
        self.options_menu.addAction(curl_action)
        
        # Connect button to show menu (without dropdown arrow indicator)
        self.menu_btn.clicked.connect(self._show_options_menu)
        url_layout.addWidget(self.menu_btn)
        
        layout.addWidget(url_container, 0)  # Stretch factor 0 = fixed
        
        # Connect inputs to track changes and update title
        self.method_combo.currentIndexChanged.connect(self._mark_as_changed)
        self.method_combo.currentIndexChanged.connect(self._update_request_title)  # Update title when method changes
        self.url_input.textChanged.connect(self._mark_as_changed)
        
        # Description section has been removed - now accessed via popup button in header
        
        # Create collapsible container for request tabs
        self.request_tabs_container = QWidget()
        request_tabs_layout = QVBoxLayout(self.request_tabs_container)
        request_tabs_layout.setContentsMargins(0, 0, 0, 0)
        request_tabs_layout.setSpacing(0)
        
        # Header with collapse/expand button for request area
        request_header_layout = QHBoxLayout()
        request_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.request_tabs_toggle_btn = QPushButton("▼ Request")
        self.request_tabs_toggle_btn.setFlat(True)
        self.request_tabs_toggle_btn.setFixedHeight(28)  # Fixed height for compact layout
        self.request_tabs_toggle_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 4px 8px;
                border: none;
                background: transparent;
                color: #9E9E9E;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.2);
            }
        """)
        self.request_tabs_toggle_btn.clicked.connect(self._toggle_request_tabs)
        request_header_layout.addWidget(self.request_tabs_toggle_btn)
        request_header_layout.addStretch()
        
        request_tabs_layout.addLayout(request_header_layout)
        
        # No spacing between toggle button and tabs for compact layout
        
        # Tabs for Params, Headers, Authorization, Body (this should expand)
        self.inner_tabs = QTabWidget()
        self.inner_tabs.setObjectName("innerTabs")  # For specific styling
        # Set minimum height to allow window resizing when request tabs are collapsed
        self.inner_tabs.setMinimumHeight(80)  # Small minimum for collapsed state
        self.inner_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Params tab
        self.params_table = self._create_key_value_table()
        self.params_table.itemChanged.connect(self._update_tab_counts)
        self.params_table.itemChanged.connect(lambda: self._auto_add_table_rows(self.params_table))
        self.params_table.itemChanged.connect(self._sync_params_to_url)  # Live sync params to URL
        self.inner_tabs.addTab(self.params_table, "Params")
        
        # Headers tab
        self.headers_table = self._create_key_value_table()
        self.headers_table.itemChanged.connect(self._update_tab_counts)
        self.headers_table.itemChanged.connect(lambda: self._auto_add_table_rows(self.headers_table))
        self.inner_tabs.addTab(self.headers_table, "Headers")
        
        # Authorization tab
        auth_widget = self._create_auth_widget()
        self.inner_tabs.addTab(auth_widget, "Authorization")
        
        # Body tab
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        
        # Body type selector (Postman-style)
        body_type_row = QHBoxLayout()
        body_type_label = QLabel("Body Type:")
        body_type_label.setFixedWidth(80)
        self.body_type_combo = QComboBox()
        self.body_type_combo.addItems(["none", "form-data", "x-www-form-urlencoded", "raw"])
        self.body_type_combo.setCurrentText("raw")
        self.body_type_combo.currentTextChanged.connect(self._on_body_type_changed)
        self.body_type_combo.currentTextChanged.connect(self._mark_as_changed)
        self.body_type_combo.setMinimumWidth(180)
        self.body_type_combo.setFixedHeight(24)
        self.body_type_combo.setStyleSheet("""
            QComboBox {
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                font-size: 11px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 20px;
                padding: 4px 8px;
            }
        """)
        body_type_row.addWidget(body_type_label)
        body_type_row.addWidget(self.body_type_combo)
        body_type_row.addStretch()
        body_layout.addLayout(body_type_row)
        
        # Use AutocompleteTextEdit for variable autocomplete support
        from src.ui.widgets.variable_autocomplete import AutocompleteTextEdit
        self.body_input = AutocompleteTextEdit(theme=self.current_theme)
        self.body_input.set_environment_manager(self.env_manager)
        self.body_input.set_main_window(self)  # Set main window for variable resolution
        self.body_input.setPlaceholderText("Enter request body (e.g., JSON)")
        self.body_input.textChanged.connect(self._mark_as_changed)
        self.body_input.textChanged.connect(self._update_tab_indicators)
        
        # Add variable syntax highlighting to body with status colors
        self.body_highlighter = VariableSyntaxHighlighter(self.body_input.document(), self.current_theme)
        self.body_highlighter.environment_manager = self.env_manager
        
        body_layout.addWidget(self.body_input)
        self.inner_tabs.addTab(body_widget, "Body")
        
        # Tests tab
        self.test_tab = TestTabWidget()
        self.test_tab.assertions_changed.connect(self._on_tests_changed)
        self.inner_tabs.addTab(self.test_tab, "Tests")
        
        # Scripts tab
        self.scripts_tab = ScriptTabWidget(theme=self.current_theme)
        self.scripts_tab.scripts_changed.connect(self._mark_as_changed)
        self.scripts_tab.scripts_changed.connect(self._update_tab_indicators)
        self.inner_tabs.addTab(self.scripts_tab, "Scripts")
        
        # Cookies tab
        self.cookies_tab = CookieTabWidget(theme=self.current_theme)
        self.cookies_tab.set_db_manager(self.db)
        self.cookies_tab.cookies_changed.connect(self._mark_as_changed)
        self.cookies_tab.cookies_changed.connect(self._update_tab_indicators)
        self.inner_tabs.addTab(self.cookies_tab, "Cookies")
        
        # Initialize tab counts
        self._update_tab_counts()
        
        request_tabs_layout.addWidget(self.inner_tabs, 1)  # Stretch factor 1 = expands to fill
        
        # Add the request tabs container to the main layout
        layout.addWidget(self.request_tabs_container, 1)  # Stretch factor 1 = expands to fill
        
        return editor
    
    def _create_response_viewer(self) -> QWidget:
        """Create the response viewer section."""
        viewer = QWidget()
        # Hide response viewer initially until we have a response
        viewer.setVisible(False)
        layout = QVBoxLayout(viewer)
        
        # Status info row with collapse button integrated
        status_layout = QHBoxLayout()
        
        # Collapse button on the left side (clickable with hover effect)
        self.response_collapse_btn = QPushButton("▼")
        self.response_collapse_btn.setFlat(True)
        self.response_collapse_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 2px 6px;
                border: none;
                background: transparent;
                color: #9E9E9E;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.2);
                border-radius: 3px;
            }
        """)
        self.response_collapse_btn.clicked.connect(self._toggle_response_panel)
        self.response_collapse_btn.setToolTip("Collapse/Expand response panel")
        self.response_collapse_btn.setFixedSize(24, 24)
        status_layout.addWidget(self.response_collapse_btn)
        
        # Use StatusBadge widget for professional status display
        self.status_badge = StatusBadge()
        self.status_badge.setVisible(False)  # Hidden until we have a response
        status_layout.addWidget(self.status_badge)
        
        # Metadata labels - use tertiary color for less prominence
        self.status_label = QLabel("Status: -")
        self.status_label.setProperty("class", "tertiary")  # Tertiary text for metadata
        self.status_label.setStyleSheet("font-size: 11px;")
        status_layout.addWidget(self.status_label)
        
        self.time_label = QLabel("Time: -")
        self.time_label.setProperty("class", "tertiary")  # Tertiary text for metadata
        self.time_label.setStyleSheet("font-size: 11px;")
        status_layout.addWidget(self.time_label)
        
        self.size_label = QLabel("Size: -")
        self.size_label.setProperty("class", "tertiary")  # Tertiary text for metadata
        self.size_label.setStyleSheet("font-size: 11px;")
        status_layout.addWidget(self.size_label)
        
        status_layout.addStretch()
        
        # Copy response button
        self.copy_response_btn = QPushButton("📋 Copy Response")
        self.copy_response_btn.setObjectName("copyButton")  # For stylesheet targeting
        self.copy_response_btn.setProperty("class", "secondary")
        self.copy_response_btn.clicked.connect(self._copy_response)
        self.copy_response_btn.setMaximumWidth(150)
        self.copy_response_btn.setFixedHeight(24)
        self.copy_response_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 4px 8px;
            }
        """)
        status_layout.addWidget(self.copy_response_btn)
        
        layout.addLayout(status_layout)
        
        # Create collapsible content container
        self.response_content_widget = QWidget()
        self.response_content_widget.setMinimumHeight(80)  # Small minimum for collapsed state
        response_content_layout = QVBoxLayout(self.response_content_widget)
        response_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs for Body and Headers
        self.response_tabs = QTabWidget()
        
        # Body tab with search
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar row with search and formatting controls
        toolbar_layout = QHBoxLayout()
        
        # Search section
        search_label = QLabel("🔍")
        toolbar_layout.addWidget(search_label)
        
        self.response_search = QLineEdit()
        self.response_search.setPlaceholderText("Search in response...")
        self.response_search.textChanged.connect(self._search_response)
        self.response_search.setClearButtonEnabled(True)
        self.response_search.setMaximumWidth(200)
        toolbar_layout.addWidget(self.response_search)
        
        # Search navigation buttons
        self.search_prev_btn = QPushButton("◀")
        self.search_prev_btn.setMaximumWidth(30)
        self.search_prev_btn.setFixedHeight(24)
        self.search_prev_btn.setStyleSheet("font-size: 11px; padding: 4px;")
        self.search_prev_btn.setToolTip("Previous match (Shift+Enter)")
        self.search_prev_btn.clicked.connect(self._search_previous)
        self.search_prev_btn.setEnabled(False)
        toolbar_layout.addWidget(self.search_prev_btn)
        
        self.search_next_btn = QPushButton("▶")
        self.search_next_btn.setMaximumWidth(30)
        self.search_next_btn.setFixedHeight(24)
        self.search_next_btn.setStyleSheet("font-size: 11px; padding: 4px;")
        self.search_next_btn.setToolTip("Next match (Enter)")
        self.search_next_btn.clicked.connect(self._search_next)
        self.search_next_btn.setEnabled(False)
        toolbar_layout.addWidget(self.search_next_btn)
        
        # Search counter label
        self.search_counter_label = QLabel("")
        self.search_counter_label.setStyleSheet("color: #666; font-size: 11px; padding: 0 8px;")
        self.search_counter_label.setVisible(False)
        toolbar_layout.addWidget(self.search_counter_label)
        
        toolbar_layout.addStretch()
        
        # Formatting controls
        self.pretty_raw_btn = QPushButton("📄 Pretty")
        self.pretty_raw_btn.setCheckable(True)
        self.pretty_raw_btn.setChecked(True)  # Pretty mode by default
        self.pretty_raw_btn.setMaximumWidth(100)
        self.pretty_raw_btn.setFixedHeight(24)
        self.pretty_raw_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 4px 8px;
            }
        """)
        self.pretty_raw_btn.setToolTip("Toggle between Pretty (formatted) and Raw view")
        self.pretty_raw_btn.clicked.connect(self._toggle_pretty_raw)
        toolbar_layout.addWidget(self.pretty_raw_btn)
        
        self.word_wrap_btn = QPushButton("↔️ Wrap")
        self.word_wrap_btn.setCheckable(True)
        self.word_wrap_btn.setChecked(False)  # No wrap by default
        self.word_wrap_btn.setMaximumWidth(100)
        self.word_wrap_btn.setFixedHeight(24)
        self.word_wrap_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 4px 8px;
            }
        """)
        self.word_wrap_btn.setToolTip("Toggle word wrap")
        self.word_wrap_btn.clicked.connect(self._toggle_word_wrap)
        toolbar_layout.addWidget(self.word_wrap_btn)
        
        body_layout.addLayout(toolbar_layout)
        
        # Use stacked widget to switch between empty state and response
        from PyQt6.QtWidgets import QStackedWidget
        self.response_stack = QStackedWidget()
        
        # Empty state widget
        self.response_empty_state = NoResponseEmptyState()
        self.response_stack.addWidget(self.response_empty_state)
        
        # Response body text area
        self.response_body = QTextEdit()
        self.response_body.setReadOnly(True)
        self.response_body.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # No wrap by default
        self.response_body.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.response_body.customContextMenuRequested.connect(self._show_response_context_menu)
        self.response_stack.addWidget(self.response_body)
        
        body_layout.addWidget(self.response_stack)
        
        # Show empty state by default
        self.response_stack.setCurrentWidget(self.response_empty_state)
        
        # Initialize response data storage
        self.current_response = None  # Store the ApiResponse object
        self.current_response_raw = ""  # Raw response text
        self.current_response_pretty = ""  # Pretty-formatted text
        self.is_pretty_mode = True  # Track current view mode
        
        # Initialize request details storage
        self.current_request_details = None  # Store actual request that was sent
        
        # Add padding to body widget
        body_layout.setContentsMargins(10, 10, 10, 10)
        
        self.response_tabs.addTab(body_widget, "Response Body")
        
        # Headers tab
        self.response_headers_table = QTableWidget()
        self.response_headers_table.setColumnCount(2)
        self.response_headers_table.setHorizontalHeaderLabels(['Key', 'Value'])
        self.response_headers_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.response_tabs.addTab(self.response_headers_table, "Response Headers")
        
        # Request Details tab
        self.request_details_viewer = QTextEdit()
        self.request_details_viewer.setReadOnly(True)
        self.request_details_viewer.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.response_tabs.addTab(self.request_details_viewer, "Request Details")
        
        # Variable Extraction tab
        self.variable_extraction_widget = VariableExtractionWidget()
        self.variable_extraction_widget.variable_extracted.connect(self._on_variable_extracted)
        self.response_tabs.addTab(self.variable_extraction_widget, "Extract Variables from Response")
        
        # Security Scan tab
        self.security_scan_tab = SecurityScanTab()
        self.security_scan_tab.export_requested.connect(self._on_security_report_export)
        self.security_scan_tab_index = self.response_tabs.addTab(self.security_scan_tab, "Security Scan")
        # Security scan tab visible by default - shows empty state until scan is run
        
        # Test Results tab - moved from collapsible panel to tab
        self.test_results_viewer = TestResultsViewer()
        self.test_results_tab_index = self.response_tabs.addTab(self.test_results_viewer, "Test Results")
        # Hide test results tab by default - will be shown when tests are run
        self.response_tabs.setTabVisible(self.test_results_tab_index, False)
        
        response_content_layout.addWidget(self.response_tabs)
        
        layout.addWidget(self.response_content_widget)
        
        return viewer
    
    def _create_key_value_table(self) -> QTableWidget:
        """Create a table widget for key-value pairs (params/headers)."""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Key', 'Value'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setRowCount(1)  # Start with just 1 empty row (dynamic expansion will handle the rest)
        
        # Apply custom delegate with variable highlighting
        delegate = NoPaddingDelegate(table, self.current_theme)
        table.setItemDelegate(delegate)
        # Store delegate reference to update theme later
        table._custom_delegate = delegate
        
        # Enable context menu for right-click delete
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda pos: self._show_table_context_menu(table, pos))
        
        # Enable keyboard Delete key
        table.keyPressEvent = lambda event: self._handle_table_key_press(table, event)
        
        # Remove max height constraint so table anchors to parent panel properly
        return table
    
    # _create_description_section removed - description now accessed via popup button in header
    
    # _toggle_description removed - no longer needed
    
    def _toggle_request_tabs(self):
        """Toggle the visibility of the request tabs section."""
        is_visible = self.inner_tabs.isVisible()
        self.inner_tabs.setVisible(not is_visible)
        
        # Update button text and adjust splitter
        if is_visible:
            # Collapsing - give more space to response
            self.request_tabs_toggle_btn.setText("▶ Request")
            # When collapsed, set minimal height for the container
            self.request_tabs_container.setMaximumHeight(28)  # Match button height
            
            # Adjust splitter to give most space to response
            # Fixed parts in request editor when collapsed:
            # - Title header: 32px (fixed height)
            # - URL bar: 40px (fixed height)
            # - Request toggle button: 28px (fixed height)
            # - Layout spacing: ~4px (2px * 2 spacing between elements)
            # Total: ~104px
            total_height = sum(self.request_response_splitter.sizes())
            request_fixed_height = 110  # Accurate measurement of fixed elements
            response_height = max(total_height - request_fixed_height, total_height * 0.85)  # At least 85% to response
            self.request_response_splitter.setSizes([int(total_height - response_height), int(response_height)])
        else:
            # Expanding - restore normal proportions
            self.request_tabs_toggle_btn.setText("▼ Request")
            # When expanded, allow it to grow
            self.request_tabs_container.setMaximumHeight(16777215)  # Qt's default max
            
            # Restore 50/50 split or user's preferred split
            total_height = sum(self.request_response_splitter.sizes())
            self.request_response_splitter.setSizes([int(total_height * 0.5), int(total_height * 0.5)])
    
    def _create_auth_widget(self) -> QWidget:
        """Create the authorization configuration widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Auth type dropdown
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setProperty("class", "secondary")  # Secondary text for form labels
        type_layout.addWidget(type_label)
        self.auth_type_combo = QComboBox()
        self.auth_type_combo.addItems(['None', 'Bearer Token', 'OAuth 2.0'])
        self.auth_type_combo.currentTextChanged.connect(self._on_auth_type_changed)
        self.auth_type_combo.setMinimumWidth(120)
        self.auth_type_combo.setFixedHeight(24)
        self.auth_type_combo.setStyleSheet("""
            QComboBox {
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                font-size: 11px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 20px;
                padding: 4px 8px;
            }
        """)
        type_layout.addWidget(self.auth_type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Bearer Token section
        self.bearer_token_widget = QWidget()
        bearer_layout = QVBoxLayout(self.bearer_token_widget)
        bearer_layout.setContentsMargins(0, 0, 0, 0)
        
        token_layout = QHBoxLayout()
        token_label = QLabel("Token:")
        token_label.setProperty("class", "secondary")  # Secondary text for form labels
        token_layout.addWidget(token_label)
        # Use HighlightedLineEdit for variable highlighting with status colors
        self.auth_token_input = HighlightedLineEdit(theme=self.current_theme)
        self.auth_token_input.environment_manager = self.env_manager
        self.auth_token_input.main_window = self  # Set main window for collection variable resolution
        self.auth_token_input.setPlaceholderText("Enter bearer token or use {{variable}}")
        self.auth_token_input.textChanged.connect(self._update_tab_counts)
        token_layout.addWidget(self.auth_token_input)
        bearer_layout.addLayout(token_layout)
        
        self.bearer_token_widget.setVisible(False)
        layout.addWidget(self.bearer_token_widget)
        
        # OAuth 2.0 section
        self.oauth_widget = QWidget()
        oauth_layout = QVBoxLayout(self.oauth_widget)
        oauth_layout.setContentsMargins(0, 0, 0, 0)
        
        oauth_status_layout = QHBoxLayout()
        self.oauth_status_label = QLabel("No OAuth token configured")
        self.oauth_status_label.setProperty("class", "tertiary")  # Tertiary text for helper/status messages
        oauth_status_layout.addWidget(self.oauth_status_label)
        oauth_status_layout.addStretch()
        oauth_layout.addLayout(oauth_status_layout)
        
        oauth_btn_layout = QHBoxLayout()
        self.oauth_config_btn = QPushButton("🔐 Configure OAuth")
        self.oauth_config_btn.clicked.connect(self._configure_oauth)
        oauth_btn_layout.addWidget(self.oauth_config_btn)
        
        self.oauth_refresh_btn = QPushButton("🔄 Refresh Token")
        self.oauth_refresh_btn.clicked.connect(self._refresh_oauth_token)
        self.oauth_refresh_btn.setEnabled(False)
        oauth_btn_layout.addWidget(self.oauth_refresh_btn)
        
        self.oauth_clear_btn = QPushButton("❌ Clear")
        self.oauth_clear_btn.clicked.connect(self._clear_oauth)
        self.oauth_clear_btn.setEnabled(False)
        oauth_btn_layout.addWidget(self.oauth_clear_btn)
        
        oauth_btn_layout.addStretch()
        oauth_layout.addLayout(oauth_btn_layout)
        
        self.oauth_widget.setVisible(False)
        layout.addWidget(self.oauth_widget)
        
        # Separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)
        
        # Request Settings section
        settings_label = QLabel("<b>Request Settings:</b>")
        layout.addWidget(settings_label)
        
        # Timeout setting
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout:"))
        self.timeout_input = QLineEdit()
        self.timeout_input.setPlaceholderText("30")
        self.timeout_input.setMaximumWidth(80)
        self.timeout_input.setText("30")
        self.timeout_input.setToolTip("Request timeout in seconds (default: 30)")
        timeout_layout.addWidget(self.timeout_input)
        timeout_layout.addWidget(QLabel("seconds"))
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)
        
        # SSL verification toggle
        from PyQt6.QtWidgets import QCheckBox
        ssl_layout = QHBoxLayout()
        self.verify_ssl_checkbox = QCheckBox("Verify SSL certificates")
        self.verify_ssl_checkbox.setChecked(True)
        self.verify_ssl_checkbox.setToolTip(
            "Uncheck to disable SSL certificate verification\n"
            "(useful for local development with self-signed certificates)"
        )
        ssl_layout.addWidget(self.verify_ssl_checkbox)
        ssl_layout.addStretch()
        layout.addLayout(ssl_layout)
        
        layout.addStretch()
        
        # OAuth state
        self.current_oauth_config = None
        self.current_oauth_token = None
        
        return widget
    
    def _on_auth_type_changed(self, auth_type: str):
        """Handle authorization type change."""
        self.bearer_token_widget.setVisible(auth_type == 'Bearer Token')
        self.oauth_widget.setVisible(auth_type == 'OAuth 2.0')
        self._update_tab_counts()
    
    # ==================== Collections Tree Management ====================
    
    def _add_folder_and_parents_to_expanded(self, folder_id: int, expanded_folder_ids: set):
        """Recursively add a folder and all its parents to the expanded set."""
        if not folder_id:
            return
        
        expanded_folder_ids.add(folder_id)
        
        # Get the folder to find its parent
        folder = self.db.get_folder(folder_id)
        if folder and folder.get('parent_id'):
            # Recursively add parent folders
            self._add_folder_and_parents_to_expanded(folder.get('parent_id'), expanded_folder_ids)
    
    def _force_expand_folders_recursive(self, item, folder_ids_to_expand: set):
        """Recursively force expansion of specific folders after tree is built."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and isinstance(data, dict):
            if data.get('type') == 'folder' and data.get('id') in folder_ids_to_expand:
                item.setExpanded(True)
        
        # Recurse through children
        for i in range(item.childCount()):
            self._force_expand_folders_recursive(item.child(i), folder_ids_to_expand)
    
    def _ensure_request_visible_in_tree(self, request_id: int):
        """Ensure a request is visible in the collections tree by expanding parent folders."""
        if not request_id:
            return
        
        request = self.db.get_request(request_id)
        if not request:
            return
        
        collection_id = request.get('collection_id')
        folder_id = request.get('folder_id')
        
        # Find and expand the collection
        for i in range(self.collections_tree.topLevelItemCount()):
            collection_item = self.collections_tree.topLevelItem(i)
            data = collection_item.data(0, Qt.ItemDataRole.UserRole)
            
            if data and data.get('type') == 'collection' and data.get('id') == collection_id:
                collection_item.setExpanded(True)
                
                # If request is in a folder, expand all parent folders
                if folder_id:
                    self._expand_folder_hierarchy(collection_item, folder_id)
                
                break
    
    def _expand_folder_hierarchy(self, parent_item: QTreeWidgetItem, target_folder_id: int):
        """Recursively expand folders to make a target folder visible."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            
            if data and data.get('type') == 'folder':
                if data.get('id') == target_folder_id:
                    # Found the target folder, expand it
                    child.setExpanded(True)
                    return True
                else:
                    # Check if target is in this folder's children
                    if self._expand_folder_hierarchy(child, target_folder_id):
                        # Target was found in subfolder, expand this folder too
                        child.setExpanded(True)
                        return True
        
        return False
    
    def _load_collections(self):
        """Load all collections, folders, and requests from database into the tree."""
        from PyQt6.QtGui import QIcon
        
        # Store currently expanded items (collections and folders) before clearing
        expanded_collection_ids = set()
        expanded_folder_ids = set()
        for i in range(self.collections_tree.topLevelItemCount()):
            item = self.collections_tree.topLevelItem(i)
            self._store_expanded_state(item, expanded_collection_ids, expanded_folder_ids)
        
        # Add any folders/collections that should be kept expanded (e.g., after deletion)
        if hasattr(self, '_folders_to_keep_expanded'):
            expanded_folder_ids.update(self._folders_to_keep_expanded)
        if hasattr(self, '_collections_to_keep_expanded'):
            expanded_collection_ids.update(self._collections_to_keep_expanded)
        
        # If there's a current request, ensure its folder will be expanded
        if self.current_request_id:
            request = self.db.get_request(self.current_request_id)
            if request and request.get('folder_id'):
                # Add the folder and all parent folders to expanded set
                folder_id = request.get('folder_id')
                self._add_folder_and_parents_to_expanded(folder_id, expanded_folder_ids)
            # Also ensure the collection is expanded
            if request and request.get('collection_id'):
                expanded_collection_ids.add(request.get('collection_id'))
        
        self.collections_tree.clear()
        collections = self.db.get_all_collections()
        
        # Determine which icons to use based on current stylesheet
        current_stylesheet = self.styleSheet()
        is_dark = 'dark' in current_stylesheet.lower() or '#252526' in current_stylesheet or '#1e1e1e' in current_stylesheet
        collection_icon_path = self._get_icon_path("collection-icon-dark.svg" if is_dark else "collection-icon.svg")
        folder_icon_path = self._get_icon_path("folder-icon-dark.svg" if is_dark else "folder-icon.svg")
        folder_open_icon_path = self._get_icon_path("folder-open-icon-dark.svg" if is_dark else "folder-open-icon.svg")
        
        for collection in collections:
            # Load all requests for this collection (for count)
            all_requests = self.db.get_requests_by_collection(collection['id'])
            request_count = len(all_requests)
            
            # Add sync status icon (🌐 for public/synced, 🔒 for private/local)
            sync_icon = "🌐" if collection.get('sync_to_git', 0) == 1 else "🔒"
            
            # Create collection item with custom icon
            collection_name = f"{sync_icon} {collection['name']} [{request_count}]"
            collection_item = QTreeWidgetItem([collection_name])
            collection_item.setData(0, Qt.ItemDataRole.UserRole, 
                                   {'type': 'collection', 'id': collection['id'], 'name': collection['name']})
            collection_item.setIcon(0, QIcon(collection_icon_path))
            
            # Enable drag & drop for collections
            collection_item.setFlags(
                collection_item.flags() | 
                Qt.ItemFlag.ItemIsDragEnabled | 
                Qt.ItemFlag.ItemIsDropEnabled
            )
            
            # Collection names should NOT be bold by default
            # Bold will be applied only when it contains the active request
            is_dark_theme = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
            text_color = '#CCCCCC' if is_dark_theme else '#424242'
            collection_item.setForeground(0, QBrush(QColor(text_color)))
            
            self.collections_tree.addTopLevelItem(collection_item)
            
            # Load folders for this collection
            folders = self.db.get_folders_by_collection(collection['id'])
            
            # Build folder hierarchy
            folder_items = {}  # folder_id -> QTreeWidgetItem
            root_folders = [f for f in folders if f['parent_id'] is None]
            
            # Create folder items recursively
            def create_folder_item(folder_data, parent_item):
                # Count subfolders and requests recursively
                def count_items(folder_id):
                    subfolder_count = 0
                    request_count = 0
                    
                    # Count direct requests in this folder
                    direct_requests = self.db.get_requests_by_folder(folder_id, folder_data['collection_id'])
                    request_count += len(direct_requests)
                    
                    # Count subfolders and their contents
                    subfolders = [f for f in folders if f['parent_id'] == folder_id]
                    subfolder_count += len(subfolders)
                    
                    for subfolder in subfolders:
                        sub_folder_count, sub_request_count = count_items(subfolder['id'])
                        subfolder_count += sub_folder_count
                        request_count += sub_request_count
                    
                    return subfolder_count, request_count
                
                folder_count, request_count = count_items(folder_data['id'])
                
                # Format folder name with request count only
                folder_name = f"{folder_data['name']} [{request_count}]"
                folder_item = QTreeWidgetItem([folder_name])
                folder_item.setData(0, Qt.ItemDataRole.UserRole,
                                   {'type': 'folder', 'id': folder_data['id'],
                                    'collection_id': folder_data['collection_id'],
                                    'parent_id': folder_data['parent_id'],
                                    'name': folder_data['name']})
                
                # Enable drag & drop for folders
                folder_item.setFlags(
                    folder_item.flags() | 
                    Qt.ItemFlag.ItemIsDragEnabled | 
                    Qt.ItemFlag.ItemIsDropEnabled
                )
                
                # Set icon based on expanded state
                if folder_data['id'] in expanded_folder_ids:
                    folder_item.setIcon(0, QIcon(folder_open_icon_path))
                    folder_item.setExpanded(True)
                else:
                    folder_item.setIcon(0, QIcon(folder_icon_path))
                
                is_dark_theme = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
                text_color = '#CCCCCC' if is_dark_theme else '#424242'
                folder_item.setForeground(0, QBrush(QColor(text_color)))
                
                parent_item.addChild(folder_item)
                folder_items[folder_data['id']] = folder_item
                
                # Add requests in this folder
                folder_requests = self.db.get_requests_by_folder(folder_data['id'], folder_data['collection_id'])
                for request in folder_requests:
                    self._add_request_item_to_tree(request, folder_item, collection['id'])
                
                # Recursively add child folders
                child_folders = [f for f in folders if f['parent_id'] == folder_data['id']]
                for child_folder in child_folders:
                    create_folder_item(child_folder, folder_item)
            
            # Create root-level folders
            for folder in root_folders:
                create_folder_item(folder, collection_item)
            
            # Add requests that are not in any folder (collection root)
            root_requests = self.db.get_requests_by_folder(None, collection['id'])
            for request in root_requests:
                self._add_request_item_to_tree(request, collection_item, collection['id'])
            
            # Restore expanded state
            if collection['id'] in expanded_collection_ids:
                collection_item.setExpanded(True)
        
        # Force expansion of folders that should be kept expanded (second pass after tree is fully built)
        # This ensures Qt doesn't collapse them during tree construction
        if hasattr(self, '_folders_to_keep_expanded') and self._folders_to_keep_expanded:
            for i in range(self.collections_tree.topLevelItemCount()):
                collection_item = self.collections_tree.topLevelItem(i)
                self._force_expand_folders_recursive(collection_item, self._folders_to_keep_expanded)
        
        # Highlight currently opened request
        self._update_current_request_highlight()
        
        # Clear temporary tracking sets after they've been used
        if hasattr(self, '_folders_to_keep_expanded'):
            self._folders_to_keep_expanded.clear()
        if hasattr(self, '_collections_to_keep_expanded'):
            self._collections_to_keep_expanded.clear()
    
    def _store_expanded_state(self, item, expanded_collection_ids, expanded_folder_ids):
        """Recursively store expanded state of collections and folders."""
        if item.isExpanded():
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and isinstance(data, dict):
                item_type = data.get('type')
                item_id = data.get('id')
                if item_type == 'collection':
                    expanded_collection_ids.add(item_id)
                elif item_type == 'folder':
                    expanded_folder_ids.add(item_id)
        
        # Recurse through children
        for i in range(item.childCount()):
            self._store_expanded_state(item.child(i), expanded_collection_ids, expanded_folder_ids)
    
    def _expand_and_show_request(self, request_id: int):
        """Expand the collection containing a request and scroll to make it visible."""
        # Get request info to find its collection
        request = self.db.get_request(request_id)
        if not request:
            return
        
        collection_id = request.get('collection_id')
        if not collection_id:
            return
        
        # Find and expand the collection item in the tree
        for i in range(self.collections_tree.topLevelItemCount()):
            collection_item = self.collections_tree.topLevelItem(i)
            data = collection_item.data(0, Qt.ItemDataRole.UserRole)
            
            if data and data.get('type') == 'collection' and data.get('id') == collection_id:
                # Expand the collection
                collection_item.setExpanded(True)
                
                # Find and scroll to the request item
                self._find_and_scroll_to_request(collection_item, request_id)
                break
    
    def _find_and_scroll_to_request(self, parent_item, request_id: int):
        """Recursively find a request item and scroll to it."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            
            if data and data.get('type') == 'request' and data.get('id') == request_id:
                # Found the request - scroll to it
                self.collections_tree.scrollToItem(child)
                return True
            elif data and data.get('type') == 'folder':
                # This is a folder - expand it and recurse
                child.setExpanded(True)
                if self._find_and_scroll_to_request(child, request_id):
                    return True
        
        return False
    
    def _add_request_item_to_tree(self, request, parent_item, collection_id):
        """Add a request item to the tree under the given parent."""
        method = request['method']
        method_badge = self._get_method_icon(method)
        
        # Create item with badge and name - request name in default gray color
        request_text = f"{method_badge} {request['name']}"
        request_item = QTreeWidgetItem([request_text])
        request_item.setData(0, Qt.ItemDataRole.UserRole,
                            {'type': 'request', 'id': request['id'],
                             'collection_id': collection_id,
                             'folder_id': request.get('folder_id')})
        
        # Enable drag & drop for requests
        request_item.setFlags(
            request_item.flags() | 
            Qt.ItemFlag.ItemIsDragEnabled | 
            Qt.ItemFlag.ItemIsDropEnabled
        )
        
        # Set text color based on theme
        is_dark_theme = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        text_color = '#CCCCCC' if is_dark_theme else '#424242'
        request_item.setForeground(0, QBrush(QColor(text_color)))
        
        parent_item.addChild(request_item)
    
    def _update_tree_item_counts(self, *collection_ids):
        """
        Update the request counts displayed in collection and folder names.
        
        Args:
            *collection_ids: IDs of collections to update. If none provided, updates all.
        """
        # If no collection IDs provided, update all
        if not collection_ids:
            for i in range(self.collections_tree.topLevelItemCount()):
                item = self.collections_tree.topLevelItem(i)
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data and data.get('type') == 'collection':
                    collection_ids = (*collection_ids, data['id'])
        
        # Update each specified collection
        for collection_id in collection_ids:
            # Find collection item in tree
            for i in range(self.collections_tree.topLevelItemCount()):
                item = self.collections_tree.topLevelItem(i)
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data and data.get('type') == 'collection' and data['id'] == collection_id:
                    # Update collection count
                    all_requests = self.db.get_requests_by_collection(collection_id)
                    request_count = len(all_requests)
                    collection_name = f"{data['name']} [{request_count}]"
                    item.setText(0, collection_name)
                    
                    # Update all folder counts in this collection recursively
                    self._update_folder_counts_recursive(item)
                    break
    
    def _update_folder_counts_recursive(self, parent_item):
        """Recursively update request counts for all folders under parent_item."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            
            if data and data.get('type') == 'folder':
                folder_id = data['id']
                collection_id = data['collection_id']
                
                # Count requests recursively with cycle detection
                def count_requests_in_folder(fid, visited=None):
                    if visited is None:
                        visited = set()
                    
                    # Detect circular references
                    if fid in visited:
                        print(f"[WARNING] Circular folder reference detected for folder {fid}")
                        return 0
                    
                    visited.add(fid)
                    
                    count = 0
                    try:
                        # Count direct requests
                        direct_requests = self.db.get_requests_by_folder(fid, collection_id)
                        count += len(direct_requests)
                        
                        # Count requests in subfolders
                        folders = self.db.get_folders_by_collection(collection_id)
                        subfolders = [f for f in folders if f['parent_id'] == fid]
                        for subfolder in subfolders:
                            count += count_requests_in_folder(subfolder['id'], visited.copy())
                    except Exception as e:
                        print(f"[ERROR] Error counting requests in folder {fid}: {e}")
                    
                    return count
                
                request_count = count_requests_in_folder(folder_id)
                folder_name = f"{data['name']} [{request_count}]"
                child.setText(0, folder_name)
                
                # Recurse into subfolders
                self._update_folder_counts_recursive(child)
    
    def _update_current_request_highlight(self):
        """Update the tree to highlight/bold the currently opened request and underline all open requests."""
        from PyQt6.QtGui import QIcon
        
        print(f"[DEBUG] _update_current_request_highlight called")
        
        # Get current request ID from active tab
        current_tab_index = self.request_tabs.currentIndex()
        current_request_id = None
        if current_tab_index >= 0 and current_tab_index in self.tab_states:
            current_request_id = self.tab_states[current_tab_index].get('request_id')
        
        print(f"[DEBUG] Current tab index: {current_tab_index}, current_request_id: {current_request_id}")
        
        # Get all open request IDs from all tabs
        open_request_ids = set()
        for tab_state in self.tab_states.values():
            req_id = tab_state.get('request_id')
            if req_id:
                open_request_ids.add(req_id)
        
        print(f"[DEBUG] Open request IDs: {open_request_ids}")
        
        # Determine which icons to use based on current stylesheet
        current_stylesheet = self.styleSheet()
        is_dark = 'dark' in current_stylesheet.lower() or '#252526' in current_stylesheet or '#1e1e1e' in current_stylesheet
        arrow_icon_path = self._get_icon_path("arrow-right-blue-dark.svg" if is_dark else "arrow-right-blue.svg")
        dot_icon_path = self._get_icon_path("dot-gray-dark.svg" if is_dark else "dot-gray.svg")
        
        # Recursive function to update all children (including nested folders)
        def update_item_recursive(item):
            """Recursively update styling for all children of an item."""
            has_current = False
            has_open = False
            
            for i in range(item.childCount()):
                child = item.child(i)
                child_data = child.data(0, Qt.ItemDataRole.UserRole)
                
                if not child_data or not isinstance(child_data, dict):
                    continue
                
                child_type = child_data.get('type')
                
                if child_type == 'request':
                    request_id = child_data.get('id')
                    
                    # Get original text without any indicators
                    original_text = child.text(0)
                    if ' •' in original_text:
                        original_text = original_text.replace(' •', '')
                    
                    if request_id == current_request_id:
                        # Active request - bold + dot on the right
                        font = child.font(0)
                        font.setBold(True)
                        font.setUnderline(False)
                        child.setFont(0, font)
                        child.setText(0, f"{original_text} •")
                        child.setIcon(0, QIcon())  # Remove left icon
                        has_current = True
                        has_open = True
                    elif request_id in open_request_ids:
                        # Open in another tab - small dot on the right
                        font = child.font(0)
                        font.setBold(False)
                        font.setUnderline(False)
                        child.setFont(0, font)
                        child.setText(0, f"{original_text} •")
                        child.setIcon(0, QIcon())  # Remove left icon
                        has_open = True
                    else:
                        # Not open - remove all styling
                        font = child.font(0)
                        font.setBold(False)
                        font.setUnderline(False)
                        child.setFont(0, font)
                        child.setText(0, original_text)
                        child.setIcon(0, QIcon())
                        
                elif child_type == 'folder':
                    # Recursively check folder's children
                    folder_has_current, folder_has_open = update_item_recursive(child)
                    if folder_has_current:
                        has_current = True
                        has_open = True
                    elif folder_has_open:
                        has_open = True
                    
                    # Update folder styling based on its contents
                    if folder_has_current or folder_has_open:
                        # Folder has open requests - add dot to the end
                        original_text = child.text(0)
                        # Remove any existing dot first
                        if ' •' in original_text:
                            original_text = original_text.replace(' •', '')
                        child.setText(0, f"{original_text} •")
                        
                        font = child.font(0)
                        # Bold if it contains the active request
                        font.setBold(folder_has_current)
                        font.setUnderline(False)
                        child.setFont(0, font)
                    else:
                        # No open requests - remove dot
                        original_text = child.text(0)
                        if ' •' in original_text:
                            child.setText(0, original_text.replace(' •', ''))
                        
                        font = child.font(0)
                        font.setBold(False)
                        font.setUnderline(False)
                        child.setFont(0, font)
            
            return has_current, has_open
        
        # Iterate through all collections
        for i in range(self.collections_tree.topLevelItemCount()):
            collection_item = self.collections_tree.topLevelItem(i)
            
            # Recursively check all children (including nested folders)
            collection_has_current, collection_has_open = update_item_recursive(collection_item)
            
            # Update collection styling - add dot icon in text if has open requests
            if collection_has_current or collection_has_open:
                # Collection has open requests - add dot to the end
                original_text = collection_item.text(0)
                # Remove any existing dot first
                if ' •' in original_text:
                    original_text = original_text.replace(' •', '')
                collection_item.setText(0, f"{original_text} •")
                
                font = collection_item.font(0)
                # Bold if it contains the active request
                font.setBold(collection_has_current)
                font.setUnderline(False)
                collection_item.setFont(0, font)
            else:
                # No open requests - remove dot
                original_text = collection_item.text(0)
                if ' •' in original_text:
                    collection_item.setText(0, original_text.replace(' •', ''))
                
                font = collection_item.font(0)
                font.setBold(False)
                font.setUnderline(False)
                collection_item.setFont(0, font)
    
    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle single-click on tree item - expand/collapse folders or open requests."""
        import time
        
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Check if data exists and is a dictionary
        if not data or not isinstance(data, dict):
            return
        
        item_type = data.get('type')
        if item_type in ('collection', 'folder'):
            # Single-click on collection or folder - toggle expansion
            item.setExpanded(not item.isExpanded())
        elif item_type == 'request':
            # Single-click on request - open it in temporary tab
            request_id = data['id']
            current_time = time.time()
            
            # Ignore if this is a duplicate click within 300ms (debounce)
            if (current_time - self._last_single_click_time < 0.3 and 
                request_id == self._last_single_click_request_id):
                print(f"[DEBUG] Ignoring duplicate single-click on request {request_id}")
                return
            
            # Update last single-click tracking (use separate variables from double-click)
            self._last_single_click_time = current_time
            self._last_single_click_request_id = request_id
            
            print(f"[DEBUG] Single-click on request {request_id}, opening in temporary tab")
            self._open_request_in_new_tab(request_id, is_temporary=True)
    
    def _on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click on tree item - open request in new tab or toggle collection/folder."""
        import time
        
        print(f"[DEBUG] _on_tree_item_double_clicked called")
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Check if data exists and is a dictionary
        if not data or not isinstance(data, dict):
            return
        
        item_type = data.get('type')
        if item_type in ('collection', 'folder'):
            # Double-click on collection - just toggle expansion
            print(f"[DEBUG] Double-click on collection, toggling expansion")
            item.setExpanded(not item.isExpanded())
        elif data.get('type') == 'request':
            request_id = data['id']
            current_time = time.time()
            
            # Check if this request is already open in a temporary tab
            existing_tab = self._find_tab_with_request(request_id)
            is_temp_tab = (existing_tab >= 0 and 
                          existing_tab in self.tab_states and 
                          self.tab_states[existing_tab].get('is_temporary', False))
            
            # Only ignore duplicate double-clicks if NOT converting a temporary tab to permanent
            if not is_temp_tab:
                if (current_time - self._last_double_click_time < 0.5 and 
                    request_id == self._last_double_click_request_id):
                    print(f"[DEBUG] Ignoring duplicate double-click on request {request_id}")
                    return
            
            # Update last double-click tracking
            self._last_double_click_time = current_time
            self._last_double_click_request_id = request_id
            
            # Double-click on request - open in persistent tab (or switch to existing tab and make it persistent)
            print(f"[DEBUG] Double-click on request {request_id}, calling _open_request_in_new_tab with is_temporary=False")
            self._open_request_in_new_tab(request_id, is_temporary=False)
    
    def _on_tree_item_expanded(self, item: QTreeWidgetItem):
        """Handle folder expansion - change icon to open folder."""
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, dict):
            return
        
        # Only update icon for folders
        if data.get('type') == 'folder':
            # Determine which icon to use based on current stylesheet
            current_stylesheet = self.styleSheet()
            is_dark = 'dark' in current_stylesheet.lower() or '#252526' in current_stylesheet or '#1e1e1e' in current_stylesheet
            folder_open_icon_path = self._get_icon_path("folder-open-icon-dark.svg" if is_dark else "folder-open-icon.svg")
            
            from PyQt6.QtGui import QIcon
            item.setIcon(0, QIcon(folder_open_icon_path))
    
    def _on_tree_item_collapsed(self, item: QTreeWidgetItem):
        """Handle folder collapse - change icon to closed folder."""
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, dict):
            return
        
        # Only update icon for folders
        if data.get('type') == 'folder':
            # Determine which icon to use based on current stylesheet
            current_stylesheet = self.styleSheet()
            is_dark = 'dark' in current_stylesheet.lower() or '#252526' in current_stylesheet or '#1e1e1e' in current_stylesheet
            folder_icon_path = self._get_icon_path("folder-icon-dark.svg" if is_dark else "folder-icon.svg")
            
            from PyQt6.QtGui import QIcon
            item.setIcon(0, QIcon(folder_icon_path))
    
    def _handle_tree_reorder(self, dragged_item: QTreeWidgetItem, dragged_data: dict):
        """
        Handle reordering after a drag & drop operation.
        Updates the database with the new order of items.
        Also handles moving items between collections/folders.
        """
        if not dragged_data or not isinstance(dragged_data, dict):
            return
        
        item_type = dragged_data.get('type')
        if not item_type:
            return
        
        # Get the parent of the dragged item (after the drop)
        parent_item = dragged_item.parent()
        
        try:
            if item_type == 'collection':
                # Reorder collections at root level
                collection_ids = []
                for i in range(self.collections_tree.topLevelItemCount()):
                    item = self.collections_tree.topLevelItem(i)
                    data = item.data(0, Qt.ItemDataRole.UserRole)
                    if data and data.get('type') == 'collection':
                        collection_ids.append(data['id'])  # Use 'id' key
                
                if collection_ids:
                    self.db.reorder_collections(collection_ids)
            
            elif item_type == 'folder':
                # Check if folder moved to a new collection or parent folder
                folder_id = dragged_data.get('id')
                old_collection_id = dragged_data.get('collection_id')
                old_parent_id = dragged_data.get('parent_id')
                
                # Determine new parent and collection based on where it was dropped
                new_collection_id = old_collection_id  # Default: same collection
                new_parent_id = old_parent_id  # Default: same parent
                
                if parent_item:
                    parent_data = parent_item.data(0, Qt.ItemDataRole.UserRole)
                    if parent_data:
                        if parent_data.get('type') == 'collection':
                            new_collection_id = parent_data.get('id')
                            new_parent_id = None  # At collection root
                        elif parent_data.get('type') == 'folder':
                            new_parent_id = parent_data.get('id')
                            new_collection_id = parent_data.get('collection_id')
                
                print(f"[FOLDER MOVE] ID={folder_id}, old_collection={old_collection_id}, new_collection={new_collection_id}, old_parent={old_parent_id}, new_parent={new_parent_id}")
                
                # Update folder's collection_id and/or parent_id if moved
                if new_collection_id != old_collection_id or new_parent_id != old_parent_id:
                    # Folder moved to different collection or parent
                    print(f"[MOVE] Folder {folder_id} moved to collection {new_collection_id}, parent {new_parent_id}")
                    cursor = self.db.connection.cursor()
                    cursor.execute("UPDATE folders SET collection_id = ?, parent_id = ? WHERE id = ?",
                                 (new_collection_id, new_parent_id, folder_id))
                    self.db.connection.commit()
                    
                    # Verify the update
                    cursor.execute("SELECT collection_id, parent_id FROM folders WHERE id = ?", (folder_id,))
                    result = cursor.fetchone()
                    if result:
                        print(f"[DB VERIFY] Folder {folder_id} in DB: collection_id={result[0]}, parent_id={result[1]}")
                    else:
                        print(f"[DB ERROR] Folder {folder_id} not found in database!")
                else:
                    print(f"[NO MOVE] Folder {folder_id} - same position (old_parent={old_parent_id}, new_parent={new_parent_id})")
                
                # Now reorder folders in the new parent
                if new_collection_id:
                    folder_ids = []
                    if parent_item:  # Inside a folder or collection
                        for i in range(parent_item.childCount()):
                            child = parent_item.child(i)
                            child_data = child.data(0, Qt.ItemDataRole.UserRole)
                            if child_data and child_data.get('type') == 'folder':
                                folder_ids.append(child_data['id'])
                    
                    if folder_ids:
                        self.db.reorder_folders(new_collection_id, folder_ids)
            
            elif item_type == 'request':
                # Check if request moved to a new collection or folder
                request_id = dragged_data.get('id')
                old_collection_id = dragged_data.get('collection_id')
                old_folder_id = dragged_data.get('folder_id')
                
                # Determine new parent (folder or collection)
                new_collection_id = None
                new_folder_id = None
                
                if parent_item:
                    parent_data = parent_item.data(0, Qt.ItemDataRole.UserRole)
                    if parent_data:
                        if parent_data.get('type') == 'collection':
                            new_collection_id = parent_data.get('id')
                            new_folder_id = None  # At collection root
                        elif parent_data.get('type') == 'folder':
                            new_folder_id = parent_data.get('id')
                            new_collection_id = parent_data.get('collection_id')
                
                # Update request's collection_id and/or folder_id if moved
                if new_collection_id is not None and (new_collection_id != old_collection_id or new_folder_id != old_folder_id):
                    print(f"[MOVE] Request {request_id} moved to collection {new_collection_id}, folder {new_folder_id}")
                    cursor = self.db.connection.cursor()
                    cursor.execute("UPDATE requests SET collection_id = ?, folder_id = ? WHERE id = ?",
                                 (new_collection_id, new_folder_id, request_id))
                    self.db.connection.commit()
                
                # Now reorder requests in the new parent
                if new_collection_id is not None:
                    request_ids = []
                    if parent_item:
                        for i in range(parent_item.childCount()):
                            child = parent_item.child(i)
                            child_data = child.data(0, Qt.ItemDataRole.UserRole)
                            if child_data and child_data.get('type') == 'request':
                                request_ids.append(child_data['id'])
                    
                    if request_ids:
                        self.db.reorder_requests(new_collection_id, new_folder_id, request_ids)
            
            # For moves that change parent relationships, reload the entire tree to ensure counts are correct
            # This is simpler and more reliable than tracking all affected folders
            should_reload = False
            
            if item_type == 'folder':
                old_parent_id = dragged_data.get('parent_id')
                new_parent_id = None
                if parent_item:
                    parent_data = parent_item.data(0, Qt.ItemDataRole.UserRole)
                    if parent_data and parent_data.get('type') == 'folder':
                        new_parent_id = parent_data.get('id')
                
                print(f"[RELOAD CHECK] Folder: old_parent={old_parent_id}, new_parent={new_parent_id}")
                # If parent changed, need to update counts
                if old_parent_id != new_parent_id:
                    should_reload = True
                    print(f"[RELOAD] Triggering reload due to folder parent change")
            
            elif item_type == 'request':
                old_collection_id = dragged_data.get('collection_id')
                old_folder_id = dragged_data.get('folder_id')
                new_collection_id = None
                new_folder_id = None
                
                if parent_item:
                    parent_data = parent_item.data(0, Qt.ItemDataRole.UserRole)
                    if parent_data:
                        if parent_data.get('type') == 'collection':
                            new_collection_id = parent_data.get('id')
                        elif parent_data.get('type') == 'folder':
                            new_folder_id = parent_data.get('id')
                            new_collection_id = parent_data.get('collection_id')
                
                print(f"[RELOAD CHECK] Request: old_collection={old_collection_id}, new_collection={new_collection_id}, old_folder={old_folder_id}, new_folder={new_folder_id}")
                # If collection or folder changed, need to update counts
                if new_collection_id != old_collection_id or new_folder_id != old_folder_id:
                    should_reload = True
                    print(f"[RELOAD] Triggering reload due to request move")
            
            # Reload tree if items were moved between parents
            if should_reload:
                print("[INFO] Reloading tree to update counts after move")
                
                # Before reloading, ensure affected folders and collections stay expanded
                if not hasattr(self, '_folders_to_keep_expanded'):
                    self._folders_to_keep_expanded = set()
                if not hasattr(self, '_collections_to_keep_expanded'):
                    self._collections_to_keep_expanded = set()
                
                if item_type == 'folder':
                    # Keep the moved folder's parent expanded (if it has one)
                    old_parent_id = dragged_data.get('parent_id')
                    if old_parent_id:
                        self._folders_to_keep_expanded.add(old_parent_id)
                    
                    # Keep the destination folder expanded (if dropped into a folder)
                    if parent_item:
                        parent_data = parent_item.data(0, Qt.ItemDataRole.UserRole)
                        if parent_data:
                            if parent_data.get('type') == 'folder':
                                self._folders_to_keep_expanded.add(parent_data.get('id'))
                            elif parent_data.get('type') == 'collection':
                                self._collections_to_keep_expanded.add(parent_data.get('id'))
                
                elif item_type == 'request':
                    # Keep both old and new parent folders/collections expanded
                    old_folder_id = dragged_data.get('folder_id')
                    old_collection_id = dragged_data.get('collection_id')
                    
                    if old_folder_id:
                        self._folders_to_keep_expanded.add(old_folder_id)
                    if old_collection_id:
                        self._collections_to_keep_expanded.add(old_collection_id)
                    
                    if parent_item:
                        parent_data = parent_item.data(0, Qt.ItemDataRole.UserRole)
                        if parent_data:
                            if parent_data.get('type') == 'folder':
                                self._folders_to_keep_expanded.add(parent_data.get('id'))
                                # Also keep the folder's collection expanded
                                if parent_data.get('collection_id'):
                                    self._collections_to_keep_expanded.add(parent_data.get('collection_id'))
                            elif parent_data.get('type') == 'collection':
                                self._collections_to_keep_expanded.add(parent_data.get('id'))
                
                # If there's a current open request, ensure its folder stays expanded
                if self.current_request_id:
                    current_request = self.db.get_request(self.current_request_id)
                    if current_request:
                        if current_request.get('folder_id'):
                            self._folders_to_keep_expanded.add(current_request.get('folder_id'))
                        if current_request.get('collection_id'):
                            self._collections_to_keep_expanded.add(current_request.get('collection_id'))
                
                self._load_collections()
                
                # Clear the kept expanded folders/collections after reload
                self._folders_to_keep_expanded.clear()
                self._collections_to_keep_expanded.clear()
        
        except Exception as e:
            print(f"Error reordering items: {e}")
            import traceback
            traceback.print_exc()
            # Reload tree to restore correct order
            self._load_collections()
    
    def _show_tree_context_menu(self, position):
        """Show context menu for collections tree."""
        item = self.collections_tree.itemAt(position)
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, dict):
            return
        
        menu = QMenu(self)
        item_type = data.get('type')
        
        if item_type == 'collection':
            # Collection context menu
            add_folder_action = QAction("📁 Add Folder", self)
            add_folder_action.triggered.connect(lambda: self._add_folder_to_collection(data['id']))
            menu.addAction(add_folder_action)
            
            add_request_action = QAction("➕ Add Request", self)
            add_request_action.triggered.connect(lambda: self._add_request_to_collection(data['id']))
            menu.addAction(add_request_action)
            
            menu.addSeparator()
            
            variables_action = QAction("🔧 Manage Variables", self)
            variables_action.triggered.connect(lambda: self._manage_collection_variables(data['id']))
            menu.addAction(variables_action)
            
            menu.addSeparator()
            
            # Add sync status actions
            collection_id = data['id']
            collection = self.db.get_collection(collection_id)
            if collection:
                is_public = collection.get('sync_to_git', 0) == 1
                if is_public:
                    make_private_action = QAction("🔒 Make Private (Don't Sync)", self)
                    make_private_action.triggered.connect(lambda: self._toggle_collection_sync_status(collection_id, 0))
                    menu.addAction(make_private_action)
                else:
                    make_public_action = QAction("🌐 Make Public (Sync to Git)", self)
                    make_public_action.triggered.connect(lambda: self._toggle_collection_sync_status(collection_id, 1))
                    menu.addAction(make_public_action)
            
            menu.addSeparator()
            
            export_action = QAction("📤 Export Collection", self)
            export_action.triggered.connect(lambda: self._export_collection_from_menu(data['id']))
            menu.addAction(export_action)
            
            run_tests_action = QAction("▶️ Run All Tests", self)
            run_tests_action.triggered.connect(lambda: self._run_collection_tests_from_menu(data['id']))
            menu.addAction(run_tests_action)
            
            menu.addSeparator()
            
            rename_action = QAction("✏️ Rename", self)
            rename_action.triggered.connect(lambda: self._rename_collection(data['id']))
            menu.addAction(rename_action)
            
            duplicate_action = QAction("📑 Duplicate", self)
            duplicate_action.triggered.connect(lambda: self._duplicate_collection(data['id']))
            menu.addAction(duplicate_action)
            
            menu.addSeparator()
            
            delete_action = QAction("🗑️ Delete", self)
            delete_action.triggered.connect(lambda: self._delete_collection_from_menu(data['id']))
            menu.addAction(delete_action)
            
        elif item_type == 'folder':
            # Folder context menu
            folder_id = data['id']
            collection_id = data['collection_id']
            
            add_folder_action = QAction("📁 Add Subfolder", self)
            add_folder_action.triggered.connect(lambda checked=False, fid=folder_id, cid=collection_id: self._add_folder_to_folder(cid, fid))
            menu.addAction(add_folder_action)
            
            add_request_action = QAction("➕ Add Request", self)
            add_request_action.triggered.connect(lambda checked=False, fid=folder_id, cid=collection_id: self._add_request_to_folder(cid, fid))
            menu.addAction(add_request_action)
            
            menu.addSeparator()
            
            rename_action = QAction("✏️ Rename", self)
            rename_action.triggered.connect(lambda checked=False, fid=folder_id: self._rename_folder(fid))
            menu.addAction(rename_action)
            
            menu.addSeparator()
            
            delete_action = QAction("🗑️ Delete", self)
            delete_action.triggered.connect(lambda checked=False, fid=folder_id: self._delete_folder_from_menu(fid))
            menu.addAction(delete_action)
            
        elif item_type == 'request':
            # Request context menu
            request_id = data['id']  # Capture in local variable to avoid closure issues
            collection_id = data['collection_id']
            
            open_action = QAction("📂 Open", self)
            open_action.triggered.connect(lambda checked=False, rid=request_id: self._load_request(rid))
            menu.addAction(open_action)
            
            open_new_tab_action = QAction("🗂️ Open in New Tab", self)
            open_new_tab_action.triggered.connect(lambda checked=False, rid=request_id: self._open_request_in_new_tab(rid))
            menu.addAction(open_new_tab_action)
            
            menu.addSeparator()
            
            # Move to folder submenu
            move_menu = QMenu("📂 Move to", self)
            
            # Add "Collection Root" option
            move_to_root_action = QAction("📦 Collection Root", self)
            move_to_root_action.triggered.connect(lambda checked=False, rid=request_id: self._move_request_to_folder(rid, None))
            move_menu.addAction(move_to_root_action)
            
            # Add folders
            folders = self.db.get_folders_by_collection(collection_id)
            if folders:
                move_menu.addSeparator()
                for folder in folders:
                    folder_action = QAction(f"📁 {folder['name']}", self)
                    folder_id = folder['id']
                    folder_action.triggered.connect(lambda checked=False, rid=request_id, fid=folder_id: self._move_request_to_folder(rid, fid))
                    move_menu.addAction(folder_action)
            
            menu.addMenu(move_menu)
            
            menu.addSeparator()
            
            copy_curl_action = QAction("📋 Copy as cURL", self)
            copy_curl_action.triggered.connect(lambda checked=False, rid=request_id: self._copy_request_as_curl(rid))
            menu.addAction(copy_curl_action)
            
            menu.addSeparator()
            
            rename_action = QAction("✏️ Rename", self)
            rename_action.triggered.connect(lambda checked=False, rid=request_id: self._rename_request(rid))
            menu.addAction(rename_action)
            
            duplicate_action = QAction("📑 Duplicate", self)
            duplicate_action.triggered.connect(lambda checked=False, rid=request_id: self._duplicate_request(rid))
            menu.addAction(duplicate_action)
            
            menu.addSeparator()
            
            delete_action = QAction("🗑️ Delete", self)
            delete_action.triggered.connect(lambda checked=False, rid=request_id: self._delete_request_from_menu(rid))
            menu.addAction(delete_action)
        
        menu.exec(self.collections_tree.viewport().mapToGlobal(position))
    
    def _get_unique_collection_name(self, base_name: str) -> str:
        """Generate a unique collection name by appending a number if needed."""
        existing_collections = self.db.get_all_collections()
        existing_names = {col['name'] for col in existing_collections}
        
        # If base name is unique, return it
        if base_name not in existing_names:
            return base_name
        
        # Otherwise, find the next available number
        counter = 2
        while f"{base_name} ({counter})" in existing_names:
            counter += 1
        
        return f"{base_name} ({counter})"
    
    def _get_unique_request_name(self, collection_id: int, base_name: str, method: str) -> str:
        """Generate a unique request name within a collection by appending a number if needed.
        
        Considers both name AND method when checking for duplicates, so 'Users' for GET and POST
        are considered different requests.
        """
        existing_requests = self.db.get_requests_by_collection(collection_id)
        # Create set of (name, method) tuples for same-method requests
        existing_names = {req['name'] for req in existing_requests if req['method'] == method}
        
        # If base name is unique for this method, return it
        if base_name not in existing_names:
            return base_name
        
        # Otherwise, find the next available number
        counter = 2
        while f"{base_name} ({counter})" in existing_names:
            counter += 1
        
        return f"{base_name} ({counter})"
    
    def _check_duplicate_request_name(self, collection_id: int, name: str, method: str) -> tuple[bool, str]:
        """Check if a request name already exists and suggest a unique alternative.
        
        Returns:
            (is_duplicate, suggested_name)
        """
        existing_requests = self.db.get_requests_by_collection(collection_id)
        existing_names = {req['name'] for req in existing_requests if req['method'] == method}
        
        is_duplicate = name in existing_names
        suggested_name = self._get_unique_request_name(collection_id, name, method) if is_duplicate else name
        
        return is_duplicate, suggested_name
    
    def _add_collection(self):
        """Add a new collection via dialog."""
        name, ok = QInputDialog.getText(self, "New Collection", "Collection name:")
        if ok and name.strip():
            name = name.strip()
            
            # Check if name already exists
            existing_collections = self.db.get_all_collections()
            existing_names = {col['name'] for col in existing_collections}
            
            if name in existing_names:
                # Suggest a unique name
                suggested_name = self._get_unique_collection_name(name)
                
                # Ask user if they want to use the suggested name
                reply = QMessageBox.question(
                    self,
                    "Collection Already Exists",
                    f"A collection named '{name}' already exists.\n\n"
                    f"Would you like to create it as '{suggested_name}' instead?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    name = suggested_name
                else:
                    # Let user enter a different name
                    return self._add_collection()
            
            try:
                self.db.create_collection(name)
                self._auto_sync_to_filesystem()
                self._load_collections()
                # Show success status
                self._show_status(f"Collection '{name}' created", "success")
            except Exception as e:
                self._show_status(f"Failed to create collection: {str(e)[:30]}...", "error")
                QMessageBox.critical(self, "Error", f"Failed to create collection: {str(e)}")
    
    def _add_request(self):
        """Add a new request to the currently selected collection."""
        if not self.current_collection_id:
            QMessageBox.warning(self, "Warning", "Please select a collection first!")
            return
        
        # Check for unsaved changes before creating new request
        if not self._check_unsaved_changes():
            return
        
        # Get collection name to show in prompt
        collection = self.db.get_collection(self.current_collection_id)
        collection_name = collection.get('name', 'Unknown') if collection else 'Unknown'
        
        name, ok = QInputDialog.getText(
            self, 
            "New Request", 
            f"Request name (will be added to '{collection_name}'):"
        )
        if ok and name.strip():
            name = name.strip()
            method = 'GET'  # Default method for new requests
            
            # Check for duplicate name
            is_duplicate, suggested_name = self._check_duplicate_request_name(
                self.current_collection_id, name, method
            )
            
            if is_duplicate:
                reply = QMessageBox.question(
                    self,
                    "Request Already Exists",
                    f"A [GET] request named '{name}' already exists in this collection.\n\n"
                    f"Would you like to create it as '{suggested_name}' instead?\n\n"
                    f"Note: Having multiple requests with the same name can be confusing.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    name = suggested_name
                else:
                    # Let user try again
                    return self._add_request()
            
            try:
                request_id = self.db.create_request(
                    collection_id=self.current_collection_id,
                    name=name,
                    method=method,
                    url='',
                    body_type='raw'
                )
                self._load_collections()
                
                # Load the newly created request and show workspace
                self.current_request_id = request_id
                self.center_stack.setCurrentWidget(self.tabs_container)
                self._load_request(request_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create request: {str(e)}")
    
    def _add_request_to_collection(self, collection_id: int):
        """Add a new request to a specific collection (from context menu)."""
        # Check for unsaved changes before creating new request
        if not self._check_unsaved_changes():
            return
        
        # Get collection name to show in prompt
        collection = self.db.get_collection(collection_id)
        collection_name = collection.get('name', 'Unknown') if collection else 'Unknown'
        
        name, ok = QInputDialog.getText(
            self, 
            "New Request", 
            f"Request name (will be added to '{collection_name}'):"
        )
        if ok and name.strip():
            name = name.strip()
            method = 'GET'  # Default method for new requests
            
            # Check for duplicate name
            is_duplicate, suggested_name = self._check_duplicate_request_name(
                collection_id, name, method
            )
            
            if is_duplicate:
                reply = QMessageBox.question(
                    self,
                    "Request Already Exists",
                    f"A [GET] request named '{name}' already exists in this collection.\n\n"
                    f"Would you like to create it as '{suggested_name}' instead?\n\n"
                    f"Note: Having multiple requests with the same name can be confusing.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    name = suggested_name
                else:
                    # Let user try again
                    return self._add_request_to_collection(collection_id)
            
            try:
                request_id = self.db.create_request(
                    collection_id=collection_id,
                    name=name,
                    method=method,
                    url='',
                    body_type='raw'
                )
                self._load_collections()
                self._show_status(f"Request '{name}' created", "success")
                
                # Load the newly created request and show workspace
                self.current_request_id = request_id
                self.current_collection_id = collection_id
                self.center_stack.setCurrentWidget(self.tabs_container)
                self._load_request(request_id)
            except Exception as e:
                self._show_status(f"Failed to create request: {str(e)[:50]}...", "error")
                QMessageBox.critical(self, "Error", f"Failed to create request: {str(e)}")
    
    # ==================== Folder Management ====================
    
    def _add_folder_to_collection(self, collection_id: int):
        """Add a new folder to a collection root."""
        collection = self.db.get_collection(collection_id)
        collection_name = collection.get('name', 'Unknown') if collection else 'Unknown'
        
        name, ok = QInputDialog.getText(
            self,
            "New Folder",
            f"Folder name (will be added to '{collection_name}'):"
        )
        if ok and name.strip():
            try:
                self.db.create_folder(collection_id, name.strip())
                # Keep the collection expanded after adding folder
                if not hasattr(self, '_collections_to_keep_expanded'):
                    self._collections_to_keep_expanded = set()
                self._collections_to_keep_expanded.add(collection_id)
                self._load_collections()
                self._show_status(f"Folder '{name}' created", "success")
            except Exception as e:
                self._show_status(f"Failed to create folder: {str(e)[:50]}...", "error")
                QMessageBox.critical(self, "Error", f"Failed to create folder: {str(e)}")
    
    def _add_folder_to_folder(self, collection_id: int, parent_folder_id: int):
        """Add a subfolder to an existing folder."""
        parent_folder = self.db.get_folder(parent_folder_id)
        parent_name = parent_folder.get('name', 'Unknown') if parent_folder else 'Unknown'
        
        name, ok = QInputDialog.getText(
            self,
            "New Subfolder",
            f"Subfolder name (will be added to '{parent_name}'):"
        )
        if ok and name.strip():
            try:
                self.db.create_folder(collection_id, name.strip(), parent_folder_id)
                # Keep the parent folder AND all its parents expanded after adding subfolder
                if not hasattr(self, '_folders_to_keep_expanded'):
                    self._folders_to_keep_expanded = set()
                # Add parent folder and all its ancestors
                self._add_folder_and_parents_to_expanded(parent_folder_id, self._folders_to_keep_expanded)
                if not hasattr(self, '_collections_to_keep_expanded'):
                    self._collections_to_keep_expanded = set()
                self._collections_to_keep_expanded.add(collection_id)
                self._load_collections()
                self._show_status(f"Subfolder '{name}' created", "success")
            except Exception as e:
                self._show_status(f"Failed to create subfolder: {str(e)[:50]}...", "error")
                QMessageBox.critical(self, "Error", f"Failed to create subfolder: {str(e)}")
    
    def _add_request_to_folder(self, collection_id: int, folder_id: int):
        """Add a new request to a specific folder."""
        folder = self.db.get_folder(folder_id)
        folder_name = folder.get('name', 'Unknown') if folder else 'Unknown'
        
        name, ok = QInputDialog.getText(
            self,
            "New Request",
            f"Request name (will be added to folder '{folder_name}'):"
        )
        if ok and name.strip():
            name = name.strip()
            method = 'GET'
            
            try:
                request_id = self.db.create_request(
                    collection_id=collection_id,
                    name=name,
                    method=method,
                    url='',
                    body_type='raw'
                )
                # Move request to folder
                self.db.move_request_to_folder(request_id, folder_id)
                self._load_collections()
                self._show_status(f"Request '{name}' created in folder '{folder_name}'", "success")
                
                # Load the newly created request
                self.current_request_id = request_id
                self.current_collection_id = collection_id
                self.center_stack.setCurrentWidget(self.tabs_container)
                self._load_request(request_id)
            except Exception as e:
                self._show_status(f"Failed to create request: {str(e)[:50]}...", "error")
                QMessageBox.critical(self, "Error", f"Failed to create request: {str(e)}")
    
    def _rename_folder(self, folder_id: int):
        """Rename a folder."""
        folder = self.db.get_folder(folder_id)
        if not folder:
            QMessageBox.warning(self, "Error", "Folder not found!")
            return
        
        name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            "New folder name:",
            text=folder['name']
        )
        if ok and name.strip():
            try:
                self.db.update_folder(folder_id, name=name.strip())
                self._load_collections()
                self._show_status(f"Folder renamed to '{name}'", "success")
            except Exception as e:
                self._show_status(f"Failed to rename folder: {str(e)[:50]}...", "error")
                QMessageBox.critical(self, "Error", f"Failed to rename folder: {str(e)}")
    
    def _delete_folder_from_menu(self, folder_id: int):
        """Delete a folder (from context menu)."""
        folder = self.db.get_folder(folder_id)
        if not folder:
            QMessageBox.warning(self, "Error", "Folder not found!")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete folder '{folder['name']}'?\n\n"
            "All subfolders and requests inside will also be deleted!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_folder(folder_id)
                self._load_collections()
                self._show_status(f"Folder '{folder['name']}' deleted", "success")
            except Exception as e:
                self._show_status(f"Failed to delete folder: {str(e)[:50]}...", "error")
                QMessageBox.critical(self, "Error", f"Failed to delete folder: {str(e)}")
    
    def _move_request_to_folder(self, request_id: int, folder_id: Optional[int]):
        """Move a request to a folder (or collection root if folder_id is None)."""
        try:
            self.db.move_request_to_folder(request_id, folder_id)
            self._load_collections()
            
            if folder_id is None:
                self._show_status("Request moved to collection root", "success")
            else:
                folder = self.db.get_folder(folder_id)
                folder_name = folder.get('name', 'folder') if folder else 'folder'
                self._show_status(f"Request moved to '{folder_name}'", "success")
        except Exception as e:
            self._show_status(f"Failed to move request: {str(e)[:50]}...", "error")
            QMessageBox.critical(self, "Error", f"Failed to move request: {str(e)}")
    
    def _manage_collection_variables(self, collection_id: int):
        """Show collection variables management dialog."""
        from src.ui.dialogs.collection_variables_dialog import CollectionVariablesDialog
        
        collection = self.db.get_collection(collection_id)
        collection_name = collection.get('name', 'Unknown') if collection else 'Unknown'
        
        dialog = CollectionVariablesDialog(self, self.db, collection_id, collection_name)
        dialog.exec()
    
    def _toggle_collection_sync_status(self, collection_id: int, sync_to_git: int):
        """Toggle sync status of a collection between public (1) and private (0)."""
        try:
            self.db.set_collection_sync_status(collection_id, sync_to_git)
            status_text = "public (will sync to Git)" if sync_to_git == 1 else "private (local only)"
            collection = self.db.get_collection(collection_id)
            collection_name = collection.get('name', 'Collection') if collection else 'Collection'
            self._show_status(f"Collection '{collection_name}' marked as {status_text}", "success")
            
            # Reload tree to update icon
            self._load_collections()
            
            # Auto-sync to filesystem if Git sync is enabled
            if sync_to_git == 1:
                # Making public - export to Git
                self._auto_sync_to_filesystem()
            else:
                # Making private - remove from Git
                if hasattr(self, 'git_sync_manager') and self.git_sync_manager:
                    success, message = self.git_sync_manager.remove_collection_file(collection_id)
                    if success:
                        self._show_status(f"Removed '{collection_name}' from Git sync folder", "success")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update sync status: {str(e)}")
    
    def _delete_selected(self):
        """Delete the currently selected collection, folder, or request."""
        current_item = self.collections_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select an item to delete!")
            return
        
        data = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Check if data exists and is valid
        if not data or not isinstance(data, dict) or 'type' not in data:
            QMessageBox.warning(self, "Warning", "Invalid item selected!")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete this {data['type']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                item_name = current_item.text(0)
                if data['type'] == 'collection':
                    self.db.delete_collection(data['id'])
                    self.current_collection_id = None
                    self.current_request_id = None
                    self._clear_request_editor()
                    self.center_stack.setCurrentWidget(self.no_request_empty_state)
                    self._show_status(f"Collection '{item_name}' deleted", "success")
                elif data['type'] == 'folder':
                    self.db.delete_folder(data['id'])
                    self._show_status(f"Folder '{item_name}' deleted", "success")
                elif data['type'] == 'request':
                    self.db.delete_request(data['id'])
                    if self.current_request_id == data['id']:
                        self.current_request_id = None
                        self._clear_request_editor()
                        self.center_stack.setCurrentWidget(self.no_request_empty_state)
                    self._show_status(f"Request '{item_name}' deleted", "success")
                    # Refresh recent requests to remove deleted entry
                    self.recent_requests_widget.refresh()
                
                # Auto-sync to filesystem if Git sync is enabled
                self._auto_sync_to_filesystem()
                
                self._load_collections()
            except Exception as e:
                self._show_status(f"Failed to delete: {str(e)[:30]}...", "error")
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")
    
    # ==================== Request Editor Management ====================
    
    def _load_request(self, request_id: int):
        """Load a request's details into the editor in temporary mode.
        If the request is already open in a tab, switch to that tab.
        Otherwise, open it in a new temporary tab."""
        try:
            # Open the request in temporary tab mode (will switch if already open)
            # This also handles loading the request data via _on_tab_changed
            self._open_request_in_new_tab(request_id, is_temporary=True)
            
            # Track in recent requests
            self.recent_requests_widget.add_request(request_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load request: {str(e)}")
    
    def _load_request_persistent(self, request_id: int):
        """Load a request's details into the editor in persistent mode (e.g., from double-click in recent requests).
        If the request is already open in a tab, switch to that tab and make it persistent.
        Otherwise, open it in a new persistent tab."""
        try:
            # Open the request in persistent tab mode (not temporary)
            # This also handles loading the request data via _on_tab_changed
            self._open_request_in_new_tab(request_id, is_temporary=False)
            
            # Track in recent requests
            self.recent_requests_widget.add_request(request_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load request: {str(e)}")
    
    def _load_request_data(self, request_id: int):
        """Internal method to load request data into the current tab.
        This should only be called when we're sure we want to load into the current tab."""
        try:
            # Now load the request data
            request = self.db.get_request(request_id)
            if not request:
                QMessageBox.warning(self, "Warning", "Request not found!")
                return
            
            # Block all signals during restoration to prevent marking as modified
            print(f"[DEBUG] Blocking signals for _load_request_data")
            self.method_combo.blockSignals(True)
            self.url_input.blockSignals(True)
            self.params_table.blockSignals(True)
            self.headers_table.blockSignals(True)
            self.body_input.blockSignals(True)
            self.auth_type_combo.blockSignals(True)
            self.auth_token_input.blockSignals(True)
            # description_input removed - now using _current_description string
            self.test_tab.blockSignals(True)
            self.scripts_tab.blockSignals(True)
            
            # Store current request info for later use
            self.current_request_id = request_id
            self.current_collection_id = request.get('collection_id')
            self.current_request_name = request.get('name', 'Unnamed Request')
            self.current_folder_id = request.get('folder_id')  # Track folder
            collection = self.db.get_collection(request.get('collection_id'))
            self.current_collection_name = collection.get('name', 'Unknown Collection') if collection else 'Unknown Collection'
            
            # Load basic info
            self.method_combo.setCurrentText(request.get('method', 'GET'))
            # Initialize method styling
            self._update_method_style(request.get('method', 'GET'))
            self.url_input.setText(request.get('url', ''))
            
            # Load params (handle None)
            params = request.get('params')
            if params is None:
                params = {}
            self._load_dict_to_table(params, self.params_table)
            
            # Load headers (handle None)
            headers = request.get('headers')
            if headers is None:
                headers = {}
            self._load_dict_to_table(headers, self.headers_table)
            
            # Load body
            body = request.get('body', '') or ''
            self.body_input.setPlainText(body)
            
            # Load body type
            body_type = request.get('body_type', 'raw')
            self.body_type_combo.blockSignals(True)
            self.body_type_combo.setCurrentText(body_type)
            self.body_type_combo.blockSignals(False)
            self._update_body_editor_for_type(body_type)
            
            # Load auth
            auth_type = request.get('auth_type', 'None')
            self.auth_type_combo.setCurrentText(auth_type)
            auth_token = request.get('auth_token', '') or ''
            self.auth_token_input.setText(auth_token)
            # Manually update widget visibility since signals are blocked
            self.bearer_token_widget.setVisible(auth_type == 'Bearer Token')
            self.oauth_widget.setVisible(auth_type == 'OAuth 2.0')
            
            # Load description
            description = request.get('description', '') or ''
            self._current_description = description
            self._update_description_button_style()
            
            # Load test assertions
            self._load_test_assertions(request_id)
            
            # Load scripts and clear console
            pre_request_script = request.get('pre_request_script', '') or ''
            post_response_script = request.get('post_response_script', '') or ''
            self.scripts_tab.load_scripts(pre_request_script, post_response_script)
            # Always clear console when loading a request
            self.scripts_tab._clear_console()
            
            # Load cookies from database
            self.cookies_tab.load_cookies()
            
            # Update tab indicators after loading
            self._update_tab_indicators()
            # Explicitly update script toggle indicators
            self.scripts_tab.update_toggle_indicators()
            
            # Clear test results
            self.test_results_viewer.clear()
            self._current_test_results = None  # Clear stored test results
            # Hide test results tab when loading a new request
            if hasattr(self, 'test_results_tab_index'):
                self.response_tabs.setTabVisible(self.test_results_tab_index, False)
            
            # Clear response viewer - fresh request has no response yet
            self._clear_response_viewer()
            
            # Store original data for change detection
            self._store_original_request_data()
            
            # Reset unsaved changes flag and update title
            self.has_unsaved_changes = False
            self._update_request_title()
            
            # Update tab counts
            self._update_tab_counts()
            
            # Track in recent requests
            self.recent_requests_widget.add_request(request_id)
            
            # Update current tab state and title
            current_tab_index = self.request_tabs.currentIndex()
            if current_tab_index >= 0 and current_tab_index in self.tab_states:
                self.tab_states[current_tab_index]['request_id'] = request_id
                self.tab_states[current_tab_index]['name'] = self.current_request_name
                self.tab_states[current_tab_index]['method'] = request.get('method', 'GET')
                self.tab_states[current_tab_index]['has_changes'] = False
                self._update_tab_title(current_tab_index)
            
            # Update collections tree highlighting
            self._update_current_request_highlight()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load request: {str(e)}")
        finally:
            # Always unblock signals after loading
            print(f"[DEBUG] Unblocking signals after _load_request_data")
            self.method_combo.blockSignals(False)
            self.url_input.blockSignals(False)
            self.params_table.blockSignals(False)
            self.headers_table.blockSignals(False)
            self.body_input.blockSignals(False)
            self.auth_type_combo.blockSignals(False)
            self.auth_token_input.blockSignals(False)
            # description_input removed - now using _current_description string
            self.test_tab.blockSignals(False)
            self.scripts_tab.blockSignals(False)
    
    def _clear_request_editor(self):
        """Clear all fields in the request editor."""
        self.method_combo.setCurrentText('GET')
        self.url_input.clear()
        self.test_tab.clear()
        self.scripts_tab.clear_all()
        self.test_results_viewer.clear()
        # Hide test results tab when clearing
        if hasattr(self, 'test_results_tab_index'):
            self.response_tabs.setTabVisible(self.test_results_tab_index, False)
        self.params_table.clearContents()
        self.params_table.setRowCount(1)  # Reset to 1 empty row
        self.headers_table.clearContents()
        self.headers_table.setRowCount(1)  # Reset to 1 empty row
        self.body_input.clear()
        self.auth_type_combo.setCurrentText('None')
        self.auth_token_input.clear()
        self._current_description = ""  # Clear description string
        self._update_description_button_style()  # Update button to show empty state
        self.timeout_input.setText("30")
        self.verify_ssl_checkbox.setChecked(True)
        self._clear_response_viewer()
        
        # Reset tracking variables
        self.current_request_id = None
        self.current_request_name = None
        self.current_collection_name = None
        self.current_folder_id = None  # Reset folder
        self.has_unsaved_changes = False
        self.original_request_data = {}
        self._update_request_title()
    
    def _load_dict_to_table(self, data: Dict, table: QTableWidget):
        """Load a dictionary into a key-value table."""
        table.clearContents()
        
        # Handle None or empty data
        if not data:
            table.setRowCount(1)  # Reset to 1 empty row
            return
        
        # Set exact number of rows needed: data rows + 1 empty row
        table.setRowCount(len(data) + 1)
        
        for i, (key, value) in enumerate(data.items()):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        # Update tab counts after loading
        self._update_tab_counts()
    
    def _get_method_icon(self, method: str) -> str:
        """Get text badge for HTTP method."""
        return method  # Return method without brackets
    
    def _get_method_color(self, method: str) -> str:
        """Get color hex code for HTTP method."""
        method_colors = {
            'GET': '#4EC9B0',      # Teal/cyan for read
            'POST': '#FF9800',     # Orange for create
            'PUT': '#2196F3',      # Blue for update
            'PATCH': '#FFC107',    # Yellow for partial update
            'DELETE': '#F44336',   # Red for delete
            'HEAD': '#9E9E9E',     # Gray for metadata
            'OPTIONS': '#9C27B0'   # Purple for options
        }
        return method_colors.get(method, '#FFFFFF')  # White as default
    
    def _get_table_as_dict(self, table: QTableWidget) -> Dict:
        """Extract key-value pairs from a table as a dictionary."""
        result = {}
        for row in range(table.rowCount()):
            key_item = table.item(row, 0)
            value_item = table.item(row, 1)
            
            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                if key:  # Only add if key is not empty
                    result[key] = value
        
        return result
    
    def _sync_url_to_params(self):
        """Sync query parameters from URL to params table (Postman-style live sync)."""
        # Prevent infinite loop
        if getattr(self, '_syncing_params', False):
            return
        
        self._syncing_params = True
        try:
            url = self.url_input.text().strip()
            if not url:
                self._syncing_params = False
                return
            
            # Parse URL to extract query parameters
            try:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                
                # Convert parse_qs result (lists) to simple key-value dict
                params_dict = {}
                for key, values in query_params.items():
                    # parse_qs returns lists, take first value
                    params_dict[key] = values[0] if values else ''
                
                # Update params table
                self.params_table.blockSignals(True)
                self.params_table.setRowCount(0)  # Clear existing
                
                # Add parsed params
                for key, value in params_dict.items():
                    row = self.params_table.rowCount()
                    self.params_table.insertRow(row)
                    self.params_table.setItem(row, 0, QTableWidgetItem(key))
                    self.params_table.setItem(row, 1, QTableWidgetItem(value))
                
                # Add one empty row for adding new params
                row = self.params_table.rowCount()
                self.params_table.insertRow(row)
                self.params_table.setItem(row, 0, QTableWidgetItem(''))
                self.params_table.setItem(row, 1, QTableWidgetItem(''))
                
                self.params_table.blockSignals(False)
                self._update_tab_counts()
                
            except Exception as e:
                # Invalid URL or parsing error - silently ignore
                pass
        finally:
            self._syncing_params = False
    
    def _sync_params_to_url(self):
        """Sync params table to URL query string (Postman-style live sync)."""
        # Prevent infinite loop
        if getattr(self, '_syncing_params', False):
            return
        
        self._syncing_params = True
        try:
            url = self.url_input.text().strip()
            if not url:
                self._syncing_params = False
                return
            
            # Get params from table
            params_dict = self._get_table_as_dict(self.params_table)
            
            # Parse current URL
            try:
                parsed = urlparse(url)
                
                # Build new query string
                if params_dict:
                    new_query = urlencode(params_dict)
                else:
                    new_query = ''
                
                # Reconstruct URL with new query
                new_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))
                
                # Update URL input
                self.url_input.blockSignals(True)
                self.url_input.setText(new_url)
                self.url_input.blockSignals(False)
                
            except Exception as e:
                # Invalid URL - silently ignore
                pass
        finally:
            self._syncing_params = False
    
    def _store_original_request_data(self):
        """Store the current request data for change detection."""
        self.original_request_data = {
            'method': self.method_combo.currentText(),
            'url': self.url_input.text(),
            'params': self._get_table_as_dict(self.params_table),
            'headers': self._get_table_as_dict(self.headers_table),
            'body': self.body_input.toPlainText(),
            'body_type': self.body_type_combo.currentText(),
            'auth_type': self.auth_type_combo.currentText(),
            'auth_token': self.auth_token_input.text(),
            'description': self._current_description,  # Use string instead of widget
            'pre_request_script': self.scripts_tab.get_pre_request_script(),
            'post_response_script': self.scripts_tab.get_post_response_script()
        }
    
    def _mark_as_changed(self):
        """Mark the request as having unsaved changes."""
        # Don't mark as changed if there's no request loaded
        current_tab_index = self.request_tabs.currentIndex()
        if current_tab_index < 0:
            return  # No tab open
        
        if current_tab_index not in self.tab_states:
            return  # Tab has no state
        
        # Don't mark as changed if this tab has no request (empty/new tab with no data)
        tab_state = self.tab_states[current_tab_index]
        if not tab_state.get('request_id') and not self.current_request_id:
            return  # No request to mark as changed
        
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self._update_request_title()
            
            # Update current tab's unsaved indicator
            self.tab_states[current_tab_index]['has_changes'] = True
            self._update_tab_title(current_tab_index)
    
    def _update_method_style(self, method: str):
        """Update the method combo styling based on selected method."""
        # Define colors for each HTTP method
        method_colors = {
            'GET': '#4CAF50',      # Green
            'POST': '#2196F3',     # Blue
            'PUT': '#FF9800',      # Orange
            'DELETE': '#F44336',   # Red
            'PATCH': '#9C27B0',    # Purple
            'HEAD': '#757575',     # Gray
            'OPTIONS': '#757575',  # Gray
        }
        
        color = method_colors.get(method, '#757575')
        
        # Apply styled dropdown with method color
        self.method_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {color};
                color: #FFFFFF;
                border: 2px solid {color};
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: bold;
                font-size: 12px;
            }}
            QComboBox:hover {{
                opacity: 0.9;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 20px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                /* Clean flat white arrow for colored background */
                image: url(assets/icons/arrow-down-white.svg);
                width: 12px;
                height: 12px;
            }}
        """)
    
    def _on_body_type_changed(self, body_type: str):
        """Handle body type selection change."""
        self._update_body_editor_for_type(body_type)
        self._auto_set_content_type_header(body_type)
    
    def _auto_set_content_type_header(self, body_type: str):
        """
        Automatically set Content-Type header based on body type selection.
        
        Args:
            body_type: Selected body type ('none', 'raw', 'form-data', 'x-www-form-urlencoded')
        """
        # Map body types to Content-Type values
        content_type_map = {
            'none': None,  # No Content-Type needed
            'raw': 'application/json',  # Default to JSON for raw
            'form-data': 'multipart/form-data',
            'x-www-form-urlencoded': 'application/x-www-form-urlencoded'
        }
        
        new_content_type = content_type_map.get(body_type)
        
        if new_content_type is None and body_type != 'none':
            return  # Unknown body type, don't modify headers
        
        # Check if Content-Type header already exists
        content_type_row = -1
        for row in range(self.headers_table.rowCount()):
            key_item = self.headers_table.item(row, 0)
            if key_item and key_item.text().strip().lower() == 'content-type':
                content_type_row = row
                break
        
        if body_type == 'none':
            # Remove Content-Type header if body type is none
            if content_type_row >= 0:
                self.headers_table.removeRow(content_type_row)
                # Ensure at least 1 empty row remains
                if self.headers_table.rowCount() == 0:
                    self.headers_table.setRowCount(1)
        else:
            # Set or update Content-Type header
            if content_type_row >= 0:
                # Update existing Content-Type value
                value_item = self.headers_table.item(content_type_row, 1)
                if value_item:
                    value_item.setText(new_content_type)
                else:
                    self.headers_table.setItem(content_type_row, 1, QTableWidgetItem(new_content_type))
            else:
                # Add new Content-Type header
                # Find first empty row or add new row
                empty_row = -1
                for row in range(self.headers_table.rowCount()):
                    key_item = self.headers_table.item(row, 0)
                    if not key_item or not key_item.text().strip():
                        empty_row = row
                        break
                
                if empty_row >= 0:
                    # Use existing empty row
                    self.headers_table.setItem(empty_row, 0, QTableWidgetItem('Content-Type'))
                    self.headers_table.setItem(empty_row, 1, QTableWidgetItem(new_content_type))
                else:
                    # Add new row
                    row_count = self.headers_table.rowCount()
                    self.headers_table.insertRow(row_count)
                    self.headers_table.setItem(row_count, 0, QTableWidgetItem('Content-Type'))
                    self.headers_table.setItem(row_count, 1, QTableWidgetItem(new_content_type))
        
        # Update tab counts to reflect header change
        self._update_tab_counts()
    
    def _update_body_editor_for_type(self, body_type: str):
        """Update body editor UI based on selected body type."""
        if body_type == 'none':
            self.body_input.setEnabled(False)
            self.body_input.setPlaceholderText("No body for this request")
        else:
            self.body_input.setEnabled(True)
            if body_type == 'raw':
                self.body_input.setPlaceholderText("Enter request body (e.g., JSON)")
            elif body_type == 'form-data':
                self.body_input.setPlaceholderText('Enter form data as JSON: {"key": "value", "file": "path"}')
            elif body_type == 'x-www-form-urlencoded':
                self.body_input.setPlaceholderText('Enter form data as JSON: {"key": "value"}')
    
    def _update_tab_counts(self):
        """Update tab labels to show item counts and status indicators."""
        # Count params
        params_count = 0
        for row in range(self.params_table.rowCount()):
            key_item = self.params_table.item(row, 0)
            if key_item and key_item.text().strip():
                params_count += 1
        
        # Count headers
        headers_count = 0
        for row in range(self.headers_table.rowCount()):
            key_item = self.headers_table.item(row, 0)
            if key_item and key_item.text().strip():
                headers_count += 1
        
        # Check if authorization is configured
        auth_type = self.auth_type_combo.currentText()
        auth_configured = auth_type != 'None' and (
            (auth_type == 'Bearer Token' and self.auth_token_input.text().strip()) or
            (auth_type == 'OAuth 2.0' and hasattr(self, 'current_oauth_token') and self.current_oauth_token is not None)
        )
        
        # Count tests
        tests_count = len(self.test_tab.get_assertions())
        
        # Update tab labels with counts and indicators
        params_label = f"Params ({params_count})" if params_count > 0 else "Params"
        headers_label = f"Headers ({headers_count})" if headers_count > 0 else "Headers"
        auth_label = "Authorization ✓" if auth_configured else "Authorization"
        tests_label = f"Tests ({tests_count})" if tests_count > 0 else "Tests"
        
        self.inner_tabs.setTabText(0, params_label)
        self.inner_tabs.setTabText(1, headers_label)
        self.inner_tabs.setTabText(2, auth_label)
        self.inner_tabs.setTabText(4, tests_label)
    
    def _update_tab_indicators(self):
        """Update content indicators (dots) on Body and Scripts tabs."""
        # Body tab indicator - show dot if body has content
        body_index = self.inner_tabs.indexOf(self.body_input.parent())
        if body_index != -1:
            has_body_content = bool(self.body_input.toPlainText().strip())
            body_text = "Body ·" if has_body_content else "Body"
            self.inner_tabs.setTabText(body_index, body_text)
        
        # Scripts tab indicator - show dot if either script has content
        scripts_index = self.inner_tabs.indexOf(self.scripts_tab)
        if scripts_index != -1:
            has_pre_script = bool(self.scripts_tab.get_pre_request_script())
            has_post_script = bool(self.scripts_tab.get_post_response_script())
            has_any_script = has_pre_script or has_post_script
            scripts_text = "Scripts ·" if has_any_script else "Scripts"
            self.inner_tabs.setTabText(scripts_index, scripts_text)
        
        # Cookies tab indicator - show dot if any cookies exist
        cookies_index = self.inner_tabs.indexOf(self.cookies_tab)
        if cookies_index != -1:
            cookies = self.cookies_tab.get_cookies_as_list()
            has_cookies = len(cookies) > 0
            cookies_text = "Cookies ·" if has_cookies else "Cookies"
            self.inner_tabs.setTabText(cookies_index, cookies_text)
        
        # Update script toggle button indicators
        self.scripts_tab.update_toggle_indicators()
    
    def _auto_add_table_rows(self, table: QTableWidget):
        """Dynamically manage table rows: show only filled rows + 1 empty row (no sorting during editing)."""
        # Block signals to prevent recursive calls
        table.blockSignals(True)
        
        try:
            # Count filled rows and collect empty row indices
            filled_count = 0
            empty_rows_to_remove = []
            
            for row in range(table.rowCount()):
                key_item = table.item(row, 0)
                value_item = table.item(row, 1)
                key_text = key_item.text().strip() if key_item else ""
                value_text = value_item.text().strip() if value_item else ""
                
                # If either key or value has content, it's filled
                if key_text or value_text:
                    filled_count += 1
                else:
                    empty_rows_to_remove.append(row)
            
            # Remove all empty rows except keep one at the end
            if len(empty_rows_to_remove) > 1:
                # Remove empty rows from bottom to top (to maintain indices)
                for row in reversed(empty_rows_to_remove[:-1]):
                    table.removeRow(row)
            elif len(empty_rows_to_remove) == 0:
                # No empty rows exist, add one at the end
                table.insertRow(table.rowCount())
        
        finally:
            # Re-enable signals
            table.blockSignals(False)
    
    def _update_request_title(self):
        """Update the request title label to show current state with breadcrumb (Postman-style)."""
        # Check if this is a new unsaved request
        current_tab_index = self.request_tabs.currentIndex()
        is_new_request = False
        
        if current_tab_index >= 0 and current_tab_index in self.tab_states:
            tab_state = self.tab_states[current_tab_index]
            if 'ui_state' in tab_state and tab_state['ui_state'].get('is_new_request'):
                is_new_request = True
        
        if is_new_request:
            # Creating a new request
            new_request_color = "#2196F3" if self.current_theme == 'light' else "#64B5F6"
            self.request_title_label.setText(
                f"<span style='color: {new_request_color}; font-weight: 600;'>✨ Creating New Request</span>"
            )
            self.request_title_label.setProperty("saved", "false")
            self.rename_request_btn.setVisible(False)
            self.description_btn.setVisible(False)  # Hide description button for new requests
        elif self.current_request_id and self.current_request_name:
            # Saved request - show full breadcrumb with colored method
            method = self.method_combo.currentText()
            method_color = self._get_method_color(method)
            
            # Theme-aware colors
            muted_color = "#757575" if self.current_theme == 'light' else "#AAAAAA"
            text_color = "#212121" if self.current_theme == 'light' else "#E0E0E0"
            new_request_color = "#9E9E9E" if self.current_theme == 'light' else "#999999"
            
            # Build breadcrumb path: Collection > Folder1 > Folder2 > METHOD RequestName
            breadcrumb_parts = []
            
            # Add collection name (muted, not bold)
            breadcrumb_parts.append(f"<span style='color: {muted_color}; font-weight: normal;'>{self.current_collection_name}</span>")
            
            # Add folder path if exists (muted, not bold)
            if self.current_folder_id:
                folder_path = self.db.get_folder_path(self.current_folder_id)
                for folder_name in folder_path:
                    breadcrumb_parts.append(f"<span style='color: {muted_color}; font-weight: normal;'>{folder_name}</span>")
            
            # Build the HTML breadcrumb
            title_html = " › ".join(breadcrumb_parts)
            
            # Add separator before method and request name
            if breadcrumb_parts:
                title_html += " › "
            
            # Add highlighted method and request name
            title_html += f"<span style='color: {method_color}; font-weight: bold;'>{method}</span> "
            title_html += f"<span style='font-weight: 600; color: {text_color};'>{self.current_request_name}</span>"
            
            # Add unsaved indicator
            if self.has_unsaved_changes:
                title_html += " <span style='color: #FF6B6B;'>•</span>"  # Red dot for unsaved
            
            self.request_title_label.setText(title_html)
            self.request_title_label.setProperty("saved", "true")
            
            # Show rename and description buttons for saved requests
            self.rename_request_btn.setVisible(True)
            self.description_btn.setVisible(True)
        else:
            # New unsaved request
            new_request_color = "#9E9E9E" if self.current_theme == 'light' else "#999999"
            self.request_title_label.setText(f"<span style='color: {new_request_color}; font-style: italic;'>New Request (not saved)</span>")
            self.request_title_label.setProperty("saved", "false")
            
            # Hide rename and description buttons for unsaved requests
            self.rename_request_btn.setVisible(False)
            self.description_btn.setVisible(False)
        
        # Force style refresh
        self.request_title_label.style().unpolish(self.request_title_label)
        self.request_title_label.style().polish(self.request_title_label)
    
    def _check_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes. Returns True if user wants to continue."""
        if not self.has_unsaved_changes:
            return True
        
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False
    
    def _save_request(self):
        """Save the current request to the database."""
        # Check if this is a new unsaved request
        current_tab_index = self.request_tabs.currentIndex()
        is_new_request = False
        
        if current_tab_index >= 0 and current_tab_index in self.tab_states:
            tab_state = self.tab_states[current_tab_index]
            if tab_state.get('request_id') is None:
                is_new_request = True
        
        if is_new_request:
            # Convert temporary tab to persistent when saving new request
            self._convert_temporary_to_persistent()
            # New request - prompt for collection selection
            self._save_new_request()
            return
        
        if not self.current_request_id:
            QMessageBox.warning(self, "Warning", "No request selected to save!")
            # Don't convert temporary tab if there's nothing to save
            return
        
        # Convert temporary tab to persistent only when actually saving
        self._convert_temporary_to_persistent()
        
        try:
            # Get current request name
            request = self.db.get_request(self.current_request_id)
            
            # Update with current values
            self.db.update_request(
                request_id=self.current_request_id,
                name=request['name'],
                method=self.method_combo.currentText(),
                url=self.url_input.text(),
                params=self._get_table_as_dict(self.params_table),
                headers=self._get_table_as_dict(self.headers_table),
                body=self.body_input.toPlainText(),
                auth_type=self.auth_type_combo.currentText(),
                auth_token=self.auth_token_input.text(),
                description=self._current_description,  # Use string instead of widget
                pre_request_script=self.scripts_tab.get_pre_request_script(),
                post_response_script=self.scripts_tab.get_post_response_script(),
                folder_id=request.get('folder_id'),
                body_type=self.body_type_combo.currentText()
            )
            
            # Save test assertions
            self._save_test_assertions()
            
            # Reset unsaved changes flag
            self._store_original_request_data()
            self.has_unsaved_changes = False
            self._update_request_title()
            
            # Update tab title to remove unsaved indicator
            current_tab_index = self.request_tabs.currentIndex()
            if current_tab_index >= 0 and current_tab_index < len(self.tab_states):
                self.tab_states[current_tab_index]['has_changes'] = False
                self._update_tab_title(current_tab_index)
            
            # Update status bar
            self._update_save_status("✓ Request saved successfully")
            
            # Show success status
            self._show_status("Request saved successfully", "success")
            
            # Auto-sync to filesystem if Git sync is enabled
            self._auto_sync_to_filesystem()
            
            # Reload collections to show updated request, preserving folder state
            self._load_collections()
            
            # Ensure the request is visible in the tree (keeps folder expanded)
            self._ensure_request_visible_in_tree(self.current_request_id)
        except Exception as e:
            self._update_save_status("✗ Failed to save request", duration=5000)
            self._show_status(f"Failed to save: {str(e)[:40]}...", "error")
    
    def _save_new_request(self):
        """Save a new unsaved request by prompting for collection."""
        try:
            print("[DEBUG] _save_new_request called")
            
            # Create dialog to select collection
            dialog = QDialog(self)
            dialog.setWindowTitle("Save New Request")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            # Request name
            layout.addWidget(QLabel("Request Name:"))
            name_input = QLineEdit()
            name_input.setText("New Request")
            name_input.selectAll()
            layout.addWidget(name_input)
            
            # Collection selection
            layout.addWidget(QLabel("Save to Collection:"))
            collection_combo = QComboBox()
            
            # Load collections
            collections = self.db.get_all_collections()
            if not collections:
                QMessageBox.warning(self, "No Collections", "Please create a collection first!")
                return
            
            for collection in collections:
                collection_combo.addItem(collection['name'], collection['id'])
            
            layout.addWidget(collection_combo)
            
            # Folder selection (optional)
            layout.addWidget(QLabel("Folder (optional):"))
            folder_combo = QComboBox()
            folder_combo.addItem("(No folder)", None)
            
            def update_folders():
                folder_combo.clear()
                folder_combo.addItem("(No folder)", None)
                collection_id = collection_combo.currentData()
                if collection_id:
                    folders = self.db.get_folders_by_collection(collection_id)
                    for folder in folders:
                        folder_combo.addItem(folder['name'], folder['id'])
            
            collection_combo.currentIndexChanged.connect(update_folders)
            update_folders()
            
            layout.addWidget(folder_combo)
            
            # Buttons
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            print("[DEBUG] Showing dialog...")
            result = dialog.exec()
            print(f"[DEBUG] Dialog closed with result: {result}")
            
            if result == QDialog.DialogCode.Accepted:
                # Save the request
                collection_id = collection_combo.currentData()
                folder_id = folder_combo.currentData()
                request_name = name_input.text().strip() or "New Request"
                
                print(f"[DEBUG] Starting save new request: {request_name}")
                
                # Create the request in database
                print(f"[DEBUG] Creating request in DB...")
                request_id = self.db.create_request(
                    name=request_name,
                    url=self.url_input.text(),
                    method=self.method_combo.currentText(),
                    collection_id=collection_id,
                    folder_id=folder_id,
                    params=self._get_table_as_dict(self.params_table),
                    headers=self._get_table_as_dict(self.headers_table),
                    body=self.body_input.toPlainText(),
                    auth_type=self.auth_type_combo.currentText(),
                    auth_token=self.auth_token_input.text(),
                    description=self._current_description,  # Use string instead of widget
                    pre_request_script=self.scripts_tab.get_pre_request_script(),
                    post_response_script=self.scripts_tab.get_post_response_script()
                )
                print(f"[DEBUG] Request created with ID: {request_id}")
                
                # Update current tab state
                print(f"[DEBUG] Updating tab state...")
                current_tab_index = self.request_tabs.currentIndex()
                if current_tab_index >= 0 and current_tab_index in self.tab_states:
                    self.tab_states[current_tab_index]['request_id'] = request_id
                    self.tab_states[current_tab_index]['has_changes'] = False
                    self.tab_states[current_tab_index]['name'] = request_name
                    if 'ui_state' in self.tab_states[current_tab_index]:
                        self.tab_states[current_tab_index]['ui_state']['is_new_request'] = False
                        self.tab_states[current_tab_index]['ui_state']['request_id'] = request_id
                        self.tab_states[current_tab_index]['ui_state']['collection_id'] = collection_id
                        self.tab_states[current_tab_index]['ui_state']['request_name'] = request_name
                
                # Update current_request_id and related variables
                print(f"[DEBUG] Setting current request variables...")
                self.current_request_id = request_id
                self.current_collection_id = collection_id
                self.current_request_name = request_name
                self.current_folder_id = folder_id
                
                # Get collection name
                print(f"[DEBUG] Getting collection name...")
                collection = self.db.get_collection(collection_id)
                if collection:
                    self.current_collection_name = collection.get('name', 'Unknown Collection')
                else:
                    self.current_collection_name = 'Unknown Collection'
                print(f"[DEBUG] Collection name: {self.current_collection_name}")
                
                # Reset unsaved changes flag
                print(f"[DEBUG] Storing original request data...")
                self._store_original_request_data()
                self.has_unsaved_changes = False
                
                # Update tab title
                print(f"[DEBUG] Updating tab title...")
                self._update_tab_title(current_tab_index)
                
                print(f"[DEBUG] Updating request title...")
                self._update_request_title()
                
                # Reload collections to show new request
                print(f"[DEBUG] Reloading collections...")
                self._load_collections()
                
                # Ensure the new request is visible in the tree
                print(f"[DEBUG] Ensuring request is visible...")
                self._ensure_request_visible_in_tree(request_id)
                
                # Update highlight
                print(f"[DEBUG] Updating current request highlight...")
                self._update_current_request_highlight()
                
                # Show success status
                print(f"[DEBUG] Showing success status...")
                self._show_status(f"Request '{request_name}' saved successfully", "success")
                
                # Auto-sync to filesystem if Git sync is enabled
                print(f"[DEBUG] Auto-syncing to filesystem...")
                self._auto_sync_to_filesystem()
                
                print(f"[DEBUG] Save completed successfully!")
            
            print("[DEBUG] _save_new_request function ending normally")
                
        except Exception as e:
            print(f"[ERROR] Exception in _save_new_request: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save request: {str(e)}\n\nPlease check the console for details.")
            try:
                self._show_status(f"Failed to save: {str(e)[:40]}...", "error")
            except:
                pass  # Status might also fail
    
    # ==================== Request Execution ====================
    
    def _send_request(self):
        """Execute the HTTP request and display the response."""
        # Convert temporary tab to persistent when sending request
        self._convert_temporary_to_persistent()
        
        url = self.url_input.text().strip()
        if not url:
            self._show_status("Please enter a URL!", "warning")
            return
        
        # Show loading state with enhanced visual feedback
        self.send_btn.setEnabled(False)
        self.send_btn.setText("⏳ Sending...")
        # Override with loading state color - use animated orange
        self.send_btn.setStyleSheet("""
            QPushButton#sendButton {
                background-color: #FF9800;
                color: white;
                border: 2px solid #FFB74D;
            }
            QPushButton#sendButton:disabled {
                background-color: #FF9800;
                color: white;
                border: 2px solid #FFB74D;
            }
        """)
        
        # Show loading status
        self._show_status(f"Sending {self.method_combo.currentText()} request...", "info")
        
        # Auto-expand response panel when sending
        self._expand_response_panel()
        
        # Clear previous response
        self._clear_response_viewer()
        
        # Get request parameters
        method = self.method_combo.currentText()
        params = self._get_table_as_dict(self.params_table)
        headers = self._get_table_as_dict(self.headers_table)
        body = self.body_input.toPlainText()
        auth_type = self.auth_type_combo.currentText()
        
        # Store ORIGINAL unsubstituted values for pre-request script re-substitution
        original_url = url
        original_params = params.copy() if params else {}
        original_headers = headers.copy() if headers else {}
        original_body = body
        original_auth_token = ""
        
        # Get auth token based on auth type
        auth_token = ""
        if auth_type == 'Bearer Token':
            auth_token = self.auth_token_input.text()
            original_auth_token = auth_token  # Store original before substitution
        elif auth_type == 'OAuth 2.0':
            # OAuth token will be added directly to headers
            auth_header = self._get_authorization_header()
            if auth_header is None:
                # Token expired or invalid
                self.send_btn.setEnabled(True)
                self.send_btn.setText("Send")
                return
            # Add OAuth token to headers
            if headers is None:
                headers = {}
            headers['Authorization'] = auth_header
            # Set auth_type to None so ApiClient doesn't add another Authorization header
            auth_type = 'None'
            auth_token = ""
        
        # Apply variable substitution with new prefix system
        # {{env.xxx}} - environment variables
        # {{col.xxx}} - collection variables
        # {{ext.xxx}} - extracted variables
        # {{$xxx}} - dynamic variables
        # {{xxx}} - backward compatibility (checks all scopes)
        
        # Get collection variables if we have a current collection
        collection_variables = {}
        if self.current_collection_id:
            collection_variables = self.db.get_collection_variables(self.current_collection_id)
        
        # Get extracted variables (always available)
        extracted_variables = {}
        all_extracted = self.db.get_all_extracted_variables()
        for var in all_extracted:
            # Store WITHOUT prefix - the new substitution system handles prefixes
            extracted_variables[var['name']] = var['value']
        
        # Update environment manager's extracted variables for substitution
        self.env_manager.set_extracted_variables(extracted_variables)
        
        # Debug: Show what variables are available
        if all_extracted:
            print(f"[DEBUG] Loaded {len(all_extracted)} extracted variables:")
            for var in all_extracted:
                print(f"  - {var['name']} = {var['value']}")
        else:
            print("[DEBUG] No extracted variables found in database")
        
        print(f"[DEBUG] Collection variables: {len(collection_variables)}")
        print(f"[DEBUG] Environment variables: {len(self.env_manager.get_active_variables()) if self.env_manager.has_active_environment() else 0}")
        
        if self.env_manager.has_active_environment():
            print(f"[DEBUG] Using environment manager substitution with new prefix system")
            
            # Substitute with new prefix system
            substituted, unresolved = self.env_manager.substitute_in_request(
                url, params, headers, body, auth_token, collection_variables=collection_variables
            )
            
            print(f"[DEBUG] After substitution:")
            print(f"  URL: {substituted['url']}")
            print(f"  Headers: {substituted.get('headers')}")
            
            # Warn about unresolved variables
            if unresolved:
                reply = QMessageBox.question(
                    self, "Unresolved Variables",
                    f"The following variables are not defined:\n"
                    f"{', '.join(unresolved)}\n\n"
                    f"Do you want to continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    self.send_btn.setEnabled(True)
                    self.send_btn.setText("Send")
                    return
            
            # Use substituted values
            url = substituted['url']
            params = substituted['params']
            headers = substituted['headers']
            body = substituted['body']
            # Don't overwrite OAuth token with substituted auth_token
            if auth_type == 'Bearer Token':
                auth_token = substituted['auth_token']
        else:
            # No active environment - use direct substitution for collection, extracted, and dynamic variables
            from src.features.variable_substitution import VariableSubstitution
            
            print(f"[DEBUG] No active environment - using direct substitution with new prefix system")
            print(f"[DEBUG] Collection vars: {len(collection_variables)}")
            print(f"[DEBUG] Extracted vars: {len(extracted_variables)}")
            
            # Substitute URL (no env vars, but collection and extracted vars work)
            url, _ = VariableSubstitution.substitute(url, None, collection_variables, extracted_variables)
            print(f"[DEBUG] URL after {{variable}} substitution: {url}")
            
            # Substitute path parameters (:paramName syntax) in URL
            url, _ = VariableSubstitution.substitute_path_params(url, None, collection_variables, extracted_variables)
            print(f"[DEBUG] URL after :pathParam substitution: {url}")
            
            # Substitute params
            if params:
                params, _ = VariableSubstitution.substitute_dict(params, None, collection_variables, extracted_variables)
            
            # Substitute headers
            if headers:
                print(f"[DEBUG] Substituting headers: {headers}")
                headers, _ = VariableSubstitution.substitute_dict(headers, None, collection_variables, extracted_variables)
                print(f"[DEBUG] Headers after substitution: {headers}")
            
            # Substitute body
            if body:
                body, _ = VariableSubstitution.substitute(body, None, collection_variables, extracted_variables)
            
            # Substitute auth token
            if auth_token:
                auth_token, _ = VariableSubstitution.substitute(auth_token, None, collection_variables, extracted_variables)
        
        # Apply default protocol if URL doesn't have one
        if not url.startswith(('http://', 'https://', 'ws://', 'wss://')):
            default_protocol = self.db.get_setting('default_protocol', 'https')
            url = f"{default_protocol}://{url}"
            print(f"[INFO] Applied default protocol: {default_protocol}:// to URL")
        
        # Get and validate timeout setting
        try:
            timeout_text = self.timeout_input.text().strip()
            timeout = int(timeout_text) if timeout_text else 30
            # Validate timeout range (1-300 seconds)
            if timeout < 1:
                timeout = 1
            elif timeout > 300:
                timeout = 300
            self.api_client.timeout = timeout
        except ValueError:
            self._show_status("Invalid timeout value, using default (30s)", "warning")
            self.api_client.timeout = 30
        
        # Set SSL verification option
        self.api_client.verify_ssl = self.verify_ssl_checkbox.isChecked()
        if not self.api_client.verify_ssl:
            self._show_status("SSL verification disabled - not recommended for production!", "warning")
        
        # Clean up existing thread if still running
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.wait()
        
        # Debug: Print what's being sent (helps verify variable substitution)
        print(f"\n[DEBUG] Sending request:")
        print(f"  Method: {method}")
        print(f"  URL: {url}")
        if params:
            print(f"  Params: {params}")
        if headers:
            print(f"  Headers: {headers}")
        if body:
            print(f"  Body (first 200 chars): {body[:200]}")
        
        # Check if any variables are still unsubstituted
        unsubstituted = []
        if '{{' in url:
            unsubstituted.append(f"URL contains: {url}")
        for k, v in (headers or {}).items():
            if '{{' in str(v) or '{{' in str(k):
                unsubstituted.append(f"Header {k}: {v}")
        if unsubstituted:
            print(f"[WARNING] Unsubstituted variables detected:")
            for u in unsubstituted:
                print(f"  - {u}")
        print()
        
        # ========== Execute Pre-request Script ==========
        pre_request_script = self.scripts_tab.get_pre_request_script()
        if pre_request_script:
            self.scripts_tab.append_console_text(f"--- Pre-request script execution ---", "info")
            try:
                # Get current environment and collection variables
                env_variables = self.env_manager.get_active_variables() if self.env_manager.has_active_environment() else {}
                coll_variables = collection_variables if 'collection_variables' in locals() else {}
                
                # Execute pre-request script
                script_result = self.script_engine.execute_pre_request_script(
                    script=pre_request_script,
                    url=url,
                    method=method,
                    headers=headers or {},
                    body=body or "",
                    params=params or {},
                    environment=env_variables,
                    collection_vars=coll_variables
                )
                
                # Apply modifications from script
                url = script_result['url']
                method = script_result['method']
                headers = script_result['headers']
                body = script_result['body']
                params = script_result['params']
                
                # Update environment and collection variables
                if self.env_manager.has_active_environment():
                    for key, value in script_result['environment'].items():
                        if key not in env_variables or env_variables[key] != value:
                            self.env_manager.set_variable(key, value)
                
                # Track if collection variables were updated
                collection_vars_updated = False
                
                if self.current_collection_id:
                    for key, value in script_result['collection_variables'].items():
                        if key not in coll_variables or coll_variables[key] != value:
                            # Update collection variable in database
                            existing_vars = self.db.get_collection_variables_with_metadata(self.current_collection_id)
                            var_exists = any(v['key'] == key for v in existing_vars)
                            if var_exists:
                                var_id = next(v['id'] for v in existing_vars if v['key'] == key)
                                self.db.update_collection_variable(var_id, value=value)
                            else:
                                self.db.create_collection_variable(self.current_collection_id, key, value)
                            collection_vars_updated = True
                
                # Always reload collection variables after pre-request script
                # (script may have set new values that need to be substituted)
                if self.current_collection_id:
                    collection_variables = self.db.get_collection_variables(self.current_collection_id)
                    print(f"[DEBUG] Reloaded collection variables after pre-request script: {collection_variables}")
                
                # Re-apply variable substitution after script execution
                # CRITICAL: Re-substitute from ORIGINAL values (before first substitution)
                # This ensures variables set by the script are properly substituted
                # IMPORTANT: Must preserve headers/params/body added by the script
                script_modified_headers = headers.copy()  # Save script-modified headers
                script_modified_params = params.copy() if params else {}
                script_modified_body = body
                
                if self.env_manager.has_active_environment():
                    print(f"[DEBUG] Re-applying substitution from ORIGINAL values after pre-request script")
                    
                    # Get fresh environment variables (script may have updated them)
                    env_variables = self.env_manager.get_active_variables()
                    
                    # Re-substitute from ORIGINAL unsubstituted values
                    substituted, unresolved = self.env_manager.substitute_in_request(
                        original_url, original_params, original_headers, original_body, original_auth_token, collection_variables=collection_variables
                    )
                    
                    # Use newly substituted values
                    url = substituted['url']
                    params = substituted['params']
                    headers = substituted['headers']
                    body = substituted['body']
                    if auth_type == 'Bearer Token':
                        auth_token = substituted['auth_token']
                    
                    # CRITICAL FIX: Merge script-added headers back in (script modifications take priority)
                    # This ensures headers added via pm.request.headers.add() are preserved
                    for key, value in script_modified_headers.items():
                        if key not in original_headers:
                            # Header was added by script, not in original - preserve it
                            headers[key] = value
                        elif script_modified_headers[key] != original_headers.get(key):
                            # Header was modified by script - use script value
                            headers[key] = value
                    
                    # Similarly for params added by script
                    # CRITICAL: Merge script-modified params properly
                    # Re-substituted params from original_params will have updated variable values
                    # We need to preserve params that were:
                    # 1. Added by script (not in original)
                    # 2. Modified by script to a literal value (not a variable reference)
                    for key, value in script_modified_params.items():
                        if original_params and key not in original_params:
                            # Param was added by script
                            params[key] = value
                        elif original_params and key in original_params:
                            # Param existed in original - check if script modified it
                            # If the original had a variable reference and script set a literal value, use script value
                            # Otherwise, use the re-substituted value (which has updated variable values)
                            original_value = original_params[key]
                            if '{{' not in str(original_value) and script_modified_params[key] != original_value:
                                # Original was literal and script changed it - use script value
                                params[key] = value
                            # If original had {{variable}}, params[key] already has the re-substituted value with updated variable
                    
                    # If script modified body and it's not just variable substitution, preserve script body
                    if script_modified_body != body and script_modified_body != original_body:
                        body = script_modified_body
                    
                    print(f"[DEBUG] After re-substitution:")
                    print(f"  URL: {url}")
                    print(f"  Headers: {headers}")
                else:
                    # No environment - use direct substitution
                    print(f"[DEBUG] Re-applying direct substitution from ORIGINAL values after pre-request script")
                    from src.features.variable_substitution import VariableSubstitution
                    
                    # Re-substitute from ORIGINAL unsubstituted values
                    url, _ = VariableSubstitution.substitute(original_url, None, collection_variables, extracted_variables)
                    # Re-substitute path parameters (:paramName syntax) in URL
                    url, _ = VariableSubstitution.substitute_path_params(url, None, collection_variables, extracted_variables)
                    
                    # Re-substitute params
                    if original_params:
                        params, _ = VariableSubstitution.substitute_dict(original_params, None, collection_variables, extracted_variables)
                    
                    # Re-substitute headers
                    if original_headers:
                        headers, _ = VariableSubstitution.substitute_dict(original_headers, None, collection_variables, extracted_variables)
                    
                    # Re-substitute body
                    if original_body:
                        body, _ = VariableSubstitution.substitute(original_body, None, collection_variables, extracted_variables)
                    
                    # Re-substitute auth token
                    if original_auth_token:
                        auth_token, _ = VariableSubstitution.substitute(original_auth_token, None, collection_variables, extracted_variables)
                    
                    # CRITICAL FIX: Merge script-added headers/params back in properly
                    # After re-substitution, params will have updated variable values
                    # We only need to preserve params that were:
                    # 1. Added by script (not in original)
                    # 2. Modified by script to a literal value (not a variable reference)
                    for key, value in script_modified_headers.items():
                        if key not in (original_headers or {}):
                            headers[key] = value
                        elif script_modified_headers[key] != (original_headers or {}).get(key):
                            headers[key] = value
                    
                    for key, value in script_modified_params.items():
                        if key not in (original_params or {}):
                            # Param was added by script
                            params[key] = value
                        elif key in (original_params or {}):
                            # Param existed in original - check if script modified it
                            original_value = (original_params or {})[key]
                            if '{{' not in str(original_value) and script_modified_params[key] != original_value:
                                # Original was literal and script changed it - use script value
                                params[key] = value
                            # If original had {{variable}}, params[key] already has the re-substituted value
                    
                    if script_modified_body != body and script_modified_body != original_body:
                        body = script_modified_body
                    
                    print(f"[DEBUG] After re-substitution:")
                    print(f"  URL: {url}")
                    print(f"  Headers: {headers}")
                
                # Display console logs
                self.scripts_tab.append_console_output(script_result['console_logs'])
                
                exec_time = script_result.get('execution_time_ms', 0)
                self.scripts_tab.append_console_text(f"✓ Pre-request script completed in {exec_time}ms", "info")
                
                # Refresh variable inspector if it's open (show updated variable values)
                if hasattr(self, 'variable_inspector_pane') and self.variable_inspector_pane.isVisible():
                    self._refresh_variable_inspector_panel()
                
                # Update method combo if changed
                if method != self.method_combo.currentText():
                    self.method_combo.setCurrentText(method)
                
            except ScriptTimeoutError as e:
                self.scripts_tab.append_console_text(f"⏱️ {str(e)}", "error")
                self._show_status("Pre-request script timed out!", "error")
                self.send_btn.setEnabled(True)
                self.send_btn.setText("Send")
                self._reset_send_button()
                return
            except ScriptExecutionError as e:
                self.scripts_tab.append_console_text(f"❌ {str(e)}", "error")
                self._show_status(f"Pre-request script failed: {str(e)[:50]}...", "error")
                self.send_btn.setEnabled(True)
                self.send_btn.setText("Send")
                self._reset_send_button()
                return
            except AttributeError as e:
                error_msg = f"Internal error: {str(e)}"
                self.scripts_tab.append_console_text(f"❌ {error_msg}", "error")
                self._show_status(f"Pre-request script failed: {str(e)[:50]}...", "error")
                print(f"[ERROR] Pre-request script AttributeError: {e}")
                import traceback
                traceback.print_exc()
                self.send_btn.setEnabled(True)
                self.send_btn.setText("Send")
                self._reset_send_button()
                return
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.scripts_tab.append_console_text(f"❌ {error_msg}", "error")
                self._show_status(f"Pre-request script failed: {str(e)[:50]}...", "error")
                print(f"[ERROR] Pre-request script unexpected error: {e}")
                import traceback
                traceback.print_exc()
                self.send_btn.setEnabled(True)
                self.send_btn.setText("Send")
                self._reset_send_button()
                return
        
        # Store request details (after variable substitution and pre-request script)
        # These are the ACTUAL values being sent to the server
        self.current_request_details = {
            'method': method,
            'url': url,
            'params': params,
            'headers': headers,
            'body': body,
            'auth_type': auth_type,
            'auth_token': auth_token
        }
        
        print(f"[DEBUG] Stored request details for Request Details tab:")
        print(f"  URL: {url}")
        print(f"  Params: {params}")
        print(f"  Headers: {headers}")
        
        # Load cookies from database into ApiClient session before sending request
        try:
            self.api_client.load_cookies_from_db(self.db)
            print("[DEBUG] Loaded cookies from database into session")
        except Exception as e:
            print(f"[DEBUG] Error loading cookies: {e}")
        
        # Create and start request thread
        self.request_thread = RequestThread(
            self.api_client, method, url, params, headers, body, auth_type, auth_token
        )
        self.request_thread.finished.connect(self._on_request_finished)
        self.request_thread.error.connect(self._on_request_error)
        self.request_thread.start()
    
    def _on_request_finished(self, response: ApiResponse):
        """Handle successful request completion."""
        # Store response for security scanning
        self.last_response = response
        
        # Re-enable send button with success indicator
        self.send_btn.setEnabled(True)
        self.send_btn.setText("✓ Send")
        # Briefly show success state with green color
        self.send_btn.setStyleSheet("""
            QPushButton#sendButton {
                background-color: #4CAF50;
                color: white;
                border: 2px solid #66BB6A;
            }
        """)
        
        # Reset button style after 1.5 seconds
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self._reset_send_button())
        
        # Show success status with status code
        try:
            status_code = response.status_code if hasattr(response, 'status_code') else response.response.status_code
            elapsed_time = response.elapsed_time if hasattr(response, 'elapsed_time') else 0
            time_ms = int(elapsed_time * 1000)
        except AttributeError:
            status_code = 0
            time_ms = 0
        
        if 200 <= status_code < 300:
            self._show_status(f"{status_code} OK • {time_ms}ms", "success")
        elif 300 <= status_code < 400:
            self._show_status(f"{status_code} Redirect • {time_ms}ms", "info")
        elif 400 <= status_code < 500:
            self._show_status(f"{status_code} Client Error • {time_ms}ms", "warning")
        else:
            self._show_status(f"{status_code} Server Error • {time_ms}ms", "error")
        
        # Display response
        self._display_response(response)
        
        # Update request details viewer
        self._update_request_details_viewer()
        
        # ========== Execute Post-response Script ==========
        post_response_script = self.scripts_tab.get_post_response_script()
        if post_response_script:
            self.scripts_tab.append_console_text(f"--- Post-response script execution ---", "info")
            try:
                # Get current environment and collection variables
                env_variables = self.env_manager.get_active_variables() if self.env_manager.has_active_environment() else {}
                collection_variables = {}
                if self.current_collection_id:
                    collection_variables = self.db.get_collection_variables(self.current_collection_id)
                
                # Safely get response data with fallbacks
                try:
                    response_body = response.text if hasattr(response, 'text') else str(response.response.text)
                    response_headers = dict(response.headers) if hasattr(response, 'headers') else dict(response.response.headers)
                    response_status = response.status_code if hasattr(response, 'status_code') else response.response.status_code
                    response_time = response.elapsed_time * 1000 if hasattr(response, 'elapsed_time') else 0
                except Exception as attr_error:
                    self.scripts_tab.append_console_text(f"⚠️ Warning: Could not access response data: {str(attr_error)}", "warning")
                    response_body = ""
                    response_headers = {}
                    response_status = 0
                    response_time = 0
                
                # Execute post-response script
                script_result = self.script_engine.execute_post_response_script(
                    script=post_response_script,
                    response_status=response_status,
                    response_headers=response_headers,
                    response_body=response_body,
                    response_time_ms=response_time,
                    environment=env_variables,
                    collection_vars=collection_variables
                )
                
                # Update environment variables
                if self.env_manager.has_active_environment():
                    for key, value in script_result['environment'].items():
                        if key not in env_variables or env_variables[key] != value:
                            self.env_manager.set_variable(key, value)
                
                # Update collection variables
                if self.current_collection_id:
                    for key, value in script_result['collection_variables'].items():
                        if key not in collection_variables or collection_variables[key] != value:
                            existing_vars = self.db.get_collection_variables_with_metadata(self.current_collection_id)
                            var_exists = any(v['key'] == key for v in existing_vars)
                            if var_exists:
                                var_id = next(v['id'] for v in existing_vars if v['key'] == key)
                                self.db.update_collection_variable(var_id, value=value)
                            else:
                                self.db.create_collection_variable(self.current_collection_id, key, value)
                
                # Display console logs
                self.scripts_tab.append_console_output(script_result['console_logs'])
                
                # Display test results from pm.test() calls
                if script_result['test_results']:
                    self.scripts_tab.append_console_text(f"\n--- Script Tests ---", "info")
                    for test in script_result['test_results']:
                        if test['passed']:
                            self.scripts_tab.append_console_text(f"  ✓ {test['name']}", "info")
                        else:
                            self.scripts_tab.append_console_text(f"  ✗ {test['name']}: {test['error']}", "error")
                
                exec_time = script_result.get('execution_time_ms', 0)
                self.scripts_tab.append_console_text(f"✓ Post-response script completed in {exec_time}ms", "info")
                
                # Refresh variable inspector if it's open (show updated variable values)
                if hasattr(self, 'variable_inspector_pane') and self.variable_inspector_pane.isVisible():
                    self._refresh_variable_inspector_panel()
                
            except ScriptTimeoutError as e:
                self.scripts_tab.append_console_text(f"⏱️ {str(e)}", "error")
                self._show_status("Post-response script timed out!", "warning")
            except ScriptExecutionError as e:
                self.scripts_tab.append_console_text(f"❌ {str(e)}", "error")
                self._show_status(f"Post-response script error: {str(e)[:50]}...", "error")
            except AttributeError as e:
                error_msg = f"Internal error: {str(e)}"
                self.scripts_tab.append_console_text(f"❌ {error_msg}", "error")
                self._show_status(f"Script execution failed: {str(e)[:50]}...", "error")
                print(f"[ERROR] Post-response script AttributeError: {e}")
                import traceback
                traceback.print_exc()
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.scripts_tab.append_console_text(f"❌ {error_msg}", "error")
                self._show_status(f"Script execution failed: {str(e)[:50]}...", "error")
                print(f"[ERROR] Post-response script unexpected error: {e}")
                import traceback
                traceback.print_exc()
        
        # Execute tests
        self._execute_tests_on_response(response)
        
        # Always run security scan on each request
        scan_id = self._auto_run_security_scan(response)
        
        # Save cookies from response to database
        try:
            self.api_client.save_cookies_to_db(self.db)
            self.cookies_tab.load_cookies()  # Reload cookies in UI
            self._update_tab_indicators()  # Update cookie tab indicator
            print("[DEBUG] Saved cookies from response to database")
        except Exception as e:
            print(f"[DEBUG] Error saving cookies: {e}")
        
        # Save to history (with scan_id if scan was performed)
        self._save_to_history(response=response, scan_id=scan_id)
    
    def _reset_send_button(self):
        """Reset the send button to its default state."""
        self.send_btn.setText("Send")
        self.send_btn.setStyleSheet("")  # Reset to use global stylesheet
    
    def _on_request_error(self, error_message: str):
        """Handle request error with helpful suggestions."""
        # Re-enable send button with error indicator
        self.send_btn.setEnabled(True)
        self.send_btn.setText("✗ Send")
        # Briefly show error state with red color
        self.send_btn.setStyleSheet("""
            QPushButton#sendButton {
                background-color: #F44336;
                color: white;
                border: 2px solid #EF5350;
            }
        """)
        
        # Reset button style after 2 seconds
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self._reset_send_button())
        
        # Get helpful error message with suggestions
        enhanced_error = self._enhance_error_message(error_message)
        
        # Show error status with helpful message
        self._show_status(f"Request failed: {enhanced_error['short'][:50]}...", "error")
        
        # Make response viewer visible when we have an error
        if hasattr(self, 'request_response_splitter'):
            response_viewer = self.request_response_splitter.widget(1)
            if response_viewer and not response_viewer.isVisible():
                response_viewer.setVisible(True)
                # Ensure panel is expanded when showing error
                if hasattr(self, 'response_panel_collapsed') and self.response_panel_collapsed:
                    self._toggle_response_panel()
        
        # Display error in status with proper styling
        self.status_label.setText(f"Status: Connection Error")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold; font-size: 13px;")
        
        # Hide status badge for errors
        self.status_badge.setVisible(False)
        
        # Show time and size as N/A
        self.time_label.setText(f"⏱ N/A")
        self.time_label.setStyleSheet("color: #999; font-weight: bold;")
        self.size_label.setText(f"📦 N/A")
        self.size_label.setStyleSheet("color: #999; font-weight: bold;")
        
        # Display error in response viewer with full details and suggestions
        self.response_body.setPlainText(enhanced_error['full'])
        
        # Switch to response body view (from empty state)
        self.response_stack.setCurrentWidget(self.response_body)
        
        # Clear response headers table
        self.response_headers_table.clearContents()
        self.response_headers_table.setRowCount(0)
        
        # Update request details viewer to show what was attempted
        self._update_request_details_viewer()
        
        # Switch to Request Details tab to show what was sent
        if hasattr(self, 'response_tabs'):
            # Find Request Details tab index
            for i in range(self.response_tabs.count()):
                if self.response_tabs.tabText(i) == "Request Details":
                    self.response_tabs.setCurrentIndex(i)
                    break
        
        # Save to history (with error)
        self._save_to_history(error_message=error_message)
    
    def _enhance_error_message(self, error_message: str) -> Dict[str, str]:
        """
        Enhance error messages with helpful suggestions.
        
        Args:
            error_message: Original error message
            
        Returns:
            Dictionary with 'short' and 'full' error messages
        """
        error_lower = error_message.lower()
        suggestions = []
        short_msg = error_message
        
        # Connection errors
        if 'connection' in error_lower or 'failed to connect' in error_lower:
            short_msg = "Connection failed"
            suggestions.extend([
                "• Check if the URL is correct",
                "• Ensure you have internet connection",
                "• Verify the server is running and accessible",
                "• Check if you need to use a VPN or proxy",
                "• Try accessing the URL in a web browser"
            ])
        
        # Timeout errors
        elif 'timeout' in error_lower or 'timed out' in error_lower:
            short_msg = "Request timed out"
            current_timeout = self.api_client.timeout
            suggestions.extend([
                "• The server may be slow or overloaded",
                f"• Increase the timeout setting in Authorization tab (currently {current_timeout}s)",
                "• Check your internet connection speed",
                "• Try again later"
            ])
        
        # DNS resolution errors
        elif 'name or service not known' in error_lower or 'getaddrinfo failed' in error_lower or 'nodename nor servname provided' in error_lower:
            short_msg = "Cannot resolve hostname"
            suggestions.extend([
                "• Check if the URL is spelled correctly",
                "• Ensure the domain name exists",
                "• Try using an IP address instead of hostname",
                "• Check your DNS settings"
            ])
        
        # SSL/TLS errors
        elif 'ssl' in error_lower or 'certificate' in error_lower or 'https' in error_lower:
            short_msg = "SSL/Certificate error"
            suggestions.extend([
                "• The server's SSL certificate may be invalid or expired",
                "• Try using 'http://' instead of 'https://' for local development",
                "• For local dev, you may need to disable SSL verification",
                "• Contact the API provider about certificate issues"
            ])
        
        # 4xx errors (client errors)
        elif '400' in error_lower or 'bad request' in error_lower:
            short_msg = "Bad Request (400)"
            suggestions.extend([
                "• Check if the request body is valid JSON",
                "• Verify all required parameters are included",
                "• Review the API documentation for correct format"
            ])
        elif '401' in error_lower or 'unauthorized' in error_lower:
            short_msg = "Unauthorized (401)"
            suggestions.extend([
                "• Check if you need to add authentication",
                "• Verify your API key or token is correct",
                "• Ensure the Authorization header is set properly",
                "• Your token may have expired - try refreshing"
            ])
        elif '403' in error_lower or 'forbidden' in error_lower:
            short_msg = "Forbidden (403)"
            suggestions.extend([
                "• You don't have permission to access this resource",
                "• Check if your API key has the required scopes",
                "• Verify you're using the correct authentication method",
                "• Contact the API provider about access"
            ])
        elif '404' in error_lower or 'not found' in error_lower:
            short_msg = "Not Found (404)"
            suggestions.extend([
                "• Check if the endpoint URL is correct",
                "• Verify the resource exists",
                "• Review the API documentation for correct paths",
                "• Check if the API version in the URL is correct"
            ])
        elif '429' in error_lower or 'rate limit' in error_lower:
            short_msg = "Rate Limited (429)"
            suggestions.extend([
                "• You're making too many requests",
                "• Wait a moment and try again",
                "• Check the API's rate limit documentation",
                "• Consider implementing request throttling"
            ])
        
        # 5xx errors (server errors)
        elif '500' in error_lower or 'internal server error' in error_lower:
            short_msg = "Internal Server Error (500)"
            suggestions.extend([
                "• The server encountered an error",
                "• Try again in a few moments",
                "• Check if the request data is correct",
                "• Contact the API provider if issue persists"
            ])
        elif '502' in error_lower or 'bad gateway' in error_lower:
            short_msg = "Bad Gateway (502)"
            suggestions.extend([
                "• The gateway/proxy server received an invalid response",
                "• The server may be temporarily down",
                "• Try again in a few moments"
            ])
        elif '503' in error_lower or 'service unavailable' in error_lower:
            short_msg = "Service Unavailable (503)"
            suggestions.extend([
                "• The server is temporarily unavailable",
                "• Server may be under maintenance",
                "• Try again later"
            ])
        
        # JSON errors
        elif 'json' in error_lower and ('decode' in error_lower or 'parse' in error_lower):
            short_msg = "Invalid JSON"
            suggestions.extend([
                "• Check if your request body is valid JSON",
                "• Use a JSON validator to verify format",
                "• Ensure Content-Type header is set to 'application/json'",
                "• Check for trailing commas or syntax errors"
            ])
        
        # Network errors
        elif 'network' in error_lower or 'unreachable' in error_lower:
            short_msg = "Network error"
            suggestions.extend([
                "• Check your internet connection",
                "• Verify network firewalls aren't blocking the request",
                "• Try accessing other websites to confirm connectivity"
            ])
        
        # Build full error message
        full_msg = f"❌ Error: {error_message}\n\n"
        if suggestions:
            full_msg += "💡 Suggestions:\n" + "\n".join(suggestions)
        else:
            full_msg += "💡 Suggestions:\n• Check the error details above\n• Review your request configuration\n• Try the request again"
        
        return {
            'short': short_msg,
            'full': full_msg
        }
    
    def _display_response(self, response: ApiResponse):
        """Display the HTTP response in the response viewer."""
        # Make response viewer visible when we have a response
        if hasattr(self, 'request_response_splitter'):
            response_viewer = self.request_response_splitter.widget(1)
            if response_viewer and not response_viewer.isVisible():
                response_viewer.setVisible(True)
                # Ensure panel is expanded when showing response
                if hasattr(self, 'response_panel_collapsed') and self.response_panel_collapsed:
                    self._toggle_response_panel()
        
        # Store response for later use (Raw/Pretty toggle)
        self.current_response = response
        try:
            self.current_response_raw = response.text if hasattr(response, 'text') else str(response.response.text)
        except AttributeError:
            self.current_response_raw = ""
        
        # Update status badge with professional styling
        try:
            status_code = response.status_code if hasattr(response, 'status_code') else response.response.status_code
            self.status_badge.set_status(status_code)
        except AttributeError:
            self.status_badge.set_status(0)
        self.status_badge.setVisible(True)
        
        # Determine status color and icon based on status code
        try:
            status_code = response.status_code if hasattr(response, 'status_code') else response.response.status_code
        except AttributeError:
            status_code = 0
        
        if 200 <= status_code < 300:
            color = "#4CAF50"  # Green for success
            icon = "✓"
            status_text = "Success"
        elif 300 <= status_code < 400:
            color = "#2196F3"  # Blue for redirect
            icon = "↻"
            status_text = "Redirect"
        elif 400 <= status_code < 500:
            color = "#FF9800"  # Orange for client error
            icon = "⚠"
            status_text = "Client Error"
        elif 500 <= status_code < 600:
            color = "#F44336"  # Red for server error
            icon = "✗"
            status_text = "Server Error"
        else:
            color = "#666666"  # Gray for unknown
            icon = "?"
            status_text = "Unknown"
        
        # Display status info with color (kept for backward compatibility)
        self.status_label.setText(f"{status_text}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")
        
        try:
            elapsed_time = response.elapsed_time if hasattr(response, 'elapsed_time') else 0
            self.time_label.setText(f"⏱ {elapsed_time:.2f}s")
        except AttributeError:
            self.time_label.setText(f"⏱ 0.00s")
        self.time_label.setStyleSheet("font-weight: bold;")
        
        # Display size with warning for large responses
        size_text = self._format_size(response.size)
        if response.size > 1_000_000:  # > 1MB
            self.size_label.setText(f"📦 {size_text} ⚠️")
            self.size_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            self._show_status(f"Large response: {size_text}", "warning")
        else:
            self.size_label.setText(f"📦 {size_text}")
            self.size_label.setStyleSheet("font-weight: bold;")
        
        # Determine content type
        try:
            headers = response.headers if hasattr(response, 'headers') else response.response.headers
            content_type = headers.get('content-type', headers.get('Content-Type', ''))
        except AttributeError:
            content_type = ''
        
        # Display response body with formatting
        is_json = False
        try:
            # Try to parse and pretty-print JSON
            try:
                response_text = response.text if hasattr(response, 'text') else str(response.response.text)
            except AttributeError:
                response_text = ""
            json_data = json.loads(response_text)
            self.current_response_pretty = json.dumps(json_data, indent=2)
            is_json = True
        except (json.JSONDecodeError, ValueError):
            # Not JSON, use raw text
            try:
                self.current_response_pretty = response.text if hasattr(response, 'text') else str(response.response.text)
            except AttributeError:
                self.current_response_pretty = ""
        
        # Display based on current mode (Pretty/Raw)
        if self.is_pretty_mode:
            self.response_body.setPlainText(self.current_response_pretty)
        else:
            self.response_body.setPlainText(self.current_response_raw)
        
        # Switch to response body view (from empty state)
        self.response_stack.setCurrentWidget(self.response_body)
        
        # Apply syntax highlighting based on content type
        dark_mode = (self.current_theme == 'dark')
        if is_json:
            apply_syntax_highlighting(self.response_body, 'application/json', dark_mode)
        elif any(x in content_type.lower() for x in ['xml', 'html']):
            apply_syntax_highlighting(self.response_body, content_type, dark_mode)
        
        # Display response headers
        try:
            headers = response.headers if hasattr(response, 'headers') else response.response.headers
        except AttributeError:
            headers = {}
        
        self.response_headers_table.setRowCount(len(headers))
        for i, (key, value) in enumerate(headers.items()):
            self.response_headers_table.setItem(i, 0, QTableWidgetItem(key))
            self.response_headers_table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        # Update variable extraction widget with response
        request_name = getattr(self, 'current_request_name', None) or "Unnamed Request"
        self.variable_extraction_widget.set_response(response, request_name)
    
    def _clear_response_viewer(self):
        """Clear the response viewer."""
        # Hide response viewer when clearing
        if hasattr(self, 'request_response_splitter'):
            response_viewer = self.request_response_splitter.widget(1)
            if response_viewer:
                response_viewer.setVisible(False)
        
        self.status_badge.setVisible(False)
        self.status_label.setText("Status: -")
        self.time_label.setText("Time: -")
        self.size_label.setText("Size: -")
        self.response_body.clear()
        self.response_headers_table.clearContents()
        self.response_headers_table.setRowCount(0)
        self.request_details_viewer.clear()
        self.current_response = None
        self.current_response_raw = ""
        self.current_response_pretty = ""
        self.current_request_details = None
        # Switch back to empty state
        self.response_stack.setCurrentWidget(self.response_empty_state)
        
        # Clear Extract Variables widget - hide tree and form groups
        self.variable_extraction_widget.empty_label.setText("📭 Send a request to extract variables from the response")
        self.variable_extraction_widget.empty_label.setStyleSheet("color: #999; font-size: 14px; padding: 40px;")
        self.variable_extraction_widget.empty_label.show()
        # Hide the header (hint) and tree/form groups
        self.variable_extraction_widget.header.hide()
        for widget in self.variable_extraction_widget.findChildren(QGroupBox):
            widget.hide()
        
        # Clear test results viewer
        if hasattr(self, 'test_results_viewer') and self.test_results_viewer is not None:
            self.test_results_viewer.clear()
        # Hide test results tab when clearing response
        if hasattr(self, 'test_results_tab_index'):
            self.response_tabs.setTabVisible(self.test_results_tab_index, False)
    
    def _convert_body_for_display(self, body: str, headers: Dict[str, str]) -> str:
        """
        Convert body to the format that was actually sent to the server.
        This mirrors the conversion logic in ApiClient.execute_request().
        
        Args:
            body: The body string (may be JSON)
            headers: Request headers containing Content-Type
            
        Returns:
            The body in the format that was sent (URL-encoded, multipart, or JSON)
        """
        if not body:
            return body
            
        # Check Content-Type header
        content_type = ''
        for key, value in (headers or {}).items():
            if key.lower() == 'content-type':
                content_type = value.lower()
                break
        
        if 'application/x-www-form-urlencoded' in content_type:
            # Convert JSON to URL-encoded format
            try:
                import json
                from urllib.parse import urlencode
                body_dict = json.loads(body)
                return urlencode(body_dict)
            except (json.JSONDecodeError, ValueError):
                # If not JSON, return as-is (already URL-encoded)
                return body
        elif 'multipart/form-data' in content_type:
            # For multipart, show the key-value pairs (requests library handles encoding)
            try:
                import json
                body_dict = json.loads(body)
                result = "Multipart Form Data:\n"
                for key, value in body_dict.items():
                    result += f"  {key}: {value}\n"
                return result.rstrip()
            except (json.JSONDecodeError, ValueError):
                return body
        else:
            # For JSON or other content types, return as-is
            return body
    
    def _update_request_details_viewer(self):
        """Update the request details viewer with the current request information."""
        if not self.current_request_details:
            self.request_details_viewer.clear()
            return
        
        details = self.current_request_details
        request_text = f"Method: {details.get('method', 'GET')}\n"
        request_text += f"URL: {details.get('url', '-')}\n"
        
        if details.get('params'):
            request_text += "\nQuery Parameters:\n"
            for key, value in details['params'].items():
                request_text += f"  {key}: {value}\n"
        
        if details.get('headers'):
            request_text += "\nHeaders:\n"
            for key, value in details['headers'].items():
                request_text += f"  {key}: {value}\n"
        
        if details.get('body'):
            # Convert body to the format that was actually sent
            display_body = self._convert_body_for_display(
                details['body'], 
                details.get('headers', {})
            )
            request_text += f"\nBody:\n{display_body}\n"
        
        if details.get('auth_type') and details['auth_type'] != 'None':
            request_text += f"\nAuth Type: {details['auth_type']}\n"
            if details.get('auth_token') and details['auth_type'] == 'Bearer Token':
                # Show only first 20 chars of token for security
                token = details['auth_token']
                if len(token) > 20:
                    token = token[:20] + "..."
                request_text += f"Auth Token: {token}\n"
        
        # Show cookies sent with request
        try:
            cookies = self.api_client.get_cookies()
            if cookies:
                # Filter cookies that match the request domain
                from urllib.parse import urlparse
                url_parsed = urlparse(details.get('url', ''))
                domain = url_parsed.netloc
                
                matching_cookies = []
                for cookie in cookies:
                    cookie_domain = cookie.get('domain', '')
                    if domain == cookie_domain or domain.endswith(cookie_domain.lstrip('.')):
                        matching_cookies.append(cookie)
                
                if matching_cookies:
                    request_text += f"\nCookies Sent ({len(matching_cookies)}):  \n"
                    for cookie in matching_cookies:
                        request_text += f"  {cookie['name']}: {cookie['value'][:50]}{'...' if len(cookie['value']) > 50 else ''}\n"
        except Exception as e:
            print(f"[DEBUG] Error showing cookies in request details: {e}")
        
        self.request_details_viewer.setPlainText(request_text)
    
    def _restore_response(self, response_data: Dict):
        """Restore a response from saved data."""
        # Create a mock ApiResponse-like object from the saved data
        class MockResponse:
            def __init__(self, data):
                self.status_code = data['status_code']
                self.headers = data['headers']
                self.text = data['text']
                self.size = data['size']
                self.elapsed_time = data['elapsed_time']
            
            def json(self):
                import json
                return json.loads(self.text)
        
        # Create mock response object
        mock_response = MockResponse(response_data)
        self.current_response = mock_response
        self.current_response_raw = response_data['text']
        
        # Update status badge
        self.status_badge.set_status(response_data['status_code'])
        self.status_badge.setVisible(True)
        
        # Determine status text
        status_code = response_data['status_code']
        if 200 <= status_code < 300:
            status_text = "Success"
        elif 300 <= status_code < 400:
            status_text = "Redirect"
        elif 400 <= status_code < 500:
            status_text = "Client Error"
        elif 500 <= status_code < 600:
            status_text = "Server Error"
        else:
            status_text = "Unknown"
        
        # Update status info
        self.status_label.setText(f"{status_text}")
        self.time_label.setText(f"⏱️ {response_data['elapsed_time']:.2f}s")
        self.size_label.setText(f"📦 {self._format_size(response_data['size'])}")
        
        # Display response body
        self.response_body.setPlainText(response_data['text'])
        
        # Try to pretty print if JSON
        try:
            import json
            parsed = json.loads(response_data['text'])
            self.current_response_pretty = json.dumps(parsed, indent=2)
            if self.response_pretty_checkbox.isChecked():
                self.response_body.setPlainText(self.current_response_pretty)
        except:
            self.current_response_pretty = response_data['text']
        
        # Display response headers
        self.response_headers_table.clearContents()
        self.response_headers_table.setRowCount(len(response_data['headers']))
        for i, (key, value) in enumerate(response_data['headers'].items()):
            self.response_headers_table.setItem(i, 0, QTableWidgetItem(key))
            self.response_headers_table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        # Switch to response body view
        self.response_stack.setCurrentWidget(self.response_body)
        
        # Restore Extract Variables widget with response
        request_name = getattr(self, 'current_request_name', None) or "Unnamed Request"
        self.variable_extraction_widget.set_response(mock_response, request_name)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def _toggle_pretty_raw(self):
        """Toggle between Pretty (formatted) and Raw view."""
        if not self.current_response:
            return
        
        self.is_pretty_mode = self.pretty_raw_btn.isChecked()
        
        # Update button text
        if self.is_pretty_mode:
            self.pretty_raw_btn.setText("📄 Pretty")
            self.response_body.setPlainText(self.current_response_pretty)
        else:
            self.pretty_raw_btn.setText("📝 Raw")
            self.response_body.setPlainText(self.current_response_raw)
        
        # Reapply syntax highlighting
        dark_mode = (self.current_theme == 'dark')
        content_type = self.current_response.headers.get('content-type', 
                                                         self.current_response.headers.get('Content-Type', ''))
        
        # Detect JSON
        is_json = False
        try:
            json.loads(self.current_response.text)
            is_json = True
        except:
            pass
        
        if is_json:
            apply_syntax_highlighting(self.response_body, 'application/json', dark_mode)
        elif any(x in content_type.lower() for x in ['xml', 'html']):
            apply_syntax_highlighting(self.response_body, content_type, dark_mode)
    
    def _toggle_word_wrap(self):
        """Toggle word wrap in response viewer."""
        if self.word_wrap_btn.isChecked():
            self.response_body.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            self.word_wrap_btn.setText("↔️ Wrap ✓")
        else:
            self.response_body.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            self.word_wrap_btn.setText("↔️ Wrap")
    
    def _copy_response(self):
        """Copy the response body to clipboard."""
        response_text = self.response_body.toPlainText()
        if response_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(response_text)
            
            # Show brief success message (non-blocking)
            self.copy_response_btn.setText("✓ Copied!")
            self.copy_response_btn.setStyleSheet("""
                QPushButton#copyButton {
                    background-color: #4CAF50;
                    color: white;
                }
            """)
            
            # Reset button after 2 seconds using QTimer
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self._reset_copy_button())
        else:
            QMessageBox.warning(self, "Warning", "No response to copy!")
    
    def _toggle_response_panel(self):
        """Toggle the response panel collapsed/expanded state."""
        self.response_panel_collapsed = not self.response_panel_collapsed
        
        if self.response_panel_collapsed:
            # Store current sizes before collapsing
            self.splitter_sizes_before_collapse = self.request_response_splitter.sizes()
            
            # Hide content and adjust splitter to minimal response panel size
            self.response_content_widget.hide()
            self.response_collapse_btn.setText("▶")  # Right arrow when collapsed
            
            # Get total height and set response panel to minimal height (40px for status bar only)
            total_height = sum(self.request_response_splitter.sizes())
            self.request_response_splitter.setSizes([total_height - 40, 40])
        else:
            self.response_content_widget.show()
            self.response_collapse_btn.setText("▼")  # Down arrow when expanded
            
            # Restore previous sizes or use default proportions
            if hasattr(self, 'splitter_sizes_before_collapse'):
                self.request_response_splitter.setSizes(self.splitter_sizes_before_collapse)
            else:
                # Default: 45-55 split
                total_height = sum(self.request_response_splitter.sizes())
                self.request_response_splitter.setSizes([int(total_height * 0.45), int(total_height * 0.55)])
    
    def _expand_response_panel(self):
        """Ensure response panel is expanded (called when sending request)."""
        if self.response_panel_collapsed:
            self._toggle_response_panel()
    
    def _toggle_recent_requests(self):
        """Toggle the recent requests panel visibility with overlay positioning."""
        is_visible = self.recent_requests_widget.isVisible()
        
        if not is_visible:
            # Hide history panel if visible (mutual exclusion)
            if self.history_panel_widget.isVisible():
                self.history_panel_widget.setVisible(False)
                self.history_btn.setChecked(False)
            
            # Show the overlay - position it on the right side of center_container
            container_width = self.center_container.width()
            overlay_width = 350  # Fixed width for the overlay
            
            # Position the overlay on the right side, full height
            self.recent_requests_widget.setGeometry(
                container_width - overlay_width,  # X position (right-aligned)
                0,  # Y position (top)
                overlay_width,  # Width
                self.center_container.height()  # Height (full height of container)
            )
            self.recent_requests_widget.setVisible(True)
            self.recent_requests_widget.raise_()  # Ensure it's on top
        else:
            # Hide the overlay
            self.recent_requests_widget.setVisible(False)
        
        self.recent_requests_btn.setChecked(not is_visible)
    
    def _switch_left_panel(self, panel_name: str):
        """Switch between left panels (collections, settings, git_sync, variable_inspector, etc.)."""
        # Use stored main splitter reference
        main_splitter = self.main_splitter
        
        if panel_name == self.current_left_panel:
            # Clicking the same panel toggles it
            if panel_name == 'collections':
                is_visible = self.collections_pane.isVisible()
                self.collections_pane.setVisible(not is_visible)
                self.collections_toggle_btn.setChecked(not is_visible)
                # Update splitter sizes (6 widgets: collections, settings, git, variables, environments, center)
                if not is_visible:  # About to show
                    main_splitter.setSizes([400, 0, 0, 0, 0, 1000])
                else:  # About to hide
                    main_splitter.setSizes([0, 0, 0, 0, 0, 1400])
            elif panel_name == 'settings':
                is_visible = self.settings_pane.isVisible()
                self.settings_pane.setVisible(not is_visible)
                self.settings_toggle_btn.setChecked(not is_visible)
                # Update splitter sizes
                if not is_visible:  # About to show
                    main_splitter.setSizes([0, 400, 0, 0, 0, 1000])
                else:  # About to hide
                    main_splitter.setSizes([0, 0, 0, 0, 0, 1400])
            elif panel_name == 'git_sync':
                is_visible = self.git_sync_pane.isVisible()
                self.git_sync_pane.setVisible(not is_visible)
                self.git_sync_toggle_btn.setChecked(not is_visible)
                # Update splitter sizes
                if not is_visible:  # About to show
                    main_splitter.setSizes([0, 0, 400, 0, 0, 1000])
                else:  # About to hide
                    main_splitter.setSizes([0, 0, 0, 0, 0, 1400])
            elif panel_name == 'variable_inspector':
                is_visible = self.variable_inspector_pane.isVisible()
                self.variable_inspector_pane.setVisible(not is_visible)
                self.variable_inspector_toggle_btn.setChecked(not is_visible)
                # Update splitter sizes
                if not is_visible:  # About to show
                    main_splitter.setSizes([0, 0, 0, 400, 0, 1000])
                else:  # About to hide
                    main_splitter.setSizes([0, 0, 0, 0, 0, 1400])
                # Refresh data when opening
                if not is_visible:
                    self._refresh_variable_inspector_panel()
            elif panel_name == 'environments':
                is_visible = self.environments_pane.isVisible()
                self.environments_pane.setVisible(not is_visible)
                self.environments_toggle_btn.setChecked(not is_visible)
                # Update splitter sizes
                if not is_visible:  # About to show
                    main_splitter.setSizes([0, 0, 0, 0, 400, 1000])
                else:  # About to hide
                    main_splitter.setSizes([0, 0, 0, 0, 0, 1400])
        else:
            # Switching to a different panel
            # Hide current panel
            if self.current_left_panel == 'collections':
                self.collections_pane.setVisible(False)
                self.collections_toggle_btn.setChecked(False)
            elif self.current_left_panel == 'settings':
                self.settings_pane.setVisible(False)
                self.settings_toggle_btn.setChecked(False)
            elif self.current_left_panel == 'git_sync':
                self.git_sync_pane.setVisible(False)
                self.git_sync_toggle_btn.setChecked(False)
            elif self.current_left_panel == 'variable_inspector':
                self.variable_inspector_pane.setVisible(False)
                self.variable_inspector_toggle_btn.setChecked(False)
            elif self.current_left_panel == 'environments':
                self.environments_pane.setVisible(False)
                self.environments_toggle_btn.setChecked(False)
            
            # Show new panel and update splitter sizes
            if panel_name == 'collections':
                self.collections_pane.setVisible(True)
                self.collections_toggle_btn.setChecked(True)
                main_splitter.setSizes([400, 0, 0, 0, 0, 1000])
            elif panel_name == 'settings':
                self.settings_pane.setVisible(True)
                self.settings_toggle_btn.setChecked(True)
                main_splitter.setSizes([0, 400, 0, 0, 0, 1000])
            elif panel_name == 'git_sync':
                self.git_sync_pane.setVisible(True)
                self.git_sync_toggle_btn.setChecked(True)
                main_splitter.setSizes([0, 0, 400, 0, 0, 1000])
            elif panel_name == 'variable_inspector':
                self.variable_inspector_pane.setVisible(True)
                self.variable_inspector_toggle_btn.setChecked(True)
                main_splitter.setSizes([0, 0, 0, 400, 0, 1000])
                # Refresh data when opening
                self._refresh_variable_inspector_panel()
            elif panel_name == 'environments':
                self.environments_pane.setVisible(True)
                self.environments_toggle_btn.setChecked(True)
                main_splitter.setSizes([0, 0, 0, 0, 400, 1000])
            
            self.current_left_panel = panel_name
    
    def _create_new_request(self):
        """Create a new unsaved request in temporary mode."""
        # If a temporary tab already exists, close it
        if self.temporary_tab_index is not None:
            print(f"[DEBUG] Closing existing temporary tab {self.temporary_tab_index} before creating new request")
            self._close_temporary_tab()
        
        # Save current tab state first
        current_index = self.request_tabs.currentIndex()
        if current_index >= 0 and current_index in self.tab_states:
            self.tab_states[current_index]['ui_state'] = self._capture_current_tab_state()
            self.tab_states[current_index]['has_changes'] = self.has_unsaved_changes
        
        # Create new unsaved request data
        name = f'New Request'
        method = 'GET'
        
        # Add new tab with empty widget
        tab_index = self.request_tabs.addTab(QWidget(), "")
        
        # Set tab data for custom rendering (as temporary)
        tab_bar = self.request_tabs.tabBar()
        if isinstance(tab_bar, ColoredTabBar):
            tab_bar.set_tab_data(tab_index, method, name, has_changes=True, is_temporary=True)
            # Force tab bar to recalculate tab sizes after data is set
            tab_bar.update()
            self.request_tabs.update()
        
        # Store tab state - no request_id means it's unsaved
        # Include ALL fields to ensure proper clearing when switching to this tab
        self.tab_states[tab_index] = {
            'request_id': None,  # None indicates unsaved request
            'has_changes': True,  # Always has changes until first save
            'name': name,
            'method': method,
            'is_temporary': True,  # New requests start as temporary
            'ui_state': {
                'request_id': None,
                'collection_id': None,
                'request_name': name,
                'method': method,
                'url': '',
                'params': {},
                'headers': {},
                'body': '',
                'auth_type': 'None',
                'auth_token': '',
                'description': '',
                'has_changes': True,
                'is_new_request': True,  # Flag to show "Creating New Request" header
                'response': None,  # No response yet
                'test_results': None,  # No test results yet
                'scripts': {  # Empty scripts
                    'pre_request_script': '',
                    'post_response_script': ''
                },
                'test_assertions': [],  # No test assertions
                'ui_preferences': {  # Default UI preferences
                    'active_inner_tab': 0,
                    'active_response_tab': 0,
                    'response_view_mode': 'pretty',
                    'description_visible': False
                }
            }
        }
        
        # Set tooltip
        self.request_tabs.setTabToolTip(tab_index, f"{method} • {name} (unsaved)")
        
        # Track as temporary tab
        self.temporary_tab_index = tab_index
        print(f"[DEBUG] Created new request in temporary tab {tab_index}")
        
        # Clear the current request highlight (no request selected in collections)
        self._clear_current_request_highlight()
        
        # Switch to new tab (this will trigger _on_tab_changed)
        self.request_tabs.setCurrentIndex(tab_index)
        
        # Show tabs view
        self.center_stack.setCurrentWidget(self.tabs_container)
        
        # Update the window title to show "Creating New Request"
        self._update_request_title()
    
    def _clear_current_request_highlight(self):
        """Clear the current request highlight in the collections tree."""
        # Remove highlight from all items
        iterator = QTreeWidgetItemIterator(self.collections_tree)
        while iterator.value():
            item = iterator.value()
            item.setBackground(0, QBrush())  # Clear background
            iterator += 1
    
    def _reset_copy_button(self):
        """Reset the copy button to its original state."""
        self.copy_response_btn.setText("📋 Copy Response")
        self.copy_response_btn.setStyleSheet("")  # Reset to use global stylesheet
    
    def _search_response(self, search_text: str):
        """Search for text in the response body and highlight all matches."""
        from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor, QTextDocument
        
        # Clear all previous highlights first
        cursor = self.response_body.textCursor()
        cursor.select(cursor.SelectionType.Document)
        default_format = QTextCharFormat()
        cursor.setCharFormat(default_format)
        cursor.clearSelection()
        
        if not search_text:
            # Disable navigation buttons and hide counter
            self.search_prev_btn.setEnabled(False)
            self.search_next_btn.setEnabled(False)
            self.search_counter_label.setVisible(False)
            self.search_matches = []
            self.current_match_index = -1
            return
        
        # Store all match positions
        self.search_matches = []
        self.current_match_index = -1
        
        # Create highlight formats
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#FFEB3B"))  # Yellow highlight for all matches
        highlight_format.setForeground(QColor("#000000"))  # Black text
        
        current_highlight_format = QTextCharFormat()
        current_highlight_format.setBackground(QColor("#FF9800"))  # Orange for current match
        current_highlight_format.setForeground(QColor("#FFFFFF"))  # White text
        
        # Get document text for searching
        document = self.response_body.document()
        text = document.toPlainText()
        
        # Find all matches (case-insensitive, non-overlapping)
        start = 0
        while True:
            index = text.lower().find(search_text.lower(), start)
            if index == -1:
                break
            self.search_matches.append((index, index + len(search_text)))
            start = index + len(search_text)  # Move past the current match to avoid overlaps
        
        # If no matches found
        if not self.search_matches:
            self.search_counter_label.setText("No matches")
            self.search_counter_label.setVisible(True)
            self.search_prev_btn.setEnabled(False)
            self.search_next_btn.setEnabled(False)
            return
        
        # Highlight all matches
        cursor.beginEditBlock()
        
        for i, (start, end) in enumerate(self.search_matches):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            
            # First match gets current highlight, others get regular highlight
            if i == 0:
                cursor.setCharFormat(current_highlight_format)
                self.current_match_index = 0
            else:
                cursor.setCharFormat(highlight_format)
        
        cursor.endEditBlock()
        
        # Update counter and enable buttons
        total_matches = len(self.search_matches)
        self.search_counter_label.setText(f"1 of {total_matches}")
        self.search_counter_label.setVisible(True)
        self.search_prev_btn.setEnabled(total_matches > 1)
        self.search_next_btn.setEnabled(total_matches > 1)
        
        # Scroll to first match
        if self.search_matches:
            cursor = self.response_body.textCursor()
            cursor.setPosition(self.search_matches[0][0])
            self.response_body.setTextCursor(cursor)
            self.response_body.ensureCursorVisible()
    
    def _search_next(self):
        """Navigate to the next search match."""
        if not self.search_matches or self.current_match_index == -1:
            return
        
        from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
        
        # Create highlight formats
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#FFEB3B"))  # Yellow
        highlight_format.setForeground(QColor("#000000"))
        
        current_highlight_format = QTextCharFormat()
        current_highlight_format.setBackground(QColor("#FF9800"))  # Orange
        current_highlight_format.setForeground(QColor("#FFFFFF"))
        
        # Clear current highlight
        cursor = self.response_body.textCursor()
        cursor.beginEditBlock()
        
        # Unhighlight current match (back to yellow)
        start, end = self.search_matches[self.current_match_index]
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(highlight_format)
        
        # Move to next match (wrap around)
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        
        # Highlight new current match (orange)
        start, end = self.search_matches[self.current_match_index]
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(current_highlight_format)
        
        cursor.endEditBlock()
        
        # Update counter
        self.search_counter_label.setText(f"{self.current_match_index + 1} of {len(self.search_matches)}")
        
        # Scroll to match
        cursor = self.response_body.textCursor()
        cursor.setPosition(start)
        self.response_body.setTextCursor(cursor)
        self.response_body.ensureCursorVisible()
    
    def _search_previous(self):
        """Navigate to the previous search match."""
        if not self.search_matches or self.current_match_index == -1:
            return
        
        from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
        
        # Create highlight formats
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#FFEB3B"))  # Yellow
        highlight_format.setForeground(QColor("#000000"))
        
        current_highlight_format = QTextCharFormat()
        current_highlight_format.setBackground(QColor("#FF9800"))  # Orange
        current_highlight_format.setForeground(QColor("#FFFFFF"))
        
        # Clear current highlight
        cursor = self.response_body.textCursor()
        cursor.beginEditBlock()
        
        # Unhighlight current match (back to yellow)
        start, end = self.search_matches[self.current_match_index]
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(highlight_format)
        
        # Move to previous match (wrap around)
        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        
        # Highlight new current match (orange)
        start, end = self.search_matches[self.current_match_index]
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(current_highlight_format)
        
        cursor.endEditBlock()
        
        # Update counter
        self.search_counter_label.setText(f"{self.current_match_index + 1} of {len(self.search_matches)}")
        
        # Scroll to match
        cursor = self.response_body.textCursor()
        cursor.setPosition(start)
        self.response_body.setTextCursor(cursor)
        self.response_body.ensureCursorVisible()
    
    # ==================== Environment Management ====================
    
    def _load_environments(self):
        """Load all environments into the combo box."""
        # Save current selection
        current_env_id = self.env_combo.currentData()
        
        # Clear and reload
        self.env_combo.clear()
        self.env_combo.addItem("No Environment", None)
        
        environments = self.db.get_all_environments()
        for env in environments:
            self.env_combo.addItem(env['name'], env['id'])
        
        # Restore selection if possible
        if current_env_id:
            for i in range(self.env_combo.count()):
                if self.env_combo.itemData(i) == current_env_id:
                    self.env_combo.setCurrentIndex(i)
                    break
    
    def _load_extracted_variables(self):
        """Load extracted variables from database into environment manager."""
        # Get all extracted variables from database
        all_extracted = self.db.get_all_extracted_variables()
        
        # Convert to dictionary format {name: value}
        extracted_vars = {}
        for var in all_extracted:
            extracted_vars[var['name']] = var['value']
        
        # Set in environment manager
        self.env_manager.set_extracted_variables(extracted_vars)
    
    def _on_environment_changed(self, index: int):
        """Handle environment selection change."""
        env_id = self.env_combo.itemData(index)
        
        if env_id is None:
            # No environment selected
            self.env_manager.clear_active_environment()
        else:
            # Load environment
            env = self.db.get_environment(env_id)
            if env:
                self.env_manager.set_active_environment(env)
        
        # Reload extracted variables (they're always available regardless of environment)
        self._load_extracted_variables()
        
        # Refresh variable highlighting in auth token field
        if hasattr(self, 'auth_token_input'):
            self.auth_token_input.update()
        
        # Refresh variable highlighting in body
        if hasattr(self, 'body_highlighter'):
            self.body_highlighter.rehighlight()
    
    def _on_env_change_refresh_vars(self):
        """Auto-refresh variables panel when environment changes."""
        # Only refresh if the variables panel is visible
        if self.variable_inspector_pane.isVisible():
            self._refresh_variable_inspector_panel()
    
    def _on_environment_changed_refresh(self, env_id: int = None):
        """Handle environment creation/update/deletion - refresh combo and panel."""
        self._load_environments()
        
        # Refresh environments panel if visible
        if self.environments_pane.isVisible():
            self.environments_pane.refresh()
    
    # ==================== Import/Export ====================
    
    def _export_collection(self):
        """Export the selected collection to a JSON file."""
        if not self.current_collection_id:
            QMessageBox.warning(self, "Warning", "Please select a collection to export!")
            return
        
        try:
            # Get collection info for default filename
            collection = self.db.get_collection(self.current_collection_id)
            if not collection:
                QMessageBox.warning(self, "Warning", "Collection not found!")
                return
            
            # Ask user for export format
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QDialogButtonBox
            
            format_dialog = QDialog(self)
            format_dialog.setWindowTitle("Select Export Format")
            format_dialog.setModal(True)
            format_dialog.resize(350, 150)
            
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Choose export format:"))
            
            internal_radio = QRadioButton("Internal Format (default)")
            internal_radio.setChecked(True)
            internal_radio.setToolTip("Our custom JSON format")
            layout.addWidget(internal_radio)
            
            postman_radio = QRadioButton("Postman Collection v2.1")
            postman_radio.setToolTip("Compatible with Postman and other tools")
            layout.addWidget(postman_radio)
            
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(format_dialog.accept)
            buttons.rejected.connect(format_dialog.reject)
            layout.addWidget(buttons)
            
            format_dialog.setLayout(layout)
            
            if format_dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            # Determine format
            export_format = 'postman' if postman_radio.isChecked() else 'internal'
            
            # Generate safe filename
            default_filename = get_safe_filename(collection['name'])
            
            # Ask user where to save
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Collection",
                default_filename,
                "JSON Files (*.json);;All Files (*.*)"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Export
            success = self.exporter.export_collection_to_file(
                self.current_collection_id,
                file_path,
                format=export_format
            )
            
            if success:
                format_name = "Postman Collection v2.1" if export_format == 'postman' else "Internal Format"
                self._show_status(f"Collection '{collection['name']}' exported successfully", "success")
                QMessageBox.information(
                    self, "Success",
                    f"Collection '{collection['name']}' exported successfully!\n\nFormat: {format_name}\nFile: {file_path}"
                )
            else:
                self._show_status("Failed to export collection", "error")
                QMessageBox.critical(self, "Error", "Failed to export collection!")
                
        except Exception as e:
            self._show_status(f"Export failed: {str(e)[:30]}...", "error")
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
    def _import_collection(self):
        """Import a collection from a JSON file."""
        try:
            # Ask user to select file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Collection",
                "",
                "JSON Files (*.json);;All Files (*.*)"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Ask about duplicate handling
            reply = QMessageBox.question(
                self,
                "Import Options",
                "If a collection with the same name exists:\n\n"
                "YES - Rename the imported collection\n"
                "NO - Skip import\n"
                "CANCEL - Cancel import",
                QMessageBox.StandardButton.Yes | 
                QMessageBox.StandardButton.No | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            rename_if_exists = (reply == QMessageBox.StandardButton.Yes)
            skip_if_exists = (reply == QMessageBox.StandardButton.No)
            
            # Import
            success, message, collection_id = self.importer.import_collection_from_file(
                file_path,
                rename_if_exists=rename_if_exists,
                skip_if_exists=skip_if_exists
            )
            
            if success:
                # Reload collections tree
                self._load_collections()
                
                # Select the imported collection
                if collection_id:
                    self._select_collection_by_id(collection_id)
                
                self._show_status("Collection imported successfully", "success")
                QMessageBox.information(self, "Success", message)
            else:
                self._show_status("Import was not completed", "warning")
                QMessageBox.warning(self, "Import Failed", message)
                
        except Exception as e:
            self._show_status(f"Import failed: {str(e)[:30]}...", "error")
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
    
    def _import_curl(self):
        """Import a cURL command and create a new request."""
        # Check if any collections exist
        collections = self.db.get_all_collections()
        if not collections:
            QMessageBox.warning(
                self,
                "No Collections",
                "Please create a collection first before importing cURL commands."
            )
            return
        
        # Open cURL import dialog
        from src.ui.dialogs.curl_import_dialog import CurlImportDialog
        curl_dialog = CurlImportDialog(self)
        if curl_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        request_data = curl_dialog.get_request_data()
        if not request_data:
            return
        
        # Generate default name from URL
        default_name = f"{request_data['method']} {request_data['url'].split('/')[-1] or 'Request'}"
        
        # Ask for request name and target collection
        from src.ui.dialogs.request_destination_dialog import RequestDestinationDialog
        dest_dialog = RequestDestinationDialog(
            parent=self,
            db_manager=self.db,
            default_name=default_name,
            current_collection_id=self.current_collection_id
        )
        
        if dest_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        request_name = dest_dialog.get_request_name()
        collection_id = dest_dialog.get_collection_id()
        
        if not request_name or not collection_id:
            return
        
        try:
            # Create the request in the database with all data
            request_id = self.db.create_request(
                collection_id=collection_id,
                name=request_name,
                url=request_data['url'],
                method=request_data['method'],
                params=request_data.get('params'),
                headers=request_data.get('headers'),
                body=request_data.get('body'),
                body_type='raw'
            )
            
            # Reload the collection tree
            self._load_collections()
            
            # Ensure collections pane is visible
            if not self.collections_pane.isVisible():
                self.collections_pane.setVisible(True)
                self.collections_toggle_btn.setChecked(True)
            
            # Expand collection and show the new request in the tree
            self._expand_and_show_request(request_id)
            
            # Load the new request into the editor
            self._load_request(request_id)
            
            # Auto-sync if enabled
            self._auto_sync_to_filesystem()
            
            QMessageBox.information(
                self,
                "cURL Imported",
                f"Successfully created request '{request_name}' from cURL command!"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to create request from cURL:\n{str(e)}"
            )
    
    def _import_openapi(self):
        """Import an OpenAPI/Swagger specification."""
        from PyQt6.QtWidgets import QFileDialog, QInputDialog
        from src.features.openapi_importer import import_openapi_spec
        
        # Select OpenAPI spec file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import OpenAPI/Swagger Spec",
            "",
            "OpenAPI Files (*.json *.yaml *.yml);;JSON Files (*.json);;YAML Files (*.yaml *.yml);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Import the spec
            collection, summary = import_openapi_spec(file_path)
            
            # Show import summary dialog
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("OpenAPI Import Summary")
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout(dialog)
            
            info_text = f"""
<h3>{summary['title']}</h3>
<p><b>Version:</b> {summary['version']}</p>
<p><b>OpenAPI Version:</b> {summary['openapi_version']}</p>
<p><b>Base URL:</b> {summary['base_url']}</p>
<p><b>Endpoints:</b> {summary['endpoint_count']} ({', '.join(summary['methods'])})</p>
<p><b>Description:</b> {summary['description'] or 'N/A'}</p>
<hr>
<p>Import as a new collection?</p>
            """
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            info_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(info_label)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            # Ask for collection name (auto-suggest unique name if needed)
            suggested_name = self._get_unique_collection_name(collection['name'])
            collection_name, ok = QInputDialog.getText(
                self,
                "Collection Name",
                "Enter a name for the imported collection:",
                text=suggested_name
            )
            
            if not ok or not collection_name.strip():
                return
            
            collection_name = collection_name.strip()
            
            # Check if the name already exists (in case user changed it)
            existing_collections = self.db.get_all_collections()
            existing_names = {col['name'] for col in existing_collections}
            
            if collection_name in existing_names:
                # Suggest an alternative
                unique_name = self._get_unique_collection_name(collection_name)
                reply = QMessageBox.question(
                    self,
                    "Collection Already Exists",
                    f"A collection named '{collection_name}' already exists.\n\n"
                    f"Would you like to import as '{unique_name}' instead?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    collection_name = unique_name
                else:
                    return  # Cancel the import
            
            # Create the collection
            collection_id = self.db.create_collection(collection_name)
            
            # Create all requests
            created_count = 0
            for request in collection['requests']:
                try:
                    request_id = self.db.create_request(
                        collection_id=collection_id,
                        name=request['name'],
                        url=request['url'],
                        method=request['method'],
                        description=request.get('description', ''),
                        body_type='raw'
                    )
                    
                    # Update request with all details at once
                    self.db.update_request(
                        request_id=request_id,
                        name=request['name'],
                        method=request['method'],
                        url=request['url'],
                        params=request.get('params'),
                        headers=request.get('headers'),
                        body=request.get('body'),
                        auth_type=request.get('auth_type', 'None'),
                        auth_token=request.get('auth_token'),
                        description=request.get('description', ''),
                        folder_id=None,
                        body_type='raw'
                    )
                    
                    created_count += 1
                    
                except Exception as e:
                    print(f"Error creating request {request['name']}: {e}")
                    continue
            
            # Reload collections
            self._load_collections()
            
            # Select the new collection
            self._select_collection_by_id(collection_id)
            
            # Auto-sync if enabled
            self._auto_sync_to_filesystem()
            
            # Show success message
            QMessageBox.information(
                self,
                "Import Successful",
                f"✓ Successfully imported {created_count} requests from {summary['title']}"
            )
            
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "File Not Found",
                "The selected OpenAPI spec file was not found."
            )
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Invalid Spec",
                f"The OpenAPI spec is invalid:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import OpenAPI spec:\n{str(e)}"
            )
    
    def _select_collection_by_id(self, collection_id: int):
        """Select a collection in the tree by its ID."""
        root = self.collections_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('id') == collection_id:
                self.collections_tree.setCurrentItem(item)
                break
    
    # ==================== Request History ====================
    
    def _save_to_history(self, response: Optional[ApiResponse] = None, 
                        error_message: Optional[str] = None,
                        scan_id: Optional[int] = None):
        """Save the current request to history."""
        try:
            # Get ACTUAL request details that were sent (after variable substitution)
            # Use current_request_details if available (contains substituted values)
            if hasattr(self, 'current_request_details') and self.current_request_details:
                method = self.current_request_details.get('method', self.method_combo.currentText())
                url = self.current_request_details.get('url', self.url_input.text())
                params = self.current_request_details.get('params') or self._get_table_as_dict(self.params_table)
                headers = self.current_request_details.get('headers') or self._get_table_as_dict(self.headers_table)
                body = self.current_request_details.get('body', self.body_input.toPlainText())
                auth_type = self.current_request_details.get('auth_type', self.auth_type_combo.currentText())
                auth_token = self.current_request_details.get('auth_token', self.auth_token_input.text())
            else:
                # Fallback to UI values if current_request_details not available
                method = self.method_combo.currentText()
                url = self.url_input.text()
                params = self._get_table_as_dict(self.params_table)
                headers = self._get_table_as_dict(self.headers_table)
                body = self.body_input.toPlainText()
                auth_type = self.auth_type_combo.currentText()
                auth_token = self.auth_token_input.text()
            
            # Get request name if available
            request_name = None
            if self.current_request_id:
                request = self.db.get_request(self.current_request_id)
                if request:
                    request_name = request['name']
            
            # Prepare response data
            response_status = None
            response_headers = None
            response_body = None
            response_time = None
            response_size = None
            
            if response:
                try:
                    response_status = response.status_code if hasattr(response, 'status_code') else response.response.status_code
                    response_headers = response.headers if hasattr(response, 'headers') else response.response.headers
                    response_body = response.text if hasattr(response, 'text') else str(response.response.text)
                    response_time = response.elapsed_time if hasattr(response, 'elapsed_time') else 0
                    response_size = response.size if hasattr(response, 'size') else 0
                except AttributeError as e:
                    print(f"[ERROR] Could not extract response data for history: {e}")
                    response_status = 0
                    response_headers = {}
                    response_body = ""
                    response_time = 0
                    response_size = 0
            
            # Save to database
            self.db.save_request_history(
                timestamp=datetime.now().isoformat(),
                method=method,
                url=url,
                collection_id=self.current_collection_id,
                request_id=self.current_request_id,
                request_name=request_name,
                request_params=params if params else None,
                request_headers=headers if headers else None,
                request_body=body if body else None,
                request_auth_type=auth_type,
                request_auth_token=auth_token if auth_token else None,
                response_status=response_status,
                response_headers=response_headers,
                response_body=response_body,
                response_time=response_time,
                response_size=response_size,
                error_message=error_message,
                scan_id=scan_id
            )
        except Exception as e:
            print(f"Failed to save history: {e}")
    
    def _toggle_history_panel(self):
        """Toggle the history panel visibility with overlay positioning."""
        is_visible = self.history_panel_widget.isVisible()
        
        if not is_visible:
            # Hide recent requests panel if visible (mutual exclusion)
            if self.recent_requests_widget.isVisible():
                self.recent_requests_widget.setVisible(False)
                self.recent_requests_btn.setChecked(False)
            
            # Show the history overlay - position it on the right side of center_container
            container_width = self.center_container.width()
            overlay_width = 800  # Width for history panel as specified
            
            # Position the overlay on the right side, full height
            self.history_panel_widget.setGeometry(
                container_width - overlay_width,  # X position (right-aligned)
                0,  # Y position (top)
                overlay_width,  # Width
                self.center_container.height()  # Height (full height of container)
            )
            self.history_panel_widget.setVisible(True)
            self.history_panel_widget.raise_()  # Ensure it's on top
            
            # Load history data when opening
            self.history_panel_widget.load_history()
        else:
            # Hide the overlay
            self.history_panel_widget.setVisible(False)
        
        self.history_btn.setChecked(not is_visible)
    
    def _show_variable_inspector(self):
        """Show the variable inspector dialog."""
        dialog = VariableInspectorDialog(self)
        
        # Load current variables
        self._load_inspector_variables(dialog)
        
        # Show dialog
        dialog.exec()
    
    def _load_inspector_variables(self, dialog: VariableInspectorDialog):
        """Load variables into the inspector."""
        # Get environment variables
        environment_vars = {}
        environment_name = None
        if hasattr(self, 'env_manager') and self.env_manager:
            if self.env_manager.has_active_environment():
                environment_name = self.env_manager.get_active_environment_name()
                environment_vars = self.env_manager.get_active_variables()
        
        # Get collection variables
        collection_vars = {}
        if hasattr(self, 'current_collection_id') and self.current_collection_id:
            # Use the correct database method to get collection variables
            collection_vars = self.db.get_collection_variables(self.current_collection_id)
        
        # Get extracted variables
        extracted_vars = self.db.get_all_extracted_variables()
        
        # Load into dialog
        dialog.load_variables(
            environment_vars=environment_vars,
            collection_vars=collection_vars,
            extracted_vars=extracted_vars,
            environment_name=environment_name
        )
    
    def refresh_variable_inspector(self):
        """Refresh the variable inspector (called by inspector dialog)."""
        # Find the inspector dialog if it's open
        for widget in self.findChildren(VariableInspectorDialog):
            if widget.isVisible():
                self._load_inspector_variables(widget)
    
    def _refresh_variable_inspector_panel(self):
        """Refresh the variable inspector panel with current data."""
        print(f"[DEBUG] === Refreshing Variable Inspector Panel ===")
        # Get environment variables
        environment_vars = {}
        environment_name = None
        environment_id = None
        if hasattr(self, 'env_manager') and self.env_manager:
            if self.env_manager.has_active_environment():
                environment_name = self.env_manager.get_active_environment_name()
                environment_vars = self.env_manager.get_active_variables()
                # Get environment ID from the active environment
                if self.env_manager.active_environment:
                    environment_id = self.env_manager.active_environment.get('id')
                print(f"[DEBUG] Active environment: {environment_name} (ID: {environment_id})")
                print(f"[DEBUG] Variables from env_manager: {list(environment_vars.keys())}")
                
                # Double-check database directly
                if environment_id:
                    db_env = self.db.get_environment(environment_id)
                    if db_env:
                        print(f"[DEBUG] Variables from database: {list(db_env.get('variables', {}).keys())}")
        
        # Get collection variables
        collection_vars = []
        if hasattr(self, 'current_collection_id') and self.current_collection_id:
            collection_vars = self.db.get_collection_variables_with_metadata(self.current_collection_id)
        
        # Get extracted variables
        extracted_vars = self.db.get_all_extracted_variables()
        print(f"[DEBUG] Extracted variables count: {len(extracted_vars)}")
        
        # Load into panel
        print(f"[DEBUG] Loading into panel...")
        self.variable_inspector_pane.load_variables(
            environment_vars=environment_vars,
            collection_vars=collection_vars,
            extracted_vars=extracted_vars,
            environment_name=environment_name,
            environment_id=environment_id,
            collection_id=self.current_collection_id if hasattr(self, 'current_collection_id') else None
        )
        print(f"[DEBUG] === Refresh Complete ===\n")
    
    def _on_variable_edited(self, scope: str, name: str, new_value: str):
        """Handle variable edit from inspector panel."""
        try:
            if scope == 'environment':
                # Update environment variable
                if hasattr(self, 'env_manager') and self.env_manager:
                    if self.env_manager.has_active_environment() and self.env_manager.active_environment:
                        env_id = self.env_manager.active_environment.get('id')
                        env = self.db.get_environment(env_id)
                        if env:
                            # Update the variable in the dictionary
                            variables = env.get('variables', {})
                            variables[name] = new_value
                            # Save back to database
                            self.db.update_environment(env_id, env['name'], variables)
                            # Refresh environment manager
                            self.env_manager.set_active_environment(self.db.get_environment(env_id))
                            self._show_status(f"Updated variable: {name}", "success")
            elif scope == 'collection':
                # Update collection variable
                # Find the variable ID by name
                if hasattr(self, 'current_collection_id') and self.current_collection_id:
                    collection_vars = self.db.get_collection_variables_with_metadata(self.current_collection_id)
                    for var in collection_vars:
                        if var['key'] == name:
                            self.db.update_collection_variable(var['id'], value=new_value)
                            self._show_status(f"Updated collection variable: {name}", "success")
                            break
            elif scope == 'extracted':
                # Find and update extracted variable
                extracted_vars = self.db.get_all_extracted_variables()
                for var in extracted_vars:
                    if var['name'] == name:
                        # Delete old and create new (since there's no update method)
                        self.db.delete_extracted_variable(var['id'])
                        self.db.create_extracted_variable(
                            name=name,
                            value=new_value,
                            source_request_id=var.get('source_request_id'),
                            source_request_name=var.get('source_request_name'),
                            json_path=var.get('json_path'),
                            description=var.get('description')
                        )
                        # Reload extracted variables into environment manager
                        self._load_extracted_variables()
                        # Refresh variable highlighting
                        if hasattr(self, 'body_highlighter'):
                            self.body_highlighter.rehighlight()
                        if hasattr(self, 'auth_token_input'):
                            self.auth_token_input.update()
                        self._show_status(f"Updated variable: {name}", "success")
                        break
            
            # Refresh panel
            self._refresh_variable_inspector_panel()
        except Exception as e:
            print(f"Error updating variable: {e}")
            self._show_status(f"Failed to update: {str(e)}", "error")
    
    def _handle_variable_deleted(self, scope: str, name: str):
        """Wrapper for _on_variable_deleted to help debug signal connection."""
        print(f"[DEBUG] +++++ _handle_variable_deleted WRAPPER CALLED +++++")
        print(f"[DEBUG] Wrapper received: scope='{scope}', name='{name}'")
        self._on_variable_deleted(scope, name)
    
    def _on_variable_deleted(self, scope: str, name: str):
        """Handle variable deletion from inspector panel."""
        print(f"[DEBUG] ============ _on_variable_deleted CALLED ============")
        print(f"[DEBUG] Received parameters: scope='{scope}', name='{name}'")
        print(f"[DEBUG] Parameter types: scope type={type(scope)}, name type={type(name)}")
        try:
            print(f"[DEBUG] Inside try block, about to process deletion")
            print(f"[DEBUG] Deleting variable: scope={scope}, name={name}")
            if scope == 'environment':
                # Delete environment variable
                if hasattr(self, 'env_manager') and self.env_manager:
                    if self.env_manager.has_active_environment() and self.env_manager.active_environment:
                        env_id = self.env_manager.active_environment.get('id')
                        print(f"[DEBUG] Environment ID: {env_id}")
                        env = self.db.get_environment(env_id)
                        if env:
                            print(f"[DEBUG] Environment loaded: {env['name']}")
                            # Remove the variable from the dictionary
                            variables = env.get('variables', {})
                            print(f"[DEBUG] Variables before delete: {list(variables.keys())}")
                            if name in variables:
                                del variables[name]
                                print(f"[DEBUG] Variables after delete: {list(variables.keys())}")
                                # Save back to database
                                self.db.update_environment(env_id, env['name'], variables)
                                print(f"[DEBUG] Updated environment in database")
                                # Refresh environment manager
                                updated_env = self.db.get_environment(env_id)
                                if updated_env:
                                    print(f"[DEBUG] Reloaded environment from DB: {list(updated_env.get('variables', {}).keys())}")
                                    self.env_manager.set_active_environment(updated_env)
                                    print(f"[DEBUG] Updated env_manager")
                                self._show_status(f"Deleted variable: {name}", "success")
                            else:
                                print(f"[DEBUG] Variable {name} not found in environment variables")
                                self._show_status(f"Variable {name} not found", "warning")
                        else:
                            print(f"[DEBUG] Environment not found")
                    else:
                        print(f"[DEBUG] No active environment")
            elif scope == 'collection':
                # Delete collection variable
                if hasattr(self, 'current_collection_id') and self.current_collection_id:
                    collection_vars = self.db.get_collection_variables_with_metadata(self.current_collection_id)
                    print(f"[DEBUG] Collection variables before delete: {[v['key'] for v in collection_vars]}")
                    found = False
                    for var in collection_vars:
                        if var['key'] == name:
                            self.db.delete_collection_variable(var['id'])
                            print(f"[DEBUG] Deleted collection variable with ID: {var['id']}")
                            self._show_status(f"Deleted collection variable: {name}", "success")
                            found = True
                            break
                    if not found:
                        print(f"[DEBUG] Variable {name} not found in collection variables")
                        self._show_status(f"Variable {name} not found", "warning")
            elif scope == 'extracted':
                # Find and delete extracted variable
                extracted_vars = self.db.get_all_extracted_variables()
                print(f"[DEBUG] Looking for extracted variable {name} in {len(extracted_vars)} variables")
                for var in extracted_vars:
                    if var['name'] == name:
                        print(f"[DEBUG] Found extracted variable, deleting ID: {var['id']}")
                        self.db.delete_extracted_variable(var['id'])
                        # Reload extracted variables into environment manager
                        self._load_extracted_variables()
                        # Refresh variable highlighting
                        if hasattr(self, 'body_highlighter'):
                            self.body_highlighter.rehighlight()
                        if hasattr(self, 'auth_token_input'):
                            self.auth_token_input.update()
                        self._show_status(f"Deleted variable: {name}", "success")
                        break
            
            # Refresh panel
            print(f"[DEBUG] Refreshing variables panel")
            self._refresh_variable_inspector_panel()
        except Exception as e:
            print(f"[ERROR] Error deleting variable: {e}")
            import traceback
            traceback.print_exc()
            self._show_status(f"Failed to delete: {str(e)}", "error")
    
    def _on_variable_added(self, name: str, value: str):
        """Handle adding a new variable to the current environment."""
        try:
            print(f"[DEBUG] Adding variable: name={name}, value={value}")
            if hasattr(self, 'env_manager') and self.env_manager:
                if self.env_manager.has_active_environment() and self.env_manager.active_environment:
                    env_id = self.env_manager.active_environment.get('id')
                    print(f"[DEBUG] Environment ID: {env_id}")
                    env = self.db.get_environment(env_id)
                    if env:
                        print(f"[DEBUG] Environment loaded: {env['name']}")
                        # Add the variable to the dictionary
                        variables = env.get('variables', {})
                        
                        # Check if variable already exists
                        if name in variables:
                            reply = QMessageBox.question(
                                self,
                                "Variable Exists",
                                f"Variable '{name}' already exists with value: {variables[name]}\n\nOverwrite?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No
                            )
                            if reply == QMessageBox.StandardButton.No:
                                return
                        
                        variables[name] = value
                        print(f"[DEBUG] Variables after add: {list(variables.keys())}")
                        # Save back to database
                        self.db.update_environment(env_id, env['name'], variables)
                        print(f"[DEBUG] Updated environment in database")
                        # Refresh environment manager
                        updated_env = self.db.get_environment(env_id)
                        if updated_env:
                            print(f"[DEBUG] Reloaded environment from DB: {list(updated_env.get('variables', {}).keys())}")
                            self.env_manager.set_active_environment(updated_env)
                            print(f"[DEBUG] Updated env_manager")
                        self._show_status(f"Added variable: {name}", "success")
                    else:
                        print(f"[DEBUG] Environment not found")
                        self._show_status("Environment not found", "error")
                else:
                    print(f"[DEBUG] No active environment")
                    self._show_status("No active environment", "error")
            
            # Refresh panel
            print(f"[DEBUG] Refreshing variables panel")
            self._refresh_variable_inspector_panel()
        except Exception as e:
            print(f"[ERROR] Error adding variable: {e}")
            import traceback
            traceback.print_exc()
            self._show_status(f"Failed to add: {str(e)}", "error")
    
    def _on_collection_variable_added(self, collection_id: int, name: str, value: str):
        """Handle adding a new variable to a collection."""
        try:
            print(f"[DEBUG] Adding collection variable: collection_id={collection_id}, name={name}, value={value}")
            
            # Check if variable already exists
            existing_vars = self.db.get_collection_variables_with_metadata(collection_id)
            # Note: Database returns 'key' not 'name'
            existing_var = next((var for var in existing_vars if var['key'] == name), None)
            if existing_var:
                reply = QMessageBox.question(
                    self,
                    "Variable Exists",
                    f"Collection variable '{name}' already exists.\n\nOverwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                # Delete existing variable by ID (not by collection_id, name)
                self.db.delete_collection_variable(existing_var['id'])
            
            # Add the variable to the collection
            self.db.create_collection_variable(collection_id, name, value)
            print(f"[DEBUG] Added collection variable to database")
            self._show_status(f"Added collection variable: {name}", "success")
            
            # Refresh panel
            print(f"[DEBUG] Refreshing variables panel")
            self._refresh_variable_inspector_panel()
        except Exception as e:
            print(f"[ERROR] Error adding collection variable: {e}")
            import traceback
            traceback.print_exc()
            self._show_status(f"Failed to add collection variable: {str(e)}", "error")
    
    def _update_environments_var_counts(self):
        """Update variable counts in the environments panel without full refresh."""
        if hasattr(self, 'environments_pane'):
            self.environments_pane.update_variable_counts()
        
        # Also refresh variable highlighting since variables changed
        if hasattr(self, 'auth_token_input'):
            self.auth_token_input.update()
        
        if hasattr(self, 'body_highlighter'):
            self.body_highlighter.rehighlight()
    
    def _open_variable_library(self):
        """Open the variable library dialog."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Variable Library")
        dialog.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Add variable library widget
        library = VariableLibraryWidget()
        library.variable_deleted.connect(self._on_library_variable_deleted)
        library.refresh_requested.connect(lambda: self._refresh_variable_library(library))
        layout.addWidget(library)
        
        # Load variables
        self._refresh_variable_library(library)
        
        dialog.exec()
    
    def _refresh_variable_library(self, library: VariableLibraryWidget):
        """Refresh variable library with latest data."""
        variables = self.db.get_all_extracted_variables()
        library.set_variables(variables)
    
    def _on_variable_extracted(self, name: str, value: str, json_path: str):
        """Handle variable extraction from response."""
        try:
            # Get source request info
            request_name = getattr(self, 'current_request_name', None) or "Unnamed Request"
            
            # Save to database
            self.db.create_extracted_variable(
                name=name,
                value=value,
                source_request_id=self.current_request_id,
                source_request_name=request_name,
                json_path=json_path
            )
            
            # Reload extracted variables into environment manager
            self._load_extracted_variables()
            
            # Refresh variable highlighting
            if hasattr(self, 'body_highlighter'):
                self.body_highlighter.rehighlight()
            if hasattr(self, 'auth_token_input'):
                self.auth_token_input.update()
            
            # Show success status
            self._show_status(f"Variable '{name}' saved! Use {{{{extracted.{name}}}}} in requests", "success")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save variable: {str(e)}"
            )
    
    def _on_library_variable_deleted(self, variable_id: int):
        """Handle variable deletion from variable library dialog."""
        try:
            self.db.delete_extracted_variable(variable_id)
            
            # Reload extracted variables into environment manager
            self._load_extracted_variables()
            
            # Refresh variable highlighting
            if hasattr(self, 'body_highlighter'):
                self.body_highlighter.rehighlight()
            if hasattr(self, 'auth_token_input'):
                self.auth_token_input.update()
            
            self._show_status("Variable deleted", "success")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete variable: {str(e)}"
            )
    
    def _on_security_report_export(self, format_type: str):
        """Handle security report export request."""
        try:
            # Get current scan results from security scan tab
            scan_results = self.security_scan_tab.get_scan_results()
            if not scan_results:
                QMessageBox.warning(
                    self,
                    "No Scan Results",
                    "No security scan results to export. Run a security scan first."
                )
                return
            
            # Prepare default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if format_type == "html":
                default_name = f"security_report_{timestamp}.html"
                file_filter = "HTML Files (*.html);;All Files (*)"
            else:  # json
                default_name = f"security_report_{timestamp}.json"
                file_filter = "JSON Files (*.json);;All Files (*)"
            
            # Get save path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Security Report",
                default_name,
                file_filter
            )
            
            if not file_path:
                return
            
            # Generate and save report
            report_generator = SecurityReportGenerator()
            if format_type == "html":
                report_content = report_generator.generate_html_report(scan_results)
            else:
                report_content = report_generator.generate_json_report(scan_results)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self._show_status(f"Security report exported to {file_path}", "success")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export security report: {str(e)}"
            )
    
    def _auto_run_security_scan(self, response: ApiResponse) -> Optional[int]:
        """
        Automatically run security scan on response if auto-scan is enabled.
        
        Args:
            response: The API response to scan
            
        Returns:
            scan_id if scan was performed, None otherwise
        """
        try:
            # Get request details
            url = self.url_input.text().strip()
            method = self.method_combo.currentText()
            request_headers = self._get_table_as_dict(self.headers_table)
            
            # Get response data
            response_headers = dict(response.headers) if hasattr(response, 'headers') else dict(response.response.headers)
            response_body = response.text if hasattr(response, 'text') else str(response.response.text)
            response_status = response.status_code if hasattr(response, 'status_code') else response.response.status_code
            
            # Perform security scan
            scan_results = self.security_scanner.scan_response(
                url=url,
                method=method,
                response_headers=response_headers,
                response_body=response_body,
                response_status=response_status,
                request_headers=request_headers
            )
            
            # Save to database
            scan_id = self.db.create_security_scan(
                request_id=self.current_request_id if hasattr(self, 'current_request_id') else None,
                url=url,
                method=method,
                timestamp=datetime.now().isoformat(),
                findings_count=len(scan_results),
                critical_count=sum(1 for f in scan_results if f.severity == 'Critical'),
                high_count=sum(1 for f in scan_results if f.severity == 'High'),
                medium_count=sum(1 for f in scan_results if f.severity == 'Medium'),
                low_count=sum(1 for f in scan_results if f.severity == 'Low'),
                info_count=sum(1 for f in scan_results if f.severity == 'Info')
            )
            
            # Save findings
            for finding in scan_results:
                self.db.create_security_finding(
                    scan_id=scan_id,
                    check_id=finding.check_id,
                    title=finding.title,
                    severity=finding.severity,
                    description=finding.description,
                    recommendation=finding.recommendation,
                    timestamp=finding.timestamp,
                    evidence=finding.evidence,
                    cwe_id=finding.cwe_id,
                    owasp_category=finding.owasp_category
                )
            
            # Get findings from database (includes id field needed by UI)
            findings_from_db = self.db.get_security_findings(scan_id)
            
            # Display results in SecurityScanTab
            severity_stats = {
                'critical': sum(1 for f in scan_results if f.severity == 'critical'),
                'high': sum(1 for f in scan_results if f.severity == 'high'),
                'medium': sum(1 for f in scan_results if f.severity == 'medium'),
                'low': sum(1 for f in scan_results if f.severity == 'low'),
                'info': sum(1 for f in scan_results if f.severity == 'info')
            }
            self.security_scan_tab.set_scan_results(scan_id, findings_from_db, severity_stats)
            
            # Update tab text with finding summary (tab is always visible)
            if scan_results:
                critical_count = severity_stats['critical']
                high_count = severity_stats['high']
                if critical_count > 0:
                    self.response_tabs.setTabText(self.security_scan_tab_index, f"Security Scan ({critical_count} Critical)")
                elif high_count > 0:
                    self.response_tabs.setTabText(self.security_scan_tab_index, f"Security Scan ({high_count} High)")
                else:
                    self.response_tabs.setTabText(self.security_scan_tab_index, f"Security Scan ({len(scan_results)} issues)")
            else:
                # No findings - show success checkmark
                self.response_tabs.setTabText(self.security_scan_tab_index, "Security Scan ✓")
            
            print(f"[Security] Auto-scan complete: {len(scan_results)} findings")
            
            return scan_id  # Return scan_id for linking to history
            
        except Exception as e:
            print(f"[Security] Auto-scan failed: {str(e)}")
            # Don't show error to user - auto-scan is background operation
            return None
    
    def _show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog."""
        help_text = """
<h2>Keyboard Shortcuts</h2>

<h3>Tab Management:</h3>
<table cellpadding="5">
<tr><td><b>Ctrl+W</b></td><td>Close current tab</td></tr>
<tr><td><b>Double-click request</b></td><td>Open request in new tab</td></tr>
<tr><td><b>Middle-click tab</b></td><td>Close tab</td></tr>
</table>

<h3>Request Operations:</h3>
<table cellpadding="5">
<tr><td><b>Ctrl+Enter</b></td><td>Send request</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Save request</td></tr>
<tr><td><b>Delete</b></td><td>Delete selected item</td></tr>
</table>

<h3>Panel Toggles:</h3>
<table cellpadding="5">
<tr><td><b>Alt+C</b></td><td>Toggle Collections panel</td></tr>
<tr><td><b>Alt+E</b></td><td>Toggle Environments panel</td></tr>
<tr><td><b>Alt+V</b></td><td>Toggle Variables panel</td></tr>
<tr><td><b>Alt+G</b></td><td>Toggle Git Sync panel</td></tr>
<tr><td><b>Alt+H</b></td><td>Toggle History panel</td></tr>
<tr><td><b>Alt+R</b></td><td>Toggle Recent Requests panel</td></tr>
</table>

<h3>Navigation:</h3>
<table cellpadding="5">
<tr><td><b>Ctrl+L</b></td><td>Focus URL bar</td></tr>
<tr><td><b>Single-click collection</b></td><td>Expand/collapse collection</td></tr>
<tr><td><b>Double-click collection</b></td><td>Expand/collapse collection</td></tr>
</table>

<h3>Tools:</h3>
<table cellpadding="5">
<tr><td><b>Ctrl+Shift+C</b></td><td>Generate code snippet</td></tr>
</table>

<h3>Visual Indicators:</h3>
<table cellpadding="5">
<tr><td><b>Bold + Arrow (→)</b></td><td>Active request in current tab</td></tr>
<tr><td><b>Gray dot (•)</b></td><td>Request open in another tab</td></tr>
<tr><td><b>Bold + Blue dot (•)</b></td><td>Collection contains active request</td></tr>
<tr><td><b>Blue dot (•)</b></td><td>Collection has open requests</td></tr>
</table>

<h3>Help:</h3>
<table cellpadding="5">
<tr><td><b>Ctrl+/</b></td><td>Show this help</td></tr>
</table>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Keyboard Shortcuts")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(help_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()
    
    def _replay_from_history(self, history_entry: Dict):
        """Replay a request from history in a persistent tab."""
        try:
            # If a temporary tab exists, close it (replay is an intentional action)
            if self.temporary_tab_index is not None:
                print(f"[DEBUG] Closing temporary tab {self.temporary_tab_index} before replaying from history")
                self._close_temporary_tab()
            
            # Get or create a tab for this request
            current_tab_index = self.request_tabs.currentIndex()
            
            # Check if current tab is empty (no request loaded)
            if current_tab_index >= 0 and current_tab_index in self.tab_states:
                tab_state = self.tab_states[current_tab_index]
                if tab_state['request_id'] is None:
                    # Use current empty tab
                    tab_index = current_tab_index
                else:
                    # Create a new persistent tab
                    tab_index = self._create_new_tab()
            else:
                # Create a new persistent tab
                tab_index = self._create_new_tab()
            
            # Switch to the tab
            self.request_tabs.setCurrentIndex(tab_index)
            
            # Load request data into the global widgets (they show content for current tab)
            self.method_combo.setCurrentText(history_entry['method'])
            self.url_input.setText(history_entry['url'])
            
            # Load params
            params = history_entry.get('request_params')
            if params:
                self._load_dict_to_table(params, self.params_table)
            else:
                self.params_table.clearContents()
                self.params_table.setRowCount(5)
            
            # Load headers
            headers = history_entry.get('request_headers')
            if headers:
                self._load_dict_to_table(headers, self.headers_table)
            else:
                self.headers_table.clearContents()
                self.headers_table.setRowCount(5)
            
            # Load body
            body = history_entry.get('request_body') or ''
            self.body_input.setPlainText(body)
            
            # Load auth
            auth_type = history_entry.get('request_auth_type', 'None')
            self.auth_type_combo.setCurrentText(auth_type)
            
            auth_token = history_entry.get('request_auth_token') or ''
            self.auth_token_input.setText(auth_token)
            
            # Update widget visibility (signals aren't blocked here, but set explicitly for consistency)
            self.bearer_token_widget.setVisible(auth_type == 'Bearer Token')
            self.oauth_widget.setVisible(auth_type == 'OAuth 2.0')
            
            # Mark tab as having unsaved changes
            self.tab_states[tab_index]['has_changes'] = True
            self.tab_states[tab_index]['name'] = f"{history_entry['method']} (from history)"
            self._update_tab_title(tab_index)
            
            # Show the request editor (switch from empty state if needed)
            self.center_stack.setCurrentWidget(self.tabs_container)
            
            # Show success message
            self._show_status(
                f"Request loaded from history: {history_entry['method']} {history_entry['url']}"
            , "success")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to replay request: {str(e)}")
    
    # ==================== Code Generation ====================
    
    def _show_options_menu(self):
        """Show the options menu below the menu button."""
        # Position menu below the button
        button_pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft())
        self.options_menu.exec(button_pos)
    
    def _copy_as_curl(self):
        """Copy the current request as a cURL command to clipboard."""
        try:
            # Get current request data
            method = self.method_combo.currentText()
            url = self.url_input.text().strip()
            
            if not url:
                QMessageBox.warning(self, "Warning", "Please enter a URL first!")
                return
            
            # Get request details
            params = self._get_table_as_dict(self.params_table)
            headers = self._get_table_as_dict(self.headers_table)
            body = self.body_input.toPlainText()
            auth_type = self.auth_type_combo.currentText()
            
            # Get auth token (Bearer or OAuth)
            auth_token = None
            if auth_type == 'Bearer Token':
                auth_token = self.auth_token_input.text()
            elif auth_type == 'OAuth 2.0' and self.current_oauth_token:
                auth_token = self.current_oauth_token.get('access_token')
                auth_type = 'Bearer Token'  # For code generation
            
            # Import CodeGenerator
            from src.features.code_generator import CodeGenerator
            
            # Generate cURL command
            curl_command = CodeGenerator.generate_curl(
                method=method,
                url=url,
                params=params if params else None,
                headers=headers if headers else None,
                body=body if body else None,
                auth_type=auth_type,
                auth_token=auth_token
            )
            
            # Copy to clipboard
            from PyQt6.QtGui import QClipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(curl_command)
            
            # Show success message
            QMessageBox.information(self, "✅ Copied to clipboard", "cURL command copied successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy as cURL: {str(e)}")
    
    def _generate_code(self):
        """Generate code snippet for the current request."""
        try:
            # Get current request data
            method = self.method_combo.currentText()
            url = self.url_input.text().strip()
            
            if not url:
                QMessageBox.warning(self, "Warning", "Please enter a URL first!")
                return
            
            # Get request details
            params = self._get_table_as_dict(self.params_table)
            headers = self._get_table_as_dict(self.headers_table)
            body = self.body_input.toPlainText()
            auth_type = self.auth_type_combo.currentText()
            
            # Get auth token (Bearer or OAuth)
            auth_token = None
            if auth_type == 'Bearer Token':
                auth_token = self.auth_token_input.text()
            elif auth_type == 'OAuth 2.0' and self.current_oauth_token:
                auth_token = self.current_oauth_token.get('access_token')
                auth_type = 'Bearer Token'  # For code generation
            
            # Open code snippet dialog
            dialog = CodeSnippetDialog(
                method=method,
                url=url,
                params=params if params else None,
                headers=headers if headers else None,
                body=body if body else None,
                auth_type=auth_type,
                auth_token=auth_token,
                parent=self
            )
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate code: {str(e)}")
    
    # ==================== OAuth 2.0 ====================
    
    def _configure_oauth(self):
        """Open OAuth configuration dialog."""
        try:
            dialog = OAuthConfigDialog(self.db, self)
            dialog.config_selected.connect(self._on_oauth_configured)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open OAuth dialog: {str(e)}")
    
    def _on_oauth_configured(self, data: Dict):
        """Handle OAuth configuration selection."""
        try:
            self.current_oauth_config = data['config']
            self.current_oauth_token = data['token']
            
            # Update UI
            config_name = self.current_oauth_config['name']
            token_type = self.current_oauth_token.get('token_type', 'Bearer')
            expires_at = self.current_oauth_token.get('expires_at', 'Unknown')
            
            status_text = f"✅ Using OAuth: {config_name}\n"
            status_text += f"Token Type: {token_type}\n"
            if expires_at and expires_at != 'Unknown':
                status_text += f"Expires: {expires_at[:19]}"
            
            self.oauth_status_label.setText(status_text)
            self.oauth_status_label.setStyleSheet("color: #4CAF50;")
            
            self.oauth_refresh_btn.setEnabled(bool(self.current_oauth_token.get('refresh_token')))
            self.oauth_clear_btn.setEnabled(True)
            
            QMessageBox.information(
                self, "OAuth Configured",
                f"OAuth token from '{config_name}' is now active.\n\n"
                "Your requests will automatically include the access token."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure OAuth: {str(e)}")
    
    def _refresh_oauth_token(self):
        """Refresh the OAuth access token."""
        if not self.current_oauth_config or not self.current_oauth_token:
            return
        
        try:
            refresh_token = self.current_oauth_token.get('refresh_token')
            if not refresh_token:
                QMessageBox.warning(self, "Cannot Refresh",
                                  "No refresh token available. Please re-authorize.")
                return
            
            oauth_manager = OAuthManager()
            
            # Refresh token
            token_data = oauth_manager.refresh_access_token(
                token_url=self.current_oauth_config['token_url'],
                refresh_token=refresh_token,
                client_id=self.current_oauth_config['client_id'],
                client_secret=self.current_oauth_config['client_secret'],
                scope=self.current_oauth_config.get('scope')
            )
            
            # Calculate expiry
            expires_at = None
            if 'expires_in' in token_data:
                expires_at = OAuthManager.calculate_expiry_time(token_data['expires_in'])
            
            # Save new token
            self.db.save_oauth_token(
                config_id=self.current_oauth_config['id'],
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', refresh_token),
                token_type=token_data.get('token_type', 'Bearer'),
                expires_at=expires_at,
                scope=token_data.get('scope')
            )
            
            # Update current token
            self.current_oauth_token = self.db.get_oauth_token(self.current_oauth_config['id'])
            
            QMessageBox.information(self, "Success", "✅ OAuth token refreshed successfully!")
            
            # Update status
            self._on_oauth_configured({
                'config': self.current_oauth_config,
                'token': self.current_oauth_token
            })
            
        except Exception as e:
            QMessageBox.critical(self, "Refresh Failed",
                               f"Failed to refresh OAuth token:\n\n{str(e)}\n\n"
                               "Please re-authorize using Configure OAuth.")
    
    def _clear_oauth(self):
        """Clear the current OAuth configuration."""
        self.current_oauth_config = None
        self.current_oauth_token = None
        
        self.oauth_status_label.setText("No OAuth token configured")
        self.oauth_status_label.setStyleSheet("color: #999; font-style: italic;")
        self.oauth_refresh_btn.setEnabled(False)
        self.oauth_clear_btn.setEnabled(False)
        
        QMessageBox.information(self, "Cleared", "OAuth configuration cleared.")
    
    def _get_authorization_header(self) -> Optional[str]:
        """Get the authorization header value based on current auth type."""
        auth_type = self.auth_type_combo.currentText()
        
        if auth_type == 'Bearer Token':
            token = self.auth_token_input.text().strip()
            if token:
                return f"Bearer {token}"
        elif auth_type == 'OAuth 2.0' and self.current_oauth_token:
            # Check if token is expired
            if OAuthManager.is_token_expired(self.current_oauth_token.get('expires_at')):
                QMessageBox.warning(
                    self, "Token Expired",
                    "OAuth token has expired. Please refresh or re-authorize."
                )
                return None
            
            token = self.current_oauth_token['access_token']
            token_type = self.current_oauth_token.get('token_type', 'Bearer')
            return f"{token_type} {token}"
        
        return None
    
    # ==================== API Testing / Assertions ====================
    
    def _on_tests_changed(self):
        """Handle test assertions being modified."""
        # Update tab counts immediately when tests change
        self._update_tab_counts()
        # Mark as changed
        self._mark_as_changed()
    
    def _save_test_assertions(self):
        """Save test assertions for the current request."""
        if not self.current_request_id:
            return
        
        try:
            # Delete existing assertions
            self.db.delete_all_assertions_for_request(self.current_request_id)
            
            # Get assertions from UI
            assertions = self.test_tab.get_assertions()
            
            # Save each assertion
            for assertion in assertions:
                self.db.create_test_assertion(
                    request_id=self.current_request_id,
                    assertion_type=assertion['assertion_type'],
                    operator=assertion['operator'],
                    field=assertion.get('field'),
                    expected_value=assertion.get('expected_value'),
                    enabled=assertion.get('enabled', True)
                )
        except Exception as e:
            print(f"Error saving test assertions: {e}")
    
    def _load_test_assertions(self, request_id: int):
        """Load test assertions for a request."""
        try:
            assertions = self.db.get_test_assertions(request_id)
            self.test_tab.load_assertions(assertions)
            self.test_tab.set_request_id(request_id)
        except Exception as e:
            print(f"Error loading test assertions: {e}")
            self.test_tab.clear()
    
    def _run_collection_tests(self):
        """Run all tests in the selected collection."""
        try:
            item = self.collections_tree.currentItem()
            if not item:
                QMessageBox.warning(self, "No Selection", "Please select a collection.")
                return
            
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data.get('type') != 'collection':
                QMessageBox.warning(self, "Invalid Selection", "Please select a collection to run tests.")
                return
            
            collection_id = data['id']
            collection_name = data['name']
            
            # Open test runner dialog
            dialog = CollectionTestRunnerDialog(
                self.db, self.api_client, collection_id, collection_name,
                self.env_manager, self
            )
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run tests: {str(e)}")
    
    def _execute_tests_on_response(self, response: ApiResponse):
        """Execute test assertions on a response."""
        try:
            # Get current request ID
            item = self.collections_tree.currentItem()
            if not item:
                return
            
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data.get('type') != 'request':
                return
            
            request_id = data['id']
            
            # Get test assertions for this request
            assertions = self.db.get_test_assertions(request_id)
            if not assertions:
                return
            
            # Convert to TestAssertion objects
            test_assertions = []
            for a in assertions:
                if a.get('enabled', True):
                    test_assertions.append(TestAssertion(
                        assertion_id=a['id'],
                        assertion_type=a['assertion_type'],
                        operator=a['operator'],
                        field=a.get('field'),
                        expected_value=a.get('expected_value'),
                        enabled=a.get('enabled', True)
                    ))
            
            if not test_assertions:
                return
            
            # Run tests
            test_results = TestEngine.evaluate_all(test_assertions, response)
            
            # Save results to database
            for result in test_results:
                actual_value_str = str(result.actual_value) if result.actual_value is not None else None
                self.db.save_test_result(
                    request_id=request_id,
                    assertion_id=result.assertion.id,
                    passed=result.passed,
                    actual_value=actual_value_str,
                    error_message=result.error_message
                )
            
            # Get summary
            summary = TestEngine.get_summary(test_results)
            
            # Convert results to display format
            display_results = []
            for result in test_results:
                display_results.append({
                    'passed': result.passed,
                    'assertion_type': result.assertion.type,
                    'field': result.assertion.field,
                    'operator': result.assertion.operator,
                    'expected_value': result.assertion.expected_value,
                    'actual_value': result.actual_value,
                    'error_message': result.error_message
                })
            
            # Display results
            self.test_results_viewer.display_results(display_results, summary)
            print(f"[DEBUG] Test results displayed: {len(display_results)} results, Summary: {summary}")
            
            # Show test results tab when tests are run
            if hasattr(self, 'test_results_tab_index'):
                self.response_tabs.setTabVisible(self.test_results_tab_index, True)
                # Switch to test results tab to show the results
                self.response_tabs.setCurrentIndex(self.test_results_tab_index)
            
            # Store test results for tab state persistence
            self._current_test_results = {
                'results': display_results,
                'summary': summary
            }
            
        except Exception as e:
            print(f"Error executing tests: {e}")
            # Don't show error to user, just log it
    
    # ==================== Git Sync Methods ====================
    
    def _init_git_sync(self):
        """Initialize Git sync on startup if a workspace is configured."""
        workspaces = self.db.get_all_git_workspaces()
        
        if workspaces:
            # Get the most recently updated enabled workspace
            active = next((w for w in workspaces if w['enabled']), None)
            
            if active:
                self._setup_git_sync(active['project_path'])
                self._update_git_sync_status()
                
                # Check for changes on startup
                if self.git_sync_manager:
                    status = self.git_sync_manager.get_sync_status()
                    if status.status == SyncStatus.STATUS_NEEDS_PULL:
                        # Ask user if they want to pull changes
                        reply = QMessageBox.question(
                            self,
                            "Git Sync: Changes Detected",
                            f"Found {len(status.changes.get('new_files', [])) + len(status.changes.get('modified_files', []))} updated file(s) in .postmini/\n\n"
                            "Would you like to import these changes?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        
                        if reply == QMessageBox.StandardButton.Yes:
                            self._auto_sync_from_filesystem()
    
    def _setup_git_sync(self, project_path: str):
        """Setup Git sync manager for a project path."""
        config = GitSyncConfig(project_path)
        self.git_sync_manager = GitSyncManager(self.db, config)
        self.secrets_manager = SecretsManager(str(config.secrets_path))
        self.git_workspace = self.db.get_git_workspace_by_path(project_path)
        
        # Start periodic status refresh
        if not self.git_sync_timer.isActive():
            self.git_sync_timer.start()
    
    def _open_git_sync_dialog(self):
        """Open the Git sync configuration dialog."""
        dialog = GitSyncDialog(self.db, self)
        
        # Connect signals
        dialog.sync_enabled.connect(self._on_git_sync_enabled)
        dialog.sync_disabled.connect(self._on_git_sync_disabled)
        dialog.sync_performed.connect(self._on_sync_performed)
        
        dialog.exec()
        
        # Refresh status after dialog closes to ensure it's up-to-date
        if self.git_sync_manager:
            self._update_git_sync_status()
    
    def _on_git_sync_enabled(self, project_path: str):
        """Handle Git sync being enabled."""
        self._setup_git_sync(project_path)
        self._update_git_sync_status()
        
        # Reload collections and environments
        self._load_collections()
        self._load_environments()
    
    def _on_git_sync_disabled(self):
        """Handle Git sync being disabled."""
        self.git_sync_manager = None
        self.secrets_manager = None
        self.git_workspace = None
        
        # Stop periodic status refresh
        if self.git_sync_timer.isActive():
            self.git_sync_timer.stop()
        
        self._update_git_sync_status()
    
    def _on_sync_performed(self, message: str):
        """Handle sync operation being performed."""
        # Reload collections and environments
        self._load_collections()
        self._load_environments()
        self._update_git_sync_status()
    
    def _update_git_sync_status(self):
        """Update the Git sync status indicator in toolbar."""
        if not self.git_sync_manager or not self.git_workspace:
            self.git_sync_status_label.setText("Files: Not Synced")
            self.git_sync_status_label.setStyleSheet("color: #999; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("File sync not enabled - collections not saved to filesystem")
            return
        
        # Get sync status
        status = self.git_sync_manager.get_sync_status()
        
        # Update label style (dark-mode friendly)
        if status.status == SyncStatus.STATUS_SYNCED:
            self.git_sync_status_label.setText("Files: ✅ Synced")
            self.git_sync_status_label.setStyleSheet("color: #4CAF50; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Database and .postmini/ files are in sync")
        elif status.status == SyncStatus.STATUS_NEEDS_PULL:
            self.git_sync_status_label.setText("Files: 📥 Import Available")
            self.git_sync_status_label.setStyleSheet("color: #2196F3; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Files in .postmini/ have changes - open Git Sync panel to import")
        elif status.status == SyncStatus.STATUS_NEEDS_PUSH:
            self.git_sync_status_label.setText("Files: 📤 Export Needed")
            self.git_sync_status_label.setStyleSheet("color: #FF9800; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Database has unsaved changes - open Git Sync panel to export")
        elif status.status == SyncStatus.STATUS_CONFLICT:
            self.git_sync_status_label.setText("Files: ⚠️ Conflict")
            self.git_sync_status_label.setStyleSheet("color: #F44336; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Both database and files have changes - open Git Sync panel")
        else:
            self.git_sync_status_label.setText("Files: Enabled")
            self.git_sync_status_label.setStyleSheet("color: #666; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("File sync enabled")
    
    def _auto_sync_to_filesystem(self):
        """Auto-sync database to filesystem (push) if enabled."""
        if not self.git_sync_manager or not self.git_workspace:
            return
        
        if not self.git_workspace.get('auto_sync', False):
            return
        
        try:
            success, message = self.git_sync_manager.sync_to_filesystem()
            if success:
                self.db.update_git_workspace_sync_timestamp(self.git_workspace['id'])
                self._update_git_sync_status()
        except Exception as e:
            print(f"Auto-sync to filesystem failed: {e}")
    
    def _auto_sync_from_filesystem(self):
        """Auto-sync filesystem to database (pull)."""
        if not self.git_sync_manager:
            return
        
        try:
            success, message = self.git_sync_manager.sync_from_filesystem(update_existing=True)
            if success:
                if self.git_workspace:
                    self.db.update_git_workspace_sync_timestamp(self.git_workspace['id'])
                self._load_collections()
                self._load_environments()
                self._update_git_sync_status()
                
                QMessageBox.information(
                    self,
                    "Sync Complete",
                    f"Imported changes from .postmini/ folder:\n\n{message}"
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Sync Failed",
                f"Failed to import changes:\n{str(e)}"
            )
    
    def _update_theme_button(self):
        """Update the theme toggle button icon based on current theme."""
        if not hasattr(self, 'theme_toggle_btn'):
            return
        
        if self.current_theme == 'dark':
            # Dark theme active - show sun icon (click to go to light)
            self.theme_toggle_btn.setText("☀️")
            self.theme_toggle_btn.setToolTip("Switch to light theme")
            
            # Dark theme button style
            self.theme_toggle_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 3px;
                    color: #fff;
                    font-size: 14px;
                    padding: 0;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-color: rgba(255, 255, 255, 0.2);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.15);
                }
            """)
        else:
            # Light theme active - show moon icon (click to go to dark)
            self.theme_toggle_btn.setText("🌙")
            self.theme_toggle_btn.setToolTip("Switch to dark theme")
            
            # Light theme button style
            self.theme_toggle_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.15);
                    border-radius: 3px;
                    color: #424242;
                    font-size: 14px;
                    padding: 0;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.08);
                    border-color: rgba(0, 0, 0, 0.25);
                }
                QPushButton:pressed {
                    background: rgba(0, 0, 0, 0.12);
                }
            """)
    
    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        # Determine new theme
        new_theme = "dark" if self.current_theme == "light" else "light"
        
        # Save preference
        from main import save_theme_preference, load_stylesheet
        save_theme_preference(new_theme)
        
        # Load new stylesheet
        stylesheet_file = "styles_dark.qss" if new_theme == "dark" else "styles.qss"
        stylesheet = load_stylesheet(stylesheet_file)
        
        if stylesheet:
            # Apply new stylesheet
            QApplication.instance().setStyleSheet(stylesheet)
            self.current_theme = new_theme
            
            # Process events to ensure stylesheet is fully applied before we override inline styles
            QApplication.processEvents()
            
            self._update_theme_button()
            
            # Update icon bar button hover colors for the new theme
            # MUST be called AFTER stylesheet is applied to override any stylesheet rules
            self._update_icon_bar_hover_colors()
            
            # Update collection panel header buttons
            self._update_collection_header_button_styles()
            
            # Update tab bar buttons (New Request, Recent)
            self._update_tab_bar_button_styles()
            
            # Update save button
            self._update_save_button_style()
            
            # Update environment combo
            self._update_env_combo_style()
            
            # Update response section buttons
            self._update_response_buttons_style()
            
            # Update rename button style for new theme
            self._update_rename_button_style()
            
            # Refresh request title to use theme-aware colors
            self._update_request_title()
            
            # Update variable highlighters for new theme
            if hasattr(self, 'url_input') and hasattr(self.url_input, 'set_theme'):
                self.url_input.set_theme(new_theme)
            if hasattr(self, 'body_input') and hasattr(self.body_input, 'set_theme'):
                self.body_input.set_theme(new_theme)
            if hasattr(self, 'body_highlighter'):
                self.body_highlighter.set_theme(new_theme)
            
            # Update script tab editors
            if hasattr(self, 'scripts_tab'):
                self.scripts_tab.set_theme(new_theme)
            
            # Update environments panel
            if hasattr(self, 'environments_pane'):
                self.environments_pane.set_theme(new_theme)
            
            # Update variable inspector panel
            if hasattr(self, 'variable_inspector_pane'):
                self.variable_inspector_pane.set_theme(new_theme)
            
            # Update table delegates
            for table in [self.params_table, self.headers_table]:
                if hasattr(table, '_custom_delegate'):
                    table._custom_delegate.set_theme(new_theme)
                    table.viewport().update()  # Force repaint
            
            # Show confirmation message
            theme_name = "Dark" if new_theme == "dark" else "Light"
            self.statusBar().showMessage(f"✨ {theme_name} theme activated", 3000)
        else:
            QMessageBox.warning(
                self,
                "Theme Error",
                f"Failed to load {new_theme} theme stylesheet."
            )
    
    def _update_icon_bar_hover_colors(self):
        """Update icon bar button hover colors based on current theme."""
        # Determine hover color based on theme
        if self.current_theme == 'dark':
            hover_color = "rgba(255, 255, 255, 0.1)"
        else:
            hover_color = "rgba(0, 0, 0, 0.08)"
        
        # Update each button with the current hover color
        buttons = [
            (self.collections_toggle_btn, "24px", False),
            (self.git_sync_toggle_btn, "24px", False),
            (self.variable_inspector_toggle_btn, "18px", True),
            (self.environments_toggle_btn, "24px", False),
            (self.history_btn, "24px", False),
            (self.settings_toggle_btn, "24px", False),
        ]
        
        for button, font_size, is_bold in buttons:
            weight_line = "font-weight: bold;" if is_bold else ""
            # Force clear existing stylesheet first, then apply new one
            button.setStyleSheet("")
            button.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 0px;
                    font-size: {font_size};
                    {weight_line}
                    padding: 0px;
                    width: 50px;
                    height: 50px;
                    min-width: 50px;
                    min-height: 50px;
                    max-width: 50px;
                    max-height: 50px;
                }}
                QPushButton:hover {{
                    background: {hover_color};
                }}
                QPushButton:checked {{
                    background: rgba(33, 150, 243, 0.15);
                    border-left: 3px solid #2196F3;
                }}
            """)
    
    def _update_collection_header_button_styles(self):
        """Update collection panel header button styles based on current theme."""
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
            import_button_style = button_style + """
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
            """
            import_button_style = button_style + """
                QPushButton::menu-indicator {
                    width: 0px;
                }
            """
        
        self.add_collection_btn.setStyleSheet(button_style)
        self.import_collection_menu_btn.setStyleSheet(import_button_style)
    
    def _update_tab_bar_button_styles(self):
        """Update New Request and Recent button styles based on current theme."""
        if self.current_theme == 'dark':
            # Dark theme - original styles
            new_request_style = """
                QPushButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 4px;
                    font-size: 18px;
                    font-weight: 500;
                    padding: 0px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                QPushButton:pressed {
                    background: rgba(33, 150, 243, 0.3);
                }
            """
            recent_style = """
                QPushButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 0px 10px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
                QPushButton:checked {
                    background: rgba(33, 150, 243, 0.15);
                    border: 1px solid rgba(33, 150, 243, 0.4);
                }
            """
        else:
            # Light theme - better contrast
            new_request_style = """
                QPushButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 4px;
                    font-size: 18px;
                    font-weight: 500;
                    padding: 0px;
                    text-align: center;
                    color: #212121;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.08);
                    border: 1px solid rgba(0, 0, 0, 0.15);
                }
                QPushButton:pressed {
                    background: rgba(25, 118, 210, 0.15);
                }
            """
            recent_style = """
                QPushButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 0px 10px;
                    text-align: center;
                    color: #212121;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.08);
                    border: 1px solid rgba(0, 0, 0, 0.15);
                }
                QPushButton:checked {
                    background: rgba(25, 118, 210, 0.12);
                    border: 1px solid rgba(25, 118, 210, 0.4);
                }
            """
        
        self.new_request_btn.setStyleSheet(new_request_style)
        self.recent_requests_btn.setStyleSheet(recent_style)
    
    def _update_save_button_style(self):
        """Update Save button style based on current theme."""
        if self.current_theme == 'dark':
            # Dark theme - original style
            save_style = """
                QPushButton {
                    border: 1px solid #444444;
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                    border-top-right-radius: 0px;
                    border-bottom-right-radius: 0px;
                    background-color: transparent;
                    color: #E0E0E0;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: #2A2A2A;
                    border-color: #555555;
                }
                QPushButton:pressed {
                    background-color: #2D2D2D;
                }
            """
        else:
            # Light theme - better contrast
            save_style = """
                QPushButton {
                    border: 1px solid #BDBDBD;
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                    border-top-right-radius: 0px;
                    border-bottom-right-radius: 0px;
                    background-color: #FFFFFF;
                    color: #212121;
                    font-weight: 500;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: #F5F5F5;
                    border-color: #757575;
                }
                QPushButton:pressed {
                    background-color: #E8E8E8;
                }
            """
        
        self.save_btn.setStyleSheet(save_style)
    
    def _update_env_combo_style(self):
        """Update environment combobox style based on current theme."""
        if self.current_theme == 'dark':
            # Dark theme - original style
            env_combo_style = """
                QComboBox {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 3px;
                    padding: 2px 8px;
                    color: #fff;
                    font-size: 11px;
                }
                QComboBox:hover {
                    background: rgba(255, 255, 255, 0.08);
                    border-color: rgba(255, 255, 255, 0.2);
                }
                QComboBox::drop-down {
                    border: none;
                    background: transparent;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 5px solid #999;
                    width: 0;
                    height: 0;
                    margin-right: 4px;
                }
            """
        else:
            # Light theme - better contrast
            env_combo_style = """
                QComboBox {
                    background: #FFFFFF;
                    border: 1px solid #BDBDBD;
                    border-radius: 3px;
                    padding: 2px 8px;
                    color: #212121;
                    font-size: 11px;
                    font-weight: 500;
                }
                QComboBox:hover {
                    background: #FAFAFA;
                    border-color: #757575;
                }
                QComboBox::drop-down {
                    border: none;
                    background: transparent;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 5px solid #616161;
                    width: 0;
                    height: 0;
                    margin-right: 4px;
                }
            """
        
        self.env_combo.setStyleSheet(env_combo_style)
    
    def _update_response_buttons_style(self):
        """Update response section button styles based on current theme."""
        if self.current_theme == 'dark':
            # Dark theme - transparent with light text
            button_style = """
                QPushButton {
                    background-color: transparent;
                    color: #E0E0E0;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #2A2A2A;
                    border-color: #555555;
                }
                QPushButton:pressed {
                    background-color: #2D2D2D;
                }
            """
            search_btn_style = """
                background-color: transparent;
                color: #E0E0E0;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
            """
        else:
            # Light theme - white background with dark text
            button_style = """
                QPushButton {
                    background-color: #FFFFFF;
                    color: #212121;
                    border: 1px solid #BDBDBD;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F5F5F5;
                    border-color: #757575;
                }
                QPushButton:pressed {
                    background-color: #E8E8E8;
                }
            """
            search_btn_style = """
                background-color: #FFFFFF;
                color: #212121;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
            """
        
        # Apply to all response section buttons
        if hasattr(self, 'copy_response_btn'):
            self.copy_response_btn.setStyleSheet(button_style)
        if hasattr(self, 'pretty_raw_btn'):
            self.pretty_raw_btn.setStyleSheet(button_style)
        if hasattr(self, 'word_wrap_btn'):
            self.word_wrap_btn.setStyleSheet(button_style)
        if hasattr(self, 'search_prev_btn'):
            self.search_prev_btn.setStyleSheet(search_btn_style)
        if hasattr(self, 'search_next_btn'):
            self.search_next_btn.setStyleSheet(search_btn_style)
    
    # ==================== Context Menu Helpers ====================
    
    def _export_collection_from_menu(self, collection_id: int):
        """Export collection from context menu."""
        self.current_collection_id = collection_id
        self._export_collection()
    
    def _run_collection_tests_from_menu(self, collection_id: int):
        """Run tests for collection from context menu."""
        self.current_collection_id = collection_id
        self._run_collection_tests()
    
    def _rename_collection(self, collection_id: int):
        """Rename a collection."""
        collection = self.db.get_collection(collection_id)
        if not collection:
            return
        
        new_name, ok = QInputDialog.getText(
            self, "Rename Collection",
            "New name:",
            text=collection['name']
        )
        
        if ok and new_name and new_name != collection['name']:
            try:
                # Update collection name
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "UPDATE collections SET name = ? WHERE id = ?",
                    (new_name, collection_id)
                )
                self.db.connection.commit()
                self._load_collections()
                self._show_status(f"Collection renamed to '{new_name}'", "success")
            except Exception as e:
                self._show_status(f"Failed to rename: {str(e)[:30]}...", "error")
    
    def _duplicate_collection(self, collection_id: int):
        """Duplicate a collection."""
        collection = self.db.get_collection(collection_id)
        if not collection:
            return
        
        try:
            # Create new collection
            new_name = f"{collection['name']} (Copy)"
            new_collection_id = self.db.create_collection(new_name)
            
            # Copy all requests
            requests = self.db.get_requests_by_collection(collection_id)
            for request in requests:
                self.db.create_request(
                    name=request['name'],
                    method=request['method'],
                    url=request['url'],
                    collection_id=new_collection_id,
                    params=json.loads(request.get('params', '{}')) if isinstance(request.get('params'), str) else request.get('params', {}),
                    headers=json.loads(request.get('headers', '{}')) if isinstance(request.get('headers'), str) else request.get('headers', {}),
                    body=request.get('body', ''),
                    auth_type=request.get('auth_type', 'No Auth'),
                    auth_token=request.get('auth_token', ''),
                    body_type=request.get('body_type', 'raw')
                )
            
            self._auto_sync_to_filesystem()
            self._load_collections()
            self._show_status(f"Collection '{collection['name']}' duplicated", "success")
        except Exception as e:
            self._show_status(f"Failed to duplicate: {str(e)[:30]}...", "error")
    
    def _delete_collection_from_menu(self, collection_id: int):
        """Delete collection from context menu."""
        collection = self.db.get_collection(collection_id)
        if not collection:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete collection '{collection['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_collection(collection_id)
                if self.current_collection_id == collection_id:
                    self.current_collection_id = None
                    self.current_request_id = None
                    self._clear_request_editor()
                    self.center_stack.setCurrentWidget(self.no_request_empty_state)
                self._auto_sync_to_filesystem()
                self._load_collections()
                self._show_status(f"Collection '{collection['name']}' deleted", "success")
            except Exception as e:
                self._show_status(f"Failed to delete: {str(e)[:30]}...", "error")
    
    def _copy_request_as_curl(self, request_id: int):
        """Copy request as cURL command."""
        request = self.db.get_request(request_id)
        if not request:
            return
        
        try:
            # Build cURL command
            method = request['method']
            url = request['url']
            headers = json.loads(request.get('headers', '{}')) if isinstance(request.get('headers'), str) else request.get('headers', {})
            body = request.get('body', '')
            
            curl_parts = ['curl', '-X', method]
            
            # Add headers
            for key, value in headers.items():
                if key and value:
                    curl_parts.extend(['-H', f"'{key}: {value}'"])
            
            # Add body
            if body:
                curl_parts.extend(['-d', f"'{body}'"])
            
            # Add URL
            curl_parts.append(f"'{url}'")
            
            curl_command = ' '.join(curl_parts)
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(curl_command)
            self._show_status("cURL command copied to clipboard", "success")
        except Exception as e:
            self._show_status(f"Failed to copy: {str(e)[:30]}...", "error")
    
    def _rename_current_request(self):
        """Rename the currently active request using the breadcrumb button."""
        if self.current_request_id:
            self._rename_request(self.current_request_id)
    
    def _update_rename_button_style(self):
        """Update rename button style based on current theme - delicate hover effect."""
        if self.current_theme == 'dark':
            self.rename_request_btn.setStyleSheet("""
                QPushButton#renameRequestBtn {
                    background-color: transparent;
                    border: none;
                    border-radius: 3px;
                    padding: 2px;
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.5);
                }
                QPushButton#renameRequestBtn:hover {
                    background-color: rgba(255, 255, 255, 0.25);
                    color: rgba(255, 255, 255, 0.95);
                }
                QPushButton#renameRequestBtn:pressed {
                    background-color: rgba(255, 255, 255, 0.3);
                    color: white;
                }
                QPushButton#renameRequestBtn:focus {
                    outline: none;
                    border: none;
                }
            """)
        else:
            self.rename_request_btn.setStyleSheet("""
                QPushButton#renameRequestBtn {
                    background-color: transparent;
                    border: none;
                    border-radius: 3px;
                    padding: 2px;
                    font-size: 12px;
                    color: rgba(0, 0, 0, 0.4);
                }
                QPushButton#renameRequestBtn:hover {
                    background-color: rgba(0, 0, 0, 0.12);
                    color: rgba(0, 0, 0, 0.85);
                }
                QPushButton#renameRequestBtn:pressed {
                    background-color: rgba(0, 0, 0, 0.18);
                    color: rgba(0, 0, 0, 0.95);
                }
                QPushButton#renameRequestBtn:focus {
                    outline: none;
                    border: none;
                }
            """)
    
    def _update_description_button_style(self):
        """Update description button style based on current theme and whether description exists."""
        has_description = bool(self._current_description)
        
        # Choose icon based on description state
        icon = "📝" if has_description else "💬"  # 📝 = filled note, 💬 = empty comment
        self.description_btn.setText(icon)
        
        if self.current_theme == 'dark':
            if has_description:
                self.description_btn.setStyleSheet("""
                    QPushButton#descriptionBtn {
                        background-color: transparent;
                        border: none;
                        border-radius: 3px;
                        padding: 2px;
                        font-size: 12px;
                        color: rgba(100, 181, 246, 0.9);
                    }
                    QPushButton#descriptionBtn:hover {
                        background-color: rgba(100, 181, 246, 0.25);
                        color: rgba(100, 181, 246, 1.0);
                    }
                    QPushButton#descriptionBtn:pressed {
                        background-color: rgba(100, 181, 246, 0.3);
                        color: white;
                    }
                    QPushButton#descriptionBtn:focus {
                        outline: none;
                        border: none;
                    }
                """)
            else:
                self.description_btn.setStyleSheet("""
                    QPushButton#descriptionBtn {
                        background-color: transparent;
                        border: none;
                        border-radius: 3px;
                        padding: 2px;
                        font-size: 12px;
                        color: rgba(255, 255, 255, 0.5);
                    }
                    QPushButton#descriptionBtn:hover {
                        background-color: rgba(255, 255, 255, 0.25);
                        color: rgba(255, 255, 255, 0.95);
                    }
                    QPushButton#descriptionBtn:pressed {
                        background-color: rgba(255, 255, 255, 0.3);
                        color: white;
                    }
                    QPushButton#descriptionBtn:focus {
                        outline: none;
                        border: none;
                    }
                """)
        else:
            if has_description:
                self.description_btn.setStyleSheet("""
                    QPushButton#descriptionBtn {
                        background-color: transparent;
                        border: none;
                        border-radius: 3px;
                        padding: 2px;
                        font-size: 12px;
                        color: rgba(25, 118, 210, 0.9);
                    }
                    QPushButton#descriptionBtn:hover {
                        background-color: rgba(25, 118, 210, 0.15);
                        color: rgba(25, 118, 210, 1.0);
                    }
                    QPushButton#descriptionBtn:pressed {
                        background-color: rgba(25, 118, 210, 0.25);
                        color: rgb(25, 118, 210);
                    }
                    QPushButton#descriptionBtn:focus {
                        outline: none;
                        border: none;
                    }
                """)
            else:
                self.description_btn.setStyleSheet("""
                    QPushButton#descriptionBtn {
                        background-color: transparent;
                        border: none;
                        border-radius: 3px;
                        padding: 2px;
                        font-size: 12px;
                        color: rgba(0, 0, 0, 0.4);
                    }
                    QPushButton#descriptionBtn:hover {
                        background-color: rgba(0, 0, 0, 0.1);
                        color: rgba(0, 0, 0, 0.7);
                    }
                    QPushButton#descriptionBtn:pressed {
                        background-color: rgba(0, 0, 0, 0.15);
                        color: rgba(0, 0, 0, 0.9);
                    }
                    QPushButton#descriptionBtn:focus {
                        outline: none;
                        border: none;
                    }
                """)
        
        # Update tooltip with description preview
        if has_description:
            preview = self._current_description[:100]
            if len(self._current_description) > 100:
                preview += "..."
            self.description_btn.setToolTip(f"Description:\n{preview}\n\n(Click to edit)")
        else:
            self.description_btn.setToolTip("Add description (empty)")
    
    def _edit_description(self):
        """Open dialog to edit request description."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Request Description")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel("Add notes or description for this request:")
        layout.addWidget(info_label)
        
        # Text edit
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Enter description or notes here...")
        text_edit.setPlainText(self._current_description)
        text_edit.setFocus()
        layout.addWidget(text_edit)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog and handle result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_description = text_edit.toPlainText().strip()
            if new_description != self._current_description:
                self._current_description = new_description
                self._update_description_button_style()
                self._mark_as_changed()
    
    def _rename_request(self, request_id: int):
        """Rename a request."""
        request = self.db.get_request(request_id)
        if not request:
            return
        
        new_name, ok = QInputDialog.getText(
            self, "Rename Request",
            "New name:",
            text=request['name']
        )
        
        if ok and new_name.strip() and new_name.strip() != request['name']:
            new_name = new_name.strip()
            
            # Check for duplicate name (excluding the current request)
            collection_id = request['collection_id']
            method = request['method']
            existing_requests = self.db.get_requests_by_collection(collection_id)
            existing_names = {
                req['name'] for req in existing_requests 
                if req['method'] == method and req['id'] != request_id
            }
            
            if new_name in existing_names:
                # Suggest a unique name
                suggested_name = self._get_unique_request_name(collection_id, new_name, method)
                reply = QMessageBox.question(
                    self,
                    "Request Already Exists",
                    f"A [{method}] request named '{new_name}' already exists in this collection.\n\n"
                    f"Would you like to rename it as '{suggested_name}' instead?\n\n"
                    f"Note: Having multiple requests with the same name can be confusing.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    new_name = suggested_name
                else:
                    # Let user try again
                    return self._rename_request(request_id)
            
            try:
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "UPDATE requests SET name = ? WHERE id = ?",
                    (new_name, request_id)
                )
                self.db.connection.commit()
                self._auto_sync_to_filesystem()
                self._load_collections()
                if self.current_request_id == request_id:
                    self.current_request_name = new_name
                    self.request_title_label.setText(new_name)
                    self._update_request_title()
                    
                    # Update tab title with new name
                    current_tab_index = self.request_tabs.currentIndex()
                    if current_tab_index >= 0 and current_tab_index < len(self.tab_states):
                        self.tab_states[current_tab_index]['name'] = new_name
                        self._update_tab_title(current_tab_index)
                
                self._show_status(f"Request renamed to '{new_name}'", "success")
            except Exception as e:
                self._show_status(f"Failed to rename: {str(e)[:30]}...", "error")
    
    def _duplicate_request(self, request_id: int):
        """Duplicate a request."""
        request = self.db.get_request(request_id)
        if not request:
            return
        
        try:
            # Generate a unique name for the duplicate
            base_name = f"{request['name']} (Copy)"
            new_name = self._get_unique_request_name(
                request['collection_id'], 
                base_name, 
                request['method']
            )
            
            self.db.create_request(
                name=new_name,
                method=request['method'],
                url=request['url'],
                collection_id=request['collection_id'],
                params=json.loads(request.get('params', '{}')) if isinstance(request.get('params'), str) else request.get('params', {}),
                headers=json.loads(request.get('headers', '{}')) if isinstance(request.get('headers'), str) else request.get('headers', {}),
                body=request.get('body', ''),
                auth_type=request.get('auth_type', 'No Auth'),
                auth_token=request.get('auth_token', ''),
                pre_request_script=request.get('pre_request_script', ''),
                post_response_script=request.get('post_response_script', ''),
                body_type=request.get('body_type', 'raw')
            )
            self._auto_sync_to_filesystem()
            self._load_collections()
            self._show_status(f"Request duplicated as '{new_name}'", "success")
        except Exception as e:
            self._show_status(f"Failed to duplicate: {str(e)[:30]}...", "error")
    
    def _duplicate_request_to_temp_tab(self, request_id: int):
        """Duplicate a request and open it in a temporary tab."""
        request = self.db.get_request(request_id)
        if not request:
            return
        
        try:
            # Create a temporary tab with the duplicated data (unsaved)
            # This creates a new tab WITHOUT saving to database first
            
            # Prepare request data
            name = f"{request['name']} (Copy)"
            method = request['method']
            url = request['url']
            params = json.loads(request.get('params', '{}')) if isinstance(request.get('params'), str) else request.get('params', {})
            headers = json.loads(request.get('headers', '{}')) if isinstance(request.get('headers'), str) else request.get('headers', {})
            body = request.get('body', '')
            auth_type = request.get('auth_type', 'No Auth')
            auth_token = request.get('auth_token', '')
            pre_request_script = request.get('pre_request_script', '') or ''
            post_response_script = request.get('post_response_script', '') or ''
            
            # Save current tab state
            current_index = self.request_tabs.currentIndex()
            if current_index >= 0 and current_index in self.tab_states:
                self.tab_states[current_index]['ui_state'] = self._capture_current_tab_state()
                self.tab_states[current_index]['has_changes'] = self.has_unsaved_changes
            
            # Block signals to prevent premature tab change
            self.request_tabs.blockSignals(True)
            
            # Add new temporary tab
            tab_index = self.request_tabs.addTab(QWidget(), f"{method} • {name}")
            
            # Store tab state (temporary, no request_id yet)
            self.tab_states[tab_index] = {
                'request_id': None,  # Not saved yet
                'has_changes': True,  # Has unsaved data
                'name': name,
                'method': method,
                'is_temporary': True,
                'ui_state': {}
            }
            
            # Unblock signals
            self.request_tabs.blockSignals(False)
            
            # Switch to new tab
            self.request_tabs.setCurrentIndex(tab_index)
            
            # Load the duplicated data into the editor
            self.method_combo.setCurrentText(method)
            self.url_input.setText(url)
            self._load_dict_to_table(params, self.params_table)
            self._load_dict_to_table(headers, self.headers_table)
            self.body_input.setPlainText(body)
            self.auth_type_combo.setCurrentText(auth_type)
            self.auth_token_input.setText(auth_token)
            # Update widget visibility explicitly
            self.bearer_token_widget.setVisible(auth_type == 'Bearer Token')
            self.oauth_widget.setVisible(auth_type == 'OAuth 2.0')
            
            # Load scripts
            self.scripts_tab.load_scripts(pre_request_script, post_response_script)
            self.scripts_tab.update_toggle_indicators()
            
            # Clear response viewer
            self._clear_response_viewer()
            
            # Show tabs view
            self.center_stack.setCurrentWidget(self.tabs_container)
            
            # Mark as changed and update UI
            self.has_unsaved_changes = True
            self._update_request_title()
            self._update_tab_title(tab_index)
            
            self._show_status(f"Request duplicated in temporary tab", "success")
        except Exception as e:
            self._show_status(f"Failed to duplicate: {str(e)[:30]}...", "error")
    
    def _is_request_pinned(self, request_id: int) -> bool:
        """Check if a request is pinned in recent requests."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "SELECT is_pinned FROM recent_requests WHERE request_id = ?",
                (request_id,)
            )
            result = cursor.fetchone()
            return result and bool(result[0])
        except Exception:
            return False
    
    def _pin_request_from_tab(self, request_id: int):
        """Pin a request to recent requests panel."""
        try:
            # Add to recent requests if not already there
            self.recent_requests_widget.add_request(request_id)
            
            # Pin it
            cursor = self.db.connection.cursor()
            cursor.execute(
                "UPDATE recent_requests SET is_pinned = 1 WHERE request_id = ?",
                (request_id,)
            )
            self.db.connection.commit()
            
            # Refresh recent requests widget
            self.recent_requests_widget.refresh()
            
            self._show_status("Request pinned to Recent Requests", "success")
        except Exception as e:
            self._show_status(f"Failed to pin: {str(e)[:30]}...", "error")
    
    def _unpin_request_from_tab(self, request_id: int):
        """Unpin a request from recent requests panel."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "UPDATE recent_requests SET is_pinned = 0 WHERE request_id = ?",
                (request_id,)
            )
            self.db.connection.commit()
            
            # Refresh recent requests widget
            self.recent_requests_widget.refresh()
            
            self._show_status("Request unpinned from Recent Requests", "success")
        except Exception as e:
            self._show_status(f"Failed to unpin: {str(e)[:30]}...", "error")
    
    def _delete_request_from_menu(self, request_id: int):
        """Delete request from context menu."""
        request = self.db.get_request(request_id)
        if not request:
            return
        
        # Capture the folder that contains this request before deletion
        # So we can keep it expanded after reload
        folder_id_to_keep_expanded = request.get('folder_id')
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete request '{request['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_request(request_id)
                
                # Store the folder AND all parent folders to keep expanded
                if folder_id_to_keep_expanded:
                    if not hasattr(self, '_folders_to_keep_expanded'):
                        self._folders_to_keep_expanded = set()
                    # Add this folder and all its parents to the set
                    self._add_folder_and_parents_to_expanded(folder_id_to_keep_expanded, self._folders_to_keep_expanded)
                
                # Also store the collection to keep expanded
                collection_id = request.get('collection_id')
                if collection_id:
                    if not hasattr(self, '_collections_to_keep_expanded'):
                        self._collections_to_keep_expanded = set()
                    self._collections_to_keep_expanded.add(collection_id)
                
                # Close the tab if this request is open in any tab
                tab_index_to_close = None
                for tab_idx, tab_state in self.tab_states.items():
                    if tab_state.get('request_id') == request_id:
                        tab_index_to_close = tab_idx
                        break
                
                if tab_index_to_close is not None:
                    self._close_tab(tab_index_to_close)
                
                if self.current_request_id == request_id:
                    self.current_request_id = None
                
                # Refresh recent requests to remove deleted entry
                self.recent_requests_widget.refresh()
                
                self._auto_sync_to_filesystem()
                self._load_collections()
                
                self._show_status(f"Request '{request['name']}' deleted", "success")
            except Exception as e:
                self._show_status(f"Failed to delete: {str(e)[:30]}...", "error")
    
    def _show_response_context_menu(self, position):
        """Show context menu for response viewer."""
        menu = QMenu(self)
        
        # Copy action
        copy_action = QAction("📋 Copy", self)
        copy_action.triggered.connect(self.response_body.copy)
        copy_action.setEnabled(self.response_body.textCursor().hasSelection())
        menu.addAction(copy_action)
        
        # Select all action
        select_all_action = QAction("🔘 Select All", self)
        select_all_action.triggered.connect(self.response_body.selectAll)
        select_all_action.setEnabled(len(self.response_body.toPlainText()) > 0)
        menu.addAction(select_all_action)
        
        menu.addSeparator()
        
        # Copy entire response
        copy_all_action = QAction("📄 Copy Entire Response", self)
        copy_all_action.triggered.connect(self._copy_entire_response)
        copy_all_action.setEnabled(len(self.response_body.toPlainText()) > 0)
        menu.addAction(copy_all_action)
        
        # Save to file
        save_action = QAction("💾 Save to File...", self)
        save_action.triggered.connect(self._save_response_to_file)
        save_action.setEnabled(len(self.response_body.toPlainText()) > 0)
        menu.addAction(save_action)
        
        menu.exec(self.response_body.viewport().mapToGlobal(position))
    
    def _show_table_context_menu(self, table: QTableWidget, position):
        """Show context menu for params/headers tables."""
        row = table.rowAt(position.y())
        if row < 0:
            return
        
        # Check if row has any content
        key_item = table.item(row, 0)
        value_item = table.item(row, 1)
        has_content = (key_item and key_item.text().strip()) or (value_item and value_item.text().strip())
        
        if not has_content:
            return  # Don't show menu for empty rows
        
        menu = QMenu(self)
        
        # Delete row action
        delete_action = QAction("🗑️ Delete Row", self)
        delete_action.triggered.connect(lambda: self._delete_table_row(table, row))
        menu.addAction(delete_action)
        
        menu.exec(table.viewport().mapToGlobal(position))
    
    def _handle_table_key_press(self, table: QTableWidget, event):
        """Handle keyboard events for params/headers tables."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QKeyEvent
        
        # Handle Delete key
        if event.key() == Qt.Key.Key_Delete:
            row = table.currentRow()
            if row >= 0:
                # Check if row has content
                key_item = table.item(row, 0)
                value_item = table.item(row, 1)
                has_content = (key_item and key_item.text().strip()) or (value_item and value_item.text().strip())
                
                if has_content:
                    self._delete_table_row(table, row)
                    return  # Don't propagate event
        
        # Call original keyPressEvent for other keys
        QTableWidget.keyPressEvent(table, event)
    
    def _delete_table_row(self, table: QTableWidget, row: int):
        """Delete a row from params/headers table."""
        if row < 0 or row >= table.rowCount():
            return
        
        # Clear the row content
        table.setItem(row, 0, QTableWidgetItem(""))
        table.setItem(row, 1, QTableWidgetItem(""))
        
        # Trigger reorganization (will sort and remove empty rows except one)
        self._auto_add_table_rows(table)
        
        # Mark as changed
        self._mark_as_changed()
        
        # Update tab counts
        self._update_tab_counts()
    
    def _copy_entire_response(self):
        """Copy entire response to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.response_body.toPlainText())
        self._show_status("Response copied to clipboard", "success")
    
    def _save_response_to_file(self):
        """Save response to file."""
        # Check if there's any response text to save
        response_text = self.response_body.toPlainText()
        if not response_text:
            self._show_status("No response to save", "warning")
            return
        
        # Suggest file extension based on content type
        default_ext = "txt"
        if self.current_response and hasattr(self.current_response, 'content_type'):
            content_type = self.current_response.content_type.lower()
            if 'json' in content_type:
                default_ext = "json"
            elif 'xml' in content_type or 'html' in content_type:
                default_ext = "xml"
            elif 'text' in content_type:
                default_ext = "txt"
        
        # Generate default filename: response_{request_name}_{timestamp}
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Get request name and sanitize it for filesystem
        request_name = "request"
        if hasattr(self, 'current_request_name') and self.current_request_name:
            # Remove invalid filename characters
            import re
            request_name = re.sub(r'[<>:"/\\|?*]', '_', self.current_request_name)
            request_name = request_name.strip()
        
        default_filename = f"response_{request_name}_{timestamp}.{default_ext}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Response",
            default_filename,
            f"{default_ext.upper()} Files (*.{default_ext});;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response_text)
                self._show_status(f"Response saved to file", "success")
            except Exception as e:
                self._show_status(f"Failed to save: {str(e)[:30]}...", "error")
    
    def eventFilter(self, obj, event):
        """Event filter to handle middle-click on tabs for closing."""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent
        
        # Check if this is a mouse button release event on the tab bar
        if obj == self.request_tabs.tabBar() and event.type() == QEvent.Type.MouseButtonRelease:
            mouse_event = event
            # Check if it was a middle button click
            if mouse_event.button() == Qt.MouseButton.MiddleButton:
                # Get the tab index at the click position
                tab_index = self.request_tabs.tabBar().tabAt(mouse_event.pos())
                if tab_index >= 0:
                    # Close the tab
                    self._close_tab(tab_index)
                    return True  # Event handled
        
        # Pass the event to the parent class
        return super().eventFilter(obj, event)
    
    # ==================== AUTO-UPDATE METHODS ====================
    
    def _check_for_updates(self, silent=False):
        """Check for application updates."""
        # Don't check if already checking
        if self.update_checker_thread and self.update_checker_thread.isRunning():
            return
        
        # Update UI
        if not silent:
            self.settings_pane.set_checking_updates(True)
        
        # Create and start update checker thread
        self.update_checker_thread = UpdateChecker(silent=silent)
        self.update_checker_thread.update_available.connect(self._on_update_available)
        self.update_checker_thread.no_update.connect(self._on_no_update)
        self.update_checker_thread.check_error.connect(self._on_update_check_error)
        self.update_checker_thread.finished.connect(lambda: self.settings_pane.set_checking_updates(False))
        self.update_checker_thread.start()
    
    def _on_update_available(self, update_info: dict):
        """Handle update available."""
        current_version = UpdateChecker.CURRENT_VERSION
        
        # Update settings panel status
        latest_version = update_info.get('latest_version', 'Unknown')
        self.settings_pane.set_update_status(
            f"✨ Version {latest_version} available!",
            color="#4CAF50"
        )
        
        # Show update dialog
        dialog = UpdateAvailableDialog(update_info, current_version, self)
        if dialog.exec():
            # User wants to download and install
            self._start_update_download(update_info)
    
    def _on_no_update(self, current_version: str):
        """Handle no update available."""
        # Update settings panel status
        self.settings_pane.set_update_status(
            f"✅ You're up to date!",
            color="#4CAF50"
        )
        
        # Show dialog (only if user manually checked)
        if not self.update_checker_thread.silent:
            dialog = NoUpdateDialog(current_version, self)
            dialog.exec()
    
    def _on_update_check_error(self, error_msg: str):
        """Handle update check error."""
        # Update settings panel status
        self.settings_pane.set_update_status(
            f"❌ Check failed: {error_msg}",
            color="#F44336"
        )
        
        # Show error dialog
        QMessageBox.warning(
            self,
            "Update Check Failed",
            f"Couldn't check for updates:\n\n{error_msg}\n\n"
            "Please check your internet connection and try again."
        )
    
    def _start_update_download(self, update_info: dict):
        """Start downloading the update."""
        # Show progress dialog
        progress_dialog = UpdateProgressDialog(self)
        progress_dialog.show()
        
        # Create and start downloader thread
        self.update_downloader_thread = UpdateDownloader(
            update_info['download_url'],
            update_info.get('checksum', '')
        )
        self.update_downloader_thread.download_progress.connect(progress_dialog.update_progress)
        self.update_downloader_thread.download_complete.connect(
            lambda path: self._on_download_complete(path, progress_dialog)
        )
        self.update_downloader_thread.download_error.connect(
            lambda err: self._on_download_error(err, progress_dialog)
        )
        
        # Handle dialog cancel
        progress_dialog.rejected.connect(self.update_downloader_thread.cancel)
        
        self.update_downloader_thread.start()
    
    def _on_download_complete(self, installer_path: str, progress_dialog: UpdateProgressDialog):
        """Update downloaded successfully."""
        progress_dialog.close()
        
        reply = QMessageBox.question(
            self,
            "Update Ready",
            "The update has been downloaded successfully.\n\n"
            "Install now?\n\n"
            "The application will close and the installer will run.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                UpdateInstaller.install_update(installer_path)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Installation Failed",
                    f"Failed to start installer:\n{str(e)}"
                )
    
    def _on_download_error(self, error_msg: str, progress_dialog: UpdateProgressDialog):
        """Download failed."""
        progress_dialog.close()
        
        QMessageBox.critical(
            self,
            "Download Failed",
            f"Failed to download update:\n\n{error_msg}\n\n"
            "Please try again later or download manually from the website."
        )
    
    # ==================== Security Scanner Methods ====================
    
    def _run_security_scan(self):
        """Run security scan on the current response."""
        if not hasattr(self, 'last_response') or not self.last_response:
            QMessageBox.warning(
                self,
                "No Response",
                "Please send a request first before running a security scan."
            )
            return
        
        # Get request details
        if not hasattr(self, 'current_request_details') or not self.current_request_details:
            QMessageBox.warning(
                self,
                "No Request Details",
                "Request details are not available for scanning."
            )
            return
        
        details = self.current_request_details
        response = self.last_response
        
        try:
            # Perform security scan
            findings = self.security_scanner.scan_response(
                method=details['method'],
                url=details['url'],
                request_headers=details.get('headers', {}),
                response_status=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.text,
                request_secure=details['url'].startswith('https://')
            )
            
            # Get severity stats
            stats = self.security_scanner.get_severity_stats(findings)
            
            # Save scan to database
            timestamp = datetime.now().isoformat()
            scan_id = self.db.create_security_scan(
                url=details['url'],
                method=details['method'],
                timestamp=timestamp,
                request_id=self.current_request_id,
                collection_id=self.current_collection_id,
                scan_name=self.current_request_name,
                findings_count=len(findings),
                critical_count=stats['critical'],
                high_count=stats['high'],
                medium_count=stats['medium'],
                low_count=stats['low'],
                info_count=stats['info']
            )
            
            # Save findings
            for finding in findings:
                self.db.create_security_finding(
                    scan_id=scan_id,
                    check_id=finding.check_id,
                    title=finding.title,
                    severity=finding.severity,
                    description=finding.description,
                    recommendation=finding.recommendation,
                    timestamp=finding.timestamp,
                    evidence=finding.evidence,
                    cwe_id=finding.cwe_id,
                    owasp_category=finding.owasp_category
                )
            
            # Show results
            if len(findings) == 0:
                self._show_status("✅ Security scan complete: No issues found", "success")
            else:
                self._show_status(f"🔒 Security scan complete: {len(findings)} issues found", "warning")
            
            # Update security panel if visible
            if self.security_pane.isVisible():
                self.security_pane.display_scan_results(scan_id)
            else:
                # Show security panel with results
                self._switch_left_panel('security')
                self.security_pane.display_scan_results(scan_id)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Scan Error",
                f"An error occurred during security scanning:\n\n{str(e)}"
            )
            print(f"[ERROR] Security scan failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _export_security_report(self, scan_id: int):
        """Export security scan report."""
        try:
            # Ask user for format
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Export Security Report")
            dialog.setModal(True)
            
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Select export format:"))
            
            html_radio = QRadioButton("HTML Report (Recommended)")
            html_radio.setChecked(True)
            json_radio = QRadioButton("JSON (Machine-readable)")
            
            layout.addWidget(html_radio)
            layout.addWidget(json_radio)
            
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            # Get format
            if html_radio.isChecked():
                format_type = "html"
                file_filter = "HTML Files (*.html)"
                default_ext = ".html"
            else:
                format_type = "json"
                file_filter = "JSON Files (*.json)"
                default_ext = ".json"
            
            # Ask for save location
            scan = self.db.get_security_scan(scan_id)
            if not scan:
                QMessageBox.warning(self, "Error", "Scan not found.")
                return
            
            timestamp = datetime.fromisoformat(scan['timestamp']).strftime("%Y%m%d_%H%M%S")
            default_filename = f"security_report_{timestamp}{default_ext}"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Security Report",
                default_filename,
                file_filter
            )
            
            if not file_path:
                return
            
            # Generate and save report
            if format_type == "html":
                report_content = self.security_report_generator.generate_html_report(scan_id)
            else:
                report_content = self.security_report_generator.generate_json_report(scan_id)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self._show_status(f"✅ Security report exported to {file_path}", "success")
            
            # Ask if user wants to open it
            reply = QMessageBox.question(
                self,
                "Report Exported",
                f"Security report exported successfully.\n\nDo you want to open it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import os
                os.startfile(file_path)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting the report:\n\n{str(e)}"
            )
            print(f"[ERROR] Report export failed: {e}")
            import traceback
            traceback.print_exc()
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Stop any running request thread
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.wait(1000)  # Wait up to 1 second
        
        # Stop any running update threads
        if self.update_checker_thread and self.update_checker_thread.isRunning():
            self.update_checker_thread.wait(1000)
        if self.update_downloader_thread and self.update_downloader_thread.isRunning():
            self.update_downloader_thread.cancel()
            self.update_downloader_thread.wait(1000)

        # Clean up resources
        self.db.close()
        self.api_client.close()
        event.accept()

