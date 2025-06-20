#!/usr/bin/env python3
"""
Test script to debug crash
"""

import sys
import os
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importing RivaBackend...")
    from rivacore import RivaBackend
    
    print("Creating backend instance...")
    backend = RivaBackend()
    
    print("Backend created successfully!")
    print(f"Status: {backend.get_status()}")
    
    backend.cleanup()
    print("Cleanup complete")
    
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()