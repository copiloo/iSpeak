# Quick Start Guide

Get VoiceDev running in under 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.8+)
python3 --version

# Check if Homebrew is installed
brew --version

# If not, install Homebrew first:
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Installation (5 Steps)

### 1. Install PortAudio

```bash
brew install portaudio
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Set compiler flags for PyAudio (important!)
export CFLAGS="-I/opt/homebrew/include"
export LDFLAGS="-L/opt/homebrew/lib"

# For Intel Macs, use instead:
# export CFLAGS="-I/usr/local/include"
# export LDFLAGS="-L/usr/local/lib"

# Install dependencies
pip install -r requirements.txt
```

This will take a few minutes. Grab a coffee! ☕

**If you get PyAudio errors:**
```bash
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir pyaudio
pip install -r requirements.txt
```

### 4. Test with Prototype

```bash
python prototype.py
```

**First run:** The Whisper model (~140MB) will download. This only happens once.

**When you see:** "VoiceDev Prototype Ready!"
1. Press and hold **Right Alt** key
2. Speak: "acesta este un test" (Romanian) or "this is a test" (English)
3. Release the key
4. Watch the magic happen! ✨

If text appears, you're good to go!

### 5. Run Full Application

```bash
./run.sh
```

Or manually:

```bash
cd voicedev
python main.py
```

## First Use

### Grant Permissions (Important!)

The first time you run VoiceDev, macOS will ask for permissions:

1. **Microphone** - Allow (appears automatically)
2. **Accessibility** - Go to System Settings > Privacy & Security > Accessibility
   - Click the lock icon
   - Add Terminal (or Python)
   - Enable it
3. **Input Monitoring** - May appear automatically, click Allow

Without these permissions, VoiceDev won't work!

### Using VoiceDev

1. Look for the VoiceDev icon in your menu bar
2. Open any application (TextEdit, VS Code, Terminal, etc.)
3. Click where you want text to appear
4. Press and hold **Right Alt**
5. Speak clearly in Romanian or English
6. Release **Right Alt**
7. Text appears at your cursor!

### Switching Languages

Right-click the menu bar icon > "Toggle Language (RO ⇄ EN)"

## Common First-Run Issues

### "PyAudio could not find PortAudio"

```bash
brew install portaudio
pip uninstall pyaudio
pip install --no-cache-dir pyaudio
```

### Text not appearing

1. Check Accessibility permissions (most common issue!)
2. Click in the target app first
3. Make sure you're releasing the hotkey

### "ModuleNotFoundError"

Make sure virtual environment is activated:

```bash
source venv/bin/activate
```

### Model download fails

1. Check internet connection
2. Try again - downloads can be slow
3. Model is cached in `./models/` directory

## What to Try

### Test Romanian
Press Right Alt and say:
- "funcție pentru calcul"
- "aceasta este o variabilă"
- "clasa pentru procesare"

### Test English
Press Right Alt and say:
- "function for calculation"
- "this is a variable"
- "class for processing"

### Test in VS Code
Open a Python file and try:
- "def main new line print hello world"
- "if x equals 5 new line return true"

## Performance Tips

### If transcription is slow

Edit `voicedev/transcription.py`, line 23:
```python
self.model = WhisperModel(
    "tiny",  # Change from "base" to "tiny"
    ...
```

Tiny model is 4x faster but slightly less accurate.

### If accuracy is poor

Edit `voicedev/transcription.py`, line 23:
```python
self.model = WhisperModel(
    "small",  # Change from "base" to "small"
    ...
```

Small model is slower but more accurate.

## Next Steps

1. Read [README.md](README.md) for full documentation
2. Customize [resources/vocabulary.json](resources/vocabulary.json)
3. Try in different applications
4. Report bugs or suggestions!

## Getting Help

- Check [INSTALL.md](INSTALL.md) for detailed installation guide
- Check [README.md](README.md) for troubleshooting
- Open an issue on GitHub
- Check the logs in the terminal

## Building Standalone App

Once everything works, create a standalone app:

```bash
./build_app.sh
```

The app will be at `dist/VoiceDev.app` - double-click to run!

---

**Questions?** Check the documentation or open an issue!

**Working?** Give us a star on GitHub! ⭐
