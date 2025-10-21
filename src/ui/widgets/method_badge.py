"""
HTTP Method Badge Widget

A professional badge widget for displaying HTTP methods with color coding.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MethodBadge(QLabel):
    """
    A visual badge for HTTP methods with color-coded styling.
    
    Colors:
    - GET: Green (#4CAF50)
    - POST: Blue (#2196F3)
    - PUT: Orange (#FF9800)
    - DELETE: Red (#F44336)
    - PATCH: Purple (#9C27B0)
    - HEAD: Gray (#757575)
    - OPTIONS: Gray (#757575)
    """
    
    # Method colors
    METHOD_COLORS = {
        'GET': '#4CAF50',
        'POST': '#2196F3',
        'PUT': '#FF9800',
        'DELETE': '#F44336',
        'PATCH': '#9C27B0',
        'HEAD': '#757575',
        'OPTIONS': '#757575',
    }
    
    def __init__(self, method: str = 'GET', parent=None):
        super().__init__(parent)
        self.current_method = method
        self._setup_ui()
        self.set_method(method)
    
    def _setup_ui(self):
        """Setup the widget appearance."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)
        self.setMinimumWidth(65)
        self.setMaximumWidth(75)
        
        # Set font
        font = QFont()
        font.setBold(True)
        font.setPixelSize(12)
        self.setFont(font)
    
    def set_method(self, method: str):
        """Set the HTTP method and update styling."""
        self.current_method = method.upper()
        self.setText(self.current_method)
        
        # Get color for method
        color = self.METHOD_COLORS.get(self.current_method, '#757575')
        
        # Apply badge styling with color
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: #FFFFFF;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
    
    def get_method(self) -> str:
        """Get the current method."""
        return self.current_method


class StatusBadge(QLabel):
    """
    A visual badge for HTTP status codes with color coding.
    
    Colors:
    - 2xx: Green (Success)
    - 3xx: Blue (Redirect)
    - 4xx: Orange (Client Error)
    - 5xx: Red (Server Error)
    """
    
    def __init__(self, status_code: int = 0, parent=None):
        super().__init__(parent)
        self._setup_ui()
        if status_code > 0:
            self.set_status(status_code)
    
    def _setup_ui(self):
        """Setup the widget appearance."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)
        self.setMinimumWidth(60)
        
        # Set font
        font = QFont()
        font.setBold(True)
        font.setPixelSize(12)
        self.setFont(font)
    
    def set_status(self, status_code: int):
        """Set the status code and update styling."""
        # Determine color and category based on status code
        if 200 <= status_code < 300:
            color = "#4CAF50"  # Green
            category = "OK"
            icon = "✓"
        elif 300 <= status_code < 400:
            color = "#2196F3"  # Blue
            category = "Redirect"
            icon = "↻"
        elif 400 <= status_code < 500:
            color = "#FF9800"  # Orange
            category = "Client Error"
            icon = "⚠"
        elif 500 <= status_code < 600:
            color = "#F44336"  # Red
            category = "Server Error"
            icon = "✗"
        else:
            color = "#757575"  # Gray
            category = "Unknown"
            icon = "?"
        
        self.setText(f"{icon} {status_code}")
        self.setToolTip(f"{status_code} - {category}")
        
        # Apply badge styling with color
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: #FFFFFF;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 12px;
            }}
        """)

