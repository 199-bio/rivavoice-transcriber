# RivaVoice Build and Distribution Instructions

## Building the macOS App

### Prerequisites
- macOS 10.15 or later
- Python 3.8 or later
- Command Line Tools for Xcode

## Method 1: PyInstaller (Recommended)

### Quick Build
```bash
# Create virtual environment
python3 -m venv build_env
source build_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the PyInstaller build script
python create_standalone.py

# Create app bundle
./create_app_bundle.sh
```

This creates a fully standalone executable that includes Python and all dependencies.

## Method 2: py2app (Alternative)

### Quick Build
```bash
# Run the build script
./build_app.sh
```

**Note**: py2app builds may have dependency issues. Use PyInstaller method if you encounter problems.

## Distribution

### Option 1: Direct App Distribution
1. Locate the app: `dist/RivaVoice.app`
2. Compress it: Right-click → "Compress"
3. Share the resulting `RivaVoice.app.zip`

### Option 2: Create a DMG Installer
```bash
# For PyInstaller build
hdiutil create -volname RivaVoice -srcfolder dist/RivaVoice.app -ov -format UDZO RivaVoice-standalone.dmg

# For py2app build
hdiutil create -volname RivaVoice -srcfolder dist/RivaVoice.app -ov -format UDZO RivaVoice.dmg
```

## Installation Instructions for End Users

### Installing RivaVoice

1. **Download and Extract**
   - If you received a `.zip` file, double-click to extract
   - If you received a `.dmg` file, double-click to mount

2. **Install the App**
   - Drag `RivaVoice.app` to your Applications folder
   - Or run it directly from wherever you extracted it

3. **First Launch**
   - Right-click on `RivaVoice.app` and select "Open"
   - Click "Open" when macOS warns about an unidentified developer
   - This is only needed for the first launch

### Required Permissions

RivaVoice needs these permissions to work:
- **Microphone Access**: For recording speech
- **Accessibility Access**: For global hotkeys and auto-paste

When prompted, grant these permissions in System Preferences.

### Configuration

1. **API Key**: You'll need an ElevenLabs API key
   - Get one at: https://elevenlabs.io
   - The app will prompt you to enter it on first run

2. **Settings**: Configure in the terminal interface
   - Hotkey: Default is F1
   - Auto-paste: Enabled by default
   - Chunked mode: For continuous transcription

## Troubleshooting

### "App is damaged" Error
```bash
# Remove quarantine attribute
xattr -cr /Applications/RivaVoice.app
```

### Microphone Not Working
1. Open System Preferences → Privacy & Security → Microphone
2. Ensure RivaVoice is checked

### Hotkeys Not Working
1. Open System Preferences → Privacy & Security → Accessibility
2. Add and check RivaVoice

### App Won't Launch
- Ensure you have macOS 10.15 or later
- Try running from Terminal: `open /Applications/RivaVoice.app`

## System Requirements

- **macOS**: 10.15 (Catalina) or later
- **Architecture**: Intel or Apple Silicon
- **Memory**: 100MB free RAM
- **Storage**: 50MB free disk space
- **Network**: Internet connection for transcription

## What's Included

The app bundle includes:
- All Python dependencies
- Audio recording libraries
- Hotkey management
- Clipboard integration
- No additional installation required!

## Notes

- The app runs in Terminal mode (text-based interface)
- All settings are stored in `~/.rivavoice/config.json`
- Recordings are temporarily stored and deleted after transcription
- No data is stored or transmitted except to ElevenLabs for transcription