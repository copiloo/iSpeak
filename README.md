# iSpeak

**Offline voice dictation for macOS developers**

iSpeak is a privacy-first voice-to-text application that runs 100% offline on your Mac. Perfect for developers who want to dictate code and documentation in Romanian or English without sending any data to the cloud.

## Features

- 🎤 **Offline Processing** - All transcription happens locally on your Mac
- 🇷🇴 **Romanian Support** - First-class support for Romanian language with diacritics
- 🌍 **Multi-language** - Switch between Romanian and English on the fly
- ⚡️ **Fast** - Optimized for Apple Silicon (M1/M2/M3)
- 🔒 **Private** - Your voice never leaves your machine
- 💻 **Code-aware** - Smart formatting when working in code editors
- 🎯 **System-wide** - Works in any application on your Mac

## Quick Start

### Weekend Prototype (Test First!)

Before installing the full application, test the concept with the minimal prototype:

```bash
# Install dependencies
pip install faster-whisper pyaudio pynput pyperclip numpy

# On macOS, you might need PortAudio
brew install portaudio

# Run the prototype
python prototype.py
```

**Usage:**
1. The first run will download the Whisper model (~140MB)
2. Press and hold **Right Alt** key
3. Speak in Romanian or English
4. Release the key
5. Watch the text appear!

