# ispeak/hotkey_controller.py

from pynput import keyboard
import threading

class HotkeyController:
    def __init__(self, on_start_callback, on_stop_callback):
        """
        Initialize hotkey controller
        on_start_callback: function to call when hotkey pressed
        on_stop_callback: function to call when hotkey released
        """
        self.on_start = on_start_callback
        self.on_stop = on_stop_callback

        self.is_recording = False
        self._state_lock = threading.Lock()  # Protect is_recording from race conditions

        # Default hotkey: Right Option (Alt) key
        # Can be customized by user
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

    def _on_press(self, key):
        """Called when any key is pressed"""
        try:
            if key == self.hotkey:
                with self._state_lock:
                    if not self.is_recording:
                        self.is_recording = True
                        self.on_start()  # Start recording
        except Exception as e:
            print(f"Error in key press handler: {e}")

    def _on_release(self, key):
        """Called when any key is released"""
        try:
            if key == self.hotkey:
                with self._state_lock:
                    if self.is_recording:
                        self.is_recording = False
                        self.on_stop()  # Stop recording and transcribe
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
