# ispeak/main.py

import sys
import os
import signal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, QTimer
import time

from audio_capture import AudioCapture
from transcription import TranscriptionEngine, DETECTOR_MODEL, MODELS_USING_DETECTOR
from text_processor import TextProcessor
from text_injector import TextInjector
from hotkey_controller import HotkeyController
from context_detector import ContextDetector
from overlay_widget import OverlayWidget
from settings_dialog import SettingsDialog
import settings_manager
import logging
from logging.handlers import RotatingFileHandler

# Language setting values -> labels shown in the tray menu / About box
LANGUAGE_LABELS = {
    "auto": "Auto (Romanian / English)",
    "ro":   "Romanian",
    "en":   "English",
}


def _language_label(code: str) -> str:
    return LANGUAGE_LABELS.get(code, code)

# ---------------------------------------------------------------------------
# Logging — always write to a file so crashes are diagnosable even without
# the debug console.  Logs live next to the exe (or the project root when
# running from source).  If that folder isn't writable (e.g. Program Files),
# they fall back to %LOCALAPPDATA%\iSpeak so startup can never fail on logging.
# ---------------------------------------------------------------------------

def _app_dir() -> str:
    """Directory that holds the exe (frozen) or the project root (source)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _is_writable(directory: str) -> bool:
    probe = os.path.join(directory, ".ispeak_write_test")
    try:
        with open(probe, "w"):
            pass
        os.remove(probe)
        return True
    except OSError:
        return False


def _log_dir() -> str:
    """Folder for ispeak.log / ispeak_crash.log: the exe's folder if writable."""
    app_dir = _app_dir()
    if _is_writable(app_dir):
        return app_dir
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "iSpeak")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        import tempfile
        path = tempfile.gettempdir()
    return path


_LOG_DIR = _log_dir()

_log = logging.getLogger("iSpeak")
_log.setLevel(logging.INFO)
try:
    _log_handler = RotatingFileHandler(
        os.path.join(_LOG_DIR, "ispeak.log"),
        maxBytes=1_000_000, backupCount=2, encoding="utf-8", errors="replace")
    _log_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    _log.addHandler(_log_handler)
except Exception:
    # Never let logging setup prevent the app from starting
    _log.addHandler(logging.NullHandler())


_single_instance_mutex = None  # kept alive for the whole process lifetime


def _acquire_single_instance() -> bool:
    """Return False if another iSpeak instance is already running.

    Two instances would each install a hotkey listener and paste every
    dictation twice.
    """
    global _single_instance_mutex
    if sys.platform != "win32":
        return True
    import ctypes
    ERROR_ALREADY_EXISTS = 183
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    _single_instance_mutex = kernel32.CreateMutexW(None, False, "Local\\iSpeak_SingleInstance")
    return ctypes.get_last_error() != ERROR_ALREADY_EXISTS


def _set_console_visible(visible: bool):
    """Allocate or free a debug console window at runtime.

    Because the app is built as a windowed exe (console=False), there is no
    console by default.  We create one on demand with AllocConsole() and
    redirect Python's stdout/stderr to it.  FreeConsole() detaches it —
    closing the console window will NOT kill the app.
    """
    if sys.platform != "win32":
        return
    import ctypes
    kernel32 = ctypes.windll.kernel32

    if visible:
        # Allocate a new console (no-op if one already exists)
        if not kernel32.GetConsoleWindow():
            kernel32.AllocConsole()
            # Set a friendly title
            kernel32.SetConsoleTitleW("iSpeak — Debug Console")
            # Prevent closing the console from killing the app
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                import win32con, win32gui
                # Remove the Close button from the console window so users
                # use the Settings toggle instead.  This also prevents the
                # default "close console = kill process" behaviour.
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE,
                                       style & ~win32con.WS_SYSMENU)
        # Redirect Python streams to the (new) console
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    else:
        # Free the console — the app keeps running as a windowed process
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            # Restore Python streams before freeing the console
            sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
            sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")
            kernel32.FreeConsole()


