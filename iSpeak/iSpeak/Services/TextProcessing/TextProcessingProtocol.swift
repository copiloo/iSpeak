//
//  TextProcessingProtocol.swift
//  iSpeak
//
//  Protocol for text processing service
//  Enables testing with mock implementations
//

import Foundation

/// Protocol for text processing service
protocol TextProcessingService {
    /// Process transcribed text with 4-step pipeline
    /// - Parameters:
    ///   - text: Raw transcribed text
    ///   - context: Application context for code-aware formatting
    /// - Returns: Processed text
    /// Python: process from lines 106-127
    func process(_ text: String, context: AppContext) async -> String

    /// Load vocabulary from default bundle location
    /// - Throws: Error if loading fails
    func loadVocabulary() async throws

    /// Load vocabulary from file
    /// - Parameter url: URL to vocabulary JSON file
    /// - Throws: Error if loading fails
    /// Python: _load_vocabulary from lines 193-202
    func loadVocabulary(from url: URL) async throws

    /// Add custom word to vocabulary
    /// - Parameters:
    ///   - spoken: Spoken form
    ///   - written: Written form
    /// Python: add_custom_word from lines 188-191
    func addCustomWord(spoken: String, written: String) async throws

    /// Save current vocabulary to file
    /// Python: _save_vocabulary from lines 204-211
    func saveVocabulary() async throws
}

/// Errors that can occur during text processing
enum TextProcessingError: Error, LocalizedError {
    case vocabularyLoadFailed(String)
    case vocabularySaveFailed(String)
    case invalidVocabularyFormat

    var errorDescription: String? {
        switch self {
        case .vocabularyLoadFailed(let message):
            return "Failed to load vocabulary: \(message)"
        case .vocabularySaveFailed(let message):
            return "Failed to save vocabulary: \(message)"
        case .invalidVocabularyFormat:
            return "Vocabulary file has invalid format"
        }
    }
}
