"""
Main application window for RivaVoice.

Handles UI setup, event loops, recording control, transcription provider management,
settings integration, and system tray interactions.
"""
import sys
import os
import logging
import pyperclip  # For clipboard copy
import traceback
import datetime
import subprocess
import time  # Needed for the new activation logic
import threading  # Needed for paste timer and asyncio loop
import asyncio  # Needed for OpenAI real-time
from typing import Optional  # Added for type hinting
from dotenv import load_dotenv  # Added for .env file loading
from PyQt6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QDialog,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot  # Import QObject
# Removed unused QPixmap, QIcon, QAction

# Change to absolute imports
from rivavoice.ui.components import CardContainer
from rivavoice.ui.recording_view import RecordingView
from rivavoice.ui.settings_view import SettingsView
from rivavoice.ui.components import SAFE_KEYBINDS
from rivavoice.ui.onboarding import OnboardingDialog
from rivavoice.config import Config

# Use the new pyscribetranscribe module(s)
from pyscribetranscribe import AudioRecorder, AudioRecorderError
from pyscribetranscribe.transcriber import (
    ElevenLabsTranscriber,
    ElevenLabsTranscriberError,
)  # Renamed
from pyscribetranscribe.openai_realtime_transcriber import OpenAIRealtimeTranscriber # New - OpenAI Disabled # Removed OpenAIRealtimeError
# from pyscribetranscribe.openai_realtime_transcriber import OpenAIRealtimeTranscriber, OpenAIRealtimeError # New - OpenAI Disabled
# Use the new keybind module
from pykeybindmanager import (
    KeybindManager as PyKeybindManager,
    parse_keybind_string,
    PermissionError as KeybindPermissionError,
    InvalidKeybindError,
    PynputImportError,
    play_sound_file as play_keybind_sound,
)
# from rivavoice.utils import resource_path  # Keep resource_path if needed elsewhere

# from rivavoice.keybind_manager import KeybindManager # Old import removed
from rivavoice.tray_manager import TrayManager
from rivavoice import constants

# Removed old sound file path constants comments

logger = logging.getLogger(constants.APP_NAME)  # Use constant


