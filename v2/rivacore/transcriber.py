"""
ElevenLabs transcription functionality
"""

import os
import requests
from typing import Optional


class Transcriber:
    """Simple ElevenLabs transcriber"""
    
    def __init__(self, logger=None):
        self._logger = logger
        self._last_error = ""
        self._api_url = "https://api.elevenlabs.io/v1/speech-to-text"
    
    def transcribe(self, audio_path: str, api_key: str) -> str:
        """Transcribe audio file using ElevenLabs API"""
        if not os.path.exists(audio_path):
            self._last_error = "Audio file not found"
            return ""
        
        if not api_key:
            self._last_error = "No API key provided"
            return ""
        
        try:
            headers = {"xi-api-key": api_key}
            
            with open(audio_path, 'rb') as f:
                files = {
                    "file": (os.path.basename(audio_path), f, "audio/wav")
                }
                
                data = {
                    "model_id": "scribe_v1",
                    "language_code": "en",  # English only
                    "tag_audio_events": "false"  # Disable audio event tagging
                }
                
                if self._logger:
                    self._logger.info("Sending transcription request")
                
                response = requests.post(
                    self._api_url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("text", "")
                    
                    if self._logger:
                        self._logger.info(f"Transcription successful: {len(text)} chars")
                    
                    return text
                else:
                    self._last_error = f"API error: {response.status_code}"
                    if self._logger:
                        self._logger.error(f"API error: {response.status_code} - {response.text}")
                    return ""
                    
        except requests.exceptions.Timeout:
            self._last_error = "Request timeout"
            if self._logger:
                self._logger.error("Transcription request timeout")
            return ""
            
        except Exception as e:
            self._last_error = str(e)
            if self._logger:
                self._logger.error(f"Transcription error: {e}")
            return ""
    
    def get_last_error(self) -> str:
        """Get last error message"""
        return self._last_error