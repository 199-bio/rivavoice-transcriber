#!/bin/bash

# Build script for RivaVoice macOS app

echo "RivaVoice macOS App Builder"
echo "=========================="

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script is for macOS only"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "build_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv build_env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source build_env/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install py2app

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the app
echo "Building macOS app..."
python setup.py py2app

# Check if build was successful
if [ -d "dist/RivaVoice.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "The app is located at: dist/RivaVoice.app"
    echo ""
    echo "To run the app:"
    echo "  open dist/RivaVoice.app"
    echo ""
    echo "To distribute the app:"
    echo "  1. Copy dist/RivaVoice.app to another Mac"
    echo "  2. The user may need to right-click and select 'Open' the first time"
    echo "  3. They may need to allow microphone access in System Preferences"
    echo ""
    echo "To create a DMG for distribution:"
    echo "  hdiutil create -volname RivaVoice -srcfolder dist/RivaVoice.app -ov -format UDZO RivaVoice.dmg"
else
    echo ""
    echo "❌ Build failed!"
    echo "Check the error messages above for details."
    exit 1
fi

# Deactivate virtual environment
deactivate