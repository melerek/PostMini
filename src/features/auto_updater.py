"""
Auto-update functionality for PostMini
Checks GitHub for new versions and handles updates
"""

import requests
import hashlib
import subprocess
import tempfile
import os
from typing import Optional, Dict
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from packaging import version  # pip install packaging


class UpdateChecker(QThread):
    """Checks for application updates from GitHub."""
    
    # Signals
    update_available = pyqtSignal(dict)  # Emits update info
    no_update = pyqtSignal(str)  # Emits current version
    check_error = pyqtSignal(str)  # Error message
    
    # Configuration - UPDATE THESE FOR YOUR REPOSITORY
    VERSION_URL = "https://raw.githubusercontent.com/melerek/PostMini/main/version.json"
    CURRENT_VERSION = "1.9.5"  # Should match installer version
    
    def __init__(self, silent=False):
        super().__init__()
        self.silent = silent
    
    def run(self):
        """Check if a new version is available."""
        try:
            # Fetch version manifest
            response = requests.get(self.VERSION_URL, timeout=10)
            response.raise_for_status()
            
            update_info = response.json()
            latest_version = update_info.get('latest_version', '')
            
            # Compare versions
            if version.parse(latest_version) > version.parse(self.CURRENT_VERSION):
                self.update_available.emit(update_info)
            else:
                self.no_update.emit(self.CURRENT_VERSION)
        
        except requests.RequestException as e:
            if not self.silent:
                self.check_error.emit(f"Network error: {str(e)}")
        except version.InvalidVersion:
            if not self.silent:
                self.check_error.emit(f"Invalid version format in update manifest")
        except Exception as e:
            if not self.silent:
                self.check_error.emit(f"Error checking updates: {str(e)}")


class UpdateDownloader(QThread):
    """Downloads update installer in background."""
    
    # Signals
    download_progress = pyqtSignal(int, int)  # downloaded, total
    download_complete = pyqtSignal(str)  # file path
    download_error = pyqtSignal(str)  # error message
    
    def __init__(self, download_url: str, checksum: str = ""):
        super().__init__()
        self.download_url = download_url
        self.expected_checksum = checksum
        self.temp_file = None
        self._cancelled = False
    
    def run(self):
        """Download the installer."""
        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            # Create temp file
            temp_dir = tempfile.gettempdir()
            filename = os.path.basename(self.download_url)
            self.temp_file = os.path.join(temp_dir, filename)
            
            # Download with progress
            downloaded = 0
            with open(self.temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._cancelled:
                        self.download_error.emit("Download cancelled")
                        return
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.download_progress.emit(downloaded, total_size)
            
            # Verify checksum if provided
            if self.expected_checksum:
                actual_checksum = self._calculate_checksum(self.temp_file)
                # Normalize both checksums for comparison (remove prefix if present)
                expected_hash = self.expected_checksum.replace('sha256:', '').upper()
                actual_hash = actual_checksum.replace('sha256:', '').upper()
                if actual_hash != expected_hash:
                    self.download_error.emit("Checksum verification failed. Downloaded file may be corrupted.")
                    return
            
            self.download_complete.emit(self.temp_file)
        
        except Exception as e:
            self.download_error.emit(f"Download failed: {str(e)}")
    
    def cancel(self):
        """Cancel the download."""
        self._cancelled = True
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"


class UpdateInstaller:
    """Handles installation of downloaded updates."""
    
    @staticmethod
    def install_update(installer_path: str, silent: bool = False):
        """
        Run the installer and close current app.
        
        Args:
            installer_path: Path to downloaded installer
            silent: If True, run installer in silent mode
        """
        try:
            if silent:
                # Silent installation (Windows only)
                subprocess.Popen([installer_path, '/VERYSILENT', '/CLOSEAPPLICATIONS'])
            else:
                # Normal installation (user sees wizard)
                subprocess.Popen([installer_path])
            
            # Exit current app to allow installation
            import sys
            sys.exit(0)
        
        except Exception as e:
            raise Exception(f"Failed to start installer: {e}")

