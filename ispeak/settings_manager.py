# ispeak/settings_manager.py

import os
import json
import sys

# Store settings in %APPDATA%\iSpeak\settings.json
_SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "iSpeak")
_SETTINGS_FILE = os.path.join(_SETTINGS_DIR, "settings.json")

_DEFAULTS = {
    "language": "auto",
    "model": "small",
    "auto_enter": False,
    "code_commands": False,
    "input_device": "",          # microphone name; "" = Windows default
    "fast_mode": True,           # short encoder window for short dictations
    "show_debug_console": False,
}


def load() -> dict:
    """Load settings from disk, filling in any missing keys with defaults."""
    settings = dict(_DEFAULTS)
    if os.path.exists(_SETTINGS_FILE):
        try:
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                stored = json.load(f)
                settings.update({k: v for k, v in stored.items() if k in _DEFAULTS})
        except Exception as e:
            print(f"[Settings] Could not load settings: {e}")
    return settings


def save(settings: dict):
    """Persist settings to disk."""
    try:
        os.makedirs(_SETTINGS_DIR, exist_ok=True)
        # Write to a temp file and swap it in, so a crash mid-write can't
        # leave a truncated settings.json behind.
        tmp = _SETTINGS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        os.replace(tmp, _SETTINGS_FILE)
    except Exception as e:
        print(f"[Settings] Could not save settings: {e}")
