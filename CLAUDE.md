# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Run the application
python app.py

# Or run as module
python -m rivavoice
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py
pytest tests/test_transcribers.py

# Run with coverage
pytest --cov=rivavoice --cov=pyscribetranscribe
```

### Linting
```bash
# Run flake8 linter
flake8 .

# Run black formatter (check mode)
black --check .

# Apply black formatting
black .
```

### Building macOS App
```bash
# Build the macOS app bundle
python setup.py py2app

# Create icon from PNG
./create_icns.sh
```

### Installing Dependencies
```bash
# Install from pyproject.toml
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

## Architecture

RivaVoice is a macOS speech-to-text application with these key components:

### Core Modules

**rivavoice/** - Main application package
- `__main__.py` - Entry point with single-instance checking, permissions handling, and Qt application setup
- `config.py` - JSON-based configuration management using ~/.rivavoiceconfig.json
- `constants.py` - All application constants, config keys, and defaults
- `tray_manager.py` - System tray integration for background operation
- `utils.py` - Shared utilities

**rivavoice/ui/** - PyQt6-based UI components
- `main_window.py` - Main application window with recording controls
- `recording_view.py` - Recording interface with visual feedback (pulsing orb)
- `settings_view.py` - Settings management interface
- `onboarding.py` - First-run onboarding flow
- `components.py` - Reusable UI components (card-based design)

**pyscribetranscribe/** - Audio recording and transcription
- `recorder.py` - PyAudio-based audio recording with WAV file output
- `transcriber.py` - ElevenLabs API transcription client
- `openai_realtime_transcriber.py` - OpenAI WebSocket-based real-time transcription

### Key Design Patterns

1. **Configuration**: Centralized in `constants.py` with Config class for persistence
2. **Callbacks**: Extensive use of callbacks for async operations (recording, transcription)
3. **Single Instance**: Uses QLocalServer/Socket to ensure only one app instance
4. **Permissions**: Handles macOS microphone and input monitoring permissions
5. **Background Operation**: Runs as menu bar app (LSUIElement=True)

### External Dependencies

- **PyQt6**: UI framework
- **pyaudio**: Audio recording
- **pykeybindmanager**: Global keyboard shortcuts (FN key)
- **requests**: HTTP API calls
- **websockets/aiohttp**: Real-time transcription
- **pyperclip**: Clipboard integration

### API Integration

- **ElevenLabs**: Primary transcription service (scribe_v1 model)
- **OpenAI**: Alternative real-time transcription (gpt-4o-mini-transcribe)

Both require API keys configured in settings.