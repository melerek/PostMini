"""
Settings Panel Widget for PostMini API Client.

Displays global application settings with persistence.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsPanel(QWidget):
    """Widget displaying global application settings."""
    
    setting_changed = pyqtSignal(str, str)  # key, value
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header_widget = QWidget()
        header_widget.setObjectName("settingsPanelHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(8)
        
        # Title
        header_label = QLabel("Settings")
        header_label.setObjectName("settingsPanelTitle")
        header_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        main_layout.addWidget(header_widget)
        
        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(16)
        
        # ==================== REQUEST SETTINGS ====================
        request_group = QGroupBox("Request Settings")
        request_layout = QVBoxLayout()
        request_layout.setSpacing(12)
        
        # Default Protocol
        protocol_row = QHBoxLayout()
        protocol_label = QLabel("Default Protocol:")
        protocol_label.setToolTip("Protocol to use when URL doesn't specify one")
        protocol_row.addWidget(protocol_label)
        
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItem("https://", "https")
        self.protocol_combo.addItem("http://", "http")
        self.protocol_combo.setCurrentIndex(0)  # Default to https
        self.protocol_combo.currentIndexChanged.connect(self._on_protocol_changed)
        protocol_row.addWidget(self.protocol_combo)
        
        protocol_row.addStretch()
        request_layout.addLayout(protocol_row)
        
        request_group.setLayout(request_layout)
        content_layout.addWidget(request_group)
        
        # ==================== FUTURE SETTINGS SECTIONS ====================
        # Add more setting groups here as needed
        
        content_layout.addStretch()  # Push everything to the top
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
    
    def _load_settings(self):
        """Load settings from database."""
        try:
            # Load default protocol
            default_protocol = self.db.get_setting('default_protocol', 'https')
            index = self.protocol_combo.findData(default_protocol)
            if index >= 0:
                self.protocol_combo.blockSignals(True)
                self.protocol_combo.setCurrentIndex(index)
                self.protocol_combo.blockSignals(False)
        except Exception as e:
            print(f"Failed to load settings: {e}")
    
    def _on_protocol_changed(self):
        """Handle protocol setting change."""
        protocol = self.protocol_combo.currentData()
        try:
            self.db.set_setting('default_protocol', protocol)
            self.setting_changed.emit('default_protocol', protocol)
            print(f"[Settings] Default protocol changed to: {protocol}")
        except Exception as e:
            print(f"Failed to save protocol setting: {e}")
    
    def get_default_protocol(self) -> str:
        """Get the currently selected default protocol."""
        return self.protocol_combo.currentData()

