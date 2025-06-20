#!/bin/bash
# Launch RivaVoice v2 in a new terminal window

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create a temporary script to run in the new terminal
cat > /tmp/rivavoice_launch.sh << EOF
#!/bin/bash
cd "$DIR"
echo "RivaVoice v2 Backend"
echo "===================="
echo ""
python3 rivavoice.py
echo ""
echo "Press any key to close this window..."
read -n 1
EOF

chmod +x /tmp/rivavoice_launch.sh

# Launch in new terminal based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell application "Terminal" to do script "/tmp/rivavoice_launch.sh"'
elif command -v gnome-terminal &> /dev/null; then
    # Linux with GNOME
    gnome-terminal -- /tmp/rivavoice_launch.sh
elif command -v xterm &> /dev/null; then
    # Linux with X11
    xterm -e /tmp/rivavoice_launch.sh
else
    # Fallback - just run it
    /tmp/rivavoice_launch.sh
fi