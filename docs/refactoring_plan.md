# Detailed Refactoring Plan for MainWindow

**Overall Goal:** Decouple responsibilities from the large `MainWindow` class into separate, focused controller/manager classes located in a new `rivavoice/core/` directory. This will make the code easier to understand, test, and modify.

**Refactoring Strategy:** Extract responsibilities incrementally, ensuring the application remains functional after each major extraction. Use dependency injection (passing objects during initialization) and Qt's signal/slot mechanism for communication between the new classes and `MainWindow`.

---

**Detailed Refactoring Steps:**

1.  **Create `rivavoice/core/` Directory:**
    *   **Action:** Create a new directory `rivavoice/core/`.
    *   **Action:** Add an empty `rivavoice/core/__init__.py` file.
    *   **Purpose:** Provide a dedicated location for the new non-UI controller/manager classes, separating core logic from UI presentation.

2.  **Extract Async Task Management (`AsyncTaskManager`):**
    *   **File:** Create `rivavoice/core/async_manager.py`.
    *   **Class:** Define `AsyncTaskManager(QObject)`.
    *   **Move Methods:** Move the following methods from `MainWindow` to `AsyncTaskManager`:
        *   `_start_asyncio_thread`
        *   `_run_asyncio_loop`
        *   `_stop_asyncio_thread`
        *   `submit_async_task`
    *   **Adapt Methods:** Modify these methods to manage their own `asyncio` loop (`self.loop`), thread (`self.thread`), and task queue (`self.task_queue`) internally.
    *   **Integrate:**
        *   In `MainWindow.__init__`: Instantiate `self.async_manager = AsyncTaskManager()`.
        *   In `MainWindow`: Replace all calls to `self.submit_async_task(...)` with `self.async_manager.submit_async_task(...)`.
        *   Call `self.async_manager.start()` early in `MainWindow.__init__` (after essential setup).
        *   Call `self.async_manager.stop()` in `MainWindow.closeEvent` and/or `quit_app` to ensure graceful shutdown.
    *   **Purpose:** Isolate all logic related to running the background `asyncio` event loop and submitting coroutines to it.

3.  **Extract Keybind Management (`AppKeybindHandler`):**
    *   **File:** Create `rivavoice/core/keybind_handler.py`.
    *   **Class:** Define `AppKeybindHandler(QObject)`.
    *   **Move Logic:**
        *   Move the core logic of `MainWindow._initialize_keybind_manager` into `AppKeybindHandler.__init__` or a `start_listening(config)` method. This class will need the `Config` object passed to it.
        *   Move the logic of `MainWindow._handle_keybind_activation_callback` and `MainWindow._handle_keybind_error_callback` into private methods within `AppKeybindHandler`.
    *   **Define Signals:** Add signals to `AppKeybindHandler`:
        *   `keybind_activated = pyqtSignal(str)` # Emits 'press', 'release', 'single', 'double'
        *   `keybind_error = pyqtSignal(str)` # Emits error message
    *   **Emit Signals:** Modify the handler methods (previously `_handle_keybind_activation_callback`, etc.) to `emit` these signals instead of directly manipulating `MainWindow` state or calling its methods.
    *   **Integrate:**
        *   In `MainWindow.__init__`: Instantiate `self.keybind_handler = AppKeybindHandler(self.config)`.
        *   In `MainWindow`: Create new slots (or adapt existing ones) like `on_keybind_activated(press_type)` and `on_keybind_error(error_msg)`.
        *   Connect these slots to the corresponding signals from `self.keybind_handler`. The `on_keybind_activated` slot will now contain the logic that decides whether to start/stop recording based on `press_type` and current app state.
        *   Call `self.keybind_handler.start_listening()` after initialization.
        *   Ensure `self.keybind_handler.stop_listener()` is called during cleanup (`closeEvent`/`quit_app`).
    *   **Purpose:** Isolate global keyboard shortcut detection, parsing, and event notification.

