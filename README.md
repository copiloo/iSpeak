# iSpeak - Swift Native Version

> Offline voice dictation for macOS developers - Native Swift rewrite

## Overview

This is a native Swift rewrite of iSpeak, a voice-to-text dictation app optimized for developers working with Romanian and English languages. The Swift version provides:

- **True standalone app** (~50MB vs ~500MB Python bundle)
- **App Store compatibility** (sandboxed architecture)
- **Better performance** (native macOS integration)
- **Simpler distribution** (no complex packaging)

## Status

**Current Phase:** ✅ Phase 1 Complete - Project Setup & Foundation

**Working Features:**
- ✅ Menu bar app with system tray icon
- ✅ Language selection (English/Romanian)
- ✅ Model selection (6 Whisper model sizes)
- ✅ Auto-press Enter toggle
- ✅ Sandboxed, App Store-compatible configuration

**In Development:**
- Phase 2: Audio Capture (AVFoundation)
- Phase 3: WhisperKit Transcription
- Phase 4: Hotkey System (Right Option key)
- Phases 5-11: Text Processing, Injection, UI, Testing

## Requirements

- **macOS:** 14.0+ (Sonoma or later)
- **Xcode:** 15.0+
- **Architecture:** Apple Silicon (ARM64) or Intel

## Building

1. Open `iSpeak.xcodeproj` in Xcode
2. Wait for WhisperKit package to resolve
3. Build and run (⌘R)

The app will appear as a microphone icon in your menu bar.

## Architecture

**Technology Stack:**
- **UI:** SwiftUI + AppKit (menu bar only)
- **Transcription:** WhisperKit (CoreML-optimized for Apple Silicon)
- **Audio:** AVFoundation (native recording)
- **Hotkeys:** CGEventTap (sandboxable)
- **Text Injection:** CGEvent + NSPasteboard (clipboard-based)
- **State Management:** Swift Observation framework

**Project Structure:**
```
iSpeak/
├── App/
│   ├── iSpeakApp.swift          # @main entry point
│   ├── AppDelegate.swift         # Lifecycle
│   └── AppCoordinator.swift      # State (Phase 9)
├── UI/
│   ├── MenuBar/                  # ✅ Menu bar interface
│   ├── Overlay/                  # Phase 8: Visual feedback
│   └── Settings/                 # Phase 10: Settings window
├── Services/
│   ├── Audio/                    # Phase 2: Recording
│   ├── Transcription/            # Phase 3: WhisperKit
│   ├── TextProcessing/           # Phase 5: Romanian corrections
│   ├── TextInjection/            # Phase 6: Clipboard paste
│   └── Context/                  # Phase 7: App detection
├── Hotkeys/                      # Phase 4: Global hotkeys
├── Models/                       # Data models
└── Resources/                    # Icons, dictionaries
```

## Implementation Plan

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for detailed phase breakdown.

**Total Estimated Time:** ~204 hours (6 weeks full-time)

## Key Features (Target)

- **Multi-language:** English + Romanian with diacritics support
- **6 Whisper Models:** Tiny, Base, Small, Medium, Large, Large-v3-Turbo
- **Code-aware:** Special formatting for programming terms
- **Custom Vocabulary:** User-defined word replacements
- **Offline:** No internet required (models stored locally)
- **Privacy-first:** Sandboxed, no telemetry

## Python Version

The original Python version is maintained separately at `../iSpeak/`. It remains functional via a launcher script (`iSpeak.app`).

## License

MIT License - See LICENSE file for details

## Development

**Current Branch:** main
**Phase 1 Complete:** 2026-02-06

---

*Built with Swift, WhisperKit, and ❤️ for developers*
