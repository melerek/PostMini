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

from src.ui.main_window import MainWindow
from src.core.app_paths import get_app_paths


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
                return f.read()
        
        # Fallback: try current directory (for development)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        stylesheet_path = os.path.join(script_dir, filename)
        
        with open(stylesheet_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Stylesheet file '{filename}' not found. Using default styling.")
        return ""
    except Exception as e:
        print(f"Warning: Failed to load stylesheet: {e}")
        return ""


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
    app.setApplicationVersion("1.0.0")
    
    # Load and apply the professional stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
        print("[OK] Professional design system loaded successfully")
    
    # Create and show the main window with the database path
    main_window = MainWindow(db_path=str(app_paths.database_path))
    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

