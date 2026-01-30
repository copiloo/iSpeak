# tests/test_processor.py

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ispeak.text_processor import TextProcessor


def test_custom_vocabulary():
    """Test vocabulary replacement"""
    processor = TextProcessor()

    text = "I'm using visual studio code"
    processed = processor.process(text)

    assert "VS Code" in processed


def test_romanian_corrections():
    """Test Romanian diacritics"""
    processor = TextProcessor()

    text = "aceasta este o functie"
    processed = processor.process(text)

    assert "funcție" in processed


def test_code_formatting():
    """Test code pattern replacement"""
    processor = TextProcessor()

    context = {'app_name': 'VS Code', 'file_type': '.py'}
    text = "if x equals 5 new line print hello"
    processed = processor.process(text, context)

    # Check that code patterns were applied
    assert "==" in processed or "equals" not in processed.lower()


def test_whitespace_cleanup():
    """Test whitespace cleanup"""
    processor = TextProcessor()

    text = "hello  world   test"
    processed = processor.process(text)

    # Should have single spaces
    assert "  " not in processed
    assert processed == "hello world test"


def test_punctuation_spacing():
    """Test punctuation spacing"""
    processor = TextProcessor()

    text = "hello , world .test"
    processed = processor.process(text)

    # Should remove space before punctuation
    assert " ," not in processed
    assert " ." not in processed


def test_empty_text():
    """Test handling of empty text"""
    processor = TextProcessor()

    text = ""
    processed = processor.process(text)

    assert processed == ""


def test_add_custom_word():
    """Test adding custom vocabulary"""
    processor = TextProcessor()

    processor.add_custom_word("test word", "TestWord")

    text = "this is a test word example"
    processed = processor.process(text)

    assert "TestWord" in processed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
