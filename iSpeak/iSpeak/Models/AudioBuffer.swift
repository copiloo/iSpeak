//
//  AudioBuffer.swift
//  iSpeak
//
//  Audio buffer model for captured microphone data
//  Normalized float32 samples at 16kHz mono
//

import Foundation

/// Audio buffer containing recorded audio samples
struct AudioBuffer: Sendable {
    /// Audio samples (normalized float32, range -1.0 to 1.0)
    let samples: [Float]

    /// Sample rate in Hz (always 16000 for Whisper compatibility)
    let sampleRate: Double

    /// Number of channels (always 1 for mono)
    let channels: Int

    /// Duration of audio in seconds
    var duration: TimeInterval {
        Double(samples.count) / sampleRate
    }

    /// Maximum audio level (absolute value)
    var maxLevel: Float {
        samples.map { abs($0) }.max() ?? 0.0
    }

    /// RMS (Root Mean Square) audio level
    var rmsLevel: Float {
        guard !samples.isEmpty else { return 0.0 }
        let sumOfSquares = samples.reduce(0.0) { $0 + ($1 * $1) }
        return sqrt(sumOfSquares / Float(samples.count))
    }

    /// Check if audio is silent (below threshold)
    var isSilent: Bool {
        maxLevel < 0.001  // Python threshold from line 124
    }

    /// Initialize with samples
    /// - Parameters:
    ///   - samples: Normalized float32 samples
    ///   - sampleRate: Sample rate in Hz
    ///   - channels: Number of channels
    init(samples: [Float], sampleRate: Double = 16000.0, channels: Int = 1) {
        self.samples = samples
        self.sampleRate = sampleRate
        self.channels = channels
    }

    /// Create empty buffer
    static var empty: AudioBuffer {
        AudioBuffer(samples: [])
    }
}
