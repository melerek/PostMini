"""
API Client Application - Main Entry Point

A lightweight desktop API client application similar to Postman, built with PyQt6.
This application allows users to create, manage, and execute HTTP requests with
support for collections, parameters, headers, authentication, and more.

Author: AI Assistant
Date: 2025
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFontDatabase

from src.ui.main_window import MainWindow
from src.core.app_paths import get_app_paths


def load_custom_fonts():
    """
    Load custom fonts (Inter and JetBrains Mono) for the application.
    These fonts are bundled with the application for consistent typography.
    """
    try:
        from src.core.app_paths import AppPaths
        resources_dir = AppPaths.get_resources_dir()
        fonts_dir = resources_dir / "assets" / "fonts"
        
        # Define font files to load - using static TTF files for better weight control
        font_files = [
            # Inter font (UI font) - load specific weights
            fonts_dir / "Inter" / "extras" / "ttf" / "Inter-Regular.ttf",
            fonts_dir / "Inter" / "extras" / "ttf" / "Inter-Medium.ttf",
            fonts_dir / "Inter" / "extras" / "ttf" / "Inter-SemiBold.ttf",
            fonts_dir / "Inter" / "extras" / "ttf" / "Inter-Bold.ttf",
            fonts_dir / "Inter" / "extras" / "ttf" / "Inter-Italic.ttf",
            # JetBrains Mono (Code font) - load specific weights
            fonts_dir / "JetBrainsMono" / "fonts" / "ttf" / "JetBrainsMono-Regular.ttf",
            fonts_dir / "JetBrainsMono" / "fonts" / "ttf" / "JetBrainsMono-Medium.ttf",
            fonts_dir / "JetBrainsMono" / "fonts" / "ttf" / "JetBrainsMono-SemiBold.ttf",
            fonts_dir / "JetBrainsMono" / "fonts" / "ttf" / "JetBrainsMono-Bold.ttf",
            fonts_dir / "JetBrainsMono" / "fonts" / "ttf" / "JetBrainsMono-Italic.ttf",
        ]
        
        loaded_fonts = []
        for font_path in font_files:
            if font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    loaded_fonts.extend(font_families)
                    print(f"[OK] Loaded font: {font_path.name}")
                else:
                    print(f"[Warning] Failed to load font: {font_path}")
            else:
                print(f"[Warning] Font file not found: {font_path}")
        
        if loaded_fonts:
            print(f"[OK] Successfully loaded {len(set(loaded_fonts))} custom font families")
            print(f"[OK] Font families available: {', '.join(set(loaded_fonts))}")
        else:
            print("[Warning] No custom fonts were loaded. Using system defaults.")
            
    except Exception as e:
        print(f"[Warning] Error loading custom fonts: {e}")
        print("[Info] Application will use system default fonts")


def load_stylesheet(filename: str = "styles.qss") -> str:
    """
    Load the application stylesheet from file.
    
    Args:
        filename: Name of the QSS file
        
    Returns:
        Stylesheet content as string
    """
    try:
        from src.core.app_paths import AppPaths
        # Try to load from resources directory (installation folder)
        resources_dir = AppPaths.get_resources_dir()
        stylesheet_path = resources_dir / filename
        
        if stylesheet_path.exists():
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Fallback: try current directory (for development)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            stylesheet_path = os.path.join(script_dir, filename)
            
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Replace relative asset paths with absolute paths
        assets_dir = resources_dir / "assets"
        # Convert Windows backslashes to forward slashes for CSS
        assets_path_str = str(assets_dir).replace('\\', '/')
        content = content.replace('assets/', f'{assets_path_str}/')
        
        return content
        
    except FileNotFoundError:
        print(f"Warning: Stylesheet file '{filename}' not found. Using default styling.")
        return ""
    except Exception as e:
        print(f"Warning: Failed to load stylesheet: {e}")
        return ""


def get_saved_theme() -> str:
    """Get the saved theme preference."""
    try:
        from src.core.app_paths import get_app_paths
        settings_file = get_app_paths().settings_file
        
        if settings_file.exists():
            import json
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get('theme', 'dark')
    except Exception:
        pass
    
    return 'dark'  # Default to dark theme


def save_theme_preference(theme: str):
    """Save the theme preference."""
    try:
        from src.core.app_paths import get_app_paths
        import json
        
        settings_file = get_app_paths().settings_file
        
        # Load existing settings
        settings = {}
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
        # Update theme
        settings['theme'] = theme
        
        # Save
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
            
        print(f"[OK] Theme preference saved: {theme}")
    except Exception as e:
        print(f"Warning: Failed to save theme preference: {e}")


def main():
    """
    Main entry point for the API Client application.
    """
    # Initialize application paths (creates directories in %APPDATA%)
    app_paths = get_app_paths()
    print(f"[OK] Application data directory: {app_paths.app_data_dir}")
    print(f"[OK] Database location: {app_paths.database_path}")
    
    # Enable High DPI scaling for better display on high-resolution screens
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create the application instance
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("PostMini")
    app.setOrganizationName("PostMini")
    app.setApplicationVersion("1.9.9")
    
    # Load custom fonts BEFORE loading stylesheets
    load_custom_fonts()
    
    # Set application icon (try ICO first for better Windows support, fallback to PNG)
    icon_path_ico = app_paths.get_resources_dir() / "postmini_logo.ico"
    icon_path_png = app_paths.get_resources_dir() / "postmini_logo.png"
    
    if icon_path_ico.exists():
        app.setWindowIcon(QIcon(str(icon_path_ico)))
        print(f"[OK] Application icon loaded from: {icon_path_ico}")
    elif icon_path_png.exists():
        app.setWindowIcon(QIcon(str(icon_path_png)))
        print(f"[OK] Application icon loaded from: {icon_path_png}")
    else:
        print(f"[Warning] Application icon not found")
    
    # Load saved theme preference
    current_theme = get_saved_theme()
    stylesheet_file = "styles_dark.qss" if current_theme == "dark" else "styles.qss"
    
    # Load and apply the stylesheet
    stylesheet = load_stylesheet(stylesheet_file)
    if stylesheet:
        app.setStyleSheet(stylesheet)
        print(f"[OK] {current_theme.capitalize()} theme loaded successfully")
    
    # Create and show the main window with the database path and theme
    main_window = MainWindow(db_path=str(app_paths.database_path), theme=current_theme)
    
    # Update script tab theme to match saved preference (already set in __init__)
    # No need to set current_theme again, it's already set in constructor
    
    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

