"""
Audio Module for Recording and Transcription
"""

import logging

# Configure logging for the module package
# This prevents logs from propagating to the root logger unless the
# calling application configures logging.
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Import main classes and exceptions for easier access
from .recorder import AudioRecorder, AudioRecorderError  # noqa: E402

# Import renamed ElevenLabs classes
from .transcriber import ElevenLabsTranscriber, ElevenLabsTranscriberError  # noqa: E402

# Import new OpenAI classes
from .openai_realtime_transcriber import OpenAIRealtimeTranscriber, OpenAIRealtimeError  # noqa: E402

# Define what gets imported with 'from pyscribetranscribe import *'
# (Generally discouraged, but good practice to define)
__all__ = [
    "AudioRecorder",
    "AudioRecorderError",
    "ElevenLabsTranscriber",
    "ElevenLabsTranscriberError",
    "OpenAIRealtimeTranscriber",
    "OpenAIRealtimeError",
]

# Optional: Define a version for the module
__version__ = "0.1.0"
