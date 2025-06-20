#!/usr/bin/env python3
"""
Fixed hotkey setter that properly handles existing listeners
"""

import sys
import os
import time
import threading
from pynput import keyboard

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore import RivaBackend


class HotkeyCapture:
    def __init__(self):
        self.captured_key = None
        self.capture_event = threading.Event()
    
    def on_press(self, key):
        """Handle key press"""
        try:
            if hasattr(key, 'char'):
                self.captured_key = key.char
            else:
                self.captured_key = str(key).replace('Key.', '')
            
            print(f"\nCaptured: {self.captured_key}")
            self.capture_event.set()
            return False  # Stop listener
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def capture(self):
        """Capture next key press"""
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()
        
        # Wait for key or timeout
        if self.capture_event.wait(timeout=10):
            return self.captured_key
        else:
            listener.stop()
            return None


def main():
    print("RivaCore Hotkey Setup (Fixed)")
    print("=" * 40)
    
    # Initialize backend
    backend = RivaBackend()
    
    # Show current status
    status = backend.get_status()
    current_hotkey = status.get('hotkey', '')
    
    if current_hotkey:
        print(f"Current hotkey: {current_hotkey}")
    else:
        print("No hotkey currently set")
    
    print("\nPress any key to set as the new hotkey...")
    print("(You have 10 seconds)")
    
    # Use our own capture instead of backend's
    capture = HotkeyCapture()
    captured_key = capture.capture()
    
    if captured_key:
        print(f"\nSetting hotkey to: {captured_key}")
        
        # Now set it using the backend
        if backend.set_hotkey(captured_key):
            print(f"✓ Hotkey successfully set to: {captured_key}")
            print("\nYou can now use this key to toggle recording on/off")
        else:
            print(f"✗ Failed to set hotkey: {backend.get_last_error()}")
    else:
        print("\nNo key captured (timeout)")
    
    # Cleanup
    backend.cleanup()
    print("\nDone!")


if __name__ == "__main__":
    main()