#!/usr/bin/env python3
"""
RivaVoice - Minimalist Speech-to-Text
Terminal User Interface
"""

import sys
import os
import time
import threading
from datetime import datetime
import termios
import tty
import select

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore import RivaBackend


class RivaVoiceTUI:
    """Terminal User Interface for RivaVoice"""
    
    def __init__(self):
        self.backend = RivaBackend(check_permissions=False)
        self.running = True
        self.last_transcript = ""
        self.old_settings = None
        self.recording_animation_frame = 0
        self.status_color = "\033[0m"  # Normal color
        self.last_action = None
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def move_cursor_to_top(self):
        """Move cursor to top of screen"""
        print('\033[H', end='', flush=True)
    
    def get_single_keypress(self, timeout=0.1):
        """Get a single keypress without waiting for Enter"""
        if os.name == 'posix':
            # Unix/Linux/macOS
            if self.old_settings is None:
                self.old_settings = termios.tcgetattr(sys.stdin)
            
            try:
                # Set terminal to raw mode
                tty.setraw(sys.stdin.fileno())
                
                # Check if input is available
                if select.select([sys.stdin], [], [], timeout)[0]:
                    key = sys.stdin.read(1)
                    
                    # Handle special keys
                    if ord(key) == 27:  # ESC sequence
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key += sys.stdin.read(2)
                            # Arrow keys, etc.
                        else:
                            return 'esc'
                    elif ord(key) == 3:  # Ctrl+C
                        raise KeyboardInterrupt
                    elif ord(key) == 13:  # Enter
                        return 'enter'
                    elif ord(key) == 127:  # Backspace
                        return 'backspace'
                    else:
                        return key.lower()
                else:
                    return None
            finally:
                # Restore terminal settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        else:
            # Windows
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if isinstance(key, bytes):
                    key = key.decode('utf-8', errors='ignore')
                return key.lower()
            return None
    
    def show_header(self):
        """Display the header - clean and simple"""
        print("\033[1;36m" + "RivaVoice".center(60) + "\033[0m")
        print()
    
    def show_status(self):
        """Display current status - clean without messages"""
        status = self.backend.get_status()
        
        # Status line with recording indicator
        if status['recording']:
            frames = ["🔴", "⚫"]
            indicator = frames[self.recording_animation_frame % len(frames)]
            self.recording_animation_frame += 1
            print(f"  Status: {indicator} Recording")
        else:
            print("  Status: ⚪ Ready")
            self.recording_animation_frame = 0
        
        # Settings line - compact
        paste = "ON" if status['auto_paste'] else "OFF"
        
        print(f"  Auto-paste: {paste}")
        print()
        
    def show_transcript(self):
        """Display last transcript - clean"""
        if self.last_transcript:
            print("  Last transcript:")
            # Show first 2 lines worth of text
            text = self.last_transcript[:100]
            if len(self.last_transcript) > 100:
                text += "..."
            
            # Wrap at 56 chars
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 > 56:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    current_line.append(word)
                    current_length += len(word) + 1
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines[:2]:  # Max 2 lines
                print(f"  \033[90m{line}\033[0m")
            print()
        
    def show_commands(self):
        """Display available commands - clean"""
        print("  Commands:")
        print("  [R] Record   [P] Auto-paste   [Q] Quit")
        print()
    
    def set_message(self, msg):
        """Set a temporary message - deprecated"""
        # No longer used for minimalism
        pass
    
    def refresh_display(self, full_clear=False):
        """Refresh the entire display"""
        if full_clear:
            self.clear_screen()
        else:
            # Move cursor to home position and clear from cursor down
            print('\033[H\033[J', end='', flush=True)
        
        self.show_header()
        self.show_status()
        self.show_transcript()
        self.show_commands()
        
        # Hide cursor for cleaner look
        print('\033[?25l', end='', flush=True)
    
    def handle_recording(self):
        """Handle recording toggle"""
        status = self.backend.get_status()
        
        if status['recording']:
            # Stop recording
            text = self.backend.stop_recording()
            if text:
                self.last_transcript = text
        else:
            # Start recording
            self.backend.start_recording()
    
    
    def run(self):
        """Run the TUI"""
        # Initial display with full clear
        self.refresh_display(full_clear=True)
        last_refresh = time.time()
        
        while self.running:
            try:
                # Check for keypress (non-blocking)
                key = self.get_single_keypress()
                
                # Refresh periodically to update status (recording indicator)
                current_time = time.time()
                if current_time - last_refresh > 0.5:  # Refresh every 0.5 seconds for smoother updates
                    if self.backend.get_status()['recording']:
                        self.refresh_display()
                        last_refresh = current_time
                
                # Process keypress if any
                if key:
                    if key == 'q':
                        self.running = False
                        break
                    elif key == 'r':
                        self.handle_recording()
                        self.refresh_display()
                    elif key == 's':
                        if self.backend.get_status()['recording']:
                            self.handle_recording()
                        else:
                            self.set_message("Not recording")
                        self.refresh_display()
                    elif key == 'p':
                        current = self.backend.get_status()['auto_paste']
                        self.backend.set_auto_paste(not current)
                        self.refresh_display()
                    # Removed other commands for minimalism
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.05)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                self.set_message(f"Error: {str(e)}")
                self.refresh_display()
        
        # Cleanup
        if self.old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        
        # Show cursor again and clear screen
        print('\033[?25h', end='', flush=True)  # Show cursor
        self.clear_screen()
        print("\033[1;36mRivaVoice stopped. Goodbye!\033[0m")
        self.backend.cleanup()


def main():
    """Main entry point"""
    # Check for menu bar mode
    if len(sys.argv) > 1 and sys.argv[1] == "--menubar":
        # Import and run the clean menu bar app
        from menubar import main as menubar_main
        return menubar_main()
    
    # Otherwise run terminal UI
    try:
        app = RivaVoiceTUI()
        app.run()
    except Exception as e:
        print(f"\n\033[1;31mError: {e}\033[0m")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())