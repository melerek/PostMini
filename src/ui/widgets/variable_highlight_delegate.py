"""
Variable Highlight Delegate

Custom delegate and syntax highlighter for highlighting variables in the format {{variableName}}.
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit, QStyle, QToolTip, QTextEdit
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QPainter, QFont, QPalette, QTextCursor
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
    
    def _is_variable_defined(self, var_ref):
        """Check if a variable is defined in the appropriate scope.
        
        Args:
            var_ref: Variable reference which can be:
                - "env.varname" for environment variables
                - "col.varname" for collection variables  
                - "ext.varname" for extracted variables
                - "$.varname" for dynamic variables
                - "varname" for backward compatibility (checks all scopes)
        """
        # Parse the variable reference
        if '.' in var_ref and not var_ref.startswith('$'):
            parts = var_ref.split('.', 1)
            prefix = parts[0]
            var_name = parts[1]
        else:
            prefix = None
            var_name = var_ref
        
        # Handle dynamic variables (always defined)
        if prefix == '$' or var_name.startswith('$'):
            return True
        
        if not self.environment_manager:
            return False
        
        # Handle explicit environment variables
        if prefix == 'env':
            if self.environment_manager.has_active_environment():
                env_vars = self.environment_manager.get_active_variables()
                return var_name in env_vars and env_vars[var_name] not in (None, '', '❌ Undefined')
            return False
        
        # Handle explicit collection variables
        if prefix == 'col':
            try:
                from PyQt6.QtWidgets import QWidget
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'current_collection_id') and parent.current_collection_id:
                        if hasattr(parent, 'db'):
                            col_vars = parent.db.get_collection_variables(parent.current_collection_id)
                            return var_name in col_vars and col_vars[var_name] not in (None, '', '❌ Undefined')
                    parent = parent.parent() if isinstance(parent, QWidget) else None
            except:
                pass
            return False
        
        # Handle explicit extracted variables
        if prefix == 'ext':
            try:
                extracted_vars = self.environment_manager.get_extracted_variables()
                return var_name in extracted_vars and extracted_vars[var_name] not in (None, '', '❌ Undefined')
            except:
                return False
        
        # No prefix - backward compatibility: check all scopes
        # Priority: extracted > collection > environment
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            if var_name in extracted_vars:
                return extracted_vars[var_name] not in (None, '', '❌ Undefined')
        except:
            pass
        
        try:
            from PyQt6.QtWidgets import QWidget
            parent = self.parent()
            while parent:
                if hasattr(parent, 'current_collection_id') and parent.current_collection_id:
                    if hasattr(parent, 'db'):
                        col_vars = parent.db.get_collection_variables(parent.current_collection_id)
                        if var_name in col_vars:
                            return col_vars[var_name] not in (None, '', '❌ Undefined')
                parent = parent.parent() if isinstance(parent, QWidget) else None
        except:
            pass
        
        if self.environment_manager.has_active_environment():
            env_vars = self.environment_manager.get_active_variables()
            if var_name in env_vars:
                return env_vars[var_name] not in (None, '', '❌ Undefined')
        
        return False
    
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
        
        # Find all variables with new prefix syntax
        # Pattern matches: {{env.var}}, {{col.var}}, {{ext.var}}, {{$var}}, {{var}}
        pattern = re.compile(r'\{\{(?:(env|col|ext|\$)\.)?([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
        self._variable_regions = []  # Clear previous regions
        
        for match in pattern.finditer(text):
            start_pos = match.start()
            end_pos = match.end()
            var_text = match.group(0)
            # Extract prefix and variable name
            prefix = match.group(1)  # env, col, ext, $ or None
            var_name = match.group(2)  # The variable name
            
            # Build full variable reference for lookup
            if prefix:
                var_full_ref = f"{prefix}.{var_name}"
            else:
                var_full_ref = var_name
            
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
            self._variable_regions.append((region_rect, var_full_ref))
            
            # Check if variable is defined (using full reference with prefix)
            is_defined = self._is_variable_defined(var_full_ref)
            
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
        
        for region_rect, var_ref in self._variable_regions:
            if region_rect.contains(pos):
                # Get variable value using new prefix-based lookup
                value = self._get_variable_value_by_ref(var_ref)
                
                if value and value != "❌ Undefined":
                    # Show tooltip with scope information
                    tooltip_text = f"<b>{var_ref}</b><br/><span style='color: #4CAF50;'>{value}</span>"
                    QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
                    tooltip_shown = True
                    break
        
        if not tooltip_shown:
            QToolTip.hideText()
    
    def _get_variable_value_by_ref(self, var_ref):
        """Get variable value based on reference with prefix.
        
        Args:
            var_ref: Variable reference like "env.varname", "col.varname", "ext.varname", "$.varname", or "varname"
        
        Returns:
            The variable value or "❌ Undefined" if not found
        """
        # Parse the variable reference
        if '.' in var_ref and not var_ref.startswith('$'):
            parts = var_ref.split('.', 1)
            prefix = parts[0]
            var_name = parts[1]
        else:
            prefix = None
            var_name = var_ref
        
        # Handle dynamic variables
        if prefix == '$' or var_name.startswith('$'):
            return f"🎲 Dynamic: {var_ref} (auto-generated at request time)"
        
        if not self.environment_manager:
            return "❌ Undefined"
        
        # Handle explicit environment variables
        if prefix == 'env':
            if self.environment_manager.has_active_environment():
                env_vars = self.environment_manager.get_active_variables()
                return env_vars.get(var_name, "❌ Undefined")
            return "❌ Undefined (No active environment)"
        
        # Handle explicit collection variables
        if prefix == 'col':
            try:
                from PyQt6.QtWidgets import QWidget
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'current_collection_id') and parent.current_collection_id:
                        if hasattr(parent, 'db'):
                            col_vars = parent.db.get_collection_variables(parent.current_collection_id)
                            return col_vars.get(var_name, "❌ Undefined")
                    parent = parent.parent() if isinstance(parent, QWidget) else None
            except:
                pass
            return "❌ Undefined (No collection variables)"
        
        # Handle explicit extracted variables
        if prefix == 'ext':
            try:
                extracted_vars = self.environment_manager.get_extracted_variables()
                return extracted_vars.get(var_name, "❌ Undefined")
            except:
                return "❌ Undefined (No extracted variables)"
        
        # No prefix - backward compatibility: check all scopes
        # Priority: extracted > collection > environment
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            if var_name in extracted_vars:
                return extracted_vars[var_name]
        except:
            pass
        
        try:
            from PyQt6.QtWidgets import QWidget
            parent = self.parent()
            while parent:
                if hasattr(parent, 'current_collection_id') and parent.current_collection_id:
                    if hasattr(parent, 'db'):
                        col_vars = parent.db.get_collection_variables(parent.current_collection_id)
                        if var_name in col_vars:
                            return col_vars[var_name]
                parent = parent.parent() if isinstance(parent, QWidget) else None
        except:
            pass
        
        if self.environment_manager.has_active_environment():
            env_vars = self.environment_manager.get_active_variables()
            if var_name in env_vars:
                return env_vars[var_name]
        
        return "❌ Undefined"


class HighlightedTextEdit(QTextEdit):
    """QTextEdit with variable hover tooltips."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.environment_manager = None
        self.setMouseTracking(True)
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution."""
        self.environment_manager = env_manager
    
    def _get_variable_value(self, var_ref):
        """Get the value of a variable using prefix-based lookup.
        
        Args:
            var_ref: Variable reference like "env.varname", "col.varname", "ext.varname", "$.varname", or "varname"
        
        Returns:
            The variable value or "❌ Undefined" if not found
        """
        # Parse the variable reference
        if '.' in var_ref and not var_ref.startswith('$'):
            parts = var_ref.split('.', 1)
            prefix = parts[0]
            var_name = parts[1]
        else:
            prefix = None
            var_name = var_ref
        
        # Handle dynamic variables
        if prefix == '$' or var_name.startswith('$'):
            return f"🎲 Dynamic: {var_ref} (auto-generated at request time)"
        
        if not self.environment_manager:
            return "❌ Undefined"
        
        # Handle explicit environment variables
        if prefix == 'env':
            if self.environment_manager.has_active_environment():
                env_vars = self.environment_manager.get_active_variables()
                return env_vars.get(var_name, "❌ Undefined")
            return "❌ Undefined (No active environment)"
        
        # Handle explicit collection variables
        if prefix == 'col':
            try:
                from PyQt6.QtWidgets import QWidget
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'current_collection_id') and parent.current_collection_id:
                        if hasattr(parent, 'db'):
                            col_vars = parent.db.get_collection_variables(parent.current_collection_id)
                            return col_vars.get(var_name, "❌ Undefined")
                    parent = parent.parent() if isinstance(parent, QWidget) else None
            except:
                pass
            return "❌ Undefined (No collection variables)"
        
        # Handle explicit extracted variables
        if prefix == 'ext':
            try:
                extracted_vars = self.environment_manager.get_extracted_variables()
                return extracted_vars.get(var_name, "❌ Undefined")
            except:
                return "❌ Undefined (No extracted variables)"
        
        # No prefix - backward compatibility: check all scopes
        # Priority: extracted > collection > environment
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            if var_name in extracted_vars:
                return extracted_vars[var_name]
        except:
            pass
        
        try:
            from PyQt6.QtWidgets import QWidget
            parent = self.parent()
            while parent:
                if hasattr(parent, 'current_collection_id') and parent.current_collection_id:
                    if hasattr(parent, 'db'):
                        col_vars = parent.db.get_collection_variables(parent.current_collection_id)
                        if var_name in col_vars:
                            return col_vars[var_name]
                parent = parent.parent() if isinstance(parent, QWidget) else None
        except:
            pass
        
        if self.environment_manager.has_active_environment():
            env_vars = self.environment_manager.get_active_variables()
            if var_name in env_vars:
                return env_vars[var_name]
        
        return "❌ Undefined"
    
    def mouseMoveEvent(self, event):
        """Handle mouse move to show tooltips for variables."""
        super().mouseMoveEvent(event)
        
        # Get the cursor position under the mouse
        cursor = self.cursorForPosition(event.pos())
        
        # Get the text of the current block (line)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        text = cursor.selectedText()
        
        # Find all variables with new prefix syntax
        # Pattern matches: {{env.xxx}}, {{col.xxx}}, {{ext.xxx}}, {{$xxx}}, {{xxx}}
        pattern = re.compile(r'\{\{(?:(env|col|ext|\$)\.)?([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
        
        # Get the position in the block
        position_in_block = self.cursorForPosition(event.pos()).positionInBlock()
        
        tooltip_shown = False
        for match in pattern.finditer(text):
            start = match.start()
            end = match.end()
            
            # Check if mouse is over this variable
            if start <= position_in_block <= end:
                # Extract prefix and variable name
                prefix = match.group(1)  # env, col, ext, $ or None
                var_name = match.group(2)  # The variable name
                
                # Build full variable reference for lookup
                if prefix:
                    var_ref = f"{prefix}.{var_name}"
                else:
                    var_ref = var_name
                
                # Get variable value
                value = self._get_variable_value(var_ref)
                
                if value and value != "❌ Undefined":
                    # Show tooltip
                    tooltip_text = f"<b>{var_ref}</b><br/><span style='color: #4CAF50;'>{value}</span>"
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
        self.environment_manager = None  # Will be set from main window
        self._setup_formats()
    
    def _setup_formats(self):
        """Setup the formats for variable highlighting."""
        # Format for defined variables (green)
        self.defined_format = QTextCharFormat()
        # Format for undefined variables (red)
        self.undefined_format = QTextCharFormat()
        
        # Color based on theme
        if self.theme == 'dark':
            # Green for defined variables
            self.defined_format.setForeground(QColor("#4CAF50"))
            # Red for undefined variables
            self.undefined_format.setForeground(QColor("#F44336"))
        else:
            # Dark green for defined variables (light theme)
            self.defined_format.setForeground(QColor("#2E7D32"))
            # Dark red for undefined variables (light theme)
            self.undefined_format.setForeground(QColor("#D32F2F"))
        
        # Make both slightly bold for emphasis
        self.defined_format.setFontWeight(QFont.Weight.Medium)
        self.undefined_format.setFontWeight(QFont.Weight.Medium)
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution."""
        self.environment_manager = env_manager
        self.rehighlight()
    
    def _is_variable_defined(self, var_ref):
        """Check if a variable is defined in the appropriate scope.
        
        Args:
            var_ref: Variable reference which can be:
                - "env.varname" for environment variables
                - "col.varname" for collection variables  
                - "ext.varname" for extracted variables
                - "$.varname" for dynamic variables
                - "varname" for backward compatibility (checks all scopes)
        """
        # Parse the variable reference
        if '.' in var_ref and not var_ref.startswith('$'):
            parts = var_ref.split('.', 1)
            prefix = parts[0]
            var_name = parts[1]
        else:
            prefix = None
            var_name = var_ref
        
        # Handle dynamic variables (always defined)
        if prefix == '$' or var_name.startswith('$'):
            return True
        
        if not self.environment_manager:
            return False
        
        # Handle explicit environment variables
        if prefix == 'env':
            if self.environment_manager.has_active_environment():
                env_vars = self.environment_manager.get_active_variables()
                return var_name in env_vars
            return False
        
        # Handle explicit collection variables (try to get from parent)
        if prefix == 'col':
            try:
                # Try to find parent with collection variables access
                if hasattr(self, 'parent') and callable(self.parent):
                    parent_obj = self.parent()
                    while parent_obj:
                        if hasattr(parent_obj, 'current_collection_id') and parent_obj.current_collection_id:
                            if hasattr(parent_obj, 'db'):
                                col_vars = parent_obj.db.get_collection_variables(parent_obj.current_collection_id)
                                return var_name in col_vars
                        parent_obj = parent_obj.parent() if hasattr(parent_obj, 'parent') and callable(parent_obj.parent) else None
            except:
                pass
            return False
        
        # Handle explicit extracted variables
        if prefix == 'ext':
            try:
                extracted_vars = self.environment_manager.get_extracted_variables()
                return var_name in extracted_vars
            except:
                return False
        
        # No prefix - backward compatibility: check all scopes
        # Priority: extracted > collection > environment
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            if var_name in extracted_vars:
                return True
        except:
            pass
        
        try:
            if hasattr(self, 'parent') and callable(self.parent):
                parent_obj = self.parent()
                while parent_obj:
                    if hasattr(parent_obj, 'current_collection_id') and parent_obj.current_collection_id:
                        if hasattr(parent_obj, 'db'):
                            col_vars = parent_obj.db.get_collection_variables(parent_obj.current_collection_id)
                            if var_name in col_vars:
                                return True
                    parent_obj = parent_obj.parent() if hasattr(parent_obj, 'parent') and callable(parent_obj.parent) else None
        except:
            pass
        
        if self.environment_manager.has_active_environment():
            env_vars = self.environment_manager.get_active_variables()
            if var_name in env_vars:
                return True
        
        return False
    
    def highlightBlock(self, text):
        """Highlight variable patterns with new prefix syntax."""
        from PyQt6.QtCore import QRegularExpression
        
        # Pattern to match {{prefix.variable}} or {{variable}} or {{$variable}}
        # Matches: {{env.xxx}}, {{col.xxx}}, {{ext.xxx}}, {{$xxx}}, {{xxx}}
        pattern_braces = QRegularExpression(r'\{\{(?:(env|col|ext|\$)\.)?([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
        iterator = pattern_braces.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            prefix = match.captured(1)  # env, col, ext, $ or empty
            var_name = match.captured(2)  # The variable name
            
            # Build full variable reference for lookup
            if prefix:
                var_full_ref = f"{prefix}.{var_name}"
            else:
                var_full_ref = var_name
            
            # Check if variable is defined
            is_defined = self._is_variable_defined(var_full_ref)
            
            # Apply appropriate format
            format_to_use = self.defined_format if is_defined else self.undefined_format
            self.setFormat(match.capturedStart(), match.capturedLength(), format_to_use)
    
    def set_theme(self, theme):
        """Update theme and reapply highlighting."""
        self.theme = theme
        self._setup_formats()
        self.rehighlight()


class VariableHighlightDelegate(QStyledItemDelegate):
    """Delegate for highlighting variables in table cells."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self.environment_manager = None  # Will be set from main window
        self.main_window = None  # Store reference to main window for collection variables
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution."""
        self.environment_manager = env_manager
    
    def set_main_window(self, main_window):
        """Set the main window reference for accessing collection variables."""
        self.main_window = main_window
    
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
            
            # Use regex to find variables with new prefix syntax
            import re
            pattern = re.compile(r'\{\{(?:(env|col|ext|\$)\.)?([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
            
            last_end = 0
            for match in pattern.finditer(text):
                # Draw text before variable
                before_text = text[last_end:match.start()]
                if before_text:
                    painter.setPen(base_color)
                    painter.drawText(x, y, before_text)
                    x += painter.fontMetrics().horizontalAdvance(before_text)
                
                # Extract variable info
                prefix = match.group(1)  # env, col, ext, $ or None
                var_name = match.group(2)  # The variable name
                var_text = match.group(0)  # Full text like {{col.xxx}}
                
                # Build full variable reference
                if prefix:
                    var_ref = f"{prefix}.{var_name}"
                else:
                    var_ref = var_name
                
                # Check if variable is defined
                is_defined = self._is_variable_defined(var_ref)
                
                # Choose color based on whether variable is defined
                if self.theme == 'dark':
                    var_color = QColor("#4CAF50") if is_defined else QColor("#F44336")
                else:
                    var_color = QColor("#2E7D32") if is_defined else QColor("#D32F2F")
                
                # Draw variable in appropriate color
                painter.setPen(var_color)
                painter.drawText(x, y, var_text)
                x += painter.fontMetrics().horizontalAdvance(var_text)
                
                last_end = match.end()
            
            # Draw remaining text after last variable
            remaining_text = text[last_end:]
            if remaining_text:
                painter.setPen(base_color)
                painter.drawText(x, y, remaining_text)
            
            painter.restore()
        else:
            # No variables - let Qt handle everything with standard rendering
            style = opt.widget.style() if opt.widget else QStyle()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
    
    def set_theme(self, theme):
        """Update theme."""
        self.theme = theme
    
    def _is_variable_defined(self, var_ref):
        """Check if a variable is defined using prefix-based lookup.
        
        Args:
            var_ref: Variable reference like "env.varname", "col.varname", "ext.varname", "$.varname", or "varname"
        
        Returns:
            True if defined, False otherwise
        """
        # Parse the variable reference
        if '.' in var_ref and not var_ref.startswith('$'):
            parts = var_ref.split('.', 1)
            prefix = parts[0]
            var_name = parts[1]
        else:
            prefix = None
            var_name = var_ref
        
        # Handle dynamic variables (always defined)
        if prefix == '$' or var_name.startswith('$'):
            return True
        
        if not self.environment_manager:
            return False
        
        # Handle explicit environment variables
        if prefix == 'env':
            if self.environment_manager.has_active_environment():
                env_vars = self.environment_manager.get_active_variables()
                return var_name in env_vars and env_vars[var_name] not in (None, '', '❌ Undefined')
            return False
        
        # Handle explicit collection variables
        if prefix == 'col':
            if self.main_window and hasattr(self.main_window, 'current_collection_id'):
                if self.main_window.current_collection_id and hasattr(self.main_window, 'db'):
                    col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                    return var_name in col_vars and col_vars[var_name] not in (None, '', '❌ Undefined')
            return False
        
        # Handle explicit extracted variables
        if prefix == 'ext':
            try:
                extracted_vars = self.environment_manager.get_extracted_variables()
                return var_name in extracted_vars and extracted_vars[var_name] not in (None, '', '❌ Undefined')
            except:
                return False
        
        # No prefix - backward compatibility: check all scopes
        # Priority: extracted > collection > environment
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            if var_name in extracted_vars:
                return extracted_vars[var_name] not in (None, '', '❌ Undefined')
        except:
            pass
        
        if self.main_window and hasattr(self.main_window, 'current_collection_id'):
            if self.main_window.current_collection_id and hasattr(self.main_window, 'db'):
                col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                if var_name in col_vars:
                    return col_vars[var_name] not in (None, '', '❌ Undefined')
        
        if self.environment_manager.has_active_environment():
            env_vars = self.environment_manager.get_active_variables()
            if var_name in env_vars:
                return env_vars[var_name] not in (None, '', '❌ Undefined')
        
        return False
    
    def helpEvent(self, event, view, option, index):
        """Show tooltip when hovering over variables."""
        if event.type() == event.Type.ToolTip:
            text = index.data(Qt.ItemDataRole.DisplayRole)
            
            if text and '{{' in text and '}}' in text:
                # Find if mouse is over a variable with new prefix syntax
                import re
                # Pattern matches: {{env.xxx}}, {{col.xxx}}, {{ext.xxx}}, {{$xxx}}, {{xxx}}
                pattern = re.compile(r'\{\{(?:(env|col|ext|\$)\.)?([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
                
                # Get font metrics to calculate positions
                fm = view.fontMetrics()
                
                # Calculate mouse position relative to cell
                cell_rect = view.visualRect(index)
                mouse_pos = event.pos()
                relative_x = mouse_pos.x() - cell_rect.x() - 5  # 5px left padding
                
                # Check each variable
                for match in pattern.finditer(text):
                    # Calculate position of text before this variable
                    text_before = text[:match.start()]
                    var_text = match.group(0)
                    prefix = match.group(1)  # env, col, ext, $ or None
                    var_name = match.group(2)  # The variable name
                    
                    # Build full variable reference
                    if prefix:
                        var_ref = f"{prefix}.{var_name}"
                    else:
                        var_ref = var_name
                    
                    start_x = fm.horizontalAdvance(text_before)
                    var_width = fm.horizontalAdvance(var_text)
                    end_x = start_x + var_width
                    
                    # Check if mouse is over this variable
                    if start_x <= relative_x <= end_x:
                        # Get variable value using prefix-based lookup
                        value = self._get_variable_value_for_tooltip(var_ref)
                        
                        if value and value != "❌ Undefined":
                            # Show tooltip
                            tooltip_text = f"<b>{var_ref}</b><br/><span style='color: #4CAF50;'>{value}</span>"
                            QToolTip.showText(event.globalPos(), tooltip_text, view)
                            return True
                
                # Mouse not over a variable, hide tooltip
                QToolTip.hideText()
                return True
        
        return super().helpEvent(event, view, option, index)
    
    def _get_variable_value_for_tooltip(self, var_ref):
        """Get variable value for tooltip using prefix-based lookup.
        
        Args:
            var_ref: Variable reference like "env.varname", "col.varname", "ext.varname", "$.varname", or "varname"
        
        Returns:
            The variable value or "❌ Undefined" if not found
        """
        # Parse the variable reference
        if '.' in var_ref and not var_ref.startswith('$'):
            parts = var_ref.split('.', 1)
            prefix = parts[0]
            var_name = parts[1]
        else:
            prefix = None
            var_name = var_ref
        
        # Handle dynamic variables
        if prefix == '$' or var_name.startswith('$'):
            return f"🎲 Dynamic (auto-generated)"
        
        if not self.environment_manager:
            return "❌ Undefined"
        
        # Handle explicit environment variables
        if prefix == 'env':
            if self.environment_manager.has_active_environment():
                env_vars = self.environment_manager.get_active_variables()
                return env_vars.get(var_name, "❌ Undefined")
            return "❌ Undefined (No active environment)"
        
        # Handle explicit collection variables
        if prefix == 'col':
            if self.main_window and hasattr(self.main_window, 'current_collection_id'):
                if self.main_window.current_collection_id and hasattr(self.main_window, 'db'):
                    col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                    return col_vars.get(var_name, "❌ Undefined")
            return "❌ Undefined (No collection variables)"
        
        # Handle explicit extracted variables
        if prefix == 'ext':
            try:
                extracted_vars = self.environment_manager.get_extracted_variables()
                return extracted_vars.get(var_name, "❌ Undefined")
            except:
                return "❌ Undefined (No extracted variables)"
        
        # No prefix - backward compatibility: check all scopes
        # Priority: extracted > collection > environment
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            if var_name in extracted_vars:
                return extracted_vars[var_name]
        except:
            pass
        
        if self.main_window and hasattr(self.main_window, 'current_collection_id'):
            if self.main_window.current_collection_id and hasattr(self.main_window, 'db'):
                col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                if var_name in col_vars:
                    return col_vars[var_name]
        
        if self.environment_manager.has_active_environment():
            env_vars = self.environment_manager.get_active_variables()
            if var_name in env_vars:
                return env_vars[var_name]
        
        return "❌ Undefined"

