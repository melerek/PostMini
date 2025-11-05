"""
Code Editor Widget with Syntax Highlighting

A JavaScript code editor with syntax highlighting, line numbers, and auto-indentation.
"""

from PyQt6.QtWidgets import QWidget, QTextEdit, QPlainTextEdit, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QFont, QSyntaxHighlighter,
    QTextCharFormat, QFontDatabase, QPalette
)
import re


class LineNumberArea(QWidget):
    """Widget for displaying line numbers next to the code editor."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
    
    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class JavaScriptHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for JavaScript code."""
    
    def __init__(self, document, theme='dark'):
        super().__init__(document)
        self.theme = theme
        self._setup_highlighting_rules()
    
    def _setup_highlighting_rules(self):
        """Setup syntax highlighting rules for JavaScript."""
        
        # Define colors based on theme
        if self.theme == 'dark':
            keyword_color = QColor('#C586C0')  # Purple
            string_color = QColor('#CE9178')   # Orange
            comment_color = QColor('#6A9955')  # Green
            number_color = QColor('#B5CEA8')   # Light green
            function_color = QColor('#DCDCAA') # Yellow
        else:
            keyword_color = QColor('#0000FF')  # Blue
            string_color = QColor('#A31515')   # Red
            comment_color = QColor('#008000')  # Green
            number_color = QColor('#098658')   # Dark green
            function_color = QColor('#795E26') # Brown
        
        # Keyword format
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(keyword_color)
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        
        # JavaScript keywords
        keywords = [
            'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
            'default', 'delete', 'do', 'else', 'export', 'extends', 'finally',
            'for', 'function', 'if', 'import', 'in', 'instanceof', 'let', 'new',
            'return', 'super', 'switch', 'this', 'throw', 'try', 'typeof', 'var',
            'void', 'while', 'with', 'yield', 'async', 'await', 'of',
            'true', 'false', 'null', 'undefined'
        ]
        
        self.highlighting_rules = []
        
        # Add keyword patterns
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            self.highlighting_rules.append((re.compile(pattern), self.keyword_format))
        
        # String format (single and double quotes)
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(string_color)
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format))
        self.highlighting_rules.append((re.compile(r'`[^`\\]*(\\.[^`\\]*)*`'), self.string_format))
        
        # Number format
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(number_color)
        self.highlighting_rules.append((re.compile(r'\b[0-9]+\.?[0-9]*\b'), self.number_format))
        
        # Function format
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(function_color)
        self.highlighting_rules.append((re.compile(r'\b[A-Za-z_][A-Za-z0-9_]*(?=\()'), self.function_format))
        
        # Single-line comment format
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(comment_color)
        self.comment_format.setFontItalic(True)
        
        # Multi-line comment format
        self.multi_line_comment_format = QTextCharFormat()
        self.multi_line_comment_format.setForeground(comment_color)
        self.multi_line_comment_format.setFontItalic(True)
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        
        # Apply single-line patterns
        for pattern, format_style in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_style)
        
        # Handle single-line comments
        comment_pattern = re.compile(r'//[^\n]*')
        for match in comment_pattern.finditer(text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self.comment_format)
        
        # Handle multi-line comments
        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = text.find('/*')
        
        while start_index >= 0:
            end_index = text.find('*/', start_index)
            
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + 2
            
            self.setFormat(start_index, comment_length, self.multi_line_comment_format)
            start_index = text.find('/*', start_index + comment_length)


class CodeEditor(QPlainTextEdit):
    """
    Code editor widget with line numbers and syntax highlighting.
    Optimized for JavaScript editing.
    """
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        
        # Create line number area
        self.line_number_area = LineNumberArea(self)
        
        # Setup font (use JetBrains Mono if available)
        font = QFont("JetBrains Mono", 10)
        if not font.exactMatch():
            font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        
        self.setFont(font)
        
        # Setup editor properties
        self.setTabStopDistance(40)  # 4 spaces
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Setup syntax highlighter
        self.highlighter = JavaScriptHighlighter(self.document(), theme)
        
        # Apply theme styling
        self._apply_theme()
        
        # Connect signals
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        # Initial setup
        self.update_line_number_area_width(0)
        self.highlight_current_line()
    
    def _apply_theme(self):
        """Apply theme-specific styling to the editor."""
        if self.theme == 'dark':
            bg_color = '#252526'  # Match dark theme QTextEdit background
            text_color = '#E0E0E0'  # Match dark theme primary text
            line_number_bg = '#1E1E1E'  # Slightly darker for contrast
            line_number_fg = '#858585'
            current_line_bg = '#2A2A2A'  # Subtle highlight
            border_color = '#2D2D2D'  # Match dark theme border
            selection_bg = '#3A79D0'  # Match dark theme selection
        else:
            bg_color = '#FFFFFF'
            text_color = '#000000'
            line_number_bg = '#F0F0F0'
            line_number_fg = '#707070'
            current_line_bg = '#F0F0F0'
            border_color = '#CCCCCC'
            selection_bg = '#0078D7'
        
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
                selection-background-color: {selection_bg};
                selection-color: #FFFFFF;
            }}
        """)
        
        # Store colors for line number area
        self.line_number_bg_color = QColor(line_number_bg)
        self.line_number_fg_color = QColor(line_number_fg)
        self.current_line_bg_color = QColor(current_line_bg)
    
    def line_number_area_width(self):
        """Calculate the width needed for the line number area."""
        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def update_line_number_area_width(self, _):
        """Update the width of the line number area."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        """Update the line number area when scrolling."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
    
    def line_number_area_paint_event(self, event):
        """Paint the line number area."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), self.line_number_bg_color)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        # Draw line numbers
        painter.setPen(self.line_number_fg_color)
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0, top,
                    self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )
            
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
    
    def highlight_current_line(self):
        """Highlight the current line."""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.current_line_bg_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def keyPressEvent(self, event):
        """Handle key press events for auto-indentation."""
        
        # Handle Tab key (insert 4 spaces)
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText('    ')
            return
        
        # Handle Enter key (auto-indent)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Get current line
            cursor = self.textCursor()
            current_line = cursor.block().text()
            
            # Count leading spaces
            leading_spaces = len(current_line) - len(current_line.lstrip())
            
            # Check if line ends with { to increase indentation
            stripped = current_line.rstrip()
            if stripped.endswith('{'):
                leading_spaces += 4
            
            # Insert newline and spaces
            super().keyPressEvent(event)
            self.insertPlainText(' ' * leading_spaces)
            return
        
        # Handle closing brace (auto-dedent)
        if event.key() == Qt.Key.Key_BraceRight:
            cursor = self.textCursor()
            current_line = cursor.block().text()
            
            # If line only contains spaces, remove one indentation level
            if current_line.strip() == '':
                leading_spaces = len(current_line)
                if leading_spaces >= 4:
                    # Remove 4 spaces
                    cursor.movePosition(cursor.MoveOperation.StartOfLine)
                    for _ in range(4):
                        cursor.deleteChar()
            
            super().keyPressEvent(event)
            return
        
        # Default handling
        super().keyPressEvent(event)
    
    def set_theme(self, theme: str):
        """Change the editor theme."""
        self.theme = theme
        self._apply_theme()
        self.highlighter.theme = theme
        self.highlighter._setup_highlighting_rules()
        self.highlighter.rehighlight()

