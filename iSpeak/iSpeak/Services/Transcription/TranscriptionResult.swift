//
//  TranscriptionResult.swift
//  iSpeak
//
//  Model for transcription results
//  Matches Python's return dict from transcription.py lines 125-142
//

import Foundation

/// Result of audio transcription
struct TranscriptionResult {
    /// Transcribed text
    let text: String

    /// Detected or specified language code ('en', 'ro', etc.)
    let language: String

    /// Confidence score (0.0 to 1.0)
    /// Calculated from avg_logprob: min(1.0, max(0.0, 1.0 + avgLogProb))
    /// Python: lines 230-233
    let confidence: Double

    /// Time taken to transcribe (seconds)
    let duration: TimeInterval

    /// Whether confidence is below warning threshold
    var isLowConfidence: Bool {
        confidence < 0.5  // Python warning threshold
    }

    /// Initialize transcription result
    /// - Parameters:
    ///   - text: Transcribed text
    ///   - language: Language code
    ///   - confidence: Confidence score (0-1)
    ///   - duration: Transcription duration
    init(text: String, language: String, confidence: Double, duration: TimeInterval) {
        self.text = text.trimmingCharacters(in: .whitespacesAndNewlines)
        self.language = language
        self.confidence = confidence
        self.duration = duration
    }

    /// Create empty result for errors
    static var empty: TranscriptionResult {
        TranscriptionResult(text: "", language: "", confidence: 0.0, duration: 0.0)
    }
}
