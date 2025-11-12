"""
Recent Requests Widget for PostMini API Client.

Displays a list of recently accessed requests with pinning support.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from datetime import datetime


class RecentRequestItem(QWidget):
    """Custom widget for recent request list items."""
    
    clicked = pyqtSignal(int)  # request_id - emit on single click
    pin_toggled = pyqtSignal(int, bool)  # request_id, is_pinned
    
    def __init__(self, request_id: int, name: str, method: str, url: str, is_pinned: bool = False):
        super().__init__()
        self.request_id = request_id
        self.is_pinned = is_pinned
        self.click_count = 0
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)  # 4-point grid
        layout.setSpacing(8)  # 4-point grid
        
        # Pin button - compact and modern
        self.pin_btn = QPushButton("📌" if is_pinned else "📍")
        self.pin_btn.setMaximumWidth(24)
        self.pin_btn.setMinimumWidth(24)
        self.pin_btn.setMaximumHeight(20)
        self.pin_btn.setStyleSheet("""
            QPushButton {
                padding: 0px;
                font-size: 12px;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
        """)
        self.pin_btn.clicked.connect(self._toggle_pin)
        self.pin_btn.setToolTip("Pin/Unpin request")
        layout.addWidget(self.pin_btn)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        # Request name - use Inter (inherits from global)
        name_label = QLabel(name)
        if self.is_pinned:
            name_label.setStyleSheet("font-weight: 600;")  # Bold for pinned
        content_layout.addWidget(name_label)
        
        # Method and URL - use JetBrains Mono for URL
        method_url_label = QLabel(f"{method} • {url[:40]}{'...' if len(url) > 40 else ''}")
        method_url_label.setStyleSheet("""
            color: #9E9E9E;
            font-family: 'JetBrains Mono', 'Fira Code', Consolas, 'Courier New', monospace;
            font-size: 11px;
        """)
        content_layout.addWidget(method_url_label)
        
        layout.addLayout(content_layout, stretch=1)
        
        self.setLayout(layout)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _toggle_pin(self):
        """Toggle pin state."""
        self.is_pinned = not self.is_pinned
        self.pin_btn.setText("📌" if self.is_pinned else "📍")
        self.pin_toggled.emit(self.request_id, self.is_pinned)
    
    def mousePressEvent(self, event):
        """Handle single click to open request."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Don't emit if clicking the pin button
            if not self.pin_btn.geometry().contains(event.pos()):
                self.clicked.emit(self.request_id)
        super().mousePressEvent(event)


class RecentRequestsWidget(QWidget):
    """Widget displaying recently accessed requests."""
    
    request_selected = pyqtSignal(int)  # request_id
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.recent_requests = []  # List of (request_id, timestamp, is_pinned)
        self.max_recent = 20  # Maximum number of recent requests to track
        
        self._init_ui()
        self._load_recent_requests()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with modern styling
        header_widget = QWidget()
        header_widget.setObjectName("recentRequestsHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 12, 12, 12)  # 4-point grid
        header_layout.setSpacing(8)  # 4-point grid
        
        # Title - use Inter from global stylesheet
        header_label = QLabel("Recent Requests")
        header_label.setObjectName("recentRequestsTitle")
        header_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()  # Push buttons to the right
        
        # Clear button with modern flat style
        clear_btn = QPushButton()
        clear_btn.setObjectName("recentRequestsClearButton")
        clear_btn.setText("Clear")
        clear_btn.setMaximumWidth(60)
        clear_btn.setMaximumHeight(28)
        clear_btn.setToolTip("Clear recent requests")
        clear_btn.clicked.connect(self._clear_recent)
        header_layout.addWidget(clear_btn)
        
        # Close button with custom SVG icon
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("recentRequestsCloseButton")
        self.close_btn.setText("✕")  # Close icon
        self.close_btn.setMaximumWidth(28)
        self.close_btn.setMaximumHeight(28)
        self.close_btn.setToolTip("Close recent requests panel")
        header_layout.addWidget(self.close_btn)
        
        layout.addWidget(header_widget)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(4)  # 4-point grid
        # No longer connect itemClicked - we handle double clicks in RecentRequestItem
        layout.addWidget(self.list_widget)
        
        self.setLayout(layout)
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
    
    def _load_recent_requests(self):
        """Load recent requests from database."""
        try:
            # Load from database
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT request_id, timestamp, is_pinned 
                FROM recent_requests 
                ORDER BY is_pinned DESC, timestamp DESC
                LIMIT ?
            """, (self.max_recent,))
            
            self.recent_requests = cursor.fetchall()
            self._refresh_list()
        except Exception:
            # Table might not exist yet, create it
            self._init_recent_requests_table()
    
    def _init_recent_requests_table(self):
        """Initialize the recent requests table if it doesn't exist."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recent_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    is_pinned INTEGER DEFAULT 0,
                    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_recent_requests_timestamp 
                ON recent_requests(timestamp DESC)
            """)
            self.db.connection.commit()
            self.recent_requests = []
        except Exception as e:
            print(f"Failed to create recent_requests table: {e}")
    
    def _refresh_list(self):
        """Refresh the list widget with current recent requests."""
        self.list_widget.clear()
        
        # Track valid requests (filter out deleted ones)
        valid_requests = []
        
        for request_id, timestamp, is_pinned in self.recent_requests:
            request = self.db.get_request(request_id)
            if not request:
                # Request was deleted, skip it
                continue
            
            valid_requests.append((request_id, timestamp, is_pinned))
            
            # Create custom item
            item_widget = RecentRequestItem(
                request_id,
                request['name'],
                request['method'],
                request['url'],
                bool(is_pinned)
            )
            item_widget.clicked.connect(self.request_selected.emit)  # Single click to open
            item_widget.pin_toggled.connect(self._toggle_pin)
            
            # Add to list
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(item_widget.sizeHint())
            # Store request_id in item data for easy retrieval
            list_item.setData(Qt.ItemDataRole.UserRole, request_id)
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, item_widget)
        
        # Clean up deleted requests from database if any were filtered out
        if len(valid_requests) < len(self.recent_requests):
            self._cleanup_deleted_requests()
    
    def _cleanup_deleted_requests(self):
        """Remove entries for requests that no longer exist in the database."""
        try:
            cursor = self.db.connection.cursor()
            # Delete recent_requests entries where the request_id doesn't exist in requests table
            cursor.execute("""
                DELETE FROM recent_requests 
                WHERE request_id NOT IN (SELECT id FROM requests)
            """)
            self.db.connection.commit()
        except Exception as e:
            print(f"Failed to cleanup deleted requests: {e}")
    
    def add_request(self, request_id: int):
        """Add a request to recent requests."""
        timestamp = datetime.now().isoformat()
        
        try:
            cursor = self.db.connection.cursor()
            # Check if already in recent requests
            cursor.execute(
                "SELECT id, is_pinned FROM recent_requests WHERE request_id = ?",
                (request_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update timestamp if not pinned
                if not existing[1]:
                    cursor.execute(
                        "UPDATE recent_requests SET timestamp = ? WHERE id = ?",
                        (timestamp, existing[0])
                    )
            else:
                # Insert new
                cursor.execute(
                    "INSERT INTO recent_requests (request_id, timestamp) VALUES (?, ?)",
                    (request_id, timestamp)
                )
                
                # Clean up excess non-pinned items
                cursor.execute("""
                    DELETE FROM recent_requests 
                    WHERE id IN (
                        SELECT id FROM recent_requests 
                        WHERE is_pinned = 0 
                        ORDER BY timestamp DESC 
                        LIMIT -1 OFFSET ?
                    )
                """, (self.max_recent,))
            
            self.db.connection.commit()
            self._load_recent_requests()
        except Exception as e:
            print(f"Failed to add recent request: {e}")
            # Try to initialize table and retry
            self._init_recent_requests_table()
    
    def _toggle_pin(self, request_id: int, is_pinned: bool):
        """Toggle pin state for a request."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "UPDATE recent_requests SET is_pinned = ? WHERE request_id = ?",
                (1 if is_pinned else 0, request_id)
            )
            self.db.connection.commit()
            self._load_recent_requests()
        except Exception as e:
            print(f"Failed to toggle pin: {e}")
    
    def _clear_recent(self):
        """Clear all non-pinned recent requests."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM recent_requests WHERE is_pinned = 0")
            self.db.connection.commit()
            self._load_recent_requests()
        except Exception as e:
            print(f"Failed to clear recent requests: {e}")
