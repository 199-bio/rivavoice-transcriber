import sys
import logging
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

# Change to absolute imports
from rivavoice.ui.components import PulsingOrb, IconButton
from rivavoice import constants
from rivavoice.utils import resource_path

logger = logging.getLogger(constants.APP_NAME)  # Use constant


class RecordingView(QWidget):
    """The main recording interface view"""

    # Signals
    show_settings_signal = pyqtSignal()
    start_recording_signal = pyqtSignal()  # Note: These signals seem unused currently
    stop_recording_signal = pyqtSignal()  # Note: These signals seem unused currently
    close_app_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.keybind_display = constants.DEFAULT_KEYBIND.upper()  # Use constant default
        self.init_ui()

    def init_ui(self):
        """Initialize the recording view UI"""
        logger.info("Initializing recording view UI")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header section
        header_layout = QHBoxLayout()

        # App title with logo
        logo_label = QLabel()
        # Use resource_path for logo
        logo_path = resource_path(
            constants.ICON_APP_SVG
        )  # Use constant & resource_path
        try:
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToHeight(
                    30, Qt.TransformationMode.SmoothTransformation
                )
                logo_label.setPixmap(pixmap)
                logo_label.setStyleSheet("background-color: transparent;")
            else:
                logger.warning(f"Could not load logo pixmap from: {logo_path}")
                # Fallback to text if logo can't be loaded
                logo_label.setText(constants.APP_NAME)  # Use constant
                logo_label.setStyleSheet(
                    """
                    font-size: 20px;
                    font-weight: bold;
                    color: #4E3FCA;
                    background-color: transparent;
                """
                )
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
            # Fallback to text
            logo_label.setText(constants.APP_NAME)  # Use constant
            logo_label.setStyleSheet(
                """
                font-size: 20px;
                font-weight: bold;
                color: #4E3FCA;
                background-color: transparent;
            """
            )

        header_layout.addWidget(logo_label)

        # Spacer to push buttons to the right
        header_layout.addStretch()

        # Settings and close buttons
        # Use resource_path for icons
        settings_icon_path = resource_path(
            constants.ICON_SETTINGS_SVG
        )  # Use constant & resource_path
        settings_button = IconButton(settings_icon_path, self, size=20)
        settings_button.setToolTip("Settings")
        settings_button.clicked.connect(self.show_settings_signal.emit)

        close_icon_path = resource_path(
            constants.ICON_CLOSE_SVG
        )  # Use constant & resource_path
        close_button = IconButton(close_icon_path, self, size=20)
        close_button.setToolTip("Close")
        close_button.clicked.connect(self.close_app_signal.emit)

        header_layout.addWidget(settings_button)
        header_layout.addWidget(close_button)

        main_layout.addLayout(header_layout)

        # Add spacer between header and orb
        main_layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        # Create orb in the middle
        orb_layout = QVBoxLayout()
        orb_layout.setContentsMargins(
            0, 20, 0, 0
        )  # Add 20px spacing at top to move orb down

        self.orb = PulsingOrb(self, size=182)  # Increased by 30% from 140 to 182
        orb_layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(orb_layout)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            """
            font-size: 16px;
            color: #6B7280;
            margin-top: 16px;
            background-color: transparent;
        """
        )
        main_layout.addWidget(self.status_label)

        # Transcription info
        self.transcription_label = QLabel("")
        self.transcription_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transcription_label.setStyleSheet(
            """
            font-size: 14px;
            color: #9CA3AF;
            margin-top: 8px;
            background-color: transparent;
        """
        )
        self.transcription_label.setWordWrap(True)
        main_layout.addWidget(self.transcription_label)

        # Push everything else to the bottom
        main_layout.addStretch()

        # Instructions
        self.instructions_label = QLabel(
            f"Double press {self.keybind_display} to record. Press again to stop"
        )
        self.instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instructions_label.setStyleSheet(
            """
            font-size: 14px;
            color: #6B7280;
            background-color: transparent;
        """
        )
        main_layout.addWidget(self.instructions_label)

        # Paste info
        paste_info = QLabel("Transcription will be pasted at cursor position")
        paste_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        paste_info.setStyleSheet(
            """
            font-size: 12px;
            color: #9CA3AF;
            margin-bottom: 16px;
            background-color: transparent;
        """
        )
        main_layout.addWidget(paste_info)

    def set_keybind_display(self, display_name, trigger_type):
        """Update the instructions to show the current keybind and required action"""
        self.keybind_display = display_name
        if trigger_type == "double_press_toggle":
            instruction_text = (
                f"Double press {self.keybind_display} to record. Press again to stop"
            )
        else:  # 'toggle'
            instruction_text = (
                f"Press {self.keybind_display} to record. Press again to stop"
            )
        self.instructions_label.setText(instruction_text)

    def set_recording_state(self, is_recording):
        """Update UI to reflect recording state"""
        self.orb.set_recording(is_recording)

        if is_recording:
            self.status_label.setText("Recording...")
        else:
            self.status_label.setText("Ready")
            self.transcription_label.setText("")  # Clear transcription on stop

        if is_recording:
            self.transcription_label.setText("")  # Clear transcription on start

    def update_status(self, status_text):
        """Update the status label"""
        self.status_label.setText(status_text)

    def update_transcription_info(self, word_count, char_count):
        """Update the transcription info label"""
        self.transcription_label.setText(
            f"Transcription: {word_count} words, {char_count} characters"
        )

    def update_partial_status(self, delta_text: str):
        """Append partial transcription delta to the transcription label."""
        current_text = self.transcription_label.text()
        # Simple append for now. More sophisticated logic could handle replacements if needed.
        self.transcription_label.setText(current_text + delta_text)


# For demonstration purposes - to be imported as needed
if __name__ == "__main__":
    # Simple test code for the recording view
    from PyQt6.QtWidgets import QApplication
    from .components import CardContainer

    app = QApplication(sys.argv)

    # Create a test container
    container = CardContainer()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    # Add the recording view
    recording_view = RecordingView()
    layout.addWidget(recording_view)

    container.show()

    sys.exit(app.exec())
