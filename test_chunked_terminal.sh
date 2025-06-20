#!/bin/bash
# Test chunked recording in new terminal

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

osascript -e "tell application \"Terminal\" to do script \"cd '$DIR' && python3 test_chunked.py\""