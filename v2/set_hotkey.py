#!/usr/bin/env python3
"""
Interactive hotkey setter for RivaCore
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore import RivaBackend


def main():
    print("RivaCore Hotkey Setup")
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
    
    # Capture the next key press
    captured_key = backend.capture_next_key()
    
    if captured_key:
        print(f"\nCaptured key: {captured_key}")
        
        # Set it as the new hotkey
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