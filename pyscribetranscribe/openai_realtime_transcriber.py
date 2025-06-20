import asyncio
import websockets
import json
import base64
import logging
import traceback
import aiohttp  # Added
from typing import Callable, Optional, List

# Setup logger
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

# Constants (Consider moving to a config or constants file later)
# Constants
OPENAI_REST_SESSION_URL = "https://api.openai.com/v1/realtime/transcription_sessions"
OPENAI_WEBSOCKET_URL = "wss://api.openai.com/v1/realtime"  # Base URL
EXPECTED_AUDIO_FORMAT_TYPE = "pcm16"  # Corresponds to pyaudio.paInt16


class OpenAIRealtimeError(Exception):
    """Custom exception for OpenAIRealtimeTranscriber errors."""

    pass


class OpenAIRealtimeTranscriber:
    """
    Handles real-time audio transcription using OpenAI's WebSocket API.
    """

    def __init__(
        self,
        api_key: str,
        sample_rate: int,  # Added
        channels: int,  # Added
        model: str = "gpt-4o-mini-transcribe",  # Default to faster model
        language: Optional[str] = None,
        # Callbacks
        on_partial_transcript: Optional[Callable[[str], None]] = None,
        on_final_transcript: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_connected: Optional[Callable[[], None]] = None,
        on_disconnected: Optional[Callable[[], None]] = None,
        # VAD settings (optional, defaults handled by OpenAI if None)
        vad_threshold: Optional[float] = None,
        vad_prefix_padding_ms: Optional[int] = None,
        vad_silence_duration_ms: Optional[int] = None,
        # Noise reduction (optional)
        noise_reduction_type: Optional[str] = None,  # e.g., "near_field"
        # Include options (optional)
        include_options: Optional[
            List[str]
        ] = None,  # e.g., ["item.input_audio_transcription.logprobs"]
    ):
        """
        Initializes the OpenAIRealtimeTranscriber.

        Args:
            api_key (str): Your OpenAI API key.
            sample_rate (int): The sample rate of the input audio (e.g., 44100).
            channels (int): The number of channels in the input audio (e.g., 1).
            model (str): The OpenAI transcription model to use (e.g., 'gpt-4o-transcribe', 'gpt-4o-mini-transcribe').
            language (str, optional): ISO 639-1 language code (e.g., 'en', 'es'). Defaults to auto-detect.
            on_partial_transcript (callable, optional): Callback for partial
                transcription results `callback(text: str)`.
            on_final_transcript (callable, optional): Callback for final transcription results `callback(text: str)`.
            on_error (callable, optional): Callback for errors `callback(error_message: str)`.
            on_connected (callable, optional): Callback when WebSocket connection is established.
            on_disconnected (callable, optional): Callback when WebSocket connection is closed.
            vad_threshold (float, optional): Server-side VAD threshold.
            vad_prefix_padding_ms (int, optional): Server-side VAD prefix padding.
            vad_silence_duration_ms (int, optional): Server-side VAD silence duration.
            noise_reduction_type (str, optional): Noise reduction type ("near_field" or "far_field").
            include_options (List[str], optional): Additional data to include in responses.
        """
        if not api_key:
            raise ValueError("API key is required for OpenAIRealtimeTranscriber.")

        self.api_key = api_key
        self.model = model
        self.language = language
        self.sample_rate = sample_rate  # Added
        self.channels = channels  # Added
        self.vad_settings = {
            "threshold": vad_threshold,
            "prefix_padding_ms": vad_prefix_padding_ms,
            "silence_duration_ms": vad_silence_duration_ms,
        }
        self.noise_reduction_type = noise_reduction_type
        self.include_options = include_options or []

        # Callbacks
        self.on_partial_transcript = on_partial_transcript
        self.on_final_transcript = on_final_transcript
        self.on_error = on_error
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.receive_task: Optional[asyncio.Task] = None
        self.is_connected = False
        # Removed session_id and _session_ready_event

        logger.info(
            f"OpenAIRealtimeTranscriber initialized. Model: {self.model}, Language: {self.language or 'auto'}"
        )

    async def _get_ephemeral_token(self) -> str:
        """Creates a transcription session via REST API to get an ephemeral token."""
        logger.info("Requesting ephemeral token for WebSocket connection...")
        payload = {
            "input_audio_format": EXPECTED_AUDIO_FORMAT_TYPE,  # Send as string, not object
            "input_audio_transcription": {
                "model": self.model,
            },
            # Add other REST-configurable options if needed (e.g., language, prompt)
        }
        if self.language:
            payload["input_audio_transcription"]["language"] = self.language
        # Note: VAD and noise reduction are configured via WebSocket update message later

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2",  # Header specific to this REST endpoint
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENAI_REST_SESSION_URL, json=payload, headers=headers
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        error_msg = f"Failed to create transcription session (HTTP {resp.status}): {text}"
                        logger.error(error_msg)
                        raise OpenAIRealtimeError(error_msg)
                    data = await resp.json()
                    token = data.get("client_secret", {}).get("value")
                    if not token:
                        error_msg = "Ephemeral token not found in REST API response."
                        logger.error(f"{error_msg} Response: {data}")
                        raise OpenAIRealtimeError(error_msg)
                    logger.info("Ephemeral token obtained successfully.")
                    return token
        except aiohttp.ClientError as e:
            error_msg = f"HTTP client error getting ephemeral token: {e}"
            logger.error(error_msg, exc_info=True)
            raise OpenAIRealtimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error getting ephemeral token: {e}"
            logger.error(error_msg, exc_info=True)
            raise OpenAIRealtimeError(error_msg) from e

    async def connect(self):
        """Gets ephemeral token, establishes WebSocket connection, sends config, starts receiver."""
        if self.is_connected:
            logger.warning("Already connected or connecting.")
            return

        try:
            # 1. Get ephemeral token via REST API
            ephemeral_token = await self._get_ephemeral_token()

            # 2. Connect to WebSocket using the token
            logger.info(
                f"Attempting to connect to OpenAI WebSocket: {OPENAI_WEBSOCKET_URL}"
            )
            connection_headers = {
                "Authorization": f"Bearer {ephemeral_token}",
                "OpenAI-Beta": "realtime=v1",  # Header for WebSocket connection
            }
            self.websocket = await websockets.connect(
                OPENAI_WEBSOCKET_URL,
                additional_headers=connection_headers,
                ping_interval=20,
                ping_timeout=10,
            )
            self.is_connected = True
            logger.info("WebSocket connection established.")

            # 3. Send initial configuration update via WebSocket
            await self._send_initial_config()

            # 4. Start listening for messages
            self.receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Receiver loop started.")

            if self.on_connected:
                self.on_connected()

        except OpenAIRealtimeError as e:  # Catch errors from _get_ephemeral_token
            error_msg = f"Failed to connect (token error): {e}" # More specific msg
            logger.error(error_msg)
            self.is_connected = False
            if self.on_error:
                self.on_error(error_msg)
        except websockets.exceptions.InvalidStatusCode as e:
            reason = e.response.reason if e.response else "No reason"
            error_msg = (
                f"WebSocket connection failed: Status {e.status_code} - {reason}."
            )
            logger.error(error_msg, exc_info=True)
            self.is_connected = False
            if self.on_error:
                self.on_error(error_msg)
            # Don't raise, just report error
        # Add specific handling for common network errors during connect
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
             error_msg = f"Network error during WebSocket connection: {e}"
             logger.error(error_msg, exc_info=True)
             self.is_connected = False
             if self.on_error:
                 self.on_error(error_msg)
        except Exception as e: # General fallback
            error_msg = f"Unexpected error during connection: {e}"
            logger.error(error_msg, exc_info=True)
            self.is_connected = False
            if self.on_error:
                self.on_error(error_msg)

    async def _send_initial_config(self):
        """Sends the session configuration update message via WebSocket."""
        if not self.websocket or not self.is_connected:
            logger.error("Cannot send config, WebSocket not connected.")
            return

        # Construct the session update payload based on the example
        # Note: Audio format is set via REST. Model/language are set here as per example.
        # Construct the session update payload *exactly* as shown in the functional example
        session_config = {
            "input_audio_transcription": {
                "model": self.model,
                "language": self.language or "en",  # Default to 'en' if not provided
                "prompt": "",  # Add empty prompt as per example (can be configured later if needed)
            },
            "turn_detection": {
                "type": "server_vad",
                # Use configured silence duration or default to 1000ms from example
                "silence_duration_ms": self.vad_settings.get("silence_duration_ms")
                or 1000,
                # Do not include threshold or prefix_padding_ms in this update message
            },
            # Do not include 'include' or 'input_audio_noise_reduction' in this update message
        }

        # The main message structure required by the WebSocket API after connection
        config = {
            "type": "transcription_session.update",
            "session": session_config,  # Embed the actual config under the 'session' key
        }

        try:
            config_json = json.dumps(config)
            logger.debug(f"Sending initial config: {config_json}")
            await self.websocket.send(config_json)
            logger.info("Initial configuration sent.")
        except Exception as e:
            error_msg = f"Failed to send initial config: {e}"
            logger.error(error_msg, exc_info=True)
            if self.on_error:
                self.on_error(error_msg)
            # Consider disconnecting or raising here? For now, log and continue.
            raise OpenAIRealtimeError(error_msg) from e

    async def send_audio_chunk(self, raw_audio_data: bytes):
        """Encodes and sends an audio chunk over the WebSocket."""
        if not self.websocket or not self.is_connected:
            # logger.warning("Cannot send audio, WebSocket not connected.") # Can be noisy
            return

        try:
            encoded_data = base64.b64encode(raw_audio_data).decode("utf-8")
            payload = {"type": "input_audio_buffer.append", "audio": encoded_data}
            payload_json = json.dumps(payload)
            # logger.debug(f"Sending audio chunk: {len(raw_audio_data)} bytes") # Very noisy
            await self.websocket.send(payload_json)
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("WebSocket closed while trying to send audio chunk.")
            await self.disconnect()  # Ensure cleanup
        except Exception as e:
            error_msg = f"Failed to send audio chunk: {e}"
            logger.error(error_msg, exc_info=True)
            if self.on_error:
                self.on_error(error_msg)
            # Consider disconnecting on send errors?

    async def _receive_loop(self):
        """Continuously listens for messages from the WebSocket."""
        logger.info("Receive loop started.")
        try:
            async for message in self.websocket:
                # logger.debug(f"Received message: {message}") # Can be very verbose
                try:
                    data = json.loads(message)
                    message_type = data.get("type")

                    # Handle new event types based on example and logs
                    if (
                        message_type
                        == "conversation.item.input_audio_transcription.delta"
                    ):
                        delta_text = data.get("delta", "")
                        if self.on_partial_transcript and delta_text:
                            # Note: The API might send multiple deltas rapidly.
                            # The UI handler should append or replace based on desired behavior.
                            # For now, we just pass the delta text.
                            self.on_partial_transcript(delta_text)
                    elif (
                        message_type
                        == "conversation.item.input_audio_transcription.completed"
                    ):
                        final_text = data.get("transcript", "")
                        if self.on_final_transcript and final_text:
                            self.on_final_transcript(final_text)
                        # Consider breaking the loop here if only one final transcript is expected per session?
                        # break
                    elif message_type == "input_audio_buffer.speech_started":
                        logger.debug("Speech started event received.")
                        pass  # Or trigger UI indication
                    elif message_type == "input_audio_buffer.speech_stopped":
                        logger.debug("Speech stopped event received.")
                        pass  # Or trigger UI indication
                    elif message_type == "input_audio_buffer.committed":
                        logger.debug("Audio buffer committed event received.")
                        pass
                    elif message_type == "conversation.item.created":
                        logger.debug("Conversation item created event received.")
                        pass
                    # We no longer explicitly wait for/use transcription_session.created
                    # It might still arrive, log it if needed for debugging, but don't rely on it.
                    elif message_type == "transcription_session.created":
                        logger.debug(
                            f"Received (but not using) transcription_session.created: {json.dumps(data)}"
                        )
                        # No action needed based on the example workflow
                    elif message_type == "error":
                        # Log the full error JSON received from OpenAI for detailed diagnosis
                        full_error_json = json.dumps(data)
                        logger.error(
                            f"OpenAI WebSocket Error Received: {full_error_json}"
                        )
                        # Extract details for the callback, fallback if needed
                        error_details = data.get(
                            "details", "Unknown error from OpenAI WebSocket"
                        )
                        if self.on_error:
                            self.on_error(f"OpenAI Error: {error_details}")
                        # Decide if we should disconnect on error
                        # await self.disconnect()
                        # break # Exit loop on error?
                    else:
                        logger.warning(f"Received unknown message type: {message_type}")
                        # logger.debug(f"Unknown message data: {data}")

                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON message: {message}")
                except Exception as e:
                    logger.error(
                        f"Error processing received message: {e}", exc_info=True
                    )
                    if self.on_error:
                        self.on_error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosedOK:
            logger.info("WebSocket connection closed normally.")
        except websockets.exceptions.ConnectionClosedError as e:
            # More specific logging for closed connection error
            error_msg = f"WebSocket connection closed unexpectedly: Code {e.code}, Reason: {e.reason}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(error_msg) # Pass the detailed error
        except Exception as e:
            # Catch potential errors during loop iteration/websocket interaction
            error_msg = f"Unexpected error in receive loop: {e}"
            logger.error(error_msg, exc_info=True)
            if self.on_error:
                self.on_error(error_msg)
        finally:
            logger.info("Receive loop finished.")
            await self.disconnect(
                from_receive_loop=True
            )  # Ensure cleanup if loop exits unexpectedly

    async def disconnect(self, from_receive_loop=False):
        """Closes the WebSocket connection and cleans up resources."""
        # Prevent disconnect attempts if already disconnecting or disconnected
        if (
            not self.is_connected
            and not self.websocket
            and not (self.receive_task and not self.receive_task.done())
        ):
            # logger.debug("Already disconnected or disconnect in progress.")
            return

        logger.info("Disconnecting WebSocket...")
        self.is_connected = False  # Set flag immediately
        # Removed session_id and event reset

        # Cancel the receive task if it's running and wasn't the cause of disconnect
        if self.receive_task and not self.receive_task.done() and not from_receive_loop:
            logger.debug("Cancelling receive task...")
            self.receive_task.cancel()
            try:
                await self.receive_task  # Allow cancellation to propagate
            except asyncio.CancelledError:
                logger.debug("Receive task cancelled successfully.")
            except Exception as e:
                logger.error(
                    f"Error during receive task cancellation: {e}", exc_info=True
                )

        # Close the WebSocket connection
        if self.websocket:
            ws = self.websocket
            self.websocket = None  # Clear reference
            try:
                logger.debug("Closing WebSocket connection...")
                await ws.close()
                logger.info("WebSocket connection closed.")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}", exc_info=True)

        self.receive_task = None

        if self.on_disconnected:
            self.on_disconnected()


