import os
import logging
import traceback
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
from rivavoice import constants  # Change to absolute import
from rivavoice.utils import resource_path  # Change to absolute import

logger = logging.getLogger(constants.APP_NAME)  # Use constant


class TrayManager(QObject):
    """Manages the system tray icon and menu"""

    # Signals to communicate with MainWindow
    show_app_signal = pyqtSignal()
    quit_app_signal = pyqtSignal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.tray_icon = None
        self._setup_tray_icon()

    def _setup_tray_icon(self):
        """Setup system tray icon with menu"""
        try:
            # Check if QSystemTrayIcon is available on this system
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logger.warning("System tray not available on this system.")
                return

            # Create tray icon
            self.tray_icon = QSystemTrayIcon(self.main_window)  # Parent to main window

            # Load icon using resource_path
            icon_path = resource_path(
                constants.ICON_TRAY_SVG
            )  # Use constant & resource_path
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                logger.warning(
                    f"Tray icon file not found at resolved path: {icon_path}"
                )
                # Provide a fallback icon from Qt themes if available
                fallback_icon = QIcon.fromTheme(
                    "audio-input-microphone",
                    QIcon(
                        ":/qt-project.org/styles/commonstyle/images/standardbutton-cancel-16.png"
                    ),
                )  # Example fallback
                if not fallback_icon.isNull():
                    self.tray_icon.setIcon(fallback_icon)
                else:
                    logger.error("Could not load primary or fallback tray icon.")

            # Create tray menu
            tray_menu = QMenu()

            # Show action
            show_action = QAction("Show App", self)
            show_action.triggered.connect(self._emit_show_app)  # Emit signal
            tray_menu.addAction(show_action)

            # Separator
            tray_menu.addSeparator()

            # Quit action
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self._emit_quit_app)  # Emit signal
            tray_menu.addAction(quit_action)

            # Set tray menu
            self.tray_icon.setContextMenu(tray_menu)

            # Show tray icon
            self.tray_icon.show()

            # Connect activation signal
            self.tray_icon.activated.connect(self._tray_icon_activated)

            logger.info("System tray icon setup complete")
        except Exception as e:
            logger.error(f"Error setting up system tray icon: {e}")
            logger.error(traceback.format_exc())
            self.tray_icon = None  # Ensure tray_icon is None if setup fails

    def _tray_icon_activated(self, reason):
        """Handle tray icon activation (left-click)"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Emit signal for MainWindow to handle show/hide
            self._emit_show_app()

    def _emit_show_app(self):
        """Emit signal to show the main window"""
        self.show_app_signal.emit()

    def _emit_quit_app(self):
        """Emit signal to quit the application"""
        self.quit_app_signal.emit()

    def is_visible(self):
        """Check if the tray icon is visible"""
        return self.tray_icon is not None and self.tray_icon.isVisible()

    def set_icon(self, icon_path):
        """Update the tray icon"""
        # Resolve path before using
        resolved_path = resource_path(icon_path)
        if self.tray_icon:
            if os.path.exists(resolved_path):
                self.tray_icon.setIcon(QIcon(resolved_path))
            else:
                logger.warning(
                    f"Icon path for tray update not found at resolved path: {resolved_path}"
                )

    def show_message(
        self, title, message, icon=QSystemTrayIcon.MessageIcon.Information, msecs=5000
    ):
        """Show a balloon message from the tray icon"""
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, msecs)
        else:
            logger.warning("Cannot show tray message: tray icon not available.")
