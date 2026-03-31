@echo off
setlocal enabledelayedexpansion

echo ================================================
echo  Building iSpeak for Windows
echo ================================================

REM --- Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause & exit /b 1
)

REM --- Create venv if it doesn't exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause & exit /b 1
    )
)

REM --- Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM --- Upgrade pip silently
python -m pip install --upgrade pip --quiet

REM --- Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause & exit /b 1
)

REM --- Install PyInstaller
echo Installing PyInstaller...
pip install pyinstaller --quiet

REM --- Clean previous builds
echo Cleaning previous builds...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist

REM --- Build
echo.
echo Building iSpeak.exe ...
echo ================================================
pyinstaller iSpeak.spec
if errorlevel 1 (
    echo.
    echo ERROR: Build failed! See output above for details.
    pause & exit /b 1
)

echo.
echo ================================================
echo  Build complete!
echo ================================================
echo  Executable: dist\iSpeak.exe
echo  Run it:     dist\iSpeak.exe
echo ================================================

pause
