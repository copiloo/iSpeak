# ispeak/audio_capture.py

import pyaudio
import numpy as np
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
            except:
                pass
        self.p = pyaudio.PyAudio()

    def _get_default_input_device(self):
        """Get the current default input device index."""
        try:
            default_info = self.p.get_default_input_device_info()
            device_name = default_info.get('name', 'Unknown')
            device_index = default_info.get('index')
            print(f"[Audio] Using input device: {device_name} (index {device_index})")
            return device_index
        except Exception as e:
            print(f"[Audio] Could not get default input device: {e}")
            return None

    def start_recording(self):
        """Start capturing audio"""
        self.is_recording = True
        self.audio_buffer.clear()

        # Reinitialize PyAudio to detect device changes (e.g., AirPods connected)
        self._init_pyaudio()

        try:
            # Get current default input device
            device_index = self._get_default_input_device()

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
            return np.array([], dtype=np.float32)

        audio_data = np.concatenate(list(self.audio_buffer))

        # Convert to float32 normalized (Whisper requirement)
        audio_float = audio_data.astype(np.float32) / 32768.0

        return audio_float

    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            try:
                self.stream.close()
            except:
                pass
        if self.p:
            try:
                self.p.terminate()
            except:
                pass