class MainWindow(QMainWindow):
    """Main window containing the card-based interface"""

    def __init__(self):
        super().__init__()
        # --- Load .env file FIRST ---
        logger.info("Loading .env file...")
        load_dotenv()
        # ---------------------------

        # Initialize state
        self.is_processing_transcription = (
            False  # Flag to prevent duplicate transcriptions
        )

        # Initialize properties
        self.config = Config()
        self.recorder = AudioRecorder()
        # self.provider = None # Provider is now determined dynamically
        self.transcriber = None
        # Load model data mapping
        self.model_data = {model["id"]: model for model in constants.AVAILABLE_MODELS}
        self.keybind_data = None  # Store the active keybind *display* data locally
        self._py_keybind_manager = None  # Instance of the new manager
        self._current_keybind_obj = None  # Store the parsed keybind object

        # Asyncio loop management
        self.asyncio_loop = None
        self.asyncio_thread = None
        self._start_asyncio_thread()  # Start the asyncio loop thread

        # Initialize Managers
        self.tray_manager = None  # Initialize later in init_ui

        # Check if first run (no API key) - This might exit if onboarding is cancelled
        self.check_first_run()

        # Load config and initialize the correct provider/transcriber
        # This replaces the old _initialize_transcriber() call
        self._load_config_and_init_provider()

        # Initialize UI
        self.init_ui()

        # Setup callbacks for audio components
        self.setup_callbacks()

        # Initialize and start the new keybind manager
        self._initialize_keybind_manager()

        # Update keybind display (now separate from manager logic)
        self.update_keybind_display()

        # --- Initial View Logic ---
        # Check if API key is configured AFTER loading config and initializing UI components
        if not self._is_api_key_configured():
            logger.warning(
                "No valid API key configured for the selected model. Redirecting to Settings."
            )
            # Show guidance message in settings view (implementation in settings_view.py needed)
            if hasattr(self.settings_view, "show_configuration_guidance"):
                self.settings_view.show_configuration_guidance(True)
            self.stacked_widget.setCurrentWidget(self.settings_view)
        else:
            # Default to recording view if key is configured
            self.stacked_widget.setCurrentWidget(self.recording_view)

        # --- Initial View Logic ---
        # Check if API key is configured AFTER loading config and initializing UI components
        if not self._is_api_key_configured():
            logger.warning(
                "No valid API key configured for the selected model. Redirecting to Settings."
            )
            # Show guidance message in settings view (implementation in settings_view.py needed)
            if hasattr(self.settings_view, "show_configuration_guidance"):
                self.settings_view.show_configuration_guidance(True)
            self.stacked_widget.setCurrentWidget(self.settings_view)
        else:
            # Default to recording view if key is configured
            self.stacked_widget.setCurrentWidget(self.recording_view)

        logger.info("Main window initialized")

    def check_first_run(self):
        """Check if this is the first run and show onboarding if needed"""
        # Check for *any* relevant API key to decide if onboarding is needed
        # Check if *any* API key is configured (simplification)
        elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY") or self.config.get(
            constants.CONFIG_ELEVENLABS_API_KEY
        )
        openai_key = os.environ.get("OPENAI_API_KEY") or self.config.get(
            constants.CONFIG_OPENAI_API_KEY
        )
        if not elevenlabs_key and not openai_key:
            logger.info("No API key found - showing onboarding dialog")
            self.show_onboarding()

    def show_onboarding(self):
        """Show the simplified informational onboarding dialog"""
        onboarding = OnboardingDialog(self)
        # Removed connection to api_key_saved signal

        # Show dialog and wait for result
        result = onboarding.exec()

        # If dialog was rejected, exit the app
        # App should proceed even if onboarding is cancelled/closed without entering key
        if result != QDialog.DialogCode.Accepted:
            logger.info("Onboarding canceled or closed without entering key.")
        # Removed sys.exit(0)

    # Removed save_api_key method as onboarding no longer handles key input
    def update_keybind_display(self):
        """Update the keybind display in the recording view"""
        # Get current keybind key using constant
        keybind_key = self.config.get(
            constants.CONFIG_KEYBIND, constants.DEFAULT_KEYBIND
        )  # Use constants

        # Find the matching keybind data for display purposes
        self.keybind_data = next(
            (k for k in SAFE_KEYBINDS if k["key"] == keybind_key), None
        )

        # Default to FN if not found
        if not self.keybind_data:
            # Find the default keybind data from SAFE_KEYBINDS
            self.keybind_data = next(
                (k for k in SAFE_KEYBINDS if k["key"] == constants.DEFAULT_KEYBIND),
                SAFE_KEYBINDS[0],
            )  # Fallback to first if default not found

        # Update recording view display
        if hasattr(self, "recording_view"):  # Ensure view exists before updating
            # Determine trigger type again for passing to UI
            keybind_key_str = self.config.get(
                constants.CONFIG_KEYBIND, constants.DEFAULT_KEYBIND
            )
            trigger_type = (
                "double_press_toggle" if keybind_key_str == "fn" else "toggle"
            )
            self.recording_view.set_keybind_display(
                self.keybind_data["display"], trigger_type
            )
            logger.info(f"Updated keybind display to {self.keybind_data['display']}")
        else:
            logger.warning(
                "Recording view not yet initialized during update_keybind_display."
            )

    def init_ui(self):
        """Initialize the main window UI"""
        logger.info("Initializing main window UI")

        # Set window properties using constants
        self.setWindowTitle(constants.APP_NAME)
        self.setMinimumSize(
            458, 572
        )  # Keep hardcoded for now, or move to constants if preferred
        self.setMaximumSize(915, 880)  # Keep hardcoded for now

        # Make window frameless
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Set window style
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: transparent;
            }
        """
        )

        # Setup system tray icon using TrayManager
        self.tray_manager = TrayManager(self)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Create card container
        self.card = CardContainer()
        main_layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Create stacked widget for views
        self.stacked_widget = QStackedWidget()

        # Create card layout
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(self.stacked_widget)

        # Create views
        self.recording_view = RecordingView()
        self.settings_view = SettingsView(config=self.config.data)  # Pass config data

        # Add views to stacked widget
        self.stacked_widget.addWidget(self.recording_view)
        self.stacked_widget.addWidget(self.settings_view)

        # Show recording view by default
        self.stacked_widget.setCurrentWidget(self.recording_view)

        # Connect signals for UI navigation
        self.connect_ui_signals()

        # Connect signals for TrayManager
        self.connect_tray_signals()

        logger.info("Main window UI initialized")

    def connect_ui_signals(self):
        """Connect signals between views and controller"""
        # Recording view signals
        self.recording_view.show_settings_signal.connect(self.show_settings_view)
        self.recording_view.close_app_signal.connect(self.close)

        # Settings view signals
        self.settings_view.close_settings_signal.connect(self.show_recording_view)
        self.settings_view.save_settings_signal.connect(self.save_settings)

    def connect_tray_signals(self):
        """Connect signals from TrayManager"""
        if self.tray_manager:
            self.tray_manager.show_app_signal.connect(self._handle_show_app_signal)
            self.tray_manager.quit_app_signal.connect(self.quit_app)  # Connect directly

    def _get_current_provider_type(self):
        """Helper to determine provider type based on selected model."""
        selected_model_id = self.config.get(
            constants.CONFIG_SELECTED_MODEL_ID, constants.DEFAULT_MODEL_ID
        )
        model_info = self.model_data.get(selected_model_id)
        return model_info["provider"] if model_info else None

    def setup_callbacks(self):
        """Setup callbacks for the recorder based on the current provider."""
        provider_type = self._get_current_provider_type()
        logger.debug(
            f"Setting up recorder callbacks for provider type: {provider_type}"
        )
        # Basic Recorder callbacks (always set)
        self.recorder.on_recording_started = self.on_recording_started
        self.recorder.on_recording_stopped = (
            self.on_recording_stopped
        )  # Handles provider logic internally
        self.recorder.on_recording_error = self.on_recording_error

        # Provider-specific recorder setup
        # OpenAI block is disabled. The following code runs for ElevenLabs or any other non-OpenAI provider.
        # Ensure chunk_callback is None as it was only used for OpenAI real-time.
        self.recorder.chunk_callback = None
        # Ensure saving is enabled (it might have been disabled if previously in OpenAI mode).
        if (
            not self.recorder.recording_file
        ):  # If path is None (e.g., after switching from OpenAI)
            self.recorder.recording_file = (
                constants.DEFAULT_RECORDING_FILE
            )  # Use existing constant for full path
            logger.info(
                f"Ensured recorder file saving is enabled for non-OpenAI mode: {self.recorder.recording_file}"
            )
        self.recorder.save_enabled = True
        # Note: The erroneous call to setup_transcriber_callbacks was removed here.

    # Removed setup_elevenlabs_callbacks - handled in _load_config_and_init_provider

    # --- Provider/Transcriber Callback Handlers (Ensure UI updates are thread-safe) ---

    def _handle_partial_transcript(self, delta_text: str):
        """Handles partial transcript delta from OpenAI (called from asyncio thread)."""
        # logger.debug(f"Partial delta: {delta_text}") # Can be noisy
        # Use QTimer to safely trigger keystroke simulation from the main thread
        QTimer.singleShot(0, lambda: self._simulate_keystrokes(delta_text))

    def _handle_final_transcript(self, text: str):
        """Handles final transcript from OpenAI (called from asyncio thread)."""
        logger.info(f"Final transcript received (OpenAI): {len(text)} chars")
        word_count = len(text.split())
        char_count = len(text)
        # Use QTimer to safely call the completion handler from the main thread
        QTimer.singleShot(
            0, lambda: self.on_transcription_complete(text, word_count, char_count)
        )

    def _handle_transcription_error(self, error_message: str):
        """Handles errors from either transcriber (called from transcriber thread or asyncio thread)."""
        logger.error(f"Transcription error reported: {error_message}")
        # Use QTimer to safely update UI from the main thread
        QTimer.singleShot(
            0, lambda: self.recording_view.update_status(f"Error: {error_message}")
        )
        QTimer.singleShot(
            0, lambda: self.recording_view.set_recording_state(False)
        )  # Ensure UI reflects stopped state on error
        # Reset processing flag using QTimer
        QTimer.singleShot(
            0, lambda: setattr(self, "is_processing_transcription", False)
        )

    def _handle_connected(self):
        """Handles WebSocket connected event (called from asyncio thread)."""
        logger.info("OpenAI WebSocket connected.")
        # Use QTimer to safely update UI from the main thread
        QTimer.singleShot(0, lambda: self.update_status("Connected"))

    def _handle_disconnected(self):
        """Handles WebSocket disconnected event (called from asyncio thread)."""
        logger.info("OpenAI WebSocket disconnected.")
        # Use QTimer to safely update UI from the main thread
        # Update status only if we are supposed to be in OpenAI mode (determined by transcriber type)
        # and not already processing a result
        # OpenAI check removed from _handle_disconnected as OpenAI is disabled.
        # No status update needed here for ElevenLabs.

    def _initialize_keybind_manager(self):
        """Initializes or re-initializes the PyKeybindManager."""
        # Stop existing listener if running
        if self._py_keybind_manager:
            self._py_keybind_manager.stop_listener()
            self._py_keybind_manager = None

        keybind_key_str = self.config.get(
            constants.CONFIG_KEYBIND, constants.DEFAULT_KEYBIND
        )
        logger.info(
            f"Keybind Debug: Initializing manager for key string from config: '{keybind_key_str}'"
        )

        try:
            self._current_keybind_obj = parse_keybind_string(keybind_key_str)
            logger.info(
                f"Keybind Debug: Parsed key string '{keybind_key_str}' to object: {self._current_keybind_obj}"
            )

            # Determine trigger type based on the key
            trigger_type = (
                "double_press_toggle" if keybind_key_str == "fn" else "toggle"
            )  # Use 'toggle' for non-fn keys
            logger.info(f"Keybind Debug: Determined trigger type: '{trigger_type}'")

            # Create and start the new manager
            self._py_keybind_manager = PyKeybindManager(
                keybind_definition=self._current_keybind_obj,  # Corrected arg name
                on_activated=self._handle_keybind_activation_callback,
                trigger_type=trigger_type,  # Use dynamic trigger type
                on_error=self._handle_keybind_error_callback,
            )
            self._py_keybind_manager.start_listener()
            logger.info(f"PyKeybindManager started with trigger type '{trigger_type}'.")

        except (InvalidKeybindError, PynputImportError) as e:
            logger.error(f"Failed to parse or initialize keybind manager: {e}")
            self._current_keybind_obj = None
            self._py_keybind_manager = None
            if isinstance(e, InvalidKeybindError):
                self.show_error_message(
                    "Keybind Error",
                    f"Invalid keybind '{keybind_key_str}' selected in config.",
                )
        except Exception as e:
            logger.error(f"Unexpected error initializing keybind manager: {e}")
            logger.error(traceback.format_exc())
            self._current_keybind_obj = None
            self._py_keybind_manager = None
            self.show_error_message(
                "Keybind Error", "Failed to start keyboard listener."
            )

    # --- Asyncio Thread Management ---

    def _start_asyncio_thread(self):
        """Starts a separate thread to run the asyncio event loop."""
        if self.asyncio_thread is None:
            self.asyncio_loop = asyncio.new_event_loop()
            self.asyncio_thread = threading.Thread(
                target=self._run_asyncio_loop, daemon=True
            )
            self.asyncio_thread.start()
            logger.info("Asyncio event loop thread started.")

    def _run_asyncio_loop(self):
        """Target function for the asyncio thread."""
        logger.info("Asyncio event loop running.")
        asyncio.set_event_loop(self.asyncio_loop)
        try:
            self.asyncio_loop.run_forever()
        finally:
            logger.info("Asyncio event loop stopping...")
            # Perform cleanup of remaining tasks in the loop before closing
            tasks = asyncio.all_tasks(loop=self.asyncio_loop)
            if tasks:
                logger.info(f"Cancelling {len(tasks)} outstanding asyncio tasks...")
                for task in tasks:
                    task.cancel()
                # Allow tasks to finish cancellation
                self.asyncio_loop.run_until_complete(
                    asyncio.gather(*tasks, return_exceptions=True)
                )
                logger.info("Outstanding asyncio tasks cancelled.")
            self.asyncio_loop.close()
            logger.info("Asyncio event loop closed.")

    def _stop_asyncio_thread(self):
        """Signals the asyncio event loop to stop and joins the thread."""
        if self.asyncio_loop and self.asyncio_loop.is_running():
            logger.info("Requesting asyncio event loop stop...")
            self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)

        if self.asyncio_thread:
            logger.info("Waiting for asyncio thread to join...")
            self.asyncio_thread.join(timeout=5.0)  # Wait for thread to finish
            if self.asyncio_thread.is_alive():
                logger.error("Asyncio thread did not stop cleanly.")
            else:
                logger.info("Asyncio thread joined.")
            self.asyncio_thread = None
        self.asyncio_loop = None  # Clear loop reference

    def submit_async_task(self, coro):
        """Submits a coroutine to the asyncio event loop from any thread."""
        if not self.asyncio_loop or not self.asyncio_loop.is_running():
            logger.error("Asyncio loop is not running. Cannot submit task.")
            return None

        future = asyncio.run_coroutine_threadsafe(coro, self.asyncio_loop)
        # Optional: Add callback to handle result/exception if needed
        # future.add_done_callback(lambda f: logger.debug(f"Async task completed: {f.result()}"))
        return future

    # --- Provider Initialization ---

    def _load_config_and_init_provider(self):
        """Loads config, determines provider from model, gets API key, and initializes the transcriber."""
        logger.info("Initializing transcription provider...")
        self._cleanup_provider()  # Ensure any existing provider is cleaned up

        selected_model_id = self.config.get(
            constants.CONFIG_SELECTED_MODEL_ID, constants.DEFAULT_MODEL_ID
        )
        model_info = self.model_data.get(selected_model_id)

        if not model_info:
            logger.error(
                f"Selected model ID '{selected_model_id}' not found in AVAILABLE_MODELS. Cannot initialize provider."
            )
            self.show_error_message(
                "Config Error", f"Invalid model '{selected_model_id}' selected."
            )
            # Optionally default to first model? For now, fail clearly.
            return

        provider_type = model_info["provider"]
        logger.info(f"Selected Model: {selected_model_id} (Provider: {provider_type})")

        # Get API Keys (Prioritize Environment Variables)
        elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY") or self.config.get(
            constants.CONFIG_ELEVENLABS_API_KEY
        )

        try:
            # OpenAI provider initialization block is disabled.
            # if provider_type == 'openai':
            #     ...

            # Initialize ElevenLabs if selected
            if provider_type == "elevenlabs":
                if not elevenlabs_api_key:
                    logger.error(
                        "ElevenLabs model selected, but API key is missing (check env var "
                        "ELEVENLABS_API_KEY or config)."
                    )
                    self.transcriber = None
                    # Show guidance in settings view
                    self.settings_view.show_configuration_guidance(
                        True, "ElevenLabs API Key is missing. Please add it below."
                    )
                    # Don't return here, let it fall through to the error handling below if needed
                else:
                    logger.info("Initializing ElevenLabsTranscriber")
                    self.transcriber = ElevenLabsTranscriber(api_key=elevenlabs_api_key)
                    # Setup ElevenLabs callbacks directly here
                    self.transcriber.on_transcription_started = (
                        self.on_transcription_started
                    )
                    self.transcriber.on_transcription_complete = (
                        self.on_transcription_complete
                    )
                    self.transcriber.on_transcription_error = (
                        self._handle_transcription_error
                    )  # Use shared error handler

            # Handle cases where provider is not ElevenLabs (e.g., OpenAI was selected but is disabled, or unknown)
            else:
                if provider_type == "openai":
                    logger.error(
                        f"OpenAI provider selected ('{selected_model_id}') but is disabled. Please choose an ElevenLabs model in settings."
                    )
                    self.show_error_message(
                        "Provider Disabled",
                        "OpenAI transcription is currently disabled. Please select an ElevenLabs model.",
                    )
                else:  # Unknown provider
                    logger.error(
                        f"Unknown provider type configured: {provider_type} "
                        f"for model '{selected_model_id}'"
                    )
                    self.show_error_message(
                        "Config Error", f"Unknown provider type: {provider_type}"
                    )
                self.transcriber = None  # Ensure transcriber is None if initialization fails or provider is invalid/disabled

            if self.transcriber:
                logger.info(f"{provider_type} transcriber initialized successfully.")
            else:
                logger.warning(
                    f"Transcriber initialization failed for provider type: {provider_type}"
                )

        except (
            ValueError,
            ElevenLabsTranscriberError,
        ) as e:  # OpenAIRealtimeError remains removed
            logger.error(
                f"Failed to initialize {provider_type} transcriber: {e}", exc_info=True
            )
            self.show_error_message(
                "Transcriber Error", f"Failed to initialize {provider_type}: {e}"
            )
            self.transcriber = None
        except Exception as e:
            logger.error(
                f"Unexpected error initializing transcriber: {e}", exc_info=True
            )
            self.show_error_message("Initialization Error", f"Unexpected error: {e}")
            self.transcriber = None
            # self.provider = None # Provider is not stored directly anymore

    def _cleanup_provider(self):
        """Disconnects and cleans up the current transcriber if it exists."""
        if self.transcriber:
            provider_type = (
                self._get_current_provider_type()
            )  # Determine type before clearing transcriber
            logger.info(f"Cleaning up existing provider type: {provider_type}")
            # Commented out OpenAI cleanup block in _cleanup_provider
            # if provider_type == 'openai' and isinstance(self.transcriber, OpenAIRealtimeTranscriber):
            #     # Ensure disconnect runs in the asyncio loop thread and wait for it
            #     future = self.submit_async_task(self.transcriber.disconnect())
            #     if future:
            #         try:
            #             # Wait for the disconnect task to complete (e.g., 3 seconds timeout)
            #             future.result(timeout=3.0)
            #             logger.info("Async disconnect task completed.")
            #         except TimeoutError:
            #              logger.error("Timeout waiting for WebSocket disconnect task.")
            #         except Exception as e:
            #              logger.error(f"Error waiting for WebSocket disconnect task: {e}")
            # No specific cleanup needed for ElevenLabsTranscriber instance
            self.transcriber = None
            logger.info("Provider resources cleaned up.")

    # --- New Keybind Callbacks ---

    def _handle_keybind_activation_callback(self, press_type):
        """Callback triggered by PyKeybindManager when the keybind is activated."""
        # Removed duplicate log line
        logger.info(
            f"Keybind activation callback triggered. Press type: {press_type}"
        )  # Keybind Debug Log
        # IMPORTANT: This callback runs in the listener thread.
        # UI updates MUST be scheduled on the main Qt thread using QTimer.singleShot
        logger.debug(
            f"Keybind activation callback received (type: {press_type}, from listener thread)."
        )
        display_key_name = (
            self.keybind_data["display"] if self.keybind_data else "Keybind"
        )
        try:
            action_taken = None  # Track if we start or stop
            if self.recorder.recording:
                # Stop recording on *any* press (single or double) while already recording
                logger.info(
                    f"{display_key_name} ({press_type}) activated while recording - stopping"
                )
                # Schedule UI update and stop_recording on the main thread
                QTimer.singleShot(
                    0, lambda: self.update_status("Stopping recording...")
                )
                QTimer.singleShot(0, self.stop_recording)
                action_taken = "stop"
            else:
                # Determine required press type based on the *current* listener config
                keybind_key_str = self.config.get(
                    constants.CONFIG_KEYBIND, constants.DEFAULT_KEYBIND
                )  # Get current keybind
                required_press_type = "double" if keybind_key_str == "fn" else "single"

                # Check if the received press type matches the requirement for the keybind
                # For 'toggle' keys (non-FN), we expect 'press'
                # For 'double_press_toggle' keys (FN), we expect 'double'
                should_start = (
                    required_press_type == "single" and press_type == "press"
                ) or (required_press_type == "double" and press_type == "double")

                if should_start:
                    logger.info(
                        f"{display_key_name} ({press_type} - meets requirement {required_press_type}) activated - starting recording"
                    )
                    # Schedule UI update and start_recording on the main thread
                    QTimer.singleShot(
                        0, lambda: self.update_status("Starting recording...")
                    )
                    QTimer.singleShot(0, self.start_recording)
                    action_taken = "start"
                else:  # Press type didn't match requirement
                    logger.debug(
                        f"{display_key_name} ({press_type}) activated while not "
                        f"recording - ignoring (requires {required_press_type})."
                    )

            # Play sound based on action taken (only if sounds enabled)
            if self.config.get(constants.CONFIG_SOUND_EFFECTS, True):
                if action_taken == "start":
                    QTimer.singleShot(0, lambda: play_keybind_sound("start"))
                elif action_taken == "stop":
                    QTimer.singleShot(0, lambda: play_keybind_sound("stop"))

        except Exception as e:
            logger.error(f"Error in _handle_keybind_activation_callback: {e}")
            logger.error(traceback.format_exc())

    def start_recording(self):
        """Start audio recording, handling provider specifics."""
        # Use the helper method to get the provider type instead of the removed self.provider attribute
        provider_type = self._get_current_provider_type()
        logger.info(
            f"Attempting to start recording with provider type: {provider_type}"
        )
        # Sound playing moved to _handle_keybind_activation_callback

        # Ensure transcriber is ready for the selected provider
        if not self.transcriber:
            logger.error(
                f"Cannot start recording: Transcriber for provider '{self.provider}' not initialized."
            )
            self.update_status("Error: Transcriber not ready")
            # Optionally try re-initializing?
            # self._load_config_and_init_provider()
            # if not self.transcriber: return # Exit if still not ready
            return

        try:
            # OpenAI logic is disabled
            # if provider_type == 'openai_realtime': # Use provider_type instead of self.provider
            #     # Connect WebSocket first
            #     logger.info("Connecting to OpenAI WebSocket...")
            #     self.update_status("Connecting...")
            #     connect_future = self.submit_async_task(self.transcriber.connect())
            #     # We might want to wait for connection briefly or handle connection errors
            #     # For now, proceed to start recorder immediately after submitting connect task
            #     if not connect_future:
            #          raise AudioRecorderError("Failed to submit connect task to asyncio loop.")
            #     # TODO: Add logic to wait for connect_future result or handle errors from it?

            # Start the actual audio recorder (common step)
            # Ensure recorder callbacks (like chunk_callback) are correctly set *before* this call
            self.setup_callbacks()  # Re-run to ensure chunk_callback is set/unset correctly
            if self.recorder.start_recording():
                # UI update is handled by on_recording_started callback now
                pass
            else:
                logger.warning("recorder.start_recording() returned False.")
                self.update_status("Error starting recorder")
                # If OpenAI connection was started, try disconnecting (logic disabled)
                # if provider_type == 'openai_realtime':
                #      self.submit_async_task(self.transcriber.disconnect()) # Also comment out the disconnect call

        # Remove OpenAIRealtimeError from exception handling
        except AudioRecorderError as e:  # OpenAIRealtimeError removed
            logger.error(f"Failed to start recording process: {e}", exc_info=True)

            # Check if on macOS and potentially a permission error
            if sys.platform == "darwin" and isinstance(e, AudioRecorderError):
                # Assume startup errors on macOS might be permissions
                self.show_error_message(
                    "Microphone Access Required?",
                    f"Failed to start recording. This might be due to missing Microphone permissions.\n\n"
                    f"Please check:\nSystem Settings > Privacy & Security > Microphone\n\n"
                    f"Ensure '{constants.APP_NAME}' is listed and enabled.\n\n"
                    f"Original error: {e}",
                )
                self.update_status(
                    "Error: Check Mic Permissions"
                )  # More specific status
            else:
                # Show generic error on other platforms or for other error types
                self.show_error_message(
                    "Recording Error", f"Failed to start recording process: {e}"
                )
                self.update_status(f"Error: {e}")

            # Ensure UI state is correct
            QTimer.singleShot(0, lambda: self.recording_view.set_recording_state(False))
            # Attempt cleanup if OpenAI
            # Check provider type using helper method
            # OpenAI check removed from start_recording
            # if current_provider == 'openai' ...
            #      self.submit_async_task(self.transcriber.disconnect())
        except Exception as e:
            logger.error(f"Unexpected error during start_recording: {e}", exc_info=True)
            self.update_status("Error: Failed to start")
            QTimer.singleShot(0, lambda: self.recording_view.set_recording_state(False))

    def stop_recording(self):
        """Stop audio recording, handling provider specifics."""
        provider_type = self._get_current_provider_type()
        logger.info(f"Attempting to stop recording with provider type: {provider_type}")
        # Sound playing moved to _handle_keybind_activation_callback

        try:
            # Stop the recorder first (stops feeding chunks or allows saving)
            if not self.recorder.stop_recording():
                logger.warning("recorder.stop_recording() returned False.")
                # UI state might be inconsistent, try forcing update
                QTimer.singleShot(
                    0, lambda: self.recording_view.set_recording_state(False)
                )
                self.update_status("Error stopping recorder")
                # Don't proceed if recorder failed to stop cleanly

            # Provider-specific actions after recorder stop signal is processed
            # OpenAI logic disabled
            # if provider_type == 'openai_realtime':
            # Commented out dead code block related to OpenAI disconnect check
            # if isinstance(self.transcriber, OpenAIRealtimeTranscriber):
            #     logger.info("Signaling OpenAI WebSocket to disconnect...")
            #     self.update_status("Finalizing (OpenAI)...")
            #     self.submit_async_task(self.transcriber.disconnect())
            # else:
            #      logger.error("OpenAI provider selected, but transcriber is not the correct type for disconnect.")
            # Changed elif to if since OpenAI is disabled
            if provider_type == "elevenlabs":
                # For ElevenLabs, transcription is triggered by the recorder's
                # on_recording_stopped callback after the file is saved.
                # No immediate action needed here, just wait for callback.
                logger.info(
                    "ElevenLabs: Waiting for recorder thread to save file and trigger transcription."
                )
                # Status is updated in on_recording_stopped
            else:
                # Use provider_type instead of self.provider
                logger.warning(
                    f"Stop recording called with unknown provider: {provider_type}"
                )
                QTimer.singleShot(
                    0, lambda: self.recording_view.set_recording_state(False)
                )  # Ensure UI stops
                self.update_status("Ready")

        # Remove OpenAIRealtimeError from exception handling
        except AudioRecorderError as e:
            logger.error(f"Error stopping recording process: {e}", exc_info=True)
            self.update_status(f"Error: {e}")
            QTimer.singleShot(
                0, lambda: self.recording_view.set_recording_state(False)
            )  # Ensure UI stops
        except Exception as e:
            logger.error(f"Unexpected error during stop_recording: {e}", exc_info=True)
            self.update_status("Error: Failed to stop")
            QTimer.singleShot(0, lambda: self.recording_view.set_recording_state(False))

    @pyqtSlot()
    def show_recording_view(self):
        """Switch to recording view"""
        self.stacked_widget.setCurrentWidget(self.recording_view)

    @pyqtSlot()
    def show_settings_view(self):
        """Switch to settings view"""
        # Update settings view with current config
        self.settings_view.config = self.config.data
        self.settings_view.load_config()

        # Show settings view
        self.stacked_widget.setCurrentWidget(self.settings_view)

    @pyqtSlot(dict)
    def save_settings(self, settings):
        """Save updated settings"""
        logger.info("Saving settings...")
        # Get the *current* keybind before updating the config
        current_keybind = self.config.get(
            constants.CONFIG_KEYBIND, constants.DEFAULT_KEYBIND
        )
        # Update config object
        self.config.update(settings)
        # Save config to file
        if not self.config.save():
            self.show_error_message("Save Error", "Failed to save configuration file.")
            # Continue anyway, but log the error

        # Re-initialize provider based on potentially changed settings
        # This will also handle setting up the correct transcriber callbacks
        self._load_config_and_init_provider()

        # Re-setup recorder callbacks based on the *new* provider settings
        # This connects/disconnects the chunk_callback and sets save_enabled
        self.setup_callbacks()

        # Update keybind display text
        self.update_keybind_display()
        # Re-initialize the keybind manager listener ONLY if the keybind changed
        new_keybind = settings.get(constants.CONFIG_KEYBIND, constants.DEFAULT_KEYBIND)
        # current_keybind = self.config.get(constants.CONFIG_KEYBIND, constants.DEFAULT_KEYBIND) # Now fetched *before* config update
        if new_keybind != current_keybind:
            logger.info(
                f"Keybind changed from '{current_keybind}' to '{new_keybind}'. Re-initializing listener."
            )
            self._initialize_keybind_manager()
        else:
            logger.info("Keybind unchanged. Listener not restarted.")

        # --- Switch back to Recording View if API key is now configured ---
        if self._is_api_key_configured():
            logger.info("Valid API key configured. Switching back to Recording View.")
            # Hide guidance message in settings view (implementation in settings_view.py needed)
            if hasattr(self.settings_view, "show_configuration_guidance"):
                self.settings_view.show_configuration_guidance(False)
            self.stacked_widget.setCurrentWidget(self.recording_view)
            # self.show_recording_view() # Use direct widget setting instead
        else:
            logger.warning(
                "Settings saved, but still no valid API key configured for the selected model."
            )
            # Optionally keep the guidance message visible or update it
            if hasattr(self.settings_view, "show_configuration_guidance"):
                self.settings_view.show_configuration_guidance(
                    True, "Please ensure the API key is correct for the selected model."
                )
            # Stay on settings view if key is still not configured
            self.stacked_widget.setCurrentWidget(self.settings_view)

        logger.info("Settings saved and components re-initialized.")

    def update_status(self, message: str):
        """Update status message in recording view safely from any thread."""
        # Ensure UI updates happen on the main thread
        QTimer.singleShot(0, lambda: self.recording_view.update_status(message))

    # --- Recorder Callbacks ---

    def on_recording_started(self):
        """Callback when recording starts (from AudioRecorder thread)."""
        logger.info("Callback: Recording started.")
        # Use QTimer for thread safety
        QTimer.singleShot(0, lambda: self.recording_view.update_status("Recording..."))
        QTimer.singleShot(0, lambda: self.recording_view.set_recording_state(True))

    def on_recording_stopped(self, file_path: Optional[str]):
        """
        Callback when recording stops and file is saved (or skipped).
        (from AudioRecorder thread).
        """
        logger.info(
            f"Callback: Recording stopped. Provider: {self.provider}, File path: {file_path}"
        )
        # Use QTimer for thread safety
        QTimer.singleShot(0, lambda: self.recording_view.set_recording_state(False))

        if self.provider == "elevenlabs":
            if file_path:  # Only transcribe if a file was actually saved
                QTimer.singleShot(
                    0, lambda: self.update_status("Processing (ElevenLabs)...")
                )
                # Start ElevenLabs transcription in a separate thread
                threading.Thread(
                    target=self.transcribe_recording_elevenlabs,
                    args=(file_path,),
                    daemon=True,
                ).start()
            else:
                logger.warning(
                    "ElevenLabs provider: Recording stopped but no file path provided (saving might be disabled or failed)."
                )
                QTimer.singleShot(
                    0, lambda: self.update_status("Ready")
                )  # Reset status
        elif self.provider == "openai_realtime":
            # For OpenAI, the recording thread stopping doesn't trigger transcription.
            # Transcription happens via WebSocket, triggered by _handle_final_transcript.
            # We just update the status.
            # Disconnect is handled by stop_recording().
            logger.info(
                "OpenAI Realtime: Recording thread stopped. WebSocket should handle final transcript."
            )
            # Status might be "Finalizing..." already set by stop_recording
            # QTimer.singleShot(0, lambda: self.update_status("Processing (OpenAI)...")) # Or keep "Finalizing"
        else:
            logger.warning(
                f"Recording stopped, but provider '{self.provider}' is unknown or not set."
            )
            QTimer.singleShot(0, lambda: self.update_status("Ready"))

    def on_recording_error(self, error_message: str):
        """Callback when recording encounters an error (from AudioRecorder thread)."""
        logger.error(f"Callback: Recording error: {error_message}")
        # Use QTimer for thread safety
        QTimer.singleShot(
            0,
            lambda: self.recording_view.update_status(f"Record Error: {error_message}"),
        )
        QTimer.singleShot(
            0, lambda: self.recording_view.set_recording_state(False)
        )  # Ensure UI reflects stopped state

    # --- Transcription Logic ---

    def transcribe_recording_elevenlabs(self, file_path: str):
        """Transcribe the recorded audio file using ElevenLabs (runs in a separate thread)."""
        logger.info(f"Starting ElevenLabs transcription for: {file_path}")
        if not isinstance(self.transcriber, ElevenLabsTranscriber):
            logger.error(
                "Attempted ElevenLabs transcription, but transcriber is not the correct type."
            )
            self._handle_transcription_error(
                "Internal Error: Invalid transcriber type."
            )
            return

        # API key check happens during initialization, rely on that.

        include_non_speech = self.config.get(constants.CONFIG_INCLUDE_NON_SPEECH, True)
        logger.info(f"ElevenLabs include_non_speech config value: {include_non_speech}")

        try:
            # Call the specific method - callbacks are already set up via setup_elevenlabs_callbacks
            # This will trigger on_transcription_started, on_transcription_complete, or _handle_transcription_error
            self.transcriber.transcribe_file(
                file_path, include_non_speech=include_non_speech
            )
        except FileNotFoundError as e:
            # This specific error is handled here as it occurs before API call
            logger.error(f"ElevenLabs transcription error: {e}")
            self._handle_transcription_error("Error: File not found")
        except Exception as e:
            # Catch unexpected errors during the *call* itself (not API errors handled by callback)
            logger.error(
                f"Unexpected error calling ElevenLabs transcribe_file: {e}",
                exc_info=True,
            )
            self._handle_transcription_error("Error: Transcription failed")

    # --- Transcriber Callbacks (Shared Logic) ---

    def on_transcription_started(self):
        """Callback when ElevenLabs transcription starts (from ElevenLabsTranscriber thread)."""
        # Note: OpenAI real-time doesn't have a distinct "start" event like this.
        logger.info("Callback: Transcription started (ElevenLabs).")
        QTimer.singleShot(0, lambda: self.update_status("Transcribing (ElevenLabs)..."))

    def on_transcription_complete(self, text: str, word_count: int, char_count: int):
        """Callback when transcription completes (called from EL thread or via _handle_final_transcript for OpenAI)"""
        logger.debug(
            f"on_transcription_complete called. is_processing flag: {self.is_processing_transcription}"
        )
        # This flag might still be needed if OpenAI final transcript arrives *very* quickly
        # after another event, though less likely than with the old threaded approach.
        if self.is_processing_transcription:
            logger.warning("Ignoring duplicate transcription completion call.")
            return
        logger.debug("Setting is_processing_transcription = True")
        self.is_processing_transcription = True

        try:
            QTimer.singleShot(
                0, lambda: self.recording_view.update_status("Transcription complete")
            )
            QTimer.singleShot(
                0,
                lambda: self.recording_view.update_transcription_info(
                    word_count, char_count
                ),
            )

            # Save transcription to file
            self.save_transcription_to_file(text)

            # --- Re-implement Copy and Paste ---
            # 1. Copy to clipboard
            try:
                pyperclip.copy(text)
                logger.info("Transcription copied to clipboard.")
            except Exception as clip_e:
                logger.error(f"Failed to copy text to clipboard: {clip_e}")
                # Optionally notify user via status bar?
                # QTimer.singleShot(0, lambda: self.update_status("Error copying text"))

            # 2. Paste if setting is enabled
            if self.config.get(constants.CONFIG_PASTE_AFTER_TRANSCRIPTION, True):
                if sys.platform == "darwin":
                    QTimer.singleShot(0, lambda: self.update_status("Pasting text..."))
                    # Schedule the paste action on the main thread
                    QTimer.singleShot(
                        100, self._do_paste_applescript
                    )  # Added call with 100ms delay
                    threading.Timer(0.8, lambda: self._do_paste_applescript()).start()
                    logger.info("Paste operation scheduled.")
                else:
                    logger.info(
                        "Paste after transcription enabled, but not on macOS. Text copied only."
                    )
                    # Update status to inform user text is copied
                    QTimer.singleShot(0, lambda: self.update_status("Text copied"))
        # Correctly indented finally block
        finally:
            # Reset flag using QTimer to ensure it happens after other UI updates
            logger.debug("Scheduling reset of is_processing_transcription flag.")
            QTimer.singleShot(
                0, lambda: setattr(self, "is_processing_transcription", False)
            )

    def save_transcription_to_file(self, text):
        """Save transcription to a daily text file"""
        try:
            base_folder = self.config.get(
                constants.CONFIG_TRANSCRIPT_FOLDER, os.path.expanduser("~/Documents")
            )
            transcripts_folder = os.path.join(
                base_folder, constants.TRANSCRIPTIONS_SUBFOLDER
            )
            os.makedirs(transcripts_folder, exist_ok=True)
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            filename = os.path.join(transcripts_folder, f"{today}.txt")
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            entry = f"\n\n[{timestamp}]\n{text}"
            with open(filename, "a", encoding="utf-8") as file:
                file.write(entry)
            logger.info(f"Transcription saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving transcription to file: {e}")
            self.show_error_message("Save Error", f"Could not save transcription: {e}")

    # def on_transcription_error(self, error_message): # Combined into _handle_transcription_error
    #     """Callback when transcription encounters an error"""
    #     # This method is now primarily for ElevenLabs, OpenAI uses _handle_transcription_error
    def _simulate_keystrokes(self, text_to_type: str):
        """Uses AppleScript to simulate typing text at the current cursor position."""
        if sys.platform != "darwin":
            logger.warning(
                "Keystroke simulation via AppleScript is only supported on macOS."
            )
            return

        # Escape backslashes and double quotes for AppleScript string
        escaped_text = text_to_type.replace("\\", "\\\\").replace('"', '\\"')

        applescript = f"""
            tell application "System Events"
                keystroke "{escaped_text}"
            end tell
        """
        try:
            logger.debug(
                f"Attempting to execute AppleScript for keystrokes: '{text_to_type}'"
            )  # Added log
            process = subprocess.Popen(
                ["osascript", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate(applescript)
            if process.returncode != 0:
                logger.error(
                    f"AppleScript keystroke error (Code {process.returncode}): {stderr}"
                )
            # else:
            #     logger.debug("AppleScript keystroke executed successfully.")
        except FileNotFoundError:
            logger.error("osascript command not found. Cannot simulate keystrokes.")
        except Exception as e:
            logger.error(
                f"Error executing AppleScript for keystrokes: {e}", exc_info=True
            )

        # logger.error(f"Callback: Transcription error (ElevenLabs?): {error_message}")
        # QTimer.singleShot(0, lambda: self.recording_view.update_status(f"Error: {error_message}"))
        # Note: No finally block needed here as the flag is handled in on_transcription_complete

    # --- Paste Helper ---
    def _do_paste_applescript(self):
        """Executes AppleScript to perform a paste operation."""
        # This runs in a separate thread via threading.Timer
        try:
            logger.debug(
                "Attempting to execute AppleScript paste"
            )  # Changed log level and message
            script = (
                'tell application "System Events" to keystroke "v" using {command down}'
            )
            # Use check=True and capture output for better error handling
            result = subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                text=True,
                timeout=3,
            )
            logger.info(
                f"AppleScript paste executed successfully. Output: {result.stdout}"
            )
            # Update status on main thread
            QTimer.singleShot(0, lambda: self.update_status("Text pasted"))
        except subprocess.CalledProcessError as e:
            logger.error(f"AppleScript paste error (CalledProcessError): {e}")
            logger.error(f"Stderr: {e.stderr}")
            QTimer.singleShot(0, lambda: self.update_status("Paste error"))
        except subprocess.TimeoutExpired:
            logger.error("AppleScript paste timed out.")
            QTimer.singleShot(0, lambda: self.update_status("Paste timeout"))
        except Exception as e:
            logger.error(f"Unexpected error during AppleScript paste: {e}")
            logger.error(traceback.format_exc())
            QTimer.singleShot(0, lambda: self.update_status("Paste failed"))

    @pyqtSlot()
    def _handle_show_app_signal(self):
        """Handle show app signal from TrayManager"""
        # Corrected logic: Always show and raise the window
        logger.debug("Show app signal received from tray.")
        if self.isMinimized():
            self.showNormal()  # Restore from minimized state
        elif not self.isVisible():
            self.show()  # Show if hidden
        # If already visible, activateWindow and raise_ will bring it forward

        self.activateWindow()  # Bring window to foreground
        self.raise_()  # Raise window above others (especially on macOS)
        logger.debug("Window shown and raised.")

    @pyqtSlot()  # Keep quit_app as it's connected directly
    def quit_app(self):  # Slot connected to tray manager
        """Cleans up resources and quits the application."""
        logger.info("Quit requested.")
        # Stop keybind listener first
        if self._py_keybind_manager:
            logger.info("Stopping keybind manager...")
            try:
                self._py_keybind_manager.stop_listener()
            except Exception as e:
                logger.error(f"Error stopping keybind manager: {e}", exc_info=True)
            self._py_keybind_manager = None
            logger.info("Keybind manager stopped.")

        # Ensure any active recording is stopped (important for cleanup)
        if self.recorder and self.recorder.recording:
            logger.warning(
                "Quit requested while recording - attempting to stop recording first."
            )
            # Directly signal recorder thread to stop, don't rely on full stop_recording logic here
            self.recorder.recording = False
            # Give recorder thread a moment to potentially finish IO
            time.sleep(0.1)

        # Cleanup provider (disconnect WebSocket if needed)
        # Use a blocking call here as we are quitting anyway
        provider_type = self._get_current_provider_type()
        if provider_type == "openai" and isinstance(
            self.transcriber, OpenAIRealtimeTranscriber
        ):
            if self.asyncio_loop and self.asyncio_loop.is_running():
                logger.info("Submitting final disconnect task to asyncio loop...")
                future = self.submit_async_task(self.transcriber.disconnect())
                if future:
                    try:
                        # Wait briefly for disconnect task to complete
                        future.result(timeout=2.0)
                        logger.info("OpenAI disconnect task completed.")
                    except TimeoutError:
                        logger.warning("Timeout waiting for OpenAI disconnect task.")
                    except Exception as e:
                        logger.error(
                            f"Error waiting for OpenAI disconnect task: {e}",
                            exc_info=True,
                        )
            else:
                logger.warning("Cannot disconnect OpenAI: Asyncio loop not running.")
        self.transcriber = None  # Clear reference after attempting disconnect

        # Stop the asyncio loop thread
        self._stop_asyncio_thread()

        logger.info("Exiting application.")
        QApplication.instance().quit()

    def closeEvent(self, event):
        """Handle window close event (minimize to tray)."""
        # Always hide to tray, quit is handled by tray menu's quit_app slot
        self.hide()
        event.ignore()
        logger.info("Window hidden to tray.")

    # Renamed show_permission_error to _handle_keybind_error_callback
    # and adapted it to receive the exception object
    def _handle_keybind_error_callback(self, error):
        logger.error(f"Keybind Debug: Error callback triggered: {error}")
        logger.error(f"Keybind Debug: Error callback triggered: {error}")
        logger.error(f"Keybind Debug: Error callback triggered: {error}")
        logger.error(f"Keybind Debug: Error callback triggered: {error}")
        """Callback triggered by PyKeybindManager when an error occurs."""
        # IMPORTANT: This callback likely runs in the listener thread.
        # Use QTimer.singleShot for UI interactions (like QMessageBox).
        logger.error(
            f"Keybind error callback received: {type(error).__name__} - {error}"
        )

        # Specifically handle permission errors to show the detailed message
        if isinstance(error, KeybindPermissionError):
            # Schedule the dialog display on the main thread
            QTimer.singleShot(0, self._show_permission_error_dialog)
        elif isinstance(error, PynputImportError):
            # Schedule a generic error message on the main thread
            QTimer.singleShot(
                0,
                lambda: self.show_error_message(
                    "Keybind Error",
                    "Failed to import necessary keyboard/mouse library (pynput).\n"
                    "Please ensure it's installed correctly.",
                ),
            )
        else:
            # Schedule a generic error message for other keybind errors
            QTimer.singleShot(
                0,
                lambda: self.show_error_message(
                    "Keybind Error",
                    f"An error occurred in the keyboard listener:\n{error}",
                ),
            )

    def _show_permission_error_dialog(self):
        """Shows a detailed permission error dialog (runs on main thread)."""
        logger.warning("Showing keybind permission error dialog.")
        msg = QMessageBox(self)  # Parent to main window
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Input Monitoring Permission Required")
        msg.setText(
            f"{constants.APP_NAME} needs 'Input Monitoring' permission to detect keyboard shortcuts globally.\n\n"
            "Please grant permission in:\n"
            "System Settings > Privacy & Security > Input Monitoring"
        )
        msg.setDetailedText(
            "Why is this needed?\n"
            "To detect when you press the recording shortcut key (e.g., FN) even when RivaVoice is not the active application.\n\n"
            "How to grant permission:\n"
            "1. Click 'Open Privacy Settings' below.\n"
            "2. Find 'Input Monitoring' in the list.\n"
            f"3. Unlock the settings (padlock icon).\n"
            f"4. Drag '{constants.APP_NAME}.app' into the list, or use the '+' button to add it.\n"
            f"5. If prompted, choose to 'Quit & Reopen' {constants.APP_NAME}.\n\n"
            "The application will continue to run, but the keyboard shortcut will not work until permission is granted."
        )
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
                    # Use the specific URL for Input Monitoring if possible
                    subprocess.Popen(
                        ["open", constants.MACOS_PRIVACY_URL_INPUT_MONITORING]
                    )
                # Add handlers for other platforms if needed
            except Exception as e:
                logger.error(f"Failed to open system settings: {e}")
                # Fallback to general privacy settings if specific URL fails
                try:
                    subprocess.Popen(["open", constants.MACOS_PRIVACY_URL_GENERAL])
                except Exception as e2:
                    logger.error(f"Failed to open general system settings: {e2}")

    def show_error_message(self, title, message):
        """Displays an error message box (safe to call from any thread)."""
        # Ensure this runs on the main thread if called from background thread
        if threading.current_thread() is not threading.main_thread():
            QTimer.singleShot(0, lambda: self.show_error_message(title, message))
            return
        QMessageBox.critical(self, title, message)

    def _is_api_key_configured(self) -> bool:
        """Checks if a valid API key is configured for the currently selected model."""
        try:
            selected_model_id = self.config.get(
                constants.CONFIG_SELECTED_MODEL_ID, constants.DEFAULT_MODEL_ID
            )
            model_info = self.model_data.get(selected_model_id)

            if not model_info:
                logger.error(
                    f"Cannot check API key: Model info not found for ID '{selected_model_id}'."
                )
                return False  # Cannot determine provider

            provider_type = model_info["provider"]
            api_key = None

            if provider_type == "openai":
                key_constant = constants.CONFIG_OPENAI_API_KEY
                env_var = "OPENAI_API_KEY"
            elif provider_type == "elevenlabs":
                key_constant = constants.CONFIG_ELEVENLABS_API_KEY
                env_var = "ELEVENLABS_API_KEY"
            else:
                logger.error(
                    f"Cannot check API key: Unknown provider type '{provider_type}' for model '{selected_model_id}'."
                )
                return False  # Unknown provider

            # Check environment variable first, then config file
            api_key = os.environ.get(env_var) or self.config.get(key_constant)

            if api_key:
                logger.debug(f"API key found for provider '{provider_type}'.")
                return True
            else:
                logger.warning(
                    f"API key NOT found for provider '{provider_type}' (Model: {selected_model_id}). Checked env '{env_var}' and config '{key_constant}'."
                )
                return False
        except Exception as e:
            logger.error(f"Error checking API key configuration: {e}", exc_info=True)
            return False  # Assume not configured on error
