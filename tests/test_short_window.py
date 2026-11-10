# tests/test_short_window.py

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ispeak')))

from short_window import _looks_suspicious


def test_normal_sentence_is_fine():
    assert not _looks_suspicious("Te rog să verifici dacă testele trec înainte să facem commit.", 4.3)


def test_short_answer_is_fine():
    assert not _looks_suspicious("Da.", 0.8)


def test_empty_is_suspicious():
    assert _looks_suspicious("", 2.0)


def test_repeated_word_is_suspicious():
    assert _looks_suspicious("Te rog să facem commit. Commit. Commit. Commit.", 4.3)


def test_repeated_sentence_is_suspicious():
    s = "Mâine dimineață trebuie să trimit raportul către echipa de dezvoltare. "
    assert _looks_suspicious((s * 3).strip(), 4.6)


def test_too_much_text_for_speech_is_suspicious():
    assert _looks_suspicious("Aceasta este o propoziție foarte lungă care nu are cum să fie spusă într-o secundă.", 1.0)
