"""
py2app build script for RivaVoice Menu Bar

Usage:
    python setup_menubar.py py2app
"""
import sys
from setuptools import setup

APP = ['menubar.py']
DATA_FILES = [
    ('', ['rivavoice.svg', 'icon.png', 'RivaVoice.icns']),
]
OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'rivacore', 
        'PyQt6',
        'requests',
        'certifi',
        'urllib3',
        'charset_normalizer',
        'idna',
        'pyaudio',
        'pyperclip',
        'pynput',
    ],
    'includes': [
        'rivacore',
        'rivacore.audio',
        'rivacore.backend', 
        'rivacore.chunked_audio',
        'rivacore.config',
        'rivacore.hotkey',
        'rivacore.permissions',
        'rivacore.text_utils',
        'rivacore.transcriber',
        'pkg_resources',
    ],
    'excludes': ['tkinter', 'matplotlib', 'numpy', 'pandas'],
    'iconfile': 'RivaVoice.icns',
    'plist': {
        'CFBundleName': 'RivaVoice',
        'CFBundleDisplayName': 'RivaVoice',
        'CFBundleIdentifier': 'com.199biotechnologies.rivavoice',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSMicrophoneUsageDescription': 'RivaVoice needs access to your microphone to record speech for transcription.',
        'NSAppleEventsUsageDescription': 'RivaVoice needs access to simulate keystrokes for auto-paste functionality.',
        'LSUIElement': True,  # Hide from dock - menu bar only
        'LSMinimumSystemVersion': '10.15',
        'NSHighResolutionCapable': True,
    },
    'semi_standalone': False,
    'site_packages': True,
}

setup(
    name='RivaVoice',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)