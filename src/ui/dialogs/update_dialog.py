"""
Dialogs for auto-update functionality
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl


class UpdateAvailableDialog(QDialog):
    """Dialog showing update information."""
    
    def __init__(self, update_info: dict, current_version: str, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title = QLabel(
            f"<h2>🎉 PostMini {self.update_info['latest_version']} is available!</h2>"
        )
        layout.addWidget(title)
        
        # Current version
        current_label = QLabel(
            f"<p>You're currently running version <b>{self.current_version}</b></p>"
        )
        current_label.setStyleSheet("color: #888;")
        layout.addWidget(current_label)
        
        # Release info
        release_date = self.update_info.get('release_date', 'Unknown')
        info_label = QLabel(f"<p>Released: {release_date}</p>")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info_label)
        
        # Release notes
        notes_label = QLabel("<b>What's new:</b>")
        layout.addWidget(notes_label)
        
        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setMaximumHeight(150)
        
        # Format release notes
        notes_content = "\n".join(
            f"• {note}" for note in self.update_info.get('release_notes', [])
        )
        if not notes_content:
            notes_content = "See full release notes for details."
        
        notes_text.setPlainText(notes_content)
        layout.addWidget(notes_text)
        
        # Critical update warning
        if self.update_info.get('critical', False):
            warning = QLabel(
                "⚠️ <b>This is a critical update with important security fixes.</b>"
            )
            warning.setStyleSheet("color: #FF9800; background: rgba(255, 152, 0, 0.1); padding: 8px; border-radius: 4px;")
            warning.setWordWrap(True)
            layout.addWidget(warning)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        release_notes_btn = QPushButton("View Full Release Notes")
        release_notes_btn.clicked.connect(self._open_release_notes)
        release_notes_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #2196F3;
                color: #2196F3;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(33, 150, 243, 0.1);
            }
        """)
        button_layout.addWidget(release_notes_btn)
        
        button_layout.addStretch()
        
        skip_btn = QPushButton("Remind Me Later")
        skip_btn.clicked.connect(self.reject)
        skip_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888;
                padding: 8px 16px;
            }
            QPushButton:hover {
                color: #fff;
            }
        """)
        button_layout.addWidget(skip_btn)
        
        install_btn = QPushButton("Download & Install")
        install_btn.setDefault(True)
        install_btn.clicked.connect(self.accept)
        install_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #45A049;
            }
            QPushButton:pressed {
                background: #3D8B40;
            }
        """)
        button_layout.addWidget(install_btn)
        
        layout.addLayout(button_layout)
    
    def _open_release_notes(self):
        """Open release notes in browser."""
        changelog_url = self.update_info.get('changelog_url', '')
        if changelog_url:
            QDesktopServices.openUrl(QUrl(changelog_url))


class UpdateProgressDialog(QDialog):
    """Dialog showing download progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Downloading Update")
        self.setMinimumWidth(450)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Icon and title
        title = QLabel("📥 Downloading update...")
        title.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                height: 24px;
            }
            QProgressBar::chunk {
                background: #2196F3;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Starting download...")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #666;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)
    
    def update_progress(self, downloaded: int, total: int):
        """Update progress bar."""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(downloaded)
            
            # Show MB downloaded
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            percentage = (downloaded / total) * 100
            
            self.status_label.setText(
                f"Downloaded {downloaded_mb:.1f} MB of {total_mb:.1f} MB ({percentage:.0f}%)"
            )
            self.progress_bar.setFormat(f"{percentage:.0f}%")


class NoUpdateDialog(QDialog):
    """Dialog shown when no update is available."""
    
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("No Updates Available")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Icon and message
        icon_label = QLabel("✅")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        message = QLabel(
            f"<h3>You're up to date!</h3>"
            f"<p>PostMini {self.current_version} is the latest version.</p>"
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

