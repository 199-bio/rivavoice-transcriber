#!/bin/bash

# Script to create an ICNS file from a PNG

# Check if our source file exists
if [ ! -f "icon.png" ]; then
    echo "Error: icon.png file not found"
    exit 1
fi

# Create a temporary iconset directory
mkdir -p RivaVoice.iconset

# Generate icon files at different sizes
sips -z 16 16     icon.png --out RivaVoice.iconset/icon_16x16.png
sips -z 32 32     icon.png --out RivaVoice.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out RivaVoice.iconset/icon_32x32.png
sips -z 64 64     icon.png --out RivaVoice.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out RivaVoice.iconset/icon_128x128.png
sips -z 256 256   icon.png --out RivaVoice.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out RivaVoice.iconset/icon_256x256.png
sips -z 512 512   icon.png --out RivaVoice.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out RivaVoice.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out RivaVoice.iconset/icon_512x512@2x.png

# Create ICNS file from the iconset
iconutil -c icns RivaVoice.iconset

# Clean up
rm -rf RivaVoice.iconset

echo "Created RivaVoice.icns" 