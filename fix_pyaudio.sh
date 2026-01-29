#!/bin/bash
# fix_pyaudio.sh - Fix PyAudio installation issues on macOS

set -e

echo "================================================"
echo "PyAudio Installation Fix for macOS"
echo "================================================"

# Detect architecture
if [[ $(uname -m) == "arm64" ]]; then
    echo "Detected: Apple Silicon (M1/M2/M3)"
    BREW_PREFIX="/opt/homebrew"
else
    echo "Detected: Intel Mac"
    BREW_PREFIX="/usr/local"
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo ""
echo "Step 1: Checking PortAudio installation..."
if ! brew list portaudio &>/dev/null; then
    echo "Installing PortAudio..."
    brew install portaudio
else
    echo "✅ PortAudio already installed"
fi

echo ""
echo "Step 2: Upgrading pip and build tools..."
pip install --upgrade pip setuptools wheel

echo ""
echo "Step 3: Setting compiler flags..."
export CFLAGS="-I${BREW_PREFIX}/include"
export LDFLAGS="-L${BREW_PREFIX}/lib"
echo "CFLAGS=${CFLAGS}"
echo "LDFLAGS=${LDFLAGS}"

echo ""
echo "Step 4: Removing old PyAudio if exists..."
pip uninstall -y pyaudio 2>/dev/null || true

echo ""
echo "Step 5: Installing PyAudio..."
pip install --no-cache-dir pyaudio

echo ""
echo "Step 6: Testing PyAudio installation..."
if python -c "import pyaudio; print('PyAudio version:', pyaudio.__version__)" 2>/dev/null; then
    echo "✅ PyAudio installed successfully!"
else
    echo "❌ PyAudio installation failed"
    exit 1
fi

echo ""
echo "Step 7: Installing remaining dependencies..."
pip install -r requirements.txt

echo ""
echo "================================================"
echo "✅ All dependencies installed successfully!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Test with: python prototype.py"
echo "  2. Or run full app: ./run.sh"
echo ""
