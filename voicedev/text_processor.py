# voicedev/text_processor.py

import re
from typing import Dict, List
import json
import os

class TextProcessor:
    def __init__(self, vocabulary_file="resources/vocabulary.json"):
        self.vocabulary_file = vocabulary_file

        # Custom vocabulary for Romanian tech terms
        self.vocabulary = {
            "git hub": "GitHub",
            "vis code": "VS Code",
            "visual studio code": "VS Code",
            "java script": "JavaScript",
            "type script": "TypeScript",
            "python": "Python",
            "funk ție": "funcție",
            "vari abilă": "variabilă",
            "no duri": "noduri",
            # Add more as users report issues
        }

        # Code patterns (voice commands for coding)
        self.code_patterns = {
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
        self.romanian_corrections = {
            # Function/Method
            "functie": "funcție",
            "functii": "funcții",
            "functia": "funcția",
            "metoda": "metodă",
            "metode": "metode",
            "metodă": "metodă",

            # Variables
            "variabila": "variabilă",
            "variabile": "variabile",
            "variabila": "variabilă",

            # Class
            "clasa": "clasă",
            "clase": "clase",

            # Common programming terms
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
            "liste": "liste",
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

        # Load custom vocabulary if exists
        self._load_vocabulary()

    def process(self, text: str, context: Dict = None) -> str:
        """
        Process transcribed text
        context: dict with 'app_name', 'file_type', etc.
        """
        if not text:
            return ""

        # 1. Apply custom vocabulary
        text = self._apply_vocabulary(text)

        # 2. If in code editor, apply code formatting
        if context and self._is_code_context(context):
            text = self._apply_code_formatting(text)

        # 3. Romanian-specific corrections
        text = self._apply_romanian_corrections(text)

        # 4. Clean up extra spaces
        text = self._cleanup_whitespace(text)

        return text

    def _apply_vocabulary(self, text: str) -> str:
        """Replace custom vocabulary"""
        for wrong, right in self.vocabulary.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(wrong), re.IGNORECASE)
            text = pattern.sub(right, text)
        return text

    def _is_code_context(self, context: Dict) -> bool:
        """Detect if user is in a code editor"""
        code_apps = ['Code', 'VS Code', 'PyCharm', 'Cursor', 'Sublime',
                     'IntelliJ', 'WebStorm', 'Atom', 'Xcode']
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.go',
                          '.rb', '.php', '.swift', '.kt', '.rs']

        app_name = context.get('app_name', '')
        file_type = context.get('file_type', '')

        return (any(app in app_name for app in code_apps) or
                any(file_type.endswith(ext) for ext in code_extensions))

    def _apply_code_formatting(self, text: str) -> str:
        """Apply code-specific formatting"""
        # Replace code patterns
        for spoken, written in self.code_patterns.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(spoken) + r'\b'
            text = re.sub(pattern, written, text, flags=re.IGNORECASE)

        # Handle common code phrases
        text = re.sub(r'\bif\s+(\w+)\s+equals\s+(\w+)\b',
                      r'if \1 == \2', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfor\s+(\w+)\s+in\s+range\b',
                      r'for \1 in range', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdef\s+(\w+)', r'def \1', text, flags=re.IGNORECASE)

        return text

    def _apply_romanian_corrections(self, text: str) -> str:
        """Fix Romanian diacritics that might be missing"""
        for wrong, right in self.romanian_corrections.items():
            # Only replace whole words
            pattern = r'\b' + re.escape(wrong) + r'\b'
            text = re.sub(pattern, right, text, flags=re.IGNORECASE)
        return text

    def _cleanup_whitespace(self, text: str) -> str:
        """Remove extra spaces and fix punctuation spacing"""
        # Multiple spaces -> single space
        text = re.sub(r'\s+', ' ', text)

        # Remove space before punctuation
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)

        # Add space after punctuation (if missing)
        text = re.sub(r'([,.;:!?])([A-Za-z])', r'\1 \2', text)

        return text.strip()

    def add_custom_word(self, spoken: str, written: str):
        """Allow users to add custom vocabulary"""
        self.vocabulary[spoken.lower()] = written
        self._save_vocabulary()

    def _load_vocabulary(self):
        """Load custom vocabulary from file"""
        if os.path.exists(self.vocabulary_file):
            try:
                with open(self.vocabulary_file, 'r', encoding='utf-8') as f:
                    custom = json.load(f)
                    self.vocabulary.update(custom)
                print(f"Loaded {len(custom)} custom vocabulary entries")
            except Exception as e:
                print(f"Error loading vocabulary: {e}")

    def _save_vocabulary(self):
        """Save custom vocabulary to file"""
        try:
            os.makedirs(os.path.dirname(self.vocabulary_file), exist_ok=True)
            with open(self.vocabulary_file, 'w', encoding='utf-8') as f:
                json.dump(self.vocabulary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving vocabulary: {e}")
