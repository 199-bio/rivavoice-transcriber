# Plan: Integrate OpenAI Real-time Transcription via WebSocket

**Goal:** Integrate OpenAI's real-time transcription via WebSocket as an alternative to the existing ElevenLabs file-based transcription.

**1. Dependencies:**
*   Add the following Python libraries to the project's dependencies (e.g., in `setup.py` or `requirements.txt`):
    *   `openai`
    *   `websockets`
*   Utilize Python's built-in libraries:
    *   `asyncio` (for asynchronous operations)
    *   `base64` (for encoding audio chunks)
    *   `json` (for WebSocket message payloads)
    *   `logging`

**2. Configuration (Managed by `rivavoice` application):**
*   Introduce a configuration setting to select the transcription provider: `'elevenlabs'` or `'openai_realtime'`.
*   Implement secure loading of API keys based on the selected provider (e.g., read `ELEVENLABS_API_KEY` or `OPENAI_API_KEY` from environment variables). **Crucially, do not hardcode API keys in the source code.**
*   Add configuration options specific to OpenAI real-time:
    *   `model`: (e.g., `'gpt-4o-transcribe'`, `'gpt-4o-mini-transcribe'`)
    *   `language`: (Optional) ISO language code.
    *   (Optional) Voice Activity Detection (VAD) parameters if using server-side VAD.

**3. Refactor `pyscribetranscribe/recorder.py` (`AudioRecorder`):**
*   Modify the class to support yielding audio chunks during recording.
*   Add an optional `chunk_callback` parameter to `__init__`. This callback function will be called with raw audio data chunks.
*   In the `_record_audio` method's recording loop, call `self.chunk_callback(data)` immediately after reading an audio chunk (`data = self.stream.read(...)`) if the callback is provided.
*   The `self.frames.append(data)` logic might become optional or unnecessary for the real-time path.
*   The `_save_recording` method might be bypassed or made optional when using the real-time path.

**4. Create New Class for OpenAI Real-time Transcription:**
*   Create a new file, e.g., `pyscribetranscribe/openai_realtime_transcriber.py`.
*   Define a new class `OpenAIRealtimeTranscriber`.
*   **`__init__`:** Accept `api_key`, `model`, `language`, optional VAD settings, and callbacks (`on_partial_transcript`, `on_final_transcript`, `on_error`).
*   **`async connect()`:** Establish WebSocket connection to `wss://api.openai.com/v1/realtime?intent=transcription`, handle authentication, send initial configuration payload, and start the `_receive_loop` task.
*   **`async send_audio_chunk(raw_audio_data)`:** Base64 encode the audio chunk, format the JSON payload (`{"type": "input_audio_buffer.append", ...}`), and send it via the WebSocket.
*   **`async _receive_loop()`:** Continuously listen for incoming WebSocket messages, parse JSON, identify event types, and trigger the appropriate callbacks (`on_partial_transcript`, `on_final_transcript`, `on_error`).
*   **`async disconnect()`:** Send closing messages (if required by API), cancel the receive task, and close the WebSocket connection.

**5. Refactor Existing `Transcriber`:**
*   Rename the existing `Transcriber` class in `pyscribetranscribe/transcriber.py` to `ElevenLabsTranscriber` to clearly distinguish its purpose (file-based ElevenLabs transcription).

**6. Integrate into `rivavoice` Application:**
*   Modify the main application logic to handle `asyncio`. This might involve running `asyncio.run()` or managing an event loop if the UI framework allows.
*   Based on the configuration (`'elevenlabs'` or `'openai_realtime'`), instantiate the correct transcriber class (`ElevenLabsTranscriber` or `OpenAIRealtimeTranscriber`).
*   **For OpenAI Real-time:**
    *   Define an `async` callback function (`handle_audio_chunk`) that calls `openai_transcriber.send_audio_chunk()`.
    *   Instantiate `AudioRecorder` passing `handle_audio_chunk` as the `chunk_callback`.
    *   Instantiate `OpenAIRealtimeTranscriber`, passing callbacks that update the UI with partial/final transcripts.
    *   Coordinate the start: `asyncio.create_task(openai_transcriber.connect())` followed by `recorder.start_recording()`.
    *   Coordinate the stop: `recorder.stop_recording()` followed by `asyncio.create_task(openai_transcriber.disconnect())`.
*   **For ElevenLabs:** Maintain the existing workflow (record -> save -> transcribe file).
*   Implement robust error handling for audio, network, WebSocket, and API issues, providing feedback to the user via the UI.

**Diagram (Simplified OpenAI Realtime Flow):**

```mermaid
graph TD
    subgraph RivaVoice Application
        direction LR
        UI(UI/Controller) -- Manages --> Rec(AudioRecorder)
        UI -- Manages --> Trans(OpenAIRealtimeTranscriber)
    end

    subgraph External Services
        Mic(Microphone)
        OpenAI(OpenAI WebSocket API)
    end

    User -- Start Recording --> UI
    UI -- Configures & Starts --> Rec(chunk_callback=Trans.send_audio)
    UI -- Connects --> Trans

    Rec -- Captures --> Mic
    Rec -- chunk_callback(data) --> Trans

    Trans -- connect() & config --> OpenAI
    Trans -- send_audio_chunk(data) --> OpenAI

    OpenAI -- Transcription Events --> Trans
    Trans -- Callbacks (partial/final text) --> UI
    UI -- Updates Display --> User

    User -- Stop Recording --> UI
    UI -- stop() --> Rec
    UI -- disconnect() --> Trans
    Trans -- close() --> OpenAI