#!/usr/bin/env python3
import subprocess
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
script = os.path.join(script_dir, "test_fn_key.py")

applescript = f'''
tell application "Terminal"
    activate
    do script "cd {script_dir} && python {script}"
end tell
'''

subprocess.run(['osascript', '-e', applescript])
print("Launched Fn key test in new terminal.")