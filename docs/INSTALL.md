# Installation Guide

## Prerequisites

- macOS 10.15 or later
- Python 3.8 or later
- Homebrew (for PortAudio)

## Step-by-Step Installation

### 1. Install PortAudio with Development Headers

PortAudio is required for microphone access. You need both the library and development headers:

```bash
# Install PortAudio
brew install portaudio

# Verify installation
brew info portaudio
```

### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd voiceDev
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

**Option A: Install with proper compiler flags (Recommended)**

```bash
# Set compiler flags for PyAudio
export CFLAGS="-I/opt/homebrew/include"
export LDFLAGS="-L/opt/homebrew/lib"

# For Intel Macs, use:
# export CFLAGS="-I/usr/local/include"
# export LDFLAGS="-L/usr/local/lib"

# Install dependencies
pip install -r requirements.txt
```

**Option B: Install PyAudio separately first**

If the above doesn't work, try installing PyAudio separately:

```bash
# Upgrade pip and setuptools first
pip install --upgrade pip setuptools wheel

# Install PyAudio with no cache
pip install --no-cache-dir pyaudio

# Then install remaining dependencies
pip install -r requirements.txt
```

**Note:** The first time you run VoiceDev, it will download the Whisper model (~140MB for the base model). This only happens once.

### 5. Grant Permissions

#### Microphone Access
- Go to **System Settings > Privacy & Security > Microphone**
- Enable access for Terminal or Python

#### Accessibility Access (Required!)
- Go to **System Settings > Privacy & Security > Accessibility**
- Click the lock icon to make changes
- Click the **+** button
- Add Terminal or Python
- Alternatively, run the app first and it will guide you

#### Input Monitoring
- Go to **System Settings > Privacy & Security > Input Monitoring**
- Enable access for Terminal or Python

### 6. Test with Prototype

Before running the full app, test with the simple prototype:

```bash
python prototype.py
```

1. Wait for "VoiceDev Prototype Ready!" message
2. Press and hold Right Alt
3. Speak: "acesta este un test"
4. Release Right Alt
5. The text should appear!

If this works, proceed to the full app.

### 7. Run Full Application

```bash
cd voicedev
python main.py
```

The app will:
1. Load the Whisper model (takes 2-3 seconds)
2. Start the system tray icon
3. Start listening for the hotkey

Look for the VoiceDev icon in your menu bar!

## Troubleshooting

### "PyAudio could not find PortAudio"

```bash
brew install portaudio
pip uninstall pyaudio
pip install --no-cache-dir pyaudio
```

### "AppKit module not found"

```bash
pip install pyobjc-framework-Cocoa
```

### "Permission denied" when running build_app.sh

```bash
chmod +x build_app.sh
```

### Models downloading slowly

The Whisper models are downloaded from Hugging Face. If the download is slow:
1. Wait patiently (it's a one-time download)
2. Check your internet connection
3. Models are cached in `./models/` directory

### Text not appearing in applications

1. Make sure Accessibility permissions are granted
2. Try clicking in the target application before dictating
3. Check that you're releasing the hotkey (Right Alt)

## Building Standalone App

To create a standalone .app bundle:

```bash
./build_app.sh
```

The app will be created at `dist/VoiceDev.app`.

## Uninstalling

1. Delete the project folder
2. Remove permissions from System Settings if desired
3. Delete the virtual environment: `rm -rf venv`

## Next Steps

- Read [README.md](README.md) for usage instructions
- Customize [resources/vocabulary.json](resources/vocabulary.json) for your needs
- Report issues on GitHub

---

**Need help?** Open an issue on GitHub or check the documentation.
