# RivaVoice v2 - Clean Architecture Rewrite

A minimalist speech-to-text application with a clean backend/frontend separation.

## Project Status

### ✅ Completed: Core Backend (`rivacore/`)

A fully functional, UI-agnostic backend that provides:

- **Recording**: Audio capture with configurable timeout (default 5 minutes)
- **Transcription**: ElevenLabs API integration 
- **Hotkey**: Global hotkey support with toggle mode
- **Storage**: Automatic transcript saving to `~/Documents/RivaTranscripts/`
- **Audio Feedback**: System sounds for start/stop recording
- **Configuration**: Persistent settings in `~/.rivavoice/config.json`
- **Logging**: Debug logs with rotation in `~/.rivavoice/debug.log`

### 🚧 Not Started: Frontend UI

**Decision Pending** - Evaluating options:
- Web-based (Electron, Tauri)
- Native macOS (SwiftUI via PyObjC)
- Cross-platform (Flutter, React Native)
- Keep PyQt6 (from v1)

## Backend API

```python
from rivacore import RivaBackend

backend = RivaBackend()

# Configuration
backend.set_api_key("your-elevenlabs-key")
backend.set_hotkey("F1")  
backend.set_timeout_minutes(5)

# Recording (usually triggered by hotkey)
backend.start_recording()
text = backend.stop_recording()  # Returns transcribed text

# Status
status = backend.get_status()
# {'recording': False, 'hotkey': 'F1', 'timeout_minutes': 5, 'api_key_set': True}
```

## Architecture Principles

1. **Complete Separation**: Backend has zero UI dependencies
2. **Minimalist Design**: Only essential features (record → transcribe → clipboard)
3. **Thread Safe**: Proper locking for concurrent access
4. **Error Resilient**: Graceful handling of missing audio devices, API failures
5. **Self-Contained**: All settings managed by backend

## Quick Test

```bash
# Install dependencies
pip install -r requirements.txt

# Test the backend
python test_backend.py
```

## Design Philosophy

Following Jony Ive/Steve Jobs principles:
- **Simplicity**: One button, one function
- **Clarity**: Clear audio feedback
- **Invisibility**: Runs in background, appears only when needed
- **Reliability**: Just works, every time

## Implementation Notes

### What Makes This v2

1. **Clean Architecture**: UI can be swapped without touching business logic
2. **Proper Threading**: Recording happens in background thread with locks
3. **Resource Management**: Cleans up temp files, handles PyAudio carefully
4. **Production Ready**: Comprehensive error handling, logging, configuration

### Key Improvements from v1

- No UI/backend coupling
- Thread-safe recording state
- Automatic temp file cleanup
- Required package checking
- Consistent error handling
- Single responsibility per module

## Next Steps

1. **Choose UI Framework**: Evaluate options based on:
   - Distribution ease
   - Platform integration (system tray, global hotkeys)
   - Development speed
   - User experience

2. **Implement UI**: Create minimal interface that:
   - Shows recording status
   - Allows API key entry
   - Displays errors gracefully
   - Lives in system tray

3. **Package & Distribute**: 
   - macOS app bundle
   - Code signing
   - Auto-updates

## File Structure

```
v2/
├── rivacore/              # Core backend package
│   ├── __init__.py       
│   ├── backend.py        # Main API class
│   ├── audio.py          # PyAudio recording
│   ├── transcriber.py    # ElevenLabs client
│   ├── hotkey.py         # Global hotkey manager
│   └── config.py         # Settings persistence
├── requirements.txt       # Python dependencies
├── test_backend.py        # Interactive test script
└── README.md             # This file
```

## Dependencies

- `pyaudio` - Audio recording
- `requests` - API calls
- `pyperclip` - Clipboard access
- `pynput` - Global hotkeys

## Known Limitations

1. **macOS Only**: Hotkeys and audio feedback use macOS-specific features
2. **ElevenLabs Only**: Single transcription provider (by design)
3. **No Hold-to-Record**: Toggle mode only (press to start, press to stop)

---

**Remember**: This is the working directory for v2. The original v1 code is in the parent directory.