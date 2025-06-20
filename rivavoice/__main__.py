#!/usr/bin/env python3

"""
RivaVoice - Minimalist speech-to-text app with a card-based interface
"""

import os
import sys
import logging
import traceback
import subprocess
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtCore import QTimer

# Import constants first
from rivavoice import constants  # Change to absolute import
from rivavoice.ui.main_window import MainWindow

# Define logger at module level
logger = logging.getLogger(constants.APP_NAME)


def setup_logging():
    """Configure application logging"""
    log_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        f"{constants.APP_NAME.lower()}.log",
    )
    logging.basicConfig(
        level=logging.INFO,  # Changed default level to INFO
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),  # Use log file in project root
            logging.StreamHandler(),
        ],
    )
    # Silence noisy libraries by setting their log level higher
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    # logger = logging.getLogger(constants.APP_NAME)  # Use constant - Defined globally now
    logger.info(f"Logging initialized (Level: INFO, File: {log_file})") # Corrected level
    return logger


def exception_hook(exctype, value, traceback_obj):
    """Global exception handler to log unhandled exceptions"""
    logger = logging.getLogger(constants.APP_NAME)  # Use constant
    logger.critical(f"Uncaught exception: {exctype} - {value}")
    logger.critical("".join(traceback.format_tb(traceback_obj)))
    # Call the original excepthook too
    if hasattr(sys, "_excepthook") and sys._excepthook:
        sys._excepthook(exctype, value, traceback_obj)
    else:
        sys.__excepthook__(exctype, value, traceback_obj)


def check_microphone_permission():
    """Check if microphone permission is granted"""
    logger = logging.getLogger(constants.APP_NAME)  # Get logger instance
    try:
        # On macOS we can try to record a small amount of audio to trigger the permission dialog
        import pyaudio

        p = pyaudio.PyAudio()
        stream = p.open(
            format=constants.AUDIO_FORMAT,  # Use constant
            channels=constants.AUDIO_CHANNELS,  # Use constant
            rate=constants.AUDIO_RATE,  # Use constant
            input=True,
            frames_per_buffer=constants.AUDIO_CHUNK,
        )  # Use constant
        stream.read(constants.AUDIO_CHUNK)  # Try to read a bit of audio
        stream.stop_stream()
        stream.close()
        p.terminate()
        logger.info("Microphone permission check successful (or already granted).")
        return True
    except ImportError:
        logger.error("PyAudio library not found. Cannot check microphone permissions.")
        return False  # Assume no permission if library missing
    except Exception as e:
        logger.warning(f"Microphone permission check failed: {e}")
        return False


def show_permission_instructions():
    """Show instructions for granting permissions"""
    msg = QMessageBox()
    msg.setWindowTitle(f"{constants.APP_NAME} Permissions Required")  # Use constant
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setText(
        f"{constants.APP_NAME} requires certain permissions to function properly:"
    )  # Use constant

    detailed_text = (
        "1. Microphone Access:\n"
        "   • When prompted, click 'OK' to allow microphone access\n"
        f"   • If you missed the prompt, go to System Settings > Privacy & Security > Microphone\n\n"
        "2. Input Monitoring (for keyboard shortcuts):\n"
        "   • Go to System Settings > Privacy & Security > Input Monitoring\n"
        f"   • Add {constants.APP_NAME}.app to the list of allowed applications\n"  # Use constant
        "   • You may need to restart the app after granting permissions\n\n"
        "The app will now continue, but may have limited functionality until all permissions are granted."
    )

    msg.setDetailedText(detailed_text)

    # Add "Open System Settings" button
    msg.setStandardButtons(
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Help
    )
    help_button = msg.button(QMessageBox.StandardButton.Help)
    help_button.setText("Open Privacy Settings")

    result = msg.exec()

    # If user clicked "Open Privacy Settings"
    if result == QMessageBox.StandardButton.Help:
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.Popen(
                    ["open", constants.MACOS_PRIVACY_URL_GENERAL]
                )  # Use constant
            # Add handlers for other platforms if needed
        except Exception as e:
            logging.getLogger(constants.APP_NAME).error(
                f"Failed to open system settings: {e}"
            )  # Use constant


