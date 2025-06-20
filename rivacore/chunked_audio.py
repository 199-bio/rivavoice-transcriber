"""
Chunked audio recording with Voice Activity Detection (VAD)
"""

import os
import wave
import threading
import time
import tempfile
import numpy as np
from typing import Optional, Callable, List
import pyaudio


class ChunkedAudioRecorder:
    """Audio recorder with VAD and automatic chunking"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 silence_threshold: float = 0.02,  # Default threshold (will be calibrated)
                 silence_duration: float = 2.5,  # Wait 2.5 seconds after silence detected
                 overlap_duration: float = 0.2,
                 on_chunk_ready: Optional[Callable[[str], None]] = None,
                 logger=None):
        """
        Initialize chunked audio recorder
        
        Args:
            sample_rate: Audio sample rate (Hz)
            channels: Number of audio channels
            chunk_size: Size of audio chunks to read
            silence_threshold: RMS threshold for silence detection
            silence_duration: Seconds of silence before chunking
            overlap_duration: Seconds of overlap between chunks
            on_chunk_ready: Callback when audio chunk is ready
            logger: Optional logger instance
        """
        self._sample_rate = sample_rate
        self._channels = channels
        self._chunk_size = chunk_size
        self._silence_threshold = silence_threshold
        self._silence_duration = silence_duration
        self._overlap_duration = overlap_duration
        self._on_chunk_ready = on_chunk_ready
        self._logger = logger
        
        # Audio state
        self._audio = None
        self._stream = None
        self._recording = False
        self._recording_thread = None
        
        # Buffers
        self._audio_buffer = []
        self._overlap_buffer = []
        self._silence_start_time = None
        self._is_speaking = False
        self._speech_buffer = []  # Buffer only speech segments
        self._pre_roll_buffer = []  # Keep last N chunks before voice detection
        self._pre_roll_size = 5  # Keep 5 chunks (~320ms) of pre-roll
        
        # Adaptive threshold
        self._noise_floor = 0.01
        self._rms_history = []
        self._calibrating = True
        self._calibration_samples = 50  # Calibrate for first ~3 seconds
        
        # Thread safety
        self._lock = threading.Lock()
        
    def start_recording(self) -> bool:
        """Start continuous recording with VAD"""
        with self._lock:
            if self._recording:
                return False
            
            try:
                self._audio = pyaudio.PyAudio()
                self._stream = self._audio.open(
                    format=pyaudio.paInt16,
                    channels=self._channels,
                    rate=self._sample_rate,
                    input=True,
                    frames_per_buffer=self._chunk_size
                )
                
                self._recording = True
                self._audio_buffer = []
                self._overlap_buffer = []
                self._speech_buffer = []
                self._pre_roll_buffer = []
                self._silence_start_time = None
                self._is_speaking = False
                self._calibrating = True
                self._rms_history = []
                
                # Start recording thread
                self._recording_thread = threading.Thread(
                    target=self._record_with_vad,
                    daemon=True
                )
                self._recording_thread.start()
                
                if self._logger:
                    self._logger.info(f"Chunked recording started (silence duration: {self._silence_duration}s)")
                
                return True
                
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to start recording: {e}")
                self._cleanup_stream()
                return False
    
    def stop_recording(self):
        """Stop recording and process any remaining audio"""
        with self._lock:
            if not self._recording:
                return
            
            self._recording = False
        
        # Wait for thread to finish
        if self._recording_thread:
            self._recording_thread.join(timeout=1.0)
        
        # Process any remaining audio
        if self._audio_buffer:
            self._process_chunk()
        
        self._cleanup_stream()
        
        if self._logger:
            self._logger.info("Chunked recording stopped")
    
    def _record_with_vad(self):
        """Recording thread with Voice Activity Detection"""
        if self._logger:
            self._logger.info("VAD recording started, calibrating noise floor...")
        
        while self._recording:
            try:
                # Read audio data
                data = self._stream.read(self._chunk_size, exception_on_overflow=False)
                
                # Convert to numpy array for analysis
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Calculate RMS (Root Mean Square) for volume level
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)) / 32768.0
                
                # Calibration phase - learn background noise level
                if self._calibrating:
                    self._rms_history.append(rms)
                    if len(self._rms_history) >= self._calibration_samples:
                        # Remove any zero values (might be from initialization)
                        non_zero_rms = [r for r in self._rms_history if r > 0.0001]
                        if non_zero_rms:
                            # Calculate noise floor as median of non-zero RMS values
                            sorted_rms = sorted(non_zero_rms)
                            self._noise_floor = sorted_rms[len(sorted_rms) // 2]
                        else:
                            # If all zeros, use a small default
                            self._noise_floor = 0.001
                        
                        # For low noise environments, ensure minimum practical threshold
                        # If noise floor is very low (< 0.005), use fixed minimum
                        if self._noise_floor < 0.005:
                            self._silence_threshold = 0.015  # Fixed threshold for quiet environments
                            if self._logger:
                                self._logger.info(f"Low noise environment detected, using fixed threshold")
                        else:
                            # Set threshold to 2.5x noise floor with reasonable bounds
                            self._silence_threshold = min(max(self._noise_floor * 2.5, 0.012), 0.04)
                        self._calibrating = False
                        if self._logger:
                            self._logger.info(f"Calibration complete. Noise floor: {self._noise_floor:.4f}, "
                                            f"Silence threshold: {self._silence_threshold:.4f}")
                    continue  # Don't process audio during calibration
                
                # Always store in main buffer for overlap purposes
                self._audio_buffer.append(data)
                
                # Maintain pre-roll buffer (circular buffer of last N chunks)
                self._pre_roll_buffer.append(data)
                if len(self._pre_roll_buffer) > self._pre_roll_size:
                    self._pre_roll_buffer.pop(0)
                
                # Voice Activity Detection with adaptive threshold
                is_voice = rms > self._silence_threshold
                
                # Store speech segments separately
                if is_voice:
                    self._speech_buffer.append(data)
                
                # Log RMS values periodically for debugging
                if hasattr(self, '_log_counter'):
                    self._log_counter += 1
                else:
                    self._log_counter = 0
                
                if self._log_counter % 10 == 0:  # Log every 10 chunks (~0.64s at 16kHz)
                    status = "VOICE" if is_voice else "silence"
                    if self._logger:
                        self._logger.debug(f"Audio level: RMS={rms:.4f}, threshold={self._silence_threshold:.4f}, status={status}")
                
                # Add some hysteresis to prevent rapid switching
                if is_voice and not self._is_speaking:
                    # Require 3 consecutive voice detections to start (more stable)
                    if hasattr(self, '_voice_count'):
                        self._voice_count += 1
                        if self._voice_count >= 3:
                            self._is_speaking = True
                            self._silence_start_time = None
                            
                            # Add pre-roll buffer to speech buffer to capture the beginning
                            if self._pre_roll_buffer:
                                self._speech_buffer = self._pre_roll_buffer[:-3] + self._speech_buffer
                                if self._logger:
                                    self._logger.debug(f"Added {len(self._pre_roll_buffer)-3} pre-roll chunks")
                            
                            if self._logger:
                                self._logger.info(f"🎤 VOICE DETECTED (RMS: {rms:.4f} > {self._silence_threshold:.4f})")
                    else:
                        self._voice_count = 1
                elif not is_voice:
                    self._voice_count = 0
                    if self._is_speaking:
                        if self._silence_start_time is None:
                            self._silence_start_time = time.time()
                            if self._logger:
                                self._logger.info(f"🔇 SILENCE STARTED (RMS: {rms:.4f} < {self._silence_threshold:.4f})")
                        elif time.time() - self._silence_start_time >= self._silence_duration:
                            # Enough silence detected, process chunk
                            if self._logger:
                                self._logger.info(f"✂️  PROCESSING CHUNK after {self._silence_duration}s silence")
                            self._process_chunk()
                            self._is_speaking = False
                            self._silence_start_time = None
                
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Recording error: {e}")
                break
    
    def _process_chunk(self):
        """Process and save current audio chunk"""
        if not self._audio_buffer:
            return
        
        try:
            # Check if we have actual speech content
            speech_duration = (len(self._speech_buffer) * self._chunk_size) / self._sample_rate
            
            if speech_duration < 0.5:  # Less than 0.5 seconds of actual speech
                if self._logger:
                    self._logger.info(f"Skipping chunk with insufficient speech: {speech_duration:.2f}s")
                # Clear buffers and continue
                self._audio_buffer = []
                self._speech_buffer = []
                return
            
            # Calculate total duration
            duration = (len(self._audio_buffer) * self._chunk_size) / self._sample_rate
            
            # Create temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )
            
            # Combine overlap buffer with current buffer
            full_buffer = self._overlap_buffer + self._audio_buffer
            
            # Save to WAV file
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(self._channels)
                wf.setsampwidth(self._audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self._sample_rate)
                wf.writeframes(b''.join(full_buffer))
            
            # Calculate overlap samples
            overlap_samples = int(self._overlap_duration * self._sample_rate * 
                                self._channels * 2 / self._chunk_size)
            
            # Keep last portion for overlap
            if len(self._audio_buffer) > overlap_samples:
                self._overlap_buffer = self._audio_buffer[-overlap_samples:]
            else:
                self._overlap_buffer = self._audio_buffer.copy()
            
            # Clear main buffer and speech buffer
            self._audio_buffer = []
            self._speech_buffer = []
            
            if self._logger:
                self._logger.info(f"Audio chunk saved: {temp_file.name} (duration: {duration:.2f}s, speech: {speech_duration:.2f}s)")
            
            # Notify callback
            if self._on_chunk_ready:
                self._logger.debug("Calling chunk ready callback")
                self._on_chunk_ready(temp_file.name)
            else:
                self._logger.warning("No chunk ready callback set!")
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to process chunk: {e}", exc_info=True)
    
    def _cleanup_stream(self):
        """Clean up audio resources"""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
            self._stream = None
        
        if self._audio:
            try:
                self._audio.terminate()
            except:
                pass
            self._audio = None
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._recording
    
    def get_silence_duration(self) -> float:
        """Get current silence duration in seconds"""
        if self._silence_start_time:
            return time.time() - self._silence_start_time
        return 0.0