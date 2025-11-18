"""
Variable Autocomplete Widget

Provides autocomplete functionality for variables when typing {{ or : in input fields.
Shows a modern dropdown with available variables from all scopes.
"""

from PyQt6.QtWidgets import (QListWidget, QListWidgetItem, QWidget, QLabel, 
                              QVBoxLayout, QHBoxLayout, QApplication, QLineEdit, QTextEdit, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QRect, QSize
from PyQt6.QtGui import QFont, QColor, QTextCursor, QPalette
import re


class VariableAutocompleteItem(QWidget):
    """Custom widget for autocomplete list items showing variable name, scope, and value preview."""
    
    def __init__(self, var_name: str, var_value: str, scope: str, theme: str = 'dark'):
        super().__init__()
        
        # Scope badge styling
        scope_colors = {
            'env': ('#1976D2', '#E3F2FD'),      # Blue
            'col': ('#7B1FA2', '#F3E5F5'),      # Purple
            'ext': ('#388E3C', '#E8F5E9'),      # Green
            'dynamic': ('#F57C00', '#FFF3E0')   # Orange
        }
        
        if theme == 'dark':
            scope_bg, scope_text = scope_colors.get(scope, ('#555555', '#CCCCCC'))
            name_color = '#E0E0E0'
            value_color = '#9E9E9E'
        else:
            scope_text, scope_bg = scope_colors.get(scope, ('#333333', '#EEEEEE'))
            name_color = '#212121'
            value_color = '#666666'
        
        # Build HTML content with table for proper alignment
        scope_badge = f'<span style="background-color: {scope_bg}; color: {scope_text}; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: bold;">{scope.upper()}</span>'
        
        # Truncate value if too long
        display_value = var_value if len(var_value) <= 40 else var_value[:37] + "..."
        
        html = f'''
        <table width="100%" cellpadding="4" cellspacing="0" style="border: none;">
            <tr>
                <td width="70" style="padding-right: 10px; border: none;">{scope_badge}</td>
                <td width="160" style="padding-right: 10px; color: {name_color}; font-size: 11px; font-weight: bold; font-family: Segoe UI; border: none;">{var_name}</td>
                <td style="color: {value_color}; font-size: 10px; font-family: JetBrains Mono; border: none;">{display_value}</td>
            </tr>
        </table>
        '''
        
        # Single label with HTML content
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        label = QLabel(html)
        label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(label)


class VariableAutocompleteWidget(QListWidget):
    """
    Autocomplete dropdown for variables.
    
    Triggers:
    - When user types "{{" - shows all available variables
    - When user types ":" in URL field - shows variables for path parameters
    
    Navigation:
    - Tab/Down Arrow: Select next item
    - Shift+Tab/Up Arrow: Select previous item
    - Enter: Insert selected variable
    - Escape: Close dropdown
    - Mouse click: Insert clicked variable
    """
    
    variableSelected = pyqtSignal(str)  # Emits the variable syntax to insert
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self.trigger_text = ""  # The text that triggered autocomplete ("{{" or ":")
        self.filter_text = ""  # Text typed after trigger for filtering
        self.all_variables = []  # Store all available variables
        
        # Setup appearance
        self._setup_ui()
        
        # Connect signals
        self.itemClicked.connect(self._on_item_clicked)
        self.itemActivated.connect(self._on_item_activated)
    
    def _setup_ui(self):
        """Setup the autocomplete widget appearance."""
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        # Don't use WA_ShowWithoutActivating - it prevents mouse clicks from working
        # Allow mouse tracking for proper click handling
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)  # Allow clicks to trigger item selection
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Flexible width
        self.setMinimumWidth(450)
        self.setMaximumWidth(600)
        self.setMaximumHeight(250)
        self.setMinimumHeight(40)
        
        # Set font
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        # Apply theme-specific styling
        if self.theme == 'dark':
            bg_color = '#252526'
            border_color = '#3C3C3C'
            text_color = '#CCCCCC'
            selected_bg = '#094771'
            selected_text = '#FFFFFF'
            hover_bg = '#2A2D2E'
        else:
            bg_color = '#FFFFFF'
            border_color = '#CCCCCC'
            text_color = '#333333'
            selected_bg = '#0078D4'
            selected_text = '#FFFFFF'
            hover_bg = '#F0F0F0'
        
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                outline: none;
                padding: 2px;
                color: {text_color};
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                border-radius: 3px;
                padding: 2px;
                margin: 1px 0px;
            }}
            QListWidget::item:hover {{
                background-color: {hover_bg};
            }}
            QListWidget::item:selected {{
                background-color: {selected_bg};
                color: {selected_text};
            }}
            QScrollBar:vertical {{
                background-color: {bg_color};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {border_color};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {selected_bg};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
    
    def show_autocomplete(self, variables: list, trigger: str, position: QPoint, 
                         filter_text: str = ""):
        """
        Show autocomplete dropdown with filtered variables.
        
        Args:
            variables: List of tuples (var_name, var_value, scope)
            trigger: The trigger text ("{{" or ":")
            position: Global position to show the dropdown
            filter_text: Optional text to filter variables by
        """
        self.trigger_text = trigger
        self.filter_text = filter_text.lower()
        self.all_variables = variables
        
        # Clear existing items
        self.clear()
        
        # Filter and add variables
        filtered_vars = self._filter_variables(variables, filter_text)
        
        if not filtered_vars:
            # Show "No variables found" message
            item = QListWidgetItem("No matching variables found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
            self.addItem(item)
            if self.theme == 'dark':
                item.setForeground(QColor('#666666'))
            else:
                item.setForeground(QColor('#999999'))
        else:
            for var_name, var_value, scope in filtered_vars:
                self._add_variable_item(var_name, var_value, scope)
        
        # Resize to fit content
        self._resize_to_content()
        
        # Position and show
        self.move(position)
        self.setCurrentRow(0)  # Select first item by default
        self.show()
        self.raise_()
    
    def _filter_variables(self, variables: list, filter_text: str) -> list:
        """Filter variables based on filter text."""
        if not filter_text:
            return variables
        
        filter_lower = filter_text.lower()
        filtered = []
        
        for var_name, var_value, scope in variables:
            # Match by variable name or value
            if filter_lower in var_name.lower() or filter_lower in var_value.lower():
                filtered.append((var_name, var_value, scope))
        
        return filtered
    
    def _add_variable_item(self, var_name: str, var_value: str, scope: str):
        """Add a variable to the autocomplete list."""
        item = QListWidgetItem()
        widget = VariableAutocompleteItem(var_name, var_value, scope, self.theme)
        
        # Store variable info in item data
        item.setData(Qt.ItemDataRole.UserRole, {
            'name': var_name,
            'value': var_value,
            'scope': scope
        })
        
        self.addItem(item)
        # Set item height
        item.setSizeHint(QSize(0, 36))
        self.setItemWidget(item, widget)
    
    def _resize_to_content(self):
        """Resize widget to fit content (up to max size)."""
        # Calculate height needed - each item is 36px
        item_height = 36
        total_height = 4 + (self.count() * item_height)
        
        # Show up to 6 items, then scroll
        max_visible_items = 6
        max_height = 4 + (max_visible_items * item_height)
        
        # Constrain height
        height = min(total_height, max_height)
        height = max(height, 40)
        
        self.setFixedHeight(height)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        # Accept the click immediately
        if item and item.data(Qt.ItemDataRole.UserRole):
            # Use QTimer to ensure the click is processed after the widget is fully shown
            QTimer.singleShot(0, lambda: self._insert_variable(item))
    
    def _on_item_activated(self, item: QListWidgetItem):
        """Handle item activation (Enter key)."""
        self._insert_variable(item)
    
    def _insert_variable(self, item: QListWidgetItem):
        """Insert the selected variable."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        var_name = data['name']
        scope = data['scope']
        
        # Build variable syntax based on trigger and scope
        if self.trigger_text == ":":
            # Path parameter - just insert the name (no prefix needed)
            var_syntax = var_name
        else:
            # Variable syntax - use prefix based on scope
            if scope == 'dynamic':
                var_syntax = f"${var_name}"
            elif scope in ['env', 'col', 'ext']:
                var_syntax = f"{scope}.{var_name}"
            else:
                var_syntax = var_name
        
        self.variableSelected.emit(var_syntax)
        self.hide()
    
    def keyPressEvent(self, event):
        """Handle keyboard navigation."""
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            current_item = self.currentItem()
            if current_item:
                self._insert_variable(current_item)
            event.accept()
        elif key == Qt.Key.Key_Tab:
            # Move to next item
            current_row = self.currentRow()
            next_row = (current_row + 1) % self.count()
            self.setCurrentRow(next_row)
            event.accept()
        elif key == Qt.Key.Key_Backtab:  # Shift+Tab
            # Move to previous item
            current_row = self.currentRow()
            prev_row = (current_row - 1) % self.count()
            self.setCurrentRow(prev_row)
            event.accept()
        elif key == Qt.Key.Key_Down:
            super().keyPressEvent(event)
        elif key == Qt.Key.Key_Up:
            super().keyPressEvent(event)
        else:
            # Pass other keys to parent (for continued typing/filtering)
            self.parent().keyPressEvent(event)
            event.accept()
    
    def update_filter(self, filter_text: str):
        """Update the filter and refresh the list."""
        self.filter_text = filter_text.lower()
        
        # Clear and re-filter
        self.clear()
        filtered_vars = self._filter_variables(self.all_variables, filter_text)
        
        if not filtered_vars:
            item = QListWidgetItem("No matching variables found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.addItem(item)
            if self.theme == 'dark':
                item.setForeground(QColor('#666666'))
            else:
                item.setForeground(QColor('#999999'))
        else:
            for var_name, var_value, scope in filtered_vars:
                self._add_variable_item(var_name, var_value, scope)
        
        # Resize and select first
        self._resize_to_content()
        self.setCurrentRow(0)
        
        # Don't call setFocus - it steals focus from parent text edit
        # and causes first click to not work


class AutocompleteTextEdit(QTextEdit):
    """
    QTextEdit with variable autocomplete support.
    Triggers autocomplete when user types "{{" or ":"
    """
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self.environment_manager = None
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
        
        # Enable mouse tracking for tooltips
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        
        # Initialize tooltip widget reference
        self._tooltip_widget = None
        self.main_window = None
        self._current_tooltip_var = None  # Track which variable tooltip is showing for
        
        # Timer for delayed tooltip hiding
        self._tooltip_hide_timer = QTimer()
        self._tooltip_hide_timer.setSingleShot(True)
        self._tooltip_hide_timer.timeout.connect(self._hide_tooltip)
    
    def set_environment_manager(self, env_manager):
        """Set the environment manager for variable resolution."""
        self.environment_manager = env_manager
    
    def set_main_window(self, main_window):
        """Set the main window reference for variable resolution."""
        self.main_window = main_window
    
    def set_theme(self, theme):
        """Update theme."""
        self.theme = theme
        self.autocomplete_widget.theme = theme
        self.autocomplete_widget._setup_ui()
    
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
        
        # Handle normal typing
        super().keyPressEvent(event)
        
        # Check for autocomplete triggers after text is inserted
        if text:
            self._check_autocomplete_trigger()
    
    def _check_autocomplete_trigger(self):
        """Check if we should trigger autocomplete."""
        cursor = self.textCursor()
        pos = cursor.position()
        
        # Get text before cursor
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Right, 
                          QTextCursor.MoveMode.KeepAnchor, pos)
        text_before = cursor.selectedText()
        
        # Check for {{ trigger
        if text_before.endswith("{{"):
            self._trigger_autocomplete("{{", pos)
            return
        
        # Check for : trigger (only in URLs - look for :word pattern)
        if text_before.endswith(":"):
            # Check if this looks like a path parameter (preceded by /)
            if len(text_before) >= 2 and text_before[-2] == "/":
                self._trigger_autocomplete(":", pos)
                return
        
        # Update filter if autocomplete is already active
        if self._autocomplete_active:
            self._filter_timer.start(100)  # Debounce filter updates
    
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
        cursor = self.textCursor()
        cursor_rect = self.cursorRect(cursor)
        global_pos = self.mapToGlobal(cursor_rect.bottomLeft())
        global_pos.setY(global_pos.y() + 2)  # Small offset
        
        # Show autocomplete
        self.autocomplete_widget.show_autocomplete(variables, trigger, global_pos)
    
    def _update_autocomplete_filter(self):
        """Update autocomplete filter based on current text."""
        if not self._autocomplete_active:
            return
        
        cursor = self.textCursor()
        pos = cursor.position()
        
        # Get text after trigger
        filter_text = ""
        if pos > self._autocomplete_start_pos:
            cursor.setPosition(self._autocomplete_start_pos)
            cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            filter_text = cursor.selectedText()
        
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
            if self.main_window and hasattr(self.main_window, 'current_collection_id'):
                if self.main_window.current_collection_id:
                    col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                    for name, value in col_vars.items():
                        if value and value != '❌ Undefined':
                            variables.append((name, str(value), 'col'))
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
        
        # Calculate position before the trigger
        trigger_len = len(self._autocomplete_trigger)
        pos_before_trigger = self._autocomplete_start_pos - trigger_len
        
        # Remove trigger and text after it (the partial typing)
        cursor = self.textCursor()
        cursor.setPosition(pos_before_trigger)
        cursor.movePosition(QTextCursor.MoveOperation.End, 
                          QTextCursor.MoveMode.KeepAnchor)
        
        # Build full syntax
        if self._autocomplete_trigger == "{{":
            full_syntax = f"{{{{{var_syntax}}}}}"
        else:  # ":"
            full_syntax = var_syntax
        
        cursor.insertText(full_syntax)
        self.setTextCursor(cursor)
        
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
    
    def mouseMoveEvent(self, event):
        """Show tooltip for variables under cursor."""
        if not self.environment_manager:
            super().mouseMoveEvent(event)
            return
        
        # Get text cursor at mouse position
        cursor = self.cursorForPosition(event.pos())
        pos = cursor.position()
        
        # Get all text
        text = self.toPlainText()
        
        # Check if position is valid
        if pos < 0 or pos > len(text):
            super().mouseMoveEvent(event)
            return
        
        # Find if cursor is over a variable
        import re
        var_pattern = r'\{\{([^}]+)\}\}'
        
        tooltip_shown = False
        for match in re.finditer(var_pattern, text):
            start, end = match.span()
            # Check if cursor position is within the variable (including the {{ }} brackets)
            # Use <= for start and < for end to match on opening but not after closing
            if start <= pos < end:
                var_content = match.group(1)
                
                # Mouse is over a variable - cancel hide timer
                self._tooltip_hide_timer.stop()
                
                # Try to resolve the variable
                try:
                    resolved_value = self._resolve_variable_for_tooltip(var_content)
                    # Show tooltip for ALL variables, even undefined ones
                    if resolved_value:
                        # Only update tooltip if we're hovering over a different variable
                        if var_content != self._current_tooltip_var:
                            self._current_tooltip_var = var_content
                            
                            # Try to use VariableTooltipWidget if available
                            try:
                                from src.ui.widgets.variable_highlight_delegate import VariableTooltipWidget
                                
                                # Reuse or create tooltip widget
                                if not self._tooltip_widget:
                                    self._tooltip_widget = VariableTooltipWidget(f"{{{{{var_content}}}}}", resolved_value)
                                    # Connect tooltip events to manage hide timer
                                    self._tooltip_widget.enterEvent = lambda e: self._on_tooltip_enter(e)
                                    self._tooltip_widget.leaveEvent = lambda e: self._on_tooltip_leave(e)
                                else:
                                    # Update existing tooltip content
                                    from PyQt6.QtWidgets import QLabel
                                    self._tooltip_widget.var_value = resolved_value
                                    labels = self._tooltip_widget.findChildren(QLabel)
                                    if len(labels) >= 2:
                                        labels[0].setText(f"<b>{{{{{var_content}}}}}</b>")
                                        labels[1].setText(resolved_value)
                                
                                # Position tooltip near mouse (only when changing variables)
                                global_pos = event.globalPosition().toPoint()
                                self._tooltip_widget.move(global_pos.x() + 10, global_pos.y() + 10)
                                self._tooltip_widget.show()
                                self._tooltip_widget.raise_()
                                tooltip_shown = True
                            except ImportError as e:
                                # Fallback to simple tooltip
                                self.setToolTip(f"<b>{var_content}</b><br>{resolved_value}")
                                tooltip_shown = True
                            except Exception as e:
                                # If anything fails, use simple tooltip
                                self.setToolTip(f"<b>{var_content}</b><br>{resolved_value}")
                                tooltip_shown = True
                        else:
                            # Same variable, keep showing tooltip (don't recreate/move)
                            tooltip_shown = True
                            if self._tooltip_widget and not self._tooltip_widget.isVisible():
                                self._tooltip_widget.show()
                                self._tooltip_widget.raise_()
                        break
                except Exception as e:
                    pass
        
        if not tooltip_shown:
            # Not over any variable - start hide timer
            if not self._tooltip_hide_timer.isActive():
                self._tooltip_hide_timer.start(200)  # Short delay before hiding
        
        super().mouseMoveEvent(event)
    
    def _hide_tooltip(self):
        """Hide the tooltip widget."""
        # Only hide if mouse is not currently over the tooltip
        if self._tooltip_widget and self._tooltip_widget.underMouse():
            return  # Don't hide - mouse is over tooltip
        
        self._current_tooltip_var = None
        if self._tooltip_widget:
            self._tooltip_widget.hide()
        self.setToolTip("")
    
    def _on_tooltip_enter(self, event):
        """Handle mouse entering the tooltip widget."""
        # Stop the hide timer when mouse enters tooltip
        self._tooltip_hide_timer.stop()
        # Call the original enterEvent if it exists
        from src.ui.widgets.variable_highlight_delegate import VariableTooltipWidget
        super(VariableTooltipWidget, self._tooltip_widget).enterEvent(event)
    
    def _on_tooltip_leave(self, event):
        """Handle mouse leaving the tooltip widget."""
        # Start hide timer when mouse leaves tooltip
        self._tooltip_hide_timer.start(500)  # Give user time to move back
        # Call the original leaveEvent if it exists
        from src.ui.widgets.variable_highlight_delegate import VariableTooltipWidget
        super(VariableTooltipWidget, self._tooltip_widget).leaveEvent(event)
    
    def leaveEvent(self, event):
        """Start timer to hide tooltip when mouse leaves the widget."""
        # Use a timer so user can move mouse to the tooltip
        self._tooltip_hide_timer.start(300)  # 300ms delay
        super().leaveEvent(event)
    
    def enterEvent(self, event):
        """Cancel tooltip hide timer when mouse re-enters."""
        self._tooltip_hide_timer.stop()
        super().enterEvent(event)
    
    def _resolve_variable_for_tooltip(self, var_content: str):
        """Resolve variable value for tooltip display."""
        if not self.environment_manager:
            return None
        
        # Parse variable (could be env.name, col.name, ext.name, or $dynamic)
        if '.' in var_content and not var_content.startswith('$'):
            scope, name = var_content.split('.', 1)
            
            if scope == 'env':
                # Environment variable
                if self.environment_manager.has_active_environment():
                    env_vars = self.environment_manager.get_active_variables()
                    return env_vars.get(name, '❌ Undefined')
                    
            elif scope == 'col':
                # Collection variable - use main_window
                if self.main_window and hasattr(self.main_window, 'current_collection_id'):
                    if self.main_window.current_collection_id:
                        col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                        return col_vars.get(name, '❌ Undefined')
                        
            elif scope == 'ext':
                # Extracted variable
                try:
                    ext_vars = self.environment_manager.get_extracted_variables()
                    return ext_vars.get(name, '❌ Undefined')
                except:
                    pass
                    
        elif var_content.startswith('$'):
            # Dynamic variable
            return "[Dynamic - generated at request time]"
        else:
            # Legacy format without prefix - check all scopes
            # Check extracted first
            try:
                ext_vars = self.environment_manager.get_extracted_variables()
                if var_content in ext_vars:
                    return ext_vars[var_content]
            except:
                pass
            
            # Check collection
            if self.main_window and hasattr(self.main_window, 'current_collection_id'):
                if self.main_window.current_collection_id:
                    col_vars = self.main_window.db.get_collection_variables(self.main_window.current_collection_id)
                    if var_content in col_vars:
                        return col_vars[var_content]
            
            # Check environment
            if self.environment_manager.has_active_environment():
                env_vars = self.environment_manager.get_active_variables()
                if var_content in env_vars:
                    return env_vars[var_content]
        
        return '❌ Undefined'
