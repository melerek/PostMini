"""
Code Snippet Dialog

This module provides a dialog for viewing and copying generated code snippets.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QClipboard
from typing import Dict, Optional

from src.features.code_generator import CodeGenerator


class CodeSnippetDialog(QDialog):
    """
    Dialog for viewing and copying generated code snippets.
    """
    
    def __init__(self, method: str, url: str,
                params: Optional[Dict] = None,
                headers: Optional[Dict] = None,
                body: Optional[str] = None,
                auth_type: str = 'None',
                auth_token: Optional[str] = None,
                parent=None):
        super().__init__(parent)
        
        # Store request data
        self.method = method
        self.url = url
        self.params = params or {}
        self.headers = headers or {}
        self.body = body
        self.auth_type = auth_type
        self.auth_token = auth_token
        
        self.setWindowTitle("Generate Code Snippet")
        self.setGeometry(200, 200, 800, 600)
        
        self._init_ui()
        self._generate_code()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Code Snippet Generator")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Select a language to generate code snippet:")
        layout.addWidget(desc)
        
        # Language selector
        lang_layout = QHBoxLayout()
        
        lang_layout.addWidget(QLabel("Language:"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "curl (Command Line)",
            "Python (requests)",
            "JavaScript (fetch)",
            "JavaScript (axios)",
            "Node.js (https)",
            "React (Component)",
            "C# (HttpClient)"
        ])
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.language_combo)
        
        lang_layout.addStretch()
        
        layout.addLayout(lang_layout)
        
        # Code display
        code_label = QLabel("Generated Code:")
        code_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(code_label)
        
        self.code_text = QTextEdit()
        self.code_text.setReadOnly(True)
        self.code_text.setFont(QFont("Courier New", 10))
        self.code_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.code_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        copy_btn.setProperty("class", "primary")
        button_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _get_language_key(self, display_name: str) -> str:
        """Convert display name to internal language key."""
        mapping = {
            "curl (Command Line)": "curl",
            "Python (requests)": "python",
            "JavaScript (fetch)": "javascript_fetch",
            "JavaScript (axios)": "javascript_axios",
            "Node.js (https)": "nodejs",
            "React (Component)": "react",
            "C# (HttpClient)": "csharp",
        }
        return mapping.get(display_name, "curl")
    
    def _generate_code(self):
        """Generate code for the currently selected language."""
        try:
            display_name = self.language_combo.currentText()
            language = self._get_language_key(display_name)
            
            code = CodeGenerator.generate(
                language=language,
                method=self.method,
                url=self.url,
                params=self.params,
                headers=self.headers,
                body=self.body,
                auth_type=self.auth_type,
                auth_token=self.auth_token
            )
            
            self.code_text.setPlainText(code)
            
        except Exception as e:
            self.code_text.setPlainText(f"Error generating code: {str(e)}")
    
    def _on_language_changed(self, language: str):
        """Handle language selection change."""
        self._generate_code()
    
    def _copy_to_clipboard(self):
        """Copy the generated code to clipboard."""
        try:
            code = self.code_text.toPlainText()
            clipboard = QClipboard()
            clipboard.setText(code)
            
            QMessageBox.information(
                self,
                "Success",
                "Code snippet copied to clipboard!"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to copy to clipboard: {str(e)}"
            )

