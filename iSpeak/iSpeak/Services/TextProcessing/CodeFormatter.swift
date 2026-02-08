//
//  CodeFormatter.swift
//  iSpeak
//
//  Code-aware formatting for voice commands
//  Matches Python's code_patterns from text_processor.py lines 26-47
//

import Foundation

/// Code formatter for voice commands
struct CodeFormatter {
    /// Code pattern mappings (voice command → symbol)
    /// Python: self.code_patterns dictionary
    private let patterns: [String: String] = [
        // Newlines and indentation
        "new line": "\n",
        "tab": "\t",

        // Braces and brackets
        "open brace": " {",
        "close brace": "}",
        "open bracket": "[",
        "close bracket": "]",
        "open paren": "(",
        "close paren": ")",

        // Punctuation
        "semicolon": ";",
        "colon": ":",
        "comma": ",",
        "period": ".",
        "dot": ".",

        // Operators
        "equals": " = ",
        "plus": " + ",
        "minus": " - ",
        "plus plus": "++",
        "minus minus": "--",
        "arrow": " => "
    ]

    /// Apply code formatting to text
    /// - Parameter text: Input text
    /// - Returns: Text with code patterns applied
    /// Python: _apply_code_formatting from lines 150-165
    func apply(to text: String) -> String {
        var result = text

        // Replace code patterns with word boundaries
        // Python: lines 153-156
        for (spoken, written) in patterns {
            let pattern = "\\b\(NSRegularExpression.escapedPattern(for: spoken))\\b"

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
                withTemplate: NSRegularExpression.escapedTemplate(for: written)
            )
        }

        // Handle common code phrases
        // Python: lines 158-163
        result = applyCodePhrases(to: result)

        return result
    }

    /// Apply common code phrase transformations
    /// Python: lines 159-163
    private func applyCodePhrases(to text: String) -> String {
        var result = text

        // "if x equals y" → "if x == y"
        if let regex = try? NSRegularExpression(
            pattern: "\\bif\\s+(\\w+)\\s+equals\\s+(\\w+)\\b",
            options: [.caseInsensitive]
        ) {
            let range = NSRange(result.startIndex..., in: result)
            result = regex.stringByReplacingMatches(
                in: result,
                options: [],
                range: range,
                withTemplate: "if $1 == $2"
            )
        }

        // "for x in range" → "for x in range"
        if let regex = try? NSRegularExpression(
            pattern: "\\bfor\\s+(\\w+)\\s+in\\s+range\\b",
            options: [.caseInsensitive]
        ) {
            let range = NSRange(result.startIndex..., in: result)
            result = regex.stringByReplacingMatches(
                in: result,
                options: [],
                range: range,
                withTemplate: "for $1 in range"
            )
        }

        // "def function_name" → "def function_name"
        if let regex = try? NSRegularExpression(
            pattern: "\\bdef\\s+(\\w+)",
            options: [.caseInsensitive]
        ) {
            let range = NSRange(result.startIndex..., in: result)
            result = regex.stringByReplacingMatches(
                in: result,
                options: [],
                range: range,
                withTemplate: "def $1"
            )
        }

        return result
    }

    /// Get all code patterns
    /// - Returns: Dictionary of patterns
    func getAllPatterns() -> [String: String] {
        patterns
    }
}
