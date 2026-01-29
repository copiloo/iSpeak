# voicedev/text_injector.py

from pynput.keyboard import Controller, Key
import time
import pyperclip

class TextInjector:
    def __init__(self, typing_speed=0.01):
        self.keyboard = Controller()
        self.typing_speed = typing_speed  # Delay between characters (seconds)

    def type_text(self, text: str, instant: bool = True):
        """
        Type text into active application
        instant: if True, paste instead of typing (faster but less natural)
        """
        if not text:
            return

        if instant:
            self._paste_text(text)
        else:
            self._type_slowly(text)

    def _type_slowly(self, text: str):
        """Simulate natural typing character by character"""
        for char in text:
            try:
                self.keyboard.type(char)
                if self.typing_speed > 0:
                    time.sleep(self.typing_speed)
            except Exception as e:
                print(f"Error typing character '{char}': {e}")

    def _paste_text(self, text: str):
        """
        Paste via clipboard (faster)
        This is the recommended method for longer text
        """
        try:
            print(f"[TextInjector] Starting paste operation for text: '{text[:30]}...'")

            # Save current clipboard
            try:
                old_clipboard = pyperclip.paste()
                print(f"[TextInjector] Saved old clipboard")
            except:
                old_clipboard = ""
                print(f"[TextInjector] Could not read clipboard, continuing...")

            # Copy new text
            pyperclip.copy(text)
            print(f"[TextInjector] Copied text to clipboard")

            # Small delay to ensure clipboard is updated
            time.sleep(0.05)

            # Paste (Cmd+V on Mac)
            print(f"[TextInjector] Simulating Cmd+V...")
            with self.keyboard.pressed(Key.cmd):
                self.keyboard.press('v')
                self.keyboard.release('v')

            # Wait for paste to complete
            time.sleep(0.1)
            print(f"[TextInjector] Paste complete")

            # Restore old clipboard
            if old_clipboard:
                pyperclip.copy(old_clipboard)
                print(f"[TextInjector] Restored old clipboard")

            print(f"[TextInjector] Paste operation successful")

        except Exception as e:
            print(f"[TextInjector] Error pasting text: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to typing
            print(f"[TextInjector] Falling back to typing...")
            self._type_slowly(text)

    def press_key(self, key_name: str):
        """Press special keys"""
        key_map = {
            'enter': Key.enter,
            'return': Key.enter,
            'tab': Key.tab,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'escape': Key.esc,
            'esc': Key.esc,
            'space': Key.space,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
        }

        key = key_map.get(key_name.lower())
        if key:
            self.keyboard.press(key)
            self.keyboard.release(key)

    def delete_last_word(self):
        """Delete the last word (useful for corrections)"""
        # Option+Backspace on Mac deletes word
        with self.keyboard.pressed(Key.alt):
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)

    def delete_last_character(self):
        """Delete the last character"""
        self.keyboard.press(Key.backspace)
        self.keyboard.release(Key.backspace)
