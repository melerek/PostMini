# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification File for PostMini

This file defines how to bundle the PostMini application into a standalone executable.
"""

import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path(SPECPATH)

# Additional data files to include
# Format: (source_file, destination_folder_in_exe)
# PyMiniRacer requires mini_racer.dll for JavaScript execution
import py_mini_racer
py_mini_racer_path = Path(py_mini_racer.__file__).parent
mini_racer_dll = str(py_mini_racer_path / 'mini_racer.dll')

datas = [
    ('styles.qss', '.'),              # Light theme stylesheet
    ('styles_dark.qss', '.'),         # Dark theme stylesheet
    ('postmini_logo.png', '.'),       # Application icon (PNG)
    ('postmini_logo.ico', '.'),       # Application icon (ICO for Windows)
    ('assets', 'assets'),             # Assets folder (icons, etc.)
    (mini_racer_dll, 'py_mini_racer'),  # Include mini_racer.dll
]

# Binary files to include (DLLs, shared libraries)
binaries = [
    (mini_racer_dll, '.'),  # Also include in root for compatibility
]

# Hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'requests',
    'sqlite3',
    'py_mini_racer',
]

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Data science / visualization (not needed)
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'Pillow',
        
        # GUI frameworks (not needed, we use PyQt6)
        'tkinter',
        'wx',
        'gtk',
        
        # Testing frameworks
        'pytest',
        'pytest-qt',
        '_pytest',
        'unittest.mock',
        'doctest',
        
        # Development tools
        'IPython',
        'jupyter',
        'notebook',
        'pyinstaller',
        
        # Unused standard library modules
        'pdb',
        'pydoc',
        'xmlrpc',
        'ftplib',
        'smtplib',
        'poplib',
        'imaplib',
        'telnetlib',
        'turtle',
        
        # Unused encodings
        'encodings.cp932',
        'encodings.cp949',
        'encodings.cp950',
        'encodings.euc_jp',
        'encodings.euc_kr',
        'encodings.shift_jis',
        'encodings.big5',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PostMini',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='postmini_logo.ico',  # Application icon (ICO for Windows)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PostMini',
)

