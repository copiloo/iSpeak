# Installation Guide

## Prerequisites

- macOS 10.15 or later
- Python 3.8 or later
- Homebrew (for PortAudio)

## Step-by-Step Installation

### Quick Installation (Recommended)

Use the automated setup script:

```bash
# Clone the repository
git clone <your-repo-url>
cd iSpeak

# Run the setup script
./setup.sh
```

The script will:
- ✅ Check prerequisites (macOS, Homebrew, Python)
- ✅ Install PortAudio via Homebrew
- ✅ Create a virtual environment
- ✅ Install all dependencies with proper configuration
- ✅ Build PyAudio from source with PortAudio support
- ✅ Verify the installation

**Note:** The first time you run iSpeak, it will download the Whisper model (~140MB for the base model). This only happens once.

---

### Manual Installation

If you prefer to install manually or the script doesn't work:

#### 1. Install PortAudio with Development Headers

PortAudio is required for microphone access. You need both the library and development headers:

```bash
# Install PortAudio
brew install portaudio

# Verify installation
brew info portaudio
```

#### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd iSpeak
```

#### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 4. Install Dependencies

**Important:** PyAudio needs special handling on macOS to properly link with PortAudio.

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies except PyAudio
grep -v "pyaudio" requirements.txt > /tmp/requirements_no_pyaudio.txt
pip install -r /tmp/requirements_no_pyaudio.txt
rm /tmp/requirements_no_pyaudio.txt

# Install PyAudio from source with proper flags (Apple Silicon)
CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install --no-binary :all: pyaudio

# For Intel Macs, use:
# CFLAGS="-I/usr/local/include" LDFLAGS="-L/usr/local/lib" pip install --no-binary :all: pyaudio
```

**Verify PyAudio installation:**

```bash
python -c "import pyaudio; print('PyAudio working!')"
```

If you see "PyAudio working!", you're good to go!

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

1. Wait for "iSpeak Prototype Ready!" message
2. Press and hold Right Alt
3. Speak: "acesta este un test"
4. Release Right Alt
5. The text should appear!

If this works, proceed to the full app.

### 7. Run Full Application

```bash
cd ispeak
python main.py
```

The app will:
1. Load the Whisper model (takes 2-3 seconds)
2. Start the system tray icon
3. Start listening for the hotkey

Look for the iSpeak icon in your menu bar!

## Troubleshooting

### "PyAudio could not find PortAudio" or "symbol not found '_PaMacCore_SetupChannelMap'"

This error means PyAudio wasn't properly linked to PortAudio. Fix it by rebuilding PyAudio from source:

```bash
# Make sure PortAudio is installed
brew install portaudio

# Uninstall existing PyAudio
pip uninstall -y pyaudio

# Reinstall from source with proper flags (Apple Silicon)
CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install --no-binary :all: pyaudio

# For Intel Macs, use:
# CFLAGS="-I/usr/local/include" LDFLAGS="-L/usr/local/lib" pip install --no-binary :all: pyaudio

# Verify it works
python -c "import pyaudio; print('Success!')"
```

**Why this happens:** Pre-built PyAudio wheels sometimes aren't compatible with your system's PortAudio. Building from source ensures proper linking.

### "AppKit module not found"

```bash
pip install pyobjc-framework-Cocoa
```

### "Permission denied" when running build_app.sh

```bash
chmod +x build_app.sh
```

### "You are sending unauthenticated requests to the HF Hub"

This warning appears when downloading models without a Hugging Face token. It's not an error — the app works fine without one — but setting a token gives you faster downloads and higher rate limits:

1. Get a free token at https://huggingface.co/settings/tokens (read access is enough)
2. Add to your shell profile (`~/.zshrc` or `~/.bash_profile`):
   ```bash
   export HF_TOKEN="your_token_here"
   ```
3. Reload your shell: `source ~/.zshrc`

### Models downloading slowly

The Whisper models are downloaded from Hugging Face. If the download is slow:
1. Set a HuggingFace token (see above) — unauthenticated requests have lower rate limits
2. Check your internet connection
3. Models are cached in `./models/` directory (one-time download)

### Text not appearing in applications

1. Make sure Accessibility permissions are granted
2. Try clicking in the target application before dictating
3. Check that you're releasing the hotkey (Right Alt)

## Building Standalone App

To create a standalone .app bundle:

```bash
./build_app.sh
```

The app will be created at `dist/iSpeak.app`.

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
