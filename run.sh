#!/bin/bash
# run.sh - Quick script to run iSpeak

set -e  # Exit on error

echo "================================================"
echo "Starting iSpeak"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Please run the following commands first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import faster_whisper" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo ""
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Run the application
echo "Starting application..."
echo ""
cd ispeak
python main.py
