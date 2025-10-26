"""
Variable Highlight Delegate

Custom delegate and syntax highlighter for highlighting variables in the format {{variableName}}.
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit, QStyle
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
            self.var_color = QColor("#C792EA")  # Softer purple, better contrast
            self.text_color = QColor("#CCCCCC")  # Slightly dimmed white for better contrast
            self.bg_color = QColor("#1E1E1E")  # Match global background
            self.border_color = QColor("#3C3C3C")  # Subtle border
            self.cursor_color = QColor("#FFFFFF")  # White cursor
        else:
            self.var_color = QColor("#7C4DFF")  # Vibrant but readable purple
            self.text_color = QColor("#333333")  # Dark gray
            self.bg_color = QColor("#FFFFFF")  # White background
            self.border_color = QColor("#CCCCCC")  # Light border
            self.cursor_color = QColor("#000000")  # Black cursor
    
    def set_theme(self, theme):
        """Update theme and repaint."""
        self.theme = theme
        self._setup_colors()
        self.update()
    
    def paintEvent(self, event):
        """Custom paint to highlight variables."""
        text = self.text()
        
        # If no variables, use default rendering
        if not text or '{{' not in text or '}}' not in text:
            super().paintEvent(event)
            return
        
        # Let the default paint handle background and border
        super().paintEvent(event)
        
        # Now draw text on top with highlighting
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set font
        painter.setFont(self.font())
        fm = self.fontMetrics()
        
        # Calculate text position
        contents_rect = self.contentsRect()
        x_offset = contents_rect.x() + 5
        y_baseline = contents_rect.y() + contents_rect.height() // 2 + fm.ascent() // 2 - fm.descent() // 2
        
        # Clear only the text area (not the whole background)
        text_width = fm.horizontalAdvance(text)
        text_rect = contents_rect.adjusted(0, 2, -contents_rect.width() + text_width + 10, -2)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(text_rect, self.palette().base())
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        # Get the normal text color from palette (not our custom color)
        normal_text_color = self.palette().text().color()
        
        # Draw text with highlighting
        x = x_offset
        i = 0
        
        while i < len(text):
            if i < len(text) - 1 and text[i:i+2] == '{{':
                # Find end of variable
                end = text.find('}}', i + 2)
                if end != -1:
                    # Draw variable in color
                    var_text = text[i:end+2]
                    painter.setPen(self.var_color)
                    painter.drawText(x, y_baseline, var_text)
                    x += fm.horizontalAdvance(var_text)
                    i = end + 2
                    continue
            
            # Draw regular character using palette color
            painter.setPen(normal_text_color)
            painter.drawText(x, y_baseline, text[i])
            x += fm.horizontalAdvance(text[i])
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
            if option.state & QStyle.StateFlag.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
                base_color = option.palette.highlightedText().color()
            else:
                painter.fillRect(option.rect, option.palette.base())
                base_color = option.palette.text().color()
            
            # Set font
            painter.setFont(option.font)
            
            # Variable color based on theme (matching URL bar)
            if self.theme == 'dark':
                var_color = QColor("#C792EA")  # Softer purple, better contrast
            else:
                var_color = QColor("#7C4DFF")  # Vibrant but readable purple
            
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

