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
    QSizePolicy, QDialog, QStyledItemDelegate, QMenu, QGroupBox, QTabBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QAction, QKeySequence, QShortcut, QBrush, QColor, QPalette, QPainter, QPen
import json
from typing import Dict, Optional

from src.core.database import DatabaseManager
from src.core.api_client import ApiClient, ApiResponse
from src.core.app_paths import AppPaths
from src.ui.dialogs.environment_dialog import EnvironmentDialog
from src.features.variable_substitution import EnvironmentManager
from src.features.collection_io import CollectionExporter, CollectionImporter, get_safe_filename
from src.ui.dialogs.history_dialog import HistoryDialog
from src.ui.dialogs.code_snippet_dialog import CodeSnippetDialog
from src.ui.dialogs.oauth_dialog import OAuthConfigDialog
from src.features.oauth_manager import OAuthManager
from src.ui.widgets.test_tab_widget import TestTabWidget
from src.ui.widgets.test_results_viewer import TestResultsViewer
from src.ui.widgets.toast_notification import ToastManager
from src.ui.widgets.syntax_highlighter import apply_syntax_highlighting
from src.ui.widgets.recent_requests_widget import RecentRequestsWidget
from src.ui.widgets.method_badge import MethodBadge, StatusBadge
from src.ui.widgets.variable_extraction_widget import VariableExtractionWidget
from src.ui.widgets.variable_inspector_widget import VariableInspectorDialog
from src.ui.widgets.variable_library_widget import VariableLibraryWidget
from src.ui.widgets.variable_highlight_delegate import VariableSyntaxHighlighter, VariableHighlightDelegate, HighlightedLineEdit
from src.ui.widgets.empty_state import NoRequestEmptyState, NoResponseEmptyState, NoCollectionsEmptyState
from src.features.test_engine import TestEngine, TestAssertion
from src.ui.dialogs.collection_test_runner import CollectionTestRunnerDialog
from src.ui.dialogs.git_sync_dialog import GitSyncDialog
from src.ui.dialogs.conflict_resolution_dialog import ConflictResolutionDialog
from src.ui.dialogs.curl_import_dialog import CurlImportDialog
from src.features.git_sync_manager import GitSyncManager, GitSyncConfig, SyncStatus
from src.features.secrets_manager import SecretsManager
from src.features.curl_converter import CurlConverter
from datetime import datetime
import requests


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
            
            # Draw the request name in normal font and gray
            painter.setFont(font)
            painter.setPen(QPen(QColor('#CCCCCC')))
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
    
    def createEditor(self, parent, option, index):
        """Create editor with no padding."""
        editor = QLineEdit(parent)
        
        # Remove all padding and margins from the editor
        editor.setStyleSheet("""
            QLineEdit {
                padding: 0px;
                margin: 0px;
                border: none;
            }
        """)
        
        return editor
    
    def paint(self, painter, option, index):
        """Use variable highlighting delegate's paint method."""
        self.var_highlighter_delegate.paint(painter, option, index)
    
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
        self.hovered_tab = -1  # Track which tab is hovered
    
    def set_tab_data(self, index: int, method: str, name: str, has_changes: bool = False):
        """Store tab data for custom rendering."""
        self.tab_data[index] = {
            'method': method,
            'name': name,
            'has_changes': has_changes
        }
        self.update()
    
    def tabSizeHint(self, index: int):
        """Calculate tab size based on content."""
        if index not in self.tab_data:
            return super().tabSizeHint(index)
        
        data = self.tab_data[index]
        method = data['method']
        name = data['name']
        has_changes = data['has_changes']
        
        # Calculate text width with proper font metrics
        fm = self.fontMetrics()
        
        # Bold font for method (uppercase)
        method_upper = method.upper()
        method_width = fm.horizontalAdvance(method_upper) + 8  # Add extra for bold approximation
        
        bullet_width = fm.horizontalAdvance(" • ")
        name_width = fm.horizontalAdvance(name)
        changes_width = fm.horizontalAdvance(" •") if has_changes else 0
        close_btn_width = 24  # Space for close button
        
        # Add padding
        total_width = 24 + method_width + bullet_width + name_width + changes_width + close_btn_width
        
        return QSize(min(max(total_width, 120), 250), 38)  # Reduced height from 42 to 38
    
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
            
            # Get tab rect
            rect = self.tabRect(index)
            is_selected = (index == self.currentIndex())
            is_dark_theme = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
            
            # Draw background
            if is_selected:
                painter.fillRect(rect, QColor('#1e1e1e' if is_dark_theme else '#FFFFFF'))
            elif rect.contains(self.mapFromGlobal(self.cursor().pos())):
                # Hover state
                painter.fillRect(rect, QColor('#1a3a52' if is_dark_theme else '#E3F2FD'))
            
            # Draw vertical separator (right border)
            separator_color = QColor('#3e3e42' if is_dark_theme else '#E0E0E0')
            painter.setPen(QPen(separator_color, 1))
            painter.drawLine(rect.topRight().x(), rect.top(), rect.bottomRight().x(), rect.bottom())
            
            # Draw bottom border (underline) for selected tab
            if is_selected:
                painter.setPen(QPen(QColor('#007acc' if is_dark_theme else '#2196F3'), 3))
                painter.drawLine(rect.bottomLeft().x(), rect.bottom() - 1, 
                               rect.bottomRight().x(), rect.bottom() - 1)
            
            # Start position for text (with some padding)
            x = rect.x() + 12
            y = rect.center().y() + 5  # Center vertically
            
            # Draw method with color (uppercase)
            method_upper = method.upper()
            method_color = QColor(self.METHOD_COLORS.get(method, '#FFFFFF'))
            painter.setPen(QPen(method_color))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(x, y, method_upper)
            
            # Calculate width of method text
            method_width = painter.fontMetrics().horizontalAdvance(method_upper)
            x += method_width + 8
            
            # Draw bullet separator
            if is_selected:
                painter.setPen(QPen(QColor('#007acc' if is_dark_theme else '#2196F3')))
            else:
                painter.setPen(QPen(QColor('#9E9E9E' if is_dark_theme else '#757575')))
            font.setBold(False)
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(x, y, "•")
            x += painter.fontMetrics().horizontalAdvance("•") + 8
            
            # Draw name (truncate if needed)
            max_name_width = rect.width() - (x - rect.x()) - 30  # Reserve space for close button
            name_display = name
            name_width = painter.fontMetrics().horizontalAdvance(name)
            
            if name_width > max_name_width:
                # Truncate with ellipsis
                while name_width > max_name_width - painter.fontMetrics().horizontalAdvance("...") and len(name_display) > 0:
                    name_display = name_display[:-1]
                    name_width = painter.fontMetrics().horizontalAdvance(name_display)
                name_display += "..."
            
            # Apply text hierarchy: active = primary, inactive = secondary
            if is_selected:
                painter.setPen(QPen(QColor('#E0E0E0' if is_dark_theme else '#212121')))  # Primary text
            else:
                painter.setPen(QPen(QColor('#9E9E9E' if is_dark_theme else '#757575')))  # Secondary text
            
            painter.drawText(x, y, name_display)
            x += painter.fontMetrics().horizontalAdvance(name_display) + 6
            
            # Draw unsaved indicator
            if has_changes:
                painter.drawText(x, y, "•")


