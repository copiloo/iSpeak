//
//  WhisperKitTranscriptionService.swift
//  iSpeak
//
//  WhisperKit-based transcription service
//  Implements Python's TranscriptionEngine from transcription.py
//

import Foundation
import WhisperKit

/// WhisperKit transcription service
/// Matches Python's TranscriptionEngine behavior with simplified single backend
final class WhisperKitTranscriptionService: TranscriptionService {
    // MARK: - Properties

    /// Model manager (thread-safe)
    private let modelManager = WhisperModelManager()

    /// Current language setting
    /// Python: self.current_language from line 65
    var currentLanguage: String = "en"  // Default English

    /// Current model size
    private(set) var currentModel: iSpeakModelSize = .small  // Recommended (Python line 50)

    // MARK: - Initialization

    init() {
        print("[Transcription] WhisperKit transcription service initialized")
    }

    // MARK: - TranscriptionService Protocol

    /// Transcribe audio to text
    /// - Parameters:
    ///   - audio: Normalized float32 audio samples (16kHz mono)
    ///   - language: Language code ('en', 'ro', etc.) or nil for auto-detect
    /// - Returns: Transcription result
    /// Python: transcribe from lines 117-142
    func transcribe(audio: [Float], language: String?) async throws -> iSpeak.TranscriptionResult {
        let startTime = Date()

        let usedLanguage = language ?? currentLanguage
        print("[Transcription] Transcribing \(audio.count) samples in language: \(usedLanguage)")

        // Get WhisperKit instance — model must be pre-loaded via downloadAndLoadModel
        guard let kit = await modelManager.getCurrentWhisperKit() else {
            throw TranscriptionError.modelNotLoaded
        }

        do {
            // Prepare transcription options (optimized like Python)
            // Python: lines 182-192 (faster-whisper parameters)
            let options = DecodingOptions(
                language: usedLanguage,
                temperature: 0.0,                     // Fixed temperature (Python line 154)
                temperatureFallbackCount: 0,          // No retries (Python line 154)
                usePrefillPrompt: false,              // Python: condition_on_previous_text=False
                usePrefillCache: false,
                skipSpecialTokens: true,
                withoutTimestamps: true               // Faster (Python: word_timestamps=False)
            )

            // Transcribe
            let result = try await kit.transcribe(
                audioArray: audio,
                decodeOptions: options
            )

            // Extract text
            let text = result.first?.text ?? ""

            // Calculate confidence from segments
            // Python: _calculate_confidence_fw from lines 225-233
            // WhisperKit may not expose avg_logprob directly in current version
            // Use a default confidence based on result presence
            let confidence: Double = (!result.isEmpty && !text.isEmpty) ? 0.7 : 0.0

            let duration = Date().timeIntervalSince(startTime)

            // Log results like Python (lines 124-131 in audio_capture.py)
            if confidence < 0.5 {
                print("[Transcription] ⚠️  Low confidence: \(String(format: "%.2f", confidence))")
            }

            print("[Transcription] ✅ Transcribed in \(String(format: "%.2f", duration))s: '\(text.prefix(50))...'")

            return iSpeak.TranscriptionResult(
                text: text,
                language: result.first?.language ?? usedLanguage,
                confidence: confidence,
                duration: duration
            )
        } catch {
            print("[Transcription] ❌ Transcription failed: \(error.localizedDescription)")
            throw TranscriptionError.transcriptionFailed(error.localizedDescription)
        }
    }

    /// Switch to a different model size
    /// - Parameter size: New model size
    /// Python: switch_model from lines 240-247
    func switchModel(to size: iSpeakModelSize) async throws {
        guard size != currentModel else {
            print("[Transcription] Already using model: \(size.rawValue)")
            return
        }

        print("[Transcription] Switching from \(currentModel.rawValue) to \(size.rawValue)...")

        _ = try await modelManager.switchModel(to: size)
        currentModel = size

        print("[Transcription] Model switched to: \(size.rawValue)")
    }

    /// Set the current language
    /// - Parameter langCode: Language code ('en', 'ro', etc.)
    /// Python: set_language from lines 235-238
    func setLanguage(_ langCode: String) {
        currentLanguage = langCode
        print("[Transcription] Language set to: \(langCode)")
    }

    // MARK: - Additional Utilities

    /// Get the models directory for downloading
    func getModelsDirectory() async -> URL {
        await modelManager.getModelsDirectory()
    }

    /// Check if a model is already cached
    /// - Parameter size: Model size
    /// - Returns: True if cached locally
    func isModelCached(_ size: iSpeakModelSize) async -> Bool {
        await modelManager.isModelCached(size)
    }

    /// Get total size of cached models
    /// - Returns: Size in bytes
    func getCacheSize() async -> Int64 {
        await modelManager.getCacheSize()
    }

    /// Preload a model in the background
    /// - Parameter size: Model size to preload
    func preloadModel(_ size: iSpeakModelSize) async throws {
        _ = try await modelManager.loadModel(size)
        currentModel = size
    }

    /// Warm up the loaded model by running a short silent inference.
    /// CoreML compiles/optimizes the neural engine graph on first run,
    /// which is slow and often produces empty results. This ensures the
    /// first real dictation works immediately.
    func warmUpModel() async {
        guard let kit = await modelManager.getCurrentWhisperKit() else { return }

        let silentAudio = [Float](repeating: 0.0, count: 16000)  // 1s of silence at 16kHz
        let options = DecodingOptions(
            language: "en",
            temperature: 0.0,
            temperatureFallbackCount: 0,
            usePrefillPrompt: false,
            usePrefillCache: false,
            skipSpecialTokens: true,
            withoutTimestamps: true
        )

        print("[Transcription] Warming up model...")
        let startTime = Date()
        _ = try? await kit.transcribe(audioArray: silentAudio, decodeOptions: options)
        let warmUpTime = Date().timeIntervalSince(startTime)
        print("[Transcription] Model warm-up complete (\(String(format: "%.2f", warmUpTime))s)")
    }
}
