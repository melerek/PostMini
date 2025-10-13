"""
OAuth Configuration Dialog

This module provides UI for configuring and managing OAuth 2.0 authentication.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QTextEdit, QListWidget, QMessageBox,
    QFormLayout, QGroupBox, QTabWidget, QWidget, QListWidgetItem,
    QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from typing import Dict, Optional

from src.core.database import DatabaseManager
from src.features.oauth_manager import OAuthManager


class OAuthFlowThread(QThread):
    """Thread for running OAuth authorization flow."""
    
    success = pyqtSignal(dict)  # Emits token data
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, oauth_manager: OAuthManager, flow_type: str, config: Dict):
        super().__init__()
        self.oauth_manager = oauth_manager
        self.flow_type = flow_type
        self.config = config
    
    def run(self):
        """Run the OAuth flow."""
        try:
            if self.flow_type == OAuthManager.FLOW_AUTHORIZATION_CODE:
                self._run_authorization_code_flow()
            elif self.flow_type == OAuthManager.FLOW_CLIENT_CREDENTIALS:
                self._run_client_credentials_flow()
            elif self.flow_type == OAuthManager.FLOW_PASSWORD:
                self._run_password_flow()
            else:
                self.error.emit(f"Unsupported flow type: {self.flow_type}")
        except Exception as e:
            self.error.emit(str(e))
    
    def _run_authorization_code_flow(self):
        """Run Authorization Code Flow."""
        # Start local callback server
        redirect_uri = self.oauth_manager.start_local_callback_server(port=8080)
        
        # Build authorization URL
        auth_url, state = self.oauth_manager.start_authorization_code_flow(
            auth_url=self.config['auth_url'],
            client_id=self.config['client_id'],
            redirect_uri=redirect_uri,
            scope=self.config.get('scope'),
            state=self.config.get('state'),
            additional_params=self.config.get('additional_params')
        )
        
        # Open browser
        self.oauth_manager.open_browser(auth_url)
        
        # Wait for callback
        code, returned_state, error = self.oauth_manager.wait_for_callback(timeout=300)
        
        self.oauth_manager.stop_callback_server()
        
        if error:
            self.error.emit(f"Authorization error: {error}")
            return
        
        if not code:
            self.error.emit("Authorization cancelled or timed out")
            return
        
        if state and returned_state != state:
            self.error.emit("State mismatch - possible CSRF attack")
            return
        
        # Exchange code for token
        token_data = self.oauth_manager.exchange_code_for_token(
            token_url=self.config['token_url'],
            code=code,
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            redirect_uri=redirect_uri,
            additional_params=self.config.get('additional_params')
        )
        
        self.success.emit(token_data)
    
    def _run_client_credentials_flow(self):
        """Run Client Credentials Flow."""
        token_data = self.oauth_manager.get_client_credentials_token(
            token_url=self.config['token_url'],
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            scope=self.config.get('scope'),
            additional_params=self.config.get('additional_params')
        )
        self.success.emit(token_data)
    
    def _run_password_flow(self):
        """Run Password Grant Flow."""
        token_data = self.oauth_manager.get_password_grant_token(
            token_url=self.config['token_url'],
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            username=self.config['username'],
            password=self.config['password'],
            scope=self.config.get('scope'),
            additional_params=self.config.get('additional_params')
        )
        self.success.emit(token_data)


class OAuthConfigDialog(QDialog):
    """Dialog for managing OAuth configurations."""
    
    config_selected = pyqtSignal(dict)  # Emits selected OAuth config with token
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.oauth_manager = OAuthManager()
        self.current_config_id = None
        self.oauth_thread = None
        
        self.setWindowTitle("OAuth 2.0 Configuration")
        self.setGeometry(200, 200, 900, 700)
        
        self._init_ui()
        self._load_configs()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("OAuth 2.0 Configuration Manager")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Main content with tabs
        tabs = QTabWidget()
        
        # Tab 1: Manage Configurations
        manage_tab = self._create_manage_tab()
        tabs.addTab(manage_tab, "📋 Manage Configs")
        
        # Tab 2: Create/Edit Configuration
        edit_tab = self._create_edit_tab()
        tabs.addTab(edit_tab, "➕ Add/Edit Config")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_manage_tab(self) -> QWidget:
        """Create the manage configurations tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        info = QLabel("Select an OAuth configuration to authorize and get an access token:")
        layout.addWidget(info)
        
        # Configurations list
        self.config_list = QListWidget()
        self.config_list.itemClicked.connect(self._on_config_selected)
        layout.addWidget(self.config_list)
        
        # Config details
        details_group = QGroupBox("Configuration Details")
        details_layout = QFormLayout()
        
        self.detail_name = QLabel("-")
        self.detail_flow = QLabel("-")
        self.detail_auth_url = QLabel("-")
        self.detail_token_url = QLabel("-")
        self.detail_client_id = QLabel("-")
        self.detail_scope = QLabel("-")
        
        details_layout.addRow("Name:", self.detail_name)
        details_layout.addRow("Flow Type:", self.detail_flow)
        details_layout.addRow("Auth URL:", self.detail_auth_url)
        details_layout.addRow("Token URL:", self.detail_token_url)
        details_layout.addRow("Client ID:", self.detail_client_id)
        details_layout.addRow("Scope:", self.detail_scope)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Token status
        token_group = QGroupBox("Token Status")
        token_layout = QVBoxLayout()
        
        self.token_status_label = QLabel("No token")
        self.token_status_label.setProperty("class", "secondary-text")
        token_layout.addWidget(self.token_status_label)
        
        token_group.setLayout(token_layout)
        layout.addWidget(token_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.authorize_btn = QPushButton("🔐 Authorize")
        self.authorize_btn.clicked.connect(self._authorize_config)
        self.authorize_btn.setEnabled(False)
        self.authorize_btn.setProperty("class", "primary")
        action_layout.addWidget(self.authorize_btn)
        
        self.use_token_btn = QPushButton("✅ Use This Token")
        self.use_token_btn.clicked.connect(self._use_selected_token)
        self.use_token_btn.setEnabled(False)
        action_layout.addWidget(self.use_token_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete Config")
        self.delete_btn.clicked.connect(self._delete_config)
        self.delete_btn.setEnabled(False)
        action_layout.addWidget(self.delete_btn)
        
        layout.addLayout(action_layout)
        
        return widget
    
    def _create_edit_tab(self) -> QWidget:
        """Create the add/edit configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Form
        form_layout = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., GitHub OAuth")
        form_layout.addRow("Config Name:*", self.name_input)
        
        # Flow Type
        self.flow_combo = QComboBox()
        self.flow_combo.addItems([
            "Authorization Code",
            "Client Credentials",
            "Password Grant"
        ])
        self.flow_combo.currentTextChanged.connect(self._on_flow_type_changed)
        form_layout.addRow("Flow Type:*", self.flow_combo)
        
        # Auth URL (for Authorization Code flow)
        self.auth_url_input = QLineEdit()
        self.auth_url_input.setPlaceholderText("https://provider.com/oauth/authorize")
        form_layout.addRow("Authorization URL:", self.auth_url_input)
        
        # Token URL
        self.token_url_input = QLineEdit()
        self.token_url_input.setPlaceholderText("https://provider.com/oauth/token")
        form_layout.addRow("Token URL:*", self.token_url_input)
        
        # Client ID
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("your-client-id")
        form_layout.addRow("Client ID:*", self.client_id_input)
        
        # Client Secret
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_input.setPlaceholderText("your-client-secret")
        form_layout.addRow("Client Secret:*", self.client_secret_input)
        
        # Scope
        self.scope_input = QLineEdit()
        self.scope_input.setPlaceholderText("read write (space-separated)")
        form_layout.addRow("Scope:", self.scope_input)
        
        # Username (for Password Grant)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Resource owner username")
        self.username_input.setVisible(False)
        form_layout.addRow("Username:", self.username_input)
        
        # Password (for Password Grant)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Resource owner password")
        self.password_input.setVisible(False)
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setProperty("class", "secondary-text")
        self._update_info_label()
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        # Save button
        save_btn = QPushButton("💾 Save Configuration")
        save_btn.clicked.connect(self._save_config)
        save_btn.setProperty("class", "primary")
        layout.addWidget(save_btn)
        
        return widget
    
    def _on_flow_type_changed(self, flow_type: str):
        """Handle flow type selection change."""
        is_auth_code = (flow_type == "Authorization Code")
        is_password = (flow_type == "Password Grant")
        
        # Show/hide auth URL based on flow type
        self.auth_url_input.setVisible(is_auth_code)
        
        # Show/hide username/password for Password Grant
        self.username_input.setVisible(is_password)
        self.password_input.setVisible(is_password)
        
        self._update_info_label()
    
    def _update_info_label(self):
        """Update the information label based on selected flow."""
        flow = self.flow_combo.currentText()
        
        info_texts = {
            "Authorization Code": "✅ Most secure. Opens browser for user authorization. Recommended for user-facing applications.",
            "Client Credentials": "⚡ Server-to-server auth. No user interaction. Good for backend services.",
            "Password Grant": "⚠️ Legacy flow. User credentials sent directly. Use only if other flows aren't supported."
        }
        
        self.info_label.setText(info_texts.get(flow, ""))
    
    def _load_configs(self):
        """Load OAuth configurations from database."""
        self.config_list.clear()
        configs = self.db.get_all_oauth_configs()
        
        for config in configs:
            item = QListWidgetItem(f"{config['name']} ({config['flow_type']})")
            item.setData(Qt.ItemDataRole.UserRole, config)
            self.config_list.addItem(item)
    
    def _on_config_selected(self, item: QListWidgetItem):
        """Handle configuration selection."""
        config = item.data(Qt.ItemDataRole.UserRole)
        if not config:
            return
        
        self.current_config_id = config['id']
        
        # Update details
        self.detail_name.setText(config['name'])
        self.detail_flow.setText(config['flow_type'])
        self.detail_auth_url.setText(config.get('auth_url') or "N/A")
        self.detail_token_url.setText(config['token_url'])
        self.detail_client_id.setText(config['client_id'])
        self.detail_scope.setText(config.get('scope') or "N/A")
        
        # Check token status
        token = self.db.get_oauth_token(config['id'])
        if token:
            is_expired = OAuthManager.is_token_expired(token.get('expires_at'))
            if is_expired:
                self.token_status_label.setText("❌ Token expired")
                self.token_status_label.setProperty("class", "error-text")
                self.token_status_label.style().unpolish(self.token_status_label)
                self.token_status_label.style().polish(self.token_status_label)
                self.use_token_btn.setEnabled(False)
            else:
                expiry = token.get('expires_at', 'Unknown')
                self.token_status_label.setText(f"✅ Valid token (expires: {expiry[:19]})")
                self.token_status_label.setProperty("class", "success-text")
                self.token_status_label.style().unpolish(self.token_status_label)
                self.token_status_label.style().polish(self.token_status_label)
                self.use_token_btn.setEnabled(True)
        else:
            self.token_status_label.setText("No token available")
            self.token_status_label.setProperty("class", "secondary-text")
            self.token_status_label.style().unpolish(self.token_status_label)
            self.token_status_label.style().polish(self.token_status_label)
            self.use_token_btn.setEnabled(False)
        
        self.authorize_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
    
    def _save_config(self):
        """Save OAuth configuration."""
        try:
            name = self.name_input.text().strip()
            flow_type_display = self.flow_combo.currentText()
            token_url = self.token_url_input.text().strip()
            client_id = self.client_id_input.text().strip()
            client_secret = self.client_secret_input.text().strip()
            
            # Validation
            if not name or not token_url or not client_id or not client_secret:
                QMessageBox.warning(self, "Validation Error",
                                  "Please fill in all required fields (marked with *).")
                return
            
            # Map display name to internal flow type
            flow_map = {
                "Authorization Code": OAuthManager.FLOW_AUTHORIZATION_CODE,
                "Client Credentials": OAuthManager.FLOW_CLIENT_CREDENTIALS,
                "Password Grant": OAuthManager.FLOW_PASSWORD
            }
            flow_type = flow_map[flow_type_display]
            
            # Get optional fields
            auth_url = self.auth_url_input.text().strip() or None
            scope = self.scope_input.text().strip() or None
            
            # Validate auth URL for Authorization Code flow
            if flow_type == OAuthManager.FLOW_AUTHORIZATION_CODE and not auth_url:
                QMessageBox.warning(self, "Validation Error",
                                  "Authorization URL is required for Authorization Code flow.")
                return
            
            # Save to database
            config_id = self.db.create_oauth_config(
                name=name,
                flow_type=flow_type,
                auth_url=auth_url,
                token_url=token_url,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope
            )
            
            QMessageBox.information(self, "Success",
                                  f"OAuth configuration '{name}' saved successfully!\n\n"
                                  "Go to 'Manage Configs' tab to authorize and get a token.")
            
            # Clear form
            self.name_input.clear()
            self.auth_url_input.clear()
            self.token_url_input.clear()
            self.client_id_input.clear()
            self.client_secret_input.clear()
            self.scope_input.clear()
            self.username_input.clear()
            self.password_input.clear()
            
            # Reload list
            self._load_configs()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
    
    def _authorize_config(self):
        """Start OAuth authorization flow."""
        if not self.current_config_id:
            return
        
        try:
            config = self.db.get_oauth_config(self.current_config_id)
            if not config:
                QMessageBox.warning(self, "Error", "Configuration not found.")
                return
            
            # Check if Password Grant flow needs credentials
            if config['flow_type'] == OAuthManager.FLOW_PASSWORD:
                from PyQt6.QtWidgets import QInputDialog
                username, ok = QInputDialog.getText(self, "Username", "Enter username:")
                if not ok:
                    return
                password, ok = QInputDialog.getText(self, "Password", "Enter password:", QLineEdit.EchoMode.Password)
                if not ok:
                    return
                config['username'] = username
                config['password'] = password
            
            # Show progress dialog
            progress = QProgressDialog("Authorizing... Please complete the authorization in your browser.", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.show()
            
            # Start OAuth flow in thread
            self.oauth_thread = OAuthFlowThread(self.oauth_manager, config['flow_type'], config)
            self.oauth_thread.success.connect(lambda token_data: self._on_authorization_success(token_data, progress))
            self.oauth_thread.error.connect(lambda error: self._on_authorization_error(error, progress))
            self.oauth_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start authorization: {str(e)}")
    
    def _on_authorization_success(self, token_data: Dict, progress: QProgressDialog):
        """Handle successful authorization."""
        progress.close()
        
        try:
            # Calculate expiry time
            expires_at = None
            if 'expires_in' in token_data:
                expires_at = OAuthManager.calculate_expiry_time(token_data['expires_in'])
            
            # Save token
            self.db.save_oauth_token(
                config_id=self.current_config_id,
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_type=token_data.get('token_type', 'Bearer'),
                expires_at=expires_at,
                scope=token_data.get('scope')
            )
            
            QMessageBox.information(self, "Success",
                                  "✅ Authorization successful!\n\n"
                                  "Access token has been saved.\n"
                                  "Click 'Use This Token' to apply it to your requests.")
            
            # Refresh config display
            item = self.config_list.currentItem()
            if item:
                self._on_config_selected(item)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save token: {str(e)}")
    
    def _on_authorization_error(self, error: str, progress: QProgressDialog):
        """Handle authorization error."""
        progress.close()
        QMessageBox.critical(self, "Authorization Failed", f"Failed to authorize:\n\n{error}")
    
    def _use_selected_token(self):
        """Use the selected OAuth token in requests."""
        if not self.current_config_id:
            return
        
        try:
            config = self.db.get_oauth_config(self.current_config_id)
            token = self.db.get_oauth_token(self.current_config_id)
            
            if not token:
                QMessageBox.warning(self, "Error", "No token available.")
                return
            
            # Emit config and token
            self.config_selected.emit({
                'config': config,
                'token': token
            })
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to use token: {str(e)}")
    
    def _delete_config(self):
        """Delete OAuth configuration."""
        if not self.current_config_id:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this OAuth configuration?\n\n"
            "This will also delete all associated tokens.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_oauth_config(self.current_config_id)
                QMessageBox.information(self, "Success", "OAuth configuration deleted.")
                self.current_config_id = None
                self._load_configs()
                
                # Clear details
                self.detail_name.setText("-")
                self.detail_flow.setText("-")
                self.detail_auth_url.setText("-")
                self.detail_token_url.setText("-")
                self.detail_client_id.setText("-")
                self.detail_scope.setText("-")
                self.token_status_label.setText("No token")
                self.token_status_label.setProperty("class", "secondary-text")
                self.token_status_label.style().unpolish(self.token_status_label)
                self.token_status_label.style().polish(self.token_status_label)
                
                self.authorize_btn.setEnabled(False)
                self.use_token_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete configuration: {str(e)}")
    
    def closeEvent(self, event):
        """Handle dialog close event - clean up OAuth thread and callback server."""
        if self.oauth_thread and self.oauth_thread.isRunning():
            self.oauth_thread.wait(2000)  # Wait up to 2 seconds
        
        # Stop OAuth callback server if running
        if self.oauth_manager:
            self.oauth_manager.stop_callback_server()
        
        event.accept()

