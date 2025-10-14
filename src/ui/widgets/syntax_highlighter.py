"""
Syntax Highlighters for Response Viewer

Provides syntax highlighting for JSON, XML, HTML, and other formats
in the response body text editor.
"""

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import Qt, QRegularExpression
import re


class JSONHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for JSON."""
    
    def __init__(self, document, dark_mode=True):
        super().__init__(document)
        self.dark_mode = dark_mode
        self._setup_formats()
    
    def _setup_formats(self):
        """Setup text formats for different JSON elements."""
        if self.dark_mode:
            # Dark mode colors
            self.key_color = QColor("#9CDCFE")  # Light blue
            self.string_color = QColor("#CE9178")  # Orange
            self.number_color = QColor("#B5CEA8")  # Light green
            self.keyword_color = QColor("#569CD6")  # Blue (true, false, null)
            self.brace_color = QColor("#D4D4D4")  # Light gray
        else:
            # Light mode colors
            self.key_color = QColor("#0451A5")  # Blue
            self.string_color = QColor("#A31515")  # Red
            self.number_color = QColor("#098658")  # Green
            self.keyword_color = QColor("#0000FF")  # Blue
            self.brace_color = QColor("#000000")  # Black
        
        # Key format (property names)
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(self.key_color)
        self.key_format.setFontWeight(QFont.Weight.Bold)
        
        # String value format
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(self.string_color)
        
        # Number format
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(self.number_color)
        
        # Keyword format (true, false, null)
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(self.keyword_color)
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        
        # Brace/bracket format
        self.brace_format = QTextCharFormat()
        self.brace_format.setForeground(self.brace_color)
        self.brace_format.setFontWeight(QFont.Weight.Bold)
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        # Highlight JSON keys: "key":
        key_pattern = QRegularExpression(r'"([^"\\]|\\.)*"\s*:')
        key_matches = key_pattern.globalMatch(text)
        while key_matches.hasNext():
            match = key_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength() - 1, self.key_format)
        
        # Highlight string values: "value" (not followed by :)
        string_pattern = QRegularExpression(r'"([^"\\]|\\.)*"(?!\s*:)')
        string_matches = string_pattern.globalMatch(text)
        while string_matches.hasNext():
            match = string_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.string_format)
        
        # Highlight numbers
        number_pattern = QRegularExpression(r'\b-?\d+\.?\d*([eE][+-]?\d+)?\b')
        number_matches = number_pattern.globalMatch(text)
        while number_matches.hasNext():
            match = number_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.number_format)
        
        # Highlight keywords (true, false, null)
        keyword_pattern = QRegularExpression(r'\b(true|false|null)\b')
        keyword_matches = keyword_pattern.globalMatch(text)
        while keyword_matches.hasNext():
            match = keyword_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.keyword_format)
        
        # Highlight braces and brackets
        brace_pattern = QRegularExpression(r'[{}\[\],]')
        brace_matches = brace_pattern.globalMatch(text)
        while brace_matches.hasNext():
            match = brace_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.brace_format)


class XMLHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for XML/HTML."""
    
    def __init__(self, document, dark_mode=True):
        super().__init__(document)
        self.dark_mode = dark_mode
        self._setup_formats()
    
    def _setup_formats(self):
        """Setup text formats for different XML elements."""
        if self.dark_mode:
            # Dark mode colors
            self.tag_color = QColor("#569CD6")  # Blue
            self.attribute_color = QColor("#9CDCFE")  # Light blue
            self.value_color = QColor("#CE9178")  # Orange
            self.comment_color = QColor("#6A9955")  # Green
        else:
            # Light mode colors
            self.tag_color = QColor("#0000FF")  # Blue
            self.attribute_color = QColor("#FF0000")  # Red
            self.value_color = QColor("#A31515")  # Dark red
            self.comment_color = QColor("#008000")  # Green
        
        # Tag format
        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(self.tag_color)
        self.tag_format.setFontWeight(QFont.Weight.Bold)
        
        # Attribute format
        self.attribute_format = QTextCharFormat()
        self.attribute_format.setForeground(self.attribute_color)
        
        # Value format
        self.value_format = QTextCharFormat()
        self.value_format.setForeground(self.value_color)
        
        # Comment format
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(self.comment_color)
        self.comment_format.setFontItalic(True)
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        # Highlight comments
        comment_pattern = QRegularExpression(r'<!--.*?-->')
        comment_matches = comment_pattern.globalMatch(text)
        while comment_matches.hasNext():
            match = comment_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.comment_format)
        
        # Highlight tags
        tag_pattern = QRegularExpression(r'</?[\w:-]+')
        tag_matches = tag_pattern.globalMatch(text)
        while tag_matches.hasNext():
            match = tag_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.tag_format)
        
        # Highlight closing bracket
        closing_pattern = QRegularExpression(r'/?>')
        closing_matches = closing_pattern.globalMatch(text)
        while closing_matches.hasNext():
            match = closing_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.tag_format)
        
        # Highlight attribute names
        attr_pattern = QRegularExpression(r'\b[\w:-]+=')
        attr_matches = attr_pattern.globalMatch(text)
        while attr_matches.hasNext():
            match = attr_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength() - 1, self.attribute_format)
        
        # Highlight attribute values
        value_pattern = QRegularExpression(r'="[^"]*"')
        value_matches = value_pattern.globalMatch(text)
        while value_matches.hasNext():
            match = value_matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.value_format)
        
        value_pattern2 = QRegularExpression(r"='[^']*'")
        value_matches2 = value_pattern2.globalMatch(text)
        while value_matches2.hasNext():
            match = value_matches2.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.value_format)


def apply_syntax_highlighting(text_edit, content_type: str, dark_mode: bool = True):
    """
    Apply appropriate syntax highlighting based on content type.
    
    Args:
        text_edit: QTextEdit widget
        content_type: MIME type or format (e.g., 'application/json', 'text/xml')
        dark_mode: Whether to use dark mode colors
    
    Returns:
        The highlighter instance or None
    """
    # Remove existing highlighter if any
    if hasattr(text_edit, '_highlighter'):
        text_edit._highlighter.setDocument(None)
        text_edit._highlighter = None
    
    # Determine highlighter based on content type
    highlighter = None
    
    if 'json' in content_type.lower():
        highlighter = JSONHighlighter(text_edit.document(), dark_mode)
    elif any(x in content_type.lower() for x in ['xml', 'html', 'xhtml']):
        highlighter = XMLHighlighter(text_edit.document(), dark_mode)
    
    # Store reference to prevent garbage collection
    if highlighter:
        text_edit._highlighter = highlighter
    
    return highlighter

