//
//  RomanianCorrector.swift
//  iSpeak
//
//  Romanian diacritics corrections for programming terms
//  Matches Python's romanian_corrections from text_processor.py lines 49-101
//

import Foundation

/// Romanian diacritics corrector
struct RomanianCorrector {
    /// Romanian correction mappings
    /// Python: self.romanian_corrections dictionary
    private let corrections: [String: String] = [
        // Function/Method (lines 51-57)
        "functie": "funcție",
        "functii": "funcții",
        "functia": "funcția",
        "metoda": "metodă",
        "metode": "metode",

        // Variables (lines 59-61)
        "variabila": "variabilă",
        "variabile": "variabile",

        // Class (lines 63-65)
        "clasa": "clasă",
        "clase": "clase",

        // Common programming terms (lines 67-101)
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
        "initializeaza": "inițializează"
    ]

    /// Apply Romanian corrections to text
    /// - Parameter text: Input text
    /// - Returns: Text with corrected diacritics
    /// Python: _apply_romanian_corrections from lines 167-173
    func apply(to text: String) -> String {
        var result = text

        for (wrong, right) in corrections {
            // Only replace whole words using word boundaries
            // Python: r'\b' + re.escape(wrong) + r'\b' from line 171
            let pattern = "\\b\(NSRegularExpression.escapedPattern(for: wrong))\\b"

            guard let regex = try? NSRegularExpression(
                pattern: pattern,
                options: [.caseInsensitive]
            ) else {
                continue
            }

            let range = NSRange(result.startIndex..., in: result)
            result = regex.stringByReplacingMatches(
                in: result,
                options: [],
                range: range,
                withTemplate: right
            )
        }

        return result
    }

    /// Get all correction mappings
    /// - Returns: Dictionary of corrections
    func getAllCorrections() -> [String: String] {
        corrections
    }
}
