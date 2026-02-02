# ispeak/audio_capture.py

import pyaudio
import numpy as np
import time
from collections import deque

class AudioCapture:
    def __init__(self,
                 rate=16000,      # Whisper expects 16kHz
                 chunk_size=1024,  # Process in small chunks
                 channels=1):      # Mono audio

        self.rate = rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio_buffer = deque(maxlen=300)  # ~10 seconds buffer
        self.is_recording = False

        self.p = None
        self.stream = None

    def _init_pyaudio(self):
        """Initialize or reinitialize PyAudio to detect device changes."""
        if self.p is not None:
            try:
                self.p.terminate()
            except Exception as e:
                print(f"[Audio] Warning: Error terminating PyAudio: {e}")
        self.p = pyaudio.PyAudio()

    def _get_default_input_device(self):
        """Get the current default input device index."""
        try:
            default_info = self.p.get_default_input_device_info()
            device_name = default_info.get('name', 'Unknown')
            device_index = default_info.get('index')
            print(f"[Audio] Using input device: {device_name} (index {device_index})")

            # Check if it's a Bluetooth device (needs warm-up time)
            is_bluetooth = any(keyword in device_name.lower()
                             for keyword in ['airpods', 'bluetooth', 'wireless', 'bt'])
            if is_bluetooth:
                print(f"[Audio] Bluetooth device detected, may need warm-up time")

            return device_index, is_bluetooth
        except Exception as e:
            print(f"[Audio] Could not get default input device: {e}")
            return None, False

    def start_recording(self):
        """Start capturing audio"""
        self.is_recording = True
        self.audio_buffer.clear()

        # Reinitialize PyAudio to detect device changes (e.g., AirPods connected)
        self._init_pyaudio()

        try:
            # Get current default input device
            device_index, is_bluetooth = self._get_default_input_device()

            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            self.stream.start_stream()

            # Give Bluetooth devices a moment to warm up
            if is_bluetooth:
                time.sleep(0.2)  # 200ms warm-up for Bluetooth devices

        except Exception as e:
            print(f"[Audio] Error opening stream: {e}")
            # Try again without specifying device (use system default)
            try:
                print("[Audio] Retrying with system default device...")
                self.stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=self._audio_callback
                )
                self.stream.start_stream()
            except Exception as e2:
                print(f"[Audio] Failed to open audio stream: {e2}")
                self.is_recording = False
                raise

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Called continuously while recording"""
        if self.is_recording:
            audio_chunk = np.frombuffer(in_data, dtype=np.int16)
            self.audio_buffer.append(audio_chunk)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self):
        """Stop and return accumulated audio"""
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        # Combine all chunks into single array
        if len(self.audio_buffer) == 0:
            print("[Audio] ⚠️  No audio data captured")
            return np.array([], dtype=np.float32)

        # Optimized: concatenate and convert in one step to avoid intermediate allocation
        audio_float = np.concatenate(list(self.audio_buffer)).astype(np.float32) / 32768.0

        # Check audio levels to detect silent recordings
        audio_level = np.abs(audio_float).max()
        audio_rms = np.sqrt(np.mean(audio_float ** 2))

        if audio_level < 0.001:
            print(f"[Audio] ⚠️  Audio is silent! Max level: {audio_level:.6f}")
            print("[Audio] This might be a device issue. Try:")
            print("   1. Speak louder or move closer to microphone")
            print("   2. Check system audio input settings")
            print("   3. Try recording again (first recording after device change may fail)")
        else:
            print(f"[Audio] Audio captured: max={audio_level:.3f}, rms={audio_rms:.3f}")

        return audio_float

    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            try:
                self.stream.close()
            except Exception as e:
                print(f"[Audio] Warning: Error closing stream: {e}")
        if self.p:
            try:
                self.p.terminate()
            except Exception as e:
                print(f"[Audio] Warning: Error terminating PyAudio: {e}")
