# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],  # Main application script
    pathex=[],  # Additional search paths for modules
    binaries=[],  # List of binary files to include
    datas=[
        ('templates', 'templates'),  # Include HTML files from the templates directory
        ('static', 'static'),  # Include static files (CSS, JS, images) from the static directory
    ],
    hiddenimports=[],  # Any hidden imports that PyInstaller might miss
    hookspath=[],  # Path to custom hooks
    hooksconfig={},  # Configuration for hooks
    runtime_hooks=[],  # Hooks to run at runtime
    excludes=[],  # Modules to exclude
    noarchive=False,  # If True, disables .pyz archive creation
    optimize=0,  # Optimization level
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Library',  # Name of the generated executable
    debug=False,  # Set to True for debug mode
    bootloader_ignore_signals=False,
    strip=False,  # If True, strip binaries
    upx=True,  # Use UPX to compress executables
    upx_exclude=[],  # Exclude specific files from UPX compression
    runtime_tmpdir=None,  # Directory for temporary files
    console=True,  # If True, runs with a console window
    disable_windowed_traceback=False,  # Show traceback in a console window
    argv_emulation=False,  # Emulate command-line arguments
    target_arch=None,  # Architecture target (e.g., 'x86_64')
    codesign_identity=None,  # Codesign identity for macOS
    entitlements_file=None,  # Entitlements file for macOS
    icon="C:\\Users\\sahil\\workspace\\library-win\\favicon.ico",  # Specify the path to your .ico file
)
