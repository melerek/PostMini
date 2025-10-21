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
        icon_font = QFont()
        icon_font.setPixelSize(80)
        icon_label.setFont(icon_font)
        layout.addWidget(icon_label)
        
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
            title="Select a request to get started",
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

