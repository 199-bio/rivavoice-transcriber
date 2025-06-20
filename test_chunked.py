#!/usr/bin/env python3
"""
Test chunked audio recording directly
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivacore.chunked_audio import ChunkedAudioRecorder
from rivacore.config import Config
from rivacore.transcriber import Transcriber
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_chunked")

# Track chunks
chunk_count = 0
total_text = ""

def process_chunk(audio_path):
    """Process audio chunk"""
    global chunk_count, total_text
    chunk_count += 1
    
    logger.info(f"=== CHUNK {chunk_count} ===")
    logger.info(f"Audio file: {audio_path}")
    
    # Check file size
    file_size = os.path.getsize(audio_path)
    logger.info(f"File size: {file_size} bytes")
    
    # Get duration
    import wave
    with wave.open(audio_path, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
        logger.info(f"Duration: {duration:.2f} seconds")
    
    # Transcribe
    config = Config()
    api_key = config.get("api_key")
    
    if api_key:
        transcriber = Transcriber(logger=logger)
        text = transcriber.transcribe(audio_path, api_key)
        
        if text:
            logger.info(f"Transcribed: {text}")
            total_text += text + " "
        else:
            logger.warning("No transcription returned")
    else:
        logger.error("No API key configured")
    
    # Cleanup
    try:
        os.remove(audio_path)
    except:
        pass

def main():
    print("Chunked Audio Test")
    print("=" * 40)
    print("Will record audio and transcribe after 2 seconds of silence")
    print("Press Ctrl+C to stop")
    print()
    
    # Create chunked recorder
    recorder = ChunkedAudioRecorder(
        silence_duration=2.0,
        on_chunk_ready=process_chunk,
        logger=logger
    )
    
    # Start recording
    if recorder.start_recording():
        print("Recording started... Speak, then pause for 2 seconds")
        print()
        
        try:
            # Keep running until interrupted
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping...")
            
    else:
        print("Failed to start recording")
    
    # Stop recording
    recorder.stop_recording()
    
    print(f"\nTotal chunks: {chunk_count}")
    print(f"Total text: {total_text}")

if __name__ == "__main__":
    main()