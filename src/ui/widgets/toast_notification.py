"""
Toast Notification Widget

A non-blocking notification widget that displays temporary messages at the bottom
of the window, similar to modern mobile apps and web applications.
"""

from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect, QWidget
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont


class ToastNotification(QLabel):
    """A toast notification that appears and fades out automatically."""
    
    # Toast types with their colors and icons
    SUCCESS = ("success", "#4CAF50", "✓")
    ERROR = ("error", "#F44336", "✗")
    WARNING = ("warning", "#FF9800", "⚠")
    INFO = ("info", "#2196F3", "ℹ")
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        
        # Initialize duration tracker
        self._pending_duration = 0
        
        # Setup appearance
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setFont(QFont("Arial", 11))
        
        # Position at bottom center of parent
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        self.setMinimumHeight(50)
        
        # Style
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(45, 45, 48, 0.95);
                color: white;
                border-radius: 8px;
                padding: 12px 20px;
                border: 1px solid #3e3e42;
            }
        """)
        
        # Setup opacity effect for fade in/out
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Animation for fade in/out
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)  # 300ms fade
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Timer to auto-hide
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self._start_fade_out)
        
        # Initially hidden
        self.hide()
    
    def show_toast(self, message: str, toast_type: tuple = INFO, duration: int = 3000):
        """
        Show a toast notification.
        
        Args:
            message: The message to display
            toast_type: Tuple of (type_name, color, icon)
            duration: How long to show the toast in milliseconds (0 = permanent)
        """
        type_name, color, icon = toast_type
        
        # Set message with icon
        self.setText(f"{icon}  {message}")
        
        # Update color based on type
        if self.parent():
            # Detect if using dark mode by checking parent's background
            is_dark = True  # Assume dark mode for now
            
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    border: none;
                    font-weight: 500;
                }}
            """)
        
        # Position at bottom center of parent
        if self.parent():
            parent_rect = self.parent().rect()
            self.adjustSize()
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - self.height() - 60  # 60px from bottom
            self.move(x, y)
        
        # Show with fade in
        self.show()
        self.raise_()  # Bring to front
        
        # Store duration for later use
        self._pending_duration = duration
        
        # Fade in
        self.fade_animation.stop()
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        
        # Disconnect any previous connections
        try:
            self.fade_animation.finished.disconnect()
        except:
            pass
        
        # Start hide timer AFTER fade-in completes
        if duration > 0:
            self.fade_animation.finished.connect(self._on_fade_in_complete)
        
        self.fade_animation.start()
    
    def _on_fade_in_complete(self):
        """Called when fade-in animation completes. Start the hide timer."""
        # Disconnect this handler
        try:
            self.fade_animation.finished.disconnect(self._on_fade_in_complete)
        except:
            pass
        
        # Now start the timer to hide after the specified duration
        if self._pending_duration > 0:
            self.hide_timer.stop()
            self.hide_timer.start(self._pending_duration)
    
    def _start_fade_out(self):
        """Start the fade out animation."""
        self.hide_timer.stop()
        
        # Fade out
        self.fade_animation.stop()
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        # Disconnect any previous connections to avoid multiple calls
        try:
            self.fade_animation.finished.disconnect()
        except:
            pass
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
    
    def hide_now(self):
        """Hide the toast immediately without animation."""
        self.hide_timer.stop()
        self.fade_animation.stop()
        self.hide()


class ToastManager:
    """Manages toast notifications for a window."""
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.toast = ToastNotification(parent)
    
    def success(self, message: str, duration: int = 3000):
        """Show a success toast (visible for 3 seconds)."""
        self.toast.show_toast(message, ToastNotification.SUCCESS, duration)
    
    def error(self, message: str, duration: int = 3000):
        """Show an error toast (visible for 3 seconds)."""
        self.toast.show_toast(message, ToastNotification.ERROR, duration)
    
    def warning(self, message: str, duration: int = 3000):
        """Show a warning toast (visible for 3 seconds)."""
        self.toast.show_toast(message, ToastNotification.WARNING, duration)
    
    def info(self, message: str, duration: int = 3000):
        """Show an info toast (visible for 3 seconds)."""
        self.toast.show_toast(message, ToastNotification.INFO, duration)

