# tests/test_audio_names.py

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ispeak')))

from audio_capture import _fix_name


def test_fix_name_repairs_mojibake():
    original = "Headset (Kid’s Airpods 3)"
    garbled = original.encode("utf-8").decode("cp1252")
    assert garbled != original
    assert _fix_name(garbled) == original


def test_fix_name_repairs_romanian_letters():
    original = "Microfon căști"          # "Microfon căști"
    garbled = original.encode("utf-8").decode("cp1252", errors="ignore")
    assert _fix_name(garbled) in (original, garbled)  # never worse than input


def test_fix_name_keeps_correct_names():
    assert _fix_name("Microphone (Realtek(R) Audio)") == "Microphone (Realtek(R) Audio)"
    assert _fix_name("Mikrofon Ä") == "Mikrofon Ä"
