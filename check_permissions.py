#!/usr/bin/env python3
"""
Check required permissions for RivaCore
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore.permissions import PermissionChecker


def main():
    print("RivaCore Permission Checker")
    print("=" * 50)
    print("\nThis tool checks if your system has granted the necessary")
    print("permissions for RivaCore to function properly.\n")
    
    # Check and display permissions
    PermissionChecker.print_permission_status()
    
    # Additional guidance
    print("\nNotes:")
    print("- Microphone: Required for audio recording")
    print("- Accessibility: Required for global hotkeys and auto-paste")
    print("- Input Monitoring: Required for keyboard detection")
    print("\nIf any permissions are missing, the app will still run")
    print("but some features may not work correctly.")


if __name__ == "__main__":
    main()