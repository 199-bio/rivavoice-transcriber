"""
Core backend for RivaVoice v2 - Minimalist speech-to-text
"""

import os
import json
import logging
import logging.handlers
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .config import Config
from .audio import AudioRecorder
from .chunked_audio import ChunkedAudioRecorder
from .transcriber import Transcriber
from .hotkey import HotkeyManager
from .permissions import PermissionChecker
from .text_utils import deduplicate_transcripts, clean_transcript, ensure_space_before_text


class RivaBackend:
    """Minimalist backend for speech-to-text functionality"""
    
    def __init__(self, check_permissions=True):
        # Check required packages
        self._check_dependencies()
        
        self._config = Config()
        self._logger = self._setup_logging()
        
        # Initialize components first to avoid threading issues
        self._recorder = AudioRecorder(logger=self._logger)
        self._chunked_recorder = None  # Initialized on demand
        self._transcriber = Transcriber(logger=self._logger)
        self._hotkey = HotkeyManager(logger=self._logger)
        
        # Check permissions after initialization if requested
        if check_permissions:
            try:
                self._check_permissions()
            except Exception as e:
                self._logger.warning(f"Permission check failed: {e}")
        
        self._recording = False
        self._recording_lock = threading.Lock()
        self._recording_thread = None
        self._last_error = ""
        
        # Chunked mode state
        self._chunked_mode = self._config.get("chunked_mode", False)
        self._accumulated_transcript = ""
        self._chunk_count = 0
        
        # Clean old temp files
        self._cleanup_temp_files()
        
        # Load saved settings
        self._load_settings()
        
        self._logger.info("RivaBackend initialized")
    
    def _check_dependencies(self):
        """Check that required packages are available"""
        required = {
            'pyaudio': 'pyaudio',
            'requests': 'requests',
            'pyperclip': 'pyperclip',
            'pynput': 'pynput'
        }
        
        missing = []
        for module, package in required.items():
            try:
                __import__(module)
            except ImportError:
                missing.append(package)
        
        if missing:
            raise RuntimeError(f"Missing required packages: {', '.join(missing)}. Run: pip install {' '.join(missing)}")
    
    def _check_permissions(self):
        """Check required macOS permissions"""
        results = PermissionChecker.check_all_permissions()
        
        # Log permission status
        self._logger.info("Permission check results:")
        for perm, info in results.items():
            if perm != 'all_granted':
                self._logger.info(f"  {perm}: {'granted' if info['granted'] else 'denied'}")
        
        # Show warnings for missing permissions
        if not results['microphone']['granted']:
            print("\n⚠️  WARNING: Microphone access denied!")
            print("   Audio recording will not work.")
            print("   Grant permission in System Settings > Privacy & Security > Microphone\n")
        
        if not results['accessibility']['granted'] or not results['input_monitoring']['granted']:
            print("\n⚠️  WARNING: Keyboard access limited!")
            print("   Global hotkeys and auto-paste may not work.")
            print("   Grant Terminal permission in System Settings > Privacy & Security > Accessibility\n")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup debug logging"""
        log_dir = Path.home() / ".rivavoice"
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger("rivacore")
        logger.setLevel(logging.DEBUG)
        
        # Rotating file handler (max 10MB)
        handler = logging.handlers.RotatingFileHandler(
            log_dir / "debug.log",
            maxBytes=10*1024*1024,
            backupCount=1
        )
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(handler)
        
        return logger
    
    def _cleanup_temp_files(self):
        """Clean up old temporary WAV files on startup"""
        try:
            import tempfile
            import glob
            temp_dir = tempfile.gettempdir()
            # Find WAV files that look like our temp files
            pattern = os.path.join(temp_dir, "tmp*.wav")
            for file in glob.glob(pattern):
                try:
                    # Only delete if older than 1 hour
                    if time.time() - os.path.getmtime(file) > 3600:
                        os.remove(file)
                        self._logger.info(f"Cleaned up old temp file: {file}")
                except Exception:
                    pass
        except Exception as e:
            self._logger.warning(f"Temp file cleanup error: {e}")
    
    def _load_settings(self):
        """Load saved settings on startup"""
        # Register saved hotkey if exists
        saved_hotkey = self._config.get("hotkey")
        if saved_hotkey:
            self._hotkey.register(saved_hotkey, self._toggle_recording)
            self._logger.info(f"Loaded hotkey: {saved_hotkey}")
    
    def _toggle_recording(self):
        """Toggle recording on/off (called by hotkey)"""
        with self._recording_lock:
            is_recording = self._recording
        
        # Play audio feedback
        self._play_feedback()
        
        if is_recording:
            # Stop recording
            threading.Thread(target=self._stop_and_transcribe).start()
        else:
            # Start recording
            self.start_recording()
    
    def _play_feedback(self):
        """Play simple audio feedback beep"""
        try:
            # Use different sounds for start/stop
            if self._recording:
                # Stopping - lower tone
                os.system('afplay /System/Library/Sounds/Pop.aiff &')
            else:
                # Starting - higher tone
                os.system('afplay /System/Library/Sounds/Tink.aiff &')
        except Exception:
            # Continue silently if sound fails
            pass
    
    def _stop_and_transcribe(self):
        """Stop recording and transcribe in background"""
        text = self.stop_recording()
        if not text and self._last_error:
            self._logger.error(f"Transcription failed: {self._last_error}")
        
        # Auto-paste must happen in main thread for keyboard events
        # It's already handled in stop_recording()
    
    def start_recording(self) -> bool:
        """Start audio recording"""
        with self._recording_lock:
            if self._recording:
                self._last_error = "Already recording"
                return False
            self._recording = True
        
        api_key = self._config.get("api_key")
        if not api_key:
            self._last_error = "No API key configured"
            self._logger.error(self._last_error)
            with self._recording_lock:
                self._recording = False
            return False
        
        if self._chunked_mode:
            # Reset state for new chunked recording
            self._accumulated_transcript = ""
            self._chunk_count = 0
            self._logger.info("Starting chunked recording session")
            return self._start_chunked_recording()
        else:
            # Start regular recording
            self._recording_thread = threading.Thread(target=self._record_with_timeout)
            self._recording_thread.start()
        
        self._logger.info("Recording started")
        return True
    
    def _record_with_timeout(self):
        """Record with timeout handling"""
        timeout_minutes = self._config.get("timeout_minutes", 5)
        timeout_seconds = timeout_minutes * 60
        
        try:
            # Start recording
            audio_path = self._recorder.start_recording()
            
            # Wait for timeout or stop signal
            start_time = time.time()
            while True:
                with self._recording_lock:
                    if not self._recording:
                        break
                if (time.time() - start_time) >= timeout_seconds:
                    break
                time.sleep(0.1)
            
            # Stop recording if still active
            if self._recorder.is_recording():
                self._recorder.stop_recording()
                
        except Exception as e:
            self._last_error = str(e)
            self._logger.error(f"Recording error: {e}")
            with self._recording_lock:
                self._recording = False
    
    def stop_recording(self) -> str:
        """Stop recording and transcribe"""
        with self._recording_lock:
            if not self._recording:
                self._last_error = "Not recording"
                return ""
            self._recording = False
        
        if self._chunked_mode:
            # Stop chunked recording
            if self._chunked_recorder:
                self._chunked_recorder.stop_recording()
            
            # Give a moment for any final chunk processing to complete
            time.sleep(0.5)
            
            # Clear session timestamp for next recording
            if hasattr(self, '_session_timestamp'):
                delattr(self, '_session_timestamp')
            
            # Return accumulated transcript
            final_text = self._accumulated_transcript
            self._logger.info(f"Chunked recording complete: {self._chunk_count} chunks, {len(final_text)} chars total")
            
            # Reset for next recording
            self._accumulated_transcript = ""
            self._chunk_count = 0
            
            return final_text
        
        # Regular recording mode
        # Wait for recording thread to finish
        if self._recording_thread:
            self._recording_thread.join(timeout=1.0)
        
        # Get the audio file
        audio_path = self._recorder.get_last_recording()
        if not audio_path:
            self._last_error = "No audio recorded"
            self._logger.error(self._last_error)
            return ""
        
        # Transcribe
        api_key = self._config.get("api_key")
        text = self._transcriber.transcribe(audio_path, api_key)
        
        if text:
            # Save transcript
            self._save_transcript(text)
            
            # Copy to clipboard
            self._copy_to_clipboard(text)
            
            # Auto-paste if enabled
            if self._config.get("auto_paste", False):
                self._logger.info("Auto-paste is enabled, attempting paste...")
                time.sleep(0.5)  # Longer delay to ensure clipboard is ready
                
                # Check if we should preserve clipboard
                if self._config.get("preserve_clipboard", False):
                    self._direct_type_text(text)
                else:
                    self._paste_text()
            
            self._logger.info(f"Transcription complete: {len(text)} chars")
        else:
            self._last_error = self._transcriber.get_last_error()
        
        # Clean up audio file
        try:
            os.remove(audio_path)
        except:
            pass
        
        return text
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        with self._recording_lock:
            return self._recording
    
    def set_api_key(self, key: str) -> bool:
        """Set ElevenLabs API key"""
        self._config.set("api_key", key)
        self._config.save()
        self._logger.info("API key updated")
        return True
    
    def set_hotkey(self, key: str) -> bool:
        """Set global hotkey"""
        if self._hotkey.register(key, self._toggle_recording):
            self._config.set("hotkey", key)
            self._config.save()
            self._logger.info(f"Hotkey set to: {key}")
            return True
        else:
            self._last_error = "Failed to register hotkey"
            return False
    
    def capture_next_key(self) -> str:
        """Capture the next key press"""
        return self._hotkey.capture_next_key()
    
    def set_timeout_minutes(self, minutes: int) -> bool:
        """Set recording timeout in minutes"""
        if minutes < 1 or minutes > 60:
            self._last_error = "Timeout must be between 1 and 60 minutes"
            return False
        
        self._config.set("timeout_minutes", minutes)
        self._config.save()
        self._logger.info(f"Timeout set to: {minutes} minutes")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "recording": self._recording,
            "hotkey": self._config.get("hotkey", ""),
            "timeout_minutes": self._config.get("timeout_minutes", 5),
            "api_key_set": bool(self._config.get("api_key")),
            "auto_paste": self._config.get("auto_paste", False),
            "preserve_clipboard": self._config.get("preserve_clipboard", False),
            "chunked_mode": self._chunked_mode,
            "chunk_silence_duration": self._config.get("chunk_silence_duration", 2.5)
        }
    
    def set_auto_paste(self, enabled: bool) -> bool:
        """Enable or disable auto-paste after transcription"""
        self._config.set("auto_paste", enabled)
        self._config.save()
        self._logger.info(f"Auto-paste {'enabled' if enabled else 'disabled'}")
        return True
    
    def set_preserve_clipboard(self, enabled: bool) -> bool:
        """Enable or disable clipboard preservation (direct typing instead)"""
        self._config.set("preserve_clipboard", enabled)
        self._config.save()
        self._logger.info(f"Clipboard preservation {'enabled' if enabled else 'disabled'}")
        return True
    
    def get_last_error(self) -> str:
        """Get last error message"""
        return self._last_error
    
    def get_permission_status(self) -> Dict[str, Any]:
        """Get current permission status"""
        return PermissionChecker.check_all_permissions()
    
    def set_chunked_mode(self, enabled: bool, silence_duration: float = 2.5) -> bool:
        """Enable or disable chunked transcription mode"""
        self._chunked_mode = enabled
        self._config.set("chunked_mode", enabled)
        self._config.set("chunk_silence_duration", silence_duration)
        self._config.save()
        
        self._logger.info(f"Chunked mode {'enabled' if enabled else 'disabled'}")
        return True
    
    def _start_chunked_recording(self) -> bool:
        """Start recording in chunked mode"""
        # Always create new recorder to pick up config changes
        self._chunked_recorder = ChunkedAudioRecorder(
            silence_duration=self._config.get("chunk_silence_duration", 2.5),
            on_chunk_ready=self._process_audio_chunk,
            logger=self._logger
        )
        
        return self._chunked_recorder.start_recording()
    
    def _process_audio_chunk(self, audio_path: str):
        """Process a single audio chunk"""
        self._logger.info(f"Processing audio chunk: {audio_path}")
        try:
            # Check if file exists and has content
            import os
            if not os.path.exists(audio_path):
                self._logger.error(f"Audio chunk file not found: {audio_path}")
                return
            
            file_size = os.path.getsize(audio_path)
            self._logger.info(f"Chunk file size: {file_size} bytes")
            
            # Transcribe the chunk
            api_key = self._config.get("api_key")
            self._logger.info("Starting chunk transcription...")
            chunk_text = self._transcriber.transcribe(audio_path, api_key)
            
            if chunk_text:
                self._chunk_count += 1
                self._logger.info(f"Chunk {self._chunk_count} transcribed: {len(chunk_text)} chars")
                self._logger.debug(f"Chunk text: {chunk_text[:100]}...")
                
                # Deduplicate with previous transcript
                if self._accumulated_transcript:
                    merged_text = deduplicate_transcripts(
                        self._accumulated_transcript, 
                        chunk_text
                    )
                    # Extract only the new part
                    new_text = merged_text[len(self._accumulated_transcript):]
                    self._accumulated_transcript = merged_text
                else:
                    new_text = chunk_text
                    self._accumulated_transcript = chunk_text
                
                # Clean the new text
                new_text = clean_transcript(new_text)
                
                # Ensure proper spacing when adding to accumulated text
                if self._accumulated_transcript and new_text:
                    new_text = ensure_space_before_text(
                        self._accumulated_transcript, 
                        new_text
                    )
                
                if new_text.strip():
                    self._logger.info(f"New text to paste: {len(new_text)} chars")
                    
                    # Handle clipboard and auto-paste
                    if self._config.get("auto_paste", False):
                        if self._config.get("preserve_clipboard", False):
                            # Direct type without using clipboard
                            time.sleep(0.1)
                            self._direct_type_text(new_text)
                        else:
                            # Copy to clipboard and paste
                            self._copy_to_clipboard(new_text)
                            time.sleep(0.1)
                            self._paste_text()
                    else:
                        # Just copy to clipboard
                        self._copy_to_clipboard(new_text)
                    
                    # Save partial transcript
                    self._save_partial_transcript(new_text)
            else:
                self._logger.warning("No text returned from chunk transcription")
                error = self._transcriber.get_last_error()
                if error:
                    self._logger.error(f"Transcription error: {error}")
            
            # Clean up chunk file
            try:
                os.remove(audio_path)
                self._logger.debug(f"Removed chunk file: {audio_path}")
            except Exception as e:
                self._logger.warning(f"Failed to remove chunk file: {e}")
                
        except Exception as e:
            self._logger.error(f"Chunk processing error: {e}", exc_info=True)
    
    def _save_partial_transcript(self, text: str):
        """Save partial transcript to file"""
        transcript_dir = Path.home() / "Documents" / "RivaTranscripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        
        # Use session timestamp
        if not hasattr(self, '_session_timestamp'):
            self._session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        file_path = transcript_dir / f"{self._session_timestamp}_chunked.txt"
        
        # Append to file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(text + " ")
        
        self._logger.info(f"Partial transcript appended: {file_path}")
    
    def _save_transcript(self, text: str):
        """Save transcript to file"""
        transcript_dir = Path.home() / "Documents" / "RivaTranscripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = transcript_dir / f"{timestamp}.txt"
        
        file_path.write_text(text)
        self._logger.info(f"Transcript saved: {file_path}")
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        try:
            import pyperclip
            pyperclip.copy(text)
            self._logger.info("Text copied to clipboard")
        except Exception as e:
            self._logger.error(f"Clipboard error: {e}")
    
    def _paste_text(self):
        """Simulate paste action (Cmd+V)"""
        try:
            # Try AppleScript approach first (more reliable on macOS)
            import subprocess
            script = '''
            tell application "System Events"
                keystroke "v" using command down
            end tell
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            self._logger.info("Auto-paste triggered via AppleScript")
        except Exception as e:
            # Fallback to pynput
            try:
                from pynput.keyboard import Controller, Key
                keyboard = Controller()
                # Press and release Cmd+V
                keyboard.press(Key.cmd)
                keyboard.press('v')
                keyboard.release('v')
                keyboard.release(Key.cmd)
                self._logger.info("Auto-paste triggered via pynput")
            except Exception as e2:
                self._logger.error(f"Auto-paste error: {e}, {e2}")
    
    def _direct_type_text(self, text: str):
        """Type text directly without using clipboard"""
        try:
            # Use AppleScript to type text directly
            import subprocess
            # Escape special characters for AppleScript
            escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
            script = f'''
            tell application "System Events"
                keystroke "{escaped_text}"
            end tell
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            self._logger.info(f"Direct typed {len(text)} characters")
        except Exception as e:
            self._logger.error(f"Direct type error: {e}")
            # Fallback to clipboard method
            self._copy_to_clipboard(text)
            self._paste_text()
    
    def cleanup(self):
        """Cleanup resources on exit"""
        self._hotkey.stop()
        self._logger.info("Backend cleaned up")