class iSpeakApp(QObject):
    # The pynput hotkey callbacks run inside a Windows low-level keyboard hook.
    # Windows silently uninstalls hooks that take too long to return, so the
    # callbacks do nothing but emit these signals; the actual work (opening
    # the mic, capturing focus, touching Qt widgets) runs on the Qt main thread.
    _hotkey_pressed = pyqtSignal()
    _hotkey_released = pyqtSignal()

    def __init__(self):
        super().__init__()
        print("Initializing iSpeak...")

        # Load persisted settings first
        self._settings = settings_manager.load()
        _set_console_visible(self._settings.get("show_debug_console", False))

        self.audio = AudioCapture(device_name=self._settings.get("input_device", ""))
        self.transcriber = None          # loaded async after tray appears
        self.processor = TextProcessor(
            code_commands_enabled=self._settings.get("code_commands", False))
        self.injector = TextInjector()
        self.hotkey = HotkeyController(
            on_start_callback=self._hotkey_pressed.emit,
            on_stop_callback=self._hotkey_released.emit,
        )
        self.context = ContextDetector()

        # State — seeded from saved settings
        self.current_language = self._settings.get("language", "auto")
        self.current_model = self._settings.get("model", "small")
        self.auto_press_enter = self._settings.get("auto_enter", False)
        self.is_processing = True        # Block dictation until model is ready
        self._is_recording = False

        # Live worker threads.  Each removes itself (and is deleteLater'd) on
        # QThread's built-in `finished`, i.e. only after run() has returned.
        self._threads = set()
        self._target_hwnd = None        # Top-level window before recording
        self._target_focus_hwnd = None  # Focused child control before recording

        # Hide from Dock on macOS
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
                ns_app = NSApplication.sharedApplication()
                ns_app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
            except Exception as e:
                print(f"Warning: Could not hide Dock icon: {e}")

        # Bridge pynput listener thread → Qt main thread (queued connections)
        self._hotkey_pressed.connect(self.start_dictation)
        self._hotkey_released.connect(self.stop_dictation)

        # Show tray icon FIRST — model loads in background after event loop starts
        self.tray_icon = self._create_tray_icon()
        self.overlay = OverlayWidget()

        print("iSpeak tray icon ready. Loading model in background...")

    # ------------------------------------------------------------------
    # Dictation lifecycle
    # ------------------------------------------------------------------

    @pyqtSlot()
    def start_dictation(self):
        """Hotkey pressed — runs on the Qt main thread."""
        if self.transcriber is None or self.is_processing:
            _log.info("Hotkey pressed — ignored (model not ready or still processing)")
            return
        # Capture focus NOW — the user is in their target window at press time
        # (Right Ctrl doesn't move focus), so the focused child control is correct.
        from text_injector import get_focus_info
        self._target_hwnd, self._target_focus_hwnd = get_focus_info()
        try:
            self.audio.start_recording()
        except Exception as e:
            _log.error(f"Could not open microphone: {e}")
            self.tray_icon.setToolTip("❌ Microphone unavailable")
            return
        self._is_recording = True
        mic = self.audio.active_device_name or "default microphone"
        _log.info(f"Hotkey pressed — recording started (mic: {mic})")
        if self.audio.used_fallback:
            self.tray_icon.setToolTip(f"🎤 Recording — selected mic not found, using {mic}")
        else:
            self.tray_icon.setToolTip(f"🎤 Recording ({mic})...")
        self.overlay.show_listening()

    @pyqtSlot()
    def stop_dictation(self):
        """Hotkey released — runs on the Qt main thread."""
        if not self._is_recording:
            return  # the press was ignored (model loading / busy / mic error)
        self._is_recording = False

        audio_data = self.audio.stop_recording()
        _log.info(f"Hotkey released — recorded {len(audio_data) / 16000:.1f}s of audio")

        if len(audio_data) < 4800:  # < 0.3 seconds at 16kHz
            _log.info("Recording too short (< 0.3s), ignored")
            self.tray_icon.setToolTip("✅ Ready")
            self.overlay.hide_overlay()
            return

        self.is_processing = True
        self.tray_icon.setToolTip("⏳ Transcribing...")
        self.overlay.show_processing()
        self._start_transcription_thread(audio_data)

    def _track_thread(self, thread: QThread):
        """Keep a Python reference to a worker until run() has fully returned.

        Dropping the last reference (or calling deleteLater) while run() is
        still executing destroys a running QThread and aborts the process.
        """
        self._threads.add(thread)
        thread.finished.connect(self._on_thread_finished)  # QThread built-in

    @pyqtSlot()
    def _on_thread_finished(self):
        thread = self.sender()
        self._threads.discard(thread)
        if thread is not None:
            thread.deleteLater()

    def _start_transcription_thread(self, audio_data):
        thread = TranscriptionThread(
            audio_data,
            self.transcriber,
            self.processor,
            self.context,
            self.current_language,
            self._target_hwnd,
        )
        thread.result_ready.connect(self._on_transcription_done)
        self._track_thread(thread)
        thread.start()

    @pyqtSlot(bool, str)
    def _on_transcription_done(self, success: bool, text: str = ""):
        _log.info(f"Transcription done: success={success}, {len(text) if text else 0} chars")

        self.is_processing = False
        self.overlay.hide_overlay()

        if success and text:
            self.tray_icon.setToolTip("✅ Ready")
            self._inject_text(text)
        else:
            print("[Main] ❌ Transcription failed or empty")
            self.tray_icon.setToolTip("❌ Nothing recognised - Ready")

    def _inject_text(self, text: str):
        try:
            from text_injector import is_hwnd_valid, get_focus_info

            target_hwnd = self._target_hwnd
            target_focus_hwnd = self._target_focus_hwnd

            # If the target window was closed during transcription, fall back
            if not is_hwnd_valid(target_hwnd):
                print("[Main] Stored target window is no longer valid, using current foreground")
                target_hwnd, target_focus_hwnd = get_focus_info()

            self.injector.type_text(text, instant=True,
                                    target_hwnd=target_hwnd,
                                    target_focus_hwnd=target_focus_hwnd)
            print(f"[Main] ✅ Inserted: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            _log.info(f"Pasted {len(text)} chars into window {target_hwnd}")
            if self.auto_press_enter:
                QTimer.singleShot(100, lambda: self.injector.press_key('enter'))
        except Exception as e:
            _log.error(f"Error pasting text: {e}", exc_info=True)
            import traceback
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Language / model controls
    # ------------------------------------------------------------------

    def _save_settings(self):
        """Persist the current state immediately (not just on Quit — a Windows
        shutdown or logoff never reaches quit())."""
        self._settings.update({
            "language": self.current_language,
            "model": self.current_model,
            "auto_enter": self.auto_press_enter,
            "code_commands": self.processor.code_commands_enabled,
            "input_device": self.audio.device_name,
        })
        settings_manager.save(self._settings)

    def set_language(self, language: str):
        """language: 'auto', 'ro' or 'en'."""
        self.current_language = language
        _log.info(f"Language set to {language}")
        if self.transcriber is not None:  # may still be loading
            self.transcriber.set_language(language)
        self._save_settings()
        self._update_tray_menu()

    def set_input_device(self, device_name: str):
        """device_name: microphone name, or "" for the Windows default."""
        self.audio.set_device(device_name)
        _log.info(f"Microphone set to {device_name or 'Windows default'}")
        self._save_settings()
        self._update_tray_menu()

    def _populate_mic_menu(self, mic_menu: QMenu):
        """Filled each time the submenu opens, so newly plugged-in headsets show up."""
        mic_menu.clear()
        if self._is_recording:
            busy = mic_menu.addAction("(not available while recording)")
            busy.setEnabled(False)
            return
        selected = self.audio.device_name
        devices = self.audio.list_input_devices()
        default_name = self.audio.default_device_name()

        entries = [("", f"Windows default ({default_name})" if default_name else "Windows default")]
        entries += [(name, name) for name in devices]
        if selected and selected not in devices:
            entries.append((selected, f"{selected} (not connected)"))

        for value, label in entries:
            action = mic_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(value == selected)
            action.triggered.connect(lambda checked, v=value: self.set_input_device(v))

    def toggle_auto_enter(self):
        self.auto_press_enter = not self.auto_press_enter
        print(f"⏎ Auto-press Enter {'enabled' if self.auto_press_enter else 'disabled'}")
        self._save_settings()
        self._update_tray_menu()

    def switch_model(self, model_name: str, confirm: bool = True):
        if model_name == self.current_model:
            return

        if self.is_processing or self._is_recording:
            QMessageBox.warning(None, "Model Switch",
                                "Cannot switch models while loading, recording or processing.")
            self._update_tray_menu()
            return

        if not confirm:
            self._begin_model_switch(model_name)
            return

        model_info = {
            "tiny":   "Fastest, least accurate. ~75MB.",
            "base":   "Fast, fair accuracy. ~142MB.",
            "small":  "Balanced. ~466MB. Recommended for Romanian.",
            "medium": "Slower, excellent accuracy. ~1.5GB.",
            "large":  "Slowest, best accuracy. ~2.9GB.",
            "turbo":  "Fast + accurate! ~800MB. Recommended!",
        }
        msg = QMessageBox()
        msg.setWindowTitle("Switch Model")
        msg.setText(f"Switch to '{model_name}' model?")
        msg.setInformativeText(
            f"{model_info.get(model_name, '')}\n\n"
            "Will download if not cached. App unavailable during download."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        if msg.exec() != QMessageBox.StandardButton.Ok:
            self._update_tray_menu()
            return

        self._begin_model_switch(model_name)

    def _begin_model_switch(self, model_name: str):
        self.is_processing = True
        self.tray_icon.setToolTip(f"Loading {model_name} model...")
        # Rebuild menu immediately so the clicked item's checkmark is cleared
        # (Qt visually toggles it on click, but current_model hasn't changed yet)
        self._update_tray_menu()
        self._start_model_load_thread(model_name)

    def _start_model_load_thread(self, model_name: str):
        models_dir = os.path.join(_app_dir(), "models")
        thread = ModelLoadThread(model_name, models_dir=models_dir)
        thread.loaded.connect(self._on_model_loaded)
        thread.progress.connect(self._on_model_download_progress)
        self._track_thread(thread)
        thread.start()

    @pyqtSlot(str)
    def _on_model_download_progress(self, message: str):
        self.tray_icon.setToolTip(message)
        print(message)

    @pyqtSlot(bool, str, object)
    def _on_model_loaded(self, success: bool, model_name: str, backend_info: dict):
        is_initial_load = self.transcriber is None

        if success:
            self.transcriber = TranscriptionEngine.from_loaded(
                model_name, backend_info,
                language=self.current_language,
                models_dir=os.path.join(_app_dir(), "models"),
            )
            self.transcriber.fast_mode = self._settings.get("fast_mode", True)
            self.current_model = model_name
            self._save_settings()  # only persist a model that actually loaded

            backend_name = backend_info.get("backend", "faster-whisper").upper()
            _log.info(f"Model ready: {model_name} ({backend_name})")
            self.tray_icon.setToolTip("iSpeak - Ready")

            if not is_initial_load:
                QMessageBox.information(None, "Model Loaded",
                                        f"Switched to '{model_name}' model!\nBackend: {backend_name}")
        else:
            _log.warning(f"Failed to load {model_name} model")
            self.tray_icon.setToolTip("iSpeak - Model load failed")
            QMessageBox.critical(None, "Model Load Error",
                                 f"Failed to load '{model_name}'.")

        self.is_processing = False
        self._update_tray_menu()

    # ------------------------------------------------------------------
    # Tray UI
    # ------------------------------------------------------------------

    def _resource_path(self, relative_path: str) -> str:
        """Resolve a resource path that works both from source and PyInstaller frozen exe."""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle — resources are in _MEIPASS
            base = sys._MEIPASS
        else:
            # Running from source — resources are one level up from ispeak/
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, relative_path)

    def _create_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("ERROR: System tray not available on this system.")

        icon = QSystemTrayIcon()

        icon_path = self._resource_path(os.path.join("resources", "icon.png"))
        if os.path.exists(icon_path):
            icon.setIcon(QIcon(icon_path))
        else:
            # Fallback: draw a simple colored circle
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(70, 130, 180))
            painter.setPen(QColor(0, 0, 0, 0))
            painter.drawEllipse(8, 8, 48, 48)
            painter.end()
            icon.setIcon(QIcon(pixmap))

        icon.setToolTip("iSpeak - Loading...")
        icon.setContextMenu(self._build_menu())
        icon.show()
        return icon

    def _build_menu(self):
        """Build a fresh context menu (called once per update)."""
        menu = QMenu()

        status = menu.addAction(f"Language: {_language_label(self.current_language)}")
        status.setEnabled(False)

        if self.transcriber is not None:
            backend_info = self.transcriber.get_backend_info()
            backend_label = "MLX" if backend_info['using_mlx'] else "FW"
            model_status = menu.addAction(f"Model: {self.current_model} ({backend_label})")
        else:
            model_status = menu.addAction(f"Model: {self.current_model} (loading...)")
        model_status.setEnabled(False)

        menu.addSeparator()

        lang_menu = menu.addMenu("Language")
        for code, label in LANGUAGE_LABELS.items():
            action = lang_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(code == self.current_language)
            action.triggered.connect(lambda checked, c=code: self.set_language(c))

        mic_menu = menu.addMenu("Microphone")
        mic_menu.aboutToShow.connect(lambda m=mic_menu: self._populate_mic_menu(m))

        auto_enter_action = menu.addAction("Auto-Press Enter After Dictation")
        auto_enter_action.setCheckable(True)
        auto_enter_action.setChecked(self.auto_press_enter)
        auto_enter_action.triggered.connect(self.toggle_auto_enter)

        menu.addSeparator()

        model_menu = menu.addMenu("Select Model")
        models = [
            ("turbo",  "Turbo (fast + accurate) ⭐ NEW"),
            ("tiny",   "Tiny (fastest, least accurate)"),
            ("base",   "Base (fast, fair accuracy)"),
            ("small",  "Small (balanced)"),
            ("medium", "Medium (slow, excellent)"),
            ("large",  "Large (very slow, best)"),
        ]
        for model_name, description in models:
            action = model_menu.addAction(description)
            action.setCheckable(True)
            action.setChecked(model_name == self.current_model)
            action.triggered.connect(lambda checked, m=model_name: self.switch_model(m))

        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self._open_settings)

        menu.addSeparator()

        about_action = menu.addAction("About iSpeak")
        about_action.triggered.connect(self._show_about)

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit)

        return menu

    def _update_tray_menu(self):
        """Replace the tray context menu, deleting the old one."""
        old_menu = self.tray_icon.contextMenu()
        new_menu = self._build_menu()
        self.tray_icon.setContextMenu(new_menu)
        if old_menu is not None:
            old_menu.deleteLater()

    def _open_settings(self):
        current = {
            "language": self.current_language,
            "model": self.current_model,
            "auto_enter": self.auto_press_enter,
            "code_commands": self.processor.code_commands_enabled,
            "input_device": self.audio.device_name,
            "fast_mode": self._settings.get("fast_mode", True),
            "show_debug_console": self._settings.get("show_debug_console", False),
        }
        devices = [] if self._is_recording else self.audio.list_input_devices()
        dlg = SettingsDialog(current, input_devices=devices,
                             default_device=self.audio.default_device_name())
        if dlg.exec() != SettingsDialog.DialogCode.Accepted:
            return

        new = dlg.get_settings()

        # Apply language change
        if new["language"] != self.current_language:
            self.current_language = new["language"]
            if self.transcriber:
                self.transcriber.set_language(self.current_language)

        self.auto_press_enter = new["auto_enter"]
        self.processor.code_commands_enabled = new["code_commands"]
        self.audio.set_device(new["input_device"])
        self._settings["fast_mode"] = new["fast_mode"]
        if self.transcriber is not None:
            self.transcriber.fast_mode = new["fast_mode"]

        # Apply debug console visibility immediately
        if new["show_debug_console"] != self._settings.get("show_debug_console", False):
            _set_console_visible(new["show_debug_console"])
        self._settings["show_debug_console"] = new["show_debug_console"]

        # The model is saved by _on_model_loaded once it has actually loaded,
        # so a failed download never ends up persisted as the startup model.
        self._save_settings()

        # Apply model change (user already confirmed by pressing OK)
        if new["model"] != self.current_model:
            self.switch_model(new["model"], confirm=False)

        self._update_tray_menu()

    def _show_about(self):
        if self.transcriber is not None:
            backend_info = self.transcriber.get_backend_info()
            backend_str = backend_info['backend'].upper()
            if backend_info['using_mlx']:
                backend_str += " (Apple Silicon optimized)"
        else:
            backend_str = "Loading..."

        msg = QMessageBox()
        msg.setWindowTitle("About iSpeak")
        msg.setText(
            "iSpeak v0.3.0\n\n"
            "Offline voice dictation for developers\n\n"
            "Press Right Ctrl to start dictating.\n"
            f"Language: {_language_label(self.current_language)}\n"
            f"Model: {self.current_model}\n"
            f"Backend: {backend_str}\n\n"
            "Your voice never leaves your machine."
        )
        msg.exec()

    # ------------------------------------------------------------------
    # App lifecycle
    # ------------------------------------------------------------------

    def run(self):
        print("=" * 60)
        print("iSpeak Started!")
        print("=" * 60)
        print(f"   Hotkey:   {self.hotkey.get_hotkey_name()}")
        print(f"   Language: {_language_label(self.current_language)}")
        print(f"   Model:    {self.current_model} (loading...)")
        print("=" * 60)
        _log.info(f"iSpeak started — hotkey={self.hotkey.get_hotkey_name()}, "
                   f"lang={self.current_language}, model={self.current_model}")

        self.hotkey.start_listening()

        # Load the model after the event loop starts (100ms delay so tray renders first)
        QTimer.singleShot(100, self._load_model_async)

        sys.exit(QApplication.instance().exec())

    def _load_model_async(self):
        """Start loading the Whisper model in a background thread."""
        self.tray_icon.setToolTip(f"iSpeak - Loading model ({self.current_model})...")
        self._start_model_load_thread(self.current_model)

    def quit(self):
        print("\nShutting down iSpeak...")
        self._save_settings()
        self.hotkey.stop_listening()

        for thread in list(self._threads):
            if thread.isRunning():
                print("Waiting for background work to finish...")
                thread.wait(3000)

        self.audio.cleanup()
        self.tray_icon.hide()
        QApplication.instance().quit()
        print("Goodbye!")


