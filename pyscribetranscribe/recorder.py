"""
Provides the AudioRecorder class for capturing microphone input using PyAudio.

Supports saving recordings to WAV files and providing real-time audio chunks
via a callback mechanism.
"""
import os
import pyaudio
import wave
import threading
import logging
import tempfile
import time  # Keep time for testing block if added later

# Define default audio parameters here or pass them all in __init__
DEFAULT_AUDIO_FORMAT = pyaudio.paInt16
DEFAULT_AUDIO_CHANNELS = 1
DEFAULT_AUDIO_RATE = 44100
DEFAULT_AUDIO_CHUNK = 1024
DEFAULT_TEMP_DIR = tempfile.gettempdir()
DEFAULT_RECORDING_FILENAME = "recording.wav"

# Setup a logger for the module
logger = logging.getLogger(__name__)
# Configure basic logging if no handler is set by the calling application
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


class AudioRecorderError(Exception):
    """Custom exception for AudioRecorder errors."""

    pass


class AudioRecorder:
    """
    Records audio using PyAudio. Can optionally save to a WAV file
    and/or provide audio chunks via a callback for real-time processing.
    """

    def __init__(
        self,
        recording_file=None,
        audio_format=DEFAULT_AUDIO_FORMAT,
        channels=DEFAULT_AUDIO_CHANNELS,
        rate=DEFAULT_AUDIO_RATE,
        chunk=DEFAULT_AUDIO_CHUNK,
        chunk_callback=None,
    ):
        """
        Initializes the AudioRecorder.

        Args:
            recording_file (str | None, optional): Full path to save the recording.
                                                   If an empty string "", defaults to 'recording.wav'
                                                   in the system's temp directory.
                                                   If None, saving is disabled.
            audio_format (int, optional): PyAudio format constant. Defaults to paInt16.
            channels (int, optional): Number of audio channels. Defaults to 1.
            rate (int, optional): Sample rate in Hz. Defaults to 44100.
            chunk (int, optional): Buffer size. Defaults to 1024.
            chunk_callback (callable, optional): A function to call with each raw audio data chunk
                                                 as it's recorded. `callback(data: bytes)`. Defaults to None.
        """
        # Determine recording file path and whether saving is enabled
        if recording_file is None:
            self.recording_file = None  # Indicate saving is disabled
            self.save_enabled = False
            logger.info("Recording file path is None, saving will be skipped.")
        elif recording_file == "":  # Treat empty string as default path
            self.recording_file = os.path.join(
                DEFAULT_TEMP_DIR, DEFAULT_RECORDING_FILENAME
            )
            self.save_enabled = True
            logger.info(f"Recording file path set to default: {self.recording_file}")
        else:
            self.recording_file = recording_file
            self.save_enabled = True
            logger.info(f"Recording file path: {self.recording_file}")

        self.format = audio_format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk

        self.recording = False
        self.audio = None
        self.stream = None
        # Initialize frames only if saving is enabled
        self.frames = [] if self.save_enabled else None
        self.audio_thread = None

        # Callbacks
        self.on_recording_started = None
        self.on_recording_stopped = None  # Passes file_path (str or None)
        self.on_recording_error = None  # Passes error_message (str)
        self.chunk_callback = chunk_callback  # Store the chunk callback

        logger.info(
            f"AudioRecorder initialized. Format={self.format}, Channels={self.channels}, Rate={self.rate}, Chunk={self.chunk}"
        )

    def start_recording(self):
        """Start audio recording in a separate thread."""
        if self.recording:
            logger.warning("Attempted to start recording when already recording.")
            return False

        try:
            if self.save_enabled:
                self.frames = []  # Reset frames only if saving
            self.recording = True
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            logger.info("Recording thread started.")

            if self.on_recording_started:
                self.on_recording_started()
            return True
        except Exception as e:
            error_msg = f"Error starting recording: {e}"
            logger.error(error_msg, exc_info=True)
            self.recording = False
            if self.on_recording_error:
                self.on_recording_error(error_msg)
            raise AudioRecorderError(error_msg) from e  # Raise custom exception

    def stop_recording(self):
        """Stop the current recording and potentially save the file."""
        if not self.recording:
            logger.warning("Attempted to stop recording when not recording.")
            return False

        try:
            logger.info("Stopping recording...")
            self.recording = False  # Signal the recording thread to stop

            if self.audio_thread and self.audio_thread.is_alive():
                logger.info("Waiting for recording thread to complete...")
                self.audio_thread.join(
                    timeout=5.0
                )  # Wait for thread to finish cleanup/saving
                if self.audio_thread.is_alive():
                    # This case is problematic, thread didn't exit cleanly
                    error_msg = "Recording thread did not complete in time."
                    logger.error(error_msg)
                    if self.on_recording_error:
                        self.on_recording_error(error_msg)
                    # Don't raise here, but indicate failure
                    return False  # Indicate failure

            logger.info("Recording stopped signal processed.")
            # Note: The actual 'stopped' callback is triggered from within the thread
            # after saving (or deciding not to save). This ensures saving is complete.
            return True  # Indicate success in signaling stop

        except Exception as e:
            error_msg = f"Error signaling stop recording: {e}"
            logger.error(error_msg, exc_info=True)
            if self.on_recording_error:
                self.on_recording_error(error_msg)
            # Don't raise here, allow potential cleanup
            return False  # Indicate failure

    def _record_audio(self):
        """Internal method to record audio in a thread."""
        self.audio = None
        self.stream = None
        try:
            logger.debug("Audio recording thread running.")
            self.audio = pyaudio.PyAudio()
            logger.debug("Opening audio stream...")
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )
            logger.info("Audio stream opened. Recording...")

            while self.recording:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    # Call the chunk callback if provided
                    if self.chunk_callback:
                        try:
                            # Consider running callback in executor if it's blocking
                            self.chunk_callback(data)
                        except Exception as cb_e:
                            logger.error(
                                f"Error in chunk_callback: {cb_e}", exc_info=True
                            )
                            # Decide if this should stop recording? For now, just log.
                    # Still append frames if saving is enabled
                    if self.save_enabled:
                        self.frames.append(data)
                except IOError as e:
                    # This can happen if the stream is closed prematurely or device issues
                    if (
                        self.recording
                    ):  # Only log warning if we expected to still be recording
                        logger.warning(
                            f"IOError during recording stream read: {e}. Continuing..."
                        )
                    else:
                        logger.debug(f"IOError after stop signal: {e}. Expected.")
                        break  # Exit loop if stop was signaled

            logger.info("Recording loop finished.")

        except Exception as e:
            error_msg = f"Error during audio stream handling: {e}"
            logger.error(error_msg, exc_info=True)
            if self.on_recording_error:
                self.on_recording_error(error_msg)
            # Don't raise from thread, use callback

        finally:
            # Ensure resources are cleaned up
            logger.debug("Cleaning up audio resources...")
            if self.stream:
                try:
                    if self.stream.is_active():
                        self.stream.stop_stream()
                    self.stream.close()
                    logger.debug("Audio stream closed.")
                except Exception as e_close:
                    logger.error(f"Error closing stream: {e_close}", exc_info=True)
            if self.audio:
                try:
                    self.audio.terminate()
                    logger.debug("PyAudio terminated.")
                except Exception as e_term:
                    logger.error(f"Error terminating PyAudio: {e_term}", exc_info=True)

            # Save the recording after cleanup if enabled
            saved_file_path = None
            if self.save_enabled:
                saved_file_path = self._save_recording()  # Returns path or None

            # Trigger the final stopped callback *after* all cleanup and saving attempt
            if self.on_recording_stopped:
                try:
                    self.on_recording_stopped(saved_file_path)
                except Exception as cb_e:
                    logger.error(
                        f"Error in on_recording_stopped callback: {cb_e}", exc_info=True
                    )

    def _save_recording(self):
        """
        Save recorded audio frames to a WAV file. Assumes self.save_enabled is True.
        Returns the file path if successful, None otherwise.
        """
        if not self.frames:
            logger.warning("No frames recorded, skipping save.")
            if self.on_recording_error:
                self.on_recording_error("No audio data was recorded to save.")
            return None  # Indicate failure/no file

        # Should always have a path if save_enabled is True, but double-check
        if not self.recording_file:
            logger.error(
                "Attempted to save recording but recording_file path is missing."
            )
            if self.on_recording_error:
                self.on_recording_error(
                    "Internal error: Recording file path missing during save."
                )
            return None

        try:
            # Ensure the directory exists
            recording_dir = os.path.dirname(self.recording_file)
            if recording_dir:  # Only create if path includes a directory
                os.makedirs(recording_dir, exist_ok=True)

            logger.info(f"Saving recording to {self.recording_file}")
            with wave.open(self.recording_file, "wb") as wf:
                wf.setnchannels(self.channels)
                # Need PyAudio instance to get sample size if not already terminated
                # This is slightly inefficient but ensures correctness if PyAudio was terminated early
                temp_audio = pyaudio.PyAudio()
                try:
                    sample_width = temp_audio.get_sample_size(self.format)
                finally:
                    temp_audio.terminate()  # Clean up temporary instance

                wf.setsampwidth(sample_width)
                wf.setframerate(self.rate)
                wf.writeframes(b"".join(self.frames))

            logger.info("Recording saved successfully.")
            return self.recording_file  # Return path on success
        except Exception as e:
            error_msg = f"Error saving WAV file '{self.recording_file}': {e}"
            logger.error(error_msg, exc_info=True)
            if self.on_recording_error:
                self.on_recording_error(error_msg)
            return None  # Return None on failure


