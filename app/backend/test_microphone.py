#!/usr/bin/env python3
"""
Simple script to test microphone access and trigger permission request.
"""

import sounddevice as sd
import sys

def test_microphone():
    """Test microphone access to trigger permission request."""
    try:
        print("Testing microphone access...", file=sys.stderr)
        
        # Try to get default input device
        default_device = sd.default.device[0]
        print(f"Default input device: {default_device}", file=sys.stderr)
        
        # Try to get device info
        device_info = sd.query_devices(default_device)
        print(f"Device info: {device_info}", file=sys.stderr)
        
        # Try to record a very short sample (0.1 seconds)
        print("Attempting to record 0.1 seconds of audio...", file=sys.stderr)
        audio_data = sd.rec(int(0.1 * 16000), samplerate=16000, channels=1, dtype='float32')
        sd.wait()  # Wait for recording to complete
        
        print("✅ Microphone access successful!", file=sys.stderr)
        print("Microphone permission granted!")
        return True
        
    except Exception as e:
        print(f"❌ Microphone access failed: {e}", file=sys.stderr)
        print("Please grant microphone permission to Python in System Preferences > Security & Privacy > Privacy > Microphone")
        return False

if __name__ == "__main__":
    test_microphone()
