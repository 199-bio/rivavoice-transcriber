# RivaVoice Improvement Plan

This plan details actionable steps to refactor, enhance robustness, add testing, and modernize the RivaVoice codebase, categorized by risk and effort.

## Low Risk / Low Effort (Good Starting Points)

1.  **Code Style/Linting (Step 14):**
    *   **Detail:** Install `flake8` and `black`. Configure `black`. Run `black .` to auto-format. Run `flake8 .` and fix reported issues manually.
    *   **Risk/Effort:** Low. Mostly automated, improves consistency.

2.  **Improve Documentation (Step 13):**
    *   **Detail:** Add module/class/method docstrings and inline comments explaining purpose and complex logic, especially in `MainWindow`.
    *   **Risk/Effort:** Low. No code changes, improves understanding.

3.  **Resource Management Review (Step 15):**
    *   **Detail:** Review code for file/network/audio/thread resources. Ensure consistent closure using `try...finally` or `with` statements, especially in `AudioRecorder` and `OpenAIRealtimeTranscriber`.
    *   **Risk/Effort:** Low to Medium. Code review, localized changes improve stability.

4.  **API Key Validation (Step 6):**
    *   **Detail:** Add checks in `MainWindow` or `Config` to verify required API keys exist based on provider selection. Show error message if missing.
    *   **Risk/Effort:** Low. Simple conditional checks, UI feedback.

5.  **Audio Device Error Handling (Step 8):**
    *   **Detail:** In `AudioRecorder`, wrap `pyaudio` stream operations in `try...except OSError` blocks. Log errors and signal UI to show message.
    *   **Risk/Effort:** Low to Medium. Adds exception handling, may need UI signaling.

## Medium Risk / Medium Effort (Requires Careful Implementation)

6.  **Testing - Framework Setup (Step 9):**
    *   **Detail:** Add `pytest` dev dependency. Create `tests/` directory with `__init__.py` and a basic example test. Configure `pytest` if needed.
    *   **Risk/Effort:** Low effort for setup, Medium overall as it enables future testing.

7.  **Testing - Config Logic (Step 10):**
    *   **Detail:** Create `tests/test_config.py`. Use `pytest` fixtures (`tmp_path`) for temporary files. Test `Config` load/save/defaults.
    *   **Risk/Effort:** Medium. Requires `pytest` knowledge, mocking file system.

8.  **Testing - Transcription Logic (Step 11):**
    *   **Detail:** Create `tests/test_transcribers.py`. Use `pytest.mark.asyncio`. Mock network requests (`requests`, `websockets`) to simulate API responses/errors. Assert correct handling.
    *   **Risk/Effort:** Medium to High. Mocking async network calls is complex but vital.

9.  **Network/WebSocket Error Handling (Step 7):**
    *   **Detail:** In `OpenAIRealtimeTranscriber`, wrap `connect`, send, and receive operations in `try...except` blocks for specific network/WebSocket exceptions. Call `on_error` callback.
    *   **Risk/Effort:** Medium. Requires careful async exception handling and UI signaling via callback.

10. **Modernize Dependencies (Step 12):**
    *   **Detail:** Create `pyproject.toml`. Define build system, project metadata, dependencies (`[project.dependencies]`), and dev dependencies (`[project.optional-dependencies.dev]`). Update/simplify `setup.py`. Ensure `py2app` still works.
    *   **Risk/Effort:** Medium. Requires `pyproject.toml` knowledge, ensure build process remains functional.

## High Risk / High Effort (Significant Refactoring)

11. **Extract Async Task Management (Step 1):**
    *   **Detail:** Create `AsyncTaskManager` class. Move async loop/task/thread methods from `MainWindow` here. `MainWindow` instantiates and uses it. Ensure proper thread handling/cleanup.
    *   **Risk/Effort:** High. Affects core async logic. Requires careful implementation and testing.

12. **Extract Keybind Management (Step 2):**
    *   **Detail:** Create `AppKeybindHandler` class. Move keybind init/handling logic here. Handler needs callbacks/references to trigger `MainWindow` actions.
    *   **Risk/Effort:** High. Decouples logic but needs careful interface design.

13. **Extract Transcription Provider Logic (Step 3):**
    *   **Detail:** Create `TranscriptionController`. Move provider loading/init/cleanup logic here. Controller manages `self.transcriber` instance. `MainWindow` uses this controller.
    *   **Risk/Effort:** High. Centralizes logic but changes `MainWindow` interaction patterns.

14. **Extract Recording Logic (Step 4):**
    *   **Detail:** Create `RecordingManager`. Move `start_recording`/`stop_recording` logic here. Manager interacts with `AudioRecorder`, `TranscriptionController`. Needs callbacks/signals to update UI.
    *   **Risk/Effort:** High. Centralizes state but needs clear communication paths.

15. **Extract UI Update Logic (Step 5):**
    *   **Detail:** Refactor `MainWindow` to avoid direct manipulation of sub-view widgets. Pass data/state objects to views for self-updating, or use Qt Signals/Slots for communication between logical components and UI views.
    *   **Risk/Effort:** High. Changes fundamental UI update patterns. Best done incrementally with other refactoring.