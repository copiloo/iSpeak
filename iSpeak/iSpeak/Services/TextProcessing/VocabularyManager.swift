//
//  VocabularyManager.swift
//  iSpeak
//
//  Manager for custom vocabulary (user-defined word replacements)
//  Matches Python's vocabulary management from text_processor.py
//

import Foundation

/// Thread-safe vocabulary manager
actor VocabularyManager {
    // MARK: - Properties

    /// Custom vocabulary dictionary (spoken → written)
    private var vocabulary: [String: String] = [:]

    /// Built-in vocabulary (always available)
    /// Python: lines 13-24
    private let builtInVocabulary: [String: String] = [
        "git hub": "GitHub",
        "vis code": "VS Code",
        "visual studio code": "VS Code",
        "java script": "JavaScript",
        "type script": "TypeScript",
        "python": "Python",
        "node j s": "Node.js",
        "react native": "React Native",
        "mongo d b": "MongoDB",
        "postgre s q l": "PostgreSQL",
        "my s q l": "MySQL"
    ]

    /// URL for saving/loading custom vocabulary
    private var vocabularyURL: URL?

    // MARK: - Initialization

    init() {
        // Start with built-in vocabulary
        vocabulary = builtInVocabulary
        print("[TextProcessing] VocabularyManager initialized with \(builtInVocabulary.count) built-in entries")
    }

    // MARK: - Public Methods

    /// Load vocabulary from file
    /// - Parameter url: URL to vocabulary JSON file
    /// - Throws: TextProcessingError if loading fails
    /// Python: _load_vocabulary from lines 193-202
    func load(from url: URL) throws {
        self.vocabularyURL = url

        guard FileManager.default.fileExists(atPath: url.path) else {
            print("[TextProcessing] No custom vocabulary file found at \(url.path)")
            return
        }

        do {
            let data = try Data(contentsOf: url)
            let custom = try JSONDecoder().decode([String: String].self, from: data)

            // Merge with built-in vocabulary (built-in takes precedence)
            vocabulary = builtInVocabulary.merging(custom) { builtin, _ in builtin }

            print("[TextProcessing] Loaded \(custom.count) custom vocabulary entries")
        } catch {
            throw TextProcessingError.vocabularyLoadFailed(error.localizedDescription)
        }
    }

    /// Save vocabulary to file
    /// - Throws: TextProcessingError if saving fails
    /// Python: _save_vocabulary from lines 204-211
    func save() throws {
        guard let url = vocabularyURL else {
            throw TextProcessingError.vocabularySaveFailed("No vocabulary URL set")
        }

        do {
            // Create directory if needed
            let directory = url.deletingLastPathComponent()
            try FileManager.default.createDirectory(
                at: directory,
                withIntermediateDirectories: true
            )

            // Save only custom vocabulary (exclude built-in)
            let customVocabulary = vocabulary.filter { key, _ in
                !builtInVocabulary.keys.contains(key)
            }

            let data = try JSONEncoder().encode(customVocabulary)
            try data.write(to: url)

            print("[TextProcessing] Saved \(customVocabulary.count) custom vocabulary entries")
        } catch {
            throw TextProcessingError.vocabularySaveFailed(error.localizedDescription)
        }
    }

    /// Apply vocabulary replacements to text
    /// - Parameter text: Input text
    /// - Returns: Text with vocabulary applied
    /// Python: _apply_vocabulary from lines 129-135
    func apply(to text: String) -> String {
        var result = text

        for (spoken, written) in vocabulary {
            // Case-insensitive replacement
            // Python: pattern = re.compile(re.escape(wrong), re.IGNORECASE)
            guard let regex = try? NSRegularExpression(
                pattern: NSRegularExpression.escapedPattern(for: spoken),
                options: [.caseInsensitive]
            ) else {
                continue
            }

            let range = NSRange(result.startIndex..., in: result)
            result = regex.stringByReplacingMatches(
                in: result,
                options: [],
                range: range,
                withTemplate: written
            )
        }

        return result
    }

    /// Add custom word to vocabulary
    /// - Parameters:
    ///   - spoken: Spoken form
    ///   - written: Written form
    /// Python: add_custom_word from lines 188-191
    func addWord(spoken: String, written: String) {
        vocabulary[spoken.lowercased()] = written
        print("[TextProcessing] Added vocabulary: '\(spoken)' → '\(written)'")
    }

    /// Remove custom word from vocabulary
    /// - Parameter spoken: Spoken form to remove
    func removeWord(spoken: String) {
        vocabulary.removeValue(forKey: spoken.lowercased())
    }

    /// Get all vocabulary entries
    /// - Returns: Dictionary of all entries
    func getAllVocabulary() -> [String: String] {
        vocabulary
    }

    /// Get count of custom entries (excluding built-in)
    /// - Returns: Number of custom entries
    func getCustomCount() -> Int {
        vocabulary.count - builtInVocabulary.count
    }
}
