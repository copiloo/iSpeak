# ispeak/settings_manager.py

import os
import json
import sys

# Store settings in %APPDATA%\iSpeak\settings.json
_SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "iSpeak")
_SETTINGS_FILE = os.path.join(_SETTINGS_DIR, "settings.json")

_DEFAULTS = {
    "language": "en",
    "model": "small",
    "auto_enter": False,
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
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"[Settings] Could not save settings: {e}")
