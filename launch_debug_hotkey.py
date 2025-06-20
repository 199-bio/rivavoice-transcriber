#!/usr/bin/env python3
"""
Launch debug hotkey capture in a new terminal
"""

import subprocess
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
debug_script = os.path.join(script_dir, "debug_hotkey.py")

applescript = f'''
tell application "Terminal"
    activate
    do script "cd {script_dir} && python {debug_script}"
end tell
'''

subprocess.run(['osascript', '-e', applescript])

print("Launched debug hotkey capture in a new Terminal window.")
print("Check what happens when you press a key...")