#!/usr/bin/env python3
"""
Test Fn key handling
"""

from pynput import keyboard
import time

def on_press(key):
    print(f"\nRaw key: {key}")
    print(f"Type: {type(key)}")
    print(f"Has char: {hasattr(key, 'char')}")
    
    if hasattr(key, 'char'):
        print(f"Char value: {key.char}")
        print(f"Char is None: {key.char is None}")
    
    if hasattr(key, 'vk'):
        print(f"Virtual key code: {key.vk}")
    
    # Better key extraction
    key_str = None
    if hasattr(key, 'char') and key.char is not None:
        key_str = key.char
    elif hasattr(key, 'vk'):
        # Special handling for Fn key and others
        if key.vk == 179:  # Fn key
            key_str = 'fn'
        else:
            key_str = str(key).replace('Key.', '').replace('<', '').replace('>', '')
    else:
        key_str = str(key).replace('Key.', '').replace('<', '').replace('>', '')
    
    print(f"Extracted key string: '{key_str}'")
    
    return False  # Stop after one key

print("Press the Fn key (or any key)...")
listener = keyboard.Listener(on_press=on_press)
listener.start()
listener.join()