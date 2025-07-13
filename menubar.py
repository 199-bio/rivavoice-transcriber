#!/usr/bin/env python3
"""
RivaVoice Menu Bar - Clean implementation using RivaCore backend
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from rivacore import RivaBackend

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RivaMenuBar")


class RivaMenuBar(QObject):
    """Minimal menu bar interface for RivaVoice using RivaCore backend"""
    
    def __init__(self):
        super().__init__()
        self.backend = RivaBackend(check_permissions=False)
        self.tray_icon = None
        self.record_action = None
        self.autopaste_action = None
        self.hotkey_action = None
        self.waiting_for_key = False
        self._setup_tray()
        
        # Update timer for status
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(500)  # Update every 500ms
        
    def _setup_tray(self):
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("System tray not available")
            return
            
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        
        # Try to load icon
        icon_paths = [
            "rivavoice.svg",
            "icon.png",
            "RivaVoice.icns"
        ]
        
        icon_loaded = False
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
                icon_loaded = True
                logger.info(f"Loaded icon: {icon_path}")
                break
                
        if not icon_loaded:
            logger.warning("No icon file found, using default")
            # Use a default Qt icon
            self.tray_icon.setIcon(QIcon.fromTheme("audio-input-microphone"))
        
        # Create menu
        menu = QMenu()
        
        # Status (non-clickable)
        self.status_action = QAction("● Ready", self)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        
        menu.addSeparator()
        
        # Record toggle
        self.record_action = QAction("Start Recording", self)
        self.record_action.triggered.connect(self._toggle_recording)
        menu.addAction(self.record_action)
        
        menu.addSeparator()
        
        # Settings
        settings_label = QAction("Settings", self)
        settings_label.setEnabled(False)
        menu.addAction(settings_label)
        
        # Auto-paste toggle
        self.autopaste_action = QAction("✓ Auto-paste", self)
        self.autopaste_action.setCheckable(True)
        self.autopaste_action.setChecked(self.backend.get_status()['auto_paste'])
        self.autopaste_action.triggered.connect(self._toggle_autopaste)
        menu.addAction(self.autopaste_action)
        
        # Hotkey
        current_hotkey = self.backend.get_status()['hotkey'] or "Not set"
        self.hotkey_action = QAction(f"Hotkey: {current_hotkey}", self)
        self.hotkey_action.triggered.connect(self._set_hotkey)
        menu.addAction(self.hotkey_action)
        
        # API Key status (just show if set, not the actual key)
        api_key_status = "✓ Set" if self.backend.get_status()['api_key_set'] else "❌ Not set"
        self.api_key_action = QAction(f"API Key: {api_key_status}", self)
        self.api_key_action.setEnabled(False)  # Just display, not clickable
        menu.addAction(self.api_key_action)
        
        menu.addSeparator()
        
        # Quit
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        
        # Set menu and show
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
        logger.info("Menu bar setup complete")
        
    def _update_status(self):
        """Update menu items based on backend status"""
        status = self.backend.get_status()
        
        # Update recording status
        if status['recording']:
            self.status_action.setText("🔴 Recording")
            self.record_action.setText("Stop Recording")
        else:
            self.status_action.setText("● Ready")
            self.record_action.setText("Start Recording")
            
    def _toggle_recording(self):
        """Toggle recording state"""
        status = self.backend.get_status()
        
        if status['recording']:
            # Stop recording
            text = self.backend.stop_recording()
            if text:
                logger.info(f"Transcription: {text[:50]}...")
        else:
            # Start recording
            self.backend.start_recording()
            
    def _toggle_autopaste(self):
        """Toggle auto-paste setting"""
        current = self.backend.get_status()['auto_paste']
        self.backend.set_auto_paste(not current)
        
        # Update menu item
        if not current:
            self.autopaste_action.setText("✓ Auto-paste")
        else:
            self.autopaste_action.setText("  Auto-paste")
            
    def _set_hotkey(self):
        """Set new hotkey"""
        if self.waiting_for_key:
            return
            
        self.waiting_for_key = True
        self.hotkey_action.setText("Press any key...")
        
        # Start capturing the next key press
        QTimer.singleShot(100, self._capture_key)
        
    def _capture_key(self):
        """Capture key press for hotkey"""
        try:
            key = self.backend.capture_next_key()
            if key:
                success = self.backend.set_hotkey(key)
                if success:
                    self.hotkey_action.setText(f"Hotkey: {key}")
                    logger.info(f"Hotkey set to: {key}")
                else:
                    self.hotkey_action.setText("Hotkey: Failed to set")
            else:
                # User cancelled or timeout
                current_hotkey = self.backend.get_status()['hotkey'] or "Not set"
                self.hotkey_action.setText(f"Hotkey: {current_hotkey}")
        except Exception as e:
            logger.error(f"Error capturing key: {e}")
            current_hotkey = self.backend.get_status()['hotkey'] or "Not set"
            self.hotkey_action.setText(f"Hotkey: {current_hotkey}")
        finally:
            self.waiting_for_key = False
            
    def _quit(self):
        """Clean up and quit"""
        logger.info("Quitting...")
        self.backend.cleanup()
        QApplication.instance().quit()


def main():
    """Main entry point for menu bar app"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in menu bar
    
    # Create menu bar
    menubar = RivaMenuBar()
    
    logger.info("RivaVoice menu bar started")
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()