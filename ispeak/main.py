# ispeak/main.py

import sys
import os
import signal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, QTimer
import time

# Import our modules
from audio_capture import AudioCapture
from transcription import TranscriptionEngine
from text_processor import TextProcessor
from text_injector import TextInjector
from hotkey_controller import HotkeyController
from context_detector import ContextDetector
from overlay_widget import OverlayWidget


class iSpeakApp(QObject):
    def __init__(self):
        super().__init__()
        # Initialize components
        print("Initializing iSpeak...")

        self.audio = AudioCapture()
        self.transcriber = TranscriptionEngine(model_size="small")  # Better Romanian accuracy
        self.processor = TextProcessor()
        self.injector = TextInjector()
        self.hotkey = HotkeyController(
            on_start_callback=self.start_dictation,
            on_stop_callback=self.stop_dictation
        )
        self.context = ContextDetector()

        # State
        self.current_language = "ro"
        self.current_model = "small"  # Track current model
        self.auto_press_enter = False  # Auto-press Enter after dictation
        self.is_processing = False
        self.transcription_thread = None
        self.model_download_thread = None

        # UI (System tray)
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in background

        self.tray_icon = self._create_tray_icon()

        # Create status overlay
        self.overlay = OverlayWidget()

        print("iSpeak initialized!")

    def start_dictation(self):
        """Called when hotkey pressed"""
        print("🎤 Recording started...")
        self.tray_icon.setToolTip("🎤 Recording...")
        QTimer.singleShot(0, self.overlay.show_listening)
        self.audio.start_recording()

    def stop_dictation(self):
        """Called when hotkey released"""
        if self.is_processing:
            print("⚠️  Already processing, please wait...")
            return

        print("⏸️  Recording stopped, transcribing...")
        self.tray_icon.setToolTip("⏳ Transcribing...")

        # Get audio data
        audio_data = self.audio.stop_recording()

        # Check if we have audio (4800 samples = 0.3 seconds at 16kHz)
        if len(audio_data) < 4800:  # Less than 0.3 seconds
            print("❌ Recording too short, ignoring (hold key longer)")
            self.tray_icon.setToolTip("✅ Ready")
            QTimer.singleShot(0, self.overlay.hide_overlay)
            return

        # Process in background thread
        self.is_processing = True

        # Clean up previous thread if exists
        if self.transcription_thread is not None:
            if self.transcription_thread.isRunning():
                self.transcription_thread.wait(1000)  # Wait max 1 second
            self.transcription_thread.deleteLater()

        self.transcription_thread = TranscriptionThread(
            audio_data,
            self.transcriber,
            self.processor,
            self.injector,
            self.context,
            self.current_language
        )
        self.transcription_thread.finished.connect(self._on_transcription_done)
        self.transcription_thread.finished.connect(self.transcription_thread.deleteLater)
        self.transcription_thread.start()

        # Show processing animation
        QTimer.singleShot(0, self.overlay.show_processing)

    @pyqtSlot(bool, str)
    def _on_transcription_done(self, success: bool, text: str = ""):
        """Called when transcription completes"""
        print(f"[Main] _on_transcription_done called: success={success}, text_length={len(text) if text else 0}")

        if success and text:
            # Use QTimer to delay text injection slightly
            # This prevents interference with the hotkey listener
            print(f"[Main] Scheduling text injection in 100ms...")
            QTimer.singleShot(100, lambda: self._inject_text(text))
            self.tray_icon.setToolTip("✅ Ready")
        else:
            print("[Main] ❌ Transcription failed")
            self.tray_icon.setToolTip("❌ Error - Ready")

        # Always reset processing flag at the end
        print(f"[Main] Resetting is_processing flag")
        self.is_processing = False
        print(f"[Main] is_processing = {self.is_processing}")

        # Hide the overlay
        QTimer.singleShot(0, self.overlay.hide_overlay)

    def _inject_text(self, text: str):
        """Inject text - called via QTimer to avoid blocking"""
        try:
            print(f"[Main] Starting text injection...")
            self.injector.type_text(text, instant=True)
            print(f"[Main] ✅ Text inserted: '{text[:50]}{'...' if len(text) > 50 else ''}'")

            # Auto-press Enter if enabled
            if self.auto_press_enter:
                print(f"[Main] Auto-pressing Enter...")
                QTimer.singleShot(100, lambda: self.injector.press_key('enter'))
        except Exception as e:
            print(f"[Main] ❌ Error injecting text: {e}")
            import traceback
            traceback.print_exc()

    def toggle_language(self):
        """Switch between Romanian and English"""
        self.current_language = "en" if self.current_language == "ro" else "ro"
        print(f"🌐 Language switched to: {self.current_language.upper()}")
        self.transcriber.set_language(self.current_language)
        self._update_tray_menu()

    def toggle_auto_enter(self):
        """Toggle auto-press Enter after dictation"""
        self.auto_press_enter = not self.auto_press_enter
        status = "enabled" if self.auto_press_enter else "disabled"
        print(f"⏎ Auto-press Enter {status}")
        self._update_tray_menu()

    def switch_model(self, model_name: str):
        """Switch to a different Whisper model"""
        if model_name == self.current_model:
            print(f"Already using {model_name} model")
            return

        if self.is_processing:
            QMessageBox.warning(
                None,
                "Model Switch",
                "Cannot switch models while processing. Please wait and try again."
            )
            return

        print(f"🔄 Switching model from {self.current_model} to {model_name}...")

        # Show confirmation dialog
        msg = QMessageBox()
        msg.setWindowTitle("Switch Model")
        msg.setText(f"Switch to '{model_name}' model?")

        # Add info based on model
        model_info = {
            "tiny": "Fastest, least accurate. ~75MB download.",
            "base": "Fast, fair accuracy. ~142MB download.",
            "small": "Balanced speed and accuracy. ~466MB download. Recommended for Romanian.",
            "medium": "Slower, excellent accuracy. ~1.5GB download.",
            "large": "Slowest, best accuracy. ~2.9GB download."
        }
        msg.setInformativeText(
            f"{model_info.get(model_name, '')}\n\n"
            "If not downloaded, it will be fetched automatically.\n"
            "The app will be unavailable during download."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        if msg.exec() == QMessageBox.StandardButton.Ok:
            # Start model switch in background
            self.is_processing = True  # Block dictation during switch
            self.tray_icon.setToolTip(f"📥 Loading {model_name} model...")

            # Clean up previous download thread if exists
            if self.model_download_thread is not None:
                if self.model_download_thread.isRunning():
                    self.model_download_thread.wait(1000)
                self.model_download_thread.deleteLater()

            self.model_download_thread = ModelLoadThread(model_name)
            self.model_download_thread.finished.connect(self._on_model_loaded)
            self.model_download_thread.progress.connect(self._on_model_download_progress)
            self.model_download_thread.finished.connect(self.model_download_thread.deleteLater)
            self.model_download_thread.start()
        else:
            # User cancelled, update menu to reflect current model
            self._update_tray_menu()

    @pyqtSlot(str)
    def _on_model_download_progress(self, message: str):
        """Update tooltip with download progress"""
        self.tray_icon.setToolTip(message)
        print(message)

    @pyqtSlot(bool, str, object)
    def _on_model_loaded(self, success: bool, model_name: str, model_obj):
        """Called when model loading completes"""
        if success:
            # Replace the transcriber's model
            self.transcriber.model = model_obj
            self.transcriber.model_size = model_name
            self.current_model = model_name

            print(f"✅ Model switched to: {model_name}")
            self.tray_icon.setToolTip("✅ Ready")

            # Show success message
            QMessageBox.information(
                None,
                "Model Loaded",
                f"Successfully switched to '{model_name}' model!"
            )
        else:
            print(f"❌ Failed to load {model_name} model")
            self.tray_icon.setToolTip("❌ Model load failed - Ready")

            # Show error message
            QMessageBox.critical(
                None,
                "Model Load Error",
                f"Failed to load '{model_name}' model. Still using '{self.current_model}'."
            )

        self.is_processing = False
        self._update_tray_menu()

    def _create_tray_icon(self):
        """Create system tray menu"""
        # Create icon
        icon = QSystemTrayIcon()

        # Try to load icon file, fallback to text
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png")
        if os.path.exists(icon_path):
            icon.setIcon(QIcon(icon_path))
        else:
            # Create a simple default icon
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            painter.setBrush(QColor(70, 130, 180))
            painter.drawEllipse(8, 8, 48, 48)
            painter.end()
            icon.setIcon(QIcon(pixmap))

        icon.setToolTip("iSpeak - Ready")

        # Create menu directly here (will be updated later)
        menu = self._create_menu()
        icon.setContextMenu(menu)

        icon.show()
        return icon

    def _create_menu(self):
        """Create the context menu"""
        menu = QMenu()

        # Status
        status_action = menu.addAction(f"Language: {self.current_language.upper()}")
        status_action.setEnabled(False)

        model_status_action = menu.addAction(f"Model: {self.current_model}")
        model_status_action.setEnabled(False)

        menu.addSeparator()

        # Language toggle
        lang_action = menu.addAction("Toggle Language (RO ⇄ EN)")
        lang_action.triggered.connect(self.toggle_language)

        # Auto-press Enter toggle
        auto_enter_action = menu.addAction("Auto-Press Enter After Dictation")
        auto_enter_action.setCheckable(True)
        auto_enter_action.setChecked(self.auto_press_enter)
        auto_enter_action.triggered.connect(self.toggle_auto_enter)

        # Model selection submenu
        model_menu = menu.addMenu("Select Model")

        models = [
            ("tiny", "Tiny (fastest, least accurate)"),
            ("base", "Base (fast, fair accuracy)"),
            ("small", "Small (balanced) ⭐"),
            ("medium", "Medium (slow, excellent)"),
            ("large", "Large (very slow, best)")
        ]

        for model_name, description in models:
            action = model_menu.addAction(description)
            action.setCheckable(True)
            action.setChecked(model_name == self.current_model)
            action.triggered.connect(lambda checked, m=model_name: self.switch_model(m))

        # Settings (placeholder)
        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self._open_settings)

        menu.addSeparator()

        # About
        about_action = menu.addAction("About iSpeak")
        about_action.triggered.connect(self._show_about)

        # Quit
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit)

        return menu

    def _update_tray_menu(self):
        """Update tray menu (called after language change)"""
        menu = self._create_menu()
        self.tray_icon.setContextMenu(menu)

    def _open_settings(self):
        """Open settings dialog (placeholder)"""
        print("Settings dialog - TODO")
        # TODO: Create settings window with:
        # - Model size selection
        # - Hotkey customization
        # - Custom vocabulary editor
        # - Language preferences

    def _show_about(self):
        """Show about dialog"""
        msg = QMessageBox()
        msg.setWindowTitle("About iSpeak")
        msg.setText("iSpeak v0.1.0\n\n"
                   "Offline voice dictation for developers\n\n"
                   "Press Right Alt to start dictating.\n"
                   f"Current language: {self.current_language.upper()}\n\n"
                   "Your voice never leaves your Mac.")
        msg.exec()

    def run(self):
        """Start the application"""
        print("\n" + "="*60)
        print("🚀 iSpeak Started!")
        print("="*60)
        print(f"   Hotkey: {self.hotkey.get_hotkey_name()}")
        print(f"   Language: {self.current_language.upper()} (Romanian)")
        print(f"   Model: {self.transcriber.model_size}")
        print("="*60)
        print("\n⚠️  IMPORTANT: Default language is ROMANIAN (RO)")
        print("   To switch to English: Right-click menu icon > Toggle Language")
        print(f"   Current setting: {self.current_language.upper()}")
        print("\nPress the hotkey and start speaking!")
        print("Right-click the menu bar icon for options.\n")

        # Start hotkey listener
        self.hotkey.start_listening()

        # Run Qt event loop
        sys.exit(self.app.exec())

    def quit(self):
        """Clean shutdown"""
        print("\nShutting down iSpeak...")

        # Stop hotkey listener
        self.hotkey.stop_listening()

        # Wait for transcription thread to finish
        if self.transcription_thread is not None and self.transcription_thread.isRunning():
            print("Waiting for transcription to complete...")
            self.transcription_thread.wait(3000)  # Wait max 3 seconds

        # Clean up audio
        self.audio.cleanup()

        # Hide tray icon
        self.tray_icon.hide()

        # Quit application
        self.app.quit()
        print("Goodbye!")


