"""
Conflict Resolution Dialog

Dialog for helping users resolve conflicts between database and filesystem.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QGroupBox, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from typing import Dict, List


class ConflictResolutionDialog(QDialog):
    """Dialog for resolving sync conflicts."""
    
    RESOLUTION_USE_DATABASE = "use_database"
    RESOLUTION_USE_FILESYSTEM = "use_filesystem"
    RESOLUTION_MANUAL = "manual"
    
    def __init__(self, conflicts: Dict[str, List[Dict]], parent=None):
        """
        Initialize conflict resolution dialog.
        
        Args:
            conflicts: Dictionary of detected changes/conflicts
            parent: Parent widget
        """
        super().__init__(parent)
        self.conflicts = conflicts
        self.resolution_choice = self.RESOLUTION_MANUAL
        
        self.setWindowTitle("Resolve Sync Conflicts")
        self.setMinimumSize(600, 500)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("⚠️ Sync Conflict Detected")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        header_label.setFont(font)
        layout.addWidget(header_label)
        
        desc_label = QLabel(
            "Both your database and the filesystem have changes.\n"
            "Choose how to resolve this conflict:"
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Conflict summary
        summary_group = QGroupBox("Conflict Summary")
        summary_layout = QVBoxLayout()
        
        summary_text = self._build_summary_text()
        summary_display = QTextEdit()
        summary_display.setReadOnly(True)
        summary_display.setHtml(summary_text)
        summary_display.setMaximumHeight(200)
        summary_layout.addWidget(summary_display)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Resolution options
        options_group = QGroupBox("Resolution Strategy")
        options_layout = QVBoxLayout()
        
        self.button_group = QButtonGroup()
        
        # Option 1: Use database (push)
        db_radio = QRadioButton("⬆️ Use Database Version (Push to Files)")
        db_radio.setToolTip("Overwrite files with database content. Your local changes will be exported.")
        self.button_group.addButton(db_radio, 0)
        options_layout.addWidget(db_radio)
        
        db_desc = QLabel("   → Exports all database items to filesystem, overwriting files")
        db_desc.setStyleSheet("color: gray;")
        options_layout.addWidget(db_desc)
        
        # Option 2: Use filesystem (pull)
        fs_radio = QRadioButton("⬇️ Use Filesystem Version (Pull from Files)")
        fs_radio.setToolTip("Import files into database. File contents will be imported.")
        self.button_group.addButton(fs_radio, 1)
        options_layout.addWidget(fs_radio)
        
        fs_desc = QLabel("   → Imports all files into database, updating existing items")
        fs_desc.setStyleSheet("color: gray;")
        options_layout.addWidget(fs_desc)
        
        # Option 3: Manual (cancel)
        manual_radio = QRadioButton("✋ Manual Resolution")
        manual_radio.setToolTip("Close this dialog and manually sync items one by one")
        manual_radio.setChecked(True)
        self.button_group.addButton(manual_radio, 2)
        options_layout.addWidget(manual_radio)
        
        manual_desc = QLabel("   → Close dialog and use Push/Pull buttons to sync manually")
        manual_desc.setStyleSheet("color: gray;")
        options_layout.addWidget(manual_desc)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Warning
        warning_label = QLabel(
            "⚠️ <b>Warning:</b> Using 'Push' or 'Pull' will overwrite one side completely. "
            "Make sure you have a backup or commit before proceeding!"
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("background-color: #fff3cd; padding: 10px; border: 1px solid #ffc107; border-radius: 5px;")
        layout.addWidget(warning_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        resolve_button = QPushButton("Apply Resolution")
        resolve_button.clicked.connect(self._apply_resolution)
        resolve_button.setDefault(True)
        button_layout.addWidget(resolve_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _build_summary_text(self) -> str:
        """Build HTML summary of conflicts."""
        html = ""
        
        new_files = self.conflicts.get('new_files', [])
        modified_files = self.conflicts.get('modified_files', [])
        new_db_items = self.conflicts.get('new_db_items', [])
        
        if new_files:
            html += f"<b>New/Updated Files in Filesystem ({len(new_files)}):</b><br>"
            for item in new_files[:5]:  # Show max 5
                html += f"  • {item.get('name', 'Unknown')} ({item.get('type', 'unknown')})<br>"
            if len(new_files) > 5:
                html += f"  ... and {len(new_files) - 5} more<br>"
            html += "<br>"
        
        if modified_files:
            html += f"<b>Modified Files in Filesystem ({len(modified_files)}):</b><br>"
            for item in modified_files[:5]:
                html += f"  • {item.get('name', 'Unknown')} ({item.get('type', 'unknown')})<br>"
            if len(modified_files) > 5:
                html += f"  ... and {len(modified_files) - 5} more<br>"
            html += "<br>"
        
        if new_db_items:
            html += f"<b>New Items in Database ({len(new_db_items)}):</b><br>"
            for item in new_db_items[:5]:
                html += f"  • {item.get('name', 'Unknown')} ({item.get('type', 'unknown')})<br>"
            if len(new_db_items) > 5:
                html += f"  ... and {len(new_db_items) - 5} more<br>"
            html += "<br>"
        
        return html
    
    def _apply_resolution(self):
        """Apply the selected resolution strategy."""
        selected_id = self.button_group.checkedId()
        
        if selected_id == 0:
            self.resolution_choice = self.RESOLUTION_USE_DATABASE
        elif selected_id == 1:
            self.resolution_choice = self.RESOLUTION_USE_FILESYSTEM
        else:
            self.resolution_choice = self.RESOLUTION_MANUAL
        
        if self.resolution_choice == self.RESOLUTION_MANUAL:
            self.reject()
        else:
            # Confirm
            action = "export to files" if selected_id == 0 else "import from files"
            reply = QMessageBox.question(
                self,
                "Confirm Resolution",
                f"Are you sure you want to {action}?\n\n"
                "This will overwrite one side of the changes.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.accept()
            else:
                # Stay in dialog
                pass
    
    def get_resolution(self) -> str:
        """
        Get the chosen resolution strategy.
        
        Returns:
            One of RESOLUTION_USE_DATABASE, RESOLUTION_USE_FILESYSTEM, or RESOLUTION_MANUAL
        """
        return self.resolution_choice

