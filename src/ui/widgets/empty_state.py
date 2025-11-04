"""
Empty State Widget

Professional empty state displays with illustrations and helpful messages.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class EmptyStateWidget(QWidget):
    """
    A professional empty state widget with icon, title, and description.
    """
    
    def __init__(self, 
                 icon: str = "📭", 
                 title: str = "No data", 
                 description: str = "", 
                 parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title_text = title
        self.description_text = description
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the empty state UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon/Illustration (large emoji)
        icon_label = QLabel(self.icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Set large font - 3x smaller than before (300/3 = 100)
        icon_label.setMinimumSize(133, 133)  # 400/3 ≈ 133
        icon_font = QFont()
        icon_font.setPointSize(100)  # Reduced from 300 to 100 (3x smaller)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet("font-size: 100pt;")  # Also set via stylesheet as backup
        layout.addWidget(icon_label)
        print(f"[DEBUG] Empty state icon created with font size 100pt, min size 133x133")
        
        # Add spacing
        layout.addSpacing(20)
        
        # Title
        title_label = QLabel(self.title_text)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPixelSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #757575;")
        layout.addWidget(title_label)
        
        # Add spacing
        layout.addSpacing(8)
        
        # Description
        if self.description_text:
            desc_label = QLabel(self.description_text)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setWordWrap(True)
            desc_label.setMaximumWidth(400)
            desc_font = QFont()
            desc_font.setPixelSize(13)
            desc_label.setFont(desc_font)
            desc_label.setStyleSheet("color: #9E9E9E;")
            layout.addWidget(desc_label)


class NoRequestEmptyState(EmptyStateWidget):
    """Empty state for when no request is selected."""
    
    def __init__(self, parent=None):
        super().__init__(
            icon="🚀",
            title="Select or add a request to get started",
            description="Choose a request from the collections panel on the left, or create a new one to begin testing your API.",
            parent=parent
        )


class NoResponseEmptyState(EmptyStateWidget):
    """Empty state for when no response has been received yet."""
    
    def __init__(self, parent=None):
        super().__init__(
            icon="🧑‍🚀",
            title="Enter the URL and click Send to get a response",
            description="Configure your request using the tabs above, then click the Send button to execute it and see the results here.",
            parent=parent
        )


class NoCollectionsEmptyState(EmptyStateWidget):
    """Empty state for when there are no collections."""
    
    def __init__(self, parent=None):
        super().__init__(
            icon="📚",
            title="No collections yet",
            description="Create your first collection to organize your API requests. Click the 'Add Collection' button to get started.",
            parent=parent
        )

