#!/usr/bin/env python3
"""
Save a chunk for manual testing
"""

import sys
import os
import time
import shutil

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore.chunked_audio import ChunkedAudioRecorder
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_chunk_save")

saved_file = None

def save_chunk(audio_path):
    """Save the first chunk for analysis"""
    global saved_file
    
    # Copy to current directory
    saved_file = "test_chunk.wav"
    shutil.copy2(audio_path, saved_file)
    
    logger.info(f"Chunk saved to: {saved_file}")
    
    # Check file info
    import wave
    with wave.open(audio_path, 'rb') as wf:
        logger.info(f"Channels: {wf.getnchannels()}")
        logger.info(f"Sample width: {wf.getsampwidth()} bytes")
        logger.info(f"Frame rate: {wf.getframerate()} Hz")
        logger.info(f"Frames: {wf.getnframes()}")
        logger.info(f"Duration: {wf.getnframes() / wf.getframerate():.2f} seconds")

def main():
    print("Chunk Save Test")
    print("=" * 40)
    print("Speak something, then pause for 2 seconds")
    print("The first chunk will be saved as test_chunk.wav")
    print()
    
    # Create chunked recorder
    recorder = ChunkedAudioRecorder(
        silence_duration=2.0,
        on_chunk_ready=save_chunk,
        logger=logger
    )
    
    # Start recording
    if recorder.start_recording():
        print("Recording started...")
        
        # Wait for first chunk
        start = time.time()
        while saved_file is None and time.time() - start < 30:
            time.sleep(0.1)
            
    # Stop recording
    recorder.stop_recording()
    
    if saved_file:
        print(f"\nChunk saved: {saved_file}")
        print("You can test transcription with:")
        print(f"  curl -X POST https://api.elevenlabs.io/v1/speech-to-text \\")
        print(f"    -H 'xi-api-key: YOUR_API_KEY' \\")
        print(f"    -F 'file=@{saved_file}' \\")
        print(f"    -F 'model_id=scribe_v1' \\")
        print(f"    -F 'language_code=en' \\")
        print(f"    -F 'tag_audio_events=false'")
    else:
        print("\nNo chunk was saved")

if __name__ == "__main__":
    main()