# tests/test_processor.py

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ispeak.text_processor import TextProcessor

VSCODE = {'app_name': 'Code', 'file_type': ''}
NOTEPAD = {'app_name': 'notepad', 'file_type': '.txt'}


@pytest.fixture
def processor():
    return TextProcessor()


@pytest.fixture
def code_processor():
    return TextProcessor(code_commands_enabled=True)


# --- vocabulary ------------------------------------------------------------

def test_custom_vocabulary(processor):
    assert "VS Code" in processor.process("I'm using visual studio code")


def test_vocabulary_keeps_dotted_names(processor):
    assert processor.process("I use node js and visit example.com") == \
        "I use Node.js and visit example.com"


def test_vocabulary_comment_keys_are_ignored(processor):
    assert not any(k.startswith('_') for k in processor._vocabulary_map)


def test_add_custom_word(tmp_path):
    vocab = tmp_path / "vocabulary.json"
    processor = TextProcessor(vocabulary_file=str(vocab))
    processor.add_custom_word("test word", "TestWord")
    assert "TestWord" in processor.process("this is a test word example")
    assert vocab.exists()


# --- Romanian --------------------------------------------------------------

def test_romanian_is_not_translated_to_english(processor):
    text = "Aceasta funcție returnează o listă"
    assert processor.process(text, language="ro") == text
    assert processor.process(text, language="en") == text


def test_romanian_articulated_forms_untouched(processor):
    text = "Deschide clasa și metoda din lista"
    assert processor.process(text, language="ro") == text


def test_romanian_missing_diacritics_fixed(processor):
    assert "funcție" in processor.process("aceasta este o functie", language="ro")


def test_romanian_fixes_not_applied_to_english(processor):
    assert processor.process("functie", language="en") == "functie"


# --- code commands ---------------------------------------------------------

def test_code_commands_off_by_default(processor):
    text = "Please add a comma here, then a period at the end"
    assert processor.process(text, VSCODE) == text


def test_code_commands_only_in_code_editors(code_processor):
    text = "add a comma here"
    assert code_processor.process(text, NOTEPAD) == text


@pytest.mark.parametrize("spoken, expected", [
    ("x plus plus new line y equals 1", "x++\ny = 1"),
    ("call os dot path dot join", "call os.path.join"),
    ("print open paren x comma y close paren", "print(x, y)"),
    ("if x double equals 5 colon", "if x == 5:"),
    ("items open bracket 0 close bracket", "items[0]"),
    ("i minus minus semicolon", "i--;"),
    ("if x open brace", "if x {"),
])
def test_code_commands(code_processor, spoken, expected):
    assert code_processor.process(spoken, VSCODE) == expected


def test_code_context_detection():
    assert TextProcessor._is_code_context({'app_name': 'pycharm64'})
    assert TextProcessor._is_code_context({'app_name': 'Code - Insiders'})
    assert not TextProcessor._is_code_context({'app_name': 'WINWORD'})


# --- whitespace ------------------------------------------------------------

def test_whitespace_cleanup(processor):
    assert processor.process("hello  world   test") == "hello world test"


def test_punctuation_spacing(processor):
    processed = processor.process("hello , world .")
    assert processed == "hello, world."


def test_space_after_comma_added(processor):
    assert processor.process("hello,world") == "hello, world"


def test_empty_text(processor):
    assert processor.process("") == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
