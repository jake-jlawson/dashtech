#!/usr/bin/env python3
"""
Voice transcription service using Whisper for offline speech recognition.
"""

import os
import sys
import argparse
import tempfile
import json
from pathlib import Path

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

def transcribe_audio(audio_file_path: str, model_size: str = "base") -> str:
    """
    Transcribe audio file using Whisper.
    
    Args:
        audio_file_path: Path to the audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
    
    Returns:
        Transcribed text
    """
    if not WHISPER_AVAILABLE:
        return "Whisper not available. Please install: pip install openai-whisper"
    
    if not os.path.exists(audio_file_path):
        return f"Audio file not found: {audio_file_path}"
    
    try:
        # Load Whisper model
        model = whisper.load_model(model_size)
        
        # Transcribe audio
        result = model.transcribe(audio_file_path)
        
        # Return the transcribed text
        return result["text"].strip()
        
    except Exception as e:
        return f"Transcription error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio using Whisper")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--model", default="base", help="Whisper model size")
    parser.add_argument("--output", help="Output file for transcription")
    
    args = parser.parse_args()
    
    # Transcribe the audio
    transcription = transcribe_audio(args.audio_file, args.model)
    
    if args.output:
        # Save to file
        with open(args.output, 'w') as f:
            f.write(transcription)
        print(f"Transcription saved to: {args.output}")
    else:
        # Print to stdout
        print(transcription)

if __name__ == "__main__":
    main()
