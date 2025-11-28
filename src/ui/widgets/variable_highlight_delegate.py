"""
Variable Highlight Delegate

Custom delegate and syntax highlighter for highlighting variables in the format {{variableName}}.
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit, QStyle, QToolTip, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QPainter, QFont, QPalette, QTextCursor, QCursor
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal, QRect, QPoint, QTimer
import re
from src.features.variable_substitution import VariableSubstitution


class VariableTooltipWidget(QWidget):
    """Custom tooltip widget with variable information and copy button."""
    
    def __init__(self, var_name, var_value, parent=None):
        super().__init__(parent)
        self.var_value = var_value
        self.line_edit_parent = None  # Will be set by HighlightedLineEdit
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        
        # Container with background
        container = QWidget()
        container.setObjectName("tooltipContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 6, 8, 6)
        container_layout.setSpacing(6)
        
        # Variable name label
        name_label = QLabel(f"<b>{var_name}</b>")
        name_label.setStyleSheet("color: #CCCCCC; font-size: 11px;")
        container_layout.addWidget(name_label)
        
        # Variable value label
        value_label = QLabel(var_value)
        value_label.setWordWrap(True)
        value_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-family: 'JetBrains Mono', monospace;")
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        container_layout.addWidget(value_label)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
                border-color: #007ACC;
            }
            QPushButton:pressed {
                background-color: #007ACC;
            }
        """)
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.clicked.connect(self._copy_to_clipboard)
        container_layout.addWidget(copy_btn)
        
        # Style the container
        container.setStyleSheet("""
            QWidget#tooltipContainer {
                background-color: #252526;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
            }
        """)
        
        layout.addWidget(container)
        
        # Auto-hide timer (when mouse leaves)
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)
        
        self.setMouseTracking(True)
        
        # Global event filter timer to check mouse position
        self.position_check_timer = QTimer()
        self.position_check_timer.timeout.connect(self._check_mouse_position)
        self.position_check_timer.setInterval(100)  # Check every 100ms
    
    def _copy_to_clipboard(self):
        """Copy variable value to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.var_value)
        
        # Change button text temporarily to show feedback
        sender = self.sender()
        if sender:
            original_text = sender.text()
            sender.setText("✓ Copied!")
            sender.setStyleSheet(sender.styleSheet().replace("#2D2D2D", "#2E7D32"))
            QTimer.singleShot(1000, lambda: self._reset_button(sender, original_text))
    
    def _reset_button(self, button, original_text):
        """Reset button text and style."""
        if button:
            button.setText(original_text)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    color: #CCCCCC;
                    border: 1px solid #3C3C3C;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #3C3C3C;
                    border-color: #007ACC;
                }
                QPushButton:pressed {
                    background-color: #007ACC;
                }
            """)
    
    def showEvent(self, event):
        """Tooltip shown - start position checking."""
        super().showEvent(event)
        self.position_check_timer.start()
    
    def hideEvent(self, event):
        """Tooltip hidden - stop position checking."""
        super().hideEvent(event)
        self.position_check_timer.stop()
    
    def _check_mouse_position(self):
        """Check if mouse is still over tooltip or source widget."""
        global_pos = QCursor.pos()
        
        # Check if mouse is over the tooltip itself
        if self.geometry().contains(self.mapFromGlobal(global_pos)):
            # Mouse is over tooltip - keep showing and reset grace period
            self.hide_timer.stop()
            return  # Keep showing
        
        # Check if mouse is over the line edit parent
        if self.line_edit_parent and self.line_edit_parent.isVisible():
            if self.line_edit_parent.geometry().contains(self.line_edit_parent.mapFromGlobal(global_pos)):
                # Check if still over a variable region
                local_pos = self.line_edit_parent.mapFromGlobal(global_pos)
                for region_data in self.line_edit_parent._variable_regions:
                    if len(region_data) >= 2:
                        region_rect = region_data[0]
                        if region_rect.contains(local_pos):
                            # Mouse is over variable - keep showing and reset grace period
                            self.hide_timer.stop()
                            return  # Keep showing
        
        # Mouse not over tooltip or variable region - start grace period if not already started
        if not self.hide_timer.isActive():
            self.hide_timer.start(1000)  # 1 second grace period to click copy button
    
    def enterEvent(self, event):
        """Mouse entered tooltip - cancel hide timer."""
        self.hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse left tooltip - start grace period for clicking copy button."""
        # Start 1 second grace period when leaving tooltip
        if not self.hide_timer.isActive():
            self.hide_timer.start(1000)
        super().leaveEvent(event)


class HighlightedLineEdit(QLineEdit):
    """Custom QLineEdit with variable highlighting support and hover tooltips."""
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self._setup_colors()
        self.setMouseTracking(True)  # Enable mouse tracking for hover tooltips
        self.environment_manager = None  # Will be set from main window
        self.main_window = None  # Will be set from main window
        self._variable_regions = []  # Store variable positions for hover detection
        
        # Connect text changed signal to trigger repaint
        self.textChanged.connect(self.update)
        
        # Initialize autocomplete
        from src.ui.widgets.variable_autocomplete import VariableAutocompleteWidget
        self.autocomplete_widget = VariableAutocompleteWidget(self, theme)
        self.autocomplete_widget.variableSelected.connect(self._insert_variable)
        self.autocomplete_widget.hide()
        
        # Track autocomplete state
        self._autocomplete_active = False
        self._autocomplete_start_pos = 0
        self._autocomplete_trigger = ""
        
        # Timer for debouncing filter updates
        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(self._update_autocomplete_filter)
    
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
        self.autocomplete_widget.theme = theme
        self.autocomplete_widget._setup_ui()
        self.update()
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution."""
        self.environment_manager = env_manager
    
    def set_main_window(self, main_window):
        """Set the main window reference."""
        self.main_window = main_window
    
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
    
    def _is_path_param_defined(self, param_name):
        """Check if a path parameter is defined in variables.
        Path parameters use the same variable system: extracted > collection > environment
        """
        if not self.environment_manager:
            return False
        
        # Check extracted variables first
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            if param_name in extracted_vars and extracted_vars[param_name] not in (None, '', '❌ Undefined'):
                return True
        except:
            pass
        
        # Check collection variables
        if self.main_window and hasattr(self.main_window, 'current_collection_id'):
            if self.main_window.current_collection_id and hasattr(self.main_window, 'db'):
                col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                if param_name in col_vars and col_vars[param_name] not in (None, '', '❌ Undefined'):
                    return True
        
        # Check environment variables
        if self.environment_manager.has_active_environment():
            env_vars = self.environment_manager.get_active_variables()
            if param_name in env_vars and env_vars[param_name] not in (None, '', '❌ Undefined'):
                return True
        
        return False
    
    def paintEvent(self, event):
        """Custom paint event to highlight variables and path parameters."""
        # Call the parent paint event to draw the normal text
        super().paintEvent(event)
        
        # Now paint highlights on top
        text = self.text()
        if not text or ('{{' not in text and ':' not in text):
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
            self._variable_regions.append((region_rect, var_full_ref, 'variable'))
            
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
        
        # Find all path parameters (:paramName syntax)
        path_param_pattern = re.compile(r':([a-zA-Z_][a-zA-Z0-9_]*)')
        
        for match in path_param_pattern.finditer(text):
            start_pos = match.start()
            end_pos = match.end()
            param_text = match.group(0)  # Full :paramName
            param_name = match.group(1)  # Just paramName
            
            # Calculate pixel position from start of text
            text_before = text[:start_pos]
            x_offset = fm.horizontalAdvance(text_before)
            param_width = fm.horizontalAdvance(param_text)
            
            # Calculate actual screen position accounting for scroll
            x = base_x + x_offset - scroll_offset + 6
            y = content_rect.y()
            height = content_rect.height()
            
            # Only draw if visible within the content rect
            if x + param_width < content_rect.x() or x > content_rect.right():
                continue
            
            # Store region for hover detection
            region_rect = QRect(int(x), int(y), int(param_width), int(height))
            self._variable_regions.append((region_rect, param_name, 'path_param'))
            
            # Check if path parameter is defined
            is_defined = self._is_path_param_defined(param_name)
            
            # Choose color based on whether path parameter is defined
            color = self.var_defined_color if is_defined else self.var_undefined_color
            
            # Draw rounded rectangle background behind the path parameter
            painter.setPen(Qt.PenStyle.NoPen)
            highlight_bg = QColor(color)
            highlight_bg.setAlpha(50)  # Semi-transparent background
            painter.setBrush(highlight_bg)
            
            # Draw with slight padding around the text
            padding = 2
            painter.drawRoundedRect(
                int(x - padding), 
                int(y + 2), 
                int(param_width + padding * 2), 
                int(height - 4), 
                3, 3
            )
        
        painter.end()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move to show tooltips for variables and path parameters."""
        super().mouseMoveEvent(event)
        
        # Check if mouse is over a variable or path parameter
        pos = event.pos()
        tooltip_shown = False
        
        for region_data in self._variable_regions:
            if len(region_data) == 3:
                region_rect, identifier, param_type = region_data
            else:
                # Old format (backward compatibility)
                region_rect, identifier = region_data
                param_type = 'variable'
            
            if region_rect.contains(pos):
                # Get value based on type
                if param_type == 'path_param':
                    # Path parameter - look up as variable
                    value = self._get_path_param_value(identifier)
                    display_ref = f":{identifier}"
                else:
                    # Regular variable
                    value = self._get_variable_value_by_ref(identifier)
                    display_ref = identifier
                
                # Show tooltip even if undefined (to inform user)
                if value:
                    # Apply nested variable resolution to the value (for variables only, and only if defined)
                    if param_type == 'variable' and self.environment_manager and value != "❌ Undefined":
                        env_vars = self.environment_manager.get_active_variables()
                        col_vars = {}
                        ext_vars = {}
                        
                        # Get collection vars if available
                        if hasattr(self.parent(), 'db') and hasattr(self.parent(), 'current_collection_id'):
                            col_vars = self.parent().db.get_collection_variables(self.parent().current_collection_id)
                        
                        # Get extracted vars if available
                        if hasattr(self.parent(), 'extracted_variables'):
                            ext_vars = self.parent().extracted_variables
                        
                        # Recursively resolve nested variables in the value
                        resolved_value, _ = VariableSubstitution.substitute(
                            value, 
                            env_vars, 
                            col_vars, 
                            ext_vars
                        )
                        value = resolved_value
                    
                    # Show custom tooltip with copy button
                    if not hasattr(self, '_tooltip_widget') or self._tooltip_widget is None:
                        self._tooltip_widget = VariableTooltipWidget(display_ref, value)
                        # Set the line edit as parent for proper hiding behavior
                        self._tooltip_widget.line_edit_parent = self
                    else:
                        # Update existing tooltip
                        self._tooltip_widget.var_value = value
                        self._tooltip_widget.findChild(QLabel).setText(f"<b>{display_ref}</b>")
                        value_labels = [w for w in self._tooltip_widget.findChildren(QLabel) if w.text() != f"<b>{display_ref}</b>"]
                        if value_labels:
                            value_labels[0].setText(value)
                    
                    # Cancel any pending hide timer when showing tooltip
                    if hasattr(self, '_tooltip_widget') and self._tooltip_widget:
                        self._tooltip_widget.hide_timer.stop()
                    
                    # Position tooltip near mouse
                    global_pos = event.globalPosition().toPoint()
                    self._tooltip_widget.move(global_pos.x() + 10, global_pos.y() + 10)
                    self._tooltip_widget.show()
                    tooltip_shown = True
                    break
        
        # Mouse not over any variable - tooltip hiding handled by position check timer with grace period
        # The timer will start a 1-second grace period if not already active
    
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
    
    def _get_path_param_value(self, param_name):
        """Get path parameter value from variables.
        Path parameters use the same variable system: extracted > collection > environment
        
        Args:
            param_name: Parameter name (without the : prefix)
        
        Returns:
            The parameter value or "❌ Undefined" if not found
        """
        if not self.environment_manager:
            return "❌ Undefined"
        
        # Check extracted variables first (highest priority)
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            if param_name in extracted_vars:
                return extracted_vars[param_name]
        except:
            pass
        
        # Check collection variables
        if self.main_window and hasattr(self.main_window, 'current_collection_id'):
            if self.main_window.current_collection_id and hasattr(self.main_window, 'db'):
                col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                if param_name in col_vars:
                    return col_vars[param_name]
        
        # Check environment variables (lowest priority)
        if self.environment_manager.has_active_environment():
            env_vars = self.environment_manager.get_active_variables()
            if param_name in env_vars:
                return env_vars[param_name]
        
        return "❌ Undefined"
    
    def keyPressEvent(self, event):
        """Handle key press events for autocomplete triggering."""
        key = event.key()
        text = event.text()
        
        # If autocomplete is active, handle navigation keys
        if self._autocomplete_active and self.autocomplete_widget.isVisible():
            if key in [Qt.Key.Key_Tab, Qt.Key.Key_Down, Qt.Key.Key_Up, 
                      Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape,
                      Qt.Key.Key_Backtab]:
                self.autocomplete_widget.keyPressEvent(event)
                return
            elif key == Qt.Key.Key_Backspace:
                # Handle backspace - close autocomplete if we delete the trigger
                cursor_pos = self.cursorPosition()
                if cursor_pos <= self._autocomplete_start_pos:
                    self.autocomplete_widget.hide()
                    self._autocomplete_active = False
        
        # Handle normal typing
        super().keyPressEvent(event)
        
        # Check for autocomplete triggers after text is inserted
        if text:
            self._check_autocomplete_trigger()
        
        # Update filter if autocomplete is already active
        if self._autocomplete_active and text and key not in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self._filter_timer.start(100)  # Debounce filter updates
    
    def _check_autocomplete_trigger(self):
        """Check if we should trigger autocomplete."""
        cursor_pos = self.cursorPosition()
        text = self.text()
        
        # Get text before cursor
        text_before = text[:cursor_pos]
        
        # Check for {{ trigger
        if text_before.endswith("{{"):
            self._trigger_autocomplete("{{", cursor_pos)
            return
        
        # Check for : trigger (only in URLs - look for :word pattern)
        if text_before.endswith(":"):
            # Check if this looks like a path parameter (preceded by /)
            if len(text_before) >= 2 and text_before[-2] == "/":
                self._trigger_autocomplete(":", cursor_pos)
                return
    
    def _trigger_autocomplete(self, trigger: str, pos: int):
        """Trigger the autocomplete dropdown."""
        if not self.environment_manager:
            return
        
        self._autocomplete_active = True
        self._autocomplete_start_pos = pos
        self._autocomplete_trigger = trigger
        
        # Get all available variables
        variables = self._get_all_variables()
        
        if not variables:
            return
        
        # Calculate position for dropdown (below cursor)
        cursor_rect = self.cursorRect()
        global_pos = self.mapToGlobal(cursor_rect.bottomLeft())
        global_pos.setY(global_pos.y() + 2)  # Small offset
        
        # Show autocomplete
        self.autocomplete_widget.show_autocomplete(variables, trigger, global_pos)
    
    def _update_autocomplete_filter(self):
        """Update autocomplete filter based on current text."""
        if not self._autocomplete_active:
            return
        
        cursor_pos = self.cursorPosition()
        text = self.text()
        
        # Get text after trigger
        filter_text = ""
        if cursor_pos > self._autocomplete_start_pos:
            filter_text = text[self._autocomplete_start_pos:cursor_pos]
        
        # Update filter
        self.autocomplete_widget.update_filter(filter_text)
    
    def _get_all_variables(self) -> list:
        """Get all available variables from all scopes."""
        variables = []
        
        if not self.environment_manager:
            return variables
        
        # Get extracted variables
        try:
            extracted_vars = self.environment_manager.get_extracted_variables()
            for name, value in extracted_vars.items():
                if value and value != '❌ Undefined':
                    variables.append((name, str(value), 'ext'))
        except:
            pass
        
        # Get collection variables
        try:
            from PyQt6.QtWidgets import QWidget
            parent = self.parent()
            while parent:
                if hasattr(parent, 'current_collection_id') and parent.current_collection_id:
                    if hasattr(parent, 'db'):
                        col_vars = parent.db.get_collection_variables(parent.current_collection_id)
                        for name, value in col_vars.items():
                            if value and value != '❌ Undefined':
                                variables.append((name, str(value), 'col'))
                        break
                parent = parent.parent()
        except:
            pass
        
        # Get environment variables
        try:
            if self.environment_manager.has_active_environment():
                env_vars = self.environment_manager.get_active_variables()
                for name, value in env_vars.items():
                    if value and value != '❌ Undefined':
                        variables.append((name, str(value), 'env'))
        except:
            pass
        
        # Add dynamic variables
        dynamic_vars = [
            ('guid', 'Generates a UUID v4', 'dynamic'),
            ('timestamp', 'Current Unix timestamp', 'dynamic'),
            ('isoTimestamp', 'Current ISO 8601 timestamp', 'dynamic'),
            ('randomInt', 'Random integer (0-1000)', 'dynamic'),
        ]
        variables.extend(dynamic_vars)
        
        return variables
    
    def _insert_variable(self, var_syntax: str):
        """Insert the selected variable at cursor position."""
        if not self._autocomplete_active:
            return
        
        # Get current text and cursor position
        text = self.text()
        cursor_pos = self.cursorPosition()
        
        # Calculate position before the trigger
        trigger_len = len(self._autocomplete_trigger)
        pos_before_trigger = self._autocomplete_start_pos - trigger_len
        
        # Remove trigger and text after it (the partial typing)
        text_before = text[:pos_before_trigger]
        text_after = text[cursor_pos:]
        
        # Build full syntax
        if self._autocomplete_trigger == "{{":
            full_syntax = f"{{{{{var_syntax}}}}}"
        else:  # ":"
            full_syntax = var_syntax
        
        # Construct new text
        new_text = text_before + full_syntax + text_after
        
        # Update text and cursor position
        self.setText(new_text)
        self.setCursorPosition(pos_before_trigger + len(full_syntax))
        
        # Reset autocomplete state
        self._autocomplete_active = False
        self.autocomplete_widget.hide()
    
    def focusOutEvent(self, event):
        """Hide autocomplete when focus is lost."""
        # Don't hide if focus moved to autocomplete widget
        if self.autocomplete_widget.isVisible():
            focus_widget = QApplication.focusWidget()
            if focus_widget != self.autocomplete_widget:
                self.autocomplete_widget.hide()
                self._autocomplete_active = False
        super().focusOutEvent(event)


class HighlightedTextEdit(QTextEdit):
    """QTextEdit with variable hover tooltips."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.environment_manager = None
        self.setMouseTracking(True)
        
        # Timer to delay hiding tooltip (gives time for mouse to reach tooltip)
        self._hide_tooltip_timer = QTimer()
        self._hide_tooltip_timer.setSingleShot(True)
        self._hide_tooltip_timer.timeout.connect(self._hide_tooltip_if_not_hovered)
    
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
                    # Apply nested variable resolution to the value (unless it's a dynamic variable)
                    if self.environment_manager and not value.startswith("🎲 Dynamic"):
                        env_vars = self.environment_manager.get_active_variables()
                        col_vars = {}
                        ext_vars = {}
                        
                        # Get collection vars if available
                        try:
                            from PyQt6.QtWidgets import QWidget
                            parent = self.parent()
                            while parent:
                                if hasattr(parent, 'current_collection_id') and parent.current_collection_id:
                                    if hasattr(parent, 'db'):
                                        col_vars = parent.db.get_collection_variables(parent.current_collection_id)
                                        break
                                parent = parent.parent() if isinstance(parent, QWidget) else None
                        except:
                            pass
                        
                        # Get extracted vars if available
                        try:
                            parent = self.parent()
                            while parent:
                                if hasattr(parent, 'extracted_variables'):
                                    ext_vars = parent.extracted_variables
                                    break
                                parent = parent.parent() if isinstance(parent, QWidget) else None
                        except:
                            pass
                        
                        # Recursively resolve nested variables in the value
                        resolved_value, _ = VariableSubstitution.substitute(
                            value, 
                            env_vars, 
                            col_vars, 
                            ext_vars
                        )
                        value = resolved_value
                    
                    # Show custom tooltip with copy button
                    if not hasattr(self, '_tooltip_widget') or self._tooltip_widget is None:
                        self._tooltip_widget = VariableTooltipWidget(var_ref, value)
                    else:
                        # Update existing tooltip
                        self._tooltip_widget.var_value = value
                        self._tooltip_widget.findChild(QLabel).setText(f"<b>{var_ref}</b>")
                        value_labels = [w for w in self._tooltip_widget.findChildren(QLabel) if w.text() != f"<b>{var_ref}</b>"]
                        if value_labels:
                            value_labels[0].setText(value)
                    
                    # Position tooltip near mouse
                    global_pos = event.globalPosition().toPoint()
                    self._tooltip_widget.move(global_pos.x() + 10, global_pos.y() + 10)
                    self._tooltip_widget.show()
                    
                    # Cancel any pending hide timer since we're showing tooltip
                    self._hide_tooltip_timer.stop()
                    
                    tooltip_shown = True
                    break
        
        if not tooltip_shown:
            # Don't hide immediately - give time for mouse to reach tooltip
            if hasattr(self, '_tooltip_widget') and self._tooltip_widget and self._tooltip_widget.isVisible():
                self._hide_tooltip_timer.start(150)  # 150ms delay
    
    def _hide_tooltip_if_not_hovered(self):
        """Hide tooltip only if mouse is not hovering over it."""
        if hasattr(self, '_tooltip_widget') and self._tooltip_widget:
            # Check if mouse is over the tooltip widget
            if not self._tooltip_widget.underMouse():
                self._tooltip_widget.hide()


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
        """Create editor with variable highlighting and autocomplete."""
        # Use HighlightedLineEdit for autocomplete support
        editor = HighlightedLineEdit(parent, self.theme)
        
        # Set environment manager if available
        if self.environment_manager:
            editor.set_environment_manager(self.environment_manager)
        
        # Set main window reference if available
        if self.main_window:
            editor.set_main_window(self.main_window)
        
        # Set editor background to match table cell background
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
        """Show tooltip when hovering over variables and path parameters."""
        if event.type() == event.Type.ToolTip:
            text = index.data(Qt.ItemDataRole.DisplayRole)
            
            if text:
                import re
                # Get font metrics to calculate positions
                fm = view.fontMetrics()
                
                # Calculate mouse position relative to cell
                cell_rect = view.visualRect(index)
                mouse_pos = event.pos()
                relative_x = mouse_pos.x() - cell_rect.x() - 5  # 5px left padding
                
                # Check path parameters first (:paramName syntax)
                path_param_pattern = re.compile(r':([a-zA-Z_][a-zA-Z0-9_]*)')
                for match in path_param_pattern.finditer(text):
                    text_before = text[:match.start()]
                    param_text = match.group(0)  # Full :paramName
                    param_name = match.group(1)  # Just paramName
                    
                    start_x = fm.horizontalAdvance(text_before)
                    param_width = fm.horizontalAdvance(param_text)
                    end_x = start_x + param_width
                    
                    # Check if mouse is over this path parameter
                    if start_x <= relative_x <= end_x:
                        # Get path parameter value (looks up as variable)
                        value = self._get_variable_value_for_tooltip(param_name)
                        
                        # Show tooltip even if undefined (to inform user)
                        if value:
                            # Show custom tooltip with copy button
                            if not hasattr(self, '_tooltip_widget') or self._tooltip_widget is None:
                                self._tooltip_widget = VariableTooltipWidget(param_text, value, view)
                            else:
                                # Update existing tooltip
                                self._tooltip_widget.var_value = value
                                labels = self._tooltip_widget.findChildren(QLabel)
                                if len(labels) >= 2:
                                    labels[0].setText(f"<b>{param_text}</b>")
                                    labels[1].setText(value)
                            
                            # Position tooltip near mouse
                            self._tooltip_widget.move(event.globalPos().x() + 10, event.globalPos().y() + 10)
                            self._tooltip_widget.show()
                            return True
                
                # Check {{...}} variables if no path parameter matched
                if '{{' in text and '}}' in text:
                    # Pattern matches: {{env.xxx}}, {{col.xxx}}, {{ext.xxx}}, {{$xxx}}, {{xxx}}
                    pattern = re.compile(r'\{\{(?:(env|col|ext|\$)\.)?([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
                    
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
                            
                            # Show tooltip even if undefined (to inform user)
                            if value:
                                # Show custom tooltip with copy button
                                if not hasattr(self, '_tooltip_widget') or self._tooltip_widget is None:
                                    self._tooltip_widget = VariableTooltipWidget(var_ref, value, view)
                                else:
                                    # Update existing tooltip
                                    self._tooltip_widget.var_value = value
                                    labels = self._tooltip_widget.findChildren(QLabel)
                                    if len(labels) >= 2:
                                        labels[0].setText(f"<b>{var_ref}</b>")
                                        labels[1].setText(value)
                                
                                # Position tooltip near mouse
                                self._tooltip_widget.move(event.globalPos().x() + 10, event.globalPos().y() + 10)
                                self._tooltip_widget.show()
                                return True
                
                # Mouse not over a variable, hide tooltip
                if hasattr(self, '_tooltip_widget') and self._tooltip_widget:
                    self._tooltip_widget.hide()
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

