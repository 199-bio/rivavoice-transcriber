# RivaVoice Menu Bar Mode

RivaVoice runs as a clean, minimal menu bar application using the RivaCore v2 backend.

## Running in Menu Bar Mode

### Option 1: Use the launcher script
```bash
./rivavoice-menubar.sh
```

### Option 2: Direct command
```bash
python menubar.py
```

### Option 3: Via main script with flag
```bash
python rivavoice.py --menubar
```

## Features Available in Menu Bar

When running in menu bar mode, you can access all controls from the system tray icon:

- **Status Indicator**: Shows if recording is active (🔴 Recording) or ready (● Ready)
- **Start/Stop Recording**: Click to toggle recording
- **Auto-paste Toggle**: Enable/disable automatic pasting after transcription
- **Chunked Mode Toggle**: Enable/disable chunked mode (UI only, not yet functional)
- **Show Window**: Opens the main application window if you need to access settings
- **Quit**: Exits the application

## Default Behavior

- The main window is hidden by default in menu bar mode
- Recording can be controlled via the menu or keyboard shortcuts (if configured)
- All settings are persisted between sessions
- The app will show a menu bar icon and be accessible from there

## Terminal vs Menu Bar Mode

- **Terminal Mode** (default): `python rivavoice.py`
  - Shows interactive terminal interface
  - Quick access with keyboard commands
  - Real-time status updates

- **Menu Bar Mode**: `python rivavoice.py --menubar`
  - No terminal or window
  - All controls in system menu bar
  - Cleaner desktop experience
  - Background operation