# ---------------------------------------------------------------------------
# Background threads
# ---------------------------------------------------------------------------

class ModelLoadThread(QThread):
    """Downloads / loads a Whisper model in the background."""
    # NOT named `finished`: that would shadow QThread's built-in signal, which
    # is what tells us run() has actually returned and cleanup is safe.
    loaded = pyqtSignal(bool, str, object)
    progress = pyqtSignal(str)

    MLX_MODELS = {
        "tiny":          "mlx-community/whisper-tiny-mlx",
        "base":          "mlx-community/whisper-base-mlx",
        "small":         "mlx-community/whisper-small-mlx",
        "medium":        "mlx-community/whisper-medium-mlx",
        "large":         "mlx-community/whisper-large-v3-mlx",
        "large-v3":      "mlx-community/whisper-large-v3-mlx",
        "large-v3-turbo":"mlx-community/whisper-large-v3-turbo",
        "turbo":         "mlx-community/whisper-large-v3-turbo",
    }

    def __init__(self, model_name: str, models_dir="./models", use_mlx=True):
        super().__init__()
        self.model_name = model_name
        self.models_dir = models_dir
        self.use_mlx = use_mlx

    def run(self):
        if self.use_mlx and sys.platform == "darwin" and self.model_name in self.MLX_MODELS:
            try:
                import mlx_whisper
                self.progress.emit(f"📥 Loading {self.model_name} model (MLX)...")
                start = time.time()
                mlx_model_path = self.MLX_MODELS[self.model_name]
                load_time = time.time() - start
                self.progress.emit(f"✅ {self.model_name} ready (MLX) in {load_time:.1f}s")
                self.loaded.emit(True, self.model_name, {
                    "backend": "mlx",
                    "mlx_model_path": mlx_model_path,
                    "model": None,
                })
                return
            except ImportError:
                _log.info("MLX-Whisper not available, using faster-whisper")
            except Exception as e:
                _log.warning(f"MLX load failed: {e}, using faster-whisper")

        try:
            # Suppress noisy warnings from huggingface_hub / tqdm that can
            # crash windowed apps when stdout/stderr are not real consoles.
            os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning)

            from faster_whisper import WhisperModel
            from faster_whisper.utils import _MODELS

            # Ensure models directory exists
            os.makedirs(self.models_dir, exist_ok=True)
            _log.info(f"Loading model '{self.model_name}', models_dir={self.models_dir}")

            fw_model = "large-v3-turbo" if self.model_name == "turbo" else self.model_name
            repo_id = _MODELS.get(fw_model, fw_model)

            # Always go through snapshot_download with progress reporting.
            # It returns instantly if the model is fully cached, and resumes
            # with progress if a previous download was interrupted.
            self.progress.emit(f"Loading {self.model_name} model...")
            _log.info(f"Downloading/verifying {repo_id}...")
            model_path = self._download_with_progress(repo_id)

            self.progress.emit(f"Initializing {self.model_name} model...")
            start = time.time()
            # Use physical core count for optimal threading (hyper-threads don't help)
            import multiprocessing
            cpu_threads = max(4, multiprocessing.cpu_count() // 2)
            model = WhisperModel(model_path, device="cpu", compute_type="int8",
                                 cpu_threads=cpu_threads)
            load_time = time.time() - start

            _log.info(f"Model '{self.model_name}' loaded in {load_time:.1f}s")
            self.progress.emit(f"{self.model_name} loaded in {load_time:.1f}s")

            detector = None
            if self.model_name in MODELS_USING_DETECTOR:
                # Small helper model for fast "Auto (RO/EN)" language detection.
                # Optional: if it fails, the main model does detection (slower).
                try:
                    self.progress.emit("Loading language detector...")
                    det_path = self._download_with_progress(
                        _MODELS.get(DETECTOR_MODEL, DETECTOR_MODEL),
                        label=f"language detector ({DETECTOR_MODEL})")
                    detector = WhisperModel(det_path, device="cpu", compute_type="int8",
                                            cpu_threads=cpu_threads)
                    _log.info(f"Language detector '{DETECTOR_MODEL}' loaded")
                except Exception as e:
                    _log.warning(f"Language detector unavailable, using main model: {e}")

            self.loaded.emit(True, self.model_name, {
                "backend": "faster-whisper",
                "model": model,
                "detector": detector,
                "mlx_model_path": None,
            })
        except Exception as e:
            error_msg = f"Error loading {self.model_name}: {e}"
            _log.error(error_msg, exc_info=True)
            self.progress.emit(error_msg)
            self.loaded.emit(False, self.model_name, {})

    def _download_with_progress(self, repo_id: str, label: str = None) -> str:
        """Download a HuggingFace model with real-time progress reporting."""
        label = label or self.model_name
        import huggingface_hub
        from tqdm.auto import tqdm as _tqdm_base

        thread_ref = self  # capture for the inner class

        class _ProgressTqdm(_tqdm_base):
            """Custom tqdm that emits Qt signals instead of printing."""
            def __init__(self, *args, **kwargs):
                # huggingface_hub passes extra kwargs (e.g. name=) that
                # tqdm doesn't accept — strip them to avoid TqdmKeyError.
                kwargs.pop("name", None)
                kwargs["disable"] = False
                kwargs.setdefault("unit", "B")
                kwargs.setdefault("unit_scale", True)
                super().__init__(*args, **kwargs)
                self._last_emit = 0.0

            def update(self, n=1):
                super().update(n)
                # Throttle Qt signal emissions to once per second
                now = time.time()
                if now - self._last_emit < 1.0:
                    return
                self._last_emit = now
                if self.total and self.total > 0:
                    pct = int(self.n / self.total * 100)
                    mb_done = self.n / 1024 / 1024
                    mb_total = self.total / 1024 / 1024
                    thread_ref.progress.emit(
                        f"Downloading {label}: "
                        f"{pct}% ({mb_done:.0f}/{mb_total:.0f} MB)")

            def close(self):
                super().close()

        return huggingface_hub.snapshot_download(
            repo_id,
            cache_dir=self.models_dir,
            tqdm_class=_ProgressTqdm,
        )


class TranscriptionThread(QThread):
    """Runs transcription + post-processing in a background thread.
    Text injection happens in the main thread via the result_ready signal.
    """
    result_ready = pyqtSignal(bool, str)  # not `finished` — see ModelLoadThread

    def __init__(self, audio_data, transcriber, processor, context_detector, language,
                 target_hwnd=None):
        super().__init__()
        self.audio_data = audio_data
        self.transcriber = transcriber
        self.processor = processor
        self.context_detector = context_detector
        self.language = language
        self.target_hwnd = target_hwnd

    def run(self):
        try:
            start = time.time()
            print(f"Transcribing {len(self.audio_data)} samples, lang={self.language}...")

            result = self.transcriber.transcribe(self.audio_data, language=self.language)
            text = result["text"]
            # In auto mode this is the language actually used (ro/en); with a
            # fixed language it is what Whisper was told to use.
            used_lang = result["language"]
            confidence = result.get("confidence", 0.0)

            _log.info(f"Transcribed {len(self.audio_data) / 16000:.1f}s audio in "
                      f"{result.get('transcribe_time', 0):.1f}s ({result.get('mode', '?')}) — "
                      f"model={self.transcriber.model_size}, "
                      f"setting={self.language}, language={used_lang}, confidence={confidence:.2f}")
            if confidence < 0.5:
                print(f"⚠️  Low confidence ({confidence:.2f}). Result may be inaccurate.")

            if not text:
                print("No speech detected")
                self.result_ready.emit(False, "")
                return

            print(f"Transcribed: '{text}'")

            # Context of the window the user was in when they pressed the hotkey
            context = self.context_detector.get_current_context(self.target_hwnd)
            print(f"Context: {context['app_name']}")

            processed = self.processor.process(text, context, language=used_lang)
            print(f"Processed: '{processed}' — total {time.time() - start:.2f}s")

            self.result_ready.emit(True, processed)

        except Exception as e:
            print(f"❌ Transcription thread error: {e}")
            import traceback
            traceback.print_exc()
            self.result_ready.emit(False, "")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _install_crash_handler():
    """Write any unhandled exception to ispeak_crash.log (see _log_dir)."""
    crash_log = os.path.join(_LOG_DIR, "ispeak_crash.log")

    def _hook(exc_type, exc_value, exc_tb):
        import traceback
        try:
            with open(crash_log, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Crash at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
        except Exception:
            pass  # nothing we can do

    sys.excepthook = _hook


def main():
    # FIRST: safe streams — must happen before ANY print / import side-effect.
    # With console=False (windowed app), stdout/stderr may be None or a
    # broken handle that defaults to cp1252 on Windows (can't encode emoji).
    sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
    sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")

    # Global crash handler — writes unhandled exceptions to a file
    _install_crash_handler()

    # QApplication must exist before any Qt object is created
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not _acquire_single_instance():
        QMessageBox.information(None, "iSpeak",
                                "iSpeak is already running — look for its icon in the system tray.")
        return

    voice_app = iSpeakApp()

    def _signal_handler(sig, frame):
        print("\nReceived interrupt signal...")
        voice_app.quit()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    voice_app.run()


if __name__ == "__main__":
    main()
