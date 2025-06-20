#!/usr/bin/env python3

"""
Bootstrap script for RivaVoice application
"""

import os
import sys

# Make sure the rivavoice package is in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the main function from rivavoice module
from rivavoice.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