4.  **Extract Transcription Provider Logic (`TranscriptionController`):**
    *   **File:** Create `rivavoice/core/transcription_controller.py`.
    *   **Class:** Define `TranscriptionController(QObject)`.
    *   **Move Logic:**
        *   Move the logic from `MainWindow._load_config_and_init_provider` into the controller's `__init__` or an `update_provider(config)` method. It needs the `Config` object and the `AsyncTaskManager` instance.
        *   Move `MainWindow._cleanup_provider` logic into a `cleanup()` method in the controller.
    *   **State:** The controller should store the active `transcriber` instance (`self.transcriber`) and the active `provider_type`.
    *   **Interface:** Define methods like `get_active_provider_type()`, `get_transcriber_instance()`.
    *   **Define Signals:** Add signals for all transcription events:
        *   `partial_transcript_received = pyqtSignal(str)`
        *   `final_transcript_received = pyqtSignal(str)`
        *   `transcription_error_occurred = pyqtSignal(str)`
        *   `transcription_started = pyqtSignal()`
        *   `transcription_complete = pyqtSignal(str, int, int)` # text, word_count, char_count
    *   **Callbacks:** When initializing `ElevenLabsTranscriber` or `OpenAIRealtimeTranscriber` inside the controller, pass internal methods (or lambdas) that emit the corresponding signals as the `on_...` callbacks. For example, the `on_partial_transcript` callback passed to the transcriber would simply do `self.partial_transcript_received.emit(text)`.
    *   **Integrate:**
        *   In `MainWindow.__init__`: Instantiate `self.transcription_controller = TranscriptionController(self.config, self.async_manager)`.
        *   In `MainWindow`: Connect slots (like `_handle_partial_transcript`, `_handle_final_transcript`, `_handle_transcription_error`, `on_transcription_started`, `on_transcription_complete`) to the controller's signals.
        *   Replace direct management of `self.transcriber` in `MainWindow` with calls to `self.transcription_controller` methods (e.g., getting the instance when needed).
        *   Call `self.transcription_controller.cleanup()` during `closeEvent`/`quit_app`.
    *   **Purpose:** Isolate the selection, initialization, lifecycle management, and event handling related to the different transcription APIs.

5.  **Extract Recording Logic (`RecordingManager`):**
    *   **File:** Create `rivavoice/core/recording_manager.py`.
    *   **Class:** Define `RecordingManager(QObject)`.
    *   **Move Methods:** Move the core logic of `MainWindow.start_recording` and `MainWindow.stop_recording` into methods within `RecordingManager`.
    *   **Dependencies:** The `RecordingManager` will need references to `AudioRecorder`, `TranscriptionController`, `Config`, and `AsyncTaskManager`. Pass these during `__init__`.
    *   **Define Signals:** Add signals for recording state:
        *   `recording_started = pyqtSignal()`
        *   `recording_stopped = pyqtSignal(str)` # Optional file path
        *   `recording_error = pyqtSignal(str)` # Error message
        *   `status_update = pyqtSignal(str)` # To update UI status messages
    *   **Callbacks:** Pass internal methods (or lambdas emitting signals) as the `on_recording_started`, `on_recording_stopped`, `on_recording_error` callbacks to the `AudioRecorder` instance managed by this class.
    *   **Integrate:**
        *   In `MainWindow.__init__`: Instantiate `self.recording_manager = RecordingManager(self.recorder, self.transcription_controller, self.config, self.async_manager)`.
        *   In `MainWindow`: Connect slots (like `on_recording_started`, `on_recording_stopped`, `on_recording_error`, `update_status`) to the manager's signals.
        *   In `MainWindow`: Connect the `on_keybind_activated` slot (which receives signals from `AppKeybindHandler`) to call `self.recording_manager.request_start()` or `self.recording_manager.request_stop()` based on the activation type and current state.
    *   **Purpose:** Isolate the state machine controlling the recording process, coordinating the audio recorder, transcription, and keybind events.

6.  **Refine UI Update Logic (Integrated with above steps):**
    *   **Action:** As the above controllers/managers are created and signals are connected to `MainWindow` slots, ensure these slots primarily focus on updating the UI.
    *   **Example:** The slot connected to `RecordingManager.recording_started` in `MainWindow` would call `self.recording_view.set_recording_state(True)`. The slot connected to `TranscriptionController.partial_transcript_received` would call `self.recording_view.update_partial_status(text)`.
    *   **Action:** Minimize direct calls from `MainWindow` into the internal widgets of `RecordingView` or `SettingsView`. Prefer passing necessary data via method calls or signals to the view itself, letting the view manage its own children.
    *   **Purpose:** Make `MainWindow` a central coordinator that delegates actions to controllers/managers and UI updates to views via signals and slots, rather than containing all the detailed logic itself.

7.  **Final Cleanup:**
    *   **Action:** Thoroughly review `MainWindow` for any remaining methods or attributes related to the extracted responsibilities and remove them.
    *   **Action:** Verify all signal/slot connections are correct and cover the necessary interactions.
    *   **Action:** Update all necessary `import` statements in `MainWindow`, the new core classes, and potentially the UI view classes.
    *   **Action:** Run `flake8` and `pytest` to catch any errors introduced during refactoring.