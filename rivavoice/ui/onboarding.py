import sys
import logging
import webbrowser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                           QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap

# Change to absolute imports
from rivavoice.ui.components import StyledLineEdit, StyledButton, CardContainer
from rivavoice import constants

logger = logging.getLogger(constants.APP_NAME) # Use constant

class OnboardingDialog(QDialog):
    """Dialog shown on first run to guide user through setup"""

    # Removed api_key_saved signal
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set window properties using constants
        self.setWindowTitle(f"Welcome to {constants.APP_NAME}")
        self.setFixedSize(400, 420) # Adjusted height slightly

        # Remove title bar and make background transparent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Initialize UI
        self.init_ui()

        logger.info("Onboarding dialog initialized")

    def init_ui(self):
        """Initialize the dialog UI"""
        # Main layout with margins for shadow
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create card container
        card = CardContainer(width=360, height=380) # Adjusted height slightly
        main_layout.addWidget(card)

        # Card layout
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        # Welcome title using constant
        title = QLabel(f"Welcome to {constants.APP_NAME}")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4E3FCA;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        # App description using constant
        description = QLabel(
            f"{constants.APP_NAME} transcribes your speech using advanced AI models."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 14px; color: #374151; margin-bottom: 10px;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(description)

        # API key explanation
        # Configuration explanation
        config_explanation = QLabel(
            "To use RivaVoice, you'll need an API key from a supported provider "
            "(like ElevenLabs or OpenAI).\n\n"
            "Please configure your provider and API key in the <b>Settings</b> screen "
            "after clicking 'Continue'."
        )
        config_explanation.setWordWrap(True)
        config_explanation.setStyleSheet("font-size: 14px; color: #374151;")
        config_explanation.setTextFormat(Qt.TextFormat.RichText) # Allow bold tag
        card_layout.addWidget(config_explanation)

        # Expanding spacer
        card_layout.addStretch()

        # FN key note for Mac users
        if sys.platform == 'darwin':
            # Use constant for default keybind display
            fn_note = QLabel(
                f"Note: This app uses the {constants.DEFAULT_KEYBIND.upper()} key by default. You may need to "
                "disable its special function in macOS: System Settings > Keyboard > "
                "Keyboard Shortcuts > Function Keys."
            )
            fn_note.setWordWrap(True)
            fn_note.setStyleSheet("""
                font-size: 12px;
                color: #6B7280;
                background-color: #F9FAFB;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #E5E7EB;
            """)
            card_layout.addWidget(fn_note)

            # Small spacer
            card_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Continue button
        continue_button = StyledButton("Continue")
        continue_button.clicked.connect(self.continue_onboarding)
        card_layout.addWidget(continue_button)

    def continue_onboarding(self):
        """Close the onboarding dialog."""
        logger.info("Onboarding finished, closing dialog.")
        self.accept()

# For testing
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = OnboardingDialog()
    dialog.show()

    sys.exit(app.exec())
