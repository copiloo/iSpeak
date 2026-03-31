# iSpeak

Cross-platform voice-to-text dictation app powered by faster-whisper and native OS integrations.

## Platforms

| Branch | Platform | Stack |
|---|---|---|
| `platform/windows` | Windows 10/11 | Python, PyQt6, faster-whisper, pynput |
| `platform/macos` | macOS | Python, PyQt6, faster-whisper, pynput |
| `platform/swift` | macOS (native) | Swift, SwiftUI |

## Features

- Offline transcription (no cloud, no API key)
- Global hotkey (Right Alt) to start/stop dictation
- Pastes transcribed text into any focused window
- System tray icon with settings dialog

