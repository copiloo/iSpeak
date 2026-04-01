# ispeak/text_injector.py

import sys
from pynput.keyboard import Controller, Key
import time
import pyperclip

# Use Ctrl on Windows/Linux, Cmd on macOS
_PASTE_MODIFIER = Key.cmd if sys.platform == "darwin" else Key.ctrl

if sys.platform == "win32":
    import win32gui
    import win32api
    import win32con
    import ctypes
    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32

    def _get_window_class(hwnd) -> str:
        buf = ctypes.create_unicode_buffer(256)
        _user32.GetClassNameW(hwnd, buf, 256)
        return buf.value

    def _is_electron_hwnd(hwnd) -> bool:
        """Electron/Chromium apps use Chrome_RenderWidgetHostHWND for the editor pane.
        SetFocus() on these confuses Chromium's internal focus routing — skip it."""
        if not hwnd:
            return False
        cls = _get_window_class(hwnd)
        return cls in ("Chrome_RenderWidgetHostHWND", "Chrome_WidgetWin_1")


def is_hwnd_valid(hwnd) -> bool:
    """Check if a window handle still refers to an existing window."""
    if sys.platform != "win32" or not hwnd:
        return False
    return bool(_user32.IsWindow(hwnd))


def get_focus_info():
    """
    Capture both the top-level foreground window and the focused child control.
    Returns (fg_hwnd, focused_hwnd). Both needed to fully restore keyboard focus.
    """
    if sys.platform != "win32":
        return None, None
    try:
        fg_hwnd = _user32.GetForegroundWindow()
        if not fg_hwnd:
            return None, None

        # To read the focused child window we must attach to the target thread's
        # input queue — GetFocus() only works for the calling thread otherwise.
        fg_thread = _user32.GetWindowThreadProcessId(fg_hwnd, None)
        cur_thread = _kernel32.GetCurrentThreadId()

        _user32.AttachThreadInput(cur_thread, fg_thread, True)
        focused_hwnd = _user32.GetFocus()
        _user32.AttachThreadInput(cur_thread, fg_thread, False)

        cls = _get_window_class(focused_hwnd) if focused_hwnd else "?"
        print(f"[TextInjector] Captured focus — fg={fg_hwnd}, child={focused_hwnd}, class={cls}")
        return fg_hwnd, focused_hwnd
    except Exception as e:
        print(f"[TextInjector] Could not capture focus info: {e}")
        return None, None


def restore_focus(fg_hwnd, focused_hwnd):
    """
    Restore keyboard focus to the exact child control that was active when
    recording started (e.g. Scintilla in Notepad++, text area in VS Code).

    Returns True if the target window is now the foreground window.

    Key insight: Windows only allows SetForegroundWindow() from the thread that
    owns the current foreground window.  We must AttachThreadInput to the
    CURRENT foreground thread (not just the target) to inherit that privilege.
    """
    if sys.platform != "win32" or not fg_hwnd:
        return False
    try:
        target_hwnd = focused_hwnd if focused_hwnd else fg_hwnd
        electron = _is_electron_hwnd(focused_hwnd)
        cur_thread = _kernel32.GetCurrentThreadId()

        print(f"[TextInjector] restore_focus — fg={fg_hwnd}, child={focused_hwnd}, electron={electron}")

        # If the target is already the foreground window, just set child focus
        current_fg = _user32.GetForegroundWindow()
        if current_fg == fg_hwnd:
            if not electron and focused_hwnd:
                fg_thread = _user32.GetWindowThreadProcessId(fg_hwnd, None)
                _user32.AttachThreadInput(cur_thread, fg_thread, True)
                _user32.SetFocus(target_hwnd)
                _user32.AttachThreadInput(cur_thread, fg_thread, False)
            print(f"[TextInjector] Target already foreground")
            return True

        # Attach to BOTH the current foreground thread and the target thread.
        # Attaching to the foreground thread grants us the right to call
        # SetForegroundWindow; attaching to the target lets us call SetFocus.
        current_fg_thread = _user32.GetWindowThreadProcessId(current_fg, None)
        target_thread = _user32.GetWindowThreadProcessId(fg_hwnd, None)

        attached = set()
        for tid in {current_fg_thread, target_thread}:
            if tid and tid != cur_thread:
                _user32.AttachThreadInput(cur_thread, tid, True)
                attached.add(tid)

        # Simulate a null input event — satisfies the Windows requirement that
        # the calling process "received the last input event" before it may
        # change the foreground window.
        _user32.keybd_event(0, 0, 0, 0)

        _user32.SetForegroundWindow(fg_hwnd)
        _user32.BringWindowToTop(fg_hwnd)

        if not electron and focused_hwnd:
            _user32.SetFocus(target_hwnd)

        for tid in attached:
            _user32.AttachThreadInput(cur_thread, tid, False)

        delay = 0.15 if electron else 0.03
        time.sleep(delay)

        # Verify
        fg_after = _user32.GetForegroundWindow()
        success = fg_after == fg_hwnd
        print(f"[TextInjector] After restore — fg_after={fg_after}, expected={fg_hwnd}, success={success}")

        if not success:
            # Retry: ShowWindow can sometimes nudge Windows into cooperating
            print(f"[TextInjector] Retry with ShowWindow...")
            _user32.ShowWindow(fg_hwnd, 5)  # SW_SHOW
            time.sleep(0.05)
            _user32.keybd_event(0, 0, 0, 0)
            _user32.SetForegroundWindow(fg_hwnd)
            time.sleep(0.05)
            fg_after = _user32.GetForegroundWindow()
            success = fg_after == fg_hwnd
            print(f"[TextInjector] Retry result — success={success}")

        return success

    except Exception as e:
        print(f"[TextInjector] Could not restore focus: {e}")
        import traceback
        traceback.print_exc()
        return False


class TextInjector:
    def __init__(self, typing_speed=0.01):
        self.keyboard = Controller()
        self.typing_speed = typing_speed

    def type_text(self, text: str, instant: bool = True,
                  target_hwnd=None, target_focus_hwnd=None):
        """
        Type text into the active application.
        target_hwnd:       top-level window to bring to foreground
        target_focus_hwnd: child control that should receive keyboard input
        """
        if not text:
            return

        if instant:
            self._paste_text(text,
                             target_hwnd=target_hwnd,
                             target_focus_hwnd=target_focus_hwnd)
        else:
            restore_focus(target_hwnd, target_focus_hwnd)
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

    def _paste_text(self, text: str, target_hwnd=None, target_focus_hwnd=None):
        try:
            # Prepare clipboard BEFORE restoring focus — any clipboard API call after
            # restore_focus() risks disrupting Electron/Chromium's focus state.
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                old_clipboard = ""

            pyperclip.copy(text)
            time.sleep(0.01)  # Let clipboard settle

            # Restore focus as close as possible to the actual paste
            focus_ok = restore_focus(target_hwnd, target_focus_hwnd)

            if focus_ok:
                # Focus restored — use keyboard Ctrl+V
                # Dismiss any lingering Alt-activated menu bar (harmless in editors)
                electron = target_focus_hwnd and _is_electron_hwnd(target_focus_hwnd)
                self.keyboard.press(Key.esc)
                self.keyboard.release(Key.esc)
                # Electron/Chromium needs extra time to process Escape and
                # return internal focus from the menu bar to the editor.
                time.sleep(0.10 if electron else 0.02)

                with self.keyboard.pressed(_PASTE_MODIFIER):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
                print(f"[TextInjector] Pasted via Ctrl+V (electron={electron}): '{text[:50]}{'...' if len(text) > 50 else ''}'")


            elif sys.platform == "win32":
                # Focus restore failed — try sending WM_PASTE directly to the
                # target window handle.  This bypasses focus entirely and works
                # for native Win32 controls (Notepad, Notepad++, etc.).
                # Electron/Chromium controls don't process WM_PASTE, so for those
                # we fall back to a blind Ctrl+V as a last resort.
                paste_target = target_focus_hwnd or target_hwnd
                electron = paste_target and _is_electron_hwnd(paste_target)

                if paste_target and not electron:
                    WM_PASTE = 0x0302
                    print(f"[TextInjector] Focus failed, sending WM_PASTE to {paste_target}")
                    _user32.SendMessageW(paste_target, WM_PASTE, 0, 0)
                else:
                    # Last resort — blind Ctrl+V to whatever is currently focused
                    print(f"[TextInjector] Focus failed, blind Ctrl+V as last resort")
                    self.keyboard.press(Key.esc)
                    self.keyboard.release(Key.esc)
                    time.sleep(0.05)
                    with self.keyboard.pressed(_PASTE_MODIFIER):
                        self.keyboard.press('v')
                        self.keyboard.release('v')

            time.sleep(0.05)  # Let paste complete

            if old_clipboard:
                pyperclip.copy(old_clipboard)

        except Exception as e:
            print(f"[TextInjector] Error pasting text: {e}")
            import traceback
            traceback.print_exc()
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
