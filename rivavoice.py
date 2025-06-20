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

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore import RivaBackend


class RivaVoiceTUI:
    """Terminal User Interface for RivaVoice"""
    
    def __init__(self):
        self.backend = RivaBackend(check_permissions=False)
        self.running = True
        self.message = ""
        self.message_time = None
        self.last_transcript = ""
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_header(self):
        """Display the header"""
        print("\033[1;36m" + "=" * 60 + "\033[0m")
        print("\033[1;36m" + "RivaVoice".center(60) + "\033[0m")
        print("\033[1;36m" + "Minimalist Speech-to-Text".center(60) + "\033[0m")
        print("\033[1;36m" + "=" * 60 + "\033[0m")
        print()
    
    def show_status(self):
        """Display current status"""
        status = self.backend.get_status()
        
        # Status indicators
        recording = "🔴 RECORDING" if status['recording'] else "⚪ Ready"
        api_status = "✅" if status['api_key_set'] else "❌"
        
        print("\033[1;33mStatus:\033[0m")
        print(f"  Recording: {recording}")
        print(f"  API Key: {api_status}")
        print(f"  Hotkey: \033[1;32m{status['hotkey'] or 'Not set'}\033[0m")
        print()
        
        print("\033[1;33mSettings:\033[0m")
        
        # Auto-paste
        paste_mode = "Direct Type" if status.get('preserve_clipboard', False) else "Clipboard"
        paste_status = f"✅ ({paste_mode})" if status['auto_paste'] else "❌"
        print(f"  Auto-paste: {paste_status}")
        
        # Chunked mode
        chunk_status = f"✅ ({status['chunk_silence_duration']}s silence)" if status['chunked_mode'] else "❌"
        print(f"  Chunked Mode: {chunk_status}")
        
        # Timeout
        print(f"  Timeout: {status['timeout_minutes']} minutes")
        print()
        
    def show_commands(self):
        """Display available commands"""
        print("\033[1;33mCommands:\033[0m")
        print("  \033[1;32m[R]\033[0m Start Recording    \033[1;32m[S]\033[0m Stop Recording")
        print("  \033[1;32m[P]\033[0m Toggle Auto-paste  \033[1;32m[B]\033[0m Toggle Preserve Clipboard")
        print("  \033[1;32m[C]\033[0m Toggle Chunked     \033[1;32m[H]\033[0m Set Hotkey")
        print("  \033[1;32m[T]\033[0m Set Timeout        \033[1;32m[Q]\033[0m Quit")
        print()
    
    def show_message(self):
        """Display temporary message"""
        if self.message and self.message_time:
            elapsed = time.time() - self.message_time
            if elapsed < 3:  # Show message for 3 seconds
                print("\033[1;35m" + "-" * 60 + "\033[0m")
                print(f"\033[1;35m{self.message}\033[0m")
                print("\033[1;35m" + "-" * 60 + "\033[0m")
                print()
            else:
                self.message = ""
                self.message_time = None
    
    def show_transcript(self):
        """Display last transcript"""
        if self.last_transcript:
            print("\033[1;33mLast Transcript:\033[0m")
            # Wrap text at 58 characters
            words = self.last_transcript.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 > 58:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    current_line.append(word)
                    current_length += len(word) + 1
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines[:5]:  # Show max 5 lines
                print(f"  {line}")
            
            if len(lines) > 5:
                print(f"  ... ({len(self.last_transcript)} chars total)")
            print()
    
    def set_message(self, msg):
        """Set a temporary message"""
        self.message = msg
        self.message_time = time.time()
    
    def refresh_display(self):
        """Refresh the entire display"""
        self.clear_screen()
        self.show_header()
        self.show_status()
        self.show_message()
        self.show_transcript()
        self.show_commands()
        print("\n\033[1;36m>\033[0m ", end='', flush=True)
    
    def handle_recording(self):
        """Handle recording toggle"""
        status = self.backend.get_status()
        
        if status['recording']:
            # Stop recording
            self.set_message("Stopping recording...")
            self.refresh_display()
            
            text = self.backend.stop_recording()
            if text:
                self.last_transcript = text
                self.set_message(f"Transcribed {len(text)} characters")
            else:
                error = self.backend.get_last_error()
                self.set_message(f"Error: {error}")
        else:
            # Start recording
            if self.backend.start_recording():
                if status['chunked_mode']:
                    self.set_message("Recording started (chunked mode - speak, then pause)")
                else:
                    self.set_message("Recording started...")
            else:
                error = self.backend.get_last_error()
                self.set_message(f"Failed to start: {error}")
    
    def handle_hotkey(self):
        """Handle hotkey setting"""
        self.clear_screen()
        self.show_header()
        print("\033[1;33mSet Hotkey\033[0m")
        print("Press any key to use as hotkey (ESC to cancel):")
        print()
        
        key = self.backend.capture_next_key()
        if key and key != 'esc':
            if self.backend.set_hotkey(key):
                self.set_message(f"Hotkey set to: {key}")
            else:
                self.set_message("Failed to set hotkey")
        else:
            self.set_message("Hotkey change cancelled")
    
    def handle_timeout(self):
        """Handle timeout setting"""
        self.clear_screen()
        self.show_header()
        print("\033[1;33mSet Recording Timeout\033[0m")
        print("Enter timeout in minutes (1-60):")
        print()
        
        try:
            minutes = input("> ").strip()
            if minutes.isdigit():
                minutes = int(minutes)
                if self.backend.set_timeout_minutes(minutes):
                    self.set_message(f"Timeout set to {minutes} minutes")
                else:
                    self.set_message("Invalid timeout value")
            else:
                self.set_message("Invalid input")
        except:
            self.set_message("Timeout change cancelled")
    
    def run(self):
        """Run the TUI"""
        # Initial display
        self.refresh_display()
        
        while self.running:
            try:
                # Get input (non-blocking would be better but complex)
                cmd = input().lower().strip()
                
                if cmd == 'q':
                    self.running = False
                    break
                elif cmd == 'r':
                    self.handle_recording()
                elif cmd == 's':
                    if self.backend.get_status()['recording']:
                        self.handle_recording()
                    else:
                        self.set_message("Not recording")
                elif cmd == 'p':
                    current = self.backend.get_status()['auto_paste']
                    self.backend.set_auto_paste(not current)
                    self.set_message(f"Auto-paste {'enabled' if not current else 'disabled'}")
                elif cmd == 'b':
                    current = self.backend.get_status()['preserve_clipboard']
                    self.backend.set_preserve_clipboard(not current)
                    mode = "direct typing" if not current else "clipboard"
                    self.set_message(f"Switched to {mode} mode")
                elif cmd == 'c':
                    current = self.backend.get_status()['chunked_mode']
                    self.backend.set_chunked_mode(not current)
                    self.set_message(f"Chunked mode {'enabled' if not current else 'disabled'}")
                elif cmd == 'h':
                    self.handle_hotkey()
                elif cmd == 't':
                    self.handle_timeout()
                else:
                    self.set_message("Invalid command")
                
                # Refresh display
                self.refresh_display()
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                self.set_message(f"Error: {str(e)}")
                self.refresh_display()
        
        # Cleanup
        self.clear_screen()
        print("\033[1;36mRivaVoice stopped. Goodbye!\033[0m")
        self.backend.cleanup()


def main():
    """Main entry point"""
    try:
        app = RivaVoiceTUI()
        app.run()
    except Exception as e:
        print(f"\n\033[1;31mError: {e}\033[0m")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())