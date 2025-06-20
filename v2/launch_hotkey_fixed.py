#!/usr/bin/env python3
"""
Launch fixed hotkey setter in a new terminal
"""

import subprocess
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
script = os.path.join(script_dir, "set_hotkey_fixed.py")

applescript = f'''
tell application "Terminal"
    activate
    do script "cd {script_dir} && python {script}"
end tell
'''

subprocess.run(['osascript', '-e', applescript])

print("Launched fixed hotkey setter in a new Terminal window.")