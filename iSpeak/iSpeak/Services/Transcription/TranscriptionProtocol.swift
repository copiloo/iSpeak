//
//  TranscriptionProtocol.swift
//  iSpeak
//
//  Protocol for transcription service
//  Enables testing with mock implementations
//

import Foundation

/// Model size options (Python: lines 30-39)
enum iSpeakModelSize: String, CaseIterable {
    case tiny = "tiny"
    case base = "base"
    case small = "small"           // Recommended for Romanian (Python line 50)
    case medium = "medium"
    case large = "large-v3"
    case largeTurbo = "large-v3-turbo"  // Best speed/accuracy tradeoff

    var displayName: String {
        switch self {
        case .tiny: return "Tiny (fastest, least accurate)"
        case .base: return "Base"
        case .small: return "Small (recommended)"
        case .medium: return "Medium"
        case .large: return "Large"
        case .largeTurbo: return "Large Turbo (best quality)"
        }
    }

    var code: String {
        rawValue
    }
}

/// Protocol for transcription service
protocol TranscriptionService {
    /// Current language setting
    var currentLanguage: String { get set }

    /// Current model size
    var currentModel: iSpeakModelSize { get }

    /// Transcribe audio to text
    /// - Parameters:
    ///   - audio: Audio samples (float32, normalized -1 to 1)
    ///   - language: Language code ('en', 'ro', etc.) or nil for auto-detect
    /// - Returns: Transcription result with text and confidence
    /// Python: transcribe from lines 117-142
    func transcribe(audio: [Float], language: String?) async throws -> TranscriptionResult

    /// Switch to a different model size
    /// - Parameter size: New model size
    /// Python: switch_model from lines 240-247
    func switchModel(to size: iSpeakModelSize) async throws

    /// Set the current language
    /// - Parameter langCode: Language code ('en', 'ro', etc.)
    /// Python: set_language from lines 235-238
    func setLanguage(_ langCode: String)
}

/// Errors that can occur during transcription
enum TranscriptionError: Error, LocalizedError {
    case modelNotLoaded
    case modelLoadFailed(String)
    case transcriptionFailed(String)
    case invalidAudioData

    var errorDescription: String? {
        switch self {
        case .modelNotLoaded:
            return "Whisper model not loaded"
        case .modelLoadFailed(let message):
            return "Failed to load model: \(message)"
        case .transcriptionFailed(let message):
            return "Transcription failed: \(message)"
        case .invalidAudioData:
            return "Invalid audio data provided"
        }
    }
}
