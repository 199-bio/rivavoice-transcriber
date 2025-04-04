# RivaVoice

A minimalist speech-to-text application with a beautiful card-based UI. Record your voice and automatically transcribe it using ElevenLabs' speech recognition API. The transcribed text is automatically copied to the clipboard and optionally pasted at the cursor position.

## Features

- Beautiful card-based UI with rounded corners inspired by Apple's design language
- Record audio with a visual pulsing orb that changes color to indicate recording status
- Transcribe speech to text using ElevenLabs API
- Automatically paste transcribed text at cursor position
- Configurable settings with a clean interface
- Keyboard shortcut (FN key) support for easy recording

## Requirements

- Python 3.6+
- PyQt6
- pyaudio
- pynput
- requests
- pyperclip

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/rivavoice.git
cd rivavoice
```

2. Install dependencies:
```
pip install PyQt6 pyaudio pynput requests pyperclip
```

3. Run the application:
```
python voice.py
```

## Usage

- Double-press the FN key to start recording
- Single-press the FN key to stop recording and start transcription
- The transcribed text will be automatically copied to your clipboard and pasted at the cursor position
- Click the settings button to configure your ElevenLabs API key and other preferences

## Project Structure

The project has been reorganized into a more modular structure:

```
rivavoice/
├── __init__.py
├── __main__.py
├── config.py
├── utils.py
├── audio/
│   ├── __init__.py
│   ├── recorder.py
│   └── transcriber.py
└── ui/
    ├── __init__.py
    ├── components.py
    ├── main_window.py
    ├── recording_view.py
    └── settings_view.py
voice.py
doubleping.wav
singleping.wav
README.md
```

## Configuration

The app stores its configuration in `~/.rivavoiceconfig.json`. You can set your ElevenLabs API key, transcript folder, keybinding, and sound preferences in the settings view.

## Credits

- Card-based UI inspired by Apple's design language
- Sound effects for recording start/stop
- Transcription powered by ElevenLabs API 