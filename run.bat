@echo off
REM run.bat - Launch iSpeak from source (development mode)

REM Activate venv if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: venv not found. Run build_app.bat first to set up dependencies.
)

cd ispeak
python main.py
