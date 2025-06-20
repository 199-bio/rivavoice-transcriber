"""
Simple audio recording functionality
"""

import os
import wave
import tempfile
import threading
from typing import Optional
import pyaudio


class AudioRecorder:
    """Minimal audio recorder using PyAudio"""
    
    def __init__(self, logger=None):
        self._logger = logger
        self._recording = False
        self._frames = []
        self._thread = None
        self._current_file = None
        
        # Audio settings
        self._format = pyaudio.paInt16
        self._channels = 1
        self._rate = 16000
        self._chunk = 1024
        
        try:
            self._audio = pyaudio.PyAudio()
        except Exception as e:
            if logger:
                logger.error(f"Failed to initialize audio: {e}")
            self._audio = None
    
    def start_recording(self) -> str:
        """Start recording audio to a temporary file"""
        if self._recording:
            raise RuntimeError("Already recording")
        
        if not self._audio:
            raise RuntimeError("Audio system not available")
        
        # Create temporary file
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        self._current_file = path
        
        self._recording = True
        self._frames = []
        
        # Start recording in thread
        self._thread = threading.Thread(target=self._record)
        self._thread.start()
        
        if self._logger:
            self._logger.info(f"Recording started: {path}")
        
        return path
    
    def _record(self):
        """Record audio in background thread"""
        try:
            stream = self._audio.open(
                format=self._format,
                channels=self._channels,
                rate=self._rate,
                input=True,
                frames_per_buffer=self._chunk
            )
            
            while self._recording:
                data = stream.read(self._chunk, exception_on_overflow=False)
                self._frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Save to file
            self._save_audio()
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Recording error: {e}")
            self._recording = False
    
    def stop_recording(self):
        """Stop recording"""
        if not self._recording:
            return
        
        self._recording = False
        
        # Wait for thread to finish
        if self._thread:
            self._thread.join(timeout=1.0)
        
        if self._logger:
            self._logger.info("Recording stopped")
    
    def _save_audio(self):
        """Save recorded audio to WAV file"""
        if not self._current_file or not self._frames:
            return
        
        with wave.open(self._current_file, 'wb') as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(self._audio.get_sample_size(self._format))
            wf.setframerate(self._rate)
            wf.writeframes(b''.join(self._frames))
        
        if self._logger:
            self._logger.info(f"Audio saved: {self._current_file}")
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._recording
    
    def get_last_recording(self) -> Optional[str]:
        """Get path to last recording"""
        return self._current_file
    
    def __del__(self):
        """Cleanup PyAudio"""
        if hasattr(self, '_audio') and self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass