# ispeak/hotkey_controller.py

import sys
from pynput import keyboard
import threading

class HotkeyController:
    def __init__(self, on_start_callback, on_stop_callback):
        self.on_start = on_start_callback
        self.on_stop = on_stop_callback

        self.is_recording = False
        self._state_lock = threading.Lock()

        # On Windows, use Right Ctrl — Right Alt (AltGr) activates menu bars in
        # Electron apps (VS Code, Slack, etc.) on key release, stealing editor focus.
        # On macOS, Right Alt is safe (no menu activation behaviour).
        if sys.platform == "win32":
            self.hotkey = keyboard.Key.ctrl_r
        else:
            self.hotkey = keyboard.Key.alt_r

        self.listener = None

    def start_listening(self):
        """Start global hotkey listener"""
        print(f"Hotkey listener started. Press {self.hotkey} to dictate.")

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop_listening(self):
        """Stop listener"""
        if self.listener:
            self.listener.stop()
            print("Hotkey listener stopped.")

    def _matches(self, key) -> bool:
        return key == self.hotkey

    def _on_press(self, key):
        try:
            if self._matches(key):
                with self._state_lock:
                    if not self.is_recording:
                        self.is_recording = True
                        self.on_start()
        except Exception as e:
            print(f"Error in key press handler: {e}")

    def _on_release(self, key):
        try:
            if self._matches(key):
                with self._state_lock:
                    if self.is_recording:
                        self.is_recording = False
                        self.on_stop()
        except Exception as e:
            print(f"Error in key release handler: {e}")

    def set_hotkey(self, key):
        """
        Allow user to customize hotkey
        key: pynput.keyboard.Key or KeyCode
        """
        self.hotkey = key
        print(f"Hotkey changed to: {key}")

    def get_hotkey_name(self):
        """Return human-readable hotkey name"""
        if hasattr(self.hotkey, 'name'):
            return self.hotkey.name
        return str(self.hotkey)
