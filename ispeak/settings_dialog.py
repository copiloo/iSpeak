# ispeak/settings_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QCheckBox, QComboBox, QLabel, QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
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
        self._lang_combo.addItems(["English (en)", "Romanian (ro)"])
        self._lang_combo.setCurrentIndex(0 if self._settings["language"] == "en" else 1)
        lang_row.addWidget(self._lang_combo)
        general_layout.addLayout(lang_row)

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
            "language": "en" if self._lang_combo.currentIndex() == 0 else "ro",
            "model": self._model_combo.currentText(),
            "auto_enter": self._auto_enter_cb.isChecked(),
            "show_debug_console": self._console_cb.isChecked(),
        }
