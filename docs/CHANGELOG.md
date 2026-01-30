# iSpeak Changelog

## [Unreleased] - 2024-12-27

### Fixed
- **Signal connection not working** - Made iSpeakApp inherit from QObject for proper Qt signal handling
- **Callback never called** - Added @pyqtSlot decorator for thread-safe signal connections
- **Hotkey listener hang after text injection** - Added 100ms QTimer delay to prevent keyboard simulation interference
- **Threading hang on second dictation** - Moved text injection from background thread to main thread
- **Processing flag not reset** - Ensured `is_processing` resets before text injection
- **QThread destruction crash** - Added proper thread lifecycle management
- **Resource leaks** - Added thread cleanup and signal handlers
- **Menu initialization crash** - Fixed menu creation order

### Changed
- **Upgraded default model from "base" to "small"** - Significantly better Romanian accuracy
- iSpeakApp now inherits from QObject for proper Qt integration
- Text injection delayed by 100ms using QTimer to avoid hotkey conflicts
- Processing flag resets immediately, text injection happens asynchronously
- Improved error handling in text injection
- Better error messages for short recordings
- Added comprehensive debug logging
- **Enhanced Romanian diacritics correction** - Added 30+ common programming terms
- **Expanded vocabulary.json** - Added Romanian tech term pronunciations

### Added
- Signal handlers for graceful Ctrl+C shutdown
- Thread cleanup on application quit
- Language detection logging - Shows requested vs detected language
- Manual language toggle in menu (RO ⇄ EN)
- **Auto-Press Enter toggle** - Automatically press Enter after dictation (perfect for chat apps)
- **Model selector in system tray menu** - Switch between tiny/base/small/medium/large models
- **Automatic model download with progress** - Downloads models on-demand with status updates
- **Current model display** - Shows active model in menu bar
- `USAGE_TIPS.md` - Comprehensive usage guide
- `SETUP_COMPLETE.md` - Installation summary
- `IMPORTANT_PYTHON_VERSION.md` - Python architecture notes
- `LANGUAGE_TIPS.md` - Language switching and detection guide
- **`ROMANIAN_TIPS.md` - Complete guide for Romanian language optimization**
- **`ROMANIAN_IMPROVEMENTS.md` - Summary of Romanian enhancements**
- **`MODEL_SELECTION.md` - Guide for choosing and switching models**
- **`FUTURE_FEATURES.md` - Planned features and roadmap**
- `fix_pyaudio.sh` - Automated PyAudio fix script

## [0.1.0] - Initial Implementation

### Added
- Core audio capture module
- Whisper integration for speech-to-text
- Text post-processing with Romanian support
- System-wide text injection
- Global hotkey controller (Right Alt)
- Context detection for code-aware formatting
- PyQt6 system tray application
- Weekend prototype for quick testing
- Comprehensive documentation

### Features
- 100% offline processing
- Multi-language support (Romanian, English)
- Code-aware text formatting
- Custom vocabulary system
- Apple Silicon optimization
