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
        self.audio_buffer = deque(maxlen=300)  # ~19 seconds at 16kHz/1024-chunk
        self.is_recording = False

        self.stream = None

        # Initialize PyAudio once at startup (not on every recording)
        self.p = pyaudio.PyAudio()

    def _get_default_input_device(self):
        """Get the current default input device index."""
        try:
            default_info = self.p.get_default_input_device_info()
            device_name = default_info.get('name', 'Unknown')
            device_index = default_info.get('index')
            print(f"[Audio] Using input device: {device_name} (index {device_index})")

            is_bluetooth = any(keyword in device_name.lower()
                             for keyword in ['airpods', 'bluetooth', 'wireless', 'bt'])
            if is_bluetooth:
                print(f"[Audio] Bluetooth device detected, may need warm-up time")

            return device_index, is_bluetooth
        except Exception as e:
            print(f"[Audio] Could not get default input device: {e}")
            return None, False

    def _open_stream(self, device_index):
        """Open a PyAudio stream on the given device index (None = system default)."""
        return self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )

    def start_recording(self):
        """Start capturing audio."""
        self.is_recording = True
        self.audio_buffer.clear()

        try:
            device_index, is_bluetooth = self._get_default_input_device()
            self.stream = self._open_stream(device_index)
            self.stream.start_stream()

            if is_bluetooth:
                time.sleep(0.2)  # 200ms warm-up for Bluetooth devices

        except Exception as e:
            print(f"[Audio] Error opening stream: {e}")
            # Device may have changed — reinitialize PyAudio and retry once
            try:
                print("[Audio] Reinitializing PyAudio and retrying...")
                self.p.terminate()
                self.p = pyaudio.PyAudio()
                self.stream = self._open_stream(None)  # system default, no device index
                self.stream.start_stream()
            except Exception as e2:
                print(f"[Audio] Failed to open audio stream: {e2}")
                self.is_recording = False
                raise

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Called continuously while recording."""
        if self.is_recording:
            audio_chunk = np.frombuffer(in_data, dtype=np.int16)
            self.audio_buffer.append(audio_chunk)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self):
        """Stop and return accumulated audio as float32."""
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        if len(self.audio_buffer) == 0:
            print("[Audio] ⚠️  No audio data captured")
            return np.array([], dtype=np.float32)

        audio_float = np.concatenate(list(self.audio_buffer)).astype(np.float32) / 32768.0

        audio_level = np.abs(audio_float).max()
        audio_rms = np.sqrt(np.mean(audio_float ** 2))

        if audio_level < 0.001:
            print(f"[Audio] ⚠️  Audio is silent! Max level: {audio_level:.6f}")
            print("[Audio] Check system audio input settings or speak louder.")
        else:
            print(f"[Audio] Audio captured: max={audio_level:.3f}, rms={audio_rms:.3f}")

        return audio_float

    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            try:
                self.stream.close()
            except Exception as e:
                print(f"[Audio] Warning: Error closing stream: {e}")
            self.stream = None
        if self.p:
            try:
                self.p.terminate()
            except Exception as e:
                print(f"[Audio] Warning: Error terminating PyAudio: {e}")
            self.p = None
