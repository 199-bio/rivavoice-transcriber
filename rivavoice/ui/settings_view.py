import sys
import os
import logging
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QComboBox,
)
from PyQt6.QtCore import pyqtSignal  # Added QSize
# from PyQt6.QtGui import QIcon  # Added QIcon

# Change to absolute imports
from rivavoice.ui.components import (
    IconButton,
    StyledButton,
    StyledLineEdit,
    ToggleSwitch,
    KeybindSelector,
)

# Import new constants
from rivavoice import constants
from rivavoice.utils import resource_path

logger = logging.getLogger(constants.APP_NAME)  # Use constant


class SettingsView(QWidget):
    """Settings view for the application"""

    # Signals
    close_settings_signal = pyqtSignal()
    save_settings_signal = pyqtSignal(dict)

    def __init__(self, parent=None, config=None):
        super().__init__(parent)

        self.config = config or constants.DEFAULT_CONFIG.copy()
        # Store model info for easy lookup
        self.model_data = {model["id"]: model for model in constants.AVAILABLE_MODELS}

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the settings view UI"""
        logger.info("Initializing settings view UI")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)  # Reduced spacing

        # Header section
        header_layout = QHBoxLayout()

        # Settings title
        title_label = QLabel("Settings")
        # Style based on .settings-title
        title_label.setStyleSheet(
            """
            font-size: 16px; /* Approx 1.25rem */
            font-weight: 600;
            color: #6366f1;
            background-color: transparent;
        """
        )
        header_layout.addWidget(title_label)

        # Spacer to push buttons to the right
        header_layout.addStretch()

        # Close button - Use resource_path
        close_icon_path = resource_path(
            constants.ICON_CLOSE_SVG
        )  # Use constant & resource_path
        close_button = IconButton(
            close_icon_path, self, size=16
        )  # Match SVG size in example
        close_button.setToolTip("Close")
        close_button.clicked.connect(self.close_settings_signal.emit)

        header_layout.addWidget(close_button)

        main_layout.addLayout(header_layout)

        # Add spacer between header and form
        # Removed extra spacer

        # Vertical layout for settings (labels above inputs)
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(0, 10, 0, 0)  # Add some top margin
        settings_layout.setSpacing(10)  # Vertical spacing between items

        # --- Info Label for Initial Configuration ---
        self.info_label = QLabel("")
        self.info_label.setStyleSheet(
            """
            QLabel {
                background-color: #FEFCE8; /* Light yellow */
                color: #A16207; /* Dark yellow text */
                border: 1px solid #FDE68A; /* Yellow border */
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                margin-bottom: 8px; /* Space below the label */
            }
        """
        )
        self.info_label.setWordWrap(True)
        self.info_label.setVisible(False)  # Hidden by default
        settings_layout.addWidget(self.info_label)

        # --- Model Selection ---
        model_label = QLabel("Model")
        model_label.setStyleSheet(
            "font-weight: 500; margin-bottom: 2px; background-color: transparent;"
        )  # Added style
        settings_layout.addWidget(model_label)

        self.model_selector = QComboBox()
        # Simplified style based on .form-select
        self.model_selector.setStyleSheet(
            """
            QComboBox {
                padding: 8px; /* Approx 0.5rem */
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
                font-size: 14px; /* Approx 0.875rem */
            }
            QComboBox::drop-down {
                /* Use native arrow */
                border: none;
                width: 15px;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d1d5db;
                background-color: white;
                selection-background-color: #e0e7ff;
                selection-color: #1f2937; /* Added for readable selected text */
            }
            QComboBox:focus {
                 border: 1px solid #6366f1; /* Match target focus */
            }
        """
        )
        for model in constants.AVAILABLE_MODELS:
            # Store internal ID and provider type as data
            self.model_selector.addItem(
                model["display"],
                userData={"id": model["id"], "provider": model["provider"]},
            )
        self.model_selector.currentIndexChanged.connect(self._update_api_key_field)
        settings_layout.addWidget(self.model_selector)
        settings_layout.addSpacing(8)  # Add spacing after item

        # --- API Key (Single Field) ---
        self.api_key_label = QLabel("API Key")  # Label text updated dynamically
        self.api_key_label.setStyleSheet(
            "font-weight: 500; margin-bottom: 2px; background-color: transparent;"
        )  # Added style
        settings_layout.addWidget(self.api_key_label)

        self.api_key_input = StyledLineEdit(
            placeholder="Enter API key", is_password=True
        )  # Placeholder updated dynamically
        settings_layout.addWidget(self.api_key_input)
        settings_layout.addSpacing(8)  # Add spacing after item

        # --- Transcript Folder ---
        transcript_folder_label = QLabel("Transcript Folder")
        transcript_folder_label.setStyleSheet(
            "font-weight: 500; margin-bottom: 2px; background-color: transparent;"
        )  # Added style
        settings_layout.addWidget(transcript_folder_label)

        self.folder_path_input = StyledLineEdit()  # Changed from QLabel
        self.folder_path_input.setReadOnly(True)
        self.folder_path_input.setToolTip(
            "Transcript save location"
        )  # Tooltip stores full path

        browse_button = StyledButton("Browse", is_text_button=True)
        # Use simplified style matching other inputs/buttons
        browse_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 12px; /* Approx 0.5rem 0.75rem */
                background-color: white;
                border: 1px solid #d1d5db; /* Match input border */
                border-radius: 4px; /* Match input radius */
                font-size: 14px; /* Match input font size */
                color: #374151; /* Default text color */
                font-weight: 500;
            }
            QPushButton:hover { background-color: #f9fafb; } /* Lighter hover */
            QPushButton:pressed { background-color: #f3f4f6; } /* Slightly darker pressed */
        """
        )
        browse_button.clicked.connect(self.browse_folder)

        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(8)  # Gap from example
        folder_layout.addWidget(self.folder_path_input, 1)  # Let input expand
        folder_layout.addWidget(browse_button)
        settings_layout.addLayout(folder_layout)
        settings_layout.addSpacing(8)  # Add spacing after item

        # --- Recording Shortcut ---
        shortcut_label = QLabel("Recording Shortcut")
        shortcut_label.setStyleSheet(
            "font-weight: 500; margin-bottom: 2px; background-color: transparent;"
        )  # Added style
        settings_layout.addWidget(shortcut_label)

        self.keybind_selector = KeybindSelector()
        settings_layout.addWidget(self.keybind_selector)
        settings_layout.addSpacing(8)  # Add spacing after item

        # --- Sound Effects Toggle ---
        # Use QHBoxLayout for label + toggle alignment
        sound_layout = QHBoxLayout()
        sound_label = QLabel("Sound effects")
        sound_label.setStyleSheet(
            "font-weight: 500; background-color: transparent;"
        )  # Added style
        sound_layout.addWidget(sound_label)
        sound_layout.addStretch()  # Push toggle to the right

        self.sounds_toggle = ToggleSwitch()
        self.sounds_toggle.toggled.connect(self.on_sounds_toggled)
        sound_layout.addWidget(self.sounds_toggle)
        settings_layout.addLayout(sound_layout)
        settings_layout.addSpacing(8)  # Add spacing after item

        # --- Paste Toggle ---
        # Use QHBoxLayout for label + toggle alignment
        paste_layout = QHBoxLayout()
        paste_label = QLabel("Paste after transcription")
        paste_label.setStyleSheet(
            "font-weight: 500; background-color: transparent;"
        )  # Added style
        paste_layout.addWidget(paste_label)
        paste_layout.addStretch()  # Push toggle to the right

        self.paste_toggle = ToggleSwitch()
        self.paste_toggle.toggled.connect(self.on_paste_toggled)
        paste_layout.addWidget(self.paste_toggle)
        settings_layout.addLayout(paste_layout)
        # No spacing needed after the last item before the stretch

        # --- Common Settings ---
        # Spacing adjusted by QFormLayout

        # Removed old Transcript Folder section, integrated into QFormLayout above

        # Removed old Keybind section, integrated into QFormLayout above

        # Removed old Sound Effects section, integrated into QFormLayout above

        # Removed old Paste Toggle section, integrated into QFormLayout above

        main_layout.addLayout(settings_layout)

        # Add expanding spacer
        main_layout.addStretch()

        # Save button
        # Footer section
        footer_layout = QVBoxLayout()  # Use QVBoxLayout to allow button to span width
        footer_layout.setContentsMargins(0, 16, 0, 0)  # Add top margin

        save_button = StyledButton("Save Settings")
        # Style based on .save-button
        save_button.setStyleSheet(
            """
            QPushButton {
                padding: 10px; /* Approx 0.625rem */
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 500;
                font-size: 14px; /* Match other inputs */
            }
            QPushButton:hover { background-color: #4f46e5; }
            QPushButton:pressed { background-color: #4338ca; }
        """
        )
        save_button.clicked.connect(self.save_settings)
        footer_layout.addWidget(save_button)

        main_layout.addLayout(footer_layout)

        # Call initial API key field update after UI is built
        self._update_api_key_field()

    def format_path(self, path, max_length=25):
        """Format path to show ellipsis at the beginning if too long"""
        if len(path) <= max_length:
            return path

        # Split path to get components
        drive, tail = os.path.splitdrive(path)
        parts = tail.split(os.sep)

        # Keep the drive and last few components if possible
        if len(parts) > 2:
            formatted = drive + os.sep + "..." + os.sep + os.sep.join(parts[-2:])
        else:
            # Fallback if path is too short after split
            formatted = drive + os.sep + "..." + os.sep + tail

        return formatted

    def _update_api_key_field(self):
        """Updates the API key label, placeholder, and value based on selected model."""
        current_data = self.model_selector.currentData()
        if not current_data:
            logger.warning("No model data found for current selection.")
            return

        provider = current_data.get("provider")
        model_id = current_data.get("id")
        logger.debug(f"Selected model '{model_id}' with provider '{provider}'")

        api_key = ""
        label_text = "API Key"
        placeholder_text = "Enter API key"

        if provider == "openai":
            label_text = "OpenAI API Key"
            placeholder_text = "Enter OpenAI API key (sk-...)"
            api_key = self.config.get(constants.CONFIG_OPENAI_API_KEY, "")
        elif provider == "elevenlabs":
            label_text = "ElevenLabs API Key"
            placeholder_text = "Enter ElevenLabs API key"
            api_key = self.config.get(constants.CONFIG_ELEVENLABS_API_KEY, "")
        else:
            logger.error(
                f"Unknown provider '{provider}' associated with model '{model_id}'"
            )

        self.api_key_label.setText(label_text)
        self.api_key_input.setPlaceholderText(placeholder_text)
        self.api_key_input.setText(api_key)

    def load_config(self):
        """Load config values into UI fields"""
        logger.info("Loading configuration into settings UI...")

        # Model Selection
        selected_model_id = self.config.get(
            constants.CONFIG_SELECTED_MODEL_ID, constants.DEFAULT_MODEL_ID
        )
        index = self.model_selector.findData(
            lambda data: data and data.get("id") == selected_model_id
        )
        if index != -1:
            self.model_selector.setCurrentIndex(index)
        else:
            logger.warning(
                f"Saved model ID '{selected_model_id}' not found in available models. Defaulting."
            )
            self.model_selector.setCurrentIndex(0)  # Default to first item

        # Trigger API key field update based on loaded model (will load correct key)
        self._update_api_key_field()

        # Common Settings
        folder_path = self.config.get(
            constants.CONFIG_TRANSCRIPT_FOLDER, constants.DEFAULT_TRANSCRIPT_FOLDER
        )
        self.folder_path_input.setText(
            self.format_path(folder_path)
        )  # Update input field
        self.folder_path_input.setToolTip(folder_path)  # Store full path here

        keybind = self.config.get(constants.CONFIG_KEYBIND, constants.DEFAULT_KEYBIND)
        self.keybind_selector.set_keybind(keybind)

        # Set toggles using constants for keys and defaults
        self.sounds_toggle.is_checked = self.config.get(
            constants.CONFIG_SOUND_EFFECTS, constants.DEFAULT_SOUND_EFFECTS
        )  # Use correct default constant
        # self.nonspeech_toggle.is_checked = self.config.get(constants.CONFIG_INCLUDE_NON_SPEECH, constants.DEFAULT_CONFIG[constants.CONFIG_INCLUDE_NON_SPEECH]) # Removed
        self.paste_toggle.is_checked = self.config.get(
            constants.CONFIG_PASTE_AFTER_TRANSCRIPTION,
            constants.DEFAULT_PASTE_AFTER_TRANSCRIPTION,
        )

        logger.info(f"Loaded selected model ID: {selected_model_id}")
        # logger.info(f"Loaded include_non_speech: {self.nonspeech_toggle.is_checked}") # Removed
        logger.info(f"Loaded paste_after_transcription: {self.paste_toggle.is_checked}")

        # Update toggle visuals
        self._update_toggle_visuals()
        # No need for provider visibility update anymore

    def _update_toggle_visuals(self):
        """Updates the visual state of all toggle switches."""
        try:
            # Update toggle positions to match states
            self.sounds_toggle._toggle_position = (
                1.0 if self.sounds_toggle.is_checked else 0.0
            )
            # self.nonspeech_toggle._toggle_position = 1.0 if self.nonspeech_toggle.is_checked else 0.0 # Removed
            self.paste_toggle._toggle_position = (
                1.0 if self.paste_toggle.is_checked else 0.0
            )
            self.sounds_toggle.update()
            # self.nonspeech_toggle.update() # Removed
            self.paste_toggle.update()
        except Exception as e:
            logger.error(f"Error setting toggle position: {e}")

    def browse_folder(self):
        """Open file dialog to select transcript folder"""
        current_folder = self.folder_path_input.toolTip() or os.path.expanduser(
            "~"
        )  # Use input's tooltip
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Transcript Folder",
            current_folder,
            QFileDialog.Option.ShowDirsOnly,
        )

        if folder:
            self.folder_path_input.setText(
                self.format_path(folder)
            )  # Update input field
            self.folder_path_input.setToolTip(folder)  # Store full path in tooltip

    def on_sounds_toggled(self, state):
        """Handle sounds toggle state change"""
        self.sounds_toggle.is_checked = state
        logger.info(f"Sound effects toggled: {state}")

    # Removed on_nonspeech_toggled

    def on_paste_toggled(self, state):
        """Handle paste toggle state change"""
        self.paste_toggle.is_checked = state
        logger.info(f"Paste after transcription toggled: {state}")

    def save_settings(self):
        """Collect settings and emit save signal"""
        selected_model_data = self.model_selector.currentData()
        if not selected_model_data:
            logger.error("Cannot save settings, no model selected.")
            # Optionally show an error message to the user
            return

        selected_model_id = selected_model_data.get("id")
        provider = selected_model_data.get("provider")
        api_key = self.api_key_input.text()

        settings = {
            constants.CONFIG_SELECTED_MODEL_ID: selected_model_id,
            # Save the entered API key to the correct provider-specific key
            constants.CONFIG_OPENAI_API_KEY: (
                api_key
                if provider == "openai"
                else self.config.get(constants.CONFIG_OPENAI_API_KEY, "")
            ),
            constants.CONFIG_ELEVENLABS_API_KEY: (
                api_key
                if provider == "elevenlabs"
                else self.config.get(constants.CONFIG_ELEVENLABS_API_KEY, "")
            ),
            constants.CONFIG_TRANSCRIPT_FOLDER: self.folder_path_input.toolTip(),  # Get path from input's tooltip
            constants.CONFIG_KEYBIND: self.keybind_selector.get_keybind(),
            constants.CONFIG_SOUND_EFFECTS: self.sounds_toggle.is_checked,
            constants.CONFIG_PASTE_AFTER_TRANSCRIPTION: self.paste_toggle.is_checked,
            # Removed provider and non-speech settings
        }

        logger.info(
            f"Saving settings with selected model: {selected_model_id} (Provider: {provider})"
        )
        self.save_settings_signal.emit(settings)

    def show_configuration_guidance(self, show: bool, message: str = None):
        """Shows or hides the initial configuration guidance message."""
        if show:
            default_message = (
                "Welcome! Please select your desired model and enter the "
                "corresponding API key to enable recording."
            )
            self.info_label.setText(message or default_message)
            self.info_label.setVisible(True)
        else:
            self.info_label.setVisible(False)


# For testing purposes
if __name__ == "__main__":
    # Simple test code for the settings view
    from PyQt6.QtWidgets import QApplication
    from .components import CardContainer

    app = QApplication(sys.argv)

    # Create a test container
    container = CardContainer()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    # Add the settings view
    settings_view = SettingsView()
    layout.addWidget(settings_view)

    container.show()

    sys.exit(app.exec())