class ModelLoadThread(QThread):
    """Background thread for loading/downloading Whisper models"""
    finished = pyqtSignal(bool, str, object)  # success, model_name, model_object
    progress = pyqtSignal(str)  # progress message

    def __init__(self, model_name: str, models_dir="./models"):
        super().__init__()
        self.model_name = model_name
        self.models_dir = models_dir

    def run(self):
        """Load model in background with progress updates"""
        try:
            from faster_whisper import WhisperModel
            import os

            self.progress.emit(f"📥 Loading {self.model_name} model...")

            # Check if model exists locally
            model_dir = os.path.join(self.models_dir, f"models--Systran--faster-whisper-{self.model_name}")
            model_exists = os.path.exists(model_dir)

            if not model_exists:
                self.progress.emit(f"📥 Downloading {self.model_name} model... This may take a few minutes.")
                print(f"Model not found locally, downloading from HuggingFace...")
            else:
                self.progress.emit(f"📂 Loading {self.model_name} model from cache...")

            # Load the model (will download if not present)
            start_time = time.time()
            model = WhisperModel(
                self.model_name,
                device="auto",
                compute_type="int8",
                download_root=self.models_dir
            )
            load_time = time.time() - start_time

            self.progress.emit(f"✅ {self.model_name} model loaded in {load_time:.1f}s")
            print(f"Model {self.model_name} loaded successfully in {load_time:.1f}s")

            # Emit success
            self.finished.emit(True, self.model_name, model)

        except Exception as e:
            error_msg = f"❌ Error loading {self.model_name} model: {e}"
            self.progress.emit(error_msg)
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.finished.emit(False, self.model_name, None)


