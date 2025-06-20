# RivaVoice

A minimalist speech-to-text application for macOS with clean architecture and simple design.

## Features

- **One-Button Recording**: Press hotkey to start/stop recording
- **Instant Transcription**: Powered by ElevenLabs API
- **Auto-Paste**: Transcribed text automatically copied to clipboard
- **Background Operation**: Runs silently in the background
- **Clean Architecture**: Separate backend core with pluggable UI
- **Multiple Modes**: Standard, chunked, and direct-type modes
- **Audio Feedback**: System sounds for start/stop recording

## Quick Start

### Prerequisites

- macOS 10.15 or later
- Python 3.8+
- ElevenLabs API key

### Installation

```bash
# Clone the repository
git clone https://github.com/199-bio/rivavoice-transcriber.git
cd rivavoice-transcriber

# Install dependencies
pip install -r requirements.txt

# Run the terminal UI
python rivavoice.py
```

### First Run

1. The app will prompt for your ElevenLabs API key
2. Set your preferred hotkey (default: F1)
3. Press the hotkey to start/stop recording

## Architecture

```
rivavoice/
├── rivacore/              # Core backend package
│   ├── backend.py         # Main API class
│   ├── audio.py           # Audio recording
│   ├── transcriber.py     # ElevenLabs client
│   ├── hotkey.py          # Global hotkey manager
│   └── config.py          # Settings persistence
├── rivavoice.py           # Terminal UI
├── requirements.txt       # Dependencies
└── test_backend.py        # Interactive test
```

### Design Principles

- **Minimalist**: Only essential features
- **Reliable**: Comprehensive error handling
- **Clean**: UI-agnostic backend
- **Fast**: Optimized for quick transcription

## Configuration

Settings are stored in `~/.rivavoice/config.json`:

```json
{
  "api_key": "your-elevenlabs-key",
  "hotkey": "F1",
  "timeout_minutes": 5,
  "auto_paste": true,
  "preserve_clipboard": false,
  "chunked_mode": false
}
```

## Usage Modes

### Standard Mode
Press hotkey to start recording, press again to stop and transcribe.

### Chunked Mode
Automatically transcribes after detecting silence. Great for dictation.

### Direct Type Mode
When `preserve_clipboard` is enabled, simulates keyboard typing instead of using clipboard.

## API

```python
from rivacore import RivaBackend

# Initialize backend
backend = RivaBackend()

# Configure
backend.set_api_key("your-key")
backend.set_hotkey("F1")

# Record and transcribe
backend.start_recording()
text = backend.stop_recording()
```

## Development

### Running Tests

```bash
# Interactive backend test
python test_backend.py

# Test specific features
python test_chunked.py
python test_fn_key.py
```

### Building a UI

The backend is UI-agnostic. To build your own UI:

1. Import `RivaBackend` from `rivacore`
2. Use the backend API for all operations
3. Handle callbacks for recording state changes

## Troubleshooting

### Microphone Access
macOS requires explicit microphone permission. Grant access when prompted.

### Hotkey Not Working
Some applications may capture hotkeys. Try a different key combination.

### API Errors
Ensure your ElevenLabs API key is valid and has sufficient credits.

## License

MIT License - See LICENSE file for details.

## Credits

Built with:
- [PyAudio](https://pypi.org/project/PyAudio/) - Audio recording
- [ElevenLabs](https://elevenlabs.io/) - Speech transcription
- [pynput](https://pypi.org/project/pynput/) - Global hotkeys