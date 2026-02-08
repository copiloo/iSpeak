//
//  WhisperModelManager.swift
//  iSpeak
//
//  Manager for Whisper model downloading and caching
//  Matches Python's model management from transcription.py lines 67-115
//

import Foundation
import WhisperKit

/// Thread-safe manager for Whisper models
actor WhisperModelManager {
    // MARK: - Properties

    /// Directory for cached models
    /// Python: models_dir from line 54
    private let modelsDirectory: URL

    /// Currently loaded WhisperKit instance
    private var whisperKit: WhisperKit?

    /// Currently loaded model size
    private(set) var currentModelSize: iSpeakModelSize?

    // MARK: - Initialization

    init() {
        // Create models directory in Application Support
        // Python: os.makedirs(models_dir, exist_ok=True) from line 60
        let appSupport = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        )[0]

        self.modelsDirectory = appSupport
            .appendingPathComponent("iSpeak")
            .appendingPathComponent("models")

        // Ensure directory exists
        try? FileManager.default.createDirectory(
            at: modelsDirectory,
            withIntermediateDirectories: true
        )

        print("[Transcription] Models directory: \(modelsDirectory.path)")
    }

    // MARK: - Public Methods

    /// Get the models directory URL
    func getModelsDirectory() -> URL {
        modelsDirectory
    }

    /// Load a Whisper model
    /// - Parameter size: Model size to load
    /// - Returns: Loaded WhisperKit instance
    /// Python: _load_model from lines 67-115
    func loadModel(_ size: iSpeakModelSize) async throws -> WhisperKit {
        let startTime = Date()

        print("[Transcription] Loading WhisperKit model: \(size.rawValue)...")

        do {
            // WhisperKit automatically downloads from HuggingFace if not cached
            // Models are stored in modelsDirectory
            let config = WhisperKitConfig(
                model: size.rawValue,
                downloadBase: modelsDirectory,
                verbose: false,
                logLevel: .none
            )

            let kit = try await WhisperKit(config)

            whisperKit = kit
            currentModelSize = size

            let loadTime = Date().timeIntervalSince(startTime)
            print("[Transcription] Model loaded: \(size.rawValue) (\(String(format: "%.2f", loadTime))s)")

            return kit
        } catch {
            print("[Transcription] Model load failed: \(error.localizedDescription)")
            throw TranscriptionError.modelLoadFailed(error.localizedDescription)
        }
    }

    /// Get currently loaded WhisperKit instance
    /// - Returns: WhisperKit instance or nil if not loaded
    func getCurrentWhisperKit() -> WhisperKit? {
        whisperKit
    }

    /// Switch to a different model
    /// - Parameter newSize: New model size
    /// Python: switch_model from lines 240-247
    func switchModel(to newSize: iSpeakModelSize) async throws -> WhisperKit {
        // Only reload if different from current
        if newSize == currentModelSize, let existing = whisperKit {
            print("[Transcription] Model \(newSize.rawValue) already loaded")
            return existing
        }

        print("[Transcription] Switching model from \(currentModelSize?.rawValue ?? "none") to \(newSize.rawValue)...")

        // Cleanup old model
        whisperKit = nil
        currentModelSize = nil

        // Load new model
        return try await loadModel(newSize)
    }

    /// Check if a model is cached locally
    /// - Parameter size: Model size to check
    /// - Returns: True if model exists in cache
    func isModelCached(_ size: iSpeakModelSize) -> Bool {
        // WhisperKit stores models at:
        // modelsDirectory/models/argmaxinc/whisperkit-coreml/openai_whisper-{size}/
        let modelPath = modelsDirectory
            .appendingPathComponent("models")
            .appendingPathComponent("argmaxinc")
            .appendingPathComponent("whisperkit-coreml")
            .appendingPathComponent("openai_whisper-\(size.rawValue)")
        return FileManager.default.fileExists(atPath: modelPath.path)
    }

    /// Get size of cached models directory
    /// - Returns: Size in bytes
    func getCacheSize() -> Int64 {
        guard let enumerator = FileManager.default.enumerator(
            at: modelsDirectory,
            includingPropertiesForKeys: [.fileSizeKey]
        ) else {
            return 0
        }

        var totalSize: Int64 = 0
        for case let fileURL as URL in enumerator {
            if let resourceValues = try? fileURL.resourceValues(forKeys: [.fileSizeKey]),
               let fileSize = resourceValues.fileSize {
                totalSize += Int64(fileSize)
            }
        }

        return totalSize
    }
}
