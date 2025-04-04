import os
import sys
import logging
import traceback
import tempfile
from rivavoice import constants # Absolute import

logger = logging.getLogger(constants.APP_NAME) # Use constant

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller/py2app """
    try:
        # PyInstaller/py2app creates a temp folder and stores path in _MEIPASS/_MEIPASS2
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        elif getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS2'):
            base_path = sys._MEIPASS2
        # Check for py2app specific structure when frozen
        elif getattr(sys, 'frozen', False) and sys.platform == 'darwin':
            # py2app bundle structure: .app/Contents/Resources
            base_path = os.path.join(os.path.dirname(sys.executable), "..", "Resources")
        else:
            # Not bundled, assume running from source
            # Base path is the directory containing the 'rivavoice' package (project root)
            # __file__ is rivavoice/utils.py, so go up *one* level
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    except Exception as e:
        logger.error(f"Error detecting base path in resource_path: {e}")
        # Fallback if detection fails (assuming running from source)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    path = os.path.join(base_path, relative_path)
    # logger.debug(f"Resource path for '{relative_path}': '{path}' (Base: '{base_path}')")
    return path

# Removed play_sound_file and _play_sound_blocking as they moved to pykeybindmanager.sound_player

