# ispeak/settings_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QCheckBox, QComboBox, QLabel, QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    LANGUAGES = [
        ("auto", "Auto-detect (Romanian / English)"),
        ("ro",   "Romanian"),
        ("en",   "English"),
    ]

    def __init__(self, settings: dict, input_devices=None, default_device="", parent=None):
        super().__init__(parent)
        self._input_devices = list(input_devices or [])
        self._default_device = default_device
        self.setWindowTitle("iSpeak Settings")
        self.setMinimumWidth(380)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._settings = dict(settings)  # local copy — only applied on OK
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Language & Model ---
        general_group = QGroupBox("General")
        general_layout = QVBoxLayout(general_group)

        # Language
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Language:"))
        self._lang_combo = QComboBox()
        for code, label in self.LANGUAGES:
            self._lang_combo.addItem(label, code)
        idx = self._lang_combo.findData(self._settings.get("language", "auto"))
        self._lang_combo.setCurrentIndex(max(idx, 0))
        self._lang_combo.setToolTip(
            "Auto picks Romanian or English for each dictation.\n"
            "A fixed language that doesn't match what you speak makes\n"
            "Whisper TRANSLATE into that language instead of transcribing.")
        lang_row.addWidget(self._lang_combo)
        general_layout.addLayout(lang_row)

        # Microphone
        mic_row = QHBoxLayout()
        mic_row.addWidget(QLabel("Microphone:"))
        self._mic_combo = QComboBox()
        default_label = (f"Windows default ({self._default_device})"
                         if self._default_device else "Windows default")
        self._mic_combo.addItem(default_label, "")
        for name in self._input_devices:
            self._mic_combo.addItem(name, name)
        selected = self._settings.get("input_device", "")
        if selected and selected not in self._input_devices:
            self._mic_combo.addItem(f"{selected} (not connected)", selected)
        self._mic_combo.setCurrentIndex(max(self._mic_combo.findData(selected), 0))
        self._mic_combo.setToolTip(
            "Microphone used for dictation.\n"
            "If the selected one isn't connected, the Windows default is used.")
        mic_row.addWidget(self._mic_combo)
        general_layout.addLayout(mic_row)

        # Model
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Whisper model:"))
        self._model_combo = QComboBox()
        models = ["tiny", "base", "small", "medium", "large", "turbo"]
        self._model_combo.addItems(models)
        self._model_combo.setCurrentText(self._settings.get("model", "small"))
        model_row.addWidget(self._model_combo)
        general_layout.addLayout(model_row)

        # Auto-Enter
        self._auto_enter_cb = QCheckBox("Auto-press Enter after dictation")
        self._auto_enter_cb.setChecked(self._settings.get("auto_enter", False))
        general_layout.addWidget(self._auto_enter_cb)

        # Fast transcription
        self._fast_cb = QCheckBox("Fast transcription for short dictations")
        self._fast_cb.setChecked(self._settings.get("fast_mode", True))
        self._fast_cb.setToolTip(
            "Whisper normally processes a fixed 30-second window, so even a\n"
            "2-second dictation takes as long as a 30-second one (~4-5s with turbo).\n"
            "This uses a shorter window for short dictations (~4x faster).\n"
            "If a result looks unreliable it is automatically redone the normal way.")
        general_layout.addWidget(self._fast_cb)

        # Spoken code commands
        self._code_cmds_cb = QCheckBox('Spoken code commands in editors ("dot", "comma", "new line"...)')
        self._code_cmds_cb.setChecked(self._settings.get("code_commands", False))
        self._code_cmds_cb.setToolTip(
            "In code editors (VS Code, PyCharm, ...) turn spoken words like\n"
            "\"open paren\", \"dot\", \"equals\", \"new line\" into symbols.\n"
            "Off by default because these words also occur in normal prose."
        )
        general_layout.addWidget(self._code_cmds_cb)

        layout.addWidget(general_group)

        # --- Developer ---
        dev_group = QGroupBox("Developer")
        dev_layout = QVBoxLayout(dev_group)

        self._console_cb = QCheckBox("Show debug console window")
        self._console_cb.setChecked(self._settings.get("show_debug_console", False))
        self._console_cb.setToolTip(
            "Shows a console window with detailed logs.\n"
            "Useful for troubleshooting. Takes effect immediately."
        )
        dev_layout.addWidget(self._console_cb)

        layout.addWidget(dev_group)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> dict:
        """Return the settings dict reflecting the current UI state."""
        return {
            "language": self._lang_combo.currentData(),
            "model": self._model_combo.currentText(),
            "auto_enter": self._auto_enter_cb.isChecked(),
            "code_commands": self._code_cmds_cb.isChecked(),
            "input_device": self._mic_combo.currentData(),
            "fast_mode": self._fast_cb.isChecked(),
            "show_debug_console": self._console_cb.isChecked(),
        }
