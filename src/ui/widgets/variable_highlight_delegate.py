"""
Variable Highlight Delegate

Custom delegate and syntax highlighter for highlighting variables in the format {{variableName}}.
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit, QStyle, QToolTip
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QPainter, QFont, QPalette
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal, QRect, QPoint
import re


class HighlightedLineEdit(QLineEdit):
    """Custom QLineEdit with variable highlighting support and hover tooltips."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self._setup_colors()
        self.setMouseTracking(True)  # Enable mouse tracking for hover tooltips
        self.environment_manager = None  # Will be set from main window
        self._variable_regions = []  # Store variable positions for hover detection
        
        # Connect text changed signal to trigger repaint
        self.textChanged.connect(self.update)
    
    def _setup_colors(self):
        """Setup colors based on theme."""
        if self.theme == 'dark':
            self.var_defined_color = QColor("#4CAF50")  # Green for defined variables
            self.var_undefined_color = QColor("#F44336")  # Red for undefined variables
            self.text_color = QColor("#CCCCCC")  # Slightly dimmed white for better contrast
            self.bg_color = QColor("#1E1E1E")  # Match global background
            self.border_color = QColor("#3C3C3C")  # Subtle border
            self.cursor_color = QColor("#FFFFFF")  # White cursor
        else:
            self.var_defined_color = QColor("#2E7D32")  # Dark green for defined variables
            self.var_undefined_color = QColor("#D32F2F")  # Dark red for undefined variables
            self.text_color = QColor("#333333")  # Dark gray
            self.bg_color = QColor("#FFFFFF")  # White background
            self.border_color = QColor("#CCCCCC")  # Light border
            self.cursor_color = QColor("#000000")  # Black cursor
    
    def set_theme(self, theme):
        """Update theme and repaint."""
        self.theme = theme
        self._setup_colors()
        self.update()
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution."""
        self.environment_manager = env_manager
    
    def _is_variable_defined(self, var_name):
        """Check if a variable is defined in the environment manager."""
        if not self.environment_manager:
            return False
        
        # Get all active variables
        all_vars = {}
        try:
            all_vars = self.environment_manager.get_active_variables()
            
            # Also check collection variables if available
            if hasattr(self.environment_manager, 'collection_variables'):
                all_vars.update(self.environment_manager.collection_variables)
            
            # Check extracted variables
            if hasattr(self.environment_manager, 'extracted_variables'):
                for ev in self.environment_manager.extracted_variables:
                    all_vars[ev['name']] = ev['value']
        except:
            return False
        
        # Check if variable name exists and has a non-empty value
        return var_name in all_vars and all_vars[var_name] not in (None, '', '❌ Undefined')
    
    def paintEvent(self, event):
        """Custom paint event to highlight variables."""
        # Call the parent paint event to draw the normal text
        super().paintEvent(event)
        
        # Now paint highlights on top
        text = self.text()
        if not text or '{{' not in text or '}}' not in text:
            self._variable_regions = []  # Clear regions when no variables
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get font metrics
        fm = self.fontMetrics()
        
        # Get the text margins that Qt uses internally
        text_margins = self.textMargins()
        left_margin = text_margins.left()
        
        # Get content rect
        content_rect = self.contentsRect()
        
        # Calculate the base x position where text starts
        # For QLineEdit, we need to account for alignment and internal padding
        base_x = content_rect.x() + left_margin + 3  # 3px is Qt's internal padding
        
        # Get the cursor position to determine scroll offset
        # The key insight: use cursorPositionAt to find where the displayed text starts
        cursor_pos = self.cursorPosition()
        
        # Calculate how much the text is scrolled
        # When text is longer than the visible area, Qt scrolls it
        # We can estimate this by checking if cursor would be outside visible area
        text_width = fm.horizontalAdvance(text)
        visible_width = content_rect.width() - left_margin - 6
        
        # Calculate scroll offset: how many pixels the text has scrolled to the left
        scroll_offset = 0
        if text_width > visible_width:
            # Text is scrolled - calculate based on cursor position
            cursor_pixel_pos = fm.horizontalAdvance(text[:cursor_pos])
            if cursor_pixel_pos > visible_width - 20:  # Keep cursor visible with 20px margin
                scroll_offset = cursor_pixel_pos - (visible_width - 20)
        
        # Find all variables
        pattern = re.compile(r'\{\{([^}]+)\}\}')
        self._variable_regions = []  # Clear previous regions
        
        for match in pattern.finditer(text):
            start_pos = match.start()
            end_pos = match.end()
            var_text = match.group(0)
            var_name = match.group(1)  # Variable name without braces
            
            # Calculate pixel position from start of text
            text_before = text[:start_pos]
            x_offset = fm.horizontalAdvance(text_before)
            var_width = fm.horizontalAdvance(var_text)
            
            # Calculate actual screen position accounting for scroll
            # Add 6px to better align with the actual text rendering
            x = base_x + x_offset - scroll_offset + 6
            y = content_rect.y()
            height = content_rect.height()
            
            # Only draw if visible within the content rect
            if x + var_width < content_rect.x() or x > content_rect.right():
                continue
            
            # Store region for hover detection
            region_rect = QRect(int(x), int(y), int(var_width), int(height))
            self._variable_regions.append((region_rect, var_name))
            
            # Check if variable is defined
            is_defined = self._is_variable_defined(var_name)
            
            # Choose color based on whether variable is defined
            color = self.var_defined_color if is_defined else self.var_undefined_color
            
            # Draw rounded rectangle background behind the variable
            # The original text will show through - we only highlight the background
            painter.setPen(Qt.PenStyle.NoPen)
            highlight_bg = QColor(color)
            highlight_bg.setAlpha(50)  # Semi-transparent background
            painter.setBrush(highlight_bg)
            
            # Draw with slight padding around the text
            padding = 2
            painter.drawRoundedRect(
                int(x - padding), 
                int(y + 2), 
                int(var_width + padding * 2), 
                int(height - 4), 
                3, 3
            )
        
        painter.end()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move to show tooltips for variables."""
        super().mouseMoveEvent(event)
        
        # Check if mouse is over a variable
        pos = event.pos()
        tooltip_shown = False
        
        for region_rect, var_name in self._variable_regions:
            if region_rect.contains(pos):
                # Get variable value
                if self.environment_manager:
                    # Get all active variables
                    all_vars = self.environment_manager.get_active_variables()
                    
                    # Also get collection variables if available
                    if hasattr(self.environment_manager, 'collection_variables'):
                        all_vars.update(self.environment_manager.collection_variables)
                    
                    # Get extracted variables
                    if hasattr(self.environment_manager, 'extracted_variables'):
                        for ev in self.environment_manager.extracted_variables:
                            all_vars[ev['name']] = ev['value']
                    
                    # Get value
                    value = all_vars.get(var_name, "❌ Undefined")
                    
                    # Show tooltip
                    tooltip_text = f"<b>{var_name}</b><br/><span style='color: #4CAF50;'>{value}</span>"
                    QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
                    tooltip_shown = True
                    break
        
        if not tooltip_shown:
            QToolTip.hideText()


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
    """Delegate for highlighting variables in table cells."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self.environment_manager = None  # Will be set from main window
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution."""
        self.environment_manager = env_manager
    
    def createEditor(self, parent, option, index):
        """Create editor with variable highlighting."""
        editor = QLineEdit(parent)
        
        # Set editor background to match table cell background (dark theme)
        if self.theme == 'dark':
            editor.setStyleSheet("""
                QLineEdit {
                    background-color: #2D2D2D;
                    color: #CCCCCC;
                    border: none;
                    padding: 0px;
                    margin: 0px;
                    selection-background-color: #1E1E1E;
                    selection-color: #FFFFFF;
                }
            """)
        else:
            editor.setStyleSheet("""
                QLineEdit {
                    background-color: #FFFFFF;
                    color: #333333;
                    border: none;
                    padding: 0px;
                    margin: 0px;
                    selection-background-color: #E0E0E0;
                    selection-color: #000000;
                }
            """)
        
        # Note: QLineEdit doesn't support QSyntaxHighlighter (that's for QTextEdit only)
        # Variables will be highlighted only in display mode via paint()
        
        return editor
    
    def paint(self, painter, option, index):
        """Custom paint to highlight variables in display mode."""
        from PyQt6.QtWidgets import QStyleOptionViewItem, QStyle
        
        # Clone and initialize the option properly
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        
        # If selected, set dark theme selection colors in the palette
        if opt.state & QStyle.StateFlag.State_Selected:
            if self.theme == 'dark':
                # Set very dark selection background (similar to header)
                opt.palette.setColor(QPalette.ColorRole.Highlight, QColor("#1E1E1E"))
                opt.palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#CCCCCC"))
            else:
                # Light theme
                opt.palette.setColor(QPalette.ColorRole.Highlight, QColor("#E0E0E0"))
                opt.palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#333333"))
        
        text = index.data(Qt.ItemDataRole.DisplayRole)
        
        # If cell has variables, do custom text rendering
        if text and '{{' in text and '}}' in text:
            # Clear the text from opt so Qt doesn't draw it (we'll draw it ourselves)
            opt.text = ""
            
            # Let Qt draw the background and base styling (without text)
            style = opt.widget.style() if opt.widget else QStyle()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
            
            # Now draw our custom variable-highlighted text
            painter.save()
            painter.setFont(opt.font)
            
            # Determine text colors
            if opt.state & QStyle.StateFlag.State_Selected:
                base_color = opt.palette.color(QPalette.ColorRole.HighlightedText)
            else:
                base_color = opt.palette.color(QPalette.ColorRole.Text)
            
            # Parse and draw text with variable highlighting
            x = opt.rect.x() + 5  # Left padding
            y = opt.rect.y() + opt.rect.height() // 2 + painter.fontMetrics().ascent() // 2
            
            i = 0
            while i < len(text):
                if i < len(text) - 1 and text[i:i+2] == '{{':
                    # Find end of variable
                    end = text.find('}}', i + 2)
                    if end != -1:
                        # Extract variable name
                        var_text = text[i:end+2]
                        var_name = text[i+2:end]  # Variable name without braces
                        
                        # Check if variable is defined
                        is_defined = self._is_variable_defined(var_name)
                        
                        # Choose color based on whether variable is defined
                        if self.theme == 'dark':
                            var_color = QColor("#4CAF50") if is_defined else QColor("#F44336")
                        else:
                            var_color = QColor("#2E7D32") if is_defined else QColor("#D32F2F")
                        
                        # Draw variable in appropriate color
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
            # No variables - let Qt handle everything with standard rendering
            style = opt.widget.style() if opt.widget else QStyle()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
    
    def set_theme(self, theme):
        """Update theme."""
        self.theme = theme
    
    def _is_variable_defined(self, var_name):
        """Check if a variable is defined in the environment manager."""
        if not self.environment_manager:
            return False
        
        # Get all active variables
        all_vars = {}
        try:
            all_vars = self.environment_manager.get_active_variables()
            
            # Also check collection variables if available
            if hasattr(self.environment_manager, 'collection_variables'):
                all_vars.update(self.environment_manager.collection_variables)
            
            # Check extracted variables
            if hasattr(self.environment_manager, 'extracted_variables'):
                for ev in self.environment_manager.extracted_variables:
                    all_vars[ev['name']] = ev['value']
        except:
            return False
        
        # Check if variable name exists and has a non-empty value
        return var_name in all_vars and all_vars[var_name] not in (None, '', '❌ Undefined')
    
    def helpEvent(self, event, view, option, index):
        """Show tooltip when hovering over variables."""
        if event.type() == event.Type.ToolTip:
            text = index.data(Qt.ItemDataRole.DisplayRole)
            
            if text and '{{' in text and '}}' in text:
                # Find if mouse is over a variable
                import re
                pattern = re.compile(r'\{\{([^}]+)\}\}')
                
                # Get font metrics to calculate positions
                fm = view.fontMetrics()
                
                # Calculate mouse position relative to cell
                cell_rect = view.visualRect(index)
                mouse_pos = event.pos()
                relative_x = mouse_pos.x() - cell_rect.x() - 5  # 5px left padding
                
                # Check each variable
                current_x = 0
                for match in pattern.finditer(text):
                    # Calculate position of text before this variable
                    text_before = text[:match.start()]
                    var_text = match.group(0)
                    var_name = match.group(1)
                    
                    start_x = fm.horizontalAdvance(text_before)
                    var_width = fm.horizontalAdvance(var_text)
                    end_x = start_x + var_width
                    
                    # Check if mouse is over this variable
                    if start_x <= relative_x <= end_x:
                        # Get variable value
                        if self.environment_manager:
                            # Get all active variables
                            all_vars = self.environment_manager.get_active_variables()
                            
                            # Also get collection variables if available
                            if hasattr(self.environment_manager, 'collection_variables'):
                                all_vars.update(self.environment_manager.collection_variables)
                            
                            # Get extracted variables
                            if hasattr(self.environment_manager, 'extracted_variables'):
                                for ev in self.environment_manager.extracted_variables:
                                    all_vars[ev['name']] = ev['value']
                            
                            # Get value
                            value = all_vars.get(var_name, "❌ Undefined")
                            
                            # Show tooltip
                            tooltip_text = f"<b>{var_name}</b><br/><span style='color: #4CAF50;'>{value}</span>"
                            QToolTip.showText(event.globalPos(), tooltip_text, view)
                            return True
                
                # Mouse not over a variable, hide tooltip
                QToolTip.hideText()
                return True
        
        return super().helpEvent(event, view, option, index)

