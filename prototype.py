#!/usr/bin/env python3
"""
VoiceDev Weekend Prototype
Minimal implementation to test the core concept

Requirements:
    pip install faster-whisper pyaudio pynput pyperclip numpy

Usage:
    python prototype.py
    Press and hold Right Alt
    Speak in Romanian or English
    Release Right Alt
    Text appears!
"""

import numpy as np
import pyaudio
from faster_whisper import WhisperModel
from pynput import keyboard
import pyperclip
from collections import deque

# Global state
audio_buffer = deque(maxlen=300)
is_recording = False
model = None

def init_audio():
    """Initialize audio capture"""
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024,
        stream_callback=audio_callback
    )
    stream.start_stream()
    return p, stream

def audio_callback(in_data, frame_count, time_info, status):
    """Capture audio chunks"""
    if is_recording:
        chunk = np.frombuffer(in_data, dtype=np.int16)
        audio_buffer.append(chunk)
    return (in_data, pyaudio.paContinue)

def transcribe_and_type():
    """Transcribe buffered audio and type it"""
    global audio_buffer

    if len(audio_buffer) == 0:
        return

    print("Transcribing...")

    # Combine chunks
    audio = np.concatenate(list(audio_buffer))
    audio = audio.astype(np.float32) / 32768.0

    # Transcribe
    segments, info = model.transcribe(audio, language="ro", beam_size=1)
    text = " ".join([seg.text for seg in segments]).strip()

    if text:
        print(f"Text: {text}")
        # Paste via clipboard
        old_clipboard = pyperclip.paste()
        pyperclip.copy(text)

        # Simulate Cmd+V
        kb = keyboard.Controller()
        with kb.pressed(keyboard.Key.cmd):
            kb.press('v')
            kb.release('v')

        # Restore old clipboard after a brief delay
        import time
        time.sleep(0.2)
        pyperclip.copy(old_clipboard)

    audio_buffer.clear()

def on_press(key):
    """Start recording on Right Alt press"""
    global is_recording
    if key == keyboard.Key.alt_r and not is_recording:
        is_recording = True
        print("🎤 Recording...")

def on_release(key):
    """Stop and transcribe on Right Alt release"""
    global is_recording
    if key == keyboard.Key.alt_r and is_recording:
        is_recording = False
        print("⏸️  Processing...")
        transcribe_and_type()
        print("✅ Ready")

def main():
    global model

    print("Loading Whisper model...")
    model = WhisperModel("small", device="auto", compute_type="int8")  # Better Romanian accuracy

    print("Starting audio capture...")
    p, stream = init_audio()

    print("\n" + "="*50)
    print("VoiceDev Prototype Ready!")
    print("="*50)
    print("Press and hold Right Alt to dictate")
    print("Speak in Romanian or English")
    print("Release to transcribe")
    print("Press Ctrl+C to quit\n")

    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\nStopping...")

    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Goodbye!")

if __name__ == "__main__":
    main()
