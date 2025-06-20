"""
Setup script for RivaVoice application
"""

from setuptools import setup

APP = ["app.py"]
DATA_FILES = [
    ("", ["RivaVoice.icns"]),
    # ('', ['doubleping.wav', 'singleping.wav']) # Removed - Sound files handled by pykeybindmanager
]
OPTIONS = {
    "argv_emulation": True,
    "iconfile": "RivaVoice.icns",
    "plist": {
        "CFBundleName": "RivaVoice",
        "CFBundleDisplayName": "RivaVoice",
        "CFBundleIdentifier": "com.rivavoice.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHumanReadableCopyright": "Copyright © 2025",
        "NSMicrophoneUsageDescription": "RivaVoice needs microphone access to record your voice for transcription.",
        "NSAppleEventsUsageDescription": "RivaVoice needs to control other applications to paste transcribed text.",
        "NSInputMonitoringUsageDescription": "RivaVoice requires input monitoring to detect keyboard shortcuts for recording.",
        "NSAppleMusicUsageDescription": "RivaVoice needs access to audio for recording.",
        "LSUIElement": True,  # Makes the app not show in the dock
    },
    "packages": ["rivavoice"],
    "includes": [
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtNetwork",
    ],
    "excludes": [
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "PyQt5",
        "PySide6",
        "PyQt6.QtWebEngine",
        "PyQt6.QtWebEngineCore",
        "test",
        "unittest",
        "doctest",
        "pdb",
        "pydoc",
        "distutils",
        "setuptools",
        "email",
        "html",
        "http",
        "xml",
        "xmlrpc",
        "PIL",
    ],
    # This ensures app runs even if permission dialogs are shown
    "no_strip": True,
    # Only include necessary Qt plugins
    "qt_plugins": ["platforms", "styles"],
    # Optimization options
    "optimize": 2,
    "compressed": True,
}

# Core metadata and dependencies are now defined in pyproject.toml
# This setup.py is primarily for py2app configuration.
setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    # install_requires is now handled by pyproject.toml
)