# Example usage block (optional, can be removed or kept for testing)
if __name__ == "__main__":
    print("--- Testing AudioRecorder Module ---")
    # Setup console logging for test
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Starting test...")

    # --- Test Case 1: Saving Enabled (Default Path) ---
    print("\n--- Test Case 1: Saving Enabled (Default Path) ---")
    recorder1 = AudioRecorder(recording_file="")  # Use default path

    recorder1.on_recording_started = lambda: print("Callback 1: Recording started!")
    recorder1.on_recording_stopped = lambda file: print(
        f"Callback 1: Recording stopped! File saved: {file}"
    )
    recorder1.on_recording_error = lambda msg: print(f"Callback 1: ERROR: {msg}")

    try:
        print("Starting recording for 2 seconds...")
        if recorder1.start_recording():
            time.sleep(2)
            print("Stopping recording...")
            if recorder1.stop_recording():
                print(
                    f"Test 1 recording should be saved to: {recorder1.recording_file}"
                )
                # Optional: Clean up
                # try: os.remove(recorder1.recording_file) except OSError: pass
            else:
                print("Test 1: Failed to stop recording cleanly.")
        else:
            print("Test 1: Failed to start recording.")
    except AudioRecorderError as e:
        print(f"Test 1: Caught AudioRecorderError: {e}")
    except Exception as e:
        print(f"Test 1: Caught unexpected error: {e}", exc_info=True)

    # --- Test Case 2: Saving Disabled + Chunk Callback ---
    print("\n--- Test Case 2: Saving Disabled + Chunk Callback ---")
    chunk_count = 0

    def my_chunk_callback(data):
        global chunk_count
        chunk_count += 1
        # print(f"Callback 2: Got chunk {chunk_count}: {len(data)} bytes") # Too verbose

    recorder2 = AudioRecorder(recording_file=None, chunk_callback=my_chunk_callback)

    recorder2.on_recording_started = lambda: print("Callback 2: Recording started!")
    recorder2.on_recording_stopped = lambda file: print(
        f"Callback 2: Recording stopped! File saved: {file} (should be None)"
    )
    recorder2.on_recording_error = lambda msg: print(f"Callback 2: ERROR: {msg}")

    try:
        print("Starting recording for 2 seconds (no saving)...")
        if recorder2.start_recording():
            time.sleep(2)
            print("Stopping recording...")
            if recorder2.stop_recording():
                print(
                    f"Test 2: Recording stopped. Total chunks received: {chunk_count}"
                )
            else:
                print("Test 2: Failed to stop recording cleanly.")
        else:
            print("Test 2: Failed to start recording.")
    except AudioRecorderError as e:
        print(f"Test 2: Caught AudioRecorderError: {e}")
    except Exception as e:
        print(f"Test 2: Caught unexpected error: {e}", exc_info=True)

    print("\n--- AudioRecorder Test End ---")
