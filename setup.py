"""
py2app build script for RivaVoice

Usage:
    python setup.py py2app
"""
import sys
from setuptools import setup

APP = ['rivavoice.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['rivacore'],
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
    ],
    'excludes': ['tkinter'],
    'iconfile': 'RivaVoice.icns' if sys.platform == 'darwin' else None,
    'plist': {
        'CFBundleName': 'RivaVoice',
        'CFBundleDisplayName': 'RivaVoice',
        'CFBundleIdentifier': 'com.199biotechnologies.rivavoice',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSMicrophoneUsageDescription': 'RivaVoice needs access to your microphone to record speech for transcription.',
        'NSAppleEventsUsageDescription': 'RivaVoice needs access to simulate keystrokes for auto-paste functionality.',
        'LSUIElement': False,  # Show in dock since it's a terminal app
        'LSMinimumSystemVersion': '10.15',
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