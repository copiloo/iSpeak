# voicedev/audio_capture.py

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

        self.p = pyaudio.PyAudio()
        self.stream = None

    def start_recording(self):
        """Start capturing audio"""
        self.is_recording = True
        self.audio_buffer.clear()

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()

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
            self.stream.close()
        self.p.terminate()
