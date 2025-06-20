#!/usr/bin/env python3
"""
Launch the hotkey setter in a new terminal window
"""

import subprocess
import os

# Get the absolute path to the set_hotkey script
script_dir = os.path.dirname(os.path.abspath(__file__))
set_hotkey_script = os.path.join(script_dir, "set_hotkey.py")

# Create the command to run in the new terminal
applescript = f'''
tell application "Terminal"
    activate
    do script "cd {script_dir} && python {set_hotkey_script}"
end tell
'''

# Execute the AppleScript
subprocess.run(['osascript', '-e', applescript])

print("Launched hotkey setter in a new Terminal window.")
print("\nIn the new window:")
print("- Press any key within 10 seconds to set it as the hotkey")
print("- The key will be saved and used for toggling recording")