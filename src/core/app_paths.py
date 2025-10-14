"""
App Paths Manager

This module manages application data paths, ensuring that user data
is stored in the appropriate system location (%APPDATA% on Windows).
"""

import os
import sys
from pathlib import Path


class AppPaths:
    """Manages application data paths for cross-platform compatibility."""
    
    APP_NAME = "PostMini"
    APP_AUTHOR = "PostMini"
    
    def __init__(self):
        """Initialize app paths and ensure directories exist."""
        self._app_data_dir = self._get_app_data_dir()
        self._ensure_directories()
    
    def _get_app_data_dir(self) -> Path:
        """
        Get the appropriate application data directory based on the OS.
        
        Returns:
            Path to the application data directory
        """
        if sys.platform == "win32":
            # Windows: Use %APPDATA%\PostMini
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata) / self.APP_NAME
            # Fallback if APPDATA not set
            return Path.home() / "AppData" / "Roaming" / self.APP_NAME
        
        elif sys.platform == "darwin":
            # macOS: Use ~/Library/Application Support/PostMini
            return Path.home() / "Library" / "Application Support" / self.APP_NAME
        
        else:
            # Linux/Unix: Use ~/.local/share/PostMini
            xdg_data_home = os.getenv("XDG_DATA_HOME")
            if xdg_data_home:
                return Path(xdg_data_home) / self.APP_NAME
            return Path.home() / ".local" / "share" / self.APP_NAME
    
    def _ensure_directories(self):
        """Create application directories if they don't exist."""
        self._app_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.logs_dir.mkdir(exist_ok=True)
        self.exports_dir.mkdir(exist_ok=True)
    
    @property
    def app_data_dir(self) -> Path:
        """Get the main application data directory."""
        return self._app_data_dir
    
    @property
    def database_path(self) -> Path:
        """Get the path to the SQLite database."""
        return self._app_data_dir / "api_client.db"
    
    @property
    def logs_dir(self) -> Path:
        """Get the logs directory."""
        return self._app_data_dir / "logs"
    
    @property
    def exports_dir(self) -> Path:
        """Get the exports directory."""
        return self._app_data_dir / "exports"
    
    @property
    def settings_file(self) -> Path:
        """Get the settings file path."""
        return self._app_data_dir / "settings.json"
    
    @staticmethod
    def get_install_dir() -> Path:
        """
        Get the application installation directory.
        This is where the executable and resources are located.
        
        Returns:
            Path to the installation directory
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return Path(sys.executable).parent
        else:
            # Running as script
            return Path(__file__).parent.parent.parent
    
    @staticmethod
    def get_resources_dir() -> Path:
        """
        Get the resources directory (styles, icons, etc.).
        
        Returns:
            Path to the resources directory
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            # PyInstaller stores data files in _internal subdirectory
            install_dir = Path(sys.executable).parent
            internal_dir = install_dir / "_internal"
            if internal_dir.exists():
                return internal_dir
            else:
                # Fallback to install directory
                return install_dir
        else:
            # Running as script - resources in project root
            return Path(__file__).parent.parent.parent
    
    def __str__(self) -> str:
        """String representation of app paths."""
        return (
            f"PostMini Application Paths:\n"
            f"  App Data: {self.app_data_dir}\n"
            f"  Database: {self.database_path}\n"
            f"  Logs: {self.logs_dir}\n"
            f"  Exports: {self.exports_dir}\n"
            f"  Install Dir: {self.get_install_dir()}\n"
        )


# Global instance
_app_paths = None


def get_app_paths() -> AppPaths:
    """
    Get the global AppPaths instance (singleton pattern).
    
    Returns:
        AppPaths instance
    """
    global _app_paths
    if _app_paths is None:
        _app_paths = AppPaths()
    return _app_paths

