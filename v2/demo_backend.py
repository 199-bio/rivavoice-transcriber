#!/usr/bin/env python3
"""
Non-interactive demo of RivaCore backend
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore import RivaBackend


def main():
    print("RivaCore Backend Demo")
    print("=" * 40)
    
    # Initialize backend
    backend = RivaBackend()
    
    # Check status
    status = backend.get_status()
    print(f"\nInitial status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Show available methods
    print("\nAvailable methods:")
    print("  - backend.set_api_key(key)")
    print("  - backend.set_hotkey(key)")
    print("  - backend.set_timeout_minutes(minutes)")
    print("  - backend.start_recording()")
    print("  - backend.stop_recording()")
    print("  - backend.get_status()")
    print("  - backend.get_last_error()")
    print("  - backend.capture_next_key()")
    
    # Check if directories exist
    config_dir = os.path.expanduser("~/.rivavoice")
    transcript_dir = os.path.expanduser("~/Documents/RivaTranscripts")
    
    print(f"\nConfig directory: {config_dir}")
    print(f"  Exists: {os.path.exists(config_dir)}")
    if os.path.exists(config_dir):
        files = os.listdir(config_dir)
        print(f"  Files: {files}")
    
    print(f"\nTranscript directory: {transcript_dir}")
    print(f"  Exists: {os.path.exists(transcript_dir)}")
    
    # Cleanup
    backend.cleanup()
    print("\nDemo complete.")


if __name__ == "__main__":
    main()