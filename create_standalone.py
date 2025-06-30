#!/usr/bin/env python3
"""
Create a standalone executable using PyInstaller
"""
import subprocess
import os
import sys

def main():
    print("Creating standalone RivaVoice executable...")
    
    # Check if we're in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Please run this script from within the virtual environment")
        print("Run: source build_env/bin/activate")
        return 1
    
    # Install PyInstaller
    print("Installing PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Create the executable
    print("Building executable...")
    cmd = [
        "pyinstaller",
        "--name", "RivaVoice",
        "--onefile",
        "--console",  # Terminal app
        "--icon", "RivaVoice.icns",
        "--osx-bundle-identifier", "com.199biotechnologies.rivavoice",
        "--add-data", "rivacore:rivacore",
        "--hidden-import", "rivacore",
        "--hidden-import", "rivacore.audio",
        "--hidden-import", "rivacore.backend",
        "--hidden-import", "rivacore.chunked_audio",
        "--hidden-import", "rivacore.config",
        "--hidden-import", "rivacore.hotkey",
        "--hidden-import", "rivacore.permissions",
        "--hidden-import", "rivacore.text_utils",
        "--hidden-import", "rivacore.transcriber",
        "--hidden-import", "pyaudio",
        "--hidden-import", "pynput",
        "--hidden-import", "pynput.keyboard",
        "--hidden-import", "pynput.mouse",
        "--hidden-import", "pynput._util",
        "--hidden-import", "pynput._util.darwin",
        "--clean",
        "rivavoice.py"
    ]
    
    subprocess.run(cmd, check=True)
    
    print("\n✅ Build complete!")
    print("The executable is located at: dist/RivaVoice")
    print("\nTo run: ./dist/RivaVoice")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())