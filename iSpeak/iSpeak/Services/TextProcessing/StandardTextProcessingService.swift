//
//  StandardTextProcessingService.swift
//  iSpeak
//
//  Main text processing service with 4-step pipeline
//  Implements Python's TextProcessor from text_processor.py
//

import Foundation

/// Standard text processing service
/// Matches Python's TextProcessor behavior with 4-step pipeline
final class StandardTextProcessingService: TextProcessingService {
    // MARK: - Properties

    /// Vocabulary manager (thread-safe)
    private let vocabularyManager = VocabularyManager()

    /// Romanian corrector
    private let romanianCorrector = RomanianCorrector()

    /// Code formatter
    private let codeFormatter = CodeFormatter()

    // MARK: - Initialization

    init() {
        print("[TextProcessing] Standard text processing service initialized")
    }

    // MARK: - TextProcessingService Protocol

    /// Process transcribed text with 4-step pipeline
    /// Python: process from lines 106-127
    func process(_ text: String, context: AppContext) async -> String {
        guard !text.isEmpty else {
            return ""
        }

        var processed = text

        // Step 1: Apply custom vocabulary (case-insensitive)
        // Python: line 115
        processed = await vocabularyManager.apply(to: processed)

        // Step 2: If in code editor, apply code formatting
        // Python: lines 117-119
        if context.isCodeContext {
            processed = codeFormatter.apply(to: processed)
            print("[TextProcessing] Applied code formatting (context: \(context.appName))")
        }

        // Step 3: Romanian-specific corrections
        // Python: line 122
        processed = romanianCorrector.apply(to: processed)

        // Step 4: Clean up extra spaces
        // Python: line 125
        processed = cleanupWhitespace(processed)

        return processed
    }

    /// Load vocabulary from default Resources location
    func loadVocabulary() async throws {
        // Try with subdirectory first (folder reference), then without (group)
        let url = Bundle.main.url(forResource: "vocabulary", withExtension: "json", subdirectory: "Dictionaries")
            ?? Bundle.main.url(forResource: "vocabulary", withExtension: "json")
        guard let url else {
            throw TextProcessingError.vocabularyLoadFailed("vocabulary.json not found in bundle")
        }
        try await loadVocabulary(from: url)
    }

    /// Load vocabulary from file
    /// Python: _load_vocabulary from lines 193-202
    func loadVocabulary(from url: URL) async throws {
        try await vocabularyManager.load(from: url)
    }

    /// Add custom word to vocabulary
    /// Python: add_custom_word from lines 188-191
    func addCustomWord(spoken: String, written: String) async throws {
        await vocabularyManager.addWord(spoken: spoken, written: written)
        try await vocabularyManager.save()
    }

    /// Save current vocabulary to file
    /// Python: _save_vocabulary from lines 204-211
    func saveVocabulary() async throws {
        try await vocabularyManager.save()
    }

    // MARK: - Private Methods

    /// Clean up whitespace and fix punctuation spacing
    /// Python: _cleanup_whitespace from lines 175-186
    private func cleanupWhitespace(_ text: String) -> String {
        var result = text

        // Multiple spaces → single space
        // Python: line 178
        result = result.replacingOccurrences(
            of: #"\s+"#,
            with: " ",
            options: .regularExpression
        )

        // Remove space before punctuation
        // Python: line 181
        result = result.replacingOccurrences(
            of: #"\s+([,.;:!?])"#,
            with: "$1",
            options: .regularExpression
        )

        // Add space after punctuation (if missing)
        // Python: line 184
        result = result.replacingOccurrences(
            of: #"([,.;:!?])([A-Za-z])"#,
            with: "$1 $2",
            options: .regularExpression
        )

        return result.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    // MARK: - Additional Utilities

    /// Get all Romanian corrections
    /// - Returns: Dictionary of corrections
    func getRomanianCorrections() -> [String: String] {
        romanianCorrector.getAllCorrections()
    }

    /// Get all code patterns
    /// - Returns: Dictionary of patterns
    func getCodePatterns() -> [String: String] {
        codeFormatter.getAllPatterns()
    }

    /// Get current vocabulary count
    /// - Returns: Number of custom vocabulary entries
    func getVocabularyCount() async -> Int {
        await vocabularyManager.getCustomCount()
    }

    /// Get all vocabulary entries
    /// - Returns: Dictionary of all entries
    func getAllVocabulary() async -> [String: String] {
        await vocabularyManager.getAllVocabulary()
    }
}