class TranscriptionThread(QThread):
    """Background thread for transcription"""
    finished = pyqtSignal(bool, str)  # success, text

    def __init__(self, audio_data, transcriber, processor,
                 injector, context_detector, language):
        super().__init__()
        self.audio_data = audio_data
        self.transcriber = transcriber
        self.processor = processor
        self.injector = injector
        self.context_detector = context_detector
        self.language = language

    def run(self):
        """Execute transcription in background"""
        try:
            start_time = time.time()

            # 1. Transcribe
            print(f"Transcribing ({len(self.audio_data)} samples) using language: {self.language.upper()}...")
            result = self.transcriber.transcribe(
                self.audio_data,
                language=self.language
            )
            text = result["text"]
            detected_lang = result["language"]
            confidence = result.get("confidence", 0.0)

            transcribe_time = time.time() - start_time
            print(f"Transcription took {transcribe_time:.2f}s")
            print(f"Requested: {self.language.upper()}, Detected: {detected_lang.upper()}, Confidence: {confidence:.2f}")

            # Warn on language mismatch
            if detected_lang != self.language:
                print(f"⚠️  Language mismatch: requested {self.language.upper()}, but detected {detected_lang.upper()}")

            # Warn on low confidence (below 0.5 threshold)
            if confidence < 0.5:
                print(f"⚠️  Low confidence transcription ({confidence:.2f}). Result may be inaccurate.")

            if not text:
                print("No speech detected")
                self.finished.emit(False, "")
                return

            print(f"Transcribed: '{text}'")

            # 2. Get context
            context = self.context_detector.get_current_context()
            print(f"Context: {context['app_name']}")

            # 3. Post-process
            processed_text = self.processor.process(text, context)
            print(f"Processed: '{processed_text}'")

            total_time = time.time() - start_time
            print(f"Total time: {total_time:.2f}s")

            # Emit finished signal with the processed text
            # Text injection will happen in the main thread
            self.finished.emit(True, processed_text)

        except Exception as e:
            print(f"❌ Error in transcription thread: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit(False, "")


def main():
    """Entry point"""
    # Set up signal handlers for clean shutdown
    voice_app = None

    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\nReceived interrupt signal...")
        if voice_app:
            voice_app.quit()
        else:
            sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    voice_app = iSpeakApp()
    voice_app.run()


if __name__ == "__main__":
    main()