### Full Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd iSpeak
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   cd ispeak
   python main.py
   ```

## macOS Permissions

iSpeak requires the following permissions:

### 1. Microphone Access
- **Required for:** Audio capture
- **Location:** System Settings > Privacy & Security > Microphone
- The system will prompt you automatically on first use

### 2. Accessibility Access
- **Required for:** System-wide text injection
- **Location:** System Settings > Privacy & Security > Accessibility
- You must manually enable iSpeak or Python/Terminal

### 3. Input Monitoring
- **Required for:** Global hotkey listener
- **Location:** System Settings > Privacy & Security > Input Monitoring
- May appear depending on your macOS version

## Usage

### Basic Operation

1. **Start the app:** Run `python main.py` in the `ispeak` directory
2. **Activate dictation:** Press and hold **Right Alt** (or your configured hotkey)
3. **Speak:** Say what you want to type
4. **Release:** Let go of the hotkey
5. **Text appears:** The transcribed text will be inserted at your cursor

### System Tray Menu

Right-click the menu bar icon to:
- See current language (RO or EN)
- Toggle between Romanian and English
- Access settings (coming soon)
- View about information
- Quit the application

### Language Switching

- Click **Toggle Language (RO ⇄ EN)** in the menu
- The current language is displayed in the status
- Switch anytime to match what you're about to dictate

### Code-Aware Features

When dictating in a code editor (VS Code, PyCharm, etc.), iSpeak recognizes voice commands:

- "new line" → `\n`
- "tab" → `\t`
- "equals" → ` = `
- "open brace" → ` {`
- "arrow" → ` => `
- And many more...

### Custom Vocabulary

Edit `resources/vocabulary.json` to add your own word replacements:

```json
{
  "git hub": "GitHub",
  "my custom term": "MyCustomTerm"
}
```

## Project Structure

```
iSpeak/
├── ispeak/                # Main application code
│   ├── main.py            # Application entry point
│   ├── audio_capture.py   # Audio recording
│   ├── transcription.py   # Whisper integration
│   ├── text_processor.py  # Post-processing
│   ├── text_injector.py   # Text injection
│   ├── hotkey_controller.py  # Hotkey handling
│   └── context_detector.py   # App detection
│
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    # Technical architecture
│   ├── INSTALL.md         # Installation guide
│   ├── QUICKSTART.md      # Quick start guide
│   └── PROJECT_STATUS.md  # Project status
│
├── models/                # Whisper models (auto-downloaded)
├── resources/             # Icons and vocabulary
├── tests/                 # Unit tests
├── prototype.py           # Weekend prototype
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Performance

### Benchmarks (M1 Mac)

| Model  | Load Time | Transcribe 10s | Memory | Accuracy |
|--------|-----------|----------------|---------|----------|
| tiny   | 1.5s      | 0.3s           | 500MB   | 85%      |
| base   | 2.0s      | 0.6s           | 1GB     | 90%      |
| small  | 3.5s      | 1.6s           | 2GB     | 93%      |
| medium | 6.0s      | 5.0s           | 5GB     | 95%      |

**Recommended:** Use the `base` model (default) for the best speed/accuracy balance.

## Troubleshooting

### Microphone not working
- Check System Settings > Privacy & Security > Microphone
- Make sure iSpeak (or Python/Terminal) is enabled

### Text not appearing
- Check System Settings > Privacy & Security > Accessibility
- Enable iSpeak (or Python/Terminal)
- Try the clipboard paste method (default)

### Hotkey not responding
- Make sure Right Alt key is working
- Check System Settings > Privacy & Security > Input Monitoring
- Try a different hotkey in settings (future feature)

### Romanian diacritics not showing
- The text processor should handle this automatically
- Check `resources/vocabulary.json` for custom corrections
- Report issues so we can improve the vocabulary

### Slow transcription
- Try the `tiny` model: Edit `main.py` and change `model_size="tiny"`
- Close other heavy applications
- Ensure you're using Apple Silicon Mac for best performance

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest tests/
```

### Building for Distribution

```bash
# Install PyInstaller
pip install pyinstaller

# Build the app
./build_app.sh
```

The app will be created in `dist/iSpeak.app`.

## Roadmap

### Phase 1: Core MVP ✅
- [x] Audio capture
- [x] Whisper integration
- [x] Text injection
- [x] Hotkey controller
- [x] System tray UI
- [x] Language switching

### Phase 2: Enhancement
- [ ] Settings UI
- [ ] Custom hotkey configuration
- [ ] Vocabulary editor
- [x] Model size selector ✅
- [ ] Performance optimizations

### Phase 3: Production
- [ ] .app bundle with installer
- [ ] DMG distribution
- [ ] Auto-update system
- [ ] User documentation
- [ ] Beta testing

## Documentation

### Getting Started
- 📖 [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- 📦 [Installation Guide](docs/INSTALL.md) - Detailed installation steps
- ✅ [Setup Complete](docs/SETUP_COMPLETE.md) - Post-installation summary
- 💡 [Usage Tips](docs/USAGE_TIPS.md) - How to use iSpeak effectively

### Language & Models
- 🌍 [Language Tips](docs/LANGUAGE_TIPS.md) - Language switching and detection
- 🇷🇴 [Romanian Tips](docs/ROMANIAN_TIPS.md) - Romanian language optimization
- 📊 [Romanian Improvements](docs/ROMANIAN_IMPROVEMENTS.md) - Summary of Romanian enhancements
- 🔧 [Model Selection](docs/MODEL_SELECTION.md) - Choosing and switching Whisper models

### Technical
- 🏗️ [Architecture](docs/ARCHITECTURE.md) - Technical architecture details
- 📊 [Project Status](docs/PROJECT_STATUS.md) - Current status and roadmap
- 🔄 [Changelog](docs/CHANGELOG.md) - Version history and changes
- 🐍 [Python Version Notes](docs/IMPORTANT_PYTHON_VERSION.md) - Python architecture issues
- 🚀 [Future Features](docs/FUTURE_FEATURES.md) - Planned features and roadmap

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details

## Privacy

iSpeak is designed with privacy as the top priority:

- ✅ All processing happens locally on your Mac
- ✅ No data is sent to any server
- ✅ No internet connection required (after initial model download)
- ✅ No analytics or tracking
- ✅ No account or registration needed

Your voice recordings are processed in memory and immediately discarded after transcription.

## Support

- **Issues:** Report bugs and request features on GitHub Issues
- **Questions:** Start a discussion in GitHub Discussions
- **Email:** [Your contact email]

## Acknowledgments

- Built with [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- Uses OpenAI's [Whisper](https://github.com/openai/whisper) models
- Inspired by [Talon Voice](https://talonvoice.com/) and similar tools

---

Made with ❤️ for Romanian developers who want to code faster
