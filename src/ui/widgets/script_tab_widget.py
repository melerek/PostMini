"""
Script Tab Widget

UI component for managing pre-request and post-response scripts in the request editor.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QTextEdit, QComboBox, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional, Dict

from src.ui.widgets.code_editor import CodeEditor
from src.features.script_snippets import ScriptSnippets


class ScriptTabWidget(QWidget):
    """Widget for managing pre-request and post-response scripts."""
    
    scripts_changed = pyqtSignal()  # Emitted when scripts are modified
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self.current_request_id = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create main splitter (vertical split between pre/post sections)
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # ========== Pre-request Script Section ==========
        pre_request_widget = self._create_script_section(
            "Pre-request Script",
            "pre_request",
            "Runs before the request is sent. Use to set variables, modify headers, etc."
        )
        self.main_splitter.addWidget(pre_request_widget)
        
        # ========== Post-response Script Section ==========
        post_response_widget = self._create_script_section(
            "Post-response Script",
            "post_response",
            "Runs after response is received. Use to extract data, run tests, etc."
        )
        self.main_splitter.addWidget(post_response_widget)
        
        # Set initial splitter sizes (50/50 split)
        self.main_splitter.setSizes([400, 400])
        
        main_layout.addWidget(self.main_splitter)
        
        # ========== Console Output Section (bottom) ==========
        self.console_widget = self._create_console_output()
        main_layout.addWidget(self.console_widget)
        
        # Apply initial theme-aware button styles
        self._update_clear_button_styles()
    
    def _create_script_section(self, title: str, script_type: str, help_text: str) -> QWidget:
        """Create a script editor section with header and controls."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(title_label)
        
        # Help text
        help_label = QLabel(f"• {help_text}")
        help_label.setProperty("class", "secondary-text")
        help_label.setStyleSheet("font-size: 11px; color: #858585;")
        header_layout.addWidget(help_label)
        
        header_layout.addStretch()
        
        # Snippets dropdown
        snippets_label = QLabel("Snippets:")
        snippets_label.setStyleSheet("font-size: 11px;")
        header_layout.addWidget(snippets_label)
        
        snippets_combo = QComboBox()
        snippets_combo.setMinimumWidth(200)
        snippets_combo.setFixedHeight(24)  # Match button height for alignment
        snippets_combo.setStyleSheet("""
            QComboBox {
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                font-size: 11px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 20px;
                padding: 4px 8px;
            }
        """)
        snippets_combo.addItem("-- Select snippet --")
        
        # Populate snippets
        if script_type == "pre_request":
            snippet_names = ScriptSnippets.get_snippet_names("pre_request")
        else:
            snippet_names = ScriptSnippets.get_snippet_names("post_response")
        
        for name in snippet_names:
            snippets_combo.addItem(name)
        
        snippets_combo.currentTextChanged.connect(
            lambda text: self._on_snippet_selected(text, script_type)
        )
        header_layout.addWidget(snippets_combo)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.setFixedHeight(24)  # Match snippets dropdown height
        clear_btn.clicked.connect(
            lambda: self._clear_script(script_type)
        )
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Code editor
        editor = CodeEditor(theme=self.theme)
        editor.setPlaceholderText(f"// {help_text}\n// Use 'pm' object to interact with environment\n")
        editor.textChanged.connect(self.scripts_changed.emit)
        editor.setMinimumHeight(100)  # Reduced for better window sizing
        
        # Store reference to editor and clear button
        if script_type == "pre_request":
            self.pre_request_editor = editor
            self.pre_request_snippets_combo = snippets_combo
            self.pre_request_clear_btn = clear_btn
        else:
            self.post_response_editor = editor
            self.post_response_snippets_combo = snippets_combo
            self.post_response_clear_btn = clear_btn
        
        layout.addWidget(editor, 1)  # Stretch to fill
        
        return container
    
    def _create_console_output(self) -> QWidget:
        """Create the console output panel."""
        container = QWidget()
        container.setMaximumHeight(200)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(5)
        
        # Header
        header_layout = QHBoxLayout()
        
        console_label = QLabel("📋 Console Output")
        console_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(console_label)
        
        header_layout.addStretch()
        
        # Clear console button
        self.clear_console_btn = QPushButton("Clear Console")
        self.clear_console_btn.setFixedWidth(100)
        self.clear_console_btn.setFixedHeight(24)
        self.clear_console_btn.clicked.connect(self._clear_console)
        header_layout.addWidget(self.clear_console_btn)
        
        # Toggle visibility button
        self.toggle_console_btn = QPushButton("▼ Hide")
        self.toggle_console_btn.setFixedWidth(70)
        self.toggle_console_btn.setFixedHeight(24)
        self.toggle_console_btn.clicked.connect(self._toggle_console)
        header_layout.addWidget(self.toggle_console_btn)
        
        layout.addLayout(header_layout)
        
        # Console text area
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumHeight(150)
        
        # Monospace font for console
        console_font = QFont("Consolas", 9)
        self.console_output.setFont(console_font)
        
        # Style console
        if self.theme == 'dark':
            bg_color = '#252526'  # Match dark theme QTextEdit background
            text_color = '#E0E0E0'  # Match dark theme primary text
            border_color = '#2D2D2D'  # Match dark theme border
        else:
            bg_color = '#FFFFFF'
            text_color = '#000000'
            border_color = '#CCCCCC'
        
        self.console_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        layout.addWidget(self.console_output)
        
        # Initial message
        self.console_output.setPlaceholderText("Console output will appear here...\nUse console.log(), console.info(), console.warn(), console.error() in your scripts.")
        
        return container
    
    def _on_snippet_selected(self, snippet_name: str, script_type: str):
        """Handle snippet selection."""
        if snippet_name == "-- Select snippet --":
            return
        
        # Get snippet code
        snippet = ScriptSnippets.get_snippet(snippet_name, script_type)
        code = snippet.get('code', '')
        
        if code:
            # Get current editor
            editor = self.pre_request_editor if script_type == "pre_request" else self.post_response_editor
            
            # Check if editor has content
            current_text = editor.toPlainText().strip()
            
            if current_text:
                # Append with separator
                editor.setPlainText(current_text + "\n\n" + code)
            else:
                # Replace empty content
                editor.setPlainText(code)
            
            # Reset combo to default
            combo = self.pre_request_snippets_combo if script_type == "pre_request" else self.post_response_snippets_combo
            combo.setCurrentIndex(0)
    
    def _clear_script(self, script_type: str):
        """Clear the script editor."""
        editor = self.pre_request_editor if script_type == "pre_request" else self.post_response_editor
        editor.clear()
        self.scripts_changed.emit()
    
    def _clear_console(self):
        """Clear console output."""
        self.console_output.clear()
    
    def _toggle_console(self):
        """Toggle console visibility."""
        if self.console_output.isVisible():
            self.console_output.hide()
            self.toggle_console_btn.setText("▲ Show")
            self.console_widget.setMaximumHeight(40)
        else:
            self.console_output.show()
            self.toggle_console_btn.setText("▼ Hide")
            self.console_widget.setMaximumHeight(200)
    
    def get_pre_request_script(self) -> str:
        """Get the pre-request script code."""
        return self.pre_request_editor.toPlainText().strip()
    
    def get_post_response_script(self) -> str:
        """Get the post-response script code."""
        return self.post_response_editor.toPlainText().strip()
    
    def set_pre_request_script(self, script: str):
        """Set the pre-request script code."""
        self.pre_request_editor.setPlainText(script or "")
    
    def set_post_response_script(self, script: str):
        """Set the post-response script code."""
        self.post_response_editor.setPlainText(script or "")
    
    def append_console_output(self, logs: list):
        """
        Append console logs to the output area.
        
        Args:
            logs: List of log dictionaries with 'level' and 'message' keys
        """
        if not logs:
            return
        
        for log in logs:
            level = log.get('level', 'info')
            message = log.get('message', '')
            
            # Format with color based on level
            if level == 'error':
                color = '#FF6B6B'  # Red
                prefix = '❌'
            elif level == 'warning':
                color = '#FFD93D'  # Yellow
                prefix = '⚠️'
            else:
                color = '#6BCF7F'  # Green
                prefix = 'ℹ️'
            
            formatted = f'<span style="color: {color};">{prefix} [{level.upper()}]</span> {message}'
            self.console_output.append(formatted)
        
        # Show console if hidden
        if not self.console_output.isVisible():
            self._toggle_console()
    
    def append_console_text(self, text: str, level: str = 'info'):
        """
        Append a single line to console output.
        
        Args:
            text: Text to append
            level: Log level ('info', 'warning', 'error')
        """
        self.append_console_output([{'level': level, 'message': text}])
    
    def set_request_id(self, request_id: Optional[int]):
        """Set the current request ID."""
        self.current_request_id = request_id
    
    def load_scripts(self, pre_request_script: str, post_response_script: str):
        """
        Load scripts into the editors.
        
        Args:
            pre_request_script: Pre-request script code
            post_response_script: Post-response script code
        """
        self.set_pre_request_script(pre_request_script)
        self.set_post_response_script(post_response_script)
    
    def clear_all(self):
        """Clear all scripts and console output."""
        self.pre_request_editor.clear()
        self.post_response_editor.clear()
        self.console_output.clear()
        self.current_request_id = None
    
    def set_theme(self, theme: str):
        """Update theme for all editors."""
        self.theme = theme
        self.pre_request_editor.set_theme(theme)
        self.post_response_editor.set_theme(theme)
        
        # Update console colors
        if theme == 'dark':
            bg_color = '#252526'  # Match dark theme QTextEdit background
            text_color = '#E0E0E0'  # Match dark theme primary text
            border_color = '#2D2D2D'  # Match dark theme border
        else:
            bg_color = '#FFFFFF'
            text_color = '#000000'
            border_color = '#CCCCCC'
        
        self.console_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        # Update Clear button styles
        self._update_clear_button_styles()
    
    def _update_clear_button_styles(self):
        """Update Clear button styles based on current theme."""
        if self.theme == 'dark':
            button_style = """
                QPushButton {
                    background-color: #2D2D2D;
                    color: #CCCCCC;
                    border: 1px solid #3C3C3C;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3C3C3C;
                    border-color: #007ACC;
                }
                QPushButton:pressed {
                    background-color: #007ACC;
                }
            """
        else:
            button_style = """
                QPushButton {
                    background-color: #F5F5F5;
                    color: #212121;
                    border: 1px solid #BDBDBD;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #E8E8E8;
                    border-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #1976D2;
                    color: #FFFFFF;
                }
            """
        
        # Apply to all buttons
        if hasattr(self, 'pre_request_clear_btn'):
            self.pre_request_clear_btn.setStyleSheet(button_style)
        if hasattr(self, 'post_response_clear_btn'):
            self.post_response_clear_btn.setStyleSheet(button_style)
        if hasattr(self, 'clear_console_btn'):
            self.clear_console_btn.setStyleSheet(button_style)
        if hasattr(self, 'toggle_console_btn'):
            self.toggle_console_btn.setStyleSheet(button_style)

