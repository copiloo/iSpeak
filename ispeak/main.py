# ispeak/main.py

import sys
import os
import signal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, QTimer
import time

from audio_capture import AudioCapture
from transcription import TranscriptionEngine
from text_processor import TextProcessor
from text_injector import TextInjector
from hotkey_controller import HotkeyController
from context_detector import ContextDetector
from overlay_widget import OverlayWidget
from settings_dialog import SettingsDialog
import settings_manager
import logging

# ---------------------------------------------------------------------------
# Logging — always write to a file so crashes are diagnosable even without
# the debug console.  The log lives next to the executable (or next to
# main.py when running from source).
# ---------------------------------------------------------------------------

def _app_dir() -> str:
    """Directory that holds the exe (frozen) or the project root (source)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_log_path = os.path.join(_app_dir(), "ispeak.log")
_log_handler = logging.FileHandler(_log_path, encoding="utf-8", errors="replace")
_log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
_log = logging.getLogger("iSpeak")
_log.setLevel(logging.INFO)
_log.addHandler(_log_handler)


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
    # Used to safely hand audio data from pynput's listener thread to the Qt main thread
    _audio_ready = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        print("Initializing iSpeak...")

        # Load persisted settings first
        self._settings = settings_manager.load()
        _set_console_visible(self._settings.get("show_debug_console", False))

        self.audio = AudioCapture()
        self.transcriber = None          # loaded async after tray appears
        self.processor = TextProcessor()
        self.injector = TextInjector()
        self.hotkey = HotkeyController(
            on_start_callback=self.start_dictation,
            on_stop_callback=self.stop_dictation
        )
        self.context = ContextDetector()

        # State — seeded from saved settings
        self.current_language = self._settings.get("language", "en")
        self.current_model = self._settings.get("model", "small")
        self.auto_press_enter = self._settings.get("auto_enter", False)
        self.is_processing = True        # Block dictation until model is ready

        # Threads — kept as instance vars to prevent premature GC; replaced on each use
        self._transcription_thread = None
        self._model_load_thread = None
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

        # Bridge pynput listener thread → Qt main thread for delayed focus capture
        self._audio_ready.connect(self._on_audio_ready_qt)

        # Show tray icon FIRST — model loads in background after event loop starts
        self.tray_icon = self._create_tray_icon()
        self.overlay = OverlayWidget()

        print("iSpeak tray icon ready. Loading model in background...")

    # ------------------------------------------------------------------
    # Dictation lifecycle
    # ------------------------------------------------------------------

    def start_dictation(self):
        if self.transcriber is None or self.is_processing:
            print("⚠️  Model not ready yet, please wait...")
            return
        # Capture focus NOW — user is in their target window at press time.
        # pynput hooks fire before the app processes Alt, so child focus is still correct.
        from text_injector import get_focus_info
        self._target_hwnd, self._target_focus_hwnd = get_focus_info()
        print(f"🎤 Recording started...")
        self.tray_icon.setToolTip("🎤 Recording...")
        self.audio.start_recording()
        QTimer.singleShot(0, self.overlay.show_listening)

    def stop_dictation(self):
        if self.is_processing:
            print("⚠️  Already processing, please wait...")
            return

        print("⏸️  Recording stopped, transcribing...")
        self.tray_icon.setToolTip("⏳ Transcribing...")

        audio_data = self.audio.stop_recording()

        if len(audio_data) < 4800:  # < 0.3 seconds at 16kHz
            print("❌ Recording too short, ignoring")
            self.tray_icon.setToolTip("✅ Ready")
            QTimer.singleShot(0, self.overlay.hide_overlay)
            return

        self.is_processing = True
        QTimer.singleShot(0, self.overlay.show_processing)

        # Emit signal to hand audio data to the Qt main thread.
        # Can't use QTimer.singleShot(150, ...) directly here because stop_dictation()
        # runs in pynput's listener thread which has no Qt event dispatcher.
        self._audio_ready.emit(audio_data)

    @pyqtSlot(object)
    def _on_audio_ready_qt(self, audio_data):
        """Runs in Qt main thread. Focus was already captured at press time."""
        self._start_transcription_thread(audio_data)

    def _start_transcription_thread(self, audio_data):
        """Safely replace the transcription thread."""
        old = self._transcription_thread
        if old is not None:
            try:
                old.finished.disconnect()
                if old.isRunning():
                    old.wait(2000)
                old.deleteLater()
            except RuntimeError:
                pass  # C++ object already deleted — safe to ignore

        thread = TranscriptionThread(
            audio_data,
            self.transcriber,
            self.processor,
            self.context,
            self.current_language,
        )
        thread.finished.connect(self._on_transcription_done)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self._transcription_thread = thread

    @pyqtSlot(bool, str)
    def _on_transcription_done(self, success: bool, text: str = ""):
        # Clear the reference now — the thread's deleteLater() fires after this slot
        # returns (connected second). Keeping the reference would leave a dangling
        # C++ pointer that crashes on the next isRunning() / disconnect() call.
        self._transcription_thread = None
        print(f"[Main] Transcription done: success={success}, len={len(text) if text else 0}")

        if success and text:
            QTimer.singleShot(0, lambda: self._inject_text(text))
            self.tray_icon.setToolTip("✅ Ready")
        else:
            print("[Main] ❌ Transcription failed or empty")
            self.tray_icon.setToolTip("❌ Error - Ready")

        self.is_processing = False
        QTimer.singleShot(0, self.overlay.hide_overlay)

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
            if self.auto_press_enter:
                QTimer.singleShot(100, lambda: self.injector.press_key('enter'))
        except Exception as e:
            print(f"[Main] ❌ Error injecting text: {e}")
            import traceback
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Language / model controls
    # ------------------------------------------------------------------

    def toggle_language(self):
        self.current_language = "en" if self.current_language == "ro" else "ro"
        print(f"🌐 Language: {self.current_language.upper()}")
        self.transcriber.set_language(self.current_language)
        self._update_tray_menu()

    def toggle_auto_enter(self):
        self.auto_press_enter = not self.auto_press_enter
        print(f"⏎ Auto-press Enter {'enabled' if self.auto_press_enter else 'disabled'}")
        self._update_tray_menu()

    def switch_model(self, model_name: str):
        if model_name == self.current_model:
            return

        if self.is_processing:
            QMessageBox.warning(None, "Model Switch",
                                "Cannot switch models while processing.")
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

        self.is_processing = True
        self.tray_icon.setToolTip(f"Loading {model_name} model...")
        # Rebuild menu immediately so the clicked item's checkmark is cleared
        # (Qt visually toggles it on click, but current_model hasn't changed yet)
        self._update_tray_menu()
        self._start_model_load_thread(model_name)

    def _start_model_load_thread(self, model_name: str):
        """Safely replace the model load thread."""
        old = self._model_load_thread
        if old is not None:
            try:
                old.finished.disconnect()
                old.progress.disconnect()
            except RuntimeError:
                pass
            if old.isRunning():
                old.wait(2000)
            old.deleteLater()

        models_dir = os.path.join(_app_dir(), "models")
        thread = ModelLoadThread(model_name, models_dir=models_dir)
        thread.finished.connect(self._on_model_loaded)
        thread.progress.connect(self._on_model_download_progress)
        # Do NOT connect thread.deleteLater to finished — it races with
        # _on_model_loaded and can destroy the thread mid-callback.
        # Cleanup happens in _start_model_load_thread (for the old thread)
        # and _on_model_loaded (clears the reference).
        thread.start()
        self._model_load_thread = thread

    @pyqtSlot(str)
    def _on_model_download_progress(self, message: str):
        self.tray_icon.setToolTip(message)
        print(message)

    @pyqtSlot(bool, str, object)
    def _on_model_loaded(self, success: bool, model_name: str, backend_info: dict):
        # Clear the thread reference so the next load can clean it up.
        # Do NOT call deleteLater() here — Qt may still be dispatching
        # queued signals from this same thread object.
        self._model_load_thread = None

        is_initial_load = self.transcriber is None

        if success:
            if self.transcriber is None:
                # First load — create the TranscriptionEngine shell and inject the loaded model
                self.transcriber = TranscriptionEngine.__new__(TranscriptionEngine)
                self.transcriber.current_language = self.current_language
                self.transcriber.models_dir = os.path.join(_app_dir(), "models")
                self.transcriber.use_mlx = False
                self.transcriber.mlx_model_path = None
                self.transcriber.model = None

            self.transcriber.model_size = model_name
            self.transcriber.backend = backend_info.get("backend", "faster-whisper")
            if backend_info.get("model"):
                self.transcriber.model = backend_info["model"]
            if backend_info.get("mlx_model_path"):
                self.transcriber.mlx_model_path = backend_info["mlx_model_path"]
                self.transcriber.use_mlx = True
            self.current_model = model_name

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

        status = menu.addAction(f"Language: {self.current_language.upper()}")
        status.setEnabled(False)

        if self.transcriber is not None:
            backend_info = self.transcriber.get_backend_info()
            backend_label = "MLX" if backend_info['using_mlx'] else "FW"
            model_status = menu.addAction(f"Model: {self.current_model} ({backend_label})")
        else:
            model_status = menu.addAction(f"Model: {self.current_model} (loading...)")
        model_status.setEnabled(False)

        menu.addSeparator()

        lang_action = menu.addAction("Toggle Language (RO ⇄ EN)")
        lang_action.triggered.connect(self.toggle_language)

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
            "show_debug_console": self._settings.get("show_debug_console", False),
        }
        dlg = SettingsDialog(current)
        if dlg.exec() != SettingsDialog.DialogCode.Accepted:
            return

        new = dlg.get_settings()

        # Apply language change
        if new["language"] != self.current_language:
            self.current_language = new["language"]
            if self.transcriber:
                self.transcriber.set_language(self.current_language)

        # Apply model change
        if new["model"] != self.current_model:
            self.switch_model(new["model"])

        # Apply auto-enter
        self.auto_press_enter = new["auto_enter"]

        # Apply debug console visibility immediately
        if new["show_debug_console"] != self._settings.get("show_debug_console", False):
            _set_console_visible(new["show_debug_console"])

        self._settings.update(new)
        settings_manager.save(self._settings)
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
            f"Language: {self.current_language.upper()}\n"
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
        print(f"   Language: {self.current_language.upper()}")
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
        # Persist current state
        self._settings.update({
            "language": self.current_language,
            "model": self.current_model,
            "auto_enter": self.auto_press_enter,
        })
        settings_manager.save(self._settings)
        self.hotkey.stop_listening()

        if self._transcription_thread is not None and self._transcription_thread.isRunning():
            print("Waiting for transcription to finish...")
            self._transcription_thread.wait(3000)

        self.audio.cleanup()
        self.tray_icon.hide()
        QApplication.instance().quit()
        print("Goodbye!")


# ---------------------------------------------------------------------------
# Background threads
# ---------------------------------------------------------------------------

class ModelLoadThread(QThread):
    """Downloads / loads a Whisper model in the background."""
    finished = pyqtSignal(bool, str, object)
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
                self.finished.emit(True, self.model_name, {
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
            self.finished.emit(True, self.model_name, {
                "backend": "faster-whisper",
                "model": model,
                "mlx_model_path": None,
            })
        except Exception as e:
            error_msg = f"Error loading {self.model_name}: {e}"
            _log.error(error_msg, exc_info=True)
            self.progress.emit(error_msg)
            self.finished.emit(False, self.model_name, {})

    def _download_with_progress(self, repo_id: str) -> str:
        """Download a HuggingFace model with real-time progress reporting."""
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
                        f"Downloading {thread_ref.model_name}: "
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
    Text injection happens in the main thread via the finished signal.
    """
    finished = pyqtSignal(bool, str)

    def __init__(self, audio_data, transcriber, processor, context_detector, language):
        super().__init__()
        self.audio_data = audio_data
        self.transcriber = transcriber
        self.processor = processor
        self.context_detector = context_detector
        self.language = language

    def run(self):
        try:
            start = time.time()
            print(f"Transcribing {len(self.audio_data)} samples, lang={self.language.upper()}...")

            result = self.transcriber.transcribe(self.audio_data, language=self.language)
            text = result["text"]
            detected_lang = result["language"]
            confidence = result.get("confidence", 0.0)
            backend = result.get("backend", "unknown")

            print(f"Transcription: {result.get('transcribe_time', 0):.2f}s ({backend})")
            print(f"Requested: {self.language.upper()}, Detected: {detected_lang.upper()}, "
                  f"Confidence: {confidence:.2f}")

            if detected_lang != self.language:
                print(f"⚠️  Language mismatch: requested {self.language.upper()}, "
                      f"detected {detected_lang.upper()}")
            if confidence < 0.5:
                print(f"⚠️  Low confidence ({confidence:.2f}). Result may be inaccurate.")

            if not text:
                print("No speech detected")
                self.finished.emit(False, "")
                return

            print(f"Transcribed: '{text}'")

            context = self.context_detector.get_current_context()
            print(f"Context: {context['app_name']}")

            processed = self.processor.process(text, context)
            print(f"Processed: '{processed}' — total {time.time() - start:.2f}s")

            self.finished.emit(True, processed)

        except Exception as e:
            print(f"❌ Transcription thread error: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit(False, "")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _install_crash_handler():
    """Write any unhandled exception to ispeak_crash.log next to the exe."""
    crash_log = os.path.join(_app_dir(), "ispeak_crash.log")

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

    voice_app = iSpeakApp()

    def _signal_handler(sig, frame):
        print("\nReceived interrupt signal...")
        voice_app.quit()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    voice_app.run()


if __name__ == "__main__":
    main()