class MainWindow(QMainWindow):
    """
    Main application window with collections tree, request editor, and response viewer.
    """
    
    def __init__(self, db_path: str = "api_client.db"):
        super().__init__()
        
        # Initialize database and API client
        self.db = DatabaseManager(db_path=db_path)
        self.api_client = ApiClient()
        
        # Initialize environment manager
        self.env_manager = EnvironmentManager()
        
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
        self.current_theme = 'light'  # Will be set by main.py
        
        # Track current selection
        self.current_collection_id = None
        self.current_request_id = None
        self.current_request_name = None
        self.current_collection_name = None
        self.current_folder_id = None  # Track current folder
        
        # Track unsaved changes
        self.has_unsaved_changes = False
        self.original_request_data = {}
        
        # Track active threads
        self.request_thread = None
        
        # UI state tracking
        self.response_panel_collapsed = False
        
        # Setup UI
        self.setWindowTitle("PostMini - Desktop API Client")
        self.setGeometry(100, 100, 1400, 900)
        
        self._init_ui()
        
        # Initialize toast notification system (after UI is created)
        self.toast = ToastManager(self.centralWidget())
        
        self._setup_shortcuts()
        self._load_collections()
        self._load_environments()
        self._init_git_sync()
        
        # Initialize method combo styling
        self._update_method_style('GET')
    
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
        # Create toolbar
        self._create_toolbar()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create main splitter (left pane | center pane | right pane)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ==================== LEFT PANE: Collections ====================
        left_pane = self._create_collections_pane()
        main_splitter.addWidget(left_pane)
        
        # ==================== CENTER PANE: Request Editor & Response ====================
        # Create a container for the entire center area
        center_container = QWidget()
        center_container_layout = QVBoxLayout(center_container)
        center_container_layout.setContentsMargins(0, 0, 0, 0)
        center_container_layout.setSpacing(0)
        
        # Create horizontal container for tab bar + recent button (always visible)
        tab_bar_container = QWidget()
        tab_bar_container.setMaximumHeight(38)  # Fixed height to prevent extension
        tab_bar_container.setMinimumHeight(38)
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
        self.request_tabs.setMaximumHeight(38)  # Only show the tab bar (reduced from 42)
        self.request_tabs.setObjectName("requestTabs")  # For specific styling
        tab_bar_layout.addWidget(self.request_tabs)
        
        # Add Recent button - independent of tabs, always visible
        self.recent_requests_btn = QPushButton("🕐")
        self.recent_requests_btn.setToolTip("Toggle recent requests panel")
        self.recent_requests_btn.setCheckable(True)
        self.recent_requests_btn.setFixedSize(38, 38)  # Match tab bar height (reduced from 42)
        self.recent_requests_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                font-size: 18px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:checked {
                background: rgba(33, 150, 243, 0.2);
                border: 1px solid #2196F3;
            }
        """)
        self.recent_requests_btn.clicked.connect(self._toggle_recent_requests)
        tab_bar_layout.addWidget(self.recent_requests_btn)
        
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
        
        # Tab state storage: {tab_index: {request_id, ui_state, has_changes}}
        self.tab_states = {}
        self.next_untitled_num = 1
        self.previous_tab_index = None  # Track previous tab for state saving
        self._last_double_click_time = 0  # Track last double-click to prevent duplicates
        self._last_double_click_request_id = None
        
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
        self.center_stack.setCurrentWidget(self.no_request_empty_state)
        
        # Add center container to main splitter
        main_splitter.addWidget(center_container)
        
        # ==================== RIGHT PANE: Recent Requests ====================
        self.recent_requests_widget = RecentRequestsWidget(self.db)
        self.recent_requests_widget.request_selected.connect(self._load_request)
        self.recent_requests_widget.close_btn.clicked.connect(self._toggle_recent_requests)  # Connect close button
        self.recent_requests_widget.setVisible(False)  # Hidden by default
        main_splitter.addWidget(self.recent_requests_widget)
        
        # Set splitter sizes (25% left, 60% center, 15% right when visible)
        main_splitter.setSizes([350, 1050, 250])
        
        main_layout.addWidget(main_splitter)
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self):
        """Create the application toolbar with environment controls."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Environment label
        toolbar.addWidget(QLabel("Environment: "))
        
        # Environment selector
        self.env_combo = QComboBox()
        self.env_combo.setMinimumWidth(200)
        self.env_combo.addItem("No Environment", None)
        self.env_combo.currentIndexChanged.connect(self._on_environment_changed)
        toolbar.addWidget(self.env_combo)
        
        # Manage environments button
        manage_env_btn = QPushButton("⚙️ Manage Environments")
        manage_env_btn.clicked.connect(self._open_environment_dialog)
        toolbar.addWidget(manage_env_btn)
        
        toolbar.addSeparator()
        
        # History button
        history_btn = QPushButton("📋 Requests history")
        history_btn.clicked.connect(self._open_history_dialog)
        toolbar.addWidget(history_btn)
        
        toolbar.addSeparator()
        
        # Variables dropdown button (with inspector and library options)
        variables_btn = QPushButton("📊 Variables")
        variables_btn.setToolTip("Access variables tools")
        
        # Create menu for dropdown
        variables_menu = QMenu(self)
        
        inspector_action = variables_menu.addAction("🔍 Variable Inspector")
        inspector_action.setToolTip("View all available variables in current context")
        inspector_action.triggered.connect(self._show_variable_inspector)
        
        library_action = variables_menu.addAction("📚 Extracted Variables Manager")
        library_action.setToolTip("Manage extracted variables library")
        library_action.triggered.connect(self._open_variable_library)
        
        variables_btn.setMenu(variables_menu)
        toolbar.addWidget(variables_btn)
        
        toolbar.addSeparator()
        
        # Git Sync button
        self.git_sync_btn = QPushButton("🔄 Git Sync")
        self.git_sync_btn.setToolTip("Manage Git-based collaboration")
        self.git_sync_btn.clicked.connect(self._open_git_sync_dialog)
        toolbar.addWidget(self.git_sync_btn)
        
        # Git sync status indicator
        self.git_sync_status_label = QLabel("Git: Not Enabled")
        self.git_sync_status_label.setStyleSheet("color: #999; font-size: 11px; padding: 0 10px;")
        toolbar.addWidget(self.git_sync_status_label)
        
        # Add spacer to push theme toggle to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        spacer.setStyleSheet("background: transparent;")
        toolbar.addWidget(spacer)
        
        # Theme toggle button
        self.theme_toggle_btn = QPushButton()
        self._update_theme_button()
        self.theme_toggle_btn.setToolTip("Toggle dark/light theme")
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self.theme_toggle_btn)
        
        # Help hint in top right corner
        help_hint = QLabel("💡 Press Ctrl+/ for shortcuts")
        help_hint.setStyleSheet("color: #2196F3; font-size: 12px; padding-right: 10px;")
        help_hint.setToolTip("Show keyboard shortcuts help")
        toolbar.addWidget(help_hint)
    
    def _create_status_bar(self):
        """Create the bottom status bar with save status and Git sync info."""
        status_bar = self.statusBar()
        
        # Save status widget
        self.save_status_label = QLabel("Ready")
        self.save_status_label.setStyleSheet("padding: 0 10px;")
        status_bar.addWidget(self.save_status_label)
        
        # Add stretch to push items to the right
        status_bar.addPermanentWidget(QLabel())  # Spacer
        
        # Git sync status (permanent widget on right)
        self.status_git_sync_label = QLabel("")
        self.status_git_sync_label.setStyleSheet("padding: 0 10px;")
        status_bar.addPermanentWidget(self.status_git_sync_label)
    
    def _update_save_status(self, message: str, duration: int = 3000):
        """Update the status bar with a save status message."""
        self.save_status_label.setText(message)
        if duration > 0:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(duration, lambda: self.save_status_label.setText("Ready"))
    
    def _update_status_bar(self):
        """Update status bar with current state."""
        # Update Git sync status
        if self.git_workspace:
            self.status_git_sync_label.setText(f"📁 Git: {self.git_workspace['name']}")
        else:
            self.status_git_sync_label.setText("")
    
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
            response_data = {
                'status_code': self.current_response.status_code,
                'headers': self.current_response.headers,
                'text': self.current_response.text,
                'size': self.current_response.size,
                'elapsed_time': self.current_response.elapsed_time
            }
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
        
        return {
            'request_id': self.current_request_id,
            'collection_id': self.current_collection_id,
            'method': self.method_combo.currentText(),
            'url': self.url_input.text(),
            'params': self._get_table_as_dict(self.params_table),
            'headers': self._get_table_as_dict(self.headers_table),
            'body': self.body_input.toPlainText(),
            'auth_type': self.auth_type_combo.currentText(),
            'auth_token': self.auth_token_input.text(),
            'description': self.description_input.toPlainText(),
            'request_name': self.current_request_name or 'Untitled',
            'has_changes': self.has_unsaved_changes,
            'response': response_data,  # Add response data
            'test_results': test_results_data  # Add test results data
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
        self.auth_type_combo.blockSignals(True)
        self.auth_token_input.blockSignals(True)
        self.description_input.blockSignals(True)
        
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
            
            # Load body
            self.body_input.setPlainText(state.get('body', ''))
            
            # Load auth
            self.auth_type_combo.setCurrentText(state.get('auth_type', 'None'))
            self.auth_token_input.setText(state.get('auth_token', ''))
            
            # Load description
            self.description_input.setPlainText(state.get('description', ''))
            
            # Load test assertions from database (FIX: This was missing!)
            if self.current_request_id:
                self._load_test_assertions(self.current_request_id)
            else:
                self.test_tab.clear()
            
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
            self.auth_type_combo.blockSignals(False)
            self.auth_token_input.blockSignals(False)
            self.description_input.blockSignals(False)
        
        # Update tab counts after restoration (FIX: Update counts for all inner tabs)
        self._update_tab_counts()
        
        # Restore response if available
        response_data = state.get('response')
        if response_data:
            print(f"[DEBUG] Restoring response: status={response_data.get('status_code')}, size={response_data.get('size')}")
            self._restore_response(response_data)
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
            except Exception as e:
                print(f"[DEBUG] Failed to restore test results: {e}")
                # If restoration fails, just clear
                self.test_results_viewer.clear()
                self._current_test_results = None
        else:
            print("[DEBUG] No test results to restore")
            # No test results - clear the viewer
            if hasattr(self, 'test_results_viewer') and self.test_results_viewer is not None:
                self.test_results_viewer.clear()
            self._current_test_results = None
    
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
            elif tab_state.get('request_id'):
                # No UI state but has request_id - load from database directly
                print(f"[DEBUG] Loading request data from DB for tab {index}")
                self._load_request_data(tab_state['request_id'])  # Use _load_request_data instead of _load_request
                # _load_request_data will call _update_current_request_highlight() at its end
            else:
                # Empty tab - clear editor
                print(f"[DEBUG] Clearing editor for empty tab {index}")
                self._clear_request_editor()
                # Update highlight for empty tab
                self._update_current_request_highlight()
            
            # Update tab title
            self._update_tab_title(index)
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
            self.center_stack.setCurrentWidget(self.no_request_empty_state)
        else:
            # Switch to the current tab
            self._on_tab_changed(self.request_tabs.currentIndex())
        
        # Update collections tree highlighting after closing tab
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
    
    def _open_request_in_new_tab(self, request_id: int):
        """Open an existing request in a new tab."""
        print(f"[DEBUG] _open_request_in_new_tab called with request_id={request_id}")
        
        # Check if this request is already open in a tab
        existing_tab = self._find_tab_with_request(request_id)
        if existing_tab >= 0:
            # Request is already open - switch to that tab instead of creating a new one
            print(f"[DEBUG] Request {request_id} already open in tab {existing_tab}, switching to it")
            self.request_tabs.setCurrentIndex(existing_tab)
            self.center_stack.setCurrentWidget(self.tabs_container)
            return
        
        # Load the request data from database
        request_data = self.db.get_request(request_id)
        if not request_data:
            QMessageBox.warning(self, "Error", "Failed to load request!")
            return
        
        # Save current tab state first
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
            'ui_state': {}  # Will be populated when tab is activated
        }
        print(f"[DEBUG] Stored tab state for index {tab_index}, all tab_states keys: {list(self.tab_states.keys())}")
        
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
        self.center_stack.setCurrentWidget(self.tabs_container)
    
    def _update_tab_title(self, index: int):
        """Update tab title with method and name."""
        if index not in self.tab_states:
            return
        
        state = self.tab_states[index]
        method = state.get('method', 'GET')
        name = state.get('name', 'Untitled')
        has_changes = state.get('has_changes', False)
        
        # Update tab data for custom rendering
        tab_bar = self.request_tabs.tabBar()
        if isinstance(tab_bar, ColoredTabBar):
            tab_bar.set_tab_data(index, method, name, has_changes)
        
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
    
    def _create_collections_pane(self) -> QWidget:
        """Create the left pane containing the collections tree."""
        pane = QWidget()
        layout = QVBoxLayout(pane)
        
        # Title
        title = QLabel("Collections")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Collections tree
        self.collections_tree = QTreeWidget()
        self.collections_tree.setHeaderHidden(True)  # Hide "Name" header
        self.collections_tree.setIconSize(QSize(16, 16))  # Standardize icon size to 16px
        # Set custom delegate for colored method badges
        self.collections_tree.setItemDelegate(RequestTreeItemDelegate())
        # Single-click on collections to expand/collapse
        self.collections_tree.itemClicked.connect(self._on_tree_item_clicked)
        # Double-click on requests to open in new tab
        self.collections_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        # Connect expand/collapse signals for folder icon updates
        self.collections_tree.itemExpanded.connect(self._on_tree_item_expanded)
        self.collections_tree.itemCollapsed.connect(self._on_tree_item_collapsed)
        # Disable selection highlighting
        self.collections_tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.collections_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.collections_tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        layout.addWidget(self.collections_tree)
        
        # Bottom button row - Compact layout with dropdown
        button_layout = QHBoxLayout()
        
        add_collection_btn = QPushButton("Add Collection")
        add_collection_btn.setToolTip("Add a new collection")
        add_collection_btn.clicked.connect(self._add_collection)
        button_layout.addWidget(add_collection_btn)
        
        # Import button with dropdown menu
        import_menu_btn = QPushButton("📥 Import")
        import_menu_btn.setToolTip("Import collections, cURL commands, or OpenAPI specs")
        
        # Create dropdown menu
        import_menu = QMenu(import_menu_btn)
        
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
        import_menu_btn.setMenu(import_menu)
        button_layout.addWidget(import_menu_btn)
        
        layout.addLayout(button_layout)
        
        return pane
    
    def _create_workspace_pane(self) -> QWidget:
        """Create the right pane with request editor and response viewer."""
        pane = QWidget()
        layout = QVBoxLayout(pane)
        
        # Create vertical splitter (request editor | response viewer)
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setChildrenCollapsible(False)  # Prevent panels from collapsing
        
        # Top section: Request Editor
        request_editor = self._create_request_editor()
        self.main_splitter.addWidget(request_editor)
        
        # Bottom section: Response Viewer
        response_viewer = self._create_response_viewer()
        self.main_splitter.addWidget(response_viewer)
        
        # Set splitter sizes to 50/50 split (equal space for request and response)
        # This will maintain proper proportions when window is maximized
        self.main_splitter.setStretchFactor(0, 1)  # Request editor - 50%
        self.main_splitter.setStretchFactor(1, 1)  # Response viewer - 50%
        
        layout.addWidget(self.main_splitter)
        
        # Set initial sizes to 50/50 split after window is shown
        # This will be calculated based on actual available height
        
        return pane
    
    def _create_request_editor(self) -> QWidget:
        """Create the request editor section."""
        editor = QWidget()
        layout = QVBoxLayout(editor)
        layout.setSpacing(8)
        
        # Dynamic request title header (fixed height, no stretch) - ENHANCED
        # Create a container for the title label and rename button
        title_container = QWidget()
        title_container.setMaximumHeight(40)
        title_container.setMinimumHeight(40)
        title_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_layout.setSpacing(6)  # Smaller spacing for inline appearance
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Vertical center alignment
        
        self.request_title_label = QLabel("New Request (not saved)")
        self.request_title_label.setObjectName("requestTitleLabel")
        self.request_title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
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
        
        # Add stretch to push everything to the left
        title_layout.addStretch()
        
        layout.addWidget(title_container, 0)  # Stretch factor 0 = fixed
        
        # Method and URL row (fixed height, no stretch)
        # Wrap in a container widget to enforce fixed height
        url_container = QWidget()
        url_container.setMaximumHeight(48)  # Increased from 40 to 48 for better presence
        url_container.setMinimumHeight(48)
        url_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        url_layout = QHBoxLayout(url_container)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(12)  # Increased spacing for better visual separation
        
        # HTTP Method Combo with improved styling
        self.method_combo = QComboBox()
        self.method_combo.addItems(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
        self.method_combo.setObjectName("methodCombo")  # For stylesheet targeting
        self.method_combo.setMaximumWidth(100)
        self.method_combo.setMinimumHeight(38)  # Match other controls
        self.method_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Apply method-specific colors via styleSheet update on change
        self.method_combo.currentTextChanged.connect(self._update_method_style)
        url_layout.addWidget(self.method_combo)
        
        self.url_input = HighlightedLineEdit(theme=self.current_theme)
        self.url_input.setPlaceholderText("Enter request URL or paste text")
        self.url_input.returnPressed.connect(self._send_request)  # Enter key sends request
        self.url_input.setMinimumHeight(38)  # Make URL input taller
        self.url_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        url_layout.addWidget(self.url_input)
        
        # IMPROVED: Larger, more prominent Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")  # For stylesheet targeting
        self.send_btn.setProperty("class", "primary")
        self.send_btn.setProperty("primary", "true")  # For QSS targeting
        self.send_btn.setMinimumWidth(100)  # Increased from 80
        self.send_btn.setMinimumHeight(38)  # Explicit height
        self.send_btn.clicked.connect(self._send_request)
        self.send_btn.setToolTip("Send request (Ctrl+Enter)")
        self.send_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Set font to make it more prominent
        send_font = QFont()
        send_font.setBold(True)
        send_font.setPixelSize(14)
        self.send_btn.setFont(send_font)
        url_layout.addWidget(self.send_btn)
        
        # Add 8px spacing between buttons (4-point grid)
        url_layout.addSpacing(8)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setMinimumWidth(80)
        self.save_btn.setMinimumHeight(38)  # Match Send button height
        self.save_btn.clicked.connect(self._save_request)
        self.save_btn.setToolTip("Save request (Ctrl+S)")
        self.save_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        url_layout.addWidget(self.save_btn)
        
        # Add 8px spacing between buttons (4-point grid)
        url_layout.addSpacing(8)
        
        self.code_btn = QPushButton("💻 Code")
        self.code_btn.setMinimumWidth(80)
        self.code_btn.setMinimumHeight(38)  # Match Send button height
        self.code_btn.clicked.connect(self._generate_code)
        self.code_btn.setToolTip("Generate code snippet (Ctrl+Shift+C)")
        self.code_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        url_layout.addWidget(self.code_btn)
        
        layout.addWidget(url_container, 0)  # Stretch factor 0 = fixed
        
        # Connect inputs to track changes and update title
        self.method_combo.currentIndexChanged.connect(self._mark_as_changed)
        self.method_combo.currentIndexChanged.connect(self._update_request_title)  # Update title when method changes
        self.url_input.textChanged.connect(self._mark_as_changed)
        
        # Description section (collapsible)
        self.description_widget = self._create_description_section()
        layout.addWidget(self.description_widget)
        
        # Tabs for Params, Headers, Authorization, Body (this should expand)
        self.inner_tabs = QTabWidget()
        self.inner_tabs.setObjectName("innerTabs")  # For specific styling
        # Remove maximum height constraint - let it expand to fill available space
        self.inner_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Params tab
        self.params_table = self._create_key_value_table()
        self.params_table.itemChanged.connect(self._update_tab_counts)
        self.inner_tabs.addTab(self.params_table, "Params")
        
        # Headers tab
        self.headers_table = self._create_key_value_table()
        self.headers_table.itemChanged.connect(self._update_tab_counts)
        self.inner_tabs.addTab(self.headers_table, "Headers")
        
        # Authorization tab
        auth_widget = self._create_auth_widget()
        self.inner_tabs.addTab(auth_widget, "Authorization")
        
        # Body tab
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Enter request body (e.g., JSON)")
        self.body_input.textChanged.connect(self._mark_as_changed)
        
        # Add variable syntax highlighting to body
        self.body_highlighter = VariableSyntaxHighlighter(self.body_input.document(), self.current_theme)
        
        body_layout.addWidget(self.body_input)
        self.inner_tabs.addTab(body_widget, "Body")
        
        # Tests tab
        self.test_tab = TestTabWidget()
        self.test_tab.assertions_changed.connect(self._on_tests_changed)
        self.inner_tabs.addTab(self.test_tab, "Tests")
        
        # Initialize tab counts
        self._update_tab_counts()
        
        layout.addWidget(self.inner_tabs, 1)  # Stretch factor 1 = expands to fill
        
        return editor
    
    def _create_response_viewer(self) -> QWidget:
        """Create the response viewer section."""
        viewer = QWidget()
        layout = QVBoxLayout(viewer)
        
        # Title row with collapse icon
        title_layout = QHBoxLayout()
        
        # Collapse icon (clickable)
        self.response_collapse_icon = QLabel("▼")
        self.response_collapse_icon.setFont(QFont("Arial", 12))
        self.response_collapse_icon.setFixedWidth(20)
        self.response_collapse_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.response_collapse_icon.setToolTip("Collapse/Expand response panel")
        self.response_collapse_icon.mousePressEvent = lambda event: self._toggle_response_panel()
        title_layout.addWidget(self.response_collapse_icon)
        
        title = QLabel("Response")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Create collapsible content container
        self.response_content_widget = QWidget()
        response_content_layout = QVBoxLayout(self.response_content_widget)
        response_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status info row
        status_layout = QHBoxLayout()
        
        # Use StatusBadge widget for professional status display
        self.status_badge = StatusBadge()
        self.status_badge.setVisible(False)  # Hidden until we have a response
        status_layout.addWidget(self.status_badge)
        
        # Metadata labels - use tertiary color for less prominence
        self.status_label = QLabel("Status: -")
        self.status_label.setProperty("class", "tertiary")  # Tertiary text for metadata
        status_layout.addWidget(self.status_label)
        
        self.time_label = QLabel("Time: -")
        self.time_label.setProperty("class", "tertiary")  # Tertiary text for metadata
        status_layout.addWidget(self.time_label)
        
        self.size_label = QLabel("Size: -")
        self.size_label.setProperty("class", "tertiary")  # Tertiary text for metadata
        status_layout.addWidget(self.size_label)
        
        status_layout.addStretch()
        
        # Copy response button
        self.copy_response_btn = QPushButton("📋 Copy Response")
        self.copy_response_btn.setObjectName("copyButton")  # For stylesheet targeting
        self.copy_response_btn.setProperty("class", "secondary")
        self.copy_response_btn.clicked.connect(self._copy_response)
        self.copy_response_btn.setMaximumWidth(150)
        status_layout.addWidget(self.copy_response_btn)
        
        response_content_layout.addLayout(status_layout)
        
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
        self.response_search.setMaximumWidth(250)
        toolbar_layout.addWidget(self.response_search)
        
        toolbar_layout.addStretch()
        
        # Formatting controls
        self.pretty_raw_btn = QPushButton("📄 Pretty")
        self.pretty_raw_btn.setCheckable(True)
        self.pretty_raw_btn.setChecked(True)  # Pretty mode by default
        self.pretty_raw_btn.setMaximumWidth(100)
        self.pretty_raw_btn.setToolTip("Toggle between Pretty (formatted) and Raw view")
        self.pretty_raw_btn.clicked.connect(self._toggle_pretty_raw)
        toolbar_layout.addWidget(self.pretty_raw_btn)
        
        self.word_wrap_btn = QPushButton("↔️ Wrap")
        self.word_wrap_btn.setCheckable(True)
        self.word_wrap_btn.setChecked(False)  # No wrap by default
        self.word_wrap_btn.setMaximumWidth(100)
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
        
        # Add padding to body widget
        body_layout.setContentsMargins(10, 10, 10, 10)
        
        self.response_tabs.addTab(body_widget, "Body")
        
        # Headers tab
        self.response_headers_table = QTableWidget()
        self.response_headers_table.setColumnCount(2)
        self.response_headers_table.setHorizontalHeaderLabels(['Key', 'Value'])
        self.response_headers_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.response_tabs.addTab(self.response_headers_table, "Headers")
        
        # Variable Extraction tab
        self.variable_extraction_widget = VariableExtractionWidget()
        self.variable_extraction_widget.variable_extracted.connect(self._on_variable_extracted)
        self.response_tabs.addTab(self.variable_extraction_widget, "Extract Variables")
        
        response_content_layout.addWidget(self.response_tabs)
        
        # Test results viewer
        self.test_results_viewer = TestResultsViewer()
        response_content_layout.addWidget(self.test_results_viewer)
        
        layout.addWidget(self.response_content_widget)
        
        return viewer
    
    def _create_key_value_table(self) -> QTableWidget:
        """Create a table widget for key-value pairs (params/headers)."""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Key', 'Value'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setRowCount(3)  # Start with 3 empty rows (reduced for better space)
        
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
    
    def _create_description_section(self) -> QWidget:
        """Create a collapsible description/notes section."""
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Header with collapse/expand button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.description_toggle_btn = QPushButton("▶ Description")
        self.description_toggle_btn.setFlat(True)
        self.description_toggle_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 4px 8px;
                border: none;
                background: transparent;
                color: #9E9E9E;  /* Secondary text for form labels */
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.2);
            }
        """)
        self.description_toggle_btn.clicked.connect(self._toggle_description)
        header_layout.addWidget(self.description_toggle_btn)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Description text area (initially collapsed)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Add notes or description for this request...")
        self.description_input.setMaximumHeight(100)
        self.description_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.description_input.textChanged.connect(self._mark_as_changed)
        self.description_input.setVisible(False)  # Start collapsed
        layout.addWidget(self.description_input)
        
        return container
    
    def _toggle_description(self):
        """Toggle the visibility of the description section."""
        # Use testAttribute to check explicit visibility state (works even when parent is hidden)
        from PyQt6.QtCore import Qt
        is_visible = self.description_input.testAttribute(Qt.WidgetAttribute.WA_WState_ExplicitShowHide) and \
                    not self.description_input.testAttribute(Qt.WidgetAttribute.WA_WState_Hidden)
        self.description_input.setVisible(not is_visible)
        
        # Update button text
        if is_visible:
            self.description_toggle_btn.setText("▶ Description")
        else:
            self.description_toggle_btn.setText("▼ Description")
    
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
        self.auth_token_input = QLineEdit()
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
    
    def _load_collections(self):
        """Load all collections, folders, and requests from database into the tree."""
        from PyQt6.QtGui import QIcon
        
        # Store currently expanded items (collections and folders) before clearing
        expanded_collection_ids = set()
        expanded_folder_ids = set()
        for i in range(self.collections_tree.topLevelItemCount()):
            item = self.collections_tree.topLevelItem(i)
            self._store_expanded_state(item, expanded_collection_ids, expanded_folder_ids)
        
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
            
            # Create collection item with custom icon
            collection_name = f"{collection['name']} [{request_count}]"
            collection_item = QTreeWidgetItem([collection_name])
            collection_item.setData(0, Qt.ItemDataRole.UserRole, 
                                   {'type': 'collection', 'id': collection['id'], 'name': collection['name']})
            collection_item.setIcon(0, QIcon(collection_icon_path))
            
            # Collection names should NOT be bold by default
            # Bold will be applied only when it contains the active request
            collection_item.setForeground(0, QBrush(QColor('#CCCCCC')))  # Light gray for collections
            
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
                                    'name': folder_data['name']})
                
                # Set icon based on expanded state
                if folder_data['id'] in expanded_folder_ids:
                    folder_item.setIcon(0, QIcon(folder_open_icon_path))
                    folder_item.setExpanded(True)
                else:
                    folder_item.setIcon(0, QIcon(folder_icon_path))
                
                folder_item.setForeground(0, QBrush(QColor('#CCCCCC')))  # Same gray as collections
                
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
        
        # Highlight currently opened request
        self._update_current_request_highlight()
    
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
        
        # Set text color to gray (same as collections/folders)
        request_item.setForeground(0, QBrush(QColor('#CCCCCC')))
        
        parent_item.addChild(request_item)
    
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
        """Handle single-click on tree item - only for expanding/collapsing collections and folders."""
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
        # Requests do nothing on single-click
    
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
            
            # Ignore if this is a duplicate double-click within 500ms
            if (current_time - self._last_double_click_time < 0.5 and 
                request_id == self._last_double_click_request_id):
                print(f"[DEBUG] Ignoring duplicate double-click on request {request_id}")
                return
            
            # Update last double-click tracking
            self._last_double_click_time = current_time
            self._last_double_click_request_id = request_id
            
            # Double-click on request - open in new tab (or switch to existing tab)
            print(f"[DEBUG] Double-click on request {request_id}, calling _open_request_in_new_tab")
            self._open_request_in_new_tab(request_id)
    
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
                # Show success toast
                self.toast.success(f"Collection '{name}' created")
            except Exception as e:
                self.toast.error(f"Failed to create collection: {str(e)[:30]}...")
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
                    url=''
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
                    url=''
                )
                self._load_collections()
                self.toast.success(f"Request '{name}' created")
                
                # Load the newly created request and show workspace
                self.current_request_id = request_id
                self.current_collection_id = collection_id
                self.center_stack.setCurrentWidget(self.tabs_container)
                self._load_request(request_id)
            except Exception as e:
                self.toast.error(f"Failed to create request: {str(e)[:50]}...")
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
                self._load_collections()
                self.toast.success(f"Folder '{name}' created")
            except Exception as e:
                self.toast.error(f"Failed to create folder: {str(e)[:50]}...")
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
                self._load_collections()
                self.toast.success(f"Subfolder '{name}' created")
            except Exception as e:
                self.toast.error(f"Failed to create subfolder: {str(e)[:50]}...")
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
                    url=''
                )
                # Move request to folder
                self.db.move_request_to_folder(request_id, folder_id)
                self._load_collections()
                self.toast.success(f"Request '{name}' created in folder '{folder_name}'")
                
                # Load the newly created request
                self.current_request_id = request_id
                self.current_collection_id = collection_id
                self.center_stack.setCurrentWidget(self.tabs_container)
                self._load_request(request_id)
            except Exception as e:
                self.toast.error(f"Failed to create request: {str(e)[:50]}...")
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
                self.toast.success(f"Folder renamed to '{name}'")
            except Exception as e:
                self.toast.error(f"Failed to rename folder: {str(e)[:50]}...")
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
                self.toast.success(f"Folder '{folder['name']}' deleted")
            except Exception as e:
                self.toast.error(f"Failed to delete folder: {str(e)[:50]}...")
                QMessageBox.critical(self, "Error", f"Failed to delete folder: {str(e)}")
    
    def _move_request_to_folder(self, request_id: int, folder_id: Optional[int]):
        """Move a request to a folder (or collection root if folder_id is None)."""
        try:
            self.db.move_request_to_folder(request_id, folder_id)
            self._load_collections()
            
            if folder_id is None:
                self.toast.success("Request moved to collection root")
            else:
                folder = self.db.get_folder(folder_id)
                folder_name = folder.get('name', 'folder') if folder else 'folder'
                self.toast.success(f"Request moved to '{folder_name}'")
        except Exception as e:
            self.toast.error(f"Failed to move request: {str(e)[:50]}...")
            QMessageBox.critical(self, "Error", f"Failed to move request: {str(e)}")
    
    def _manage_collection_variables(self, collection_id: int):
        """Show collection variables management dialog."""
        from src.ui.dialogs.collection_variables_dialog import CollectionVariablesDialog
        
        collection = self.db.get_collection(collection_id)
        collection_name = collection.get('name', 'Unknown') if collection else 'Unknown'
        
        dialog = CollectionVariablesDialog(self, self.db, collection_id, collection_name)
        dialog.exec()
    
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
                    self.toast.success(f"Collection '{item_name}' deleted")
                elif data['type'] == 'folder':
                    self.db.delete_folder(data['id'])
                    self.toast.success(f"Folder '{item_name}' deleted")
                elif data['type'] == 'request':
                    self.db.delete_request(data['id'])
                    if self.current_request_id == data['id']:
                        self.current_request_id = None
                        self._clear_request_editor()
                        self.center_stack.setCurrentWidget(self.no_request_empty_state)
                    self.toast.success(f"Request '{item_name}' deleted")
                
                # Auto-sync to filesystem if Git sync is enabled
                self._auto_sync_to_filesystem()
                
                self._load_collections()
            except Exception as e:
                self.toast.error(f"Failed to delete: {str(e)[:30]}...")
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")
    
    # ==================== Request Editor Management ====================
    
    def _load_request(self, request_id: int):
        """Load a request's details into the editor.
        If the request is already open in a tab, switch to that tab.
        Otherwise, create a new tab or load into the current tab."""
        try:
            # Check if this request is already open in any tab
            for tab_index, state in self.tab_states.items():
                if state.get('request_id') == request_id:
                    # Request is already open - switch to that tab
                    self.request_tabs.setCurrentIndex(tab_index)
                    # Make sure we're showing the tabs view
                    self.center_stack.setCurrentWidget(self.tabs_container)
                    # Track in recent requests
                    self.recent_requests_widget.add_request(request_id)
                    return
            
            # Request not open - check if current tab is empty or create new tab
            current_tab_index = self.request_tabs.currentIndex()
            current_state = self.tab_states.get(current_tab_index, {})
            
            # If no tabs exist (currentIndex = -1) or current tab has a request_id, create a new tab
            if current_tab_index < 0 or current_state.get('request_id'):
                tab_index = self._create_new_tab()
                self.request_tabs.setCurrentIndex(tab_index)
            # Otherwise, load into the current empty tab
            
            # Make sure we're showing the tabs view
            self.center_stack.setCurrentWidget(self.tabs_container)
            
            # Load the request data into the current tab
            self._load_request_data(request_id)
            
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
            
            # Load auth
            self.auth_type_combo.setCurrentText(request.get('auth_type', 'None'))
            auth_token = request.get('auth_token', '') or ''
            self.auth_token_input.setText(auth_token)
            
            # Load description
            description = request.get('description', '') or ''
            self.description_input.setPlainText(description)
            # Auto-expand description if it has content
            if description.strip():
                self.description_input.setVisible(True)
                self.description_toggle_btn.setText("▼ Description")
            else:
                self.description_input.setVisible(False)
                self.description_toggle_btn.setText("▶ Description")
            
            # Load test assertions
            self._load_test_assertions(request_id)
            
            # Clear test results
            self.test_results_viewer.clear()
            self._current_test_results = None  # Clear stored test results
            
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
    
    def _clear_request_editor(self):
        """Clear all fields in the request editor."""
        self.method_combo.setCurrentText('GET')
        self.url_input.clear()
        self.test_tab.clear()
        self.test_results_viewer.clear()
        self.params_table.clearContents()
        self.params_table.setRowCount(3)
        self.headers_table.clearContents()
        self.headers_table.setRowCount(3)
        self.body_input.clear()
        self.auth_type_combo.setCurrentText('None')
        self.auth_token_input.clear()
        self.description_input.clear()
        self.description_input.setVisible(False)
        self.description_toggle_btn.setText("▶ Description")
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
            table.setRowCount(3)
            return
        
        table.setRowCount(max(3, len(data) + 2))
        
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
    
    def _store_original_request_data(self):
        """Store the current request data for change detection."""
        self.original_request_data = {
            'method': self.method_combo.currentText(),
            'url': self.url_input.text(),
            'params': self._get_table_as_dict(self.params_table),
            'headers': self._get_table_as_dict(self.headers_table),
            'body': self.body_input.toPlainText(),
            'auth_type': self.auth_type_combo.currentText(),
            'auth_token': self.auth_token_input.text(),
            'description': self.description_input.toPlainText()
        }
    
    def _mark_as_changed(self):
        """Mark the request as having unsaved changes."""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self._update_request_title()
            
            # Update current tab's unsaved indicator
            current_tab_index = self.request_tabs.currentIndex()
            if current_tab_index >= 0 and current_tab_index in self.tab_states:
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
    
    def _update_request_title(self):
        """Update the request title label to show current state with breadcrumb (Postman-style)."""
        if self.current_request_id and self.current_request_name:
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
            
            # Show rename button for saved requests
            self.rename_request_btn.setVisible(True)
        else:
            # New unsaved request
            new_request_color = "#9E9E9E" if self.current_theme == 'light' else "#999999"
            self.request_title_label.setText(f"<span style='color: {new_request_color}; font-style: italic;'>New Request (not saved)</span>")
            self.request_title_label.setProperty("saved", "false")
            
            # Hide rename button for unsaved requests
            self.rename_request_btn.setVisible(False)
        
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
        if not self.current_request_id:
            QMessageBox.warning(self, "Warning", "No request selected to save!")
            return
        
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
                description=self.description_input.toPlainText()
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
            
            # Show success toast
            self.toast.success("Request saved successfully")
            
            # Auto-sync to filesystem if Git sync is enabled
            self._auto_sync_to_filesystem()
            
            self._load_collections()
        except Exception as e:
            self._update_save_status("✗ Failed to save request", duration=5000)
            self.toast.error(f"Failed to save: {str(e)[:40]}...")
            QMessageBox.critical(self, "Error", f"Failed to save request: {str(e)}")
    
    # ==================== Request Execution ====================
    
    def _send_request(self):
        """Execute the HTTP request and display the response."""
        url = self.url_input.text().strip()
        if not url:
            self.toast.warning("Please enter a URL!")
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
        
        # Show loading toast
        self.toast.info(f"Sending {self.method_combo.currentText()} request...")
        
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
        
        # Get auth token based on auth type
        auth_token = ""
        if auth_type == 'Bearer Token':
            auth_token = self.auth_token_input.text()
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
        
        # Apply variable substitution (collection vars -> environment vars -> extracted vars -> dynamic variables)
        # Dynamic variables ($variable) work even without an active environment
        
        # Get collection variables if we have a current collection
        collection_variables = {}
        if self.current_collection_id:
            collection_variables = self.db.get_collection_variables(self.current_collection_id)
        
        # Get extracted variables (always available)
        extracted_variables = {}
        all_extracted = self.db.get_all_extracted_variables()
        for var in all_extracted:
            # Store WITHOUT "extracted." prefix - the substitution code adds it
            extracted_variables[var['name']] = var['value']
        
        # Debug: Show what extracted variables are available
        if all_extracted:
            print(f"[DEBUG] Loaded {len(all_extracted)} extracted variables:")
            for var in all_extracted:
                print(f"  - {var['name']} = {var['value']}")
            print(f"[DEBUG] Variable dict keys: {list(extracted_variables.keys())}")
        else:
            print("[DEBUG] No extracted variables found in database")
        
        if self.env_manager.has_active_environment():
            # Get environment variables
            env_variables = self.env_manager.get_active_variables()
            
            # Merge variables: env_variables < collection_variables < extracted_variables
            merged_variables = {**env_variables, **collection_variables, **extracted_variables}
            
            print(f"[DEBUG] Using environment manager substitution")
            print(f"[DEBUG] Merged variables count: {len(merged_variables)}")
            print(f"[DEBUG] Merged variable keys: {list(merged_variables.keys())[:10]}")  # Show first 10
            
            # Substitute both {{env}} and $dynamic variables
            substituted, unresolved = self.env_manager.substitute_in_request(
                url, params, headers, body, auth_token, extra_variables=merged_variables
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
        elif collection_variables or extracted_variables:
            # No active environment, but we have collection variables or extracted variables
            from src.features.variable_substitution import VariableSubstitution
            
            print(f"[DEBUG] No active environment - using direct substitution")
            print(f"[DEBUG] Collection vars: {len(collection_variables)}")
            print(f"[DEBUG] Extracted vars: {len(extracted_variables)}")
            
            # Don't merge - pass separately!
            print(f"[DEBUG] Extracted variables dict: {extracted_variables}")
            
            # Substitute URL
            url, _ = VariableSubstitution.substitute(url, collection_variables, extracted_variables)
            print(f"[DEBUG] URL after substitution: {url}")
            
            # Substitute params
            if params:
                new_params = {}
                for k, v in params.items():
                    new_key, _ = VariableSubstitution.substitute(k, collection_variables, extracted_variables)
                    new_val, _ = VariableSubstitution.substitute(v, collection_variables, extracted_variables)
                    new_params[new_key] = new_val
                params = new_params
            
            # Substitute headers
            if headers:
                print(f"[DEBUG] Substituting headers: {headers}")
                new_headers = {}
                for k, v in headers.items():
                    new_key, _ = VariableSubstitution.substitute(k, collection_variables, extracted_variables)
                    new_val, _ = VariableSubstitution.substitute(v, collection_variables, extracted_variables)
                    print(f"[DEBUG]   {k}: {v} -> {new_key}: {new_val}")
                    new_headers[new_key] = new_val
                headers = new_headers
                print(f"[DEBUG] Headers after substitution: {headers}")
            
            # Substitute body
            if body:
                body, _ = VariableSubstitution.substitute(body, collection_variables, extracted_variables)
            
            # Substitute auth token
            if auth_token:
                auth_token, _ = VariableSubstitution.substitute(auth_token, collection_variables, extracted_variables)
        else:
            # No active environment, but still substitute dynamic variables
            from src.features.variable_substitution import VariableSubstitution
            
            # Substitute URL
            url, _ = VariableSubstitution.substitute(url, {})
            
            # Substitute params
            if params:
                substituted_params = {}
                for key, value in params.items():
                    new_key, _ = VariableSubstitution.substitute(str(key), {})
                    new_value, _ = VariableSubstitution.substitute(str(value), {})
                    substituted_params[new_key] = new_value
                params = substituted_params
            
            # Substitute headers
            if headers:
                substituted_headers = {}
                for key, value in headers.items():
                    new_key, _ = VariableSubstitution.substitute(str(key), {})
                    new_value, _ = VariableSubstitution.substitute(str(value), {})
                    substituted_headers[new_key] = new_value
                headers = substituted_headers
            
            # Substitute body
            if body:
                body, _ = VariableSubstitution.substitute(body, {})
            
            # Substitute auth token
            if auth_token:
                auth_token, _ = VariableSubstitution.substitute(auth_token, {})
        
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
            self.toast.warning("Invalid timeout value, using default (30s)")
            self.api_client.timeout = 30
        
        # Set SSL verification option
        self.api_client.verify_ssl = self.verify_ssl_checkbox.isChecked()
        if not self.api_client.verify_ssl:
            self.toast.warning("SSL verification disabled - not recommended for production!")
        
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
        
        # Create and start request thread
        self.request_thread = RequestThread(
            self.api_client, method, url, params, headers, body, auth_type, auth_token
        )
        self.request_thread.finished.connect(self._on_request_finished)
        self.request_thread.error.connect(self._on_request_error)
        self.request_thread.start()
    
    def _on_request_finished(self, response: ApiResponse):
        """Handle successful request completion."""
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
        
        # Show success toast with status code
        status_code = response.status_code
        time_ms = int(response.elapsed_time * 1000)
        
        if 200 <= status_code < 300:
            self.toast.success(f"{status_code} OK • {time_ms}ms")
        elif 300 <= status_code < 400:
            self.toast.info(f"{status_code} Redirect • {time_ms}ms")
        elif 400 <= status_code < 500:
            self.toast.warning(f"{status_code} Client Error • {time_ms}ms")
        else:
            self.toast.error(f"{status_code} Server Error • {time_ms}ms")
        
        # Display response
        self._display_response(response)
        
        # Execute tests
        self._execute_tests_on_response(response)
        
        # Save to history
        self._save_to_history(response=response)
    
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
        
        # Show error toast with helpful message
        self.toast.error(f"Request failed: {enhanced_error['short'][:50]}...")
        
        # Display error in response viewer with full details and suggestions
        self.status_label.setText(f"Status: Error")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        self.response_body.setPlainText(enhanced_error['full'])
        
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
        # Store response for later use (Raw/Pretty toggle)
        self.current_response = response
        self.current_response_raw = response.text
        
        # Update status badge with professional styling
        self.status_badge.set_status(response.status_code)
        self.status_badge.setVisible(True)
        
        # Determine status color and icon based on status code
        status_code = response.status_code
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
        
        self.time_label.setText(f"⏱ {response.elapsed_time:.2f}s")
        self.time_label.setStyleSheet("font-weight: bold;")
        
        # Display size with warning for large responses
        size_text = self._format_size(response.size)
        if response.size > 1_000_000:  # > 1MB
            self.size_label.setText(f"📦 {size_text} ⚠️")
            self.size_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            self.toast.warning(f"Large response: {size_text}")
        else:
            self.size_label.setText(f"📦 {size_text}")
            self.size_label.setStyleSheet("font-weight: bold;")
        
        # Determine content type
        content_type = response.headers.get('content-type', response.headers.get('Content-Type', ''))
        
        # Display response body with formatting
        is_json = False
        try:
            # Try to parse and pretty-print JSON
            json_data = json.loads(response.text)
            self.current_response_pretty = json.dumps(json_data, indent=2)
            is_json = True
        except (json.JSONDecodeError, ValueError):
            # Not JSON, use raw text
            self.current_response_pretty = response.text
        
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
        self.response_headers_table.setRowCount(len(response.headers))
        for i, (key, value) in enumerate(response.headers.items()):
            self.response_headers_table.setItem(i, 0, QTableWidgetItem(key))
            self.response_headers_table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        # Update variable extraction widget with response
        request_name = getattr(self, 'current_request_name', None) or "Unnamed Request"
        self.variable_extraction_widget.set_response(response, request_name)
    
    def _clear_response_viewer(self):
        """Clear the response viewer."""
        self.status_badge.setVisible(False)
        self.status_label.setText("Status: -")
        self.time_label.setText("Time: -")
        self.size_label.setText("Size: -")
        self.response_body.clear()
        self.response_headers_table.clearContents()
        self.response_headers_table.setRowCount(0)
        self.current_response = None
        self.current_response_raw = ""
        self.current_response_pretty = ""
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
            self.splitter_sizes_before_collapse = self.main_splitter.sizes()
            
            # Hide content and adjust splitter to minimal response panel size
            self.response_content_widget.hide()
            self.response_collapse_icon.setText("▶")
            
            # Get total height and set response panel to minimal height (60px for header)
            total_height = sum(self.main_splitter.sizes())
            self.main_splitter.setSizes([total_height - 60, 60])
        else:
            self.response_content_widget.show()
            self.response_collapse_icon.setText("▼")
            
            # Restore previous sizes or use default proportions
            if hasattr(self, 'splitter_sizes_before_collapse'):
                self.main_splitter.setSizes(self.splitter_sizes_before_collapse)
            else:
                # Default: 45-55 split
                total_height = sum(self.main_splitter.sizes())
                self.main_splitter.setSizes([int(total_height * 0.45), int(total_height * 0.55)])
    
    def _expand_response_panel(self):
        """Ensure response panel is expanded (called when sending request)."""
        if self.response_panel_collapsed:
            self._toggle_response_panel()
    
    def _toggle_recent_requests(self):
        """Toggle the recent requests panel visibility."""
        is_visible = self.recent_requests_widget.isVisible()
        self.recent_requests_widget.setVisible(not is_visible)
        self.recent_requests_btn.setChecked(not is_visible)
    
    def _reset_copy_button(self):
        """Reset the copy button to its original state."""
        self.copy_response_btn.setText("📋 Copy Response")
        self.copy_response_btn.setStyleSheet("")  # Reset to use global stylesheet
    
    def _search_response(self, search_text: str):
        """Search for text in the response body and highlight matches."""
        if not search_text:
            # Clear any existing highlights
            cursor = self.response_body.textCursor()
            cursor.select(cursor.SelectionType.Document)
            cursor.setCharFormat(self.response_body.currentCharFormat())
            cursor.clearSelection()
            self.response_body.setTextCursor(cursor)
            return
        
        # Find and highlight all occurrences
        from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
        
        # Clear previous highlights
        cursor = self.response_body.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        # Create highlight format
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#FFEB3B"))  # Yellow highlight
        highlight_format.setForeground(QColor("#000000"))  # Black text
        
        # Find all matches
        self.response_body.moveCursor(QTextCursor.MoveOperation.Start)
        found = self.response_body.find(search_text)
        
        if not found:
            # Move cursor back to start
            self.response_body.moveCursor(QTextCursor.MoveOperation.Start)
        
        cursor.endEditBlock()
    
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
    
    def _open_environment_dialog(self):
        """Open the environment management dialog."""
        dialog = EnvironmentDialog(self.db, self)
        dialog.exec()
        
        # Reload environments after dialog closes
        self._load_environments()
    
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
                self.toast.success(f"Collection '{collection['name']}' exported successfully")
                QMessageBox.information(
                    self, "Success",
                    f"Collection '{collection['name']}' exported successfully!\n\nFormat: {format_name}\nFile: {file_path}"
                )
            else:
                self.toast.error("Failed to export collection")
                QMessageBox.critical(self, "Error", "Failed to export collection!")
                
        except Exception as e:
            self.toast.error(f"Export failed: {str(e)[:30]}...")
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
                
                self.toast.success("Collection imported successfully")
                QMessageBox.information(self, "Success", message)
            else:
                self.toast.warning("Import was not completed")
                QMessageBox.warning(self, "Import Failed", message)
                
        except Exception as e:
            self.toast.error(f"Import failed: {str(e)[:30]}...")
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
    
    def _import_curl(self):
        """Import a cURL command and create a new request."""
        if not self.current_collection_id:
            QMessageBox.warning(
                self,
                "No Collection Selected",
                "Please select a collection first, then import the cURL command."
            )
            return
        
        # Open cURL import dialog
        dialog = CurlImportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            request_data = dialog.get_request_data()
            
            if not request_data:
                return
            
            # Ask for request name
            from PyQt6.QtWidgets import QInputDialog
            request_name, ok = QInputDialog.getText(
                self,
                "Request Name",
                "Enter a name for this request:",
                text=f"{request_data['method']} {request_data['url'].split('/')[-1] or 'Request'}"
            )
            
            if not ok or not request_name.strip():
                return
            
            try:
                # Create the request in the database
                request_id = self.db.create_request(
                    collection_id=self.current_collection_id,
                    name=request_name.strip(),
                    url=request_data['url'],
                    method=request_data['method']
                )
                
                # Update parameters
                if request_data.get('params'):
                    self.db.update_request_params(request_id, request_data['params'])
                
                # Update headers
                if request_data.get('headers'):
                    self.db.update_request_headers(request_id, request_data['headers'])
                
                # Update body
                if request_data.get('body'):
                    self.db.update_request_body(request_id, request_data['body'])
                
                # Reload the collection tree
                self._load_collections()
                
                # Select the new request
                self._select_request_by_id(request_id)
                
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
                        description=request.get('description', '')
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
                        description=request.get('description', '')
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
                        error_message: Optional[str] = None):
        """Save the current request to history."""
        try:
            # Get request details
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
                response_status = response.status_code
                response_headers = response.headers
                response_body = response.text
                response_time = response.elapsed_time
                response_size = response.size
            
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
                error_message=error_message
            )
        except Exception as e:
            print(f"Failed to save history: {e}")
    
    def _open_history_dialog(self):
        """Open the request history dialog."""
        dialog = HistoryDialog(self.db, self)
        dialog.replay_requested.connect(self._replay_from_history)
        dialog.exec()
    
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
        library.variable_deleted.connect(self._on_variable_deleted)
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
            
            # Show success toast
            self.toast.success(f"Variable '{name}' saved! Use {{{{extracted.{name}}}}} in requests")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save variable: {str(e)}"
            )
    
    def _on_variable_deleted(self, variable_id: int):
        """Handle variable deletion."""
        try:
            self.db.delete_extracted_variable(variable_id)
            self.toast.success("Variable deleted")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete variable: {str(e)}"
            )
    
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
        """Replay a request from history."""
        try:
            # Get or create a tab for this request
            current_tab_index = self.request_tabs.currentIndex()
            
            # Check if current tab is empty (no request loaded)
            if current_tab_index >= 0 and current_tab_index in self.tab_states:
                tab_state = self.tab_states[current_tab_index]
                if tab_state['request_id'] is None:
                    # Use current empty tab
                    tab_index = current_tab_index
                else:
                    # Create a new tab
                    tab_index = self._create_new_tab()
            else:
                # Create a new tab
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
            
            # Mark tab as having unsaved changes
            self.tab_states[tab_index]['has_changes'] = True
            self.tab_states[tab_index]['name'] = f"{history_entry['method']} (from history)"
            self._update_tab_title(tab_index)
            
            # Show the request editor (switch from empty state if needed)
            self.center_stack.setCurrentWidget(self.tabs_container)
            
            # Show success message
            self.toast.success(
                f"Request loaded from history: {history_entry['method']} {history_entry['url']}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to replay request: {str(e)}")
    
    # ==================== Code Generation ====================
    
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
            self.git_sync_btn.setStyleSheet("")
            return
        
        # Get sync status
        status = self.git_sync_manager.get_sync_status()
        
        # Update label and button style (dark-mode friendly)
        if status.status == SyncStatus.STATUS_SYNCED:
            self.git_sync_status_label.setText("Files: ✅ Synced")
            self.git_sync_status_label.setStyleSheet("color: #4CAF50; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Database and .postmini/ files are in sync")
            self.git_sync_btn.setStyleSheet("")
        elif status.status == SyncStatus.STATUS_NEEDS_PULL:
            self.git_sync_status_label.setText("Files: 📥 Import Available")
            self.git_sync_status_label.setStyleSheet("color: #2196F3; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Files in .postmini/ have changes - click to import")
            # Dark mode friendly - use border instead of light background
            self.git_sync_btn.setStyleSheet("border: 2px solid #2196F3; font-weight: bold;")
        elif status.status == SyncStatus.STATUS_NEEDS_PUSH:
            self.git_sync_status_label.setText("Files: 📤 Export Needed")
            self.git_sync_status_label.setStyleSheet("color: #FF9800; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Database has unsaved changes - click to export")
            # Dark mode friendly - use border instead of light background
            self.git_sync_btn.setStyleSheet("border: 2px solid #FF9800; font-weight: bold;")
        elif status.status == SyncStatus.STATUS_CONFLICT:
            self.git_sync_status_label.setText("Files: ⚠️ Conflict")
            self.git_sync_status_label.setStyleSheet("color: #F44336; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Both database and files have changes")
            # Dark mode friendly - use border instead of light background
            self.git_sync_btn.setStyleSheet("border: 2px solid #F44336; font-weight: bold;")
        else:
            self.git_sync_status_label.setText("Files: Enabled")
            self.git_sync_status_label.setStyleSheet("color: #666; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("File sync enabled")
            self.git_sync_btn.setStyleSheet("")
    
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
        if self.current_theme == "dark":
            self.theme_toggle_btn.setText("☀️")  # Sun icon for switching to light
            self.theme_toggle_btn.setToolTip("Switch to Light Theme")
        else:
            self.theme_toggle_btn.setText("🌙")  # Moon icon for switching to dark
            self.theme_toggle_btn.setToolTip("Switch to Dark Theme")
    
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
            self._update_theme_button()
            
            # Update rename button style for new theme
            self._update_rename_button_style()
            
            # Refresh request title to use theme-aware colors
            self._update_request_title()
            
            # Update variable highlighters for new theme
            if hasattr(self, 'url_input') and hasattr(self.url_input, 'set_theme'):
                self.url_input.set_theme(new_theme)
            if hasattr(self, 'body_highlighter'):
                self.body_highlighter.set_theme(new_theme)
            
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
                self.toast.success(f"Collection renamed to '{new_name}'")
            except Exception as e:
                self.toast.error(f"Failed to rename: {str(e)[:30]}...")
    
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
                    auth_token=request.get('auth_token', '')
                )
            
            self._auto_sync_to_filesystem()
            self._load_collections()
            self.toast.success(f"Collection '{collection['name']}' duplicated")
        except Exception as e:
            self.toast.error(f"Failed to duplicate: {str(e)[:30]}...")
    
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
                self.toast.success(f"Collection '{collection['name']}' deleted")
            except Exception as e:
                self.toast.error(f"Failed to delete: {str(e)[:30]}...")
    
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
            self.toast.success("cURL command copied to clipboard")
        except Exception as e:
            self.toast.error(f"Failed to copy: {str(e)[:30]}...")
    
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
                
                self.toast.success(f"Request renamed to '{new_name}'")
            except Exception as e:
                self.toast.error(f"Failed to rename: {str(e)[:30]}...")
    
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
                auth_token=request.get('auth_token', '')
            )
            self._auto_sync_to_filesystem()
            self._load_collections()
            self.toast.success(f"Request duplicated as '{new_name}'")
        except Exception as e:
            self.toast.error(f"Failed to duplicate: {str(e)[:30]}...")
    
    def _delete_request_from_menu(self, request_id: int):
        """Delete request from context menu."""
        request = self.db.get_request(request_id)
        if not request:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete request '{request['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_request(request_id)
                if self.current_request_id == request_id:
                    self.current_request_id = None
                    self._clear_request_editor()
                    self.center_stack.setCurrentWidget(self.no_request_empty_state)
                self._auto_sync_to_filesystem()
                self._load_collections()
                self.toast.success(f"Request '{request['name']}' deleted")
            except Exception as e:
                self.toast.error(f"Failed to delete: {str(e)[:30]}...")
    
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
        
        # Clear the row content instead of removing it (to maintain row count)
        table.setItem(row, 0, QTableWidgetItem(""))
        table.setItem(row, 1, QTableWidgetItem(""))
        
        # Mark as changed
        self._mark_as_changed()
        
        # Update tab counts
        self._update_tab_counts()
    
    def _copy_entire_response(self):
        """Copy entire response to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.response_body.toPlainText())
        self.toast.success("Response copied to clipboard")
    
    def _save_response_to_file(self):
        """Save response to file."""
        # Check if there's any response text to save
        response_text = self.response_body.toPlainText()
        if not response_text:
            self.toast.warning("No response to save")
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
                self.toast.success(f"Response saved to file")
            except Exception as e:
                self.toast.error(f"Failed to save: {str(e)[:30]}...")
    
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
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Stop any running request thread
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.wait(1000)  # Wait up to 1 second

        # Clean up resources
        self.db.close()
        self.api_client.close()
        event.accept()

