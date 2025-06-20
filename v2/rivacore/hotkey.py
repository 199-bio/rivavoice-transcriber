"""
Global hotkey management
"""

import threading
import time
from typing import Optional, Callable
from pynput import keyboard


class HotkeyManager:
    """Simple hotkey capture and registration"""
    
    def __init__(self, logger=None):
        self._logger = logger
        self._listener = None
        self._hotkey = None
        self._callback = None
        self._capturing = False
        self._captured_key = None
        self._capture_event = threading.Event()
    
    def register(self, key: str, callback: Optional[Callable] = None) -> bool:
        """Register a global hotkey"""
        try:
            # Stop existing listener
            if self._listener:
                self._listener.stop()
            
            self._hotkey = key
            self._callback = callback
            
            # Create new listener
            self._listener = keyboard.Listener(on_press=self._on_press)
            self._listener.start()
            
            if self._logger:
                self._logger.info(f"Hotkey registered: {key}")
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to register hotkey: {e}")
            return False
    
    def _on_press(self, key):
        """Handle key press"""
        if self._capturing:
            # Capture mode - store the key
            try:
                # Better key extraction for special keys
                if hasattr(key, 'char') and key.char is not None:
                    self._captured_key = key.char
                elif hasattr(key, 'vk'):
                    # Handle special keys by virtual key code
                    vk = key.vk
                    if vk == 179:  # Fn key
                        self._captured_key = 'fn'
                    elif 112 <= vk <= 123:  # F1-F12
                        self._captured_key = f'f{vk - 111}'
                    else:
                        # Remove angle brackets and Key. prefix
                        self._captured_key = str(key).replace('Key.', '').replace('<', '').replace('>', '')
                else:
                    self._captured_key = str(key).replace('Key.', '').replace('<', '').replace('>', '')
                
                if self._logger:
                    self._logger.debug(f"Captured key: {self._captured_key} from {key}")
                
                self._capture_event.set()
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error capturing key: {e}")
        else:
            # Normal mode - check for hotkey
            try:
                # Same extraction logic for consistency
                key_str = None
                if hasattr(key, 'char') and key.char is not None:
                    key_str = key.char
                elif hasattr(key, 'vk'):
                    vk = key.vk
                    if vk == 179:
                        key_str = 'fn'
                    elif 112 <= vk <= 123:
                        key_str = f'f{vk - 111}'
                    else:
                        key_str = str(key).replace('Key.', '').replace('<', '').replace('>', '')
                else:
                    key_str = str(key).replace('Key.', '').replace('<', '').replace('>', '')
                
                if key_str == self._hotkey and self._callback:
                    self._callback()
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error handling hotkey: {e}")
    
    def capture_next_key(self) -> str:
        """Capture the next key press"""
        if self._listener:
            self._listener.stop()
        
        self._capturing = True
        self._captured_key = None
        self._capture_event.clear()
        
        # Start temporary listener
        listener = keyboard.Listener(on_press=self._on_press)
        listener.start()
        
        # Wait for key press (max 10 seconds)
        self._capture_event.wait(timeout=10)
        
        # Stop listener
        listener.stop()
        self._capturing = False
        
        # Restart normal listener if we have a hotkey
        if self._hotkey:
            self.register(self._hotkey, self._callback)
        
        result = self._captured_key or ""
        
        if self._logger:
            self._logger.info(f"Captured key: {result}")
        
        return result
    
    def stop(self):
        """Stop listening for hotkeys"""
        if self._listener:
            self._listener.stop()
            self._listener = None