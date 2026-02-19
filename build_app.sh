#!/bin/bash
# build_app.sh - Build iSpeak.app for macOS

set -e  # Exit on error

echo "================================================"
echo "Building iSpeak.app"
echo "================================================"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Error: Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Install PyInstaller if needed
echo "Installing PyInstaller..."
pip install pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the app
echo "Building application..."
pyinstaller \
    --name iSpeak \
    --windowed \
    --onefile \
    --add-data "resources:resources" \
    --hidden-import PyQt6 \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import faster_whisper \
    --hidden-import pyaudio \
    --hidden-import pynput \
    --hidden-import pyperclip \
    --hidden-import numpy \
    ispeak/main.py

echo ""
echo "================================================"
echo "✅ Build complete!"
echo "================================================"
echo "App location: dist/iSpeak.app"
echo ""
echo "To run: open dist/iSpeak.app"
echo "To distribute: Create a DMG or zip the .app"
echo "================================================"
