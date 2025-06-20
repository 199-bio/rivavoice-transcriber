#!/usr/bin/env python3
"""
Debug version of hotkey capture
"""

import sys
import os
import time
from pynput import keyboard

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def on_press(key):
    """Handle key press with debug output"""
    print(f"\nKey pressed: {key}")
    
    try:
        if hasattr(key, 'char'):
            key_str = key.char
            print(f"Character key: '{key_str}'")
        else:
            key_str = str(key).replace('Key.', '')
            print(f"Special key: '{key_str}'")
        
        return False  # Stop listener after first key
    except Exception as e:
        print(f"Error processing key: {e}")
        return False


def main():
    print("Debug Hotkey Capture")
    print("=" * 40)
    print("Press any key...")
    
    # Create listener
    listener = keyboard.Listener(on_press=on_press)
    
    # Start listening
    listener.start()
    
    # Wait for key (with timeout)
    start_time = time.time()
    while listener.running and (time.time() - start_time) < 10:
        time.sleep(0.1)
    
    if listener.running:
        print("\nTimeout - no key detected")
        listener.stop()
    else:
        print("\nKey capture complete!")


if __name__ == "__main__":
    main()