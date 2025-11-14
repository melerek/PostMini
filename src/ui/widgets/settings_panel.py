"""
Settings Panel Widget for PostMini API Client.

Displays global application settings with persistence.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QGroupBox, QScrollArea, QPushButton, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsPanel(QWidget):
    """Widget displaying global application settings."""
    
    setting_changed = pyqtSignal(str, str)  # key, value
    check_updates_requested = pyqtSignal()  # Emitted when user clicks "Check for Updates"
    
    APP_VERSION = "1.9.2"  # Current application version
    
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
        
        # Header - unified style
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(8)
        
        # Title
        header_label = QLabel("⚙️ Settings")
        header_label.setStyleSheet("font-size: 13px; font-weight: 600; border: none;")
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
        
        # ==================== AUTO-UPDATE SETTINGS ====================
        update_group = QGroupBox("Auto-Update Settings")
        update_layout = QVBoxLayout()
        update_layout.setSpacing(12)
        
        # Auto-check for updates on startup
        self.auto_check_updates = QCheckBox("Check for updates on startup")
        self.auto_check_updates.setChecked(True)  # Default enabled
        self.auto_check_updates.stateChanged.connect(self._on_auto_check_changed)
        update_layout.addWidget(self.auto_check_updates)
        
        update_group.setLayout(update_layout)
        content_layout.addWidget(update_group)
        
        # ==================== ABOUT & VERSION INFO ====================
        about_group = QGroupBox("About PostMini")
        about_layout = QVBoxLayout()
        about_layout.setSpacing(12)
        
        # Application name and icon
        app_title = QLabel("🚀 PostMini")
        app_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        about_layout.addWidget(app_title)
        
        # Version number
        self.version_label = QLabel(f"Version {self.APP_VERSION}")
        self.version_label.setStyleSheet("color: #888; font-size: 12px;")
        about_layout.addWidget(self.version_label)
        
        # Update status label (will show if update is available)
        self.update_status_label = QLabel("")
        self.update_status_label.setStyleSheet("font-size: 11px; color: #4CAF50;")
        self.update_status_label.setWordWrap(True)
        self.update_status_label.setVisible(False)
        about_layout.addWidget(self.update_status_label)
        
        # Check for Updates button
        self.check_updates_btn = QPushButton("Check for Updates")
        self.check_updates_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
            QPushButton:disabled {
                background: #424242;
                color: #888;
            }
        """)
        self.check_updates_btn.clicked.connect(self._on_check_updates_clicked)
        about_layout.addWidget(self.check_updates_btn)
        
        # Description
        description = QLabel(
            "Professional API testing tool for developers.\n"
            "Your data is stored locally and never leaves your device."
        )
        description.setStyleSheet("color: #888; font-size: 11px; margin-top: 8px;")
        description.setWordWrap(True)
        about_layout.addWidget(description)
        
        about_group.setLayout(about_layout)
        content_layout.addWidget(about_group)
        
        # ==================== FUTURE SETTINGS SECTIONS ====================
        # Add more setting groups here as needed
        
        content_layout.addStretch()  # Push everything to the top
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        self.setMinimumWidth(200)
        self.setMaximumWidth(450)
    
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
            
            # Load auto-check updates setting
            auto_check = self.db.get_setting('auto_check_updates', 'true')
            self.auto_check_updates.blockSignals(True)
            self.auto_check_updates.setChecked(auto_check.lower() == 'true')
            self.auto_check_updates.blockSignals(False)
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
    
    def _on_auto_check_changed(self):
        """Handle auto-check updates setting change."""
        enabled = self.auto_check_updates.isChecked()
        try:
            self.db.set_setting('auto_check_updates', 'true' if enabled else 'false')
            print(f"[Settings] Auto-check updates: {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            print(f"Failed to save auto-check setting: {e}")
    
    def _on_check_updates_clicked(self):
        """Handle Check for Updates button click."""
        self.check_updates_requested.emit()
    
    def set_update_status(self, message: str, color: str = "#4CAF50"):
        """
        Set the update status message.
        
        Args:
            message: Status message to display
            color: Text color (default: green)
        """
        if message:
            self.update_status_label.setText(message)
            self.update_status_label.setStyleSheet(f"font-size: 11px; color: {color};")
            self.update_status_label.setVisible(True)
        else:
            self.update_status_label.setVisible(False)
    
    def set_checking_updates(self, checking: bool):
        """
        Enable/disable the Check for Updates button during checks.
        
        Args:
            checking: True if currently checking for updates
        """
        self.check_updates_btn.setEnabled(not checking)
        if checking:
            self.check_updates_btn.setText("Checking...")
            self.update_status_label.setText("Checking for updates...")
            self.update_status_label.setStyleSheet("font-size: 11px; color: #2196F3;")
            self.update_status_label.setVisible(True)
        else:
            self.check_updates_btn.setText("Check for Updates")
    
    def should_auto_check_updates(self) -> bool:
        """Check if auto-update check is enabled."""
        return self.auto_check_updates.isChecked()

