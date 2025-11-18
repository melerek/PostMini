"""
Simple autocomplete test - just show if keyPressEvent is being called
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from src.ui.widgets.variable_highlight_delegate import HighlightedLineEdit
from src.features.variable_substitution import EnvironmentManager

app = QApplication(sys.argv)

# Create main window
window = QMainWindow()
widget = QWidget()
layout = QVBoxLayout(widget)

# Create line edit with autocomplete
line_edit = HighlightedLineEdit(theme='dark')

# Create a simple environment manager
env_manager = EnvironmentManager()
env_manager.set_active_environment({
    'id': 1,
    'name': 'Test',
    'variables': {
        'baseUrl': 'https://api.example.com',
        'token': 'abc123'
    }
})

line_edit.set_environment_manager(env_manager)
line_edit.setPlaceholderText("Type {{ to see autocomplete")

layout.addWidget(line_edit)
window.setCentralWidget(widget)
window.setGeometry(100, 100, 600, 100)
window.show()

print("\n" + "="*60)
print("SIMPLE AUTOCOMPLETE TEST")
print("="*60)
print("\nType '{{' in the text field above.")
print("Watch the console for debug messages.")
print("\nVariables available:")
print("  - baseUrl: https://api.example.com")
print("  - token: abc123")
print("="*60 + "\n")

sys.exit(app.exec())
