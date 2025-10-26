"""
Variable Highlight Delegate

Custom delegate and syntax highlighter for highlighting variables in the format {{variableName}}.
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QPainter, QFont, QPalette
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal


class HighlightedLineEdit(QLineEdit):
    """Custom QLineEdit with variable highlighting support."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self._setup_colors()
    
    def _setup_colors(self):
        """Setup colors based on theme."""
        if self.theme == 'dark':
            self.var_color = QColor("#BB86FC")  # Material purple
        else:
            self.var_color = QColor("#6200EA")  # Material deep purple
    
    def set_theme(self, theme):
        """Update theme and repaint."""
        self.theme = theme
        self._setup_colors()
        self.update()
    
    def paintEvent(self, event):
        """Custom paint to highlight variables."""
        # Call default paint first
        super().paintEvent(event)
        
        # Only highlight if there are variables
        text = self.text()
        if not text or '{{' not in text or '}}' not in text:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get font metrics
        fm = self.fontMetrics()
        
        # Calculate text position (accounting for cursor position and text margins)
        text_rect = self.rect()
        text_margins = self.textMargins()
        x_offset = text_margins.left() + 5  # Small padding
        y_baseline = (text_rect.height() + fm.ascent() - fm.descent()) // 2
        
        # Parse and highlight variables
        i = 0
        current_x = x_offset
        
        while i < len(text):
            if i < len(text) - 1 and text[i:i+2] == '{{':
                # Find end of variable
                end = text.find('}}', i + 2)
                if end != -1:
                    # Found a complete variable
                    var_text = text[i:end+2]
                    
                    # Calculate the width of text before variable
                    text_before = text[:i]
                    x_pos = x_offset + fm.horizontalAdvance(text_before)
                    
                    # Draw variable in color
                    painter.setPen(self.var_color)
                    painter.setFont(self.font())
                    painter.drawText(x_pos, y_baseline, var_text)
                    
                    i = end + 2
                    continue
            i += 1


class VariableSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for {{variable}} patterns - works with QTextEdit."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self._setup_format()
    
    def _setup_format(self):
        """Setup the format for variable highlighting."""
        self.variable_format = QTextCharFormat()
        
        # Color based on theme
        if self.theme == 'dark':
            # Soft purple/blue color for dark theme
            self.variable_format.setForeground(QColor("#BB86FC"))  # Material purple
        else:
            # Darker purple for light theme
            self.variable_format.setForeground(QColor("#6200EA"))  # Material deep purple
        
        # Make it slightly bold for emphasis
        self.variable_format.setFontWeight(QFont.Weight.Medium)
    
    def highlightBlock(self, text):
        """Highlight {{variable}} patterns in the text."""
        # Pattern to match {{anything}}
        pattern = QRegularExpression(r'\{\{[^}]+\}\}')
        
        iterator = pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.variable_format)
    
    def set_theme(self, theme):
        """Update theme and reapply highlighting."""
        self.theme = theme
        self._setup_format()
        self.rehighlight()


class VariableHighlightDelegate(QStyledItemDelegate):
    """Syntax highlighter for {{variable}} patterns."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self._setup_format()
    
    def _setup_format(self):
        """Setup the format for variable highlighting."""
        self.variable_format = QTextCharFormat()
        
        # Color based on theme
        if self.theme == 'dark':
            # Soft purple/blue color for dark theme
            self.variable_format.setForeground(QColor("#BB86FC"))  # Material purple
        else:
            # Darker purple for light theme
            self.variable_format.setForeground(QColor("#6200EA"))  # Material deep purple
        
        # Make it slightly bold for emphasis
        self.variable_format.setFontWeight(QFont.Weight.Medium)
    
    def highlightBlock(self, text):
        """Highlight {{variable}} patterns in the text."""
        # Pattern to match {{anything}}
        pattern = QRegularExpression(r'\{\{[^}]+\}\}')
        
        iterator = pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.variable_format)
    
    def set_theme(self, theme):
        """Update theme and reapply highlighting."""
        self.theme = theme
        self._setup_format()
        self.rehighlight()


class VariableHighlightDelegate(QStyledItemDelegate):
    """Delegate for highlighting variables in table cells."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
    
    def createEditor(self, parent, option, index):
        """Create editor with variable highlighting."""
        editor = QLineEdit(parent)
        
        # Apply syntax highlighter
        highlighter = VariableSyntaxHighlighter(editor.document(), self.theme)
        
        # Store highlighter reference to prevent garbage collection
        editor._highlighter = highlighter
        
        return editor
    
    def paint(self, painter, option, index):
        """Custom paint to highlight variables in display mode."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        
        if text and '{{' in text and '}}' in text:
            # Save painter state
            painter.save()
            
            # Draw background
            if option.state & self.State.Selected:
                painter.fillRect(option.rect, option.palette.highlight())
                base_color = option.palette.highlightedText().color()
            else:
                painter.fillRect(option.rect, option.palette.base())
                base_color = option.palette.text().color()
            
            # Set font
            painter.setFont(option.font)
            
            # Variable color based on theme
            if self.theme == 'dark':
                var_color = QColor("#BB86FC")  # Material purple
            else:
                var_color = QColor("#6200EA")  # Material deep purple
            
            # Parse and draw text with highlighting
            x = option.rect.x() + 5  # Left padding
            y = option.rect.y() + option.rect.height() // 2 + painter.fontMetrics().ascent() // 2
            
            i = 0
            while i < len(text):
                if i < len(text) - 1 and text[i:i+2] == '{{':
                    # Find end of variable
                    end = text.find('}}', i + 2)
                    if end != -1:
                        # Draw variable in color
                        var_text = text[i:end+2]
                        painter.setPen(var_color)
                        painter.drawText(x, y, var_text)
                        x += painter.fontMetrics().horizontalAdvance(var_text)
                        i = end + 2
                        continue
                
                # Draw regular character
                painter.setPen(base_color)
                painter.drawText(x, y, text[i])
                x += painter.fontMetrics().horizontalAdvance(text[i])
                i += 1
            
            painter.restore()
        else:
            # No variables, use default painting
            super().paint(painter, option, index)
    
    def set_theme(self, theme):
        """Update theme."""
        self.theme = theme

