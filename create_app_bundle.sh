#!/bin/bash

# Create macOS app bundle for RivaVoice

echo "Creating RivaVoice.app bundle..."

# Clean old app if exists
rm -rf dist/RivaVoice.app

# Create app bundle structure
mkdir -p dist/RivaVoice.app/Contents/MacOS
mkdir -p dist/RivaVoice.app/Contents/Resources

# Copy executable
cp dist/RivaVoice dist/RivaVoice.app/Contents/MacOS/

# Copy icon
cp RivaVoice.icns dist/RivaVoice.app/Contents/Resources/

# Create Info.plist
cat > dist/RivaVoice.app/Contents/Info.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleDisplayName</key>
    <string>RivaVoice</string>
    <key>CFBundleExecutable</key>
    <string>RivaVoice</string>
    <key>CFBundleIconFile</key>
    <string>RivaVoice</string>
    <key>CFBundleIdentifier</key>
    <string>com.199biotechnologies.rivavoice</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>RivaVoice</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0.0</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>RivaVoice needs access to your microphone to record speech for transcription.</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>RivaVoice needs access to simulate keystrokes for auto-paste functionality.</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ App bundle created at: dist/RivaVoice.app"
echo ""
echo "To test the app:"
echo "  open dist/RivaVoice.app"
echo ""
echo "To create a DMG:"
echo "  hdiutil create -volname RivaVoice -srcfolder dist/RivaVoice.app -ov -format UDZO RivaVoice-standalone.dmg"