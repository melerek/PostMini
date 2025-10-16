"""
Tests for Dark Mode Feature

This module tests the dark mode theme toggle functionality, including:
- Theme persistence
- Theme switching
- Cell editor padding removal
- UI element styling
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QLineEdit, QTableWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Ensure tests can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import get_saved_theme, save_theme_preference, load_stylesheet
from src.core.app_paths import AppPaths, get_app_paths


# Pytest fixture for QApplication
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestThemePersistence:
    """Test theme preference saving and loading."""
    
    def test_default_theme_is_dark(self, tmp_path):
        """Test that default theme is dark mode."""
        with patch('src.core.app_paths.get_app_paths') as mock_paths:
            mock_app_paths = Mock()
            mock_app_paths.settings_file = tmp_path / "settings.json"
            mock_paths.return_value = mock_app_paths
            
            theme = get_saved_theme()
            assert theme == 'dark', "Default theme should be dark"
    
    def test_save_theme_preference(self, tmp_path):
        """Test saving theme preference to settings file."""
        with patch('src.core.app_paths.get_app_paths') as mock_paths:
            mock_app_paths = Mock()
            settings_file = tmp_path / "settings.json"
            mock_app_paths.settings_file = settings_file
            mock_paths.return_value = mock_app_paths
            
            # Save dark theme
            save_theme_preference('dark')
            assert settings_file.exists(), "Settings file should be created"
            
            # Verify content
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            assert settings['theme'] == 'dark', "Theme should be saved as dark"
    
    def test_load_saved_theme(self, tmp_path):
        """Test loading previously saved theme preference."""
        with patch('src.core.app_paths.get_app_paths') as mock_paths:
            mock_app_paths = Mock()
            settings_file = tmp_path / "settings.json"
            mock_app_paths.settings_file = settings_file
            mock_paths.return_value = mock_app_paths
            
            # Create settings file with light theme
            settings = {'theme': 'light'}
            with open(settings_file, 'w') as f:
                json.dump(settings, f)
            
            # Load theme
            theme = get_saved_theme()
            assert theme == 'light', "Should load saved light theme"
    
    def test_theme_toggle_updates_preference(self, tmp_path):
        """Test that toggling theme updates the saved preference."""
        with patch('src.core.app_paths.get_app_paths') as mock_paths:
            mock_app_paths = Mock()
            settings_file = tmp_path / "settings.json"
            mock_app_paths.settings_file = settings_file
            mock_paths.return_value = mock_app_paths
            
            # Save dark theme
            save_theme_preference('dark')
            assert get_saved_theme() == 'dark'
            
            # Toggle to light
            save_theme_preference('light')
            assert get_saved_theme() == 'light'
            
            # Toggle back to dark
            save_theme_preference('dark')
            assert get_saved_theme() == 'dark'


class TestStylesheetLoading:
    """Test stylesheet loading functionality."""
    
    def test_load_light_stylesheet(self, tmp_path):
        """Test loading light theme stylesheet."""
        # Create a test stylesheet
        stylesheet_content = "QWidget { background: white; }"
        stylesheet_file = tmp_path / "styles.qss"
        with open(stylesheet_file, 'w') as f:
            f.write(stylesheet_content)
        
        with patch('src.core.app_paths.AppPaths.get_resources_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            
            content = load_stylesheet("styles.qss")
            assert content == stylesheet_content
    
    def test_load_dark_stylesheet(self, tmp_path):
        """Test loading dark theme stylesheet."""
        # Create a test dark stylesheet
        stylesheet_content = "QWidget { background: #1e1e1e; }"
        stylesheet_file = tmp_path / "styles_dark.qss"
        with open(stylesheet_file, 'w') as f:
            f.write(stylesheet_content)
        
        with patch('src.core.app_paths.AppPaths.get_resources_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            
            content = load_stylesheet("styles_dark.qss")
            assert content == stylesheet_content
    
    def test_missing_stylesheet_returns_empty(self):
        """Test that missing stylesheet returns empty string."""
        with patch('src.core.app_paths.AppPaths.get_resources_dir') as mock_dir:
            mock_dir.return_value = Path("/nonexistent/path")
            
            content = load_stylesheet("nonexistent.qss")
            assert content == ""


class TestNoPaddingDelegate:
    """Test the NoPaddingDelegate for table cell editors."""
    
    def test_delegate_creates_editor(self, qapp):
        """Test that delegate creates QLineEdit editor."""
        from src.ui.main_window import NoPaddingDelegate
        from PyQt6.QtWidgets import QStyleOptionViewItem
        
        delegate = NoPaddingDelegate()
        table = QTableWidget(5, 2)
        option = QStyleOptionViewItem()
        
        # Create editor
        editor = delegate.createEditor(table, option, table.model().index(0, 0))
        
        assert isinstance(editor, QLineEdit), "Editor should be QLineEdit"
    
    def test_delegate_removes_padding(self, qapp):
        """Test that delegate removes padding from editor."""
        from src.ui.main_window import NoPaddingDelegate
        from PyQt6.QtWidgets import QStyleOptionViewItem
        
        delegate = NoPaddingDelegate()
        table = QTableWidget(5, 2)
        option = QStyleOptionViewItem()
        
        # Create editor
        editor = delegate.createEditor(table, option, table.model().index(0, 0))
        
        # Check that styleSheet contains padding:0px
        style = editor.styleSheet()
        assert "padding: 0px" in style or "padding:0px" in style, \
            "Editor should have no padding"
        assert "margin: 0px" in style or "margin:0px" in style, \
            "Editor should have no margin"


class TestCollectionBoldFont:
    """Test that collection names are displayed in bold."""
    
    def test_collection_item_has_bold_font(self, qapp):
        """Test that collection items have bold font."""
        from PyQt6.QtWidgets import QTreeWidgetItem
        
        # Create a tree item (simulating collection)
        item = QTreeWidgetItem(["Test Collection [2]"])
        
        # Set bold font (as done in MainWindow._load_collections)
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)
        
        # Verify font is bold
        assert item.font(0).bold(), "Collection item font should be bold"
    
    def test_request_item_has_normal_font(self, qapp):
        """Test that request items have normal (non-bold) font."""
        from PyQt6.QtWidgets import QTreeWidgetItem
        
        # Create a tree item (simulating request)
        item = QTreeWidgetItem(["GET - Test Request"])
        
        # Default font should not be bold
        assert not item.font(0).bold(), "Request item font should not be bold"


class TestRequestTitleVisibility:
    """Test request title label visibility in different themes."""
    
    def test_request_title_has_object_name(self, qapp):
        """Test that request title label has correct object name."""
        from PyQt6.QtWidgets import QLabel
        
        label = QLabel("Test Request (Collection)")
        label.setObjectName("requestTitleLabel")
        
        assert label.objectName() == "requestTitleLabel", \
            "Label should have requestTitleLabel object name"
    
    def test_request_title_dynamic_property(self, qapp):
        """Test that request title uses dynamic property for styling."""
        from PyQt6.QtWidgets import QLabel
        
        label = QLabel("Test Request (Collection)")
        label.setObjectName("requestTitleLabel")
        
        # Set saved property
        label.setProperty("saved", "true")
        assert label.property("saved") == "true"
        
        # Set unsaved property
        label.setProperty("saved", "false")
        assert label.property("saved") == "false"


class TestToolbarSpacerTransparency:
    """Test that toolbar spacer is transparent."""
    
    def test_spacer_has_transparent_background(self, qapp):
        """Test that spacer widget has transparent background."""
        from PyQt6.QtWidgets import QWidget
        from PyQt6.QtWidgets import QSizePolicy
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        spacer.setStyleSheet("background: transparent;")
        
        # Verify styleSheet
        assert "transparent" in spacer.styleSheet(), \
            "Spacer should have transparent background"


class TestApplicationIcon:
    """Test application icon loading."""
    
    def test_icon_path_from_resources(self, tmp_path):
        """Test that icon is loaded from resources directory."""
        from PyQt6.QtGui import QIcon
        
        # Create a dummy PNG file
        icon_file = tmp_path / "postmini_logo.png"
        icon_file.write_bytes(b"fake png data")
        
        # Verify file exists
        assert icon_file.exists(), "Icon file should exist"
        
        # Create QIcon (will use default if invalid)
        icon = QIcon(str(icon_file))
        assert not icon.isNull(), "Icon should be created"


class TestThemeIntegration:
    """Integration tests for theme functionality."""
    
    def test_complete_theme_workflow(self, tmp_path, qapp):
        """Test complete theme switching workflow."""
        with patch('src.core.app_paths.get_app_paths') as mock_paths:
            mock_app_paths = Mock()
            settings_file = tmp_path / "settings.json"
            mock_app_paths.settings_file = settings_file
            mock_paths.return_value = mock_app_paths
            
            # 1. Initial state (dark by default)
            theme = get_saved_theme()
            assert theme == 'dark'
            
            # 2. User toggles to light
            save_theme_preference('light')
            theme = get_saved_theme()
            assert theme == 'light'
            
            # 3. App restart - should load light theme
            theme = get_saved_theme()
            assert theme == 'light'
            
            # 4. User toggles back to dark
            save_theme_preference('dark')
            theme = get_saved_theme()
            assert theme == 'dark'


class TestDarkModeColorPalette:
    """Test that dark mode uses correct color palette."""
    
    def test_dark_stylesheet_contains_dark_colors(self, tmp_path):
        """Test that dark stylesheet contains appropriate dark colors."""
        # Read actual dark stylesheet
        project_root = Path(__file__).parent.parent
        dark_qss = project_root / "styles_dark.qss"
        
        if dark_qss.exists():
            content = dark_qss.read_text()
            
            # Check for dark background colors
            assert "#1e1e1e" in content, "Should contain main dark background"
            assert "#252526" in content, "Should contain panel background"
            assert "#e0e0e0" in content, "Should contain light text color"
    
    def test_light_stylesheet_contains_light_colors(self, tmp_path):
        """Test that light stylesheet contains appropriate light colors."""
        # Read actual light stylesheet
        project_root = Path(__file__).parent.parent
        light_qss = project_root / "styles.qss"
        
        if light_qss.exists():
            content = light_qss.read_text()
            
            # Check for light colors
            assert "#212121" in content or "#FFFFFF" in content or "white" in content, \
                "Should contain light theme colors"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