class SingleApplication(QApplication):
    """Application class that ensures only one instance runs at a time"""

    def __init__(self, argv, app_id):
        super().__init__(argv)
        self.app_id = app_id
        self._server = None
        self.is_first_instance = self._check_instance()

    def _check_instance(self):
        """Check if another instance is already running

        Returns True if this is the first instance, False otherwise
        """
        # Create a local socket and try to connect to an existing server
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        if socket.waitForConnected(500):
            # Another instance exists - we'll exit
            logging.getLogger(constants.APP_NAME).info(
                "Another instance is already running"
            )  # Use constant
            socket.disconnectFromServer()
            return False

        # No existing instance found, start a local server
        self._server = QLocalServer()
        # Make sure we clean up any stale server
        self._server.removeServer(self.app_id)
        # Start the server
        if not self._server.listen(self.app_id):
            logger.error(
                f"Failed to listen on server name {self.app_id}. Another instance might be starting up or a stale server exists."
            )
            # Attempt to connect again just in case
            socket.connectToServer(self.app_id)
            if socket.waitForConnected(100):
                logger.info("Connected to existing instance after listen failure.")
                socket.disconnectFromServer()
                return False
            else:
                logger.warning(
                    "Could not establish server. Assuming this is the first instance, but conflicts might occur."
                )
                # Proceed, but log the potential issue
        return True


def main():
    """Main application entry point"""
    logger = None  # Initialize logger to None
    try:
        # Setup logging
        logger = setup_logging()

        # Configure exception handling for PyQt
        sys._excepthook = sys.excepthook  # Store original excepthook
        sys.excepthook = exception_hook

        # Fix for PyQt6 keyboard integration issue on macOS
        if sys.platform == "darwin":
            os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
            logger.info("Set OBJC_DISABLE_INITIALIZE_FORK_SAFETY for macOS")

        # Create single instance application using constant
        # Use a more specific app_id based on bundle ID if available
        app_instance_id = constants.BUNDLE_ID or f"{constants.APP_NAME}AppInstance"
        app = SingleApplication(sys.argv, app_instance_id)

        # Check if this is the first instance
        if not app.is_first_instance:
            logger.info("Application already running, exiting")
            # Show a brief notification using constant
            QMessageBox.information(
                None, constants.APP_NAME, f"{constants.APP_NAME} is already running"
            )
            # Exit after a short delay
            QTimer.singleShot(500, lambda: sys.exit(0))
            # Need to start and return the exec loop for the message box to show
            return app.exec()  # Important!

        # Set app ID for taskbar grouping using constants
        app.setApplicationName(constants.APP_NAME)
        app.setOrganizationName(constants.ORG_NAME)

        # Set app icon using constant
        # TODO: Use importlib.resources later
        icon_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", constants.ICON_APP_ICNS)
        )  # Use constant
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            logger.info(f"Set application icon: {icon_path}")
        else:
            logger.warning(f"Icon file not found: {icon_path}")

        # Show permission instructions on first run or if permissions needed
        # Use a flag file in a more standard location (e.g., config dir)
        # For now, keep using ~/.rivavoice_shown_permissions
        flag_file = os.path.expanduser(
            f"~/.{constants.APP_NAME.lower()}_shown_permissions"
        )  # Use constant
        if not os.path.exists(flag_file):
            show_permission_instructions()
            # Create the flag file
            try:
                with open(flag_file, "w") as f:
                    f.write("1")
            except IOError as e:
                logger.error(f"Could not create permissions flag file: {e}")

        # Additionally, check microphone permission and show instructions if needed
        if not check_microphone_permission():
            logger.warning("Microphone permission not granted")
            QMessageBox.warning(
                None,
                "Microphone Access Required",
                f"{constants.APP_NAME} needs microphone access to function properly.\n\n"  # Use constant
                "Please grant permission when prompted, or go to\n"
                "System Settings > Privacy & Security > Microphone.",
            )

        # Create and show the main window
        main_window = MainWindow()
        main_window.show()

        logger.info("Application started")

        # Start event loop
        sys.exit(app.exec())

    except Exception as e:
        # Use logger if initialized, otherwise print to stderr
        log_func = (
            logger.critical if logger else lambda msg: print(msg, file=sys.stderr)
        )
        log_func(f"Critical application error: {e}")
        log_func(traceback.format_exc())

        # Show error message if possible (QApplication might not be running)
        try:
            # Check if QApplication instance exists before showing message box
            if QApplication.instance():
                QMessageBox.critical(
                    None,
                    "Critical Error",
                    f"The application encountered a critical error and must exit:\n\n{str(e)}",
                )
            else:
                print(f"CRITICAL ERROR (GUI not available): {e}", file=sys.stderr)
        except Exception as msg_e:
            print(
                f"CRITICAL ERROR (Could not show message box: {msg_e}): {e}",
                file=sys.stderr,
            )

        sys.exit(1)


if __name__ == "__main__":
    main()
