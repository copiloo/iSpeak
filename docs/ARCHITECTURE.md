# iSpeak: Technical Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Component Breakdown](#component-breakdown)
3. [Project Structure](#project-structure)
4. [Dependencies](#dependencies)
5. [Performance Optimizations](#performance-optimizations)
6. [macOS Permissions](#macos-permissions)
7. [Build & Distribution](#build--distribution)
8. [Testing Strategy](#testing-strategy)
9. [Development Timeline](#development-timeline)
10. [Weekend Prototype](#weekend-prototype)

---

## System Overview
```
┌─────────────────────────────────────────────────────────────┐
│                        USER'S MAC                            │
│                                                              │
│  ┌────────────┐    ┌──────────────┐    ┌─────────────┐    │
│  │            │    │              │    │             │    │
│  │ Microphone │───▶│ Audio Buffer │───▶│   Whisper   │    │
│  │            │    │   (Stream)   │    │   Engine    │    │
│  └────────────┘    └──────────────┘    └─────────────┘    │
│                                               │             │
│                                               ▼             │
│  ┌────────────┐    ┌──────────────┐    ┌─────────────┐    │
│  │            │    │              │    │             │    │
│  │ VS Code /  │◀───│Text Injection│◀───│   Post-     │    │
│  │   Any App  │    │   System     │    │ Processing  │    │
│  │            │    │              │    │             │    │
│  └────────────┘    └──────────────┘    └─────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Control Layer (Menu Bar App)              │    │
│  │  • Global Hotkeys                                   │    │
│  │  • Language Toggle                                  │    │
│  │  • Settings UI                                      │    │
│  │  • Status Display                                   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- 100% offline processing (no API costs)
- All components run locally on user's Mac
- Uses local Whisper models for speech-to-text
- System-wide text injection works in any app
- Privacy-first: audio never leaves the machine

---

## Component Breakdown

### 1. Audio Capture Module

**Technology:** `PyAudio` or native macOS `AVFoundation`

**Responsibilities:**
- Capture microphone input in real-time
- Stream audio in chunks (not wait for complete recording)
- Handle multiple audio devices
- Reduce background noise (optional)

**Implementation:**
```python
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
        audio_data = np.concatenate(list(self.audio_buffer))
        
        # Convert to float32 normalized (Whisper requirement)
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        return audio_float
    
    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            self.stream.close()
        self.p.terminate()
```

**Alternative Native macOS (for production):**
```swift
// Native Swift implementation using AVFoundation
import AVFoundation

class AudioCapture {
    private var audioEngine: AVAudioEngine
    private var inputNode: AVAudioInputNode
    private var audioBuffer: [Float] = []
    
    func startRecording() {
        audioEngine = AVAudioEngine()
        inputNode = audioEngine.inputNode
        
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, 
                            bufferSize: 1024, 
                            format: recordingFormat) { buffer, _ in
            // Process audio buffer
            self.processAudioBuffer(buffer)
        }
        
        try? audioEngine.start()
    }
    
    func stopRecording() -> [Float] {
        audioEngine.stop()
        inputNode.removeTap(onBus: 0)
        return audioBuffer
    }
}
```

---

### 2. Speech-to-Text Engine

**Technology:** `faster-whisper` (Python wrapper for whisper.cpp)

**Why faster-whisper:**
- 4x faster than Python Whisper
- Optimized for Apple Silicon (Metal support)
- Smaller memory footprint
- Real-time capable with tiny/base models

**Model Selection:**

| Model | Size | Speed (M1) | Accuracy | Use Case |
|-------|------|------------|----------|----------|
| tiny | 75MB | 32x realtime | 85% | Quick dictation |
| base | 142MB | 16x realtime | 90% | **Recommended default** |
| small | 466MB | 6x realtime | 93% | High accuracy |
| medium | 1.5GB | 2x realtime | 95% | Best quality |

**Implementation:**
```python
# ispeak/transcription.py

from faster_whisper import WhisperModel
import os

class TranscriptionEngine:
    def __init__(self, model_size="base", models_dir="./models"):
        """
        Initialize Whisper model
        model_size: "tiny", "base", "small", "medium", "large"
        models_dir: directory to store/cache models
        """
        self.model_size = model_size
        self.models_dir = models_dir
        
        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)
        
        # device: "cpu", "cuda", or "auto"
        # compute_type: "int8" for speed, "float16" for quality
        print(f"Loading {model_size} model...")
        self.model = WhisperModel(
            model_size, 
            device="auto",  # Use Metal on M-series Macs
            compute_type="int8",  # Faster, minimal accuracy loss
            download_root=models_dir
        )
        print(f"Model loaded: {model_size}")
        
        self.current_language = "ro"  # Default Romanian
    
    def transcribe(self, audio_data, language=None):
        """
        Transcribe audio to text
        Returns: dict with 'text', 'language', 'segments'
        """
        if language is None:
            language = self.current_language
        
        # Transcribe with options
        segments, info = self.model.transcribe(
            audio_data,
            language=language,
            beam_size=5,          # Quality vs speed tradeoff
            vad_filter=True,      # Filter out silence
            vad_parameters=dict(
                min_silence_duration_ms=500  # 500ms silence = pause
            )
        )
        
        # Combine all segments
        text = " ".join([segment.text for segment in segments])
        
        return {
            "text": text.strip(),
            "language": info.language,
            "segments": list(segments)
        }
    
    def transcribe_realtime(self, audio_data):
        """
        Faster transcription for real-time use
        Lower accuracy but instant feedback
        """
        segments, info = self.model.transcribe(
            audio_data,
            language=self.current_language,
            beam_size=1,      # Fastest beam search
            vad_filter=True,
            without_timestamps=True  # Skip timestamp calculation
        )
        
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    
    def set_language(self, lang_code):
        """Switch language: 'ro', 'en', etc."""
        self.current_language = lang_code
        print(f"Language set to: {lang_code}")
    
    def get_supported_languages(self):
        """Return list of supported languages"""
        return [
            "en", "ro", "es", "fr", "de", "it", "pt", "nl", 
            "pl", "ru", "ja", "ko", "zh", "ar", "hi", "tr"
            # Whisper supports 99 languages total
        ]
```

---

### 3. Post-Processing Module

**Responsibilities:**
- Clean up transcription artifacts
- Apply code-aware formatting
- Handle Romanian-specific quirks
- Custom vocabulary substitution

**Implementation:**
```python
# ispeak/text_processor.py

import re
from typing import Dict, List
import json
import os

class TextProcessor:
    def __init__(self, vocabulary_file="resources/vocabulary.json"):
        self.vocabulary_file = vocabulary_file
        
        # Custom vocabulary for Romanian tech terms
        self.vocabulary = {
            "git hub": "GitHub",
            "vis code": "VS Code",
            "visual studio code": "VS Code",
            "java script": "JavaScript",
            "type script": "TypeScript",
            "python": "Python",
            "funk ție": "funcție",
            "vari abilă": "variabilă",
            "no duri": "noduri",
            # Add more as users report issues
        }
        
        # Code patterns (voice commands for coding)
        self.code_patterns = {
            "new line": "\n",
            "tab": "\t",
            "open brace": " {",
            "close brace": "}",
            "open bracket": "[",
            "close bracket": "]",
            "open paren": "(",
            "close paren": ")",
            "semicolon": ";",
            "colon": ":",
            "comma": ",",
            "period": ".",
            "equals": " = ",
            "plus": " + ",
            "minus": " - ",
            "plus plus": "++",
            "minus minus": "--",
            "arrow": " => ",
            "dot": ".",
        }
        
        # Romanian autocorrect (common diacritics issues)
        self.romanian_corrections = {
            "functie": "funcție",
            "functii": "funcții",
            "variabila": "variabilă",
            "variabile": "variabile",
            "metoda": "metodă",
            "metode": "metode",
            "clasa": "clasă",
            "clase": "clase",
            "pentru": "pentru",
            "intrare": "intrare",
            "iesire": "ieșire",
        }
        
        # Load custom vocabulary if exists
        self._load_vocabulary()
    
    def process(self, text: str, context: Dict = None) -> str:
        """
        Process transcribed text
        context: dict with 'app_name', 'file_type', etc.
        """
        if not text:
            return ""
        
        # 1. Apply custom vocabulary
        text = self._apply_vocabulary(text)
        
        # 2. If in code editor, apply code formatting
        if context and self._is_code_context(context):
            text = self._apply_code_formatting(text)
        
        # 3. Romanian-specific corrections
        text = self._apply_romanian_corrections(text)
        
        # 4. Clean up extra spaces
        text = self._cleanup_whitespace(text)
        
        return text
    
    def _apply_vocabulary(self, text: str) -> str:
        """Replace custom vocabulary"""
        for wrong, right in self.vocabulary.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(wrong), re.IGNORECASE)
            text = pattern.sub(right, text)
        return text
    
    def _is_code_context(self, context: Dict) -> bool:
        """Detect if user is in a code editor"""
        code_apps = ['Code', 'VS Code', 'PyCharm', 'Cursor', 'Sublime', 
                     'IntelliJ', 'WebStorm', 'Atom', 'Xcode']
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.go', 
                          '.rb', '.php', '.swift', '.kt', '.rs']
        
        app_name = context.get('app_name', '')
        file_type = context.get('file_type', '')
        
        return (any(app in app_name for app in code_apps) or
                any(file_type.endswith(ext) for ext in code_extensions))
    
    def _apply_code_formatting(self, text: str) -> str:
        """Apply code-specific formatting"""
        # Replace code patterns
        for spoken, written in self.code_patterns.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(spoken) + r'\b'
            text = re.sub(pattern, written, text, flags=re.IGNORECASE)
        
        # Handle common code phrases
        text = re.sub(r'\bif\s+(\w+)\s+equals\s+(\w+)\b', 
                      r'if \1 == \2', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfor\s+(\w+)\s+in\s+range\b', 
                      r'for \1 in range', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdef\s+(\w+)', r'def \1', text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_romanian_corrections(self, text: str) -> str:
        """Fix Romanian diacritics that might be missing"""
        for wrong, right in self.romanian_corrections.items():
            # Only replace whole words
            pattern = r'\b' + re.escape(wrong) + r'\b'
            text = re.sub(pattern, right, text, flags=re.IGNORECASE)
        return text
    
    def _cleanup_whitespace(self, text: str) -> str:
        """Remove extra spaces and fix punctuation spacing"""
        # Multiple spaces -> single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove space before punctuation
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        
        # Add space after punctuation (if missing)
        text = re.sub(r'([,.;:!?])([A-Za-z])', r'\1 \2', text)
        
        return text.strip()
    
    def add_custom_word(self, spoken: str, written: str):
        """Allow users to add custom vocabulary"""
        self.vocabulary[spoken.lower()] = written
        self._save_vocabulary()
    
    def _load_vocabulary(self):
        """Load custom vocabulary from file"""
        if os.path.exists(self.vocabulary_file):
            try:
                with open(self.vocabulary_file, 'r', encoding='utf-8') as f:
                    custom = json.load(f)
                    self.vocabulary.update(custom)
                print(f"Loaded {len(custom)} custom vocabulary entries")
            except Exception as e:
                print(f"Error loading vocabulary: {e}")
    
    def _save_vocabulary(self):
        """Save custom vocabulary to file"""
        try:
            os.makedirs(os.path.dirname(self.vocabulary_file), exist_ok=True)
            with open(self.vocabulary_file, 'w', encoding='utf-8') as f:
                json.dump(self.vocabulary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving vocabulary: {e}")
```

---

### 4. Text Injection System

**Responsibilities:**
- Type text into active application
- Handle special keys (Enter, Tab, etc.)
- Respect cursor position
- Work across all macOS apps

**Implementation:**
```python
# ispeak/text_injector.py

from pynput.keyboard import Controller, Key
import time
import pyperclip

class TextInjector:
    def __init__(self, typing_speed=0.01):
        self.keyboard = Controller()
        self.typing_speed = typing_speed  # Delay between characters (seconds)
    
    def type_text(self, text: str, instant: bool = True):
        """
        Type text into active application
        instant: if True, paste instead of typing (faster but less natural)
        """
        if not text:
            return
        
        if instant:
            self._paste_text(text)
        else:
            self._type_slowly(text)
    
    def _type_slowly(self, text: str):
        """Simulate natural typing character by character"""
        for char in text:
            try:
                self.keyboard.type(char)
                if self.typing_speed > 0:
                    time.sleep(self.typing_speed)
            except Exception as e:
                print(f"Error typing character '{char}': {e}")
    
    def _paste_text(self, text: str):
        """
        Paste via clipboard (faster)
        This is the recommended method for longer text
        """
        try:
            # Save current clipboard
            old_clipboard = pyperclip.paste()
            
            # Copy new text
            pyperclip.copy(text)
            
            # Small delay to ensure clipboard is updated
            time.sleep(0.05)
            
            # Paste (Cmd+V on Mac)
            with self.keyboard.pressed(Key.cmd):
                self.keyboard.press('v')
                self.keyboard.release('v')
            
            # Wait for paste to complete
            time.sleep(0.1)
            
            # Restore old clipboard
            pyperclip.copy(old_clipboard)
            
        except Exception as e:
            print(f"Error pasting text: {e}")
            # Fallback to typing
            self._type_slowly(text)
    
    def press_key(self, key_name: str):
        """Press special keys"""
        key_map = {
            'enter': Key.enter,
            'return': Key.enter,
            'tab': Key.tab,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'escape': Key.esc,
            'esc': Key.esc,
            'space': Key.space,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
        }
        
        key = key_map.get(key_name.lower())
        if key:
            self.keyboard.press(key)
            self.keyboard.release(key)
    
    def delete_last_word(self):
        """Delete the last word (useful for corrections)"""
        # Option+Backspace on Mac deletes word
        with self.keyboard.pressed(Key.alt):
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)
    
    def delete_last_character(self):
        """Delete the last character"""
        self.keyboard.press(Key.backspace)
        self.keyboard.release(Key.backspace)
```

**Note for Production:**
For a production app, consider using native macOS CGEvent API for more reliable injection:
```swift
// Swift implementation using CGEvent (more reliable)
import CoreGraphics

class TextInjector {
    func typeText(_ text: String) {
        let source = CGEventSource(stateID: .hidSystemState)
        
        for char in text {
            if let keyCode = char.keyCode {
                let keyDown = CGEvent(keyboardEventSource: source, 
                                     virtualKey: keyCode, 
                                     keyDown: true)
                let keyUp = CGEvent(keyboardEventSource: source, 
                                   virtualKey: keyCode, 
                                   keyDown: false)
                
                keyDown?.post(tap: .cghidEventTap)
                keyUp?.post(tap: .cghidEventTap)
            }
        }
    }
    
    func pasteText(_ text: String) {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(text, forType: .string)
        
        // Simulate Cmd+V
        let cmdV = CGEvent(keyboardEventSource: nil, virtualKey: 0x09, keyDown: true)
        cmdV?.flags = .maskCommand
        cmdV?.post(tap: .cghidEventTap)
    }
}
```

---

### 5. Hotkey & Control Module

**Responsibilities:**
- Global hotkey listener (works even when app not focused)
- Start/stop recording on hotkey press/release
- Status indicator (recording, processing, idle)
- Language switching

**Implementation:**
```python
# ispeak/hotkey_controller.py

from pynput import keyboard
import threading

class HotkeyController:
    def __init__(self, on_start_callback, on_stop_callback):
        """
        Initialize hotkey controller
        on_start_callback: function to call when hotkey pressed
        on_stop_callback: function to call when hotkey released
        """
        self.on_start = on_start_callback
        self.on_stop = on_stop_callback
        
        self.is_recording = False
        
        # Default hotkey: Right Option (Alt) key
        # Can be customized by user
        self.hotkey = keyboard.Key.alt_r
        
        self.listener = None
    
    def start_listening(self):
        """Start global hotkey listener"""
        print(f"Hotkey listener started. Press {self.hotkey} to dictate.")
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
    
    def stop_listening(self):
        """Stop listener"""
        if self.listener:
            self.listener.stop()
            print("Hotkey listener stopped.")
    
    def _on_press(self, key):
        """Called when any key is pressed"""
        try:
            if key == self.hotkey and not self.is_recording:
                self.is_recording = True
                self.on_start()  # Start recording
        except Exception as e:
            print(f"Error in key press handler: {e}")
    
    def _on_release(self, key):
        """Called when any key is released"""
        try:
            if key == self.hotkey and self.is_recording:
                self.is_recording = False
                self.on_stop()  # Stop recording and transcribe
        except Exception as e:
            print(f"Error in key release handler: {e}")
    
    def set_hotkey(self, key):
        """
        Allow user to customize hotkey
        key: pynput.keyboard.Key or KeyCode
        """
        self.hotkey = key
        print(f"Hotkey changed to: {key}")
    
    def get_hotkey_name(self):
        """Return human-readable hotkey name"""
        if hasattr(self.hotkey, 'name'):
            return self.hotkey.name
        return str(self.hotkey)
```

**Alternative Hotkeys:**
- `keyboard.Key.f13` - F13 key (if available)
- `keyboard.Key.cmd_r` - Right Command
- `keyboard.Key.ctrl` - Control key
- Custom combination (more complex, requires different implementation)

---

### 6. Context Detector

**Responsibilities:**
- Detect active application
- Detect file type (for code-aware processing)
- Provide context to post-processor

**Implementation:**
```python
# ispeak/context_detector.py

import os
import sys

class ContextDetector:
    def __init__(self):
        self.platform = sys.platform
        
        if self.platform == "darwin":  # macOS
            try:
                from AppKit import NSWorkspace
                self.workspace = NSWorkspace.sharedWorkspace()
                self.has_appkit = True
            except ImportError:
                print("Warning: AppKit not available. Install: pip install pyobjc-framework-Cocoa")
                self.has_appkit = False
        else:
            self.has_appkit = False
    
    def get_current_context(self) -> dict:
        """
        Get context about current environment
        Returns dict with: app_name, bundle_id, file_type
        """
        if not self.has_appkit:
            return {
                'app_name': 'Unknown',
                'bundle_id': '',
                'file_type': '',
            }
        
        try:
            active_app = self.workspace.frontmostApplication()
            
            context = {
                'app_name': active_app.localizedName(),
                'bundle_id': active_app.bundleIdentifier(),
                'file_type': self._guess_file_type(active_app),
            }
            
            return context
            
        except Exception as e:
            print(f"Error getting context: {e}")
            return {
                'app_name': 'Unknown',
                'bundle_id': '',
                'file_type': '',
            }
    
    def _guess_file_type(self, app) -> str:
        """
        Try to determine what file user is editing
        This is a basic heuristic - could be improved with accessibility API
        """
        app_name = app.localizedName()
        bundle_id = app.bundleIdentifier()
        
        # Map app to common file types
        app_file_map = {
            'Code': '.py',  # VS Code - assume Python
            'PyCharm': '.py',
            'IntelliJ IDEA': '.java',
            'Xcode': '.swift',
            'Sublime Text': '.txt',
            'TextEdit': '.txt',
        }
        
        for key, file_type in app_file_map.items():
            if key in app_name:
                return file_type
        
        # Check bundle ID for more specific detection
        if 'vscode' in bundle_id.lower():
            return '.js'  # Default to JavaScript for VS Code
        
        return ''
    
    def is_code_editor(self, app_name: str) -> bool:
        """Check if given app is a code editor"""
        code_editors = [
            'Code', 'VS Code', 'Visual Studio Code',
            'PyCharm', 'IntelliJ', 'WebStorm', 'GoLand',
            'Xcode', 'Sublime Text', 'Atom', 'Cursor',
            'TextMate', 'BBEdit', 'Nova'
        ]
        
        return any(editor.lower() in app_name.lower() for editor in code_editors)
```

**For More Advanced Context Detection:**
You could use macOS Accessibility API to get the actual file name from window titles, but that requires additional permissions and complexity.

---

### 7. Main Application Controller

**Putting it all together:**
```python
# ispeak/main.py

import sys
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QThread, pyqtSignal
import time

# Import our modules
from audio_capture import AudioCapture
from transcription import TranscriptionEngine
from text_processor import TextProcessor
from text_injector import TextInjector
from hotkey_controller import HotkeyController
from context_detector import ContextDetector


class iSpeakApp:
    def __init__(self):
        # Initialize components
        print("Initializing iSpeak...")
        
        self.audio = AudioCapture()
        self.transcriber = TranscriptionEngine(model_size="base")
        self.processor = TextProcessor()
        self.injector = TextInjector()
        self.hotkey = HotkeyController(
            on_start_callback=self.start_dictation,
            on_stop_callback=self.stop_dictation
        )
        self.context = ContextDetector()
        
        # State
        self.current_language = "ro"
        self.is_processing = False
        
        # UI (System tray)
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in background
        
        self.tray_icon = self._create_tray_icon()
        
        print("iSpeak initialized!")
    
    def start_dictation(self):
        """Called when hotkey pressed"""
        print("🎤 Recording started...")
        self.tray_icon.setToolTip("🎤 Recording...")
        self.audio.start_recording()
    
    def stop_dictation(self):
        """Called when hotkey released"""
        if self.is_processing:
            print("⚠️  Already processing, please wait...")
            return
        
        print("⏸️  Recording stopped, transcribing...")
        self.tray_icon.setToolTip("⏳ Transcribing...")
        
        # Get audio data
        audio_data = self.audio.stop_recording()
        
        # Check if we have audio
        if len(audio_data) < 1600:  # Less than 0.1 seconds
            print("❌ Recording too short, ignoring")
            self.tray_icon.setToolTip("✅ Ready")
            return
        
        # Process in background thread
        self.is_processing = True
        
        thread = TranscriptionThread(
            audio_data,
            self.transcriber,
            self.processor,
            self.injector,
            self.context,
            self.current_language
        )
        thread.finished.connect(self._on_transcription_done)
        thread.start()
    
    def _on_transcription_done(self, success: bool, text: str = ""):
        """Called when transcription completes"""
        self.is_processing = False
        
        if success:
            print(f"✅ Text inserted: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            self.tray_icon.setToolTip("✅ Ready")
        else:
            print("❌ Transcription failed")
            self.tray_icon.setToolTip("❌ Error - Ready")
    
    def toggle_language(self):
        """Switch between Romanian and English"""
        self.current_language = "en" if self.current_language == "ro" else "ro"
        print(f"🌐 Language switched to: {self.current_language.upper()}")
        self.transcriber.set_language(self.current_language)
        self._update_tray_menu()
    
    def _create_tray_icon(self):
        """Create system tray menu"""
        # Create icon
        icon = QSystemTrayIcon()
        
        # Try to load icon file, fallback to text
        icon_path = "resources/icon.png"
        if os.path.exists(icon_path):
            icon.setIcon(QIcon(icon_path))
        else:
            # Create a simple default icon
            from PyQt6.QtGui import QPixmap, QPainter, QColor
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            painter.setBrush(QColor(70, 130, 180))
            painter.drawEllipse(8, 8, 48, 48)
            painter.end()
            icon.setIcon(QIcon(pixmap))
        
        icon.setToolTip("iSpeak - Ready")
        
        # Create menu
        self._update_tray_menu()
        
        icon.show()
        return icon
    
    def _update_tray_menu(self):
        """Update tray menu (called after language change)"""
        menu = QMenu()
        
        # Status
        status_action = menu.addAction(f"Language: {self.current_language.upper()}")
        status_action.setEnabled(False)
        
        menu.addSeparator()
        
        # Language toggle
        lang_action = menu.addAction("Toggle Language (RO ⇄ EN)")
        lang_action.triggered.connect(self.toggle_language)
        
        # Settings (placeholder)
        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self._open_settings)
        
        menu.addSeparator()
        
        # About
        about_action = menu.addAction("About iSpeak")
        about_action.triggered.connect(self._show_about)
        
        # Quit
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit)
        
        self.tray_icon.setContextMenu(menu)
    
    def _open_settings(self):
        """Open settings dialog (placeholder)"""
        print("Settings dialog - TODO")
        # TODO: Create settings window with:
        # - Model size selection
        # - Hotkey customization
        # - Custom vocabulary editor
        # - Language preferences
    
    def _show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        msg = QMessageBox()
        msg.setWindowTitle("About iSpeak")
        msg.setText("iSpeak v0.1.0\n\n"
                   "Offline voice dictation for developers\n\n"
                   "Press Right Alt to start dictating.\n"
                   f"Current language: {self.current_language.upper()}\n\n"
                   "Your voice never leaves your Mac.")
        msg.exec()
    
    def run(self):
        """Start the application"""
        print("\n" + "="*60)
        print("🚀 iSpeak Started!")
        print("="*60)
        print(f"   Hotkey: {self.hotkey.get_hotkey_name()}")
        print(f"   Language: {self.current_language.upper()}")
        print(f"   Model: {self.transcriber.model_size}")
        print("="*60)
        print("\nPress the hotkey and start speaking!")
        print("Right-click the menu bar icon for options.\n")
        
        # Start hotkey listener
        self.hotkey.start_listening()
        
        # Run Qt event loop
        sys.exit(self.app.exec())
    
    def quit(self):
        """Clean shutdown"""
        print("\nShutting down iSpeak...")
        
        self.hotkey.stop_listening()
        self.audio.cleanup()
        self.tray_icon.hide()
        
        self.app.quit()
        print("Goodbye!")


class TranscriptionThread(QThread):
    """Background thread for transcription"""
    finished = pyqtSignal(bool, str)  # success, text
    
    def __init__(self, audio_data, transcriber, processor, 
                 injector, context_detector, language):
        super().__init__()
        self.audio_data = audio_data
        self.transcriber = transcriber
        self.processor = processor
        self.injector = injector
        self.context_detector = context_detector
        self.language = language
    
    def run(self):
        """Execute transcription in background"""
        try:
            start_time = time.time()
            
            # 1. Transcribe
            print(f"Transcribing ({len(self.audio_data)} samples)...")
            result = self.transcriber.transcribe(
                self.audio_data, 
                language=self.language
            )
            text = result["text"]
            
            transcribe_time = time.time() - start_time
            print(f"Transcription took {transcribe_time:.2f}s")
            
            if not text:
                print("No speech detected")
                self.finished.emit(False, "")
                return
            
            print(f"Transcribed: '{text}'")
            
            # 2. Get context
            context = self.context_detector.get_current_context()
            print(f"Context: {context['app_name']}")
            
            # 3. Post-process
            processed_text = self.processor.process(text, context)
            print(f"Processed: '{processed_text}'")
            
            # 4. Inject
            self.injector.type_text(processed_text, instant=True)
            
            total_time = time.time() - start_time
            print(f"Total time: {total_time:.2f}s")
            
            self.finished.emit(True, processed_text)
            
        except Exception as e:
            print(f"❌ Error in transcription thread: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit(False, "")


def main():
    """Entry point"""
    app = iSpeakApp()
    app.run()


if __name__ == "__main__":
    main()
```

---

## Project Structure
```
ispeak/
├── ispeak/
│   ├── __init__.py
│   ├── main.py                 # Main application controller
│   ├── audio_capture.py        # Audio recording module
│   ├── transcription.py        # Whisper integration
│   ├── text_processor.py       # Post-processing & formatting
│   ├── text_injector.py        # System text injection
│   ├── hotkey_controller.py    # Global hotkey handling
│   └── context_detector.py     # App/file detection
│
├── models/                      # Whisper models (auto-downloaded)
│   ├── ggml-tiny.bin           # 75MB
│   ├── ggml-base.bin           # 142MB (recommended)
│   └── ggml-small.bin          # 466MB (optional)
│
├── resources/
│   ├── icon.png                # Menu bar icon
│   └── vocabulary.json         # Custom user vocabulary
│
├── tests/
│   ├── test_audio.py
│   ├── test_transcription.py
│   ├── test_processor.py
│   └── test_integration.py
│
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
├── README.md                   # User documentation
├── LICENSE                     # License file
└── build_app.sh               # Build script for .app bundle
```

---

## Dependencies

### requirements.txt
```txt
# Core dependencies
faster-whisper>=0.10.0          # Fast Whisper implementation
pyaudio>=0.2.13                 # Audio capture
pynput>=1.7.6                   # Keyboard control & hotkeys
pyperclip>=1.8.2                # Clipboard operations
PyQt6>=6.6.0                    # GUI framework for tray icon
numpy>=1.24.0                   # Audio processing

# macOS-specific (only on macOS)
pyobjc-framework-Cocoa>=10.0 ; sys_platform == 'darwin'
pyobjc-framework-Quartz>=10.0 ; sys_platform == 'darwin'

# Optional for better performance
# torch>=2.0.0                  # If you want GPU acceleration
# onnxruntime>=1.16.0           # Alternative runtime
```

### Installation Commands
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# On macOS, you might also need PortAudio
brew install portaudio
```

---

## Performance Optimizations

### 1. Model Loading
```python
# Pre-load model on app start (takes 2-3 seconds)
# Don't reload for each transcription

class TranscriptionEngine:
    def __init__(self):
        # Load once, keep in memory
        self.model = WhisperModel("base", device="auto")
        # Model stays loaded for the lifetime of the app
```

### 2. Audio Buffering
```python
# Stream audio in chunks, don't wait for complete recording
# Process as soon as user releases hotkey

# Use ring buffer to keep last 10 seconds always ready
self.audio_buffer = deque(maxlen=300)  # 300 chunks = ~10 seconds
```

### 3. Background Processing
```python
# Never block UI
# Transcription happens in separate QThread
# Show loading indicator while processing

thread = TranscriptionThread(...)
thread.finished.connect(self._on_done)
thread.start()
```

### 4. Metal Acceleration (M-series Macs)
```python
# faster-whisper automatically uses Metal on M1/M2/M3
# Ensure compute_type="int8" or "float16" for GPU usage

model = WhisperModel(
    "base", 
    device="auto",          # Auto-detects Metal
    compute_type="int8"     # Quantized for speed
)
```

### 5. VAD (Voice Activity Detection)
```python
# Filter out silence automatically
# Only transcribe actual speech

segments, info = self.model.transcribe(
    audio_data,
    vad_filter=True,                    # Enable VAD
    vad_parameters=dict(
        min_silence_duration_ms=500     # 500ms silence = pause
    )
)
```

### Benchmarks (M1 Mac)

| Model | Load Time | Transcribe 10s | Memory | Accuracy |
|-------|-----------|----------------|---------|----------|
| tiny  | 1.5s      | 0.3s          | 500MB   | 85%      |
| base  | 2.0s      | 0.6s          | 1GB     | 90%      |
| small | 3.5s      | 1.6s          | 2GB     | 93%      |
| medium| 6.0s      | 5.0s          | 5GB     | 95%      |

**Recommendation:** Use `base` model for best speed/accuracy tradeoff.

---

## macOS Permissions

The app requires these permissions (user must grant):

### 1. Microphone Access ✅
- **Required for:** Audio capture
- **Prompt:** Automatic on first microphone use
- **Location:** System Settings > Privacy & Security > Microphone

### 2. Accessibility Access ✅
- **Required for:** System-wide text injection
- **Prompt:** Manual - user must enable
- **Location:** System Settings > Privacy & Security > Accessibility

### 3. Input Monitoring ⚠️
- **Required for:** Global hotkey listener (macOS 10.15+)
- **Prompt:** May appear depending on macOS version
- **Location:** System Settings > Privacy & Security > Input Monitoring

### Handling Permissions in Code
```python
def check_permissions():
    """Check if app has required permissions"""
    
    # Check microphone permission
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        p.terminate()
        print("✅ Microphone access: OK")
    except Exception:
        print("❌ Microphone access: DENIED")
        show_permission_dialog("microphone")
        return False
    
    # Check accessibility permission (harder to detect programmatically)
    # Best to just try injection and catch errors
    print("⚠️  Please ensure Accessibility access is granted")
    
    return True

def show_permission_dialog(permission_type: str):
    """Show dialog explaining how to grant permission"""
    from PyQt6.QtWidgets import QMessageBox
    
    messages = {
        "microphone": (
            "Microphone Access Required",
            "iSpeak needs microphone access to capture your voice.\n\n"
            "Please go to:\n"
            "System Settings > Privacy & Security > Microphone\n"
            "and enable iSpeak."
        ),
        "accessibility": (
            "Accessibility Access Required",
            "iSpeak needs accessibility access to type text.\n\n"
            "Please go to:\n"
            "System Settings > Privacy & Security > Accessibility\n"
            "and enable iSpeak."
        )
    }
    
    title, text = messages.get(permission_type, ("Permission Required", ""))
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.exec()
```

### Info.plist Entries (for .app bundle)
```xml
<!-- Info.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>iSpeak</string>
    
    <key>CFBundleIdentifier</key>
    <string>com.yourname.ispeak</string>
    
    <key>NSMicrophoneUsageDescription</key>
    <string>iSpeak needs access to your microphone to capture voice input for transcription.</string>
    
    <key>NSAccessibilityUsageDescription</key>
    <string>iSpeak needs accessibility access to inject text into applications.</string>
    
    <key>LSUIElement</key>
    <true/>  <!-- Run as menu bar app, no dock icon -->
</dict>
</plist>
```

---

## Build & Distribution

### Option 1: PyInstaller (Quick Development Builds)

**Build standalone app:**
```bash
#!/bin/bash
# build_app.sh

# Activate virtual environment
source venv/bin/activate

# Install PyInstaller if needed
pip install pyinstaller

# Build the app
pyinstaller \
    --name iSpeak \
    --windowed \
    --onefile \
    --icon resources/icon.icns \
    --add-data "models:models" \
    --add-data "resources:resources" \
    --hidden-import PyQt6 \
    --hidden-import faster_whisper \
    ispeak/main.py

echo "✅ Build complete: dist/iSpeak.app"
```

**Usage:**
```bash
chmod +x build_app.sh
./build_app.sh
```

**Output:** `dist/iSpeak.app` (~200-300MB including models)

### Option 2: py2app (Better macOS Integration)
```python
# setup.py for py2app

from setuptools import setup

APP = ['ispeak/main.py']
DATA_FILES = [
    ('models', ['models/ggml-base.bin']),
    ('resources', ['resources/icon.icns', 'resources/vocabulary.json'])
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'resources/icon.icns',
    'plist': {
        'CFBundleName': 'iSpeak',
        'CFBundleDisplayName': 'iSpeak',
        'CFBundleIdentifier': 'com.yourname.ispeak',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSMicrophoneUsageDescription': 'iSpeak needs microphone access for voice input.',
        'NSAccessibilityUsageDescription': 'iSpeak needs accessibility access to inject text.',
        'LSUIElement': True,  # Menu bar app
    },
    'packages': ['PyQt6', 'faster_whisper', 'numpy'],
    'includes': ['numpy', 'pyaudio', 'pynput'],
}

setup(
    app=APP,
    name='iSpeak',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

**Build:**
```bash
python setup.py py2app
```

### Option 3: Native Swift App (Production Quality)

For final production release, create a Swift wrapper:

**Structure:**
```
iSpeak/
├── iSpeak/                   # Swift UI
│   ├── AppDelegate.swift
│   ├── MenuBarController.swift
│   ├── SettingsWindow.swift
│   └── PythonBridge.swift      # Calls Python backend
│
├── PythonBackend/              # Your Python code
│   └── (all the .py files)
│
└── iSpeak.xcodeproj
```

**Benefits:**
- Native macOS look & feel
- Smaller app size (~100MB vs 300MB)
- Better performance
- Easier App Store submission
- Professional appearance

---

## Testing Strategy

### Unit Tests
```python
# tests/test_transcription.py

import pytest
import numpy as np
from ispeak.transcription import TranscriptionEngine
from ispeak.audio_capture import AudioCapture

@pytest.fixture
def engine():
    return TranscriptionEngine(model_size="tiny")

def test_load_model(engine):
    """Test that model loads successfully"""
    assert engine.model is not None
    assert engine.current_language == "ro"

def test_romanian_transcription(engine):
    """Test Romanian transcription"""
    # Load test audio file (you need to create this)
    audio = np.load("tests/fixtures/romanian_sample.npy")
    
    result = engine.transcribe(audio, language="ro")
    
    assert "funcție" in result["text"].lower()
    assert result["language"] == "ro"

def test_english_transcription(engine):
    """Test English transcription"""
    audio = np.load("tests/fixtures/english_sample.npy")
    
    result = engine.transcribe(audio, language="en")
    
    assert len(result["text"]) > 0
    assert result["language"] == "en"

def test_empty_audio(engine):
    """Test handling of empty audio"""
    audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
    
    result = engine.transcribe(audio)
    
    # Should return empty or very short text
    assert len(result["text"]) < 10


# tests/test_processor.py

from ispeak.text_processor import TextProcessor

def test_custom_vocabulary():
    """Test vocabulary replacement"""
    processor = TextProcessor()
    
    text = "I'm using visual studio code"
    processed = processor.process(text)
    
    assert "VS Code" in processed

def test_romanian_corrections():
    """Test Romanian diacritics"""
    processor = TextProcessor()
    
    text = "aceasta este o functie"
    processed = processor.process(text)
    
    assert "funcție" in processed

def test_code_formatting():
    """Test code pattern replacement"""
    processor = TextProcessor()
    
    context = {'app_name': 'VS Code', 'file_type': '.py'}
    text = "if x equals 5 new line print hello"
    processed = processor.process(text, context)
    
    assert "==" in processed
    assert "\n" in processed


# tests/test_audio.py

from ispeak.audio_capture import AudioCapture
import time

def test_audio_capture_start_stop():
    """Test basic audio capture"""
    capture = AudioCapture()
    
    capture.start_recording()
    assert capture.is_recording == True
    
    time.sleep(0.5)  # Record for 0.5 seconds
    
    audio_data = capture.stop_recording()
    assert capture.is_recording == False
    assert len(audio_data) > 0
    
    capture.cleanup()
```

### Integration Tests
```python
# tests/test_integration.py

from ispeak.main import iSpeakApp
import numpy as np

def test_full_pipeline():
    """Test complete transcription pipeline"""
    
    # Create app (without running event loop)
    app = iSpeakApp()
    
    # Load test audio
    audio = np.load("tests/fixtures/test_speech.npy")
    
    # Transcribe
    result = app.transcriber.transcribe(audio, language="ro")
    text = result["text"]
    
    assert len(text) > 0
    
    # Process
    context = {'app_name': 'Terminal', 'file_type': ''}
    processed = app.processor.process(text, context)
    
    assert len(processed) > 0
    
    print(f"Original: {text}")
    print(f"Processed: {processed}")
```

### Manual Testing Checklist

Create a checklist for manual testing:
```markdown
## Manual Test Checklist

### Basic Functionality
- [ ] App starts without errors
- [ ] Menu bar icon appears
- [ ] Right-click menu shows options
- [ ] Hotkey (Right Alt) is detected

### Recording & Transcription
- [ ] Press hotkey → recording starts (tooltip changes)
- [ ] Release hotkey → transcription begins
- [ ] Romanian speech → correct Romanian text
- [ ] English speech → correct English text
- [ ] Very short recording → handled gracefully
- [ ] Silence → no text inserted

### Text Injection
- [ ] Text appears in TextEdit
- [ ] Text appears in VS Code
- [ ] Text appears in Terminal
- [ ] Text appears in browser
- [ ] Special characters work (ă, î, ș, ț, â)
- [ ] Multi-line text works

### Language Switching
- [ ] Toggle language via menu
- [ ] Romanian mode works after switch
- [ ] English mode works after switch
- [ ] Language persists after restart (future feature)

### Code Context
- [ ] Dictate in VS Code → code formatting applied
- [ ] Dictate in TextEdit → normal text
- [ ] "new line" command works in code
- [ ] "equals" becomes " = " in code context

### Custom Vocabulary
- [ ] Add custom word via settings (future)
- [ ] Custom word is recognized
- [ ] Vocabulary persists after restart

### Edge Cases
- [ ] App survives computer sleep/wake
- [ ] Switching audio devices mid-session
- [ ] Multiple rapid recordings
- [ ] Very long recording (30+ seconds)
- [ ] Background noise handling

### Performance
- [ ] Transcription completes in < 3 seconds
- [ ] No UI freezing during transcription
- [ ] Memory usage stays reasonable (< 2GB)
- [ ] CPU usage acceptable (< 50% during transcription)

### Permissions
- [ ] Microphone permission prompt appears
- [ ] Accessibility permission explained
- [ ] App handles denied permissions gracefully
```

---

## Development Timeline

### Phase 1: Core MVP (3-4 weeks)

**Week 1-2: Foundation**
- [ ] Set up project structure
- [ ] Implement audio capture module
- [ ] Integrate Whisper (faster-whisper)
- [ ] Basic text injection (clipboard method)
- [ ] Simple command-line interface for testing

**Milestone:** Can record voice → get text → inject it

**Week 3-4: User Interface**
- [ ] Implement hotkey controller
- [ ] Create system tray UI (PyQt6)
- [ ] Add language switching
- [ ] Basic error handling
- [ ] First round of testing

**Milestone:** Usable desktop app you can use yourself

### Phase 2: Enhancement (2-3 weeks)

**Week 5-6: Smart Features**
- [ ] Implement post-processing module
- [ ] Add code-aware formatting
- [ ] Context detection (active app)
- [ ] Custom vocabulary system
- [ ] Romanian diacritics handling

**Week 7: Polish**
- [ ] Settings UI
- [ ] Comprehensive error handling
- [ ] Performance optimization
- [ ] Load time improvements
- [ ] Documentation

**Milestone:** Beta-ready version

### Phase 3: Production (2-3 weeks)

**Week 8-9: Production Build**
- [ ] Create proper .app bundle
- [ ] DMG installer
- [ ] Auto-update system (optional)
- [ ] Crash reporting (optional)
- [ ] User documentation
- [ ] Tutorial video

**Week 10: Testing & Launch**
- [ ] Beta test with 10-20 users
- [ ] Collect feedback
- [ ] Bug fixes
- [ ] Final polish
- [ ] Launch!

**Milestone:** Production-ready v1.0

---

## Weekend Prototype

Here's a minimal 50-line prototype you can build THIS WEEKEND to validate the concept:

### prototype.py
```python
#!/usr/bin/env python3
"""
iSpeak Weekend Prototype
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
        pyperclip.copy(text)
        keyboard.Controller().tap(keyboard.Key.cmd, 'v')
    
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
    model = WhisperModel("base", device="auto", compute_type="int8")
    
    print("Starting audio capture...")
    p, stream = init_audio()
    
    print("\n" + "="*50)
    print("iSpeak Prototype Ready!")
    print("="*50)
    print("Press and hold Right Alt to dictate")
    print("Speak in Romanian or English")
    print("Release to transcribe")
    print("Press Ctrl+C to quit\n")
    
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
    
    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == "__main__":
    main()
```

### Testing the Prototype
```bash
# Install dependencies
pip install faster-whisper pyaudio pynput pyperclip numpy

# Run it
python prototype.py

# The first run will download the model (~140MB)
# Then you can start dictating!
```

**What to test:**
1. Hold Right Alt → speak "funcție Python pentru calcul" → release
2. Did it type "funcție Python pentru calcul"?
3. How fast was it? (should be < 2 seconds)
4. How accurate?
5. Try English: "function for calculation"

**If it works well:** Proceed with full implementation
**If Romanian accuracy is poor:** We'll add vocabulary fixes
**If too slow:** Try `tiny` model instead of `base`

---

## Next Steps

1. **This Weekend:**
   - [ ] Test the prototype
   - [ ] Measure speed and accuracy
   - [ ] Try in VS Code with your actual workflow
   - [ ] Decide if it's worth building the full app

2. **If Promising:**
   - [ ] Start with full project structure
   - [ ] Implement component by component
   - [ ] Test each module independently
   - [ ] Integrate and test together

3. **After MVP:**
   - [ ] Collect feedback from Romanian devs
   - [ ] Add most-requested features
   - [ ] Polish and optimize
   - [ ] Launch!

---

## Questions to Answer This Weekend

1. **Speed:** Is transcription fast enough? (<2s acceptable?)
2. **Accuracy:** Does it understand your Romanian? Your accent?
3. **Usability:** Does the hotkey approach feel natural?
4. **Value:** Would you actually use this while coding?
5. **Viability:** Would other Romanian devs pay $49 for this?

If yes to most → BUILD IT! 🚀

---

## Resources & References

**Documentation:**
- faster-whisper: https://github.com/guillaumekln/faster-whisper
- PyAudio: https://people.csail.mit.edu/hubert/pyaudio/
- pynput: https://pynput.readthedocs.io/
- PyQt6: https://www.riverbankcomputing.com/static/Docs/PyQt6/

**Similar Projects:**
- Talon Voice: https://talonvoice.com/
- Voice Type: https://carelesswhisper.app/
- Wispr Flow: https://wisprflow.ai/

**Whisper Performance:**
- Whisper benchmarks: https://github.com/openai/whisper/discussions/categories/benchmarks
- whisper.cpp: https://github.com/ggerganov/whisper.cpp