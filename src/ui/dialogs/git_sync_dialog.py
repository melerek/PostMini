"""
Git Sync Dialog

Dialog for managing Git-based collaboration settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QCheckBox, QGroupBox, QTextEdit, QFileDialog,
    QMessageBox, QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.core.database import DatabaseManager
from src.features.git_sync_manager import GitSyncManager, GitSyncConfig, SyncStatus
from src.features.secrets_manager import SecretsManager


class GitSyncDialog(QDialog):
    """Dialog for Git sync configuration and management."""
    
    sync_enabled = pyqtSignal(str)  # Emits project_path when sync is enabled
    sync_disabled = pyqtSignal()
    sync_performed = pyqtSignal(str)  # Emits status message
    
    def __init__(self, db: DatabaseManager, parent=None):
        """
        Initialize Git sync dialog.
        
        Args:
            db: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.db = db
        self.git_sync_manager = None
        self.secrets_manager = None
        self.current_workspace = None
        
        self.setWindowTitle("Git Sync Settings")
        self.setMinimumSize(700, 500)
        
        self._init_ui()
        self._load_current_workspace()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_setup_tab(), "Setup")
        tabs.addTab(self._create_status_tab(), "Status")
        tabs.addTab(self._create_workspaces_tab(), "Workspaces")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_setup_tab(self) -> QWidget:
        """Create the setup tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Current status
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Git sync is not enabled")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # Project path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Project Directory:"))
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select project directory...")
        path_layout.addWidget(self.path_input)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_directory)
        path_layout.addWidget(browse_button)
        
        config_layout.addLayout(path_layout)
        
        # Auto-sync options
        self.auto_sync_checkbox = QCheckBox("Enable auto-sync (sync on save)")
        self.auto_sync_checkbox.setChecked(True)
        config_layout.addWidget(self.auto_sync_checkbox)
        
        self.create_gitignore_checkbox = QCheckBox("Add .postmini-secrets/ to .gitignore")
        self.create_gitignore_checkbox.setChecked(True)
        config_layout.addWidget(self.create_gitignore_checkbox)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Actions
        action_layout = QHBoxLayout()
        
        self.enable_button = QPushButton("🚀 Enable Git Sync")
        self.enable_button.clicked.connect(self._enable_git_sync)
        action_layout.addWidget(self.enable_button)
        
        self.disable_button = QPushButton("❌ Disable Git Sync")
        self.disable_button.clicked.connect(self._disable_git_sync)
        self.disable_button.setEnabled(False)
        action_layout.addWidget(self.disable_button)
        
        layout.addLayout(action_layout)
        
        # Important info box
        important_info = QLabel(
            "<b>📘 How File Sync Works:</b><br><br>"
            "<b>1. PostMini → Files:</b> When you save, PostMini exports to <code>.postmini/</code> folder<br>"
            "<b>2. Files → Git:</b> <span style='color: #F44336;'><b>YOU manually run Git commands</b></span> to commit/push<br>"
            "<b>3. Git → Files:</b> Teammates run <code>git pull</code> to get your files<br>"
            "<b>4. Files → PostMini:</b> They click 'Import' to load into PostMini<br><br>"
            "<b>⚠️ PostMini does NOT run Git commands automatically!</b><br>"
            "It only syncs between database and <code>.postmini/</code> files."
        )
        important_info.setWordWrap(True)
        important_info.setStyleSheet("""
            background-color: #E3F2FD; 
            padding: 15px; 
            border: 2px solid #2196F3; 
            border-radius: 5px;
            color: #0D47A1;
        """)
        layout.addWidget(important_info)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def _create_status_tab(self) -> QWidget:
        """Create the status tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Sync status display
        status_group = QGroupBox("Sync Status")
        status_layout = QVBoxLayout()
        
        self.sync_status_label = QLabel("No workspace active")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.sync_status_label.setFont(font)
        status_layout.addWidget(self.sync_status_label)
        
        self.sync_message_label = QLabel("")
        self.sync_message_label.setWordWrap(True)
        status_layout.addWidget(self.sync_message_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Changes detected
        changes_group = QGroupBox("Detected Changes")
        changes_layout = QVBoxLayout()
        
        self.changes_text = QTextEdit()
        self.changes_text.setReadOnly(True)
        self.changes_text.setMaximumHeight(150)
        changes_layout.addWidget(self.changes_text)
        
        changes_group.setLayout(changes_layout)
        layout.addWidget(changes_group)
        
        # Sync actions
        action_layout = QHBoxLayout()
        
        self.sync_to_fs_button = QPushButton("📤 Export to Files")
        self.sync_to_fs_button.setToolTip("Export database to .postmini/ folder (you still need to 'git commit' afterward)")
        self.sync_to_fs_button.clicked.connect(self._sync_to_filesystem)
        self.sync_to_fs_button.setEnabled(False)
        action_layout.addWidget(self.sync_to_fs_button)
        
        self.sync_from_fs_button = QPushButton("📥 Import from Files")
        self.sync_from_fs_button.setToolTip("Import from .postmini/ folder (run 'git pull' first to get latest changes)")
        self.sync_from_fs_button.clicked.connect(self._sync_from_filesystem)
        self.sync_from_fs_button.setEnabled(False)
        action_layout.addWidget(self.sync_from_fs_button)
        
        self.refresh_status_button = QPushButton("🔄 Refresh Status")
        self.refresh_status_button.clicked.connect(self._refresh_status)
        action_layout.addWidget(self.refresh_status_button)
        
        self.show_git_commands_button = QPushButton("📋 Show Git Commands")
        self.show_git_commands_button.clicked.connect(self._show_git_commands)
        action_layout.addWidget(self.show_git_commands_button)
        
        layout.addLayout(action_layout)
        
        # Git instructions
        git_info = QLabel(
            "<b>⚠️ Important:</b> PostMini syncs to <b>.postmini/</b> folder.<br>"
            "<b>You must use Git commands to commit changes:</b><br>"
            "• After Export: Run <code>git add .postmini/ && git commit -m 'Update collections' && git push</code><br>"
            "• Before Import: Run <code>git pull</code> to get latest changes from teammates<br>"
            "• Click <b>Show Git Commands</b> button for copy-paste ready commands"
        )
        git_info.setWordWrap(True)
        git_info.setStyleSheet("""
            background-color: #FFF3E0; 
            padding: 12px; 
            border: 1px solid #FF9800; 
            border-radius: 5px;
            color: #E65100;
        """)
        layout.addWidget(git_info)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def _create_workspaces_tab(self) -> QWidget:
        """Create the workspaces management tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("Manage all Git-synced workspaces:")
        layout.addWidget(label)
        
        # Workspaces table
        self.workspaces_table = QTableWidget()
        self.workspaces_table.setColumnCount(4)
        self.workspaces_table.setHorizontalHeaderLabels(["Project Path", "Status", "Last Sync", "Auto-Sync"])
        
        header = self.workspaces_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.workspaces_table)
        
        # Actions
        action_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 Refresh List")
        refresh_button.clicked.connect(self._refresh_workspaces_list)
        action_layout.addWidget(refresh_button)
        
        action_layout.addStretch()
        
        remove_button = QPushButton("🗑️ Remove Selected")
        remove_button.clicked.connect(self._remove_workspace)
        action_layout.addWidget(remove_button)
        
        layout.addLayout(action_layout)
        
        widget.setLayout(layout)
        return widget
    
    def _load_current_workspace(self):
        """Load currently active workspace if any."""
        workspaces = self.db.get_all_git_workspaces()
        
        if workspaces:
            # Get the most recently updated enabled workspace
            active = next((w for w in workspaces if w['enabled']), None)
            
            if active:
                self.current_workspace = active
                self._setup_managers(active['project_path'])
                self._update_ui_for_active_workspace()
    
    def _setup_managers(self, project_path: str):
        """Setup Git sync and secrets managers for a project path."""
        config = GitSyncConfig(project_path)
        self.git_sync_manager = GitSyncManager(self.db, config)
        self.secrets_manager = SecretsManager(str(config.secrets_path))
    
    def _update_ui_for_active_workspace(self):
        """Update UI when a workspace is active."""
        if self.current_workspace:
            path = self.current_workspace['project_path']
            self.status_label.setText(f"✅ Git sync enabled for: {path}")
            self.path_input.setText(path)
            self.path_input.setEnabled(False)
            self.enable_button.setEnabled(False)
            self.disable_button.setEnabled(True)
            self.sync_to_fs_button.setEnabled(True)
            self.sync_from_fs_button.setEnabled(True)
            
            # Update auto-sync checkbox
            self.auto_sync_checkbox.setChecked(self.current_workspace.get('auto_sync', True))
            
            # Refresh status
            self._refresh_status()
    
    def _browse_directory(self):
        """Browse for project directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Project Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.path_input.setText(directory)
    
    def _enable_git_sync(self):
        """Enable Git sync for the selected project."""
        project_path = self.path_input.text().strip()
        
        if not project_path:
            QMessageBox.warning(self, "No Path", "Please select a project directory.")
            return
        
        # Check if already enabled
        existing = self.db.get_git_workspace_by_path(project_path)
        if existing:
            QMessageBox.information(self, "Already Enabled", "Git sync is already enabled for this project.")
            return
        
        # Setup managers
        self._setup_managers(project_path)
        
        # Check if workspace exists
        found, workspace_info = self.git_sync_manager.detect_workspace()
        
        if found:
            # Ask user if they want to import existing workspace
            reply = QMessageBox.question(
                self,
                "Workspace Detected",
                f"Found existing .postmini/ workspace with:\n"
                f"• {workspace_info['num_collections']} collections\n"
                f"• {workspace_info['num_environments']} environments\n\n"
                f"Import these into PostMini?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Import from filesystem
                success, message = self.git_sync_manager.sync_from_filesystem(update_existing=True)
                if not success:
                    QMessageBox.warning(self, "Import Failed", message)
                    return
        else:
            # Initialize new workspace
            create_gitignore = self.create_gitignore_checkbox.isChecked()
            success, message = self.git_sync_manager.initialize_workspace(create_gitignore)
            
            if not success:
                QMessageBox.warning(self, "Initialization Failed", message)
                return
            
            # Export current database to filesystem
            success, message = self.git_sync_manager.sync_to_filesystem()
            if not success:
                QMessageBox.warning(self, "Export Failed", message)
                return
        
        # Save to database
        auto_sync = self.auto_sync_checkbox.isChecked()
        workspace_id = self.db.create_git_workspace(
            project_path=project_path,
            workspace_name=None,
            enabled=True,
            auto_sync=auto_sync
        )
        
        # Update current workspace
        self.current_workspace = self.db.get_git_workspace_by_path(project_path)
        self._update_ui_for_active_workspace()
        
        # Emit signal
        self.sync_enabled.emit(project_path)
        
        QMessageBox.information(
            self,
            "Git Sync Enabled",
            f"Git sync enabled successfully!\n\n"
            f"Collections are now synced to:\n{project_path}/.postmini/\n\n"
            f"Don't forget to commit these files to Git!"
        )
    
    def _disable_git_sync(self):
        """Disable Git sync."""
        if not self.current_workspace:
            return
        
        reply = QMessageBox.question(
            self,
            "Disable Git Sync",
            "Are you sure you want to disable Git sync?\n\n"
            "Files in .postmini/ will remain, but auto-sync will stop.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_git_workspace(self.current_workspace['id'])
            self.current_workspace = None
            self.git_sync_manager = None
            self.secrets_manager = None
            
            # Reset UI
            self.status_label.setText("Git sync is not enabled")
            self.path_input.setText("")
            self.path_input.setEnabled(True)
            self.enable_button.setEnabled(True)
            self.disable_button.setEnabled(False)
            self.sync_to_fs_button.setEnabled(False)
            self.sync_from_fs_button.setEnabled(False)
            
            # Clear status
            self.sync_status_label.setText("No workspace active")
            self.sync_message_label.setText("")
            self.changes_text.clear()
            
            # Emit signal
            self.sync_disabled.emit()
            
            QMessageBox.information(self, "Disabled", "Git sync has been disabled.")
    
    def _refresh_status(self):
        """Refresh sync status display."""
        if not self.git_sync_manager:
            return
        
        status = self.git_sync_manager.get_sync_status()
        
        # Update status label with color
        status_text = {
            SyncStatus.STATUS_SYNCED: "✅ Synced",
            SyncStatus.STATUS_NEEDS_PULL: "⬇️ Changes in Files",
            SyncStatus.STATUS_NEEDS_PUSH: "⬆️ Changes in Database",
            SyncStatus.STATUS_CONFLICT: "⚠️ Conflict",
            SyncStatus.STATUS_ERROR: "❌ Error",
            SyncStatus.STATUS_DISABLED: "Disabled"
        }.get(status.status, "Unknown")
        
        self.sync_status_label.setText(status_text)
        self.sync_message_label.setText(status.message)
        
        # Display changes
        changes = status.changes
        changes_html = "<b>Changes detected:</b><br><br>"
        
        if changes.get('new_files'):
            changes_html += "<b>New files on disk:</b><br>"
            for item in changes['new_files']:
                changes_html += f"  • {item['name']} ({item['type']})<br>"
            changes_html += "<br>"
        
        if changes.get('modified_files'):
            changes_html += "<b>Modified files on disk:</b><br>"
            for item in changes['modified_files']:
                changes_html += f"  • {item['name']} ({item['type']})<br>"
            changes_html += "<br>"
        
        if changes.get('new_db_items'):
            changes_html += "<b>New items in database:</b><br>"
            for item in changes['new_db_items']:
                changes_html += f"  • {item['name']} ({item['type']})<br>"
            changes_html += "<br>"
        
        if not any([changes.get('new_files'), changes.get('modified_files'), changes.get('new_db_items')]):
            changes_html += "No changes detected"
        
        self.changes_text.setHtml(changes_html)
    
    def _sync_to_filesystem(self):
        """Sync database to filesystem (export)."""
        if not self.git_sync_manager:
            return
        
        success, message = self.git_sync_manager.sync_to_filesystem()
        
        if success:
            # Update workspace timestamp
            if self.current_workspace:
                self.db.update_git_workspace_sync_timestamp(self.current_workspace['id'])
            
            self._refresh_status()
            self.sync_performed.emit(message)
            
            # Show success with Git instructions
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"{message}\n\n"
                "✅ Files exported to .postmini/ folder\n\n"
                "⚠️ Next step: Commit to Git\n"
                "Run in terminal:\n"
                "  git add .postmini/\n"
                "  git commit -m \"Update collections\"\n"
                "  git push"
            )
        else:
            QMessageBox.warning(self, "Export Failed", message)
    
    def _sync_from_filesystem(self):
        """Sync filesystem to database (import)."""
        if not self.git_sync_manager:
            return
        
        reply = QMessageBox.question(
            self,
            "Import from Files",
            "This will import collections and environments from .postmini/ folder.\n"
            "Existing items with the same name will be updated.\n\n"
            "💡 Tip: Run 'git pull' first to get latest changes from teammates.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_sync_manager.sync_from_filesystem(update_existing=True)
            
            if success:
                # Update workspace timestamp
                if self.current_workspace:
                    self.db.update_git_workspace_sync_timestamp(self.current_workspace['id'])
                
                self._refresh_status()
                self.sync_performed.emit(message)
                QMessageBox.information(
                    self, 
                    "Import Successful", 
                    f"{message}\n\n"
                    "✅ Collections imported from .postmini/ folder"
                )
            else:
                QMessageBox.warning(self, "Import Failed", message)
    
    def _show_git_commands(self):
        """Show Git commands dialog with copy functionality."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
        from PyQt6.QtGui import QFont
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Git Commands Reference")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        title = QLabel("<h2>Git Commands for Collaboration</h2>")
        layout.addWidget(title)
        
        # Commands text
        commands_text = QTextEdit()
        commands_text.setReadOnly(True)
        font = QFont("Courier New", 10)
        commands_text.setFont(font)
        
        commands = """# After exporting collections (clicking Export button):
# ================================================

# 1. Check what changed
git status

# 2. See the diff
git diff .postmini/

# 3. Add files to staging
git add .postmini/

# 4. Commit with message
git commit -m "Update API collections"

# 5. Push to remote
git push


# Before importing collections (to get teammates' changes):
# ================================================

# 1. Pull latest changes
git pull

# 2. Then click "Import from Files" in PostMini


# Full workflow example:
# ================================================

# Make changes in PostMini → Click Export
git add .postmini/
git commit -m "Add user authentication endpoints"
git push

# Teammate pulls and imports:
git pull
# Then click "Import from Files" in PostMini Status tab


# Tip: Add alias to your .gitconfig for quick commits:
# ================================================
# git config --global alias.sync-collections '!git add .postmini/ && git commit -m "Update collections" && git push'
# 
# Then just run:
# git sync-collections
"""
        
        commands_text.setPlainText(commands)
        layout.addWidget(commands_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        copy_button = QPushButton("📋 Copy All Commands")
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(commands))
        button_layout.addWidget(copy_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _refresh_workspaces_list(self):
        """Refresh the list of all workspaces."""
        workspaces = self.db.get_all_git_workspaces()
        
        self.workspaces_table.setRowCount(len(workspaces))
        
        for i, workspace in enumerate(workspaces):
            # Project path
            self.workspaces_table.setItem(i, 0, QTableWidgetItem(workspace['project_path']))
            
            # Status
            status = workspace.get('sync_status', 'unknown')
            self.workspaces_table.setItem(i, 1, QTableWidgetItem(status))
            
            # Last sync
            last_sync = workspace.get('last_sync_timestamp', 'Never')
            if last_sync and last_sync != 'Never':
                # Format timestamp
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_sync)
                    last_sync = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            self.workspaces_table.setItem(i, 2, QTableWidgetItem(last_sync))
            
            # Auto-sync
            auto_sync = "Yes" if workspace.get('auto_sync', False) else "No"
            self.workspaces_table.setItem(i, 3, QTableWidgetItem(auto_sync))
    
    def _remove_workspace(self):
        """Remove selected workspace from list."""
        current_row = self.workspaces_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a workspace to remove.")
            return
        
        path_item = self.workspaces_table.item(current_row, 0)
        if not path_item:
            return
        
        project_path = path_item.text()
        
        reply = QMessageBox.question(
            self,
            "Remove Workspace",
            f"Remove Git sync configuration for:\n{project_path}\n\n"
            "Files will not be deleted, only the sync configuration.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            workspace = self.db.get_git_workspace_by_path(project_path)
            if workspace:
                self.db.delete_git_workspace(workspace['id'])
                
                # If this was the current workspace, clear it
                if self.current_workspace and self.current_workspace['id'] == workspace['id']:
                    self._disable_git_sync()
                
                self._refresh_workspaces_list()
                QMessageBox.information(self, "Removed", "Workspace configuration removed.")
    
    def showEvent(self, event):
        """Called when dialog is shown."""
        super().showEvent(event)
        self._refresh_workspaces_list()
        if self.git_sync_manager:
            self._refresh_status()

