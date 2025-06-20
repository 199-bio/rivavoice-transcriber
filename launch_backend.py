#!/usr/bin/env python3
"""
Launch the RivaCore backend in a new terminal window
"""

import subprocess
import os
import sys

# Get the absolute path to the test script
script_dir = os.path.dirname(os.path.abspath(__file__))
test_script = os.path.join(script_dir, "test_backend.py")

# Create the command to run in the new terminal
# Using osascript to open a new Terminal window
applescript = f'''
tell application "Terminal"
    activate
    do script "cd {script_dir} && python {test_script}"
end tell
'''

# Execute the AppleScript
subprocess.run(['osascript', '-e', applescript])

print("Launched RivaCore backend in a new Terminal window.")
print("The interactive test interface should now be running.")
print("\nIn the new terminal window:")
print("- Enter your ElevenLabs API key when prompted")
print("- Press any key to set as hotkey")
print("- Use 'r' to start recording, 's' to stop, 'q' to quit")