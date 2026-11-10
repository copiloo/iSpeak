# ispeak/text_processor.py

import re
import os
import sys
import json
from typing import Dict, Optional

# Whitespace cleanup (compiled once).  These deliberately only touch spaces,
# never newlines/tabs, so that spoken "new line" / "tab" commands survive.
_RE_MULTI_SPACE = re.compile(r' {2,}')
_RE_SPACE_AROUND_NEWLINE = re.compile(r' *\n *')
# "hello , world" -> "hello, world" — only when the punctuation ends a word,
# so ".NET" / "./run" are left alone.
_RE_SPACE_BEFORE_PUNCT = re.compile(r' +([,.;:!?])(?=\s|$)')
# "hello,world" -> "hello, world".  Periods and colons are excluded on purpose:
# adding a space after them breaks "Node.js", "example.com", "C:\" etc.
_RE_PUNCT_NO_SPACE = re.compile(r'([,;!?])([A-Za-z])')


def _build_pattern_list(mapping: dict) -> list:
    """Compile {spoken: written} into (pattern, replacement), longest phrase first
    so that e.g. "visual studio code" wins over a shorter overlapping entry."""
    return [
        (re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE), v)
        for k, v in sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)
    ]


# ---------------------------------------------------------------------------
# Spoken code commands (opt-in, only applied in code editors).
# glue = which neighbouring spaces the symbol swallows:
#   "both"  -> os dot path        => os.path
#   "left"  -> x comma y          => x, y
#   "right" -> open brace         => {   (keeps the space before it)
#   "none"  -> x equals 1         => x = 1
# ---------------------------------------------------------------------------
_CODE_COMMANDS = [
    ("new line",     "\n",   "both"),
    ("tab key",      "\t",   "both"),
    ("open paren",   "(",    "both"),
    ("close paren",  ")",    "left"),
    ("open bracket", "[",    "both"),
    ("close bracket", "]",   "left"),
    ("open brace",   "{",    "right"),
    ("close brace",  "}",    "none"),
    ("semicolon",    ";",    "left"),
    ("colon",        ":",    "left"),
    ("comma",        ",",    "left"),
    ("period",       ".",    "left"),
    ("dot",          ".",    "both"),
    ("double equals", " == ", "none"),
    ("not equals",   " != ", "none"),
    ("equals",       " = ",  "none"),
    ("plus plus",    "++",   "left"),
    ("minus minus",  "--",   "left"),
    ("plus",         " + ",  "none"),
    ("minus",        " - ",  "none"),
    ("arrow",        " => ", "none"),
]


def _build_code_rules() -> list:
    rules = []
    for spoken, written, glue in sorted(_CODE_COMMANDS, key=lambda c: len(c[0]), reverse=True):
        left = r' *' if glue in ("both", "left") else ''
        right = r' *' if glue in ("both", "right") else ''
        pattern = re.compile(left + r'\b' + re.escape(spoken) + r'\b' + right, re.IGNORECASE)
        # Use a function so "\n" / "\t" are inserted literally (no escape processing)
        rules.append((pattern, lambda _m, w=written: w))
    return rules


_CODE_RULES = _build_code_rules()


# Romanian words Whisper sometimes outputs without diacritics.  Only entries
# that are NOT valid Romanian words on their own belong here (e.g. "clasa",
# "lista", "metoda" are correct articulated forms and must not be touched).
_ROMANIAN_DIACRITICS = {
    "functie": "funcție",
    "functii": "funcții",
    "functia": "funcția",
    "iesire": "ieșire",
    "fisier": "fișier",
    "fisiere": "fișiere",
    "fisierul": "fișierul",
    "dictionar": "dicționar",
    "dictionare": "dicționare",
    "conditie": "condiție",
    "conditii": "condiții",
    "exceptie": "excepție",
    "exceptii": "excepții",
    "iteratie": "iterație",
    "iteratii": "iterații",
    "instructiune": "instrucțiune",
    "instructiuni": "instrucțiuni",
    "sterge": "șterge",
    "actualizeaza": "actualizează",
    "gaseste": "găsește",
    "afiseaza": "afișează",
    "returneaza": "returnează",
    "initializeaza": "inițializează",
}


def _default_vocabulary_path() -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "resources", "vocabulary.json")


class TextProcessor:
    def __init__(self, vocabulary_file=None, code_commands_enabled=False):
        self.vocabulary_file = vocabulary_file or _default_vocabulary_path()
        # Spoken symbols ("comma", "dot", ...) collide with ordinary prose, so
        # they are only applied when the user explicitly opts in.
        self.code_commands_enabled = code_commands_enabled

        # Built-in tech-term fixes (multi-word mis-hearings only; plain
        # dictionary words are left alone).
        self._vocabulary_map = {
            "git hub": "GitHub",
            "vis code": "VS Code",
            "visual studio code": "VS Code",
            "java script": "JavaScript",
            "type script": "TypeScript",
        }

        # Load custom vocabulary from file (merges into _vocabulary_map)
        self._load_vocabulary()

        # Compile all patterns once
        self._vocab_patterns = _build_pattern_list(self._vocabulary_map)
        self._romanian_patterns = _build_pattern_list(_ROMANIAN_DIACRITICS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, text: str, context: Optional[Dict] = None,
                language: Optional[str] = None) -> str:
        if not text:
            return ""

        text = self._apply_patterns(text, self._vocab_patterns)

        if language == "ro":
            text = self._apply_patterns(text, self._romanian_patterns)

        if self.code_commands_enabled and context and self._is_code_context(context):
            text = self._apply_patterns(text, _CODE_RULES)

        return self._cleanup_whitespace(text)

    def add_custom_word(self, spoken: str, written: str):
        """Add a custom vocabulary entry and recompile patterns."""
        self._vocabulary_map[spoken.lower()] = written
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

    @staticmethod
    def _is_code_context(context: Dict) -> bool:
        # Exe names without ".exe"; prefix match covers "pycharm64", "Code - Insiders", ...
        code_apps = ('code', 'cursor', 'windsurf', 'pycharm', 'idea', 'webstorm',
                     'goland', 'rider', 'clion', 'sublime_text', 'notepad++',
                     'devenv', 'zed', 'fleet')
        code_extensions = ('.py', '.js', '.ts', '.java', '.cpp', '.go',
                           '.rb', '.php', '.swift', '.kt', '.rs')

        app_name = context.get('app_name', '').lower()
        file_type = context.get('file_type', '')

        return app_name.startswith(code_apps) or file_type.endswith(code_extensions)

    @staticmethod
    def _cleanup_whitespace(text: str) -> str:
        text = _RE_MULTI_SPACE.sub(' ', text)
        text = _RE_SPACE_AROUND_NEWLINE.sub('\n', text)
        text = _RE_SPACE_BEFORE_PUNCT.sub(r'\1', text)
        text = _RE_PUNCT_NO_SPACE.sub(r'\1 \2', text)
        return text.strip(' ')

    def _load_vocabulary(self):
        if not os.path.exists(self.vocabulary_file):
            return
        try:
            with open(self.vocabulary_file, 'r', encoding='utf-8') as f:
                custom = json.load(f)
            # Keys starting with "_" are comments, not vocabulary entries
            entries = {k.lower(): v for k, v in custom.items()
                       if not k.startswith('_') and isinstance(v, str)}
            self._vocabulary_map.update(entries)
            print(f"Loaded {len(entries)} custom vocabulary entries")
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
