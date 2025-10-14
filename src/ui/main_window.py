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
    QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QKeySequence, QShortcut, QBrush, QColor
import json
from typing import Dict, Optional

from src.core.database import DatabaseManager
from src.core.api_client import ApiClient, ApiResponse
from src.ui.dialogs.environment_dialog import EnvironmentDialog
from src.features.variable_substitution import EnvironmentManager
from src.features.collection_io import CollectionExporter, CollectionImporter, get_safe_filename
from src.ui.dialogs.history_dialog import HistoryDialog
from src.ui.dialogs.code_snippet_dialog import CodeSnippetDialog
from src.ui.dialogs.oauth_dialog import OAuthConfigDialog
from src.features.oauth_manager import OAuthManager
from src.ui.widgets.test_tab_widget import TestTabWidget
from src.ui.widgets.test_results_viewer import TestResultsViewer
from src.features.test_engine import TestEngine, TestAssertion
from src.ui.dialogs.collection_test_runner import CollectionTestRunnerDialog
from src.ui.dialogs.git_sync_dialog import GitSyncDialog
from src.ui.dialogs.conflict_resolution_dialog import ConflictResolutionDialog
from src.features.git_sync_manager import GitSyncManager, GitSyncConfig, SyncStatus
from src.features.secrets_manager import SecretsManager
from datetime import datetime
import requests


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
        
        # Track current selection
        self.current_collection_id = None
        self.current_request_id = None
        self.current_request_name = None
        self.current_collection_name = None
        
        # Track unsaved changes
        self.has_unsaved_changes = False
        self.original_request_data = {}
        
        # Track active threads
        self.request_thread = None
        
        # Setup UI
        self.setWindowTitle("PostMini - Desktop API Client")
        self.setGeometry(100, 100, 1400, 900)
        
        self._init_ui()
        self._setup_shortcuts()
        self._load_collections()
        self._load_environments()
        self._init_git_sync()
    
    def _init_ui(self):
        """Initialize the user interface with all components."""
        # Create toolbar
        self._create_toolbar()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create main splitter (left pane | right pane)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ==================== LEFT PANE: Collections ====================
        left_pane = self._create_collections_pane()
        main_splitter.addWidget(left_pane)
        
        # ==================== RIGHT PANE: Request Editor & Response ====================
        self.workspace_pane = self._create_workspace_pane()
        self.workspace_pane.setVisible(False)  # Hidden by default until a request is selected
        main_splitter.addWidget(self.workspace_pane)
        
        # Set splitter sizes (30% left, 70% right)
        main_splitter.setSizes([400, 1000])
        
        main_layout.addWidget(main_splitter)
    
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
        manage_env_btn = QPushButton("Manage Environments")
        manage_env_btn.clicked.connect(self._open_environment_dialog)
        toolbar.addWidget(manage_env_btn)
        
        toolbar.addSeparator()
        
        # History button
        history_btn = QPushButton("📋 History")
        history_btn.clicked.connect(self._open_history_dialog)
        toolbar.addWidget(history_btn)
        
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
        
        toolbar.addSeparator()
        
        # Info label for showing active variables
        self.env_info_label = QLabel("No active environment variables")
        self.env_info_label.setStyleSheet("color: #666; font-style: italic;")
        toolbar.addWidget(self.env_info_label)
        
        # Add spacer to push help hint to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Help hint in top right corner
        help_hint = QLabel("💡 Press Ctrl+/ for shortcuts")
        help_hint.setStyleSheet("color: #2196F3; font-size: 12px; padding-right: 10px;")
        help_hint.setToolTip("Show keyboard shortcuts help")
        toolbar.addWidget(help_hint)
    
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
        
        # New request (Ctrl+N)
        new_request_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_request_shortcut.activated.connect(self._add_request)
        
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
        self.collections_tree.itemClicked.connect(self._on_tree_item_clicked)
        layout.addWidget(self.collections_tree)
        
        # Buttons row 1
        button_layout_1 = QHBoxLayout()
        
        add_collection_btn = QPushButton("Add Collection")
        add_collection_btn.clicked.connect(self._add_collection)
        button_layout_1.addWidget(add_collection_btn)
        
        add_request_btn = QPushButton("Add Request")
        add_request_btn.clicked.connect(self._add_request)
        button_layout_1.addWidget(add_request_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected)
        button_layout_1.addWidget(delete_btn)
        
        layout.addLayout(button_layout_1)
        
        # Buttons row 2 - Import/Export
        button_layout_2 = QHBoxLayout()
        
        export_btn = QPushButton("Export Collection")
        export_btn.clicked.connect(self._export_collection)
        button_layout_2.addWidget(export_btn)
        
        import_btn = QPushButton("Import Collection")
        import_btn.clicked.connect(self._import_collection)
        button_layout_2.addWidget(import_btn)
        
        layout.addLayout(button_layout_2)
        
        # Third button row for tests
        button_layout_3 = QHBoxLayout()
        
        run_tests_btn = QPushButton("▶️ Run Tests")
        run_tests_btn.clicked.connect(self._run_collection_tests)
        run_tests_btn.setToolTip("Run all tests in selected collection")
        button_layout_3.addWidget(run_tests_btn)
        
        layout.addLayout(button_layout_3)
        
        return pane
    
    def _create_workspace_pane(self) -> QWidget:
        """Create the right pane with request editor and response viewer."""
        pane = QWidget()
        layout = QVBoxLayout(pane)
        
        # Create vertical splitter (request editor | response viewer)
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section: Request Editor
        request_editor = self._create_request_editor()
        splitter.addWidget(request_editor)
        
        # Bottom section: Response Viewer
        response_viewer = self._create_response_viewer()
        splitter.addWidget(response_viewer)
        
        # Set splitter sizes (45% request editor, 55% response viewer)
        splitter.setStretchFactor(0, 45)  # Request editor
        splitter.setStretchFactor(1, 55)  # Response viewer - 20% more space
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter)
        
        return pane
    
    def _create_request_editor(self) -> QWidget:
        """Create the request editor section."""
        editor = QWidget()
        layout = QVBoxLayout(editor)
        
        # Dynamic request title header
        self.request_title_label = QLabel("New Request (not saved)")
        self.request_title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.request_title_label.setStyleSheet("color: #616161;")
        layout.addWidget(self.request_title_label)
        
        # Method and URL row
        url_layout = QHBoxLayout()
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
        self.method_combo.setMaximumWidth(100)
        url_layout.addWidget(self.method_combo)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter request URL")
        self.url_input.returnPressed.connect(self._send_request)  # Enter key sends request
        url_layout.addWidget(self.url_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")  # For stylesheet targeting
        self.send_btn.setProperty("class", "primary")
        self.send_btn.setMaximumWidth(80)
        self.send_btn.clicked.connect(self._send_request)
        self.send_btn.setToolTip("Send request (Ctrl+Enter)")
        url_layout.addWidget(self.send_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setMaximumWidth(80)
        self.save_btn.clicked.connect(self._save_request)
        self.save_btn.setToolTip("Save request (Ctrl+S)")
        url_layout.addWidget(self.save_btn)
        
        self.code_btn = QPushButton("💻 Code")
        self.code_btn.setMaximumWidth(80)
        self.code_btn.clicked.connect(self._generate_code)
        self.code_btn.setToolTip("Generate code snippet (Ctrl+Shift+C)")
        url_layout.addWidget(self.code_btn)
        
        layout.addLayout(url_layout)
        
        # Connect inputs to track changes
        self.method_combo.currentIndexChanged.connect(self._mark_as_changed)
        self.url_input.textChanged.connect(self._mark_as_changed)
        
        # Tabs for Params, Headers, Authorization, Body
        self.request_tabs = QTabWidget()
        self.request_tabs.setMaximumHeight(350)  # Reduced height for more response space
        
        # Params tab
        self.params_table = self._create_key_value_table()
        self.params_table.itemChanged.connect(self._update_tab_counts)
        self.request_tabs.addTab(self.params_table, "Params")
        
        # Headers tab
        self.headers_table = self._create_key_value_table()
        self.headers_table.itemChanged.connect(self._update_tab_counts)
        self.request_tabs.addTab(self.headers_table, "Headers")
        
        # Authorization tab
        auth_widget = self._create_auth_widget()
        self.request_tabs.addTab(auth_widget, "Authorization")
        
        # Body tab
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Enter request body (e.g., JSON)")
        self.body_input.textChanged.connect(self._mark_as_changed)
        body_layout.addWidget(self.body_input)
        self.request_tabs.addTab(body_widget, "Body")
        
        # Tests tab
        self.test_tab = TestTabWidget()
        self.test_tab.assertions_changed.connect(self._on_tests_changed)
        self.request_tabs.addTab(self.test_tab, "Tests")
        
        layout.addWidget(self.request_tabs)
        
        return editor
    
    def _create_response_viewer(self) -> QWidget:
        """Create the response viewer section."""
        viewer = QWidget()
        layout = QVBoxLayout(viewer)
        
        # Title
        title = QLabel("Response")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Status info row
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Status: -")
        status_layout.addWidget(self.status_label)
        
        self.time_label = QLabel("Time: -")
        status_layout.addWidget(self.time_label)
        
        self.size_label = QLabel("Size: -")
        status_layout.addWidget(self.size_label)
        
        status_layout.addStretch()
        
        # Copy response button
        self.copy_response_btn = QPushButton("📋 Copy Response")
        self.copy_response_btn.setObjectName("copyButton")  # For stylesheet targeting
        self.copy_response_btn.setProperty("class", "secondary")
        self.copy_response_btn.clicked.connect(self._copy_response)
        self.copy_response_btn.setMaximumWidth(150)
        status_layout.addWidget(self.copy_response_btn)
        
        layout.addLayout(status_layout)
        
        # Tabs for Body and Headers
        self.response_tabs = QTabWidget()
        
        # Body tab with search
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search bar for response
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Search:")
        search_layout.addWidget(search_label)
        
        self.response_search = QLineEdit()
        self.response_search.setPlaceholderText("Search in response...")
        self.response_search.textChanged.connect(self._search_response)
        self.response_search.setClearButtonEnabled(True)
        search_layout.addWidget(self.response_search)
        
        body_layout.addLayout(search_layout)
        
        # Response body text area
        self.response_body = QTextEdit()
        self.response_body.setReadOnly(True)
        body_layout.addWidget(self.response_body)
        
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
        
        layout.addWidget(self.response_tabs)
        
        # Test results viewer
        self.test_results_viewer = TestResultsViewer()
        layout.addWidget(self.test_results_viewer)
        
        return viewer
    
    def _create_key_value_table(self) -> QTableWidget:
        """Create a table widget for key-value pairs (params/headers)."""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Key', 'Value'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setRowCount(3)  # Start with 3 empty rows (reduced for better space)
        # Remove max height constraint so table anchors to parent panel properly
        return table
    
    def _create_auth_widget(self) -> QWidget:
        """Create the authorization configuration widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Auth type dropdown
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
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
        token_layout.addWidget(QLabel("Token:"))
        self.auth_token_input = QLineEdit()
        self.auth_token_input.setPlaceholderText("Enter bearer token or use {{variable}}")
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
        self.oauth_status_label.setStyleSheet("color: #999; font-style: italic;")
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
        
        layout.addStretch()
        
        # OAuth state
        self.current_oauth_config = None
        self.current_oauth_token = None
        
        return widget
    
    def _on_auth_type_changed(self, auth_type: str):
        """Handle authorization type change."""
        self.bearer_token_widget.setVisible(auth_type == 'Bearer Token')
        self.oauth_widget.setVisible(auth_type == 'OAuth 2.0')
    
    # ==================== Collections Tree Management ====================
    
    def _load_collections(self):
        """Load all collections and requests from database into the tree."""
        # Store currently expanded collection IDs before clearing
        expanded_ids = set()
        for i in range(self.collections_tree.topLevelItemCount()):
            item = self.collections_tree.topLevelItem(i)
            if item.isExpanded():
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data and isinstance(data, dict):
                    expanded_ids.add(data.get('id'))
        
        self.collections_tree.clear()
        collections = self.db.get_all_collections()
        
        for collection in collections:
            # Load requests for this collection
            requests = self.db.get_requests_by_collection(collection['id'])
            request_count = len(requests)
            
            # Create collection item with request count
            collection_name = f"{collection['name']} [{request_count}]"
            collection_item = QTreeWidgetItem([collection_name])
            collection_item.setData(0, Qt.ItemDataRole.UserRole, 
                                   {'type': 'collection', 'id': collection['id'], 'name': collection['name']})
            self.collections_tree.addTopLevelItem(collection_item)
            
            # Add request items
            for request in requests:
                request_item = QTreeWidgetItem([f"{request['method']} - {request['name']}"])
                request_item.setData(0, Qt.ItemDataRole.UserRole,
                                    {'type': 'request', 'id': request['id'],
                                     'collection_id': collection['id']})
                collection_item.addChild(request_item)
            
            # Restore expanded state
            if collection['id'] in expanded_ids:
                collection_item.setExpanded(True)
    
    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle click on tree item (collection or request)."""
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Check if data exists and is a dictionary
        if not data or not isinstance(data, dict):
            return
        
        # Check for unsaved changes before switching
        if not self._check_unsaved_changes():
            return
        
        if data.get('type') == 'collection':
            self.current_collection_id = data['id']
            self.current_request_id = None
            self._clear_request_editor()
            self.workspace_pane.setVisible(False)  # Hide workspace when collection clicked
            
            # Toggle expansion when clicking anywhere on collection item
            item.setExpanded(not item.isExpanded())
        elif data.get('type') == 'request':
            self.current_collection_id = data['collection_id']
            self.current_request_id = data['id']
            self.workspace_pane.setVisible(True)  # Show workspace when request clicked
            self._load_request(data['id'])
    
    def _add_collection(self):
        """Add a new collection via dialog."""
        name, ok = QInputDialog.getText(self, "New Collection", "Collection name:")
        if ok and name:
            try:
                self.db.create_collection(name)
                self._auto_sync_to_filesystem()
                self._load_collections()
            except Exception as e:
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
        if ok and name:
            try:
                request_id = self.db.create_request(
                    collection_id=self.current_collection_id,
                    name=name,
                    method='GET',
                    url='https://api.example.com'
                )
                self._load_collections()
                
                # Load the newly created request and show workspace
                self.current_request_id = request_id
                self.workspace_pane.setVisible(True)
                self._load_request(request_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create request: {str(e)}")
    
    def _delete_selected(self):
        """Delete the currently selected collection or request."""
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
                if data['type'] == 'collection':
                    self.db.delete_collection(data['id'])
                    self.current_collection_id = None
                    self.current_request_id = None
                    self._clear_request_editor()
                    self.workspace_pane.setVisible(False)
                elif data['type'] == 'request':
                    self.db.delete_request(data['id'])
                    if self.current_request_id == data['id']:
                        self.current_request_id = None
                        self._clear_request_editor()
                        self.workspace_pane.setVisible(False)
                
                # Auto-sync to filesystem if Git sync is enabled
                self._auto_sync_to_filesystem()
                
                self._load_collections()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")
    
    # ==================== Request Editor Management ====================
    
    def _load_request(self, request_id: int):
        """Load a request's details into the editor."""
        try:
            request = self.db.get_request(request_id)
            if not request:
                QMessageBox.warning(self, "Warning", "Request not found!")
                return
            
            # Store request name and collection name for title
            self.current_request_name = request.get('name', 'Unnamed Request')
            collection = self.db.get_collection(request.get('collection_id'))
            self.current_collection_name = collection.get('name', 'Unknown Collection') if collection else 'Unknown Collection'
            
            # Load basic info
            self.method_combo.setCurrentText(request.get('method', 'GET'))
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
            
            # Load test assertions
            self._load_test_assertions(request_id)
            
            # Clear test results
            self.test_results_viewer.clear()
            
            # Store original data for change detection
            self._store_original_request_data()
            
            # Reset unsaved changes flag and update title
            self.has_unsaved_changes = False
            self._update_request_title()
            
            # Update tab counts
            self._update_tab_counts()
            
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
        self._clear_response_viewer()
        
        # Reset tracking variables
        self.current_request_id = None
        self.current_request_name = None
        self.current_collection_name = None
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
            'auth_token': self.auth_token_input.text()
        }
    
    def _mark_as_changed(self):
        """Mark the request as having unsaved changes."""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self._update_request_title()
    
    def _update_tab_counts(self):
        """Update tab labels to show item counts in square brackets."""
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
        
        # Update tab labels
        params_label = f"Params [{params_count}]" if params_count > 0 else "Params"
        headers_label = f"Headers [{headers_count}]" if headers_count > 0 else "Headers"
        
        self.request_tabs.setTabText(0, params_label)
        self.request_tabs.setTabText(1, headers_label)
    
    def _update_request_title(self):
        """Update the request title label to show current state."""
        if self.current_request_id and self.current_request_name:
            # Saved request
            title = f"{self.current_request_name} ({self.current_collection_name})"
            if self.has_unsaved_changes:
                title += " *"
            self.request_title_label.setText(title)
            self.request_title_label.setStyleSheet("color: #212121;")
        else:
            # New unsaved request
            self.request_title_label.setText("New Request (not saved)")
            self.request_title_label.setStyleSheet("color: #616161;")
    
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
                auth_token=self.auth_token_input.text()
            )
            
            # Save test assertions
            self._save_test_assertions()
            
            # Reset unsaved changes flag
            self._store_original_request_data()
            self.has_unsaved_changes = False
            self._update_request_title()
            
            # Auto-sync to filesystem if Git sync is enabled
            self._auto_sync_to_filesystem()
            
            self._load_collections()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save request: {str(e)}")
    
    # ==================== Request Execution ====================
    
    def _send_request(self):
        """Execute the HTTP request and display the response."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a URL!")
            return
        
        # Show loading state with visual feedback
        self.send_btn.setEnabled(False)
        self.send_btn.setText("⏳ Sending...")
        # Override with loading state color
        self.send_btn.setStyleSheet("""
            QPushButton#sendButton {
                background-color: #FF9800;
                color: white;
            }
        """)
        
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
        
        # Apply environment variable substitution if environment is active
        if self.env_manager.has_active_environment():
            substituted, unresolved = self.env_manager.substitute_in_request(
                url, params, headers, body, auth_token
            )
            
            # Warn about unresolved variables
            if unresolved:
                reply = QMessageBox.question(
                    self, "Unresolved Variables",
                    f"The following variables are not defined in the current environment:\n"
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
        
        # Clean up existing thread if still running
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.wait()
        
        # Create and start request thread
        self.request_thread = RequestThread(
            self.api_client, method, url, params, headers, body, auth_type, auth_token
        )
        self.request_thread.finished.connect(self._on_request_finished)
        self.request_thread.error.connect(self._on_request_error)
        self.request_thread.start()
    
    def _on_request_finished(self, response: ApiResponse):
        """Handle successful request completion."""
        # Re-enable send button and clear inline styles (use global stylesheet)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("✓ Send")
        self.send_btn.setStyleSheet("")  # Reset to use global stylesheet
        
        # Display response
        self._display_response(response)
        
        # Execute tests
        self._execute_tests_on_response(response)
        
        # Save to history
        self._save_to_history(response=response)
    
    def _on_request_error(self, error_message: str):
        """Handle request error."""
        # Re-enable send button and clear inline styles (use global stylesheet)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")
        self.send_btn.setStyleSheet("")  # Reset to use global stylesheet
        
        # Show error message
        QMessageBox.critical(self, "Request Failed", error_message)
        
        # Display error in response viewer
        self.status_label.setText(f"Status: Error")
        self.response_body.setPlainText(f"Error: {error_message}")
        
        # Save to history (with error)
        self._save_to_history(error_message=error_message)
    
    def _display_response(self, response: ApiResponse):
        """Display the HTTP response in the response viewer."""
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
        
        # Display status info with color
        self.status_label.setText(f"{icon} Status: {status_code} ({status_text})")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")
        
        self.time_label.setText(f"Time: {response.elapsed_time:.2f}s")
        self.time_label.setStyleSheet("font-weight: bold;")
        
        self.size_label.setText(f"Size: {response.size} bytes")
        self.size_label.setStyleSheet("font-weight: bold;")
        
        # Display response body
        try:
            # Try to parse and pretty-print JSON
            json_data = json.loads(response.text)
            pretty_json = json.dumps(json_data, indent=2)
            self.response_body.setPlainText(pretty_json)
        except (json.JSONDecodeError, ValueError):
            # Display as plain text if not JSON
            self.response_body.setPlainText(response.text)
        
        # Display response headers
        self.response_headers_table.setRowCount(len(response.headers))
        for i, (key, value) in enumerate(response.headers.items()):
            self.response_headers_table.setItem(i, 0, QTableWidgetItem(key))
            self.response_headers_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def _clear_response_viewer(self):
        """Clear the response viewer."""
        self.status_label.setText("Status: -")
        self.time_label.setText("Time: -")
        self.size_label.setText("Size: -")
        self.response_body.clear()
        self.response_headers_table.clearContents()
        self.response_headers_table.setRowCount(0)
    
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
            self.env_info_label.setText("No active environment variables")
        else:
            # Load environment
            env = self.db.get_environment(env_id)
            if env:
                self.env_manager.set_active_environment(env)
                var_count = len(env.get('variables', {}))
                self.env_info_label.setText(
                    f"Active: {env['name']} ({var_count} variable{'s' if var_count != 1 else ''})"
                )
    
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
                QMessageBox.information(
                    self, "Success",
                    f"Collection '{collection['name']}' exported successfully!\n\nFormat: {format_name}\nFile: {file_path}"
                )
            else:
                QMessageBox.critical(self, "Error", "Failed to export collection!")
                
        except Exception as e:
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
                
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Import Failed", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
    
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
    
    def _show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog."""
        help_text = """
<h2>Keyboard Shortcuts</h2>

<h3>Request Operations:</h3>
<table cellpadding="5">
<tr><td><b>Ctrl+Enter</b></td><td>Send request</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Save request</td></tr>
<tr><td><b>Ctrl+N</b></td><td>Create new request</td></tr>
<tr><td><b>Delete</b></td><td>Delete selected item</td></tr>
</table>

<h3>Navigation:</h3>
<table cellpadding="5">
<tr><td><b>Ctrl+L</b></td><td>Focus URL bar</td></tr>
</table>

<h3>Tools:</h3>
<table cellpadding="5">
<tr><td><b>Ctrl+Shift+C</b></td><td>Generate code snippet</td></tr>
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
            # Load request data into UI
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
            
            # Show success message
            QMessageBox.information(
                self, "Request Loaded",
                f"Request loaded from history:\n{history_entry['method']} {history_entry['url']}\n\n"
                "Click 'Send' to execute it."
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
        # Tests will be saved when request is saved
        pass
    
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
    
    def _open_git_sync_dialog(self):
        """Open the Git sync configuration dialog."""
        dialog = GitSyncDialog(self.db, self)
        
        # Connect signals
        dialog.sync_enabled.connect(self._on_git_sync_enabled)
        dialog.sync_disabled.connect(self._on_git_sync_disabled)
        dialog.sync_performed.connect(self._on_sync_performed)
        
        dialog.exec()
    
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
        
        # Update label and button style
        if status.status == SyncStatus.STATUS_SYNCED:
            self.git_sync_status_label.setText("Files: ✅ Synced")
            self.git_sync_status_label.setStyleSheet("color: #4CAF50; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Database and .postmini/ files are in sync")
            self.git_sync_btn.setStyleSheet("")
        elif status.status == SyncStatus.STATUS_NEEDS_PULL:
            self.git_sync_status_label.setText("Files: 📥 Import Available")
            self.git_sync_status_label.setStyleSheet("color: #2196F3; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Files in .postmini/ have changes - click to import")
            self.git_sync_btn.setStyleSheet("background-color: #E3F2FD;")
        elif status.status == SyncStatus.STATUS_NEEDS_PUSH:
            self.git_sync_status_label.setText("Files: 📤 Export Needed")
            self.git_sync_status_label.setStyleSheet("color: #FF9800; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Database has unsaved changes - click to export")
            self.git_sync_btn.setStyleSheet("background-color: #FFF3E0;")
        elif status.status == SyncStatus.STATUS_CONFLICT:
            self.git_sync_status_label.setText("Files: ⚠️ Conflict")
            self.git_sync_status_label.setStyleSheet("color: #F44336; font-size: 11px; padding: 0 10px;")
            self.git_sync_status_label.setToolTip("Both database and files have changes")
            self.git_sync_btn.setStyleSheet("background-color: #FFEBEE;")
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
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Stop any running request thread
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.wait(1000)  # Wait up to 1 second
        
        # Clean up resources
        self.db.close()
        self.api_client.close()
        event.accept()

