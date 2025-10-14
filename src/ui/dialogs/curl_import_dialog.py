"""
cURL Import Dialog

Dialog for importing cURL commands into PostMini.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from src.features.curl_converter import CurlConverter


class CurlImportDialog(QDialog):
    """
    Dialog for importing cURL commands.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.request_data = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Import cURL Command")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "<b>Paste your cURL command below:</b><br><br>"
            "Example:<br>"
            "<code>curl -X POST 'https://api.example.com/users' \\<br>"
            "&nbsp;&nbsp;-H 'Content-Type: application/json' \\<br>"
            "&nbsp;&nbsp;-d '{\"name\": \"John Doe\"}'</code>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Text editor for cURL command
        self.curl_input = QTextEdit()
        self.curl_input.setPlaceholderText(
            "Paste cURL command here...\n\n"
            "Example:\n"
            "curl -X POST 'https://api.example.com/users' \\\n"
            "  -H 'Content-Type: application/json' \\\n"
            "  -d '{\"name\": \"John Doe\"}'"
        )
        self.curl_input.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.curl_input)
        
        # Preview section
        preview_label = QLabel("<b>Preview:</b>")
        layout.addWidget(preview_label)
        
        self.preview_text = QLabel("Paste a cURL command to see the preview...")
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet("""
            QLabel {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                min-height: 80px;
            }
        """)
        layout.addWidget(self.preview_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        preview_btn = QPushButton("🔍 Preview")
        preview_btn.clicked.connect(self._preview_curl)
        button_layout.addWidget(preview_btn)
        
        import_btn = QPushButton("📥 Import")
        import_btn.setDefault(True)
        import_btn.clicked.connect(self._import_curl)
        button_layout.addWidget(import_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _preview_curl(self):
        """Preview the parsed cURL command."""
        curl_command = self.curl_input.toPlainText().strip()
        
        if not curl_command:
            self.preview_text.setText("⚠️ Please paste a cURL command first.")
            return
        
        try:
            data = CurlConverter.curl_to_request(curl_command)
            
            # Build preview text
            preview = f"<b>Method:</b> {data['method']}<br>"
            preview += f"<b>URL:</b> {data['url']}<br>"
            
            if data.get('params'):
                preview += f"<b>Parameters:</b> {len(data['params'])} parameter(s)<br>"
                for key, value in list(data['params'].items())[:3]:
                    preview += f"&nbsp;&nbsp;• {key} = {value}<br>"
                if len(data['params']) > 3:
                    preview += f"&nbsp;&nbsp;• ... and {len(data['params']) - 3} more<br>"
            
            if data.get('headers'):
                preview += f"<b>Headers:</b> {len(data['headers'])} header(s)<br>"
                for key, value in list(data['headers'].items())[:3]:
                    preview += f"&nbsp;&nbsp;• {key}: {value[:50]}{'...' if len(value) > 50 else ''}<br>"
                if len(data['headers']) > 3:
                    preview += f"&nbsp;&nbsp;• ... and {len(data['headers']) - 3} more<br>"
            
            if data.get('body'):
                body_preview = data['body'][:100]
                if len(data['body']) > 100:
                    body_preview += "..."
                preview += f"<b>Body:</b> {len(data['body'])} character(s)<br>"
                preview += f"&nbsp;&nbsp;<code>{body_preview}</code><br>"
            
            preview += "<br><span style='color: green;'>✅ Valid cURL command! Click Import to add this request.</span>"
            
            self.preview_text.setText(preview)
            
        except ValueError as e:
            self.preview_text.setText(f"<span style='color: red;'>❌ Error parsing cURL command:<br>{str(e)}</span>")
        except Exception as e:
            self.preview_text.setText(f"<span style='color: red;'>❌ Unexpected error:<br>{str(e)}</span>")
    
    def _import_curl(self):
        """Import the cURL command."""
        curl_command = self.curl_input.toPlainText().strip()
        
        if not curl_command:
            QMessageBox.warning(
                self,
                "Empty Command",
                "Please paste a cURL command first."
            )
            return
        
        try:
            self.request_data = CurlConverter.curl_to_request(curl_command)
            self.accept()
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Invalid cURL Command",
                f"Failed to parse cURL command:\n\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Unexpected error while importing:\n\n{str(e)}"
            )
    
    def get_request_data(self):
        """Get the imported request data."""
        return self.request_data

