# RivaVoice 🎙️

A lightning-fast, minimalist speech-to-text macOS app that lives in your menu bar. Press a hotkey, speak, and watch your words appear instantly.

![macOS](https://img.shields.io/badge/macOS-10.15+-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **🚀 Instant Transcription** - Powered by ElevenLabs' state-of-the-art speech recognition
- **⌨️ Global Hotkey** - Record from anywhere with a single keypress (default: Fn key)
- **📋 Smart Clipboard** - Transcribed text automatically copied and ready to paste
- **🎯 Menu Bar App** - Lightweight, always accessible, never in your way
- **🎨 Beautiful UI** - Clean, modern interface with smooth animations
- **🔒 Privacy First** - Audio processed locally, only transcription uses API

## 🎬 Quick Start

### Download Pre-built App

1. Download the latest release from [Releases](https://github.com/199-bio/rivavoice-transcriber/releases)
2. Open `RivaVoice.dmg` and drag to Applications
3. Launch RivaVoice and follow the setup wizard

### Build from Source

```bash
# Clone the repository
git clone https://github.com/199-bio/rivavoice-transcriber.git
cd rivavoice-transcriber

# Install dependencies
pip install -e .

# Run the app
python -m rivavoice
```

## 🔧 Configuration

On first launch, RivaVoice will guide you through:

1. **API Setup** - Enter your ElevenLabs API key ([Get one here](https://elevenlabs.io))
2. **Permissions** - Grant microphone and accessibility access
3. **Hotkey** - Choose your recording hotkey

Settings are stored in `~/.rivavoiceconfig.json`

## 🎯 Usage

1. **Start Recording** - Press your hotkey (default: Fn)
2. **Speak** - The recording indicator will pulse
3. **Stop Recording** - Press hotkey again
4. **Paste** - Your transcribed text is ready to paste anywhere!

### Pro Tips

- **Quick Mode**: Enable "Paste after transcription" for instant text insertion
- **Visual Feedback**: Watch the pulsing orb to confirm recording status
- **Background Recording**: Minimize the app - it keeps working from the menu bar

## 🏗️ Architecture

```
rivavoice/
├── rivavoice/          # Main application package
│   ├── ui/            # PyQt6 user interface
│   ├── config.py      # Settings management
│   └── tray_manager.py # Menu bar integration
├── pyscribetranscribe/ # Audio & transcription engine
│   ├── recorder.py    # PyAudio recording
│   └── transcriber.py # ElevenLabs API client
└── rivacore/          # Legacy core (being phased out)
```

## 🛠️ Development

### Requirements

- macOS 10.15+
- Python 3.8+
- PyQt6
- PyAudio
- ElevenLabs API key

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rivavoice --cov=pyscribetranscribe
```

### Building the App

```bash
# Build macOS app bundle
./build_app.sh

# Create DMG for distribution
./create_standalone.py
```

## 🤝 Contributing

We love contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [ElevenLabs](https://elevenlabs.io) for incredible speech recognition
- [PyQt6](https://pypi.org/project/PyQt6/) for the beautiful UI framework
- [PyAudio](https://pypi.org/project/PyAudio/) for reliable audio capture

---

<p align="center">
Built with ❤️ by <a href="https://github.com/borisdjordjevic">Boris Djordjevic</a> from <a href="https://www.199.company">199 Longevity</a>
<br>
<a href="https://www.199.company">199.company</a> | <a href="https://www.199bio.com">199bio.com</a>
</p>