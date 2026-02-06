#!/bin/bash
# iSpeak Setup Script for macOS

set -e  # Exit on error

echo "🎤 iSpeak Setup Script"
echo "======================"
echo ""

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed"
    echo "Please install Homebrew first: https://brew.sh"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3: brew install python@3.9"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Install PortAudio via Homebrew
echo "📦 Installing PortAudio..."
if brew list portaudio &> /dev/null; then
    echo "✅ PortAudio already installed"
else
    brew install portaudio
    echo "✅ PortAudio installed"
fi
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install all dependencies except PyAudio first
echo "📦 Installing dependencies..."
grep -v "pyaudio" requirements.txt > /tmp/requirements_no_pyaudio.txt
pip install -r /tmp/requirements_no_pyaudio.txt
rm /tmp/requirements_no_pyaudio.txt
echo "✅ Dependencies installed"
echo ""

# Install PyAudio with proper flags for macOS
echo "🎙️  Installing PyAudio with PortAudio support..."
CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install --no-binary :all: pyaudio
echo "✅ PyAudio installed"
echo ""

# Verify PyAudio import
echo "🧪 Testing PyAudio..."
if python -c "import pyaudio" 2>/dev/null; then
    echo "✅ PyAudio is working correctly"
else
    echo "❌ PyAudio test failed"
    exit 1
fi
echo ""

echo "✨ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the app: cd ispeak && python main.py"
echo ""
echo "⚠️  Remember to grant the following permissions in System Settings:"
echo "   - Microphone Access (Privacy & Security > Microphone)"
echo "   - Accessibility Access (Privacy & Security > Accessibility)"
echo "   - Input Monitoring (Privacy & Security > Input Monitoring)"
echo ""
echo "💡 Optional: Set HuggingFace token for faster model downloads:"
echo "   1. Get a free token at https://huggingface.co/settings/tokens"
echo "   2. Add to your shell profile (~/.zshrc or ~/.bash_profile):"
echo "      export HF_TOKEN=\"your_token_here\""
echo "   3. Reload your shell: source ~/.zshrc"
echo ""
