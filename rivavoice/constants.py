import os
import pyaudio
import tempfile

# --- Application Info ---
APP_NAME = "RivaVoice"
APP_VERSION = "1.0.0" # Consider reading from setup.py or __version__
ORG_NAME = "RivaVoice" # Used for Qt settings, etc.
BUNDLE_ID = "com.rivavoice.app"

# --- File Paths ---
# Config file (Consider using platformdirs later)
DEFAULT_CONFIG_FILE = os.path.expanduser("~/.rivavoiceconfig.json")
# Temporary recording file
DEFAULT_RECORDING_FILE = os.path.join(tempfile.gettempdir(), "recording.wav")
# Icon files (relative to package root)
ICON_APP_SVG = "rivavoice.svg"
ICON_APP_ICNS = "RivaVoice.icns" # For py2app
ICON_TRAY_SVG = "r.svg"
ICON_SETTINGS_SVG = "settings.svg"
ICON_CLOSE_SVG = "close.svg"
# Sound files moved to pykeybindmanager
# Transcription save subfolder
TRANSCRIPTIONS_SUBFOLDER = "transcriptions"

# --- Audio Recording ---
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_RATE = 44100
AUDIO_CHUNK = 1024

# --- Transcription API ---
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/speech-to-text"
ELEVENLABS_MODEL_ID = "scribe_v1"

# --- Configuration Keys ---
# CONFIG_TRANSCRIPTION_PROVIDER = 'transcription_provider' # Removed - Determined by model
CONFIG_SELECTED_MODEL_ID = 'selected_model_id' # Added
CONFIG_ELEVENLABS_API_KEY = 'elevenlabs_api_key'
CONFIG_OPENAI_API_KEY = 'openai_api_key'
# CONFIG_OPENAI_MODEL = 'openai_model' # Removed - Use selected_model_id
CONFIG_TRANSCRIPT_FOLDER = 'transcript_folder'
CONFIG_KEYBIND = 'keybind'
CONFIG_SOUND_EFFECTS = 'sound_effects'
CONFIG_INCLUDE_NON_SPEECH = 'include_non_speech' # Note: Only relevant for ElevenLabs currently
CONFIG_PASTE_AFTER_TRANSCRIPTION = 'paste_after_transcription'
# --- Model Definitions (Moved Before Default Config) ---
# Structure: {'display': 'User-facing Name', 'id': 'internal_id', 'provider': 'elevenlabs' | 'openai'}
AVAILABLE_MODELS = [
    {'display': 'ElevenLabs Scribe', 'id': 'elevenlabs_scribe', 'provider': 'elevenlabs'},
    # {'display': 'GPT-4o Mini Transcribe', 'id': 'gpt-4o-mini-transcribe', 'provider': 'openai'}, # Disabled
    # {'display': 'GPT-4o Transcribe', 'id': 'gpt-4o-transcribe', 'provider': 'openai'}, # Disabled
    # Add other models here if needed
]
DEFAULT_MODEL_ID = AVAILABLE_MODELS[0]['id'] # Default to the first model in the list

# --- Default Values (Define before use in DEFAULT_CONFIG) ---
DEFAULT_TRANSCRIPT_FOLDER = os.path.expanduser('~/Documents')
DEFAULT_PASTE_AFTER_TRANSCRIPTION = True
DEFAULT_SOUND_EFFECTS = True
DEFAULT_KEYBIND = 'fn' # Keep separate for clarity, though also used in DEFAULT_CONFIG

# --- Default Configuration Dictionary ---
DEFAULT_CONFIG = {
    CONFIG_SELECTED_MODEL_ID: DEFAULT_MODEL_ID,
    CONFIG_ELEVENLABS_API_KEY: '',
    CONFIG_OPENAI_API_KEY: '',
    CONFIG_TRANSCRIPT_FOLDER: DEFAULT_TRANSCRIPT_FOLDER, # Use constant
    CONFIG_KEYBIND: DEFAULT_KEYBIND, # Use constant
    CONFIG_SOUND_EFFECTS: DEFAULT_SOUND_EFFECTS, # Use constant
    CONFIG_PASTE_AFTER_TRANSCRIPTION: DEFAULT_PASTE_AFTER_TRANSCRIPTION # Use constant
}

# --- UI ---
# DEFAULT_KEYBIND = 'fn' # Defined above now

# Removed duplicate/old model definitions section
DOUBLE_PRESS_TIME_S = 0.5 # Time window for double press detection

# --- macOS Specific ---
MACOS_PRIVACY_URL_INPUT_MONITORING = 'x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent'
MACOS_PRIVACY_URL_MICROPHONE = 'x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone'
MACOS_PRIVACY_URL_GENERAL = 'x-apple.systempreferences:com.apple.preference.security?Privacy'
