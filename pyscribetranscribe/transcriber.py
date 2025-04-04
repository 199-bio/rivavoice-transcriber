import os
import logging
import requests
import traceback

# Define default API parameters (can be overridden in __init__ or methods)
DEFAULT_ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/speech-to-text"
# Update model ID based on API error message
DEFAULT_ELEVENLABS_MODEL_ID = "scribe_v1"

# Setup a logger for the module
logger = logging.getLogger(__name__)
# Configure basic logging if no handler is set by the calling application
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class ElevenLabsTranscriberError(Exception):
    """Custom exception for ElevenLabs Transcriber errors."""
    pass

class ElevenLabsTranscriber:
    """Transcribes audio files using the ElevenLabs speech-to-text API."""

    def __init__(self,
                 api_key,
                 api_url=DEFAULT_ELEVENLABS_API_URL,
                 model_id=DEFAULT_ELEVENLABS_MODEL_ID):
        """
        Initializes the ElevenLabsTranscriber.

        Args:
            api_key (str): The API key for the transcription service.
            api_url (str, optional): The endpoint URL for the transcription API.
                                     Defaults to ElevenLabs v1 URL.
            model_id (str, optional): The model ID to use for transcription.
                                      Defaults to 'eleven_multilingual_v2'.
        """
        if not api_key:
            raise ValueError("API key is required for ElevenLabsTranscriber.")

        self.api_key = api_key
        self.api_url = api_url
        self.model_id = model_id

        # Callbacks
        self.on_transcription_started = None
        self.on_transcription_complete = None # Passes (text, word_count, char_count)
        self.on_transcription_error = None   # Passes (error_message)

        logger.info(f"ElevenLabsTranscriber initialized. API URL: {self.api_url}, Model ID: {self.model_id}")

    def transcribe_file(self, file_path, include_non_speech=True):
        """
        Transcribes the audio file at the given path.

        Args:
            file_path (str): The path to the audio file (e.g., WAV).
            include_non_speech (bool, optional): Whether to include non-speech event
                                                 tags in the transcription (if supported by API).
                                                 Defaults to True.

        Returns:
            str: The transcribed text, or None if an error occurred.

        Raises:
            FileNotFoundError: If the input file_path does not exist.
            ElevenLabsTranscriberError: For API errors or other transcription issues.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        logger.info(f"Attempting to transcribe file: {file_path}")
        if self.on_transcription_started:
            self.on_transcription_started()

        try:
            headers = {
                "xi-api-key": self.api_key
            }
            file_name = os.path.basename(file_path)

            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, 'audio/wav'), # Assuming WAV, adjust if needed
                    'model_id': (None, self.model_id),
                    # Parameter name might vary between APIs
                    'tag_audio_events': (None, str(include_non_speech).lower())
                }

                logger.debug(f"Sending transcription request to {self.api_url} with model {self.model_id}")
                response = requests.post(self.api_url, headers=headers, files=files)

                if response.status_code == 200:
                    logger.info("Transcription received successfully.")
                    result = response.json()
                    transcribed_text = result.get('text', '') # Safely get text

                    # Calculate stats
                    char_count = len(transcribed_text)
                    word_count = len(transcribed_text.split())

                    if self.on_transcription_complete:
                        self.on_transcription_complete(transcribed_text, word_count, char_count)

                    return transcribed_text
                else:
                    error_msg = f"API error {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    if self.on_transcription_error:
                        self.on_transcription_error(f"API error: {response.status_code}")
                    raise ElevenLabsTranscriberError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during transcription request: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            if self.on_transcription_error:
                self.on_transcription_error("Network error during transcription.")
            raise ElevenLabsTranscriberError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during transcription: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            if self.on_transcription_error:
                self.on_transcription_error("Unexpected error during transcription.")
            raise ElevenLabsTranscriberError(error_msg) from e

# Example usage block (optional)
if __name__ == "__main__":
    print("--- Testing ElevenLabsTranscriber Module ---")
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Starting test...")

    # --- IMPORTANT ---
    # For this test to work, you MUST:
    # 1. Set the ELEVENLABS_API_KEY environment variable.
    # 2. Have a sample audio file named 'test_audio.wav' in the same directory.
    #    (Create one using the recorder.py test or provide your own)
    # --- IMPORTANT ---

    api_key_from_env = os.environ.get("ELEVENLABS_API_KEY")
    test_file = "test_audio.wav" # Needs to exist

    if not api_key_from_env:
        print("ERROR: ELEVENLABS_API_KEY environment variable not set. Skipping test.")
    elif not os.path.exists(test_file):
         print(f"ERROR: Test audio file '{test_file}' not found. Skipping test.")
    else:
        try:
            transcriber = ElevenLabsTranscriber(api_key=api_key_from_env)

            # Simple callbacks
            transcriber.on_transcription_started = lambda: print("Callback: Transcription started!")
            transcriber.on_transcription_complete = lambda text, words, chars: print(f"Callback: Transcription complete! Words: {words}, Chars: {chars}\nText: '{text}'")
            transcriber.on_transcription_error = lambda msg: print(f"Callback: ERROR: {msg}")

            print(f"Transcribing file: {test_file}...")
            transcribed_text = transcriber.transcribe_file(test_file)

            if transcribed_text is not None:
                print("Transcription successful (see callback output).")
            else:
                # Error handled by callback and exception
                print("Transcription failed (see callback/error output).")

        except (FileNotFoundError, ElevenLabsTranscriberError, ValueError) as e:
             print(f"Caught expected error: {e}")
        except Exception as e:
            print(f"Caught unexpected error: {e}")
            print(traceback.format_exc())

    print("--- ElevenLabsTranscriber Test End ---")