# Example usage (requires an async environment to run)
async def main_test():
    print("--- Testing OpenAIRealtimeTranscriber ---")
    logging.basicConfig(level=logging.DEBUG)  # Enable debug logging for test

    # --- IMPORTANT ---
    # For this test to work, you MUST:
    # 1. Set the OPENAI_API_KEY environment variable.
    # 2. Have a way to feed audio chunks (e.g., from a file or live input).
    #    This example simulates chunks.
    # --- IMPORTANT ---

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set. Skipping test.")
        return

    transcripts = {"partial": [], "final": []}
    errors = []

    def handle_partial(text):
        print(f"Partial: {text}")
        transcripts["partial"].append(text)

    def handle_final(text):
        print(f"FINAL: {text}")
        transcripts["final"].append(text)

    def handle_error(msg):
        print(f"ERROR: {msg}")
        errors.append(msg)

    def handle_connected():
        print("CONNECTED!")

    def handle_disconnected():
        print("DISCONNECTED!")

    transcriber = OpenAIRealtimeTranscriber(
        api_key=api_key,
        model="gpt-4o-mini-transcribe",
        on_partial_transcript=handle_partial,
        on_final_transcript=handle_final,
        on_error=handle_error,
        on_connected=handle_connected,
        on_disconnected=handle_disconnected,
    )

    try:
        await transcriber.connect()

        # Simulate sending audio chunks (replace with actual audio source)
        print("Simulating sending audio chunks for 5 seconds...")
        chunk_size = 1024 * 4  # Example chunk size
        for i in range(int(5 * DEFAULT_AUDIO_RATE / chunk_size)):  # Simulate 5 seconds
            if not transcriber.is_connected:
                break  # Stop if disconnected
            dummy_chunk = b"\x00" * chunk_size  # Send silence
            await transcriber.send_audio_chunk(dummy_chunk)
            await asyncio.sleep(
                chunk_size / DEFAULT_AUDIO_RATE
            )  # Simulate real-time interval

        print("Finished sending chunks.")
        # Wait a bit for final transcripts
        await asyncio.sleep(2)

    except OpenAIRealtimeError as e:
        print(f"Caught Transcriber Error: {e}")
    except Exception as e:
        print(f"Caught Unexpected Error: {e}")
        print(traceback.format_exc())
    finally:
        print("Ensuring disconnection...")
        await transcriber.disconnect()

    print("\n--- Test Summary ---")
    print(f"Partial transcripts received: {len(transcripts['partial'])}")
    print(f"Final transcripts received: {len(transcripts['final'])}")
    print(f"Errors received: {len(errors)}")
    print("--- OpenAIRealtimeTranscriber Test End ---")


if __name__ == "__main__":
    # Need to import os and load defaults for the test main block
    import os

    DEFAULT_AUDIO_RATE = 44100  # Define rate for test block if not imported elsewhere

    # Requires Python 3.7+ for asyncio.run
    try:
        asyncio.run(main_test())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
