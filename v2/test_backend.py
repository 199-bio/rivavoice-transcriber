#!/usr/bin/env python3
"""
Simple test script for RivaCore backend
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore import RivaBackend


def main():
    print("RivaCore Backend Test")
    print("=" * 40)
    
    # Initialize backend (skip permission check to avoid crash)
    backend = RivaBackend(check_permissions=False)
    
    # Check status
    status = backend.get_status()
    print(f"Initial status: {status}")
    
    # Test API key setting
    if not status['api_key_set']:
        print("\nNo API key found. Please enter your ElevenLabs API key:")
        api_key = input("> ").strip()
        if api_key:
            backend.set_api_key(api_key)
            print("API key saved.")
        else:
            print("No API key provided. Transcription will not work.")
    
    # Show current hotkey if set
    if status['hotkey']:
        print(f"\nHotkey is set to: {status['hotkey']}")
    
    # Test recording
    print("\nCommands:")
    print("  r - start recording")
    print("  s - stop recording") 
    print("  h - set new hotkey")
    print("  p - toggle auto-paste")
    print("  b - toggle preserve clipboard")
    print("  c - toggle chunked mode")
    print("  status - show current status")
    print("  q - quit")
    
    while True:
        cmd = input("\n> ").lower().strip()
        
        if cmd == 'q':
            break
        elif cmd == 'r':
            if backend.start_recording():
                print("Recording started...")
            else:
                print(f"Failed to start: {backend.get_last_error()}")
        elif cmd == 's':
            print("Stopping and transcribing...")
            text = backend.stop_recording()
            if text:
                print(f"\nTranscribed text:\n{text}\n")
                print("(Text copied to clipboard)")
            else:
                print(f"Failed: {backend.get_last_error()}")
        elif cmd == 'h':
            print("\nPress any key to set as new hotkey (10 seconds):")
            key = backend.capture_next_key()
            if key:
                if backend.set_hotkey(key):
                    print(f"✓ Hotkey set to: {key}")
                else:
                    print(f"Failed to set hotkey: {backend.get_last_error()}")
            else:
                print("No key captured")
        elif cmd == 'p':
            current = backend.get_status()['auto_paste']
            new_state = not current
            backend.set_auto_paste(new_state)
            print(f"Auto-paste {'enabled' if new_state else 'disabled'}")
        elif cmd == 'b':
            current = backend.get_status()['preserve_clipboard']
            new_state = not current
            backend.set_preserve_clipboard(new_state)
            print(f"Preserve clipboard {'enabled' if new_state else 'disabled'}")
            if new_state:
                print("  Text will be typed directly without using clipboard")
            else:
                print("  Text will be copied to clipboard then pasted")
        elif cmd == 'c':
            current = backend.get_status()['chunked_mode']
            new_state = not current
            backend.set_chunked_mode(new_state)
            print(f"Chunked mode {'enabled' if new_state else 'disabled'}")
            if new_state:
                print("  Recording will now transcribe in chunks after 2 seconds of silence")
        elif cmd == 'status':
            status = backend.get_status()
            print(f"Status: {status}")
        else:
            print("Unknown command. Type 'h' for hotkey, 'p' for auto-paste, 'b' for preserve clipboard, 'c' for chunked mode, 'r' to record, 's' to stop, 'status' for info, or 'q' to quit")
    
    # Cleanup
    backend.cleanup()
    print("\nTest complete.")


if __name__ == "__main__":
    main()