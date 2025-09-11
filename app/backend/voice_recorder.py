#!/usr/bin/env python3
"""
Real-time voice recording and transcription using sounddevice and Whisper.
This script records audio from the microphone and transcribes it using OpenAI's Whisper.
"""

import argparse
import sys
import tempfile
import os
import sounddevice as sd
import numpy as np
import whisper
import time
import wave

def _pick_input_device() -> int | None:
    """
    Return a sane input device index.
    - Use current default if it has input channels.
    - Else pick the first device with input channels > 0.
    """
    try:
        default = sd.default.device
        if isinstance(default, (list, tuple)) and default and default[0] is not None:
            info = sd.query_devices(default[0])
            if info.get("max_input_channels", 0) > 0:
                return default[0]
    except Exception:
        pass

    try:
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                return idx
    except Exception:
        pass
    return None


def record_audio(duration=5, sample_rate=16000):
    """
    Record audio from the default microphone for the specified duration.
    
    Args:
        duration (int): Recording duration in seconds
        sample_rate (int): Sample rate for recording (Whisper works best with 16kHz)
    
    Returns:
        numpy.ndarray: Recorded audio data
    """
    print(f"Recording for {duration} seconds...", file=sys.stderr)
    
    try:
        # Choose a valid input device if default is not usable
        device_index = _pick_input_device()
        if device_index is not None:
            sd.default.device = (device_index, None)
            dev_info = sd.query_devices(device_index)
            print(f"Using input device: #{device_index} - {dev_info.get('name')} (inputs={dev_info.get('max_input_channels')})", file=sys.stderr)
        else:
            print("No valid input device found; recording may fail or be silent.", file=sys.stderr)

        # Record audio
        audio_data = sd.rec(
            int(duration * sample_rate), 
            samplerate=sample_rate, 
            channels=1, 
            dtype=np.float32
        )
        sd.wait()  # Wait until recording is finished
        
        # Compute simple RMS to detect silence
        try:
            rms = float(np.sqrt(np.mean(np.square(audio_data))))
        except Exception:
            rms = 0.0
        print(f"Recording completed. RMS={rms:.6f}", file=sys.stderr)
        return audio_data.flatten()
        
    except Exception as e:
        print(f"Error recording audio: {e}", file=sys.stderr)
        return None

def save_audio_to_file(audio_data, sample_rate=16000):
    """
    Save audio data to a temporary WAV file.
    
    Args:
        audio_data (numpy.ndarray): Audio data to save
        sample_rate (int): Sample rate of the audio
    
    Returns:
        str: Path to the temporary audio file
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Convert to 16-bit PCM for WAV format
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Save as WAV file using wave module
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return temp_path
        
    except Exception as e:
        print(f"Error saving audio file: {e}", file=sys.stderr)
        return None

def transcribe_audio(audio_file_path, model_size="base"):
    """
    Transcribe audio file using Whisper.
    
    Args:
        audio_file_path (str): Path to the audio file
        model_size (str): Whisper model size (tiny, base, small, medium, large)
    
    Returns:
        str: Transcribed text
    """
    try:
        print(f"Loading Whisper model '{model_size}'...", file=sys.stderr)
        model = whisper.load_model(model_size)
        
        print("Transcribing audio...", file=sys.stderr)
        # Use fp16=False to avoid ffmpeg dependency issues
        result = model.transcribe(audio_file_path, fp16=False)
        
        transcription = result["text"].strip()
        print(f"Transcription completed. Result: '{transcription}'", file=sys.stderr)
        
        if not transcription:
            return "No speech detected. Please try speaking louder or closer to the microphone."
        
        return transcription
        
    except Exception as e:
        print(f"Error during transcription: {e}", file=sys.stderr)
        # Return a fallback message if transcription fails
        return "Voice input detected but transcription failed. Please try again or use text input."

def main():
    parser = argparse.ArgumentParser(description="Record and transcribe voice input")
    parser.add_argument("--duration", type=int, default=5, help="Recording duration in seconds")
    parser.add_argument("--model", default="base", help="Whisper model size")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Audio sample rate")
    
    args = parser.parse_args()
    
    # Record audio
    audio_data = record_audio(args.duration, args.sample_rate)
    if audio_data is None:
        sys.exit(1)
    
    # Save to temporary file
    audio_file = save_audio_to_file(audio_data, args.sample_rate)
    if audio_file is None:
        sys.exit(1)
    
    try:
        # Transcribe audio
        transcription = transcribe_audio(audio_file, args.model)
        
        if transcription:
            print(transcription)
        else:
            print("Failed to transcribe audio", file=sys.stderr)
            sys.exit(1)
            
    finally:
        # Clean up temporary file
        try:
            os.unlink(audio_file)
        except:
            pass

if __name__ == "__main__":
    main()
