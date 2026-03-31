# ispeak/text_processor.py

import re
import os
import json
from typing import Dict

# Pre-built static regex for whitespace cleanup (compiled once at module level)
_RE_MULTI_SPACE = re.compile(r'\s+')
_RE_SPACE_BEFORE_PUNCT = re.compile(r'\s+([,.;:!?])')
_RE_PUNCT_NO_SPACE = re.compile(r'([,.;:!?])([A-Za-z])')
_RE_IF_EQUALS = re.compile(r'\bif\s+(\w+)\s+equals\s+(\w+)\b', re.IGNORECASE)
_RE_FOR_IN_RANGE = re.compile(r'\bfor\s+(\w+)\s+in\s+range\b', re.IGNORECASE)
_RE_DEF = re.compile(r'\bdef\s+(\w+)', re.IGNORECASE)


def _build_pattern_list(mapping: dict) -> list:
    """Compile a dict of {spoken: written} into a list of (pattern, replacement)."""
    return [
        (re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE), v)
        for k, v in mapping.items()
    ]


class TextProcessor:
    def __init__(self, vocabulary_file=None):
        # Resolve vocabulary path relative to this file so it works regardless of cwd
        if vocabulary_file is None:
            _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            vocabulary_file = os.path.join(_base, "resources", "vocabulary.json")
        self.vocabulary_file = vocabulary_file

        # Custom vocabulary for Romanian tech terms
        self._vocabulary_map = {
            "git hub": "GitHub",
            "vis code": "VS Code",
            "visual studio code": "VS Code",
            "java script": "JavaScript",
            "type script": "TypeScript",
            "python": "Python",
            "funk ție": "funcție",
            "vari abilă": "variabilă",
            "no duri": "noduri",
        }

        # Code patterns (voice commands for coding)
        self._code_map = {
            "new line": "\n",
            "tab": "\t",
            "open brace": " {",
            "close brace": "}",
            "open bracket": "[",
            "close bracket": "]",
            "open paren": "(",
            "close paren": ")",
            "semicolon": ";",
            "colon": ":",
            "comma": ",",
            "period": ".",
            "equals": " = ",
            "plus": " + ",
            "minus": " - ",
            "plus plus": "++",
            "minus minus": "--",
            "arrow": " => ",
            "dot": ".",
        }

        # Romanian autocorrect (common diacritics issues)
        self._romanian_map = {
            "functie": "funcție",
            "functii": "funcții",
            "functia": "funcția",
            "metoda": "metodă",
            "metodă": "metodă",
            "variabila": "variabilă",
            "clasa": "clasă",
            "pentru": "pentru",
            "intrare": "intrare",
            "iesire": "ieșire",
            "fisier": "fișier",
            "fisiere": "fișiere",
            "calcul": "calcul",
            "valoare": "valoare",
            "valori": "valori",
            "rezultat": "rezultat",
            "rezultate": "rezultate",
            "lista": "listă",
            "dictionar": "dicționar",
            "dictionare": "dicționare",
            "conditie": "condiție",
            "conditii": "condiții",
            "exceptie": "excepție",
            "exceptii": "excepții",
            "verificare": "verificare",
            "iteratie": "iterație",
            "iteratii": "iterații",
            "instructiune": "instrucțiune",
            "instructiuni": "instrucțiuni",
            "adauga": "adaugă",
            "sterge": "șterge",
            "actualizeaza": "actualizează",
            "cauta": "caută",
            "gaseste": "găsește",
            "afiseaza": "afișează",
            "returneaza": "returnează",
            "verifica": "verifică",
            "executa": "execută",
            "initializeaza": "inițializează",
        }

        # Load custom vocabulary from file (merges into _vocabulary_map)
        self._load_vocabulary()

        # Compile all patterns once
        self._vocab_patterns = _build_pattern_list(self._vocabulary_map)
        self._code_patterns = _build_pattern_list(self._code_map)
        self._romanian_patterns = _build_pattern_list(self._romanian_map)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, text: str, context: Dict = None) -> str:
        if not text:
            return ""

        text = self._apply_patterns(text, self._vocab_patterns)

        if context and self._is_code_context(context):
            text = self._apply_code_formatting(text)

        text = self._apply_patterns(text, self._romanian_patterns)
        text = self._cleanup_whitespace(text)
        return text

    def add_custom_word(self, spoken: str, written: str):
        """Add a custom vocabulary entry and recompile patterns."""
        self._vocabulary_map[spoken.lower()] = written
        # Recompile only the vocabulary patterns
        self._vocab_patterns = _build_pattern_list(self._vocabulary_map)
        self._save_vocabulary()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_patterns(text: str, patterns: list) -> str:
        for pattern, replacement in patterns:
            text = pattern.sub(replacement, text)
        return text

    def _is_code_context(self, context: Dict) -> bool:
        code_apps = ['Code', 'VS Code', 'PyCharm', 'pycharm', 'Cursor', 'Sublime',
                     'IntelliJ', 'idea', 'WebStorm', 'webstorm', 'Atom', 'Xcode', 'Fleet']
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.go',
                           '.rb', '.php', '.swift', '.kt', '.rs']

        app_name = context.get('app_name', '')
        file_type = context.get('file_type', '')

        return (any(app.lower() in app_name.lower() for app in code_apps) or
                any(file_type.endswith(ext) for ext in code_extensions))

    def _apply_code_formatting(self, text: str) -> str:
        text = self._apply_patterns(text, self._code_patterns)
        text = _RE_IF_EQUALS.sub(r'if \1 == \2', text)
        text = _RE_FOR_IN_RANGE.sub(r'for \1 in range', text)
        text = _RE_DEF.sub(r'def \1', text)
        return text

    @staticmethod
    def _cleanup_whitespace(text: str) -> str:
        text = _RE_MULTI_SPACE.sub(' ', text)
        text = _RE_SPACE_BEFORE_PUNCT.sub(r'\1', text)
        text = _RE_PUNCT_NO_SPACE.sub(r'\1 \2', text)
        return text.strip()

    def _load_vocabulary(self):
        if os.path.exists(self.vocabulary_file):
            try:
                with open(self.vocabulary_file, 'r', encoding='utf-8') as f:
                    custom = json.load(f)
                    self._vocabulary_map.update(custom)
                print(f"Loaded {len(custom)} custom vocabulary entries")
            except Exception as e:
                print(f"Error loading vocabulary: {e}")

    def _save_vocabulary(self):
        try:
            vocab_dir = os.path.dirname(self.vocabulary_file)
            if vocab_dir:
                os.makedirs(vocab_dir, exist_ok=True)
            with open(self.vocabulary_file, 'w', encoding='utf-8') as f:
                json.dump(self._vocabulary_map, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving vocabulary: {e}")
