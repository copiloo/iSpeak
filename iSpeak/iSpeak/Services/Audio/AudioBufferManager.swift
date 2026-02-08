//
//  AudioBufferManager.swift
//  iSpeak
//
//  Lock-based circular buffer manager for audio chunks.
//  Thread-safe via NSLock — no Swift concurrency Tasks needed from the audio thread.
//

import Foundation
import AVFoundation

/// Thread-safe circular buffer manager for audio chunks.
/// Uses NSLock instead of actor isolation so the audio tap callback
/// can append buffers synchronously without creating Tasks.
final class AudioBufferManager {
    // MARK: - Properties

    /// Maximum number of chunks to store (~10 seconds at native sample rate)
    private let maxChunks: Int = 300

    /// Stored audio chunks (circular buffer)
    private var chunks: [AVAudioPCMBuffer] = []

    /// Target sample rate (always 16kHz for Whisper)
    private let targetSampleRate: Double = 16000.0

    /// Input format from the audio device (set before recording starts)
    private var inputFormat: AVAudioFormat?

    /// Thread-safety lock
    private let lock = NSLock()

    // MARK: - Public Methods

    /// Set the native input format (called before recording starts, from audio queue)
    func setInputFormat(_ format: AVAudioFormat) {
        lock.withLock {
            inputFormat = format
        }
    }

    /// Clear all buffered audio
    func clear() {
        lock.withLock {
            chunks.removeAll(keepingCapacity: true)
        }
    }

    /// Append a new audio chunk to the buffer (synchronous, lock-based).
    /// Safe to call from any thread including the audio render thread.
    func append(_ buffer: AVAudioPCMBuffer) {
        lock.withLock {
            if chunks.count >= maxChunks {
                chunks.removeFirst()
            }
            chunks.append(buffer)
        }
    }

    /// Consolidate all chunks into a single normalized float array,
    /// resampling from native format to 16kHz mono for Whisper.
    func consolidate() -> iSpeak.AudioBuffer {
        let (capturedChunks, format): ([AVAudioPCMBuffer], AVAudioFormat?) = lock.withLock {
            let result = chunks
            let fmt = inputFormat
            chunks.removeAll(keepingCapacity: true)
            return (result, fmt)
        }

        guard !capturedChunks.isEmpty else {
            print("[Audio] ⚠️  No audio data captured")
            return .empty
        }

        guard let sourceFormat = format else {
            print("[Audio] ⚠️  No input format set")
            return .empty
        }

        // Collect all raw samples from native-format chunks
        let totalNativeSamples = capturedChunks.reduce(0) { $0 + Int($1.frameLength) }
        var nativeSamples: [Float] = []
        nativeSamples.reserveCapacity(totalNativeSamples)

        for chunk in capturedChunks {
            guard let channelData = chunk.floatChannelData?[0] else { continue }
            let frameLength = Int(chunk.frameLength)
            for i in 0..<frameLength {
                nativeSamples.append(channelData[i])
            }
        }

        // Resample to 16kHz mono if needed
        let allSamples: [Float]
        if abs(sourceFormat.sampleRate - targetSampleRate) < 1.0 && sourceFormat.channelCount == 1 {
            // Already at target format
            allSamples = nativeSamples
        } else {
            allSamples = resample(
                nativeSamples,
                from: sourceFormat.sampleRate,
                channels: Int(sourceFormat.channelCount),
                to: targetSampleRate
            )
        }

        let buffer = iSpeak.AudioBuffer(
            samples: allSamples,
            sampleRate: targetSampleRate,
            channels: 1
        )

        if buffer.isSilent {
            print("[Audio] ⚠️  Audio is silent! Max level: \(String(format: "%.6f", buffer.maxLevel))")
        } else {
            print("[Audio] Audio captured: max=\(String(format: "%.3f", buffer.maxLevel)), rms=\(String(format: "%.3f", buffer.rmsLevel)) (\(totalNativeSamples) native → \(allSamples.count) resampled)")
        }

        return buffer
    }

    // MARK: - Private Methods

    /// Simple linear interpolation resampling from native rate to target rate.
    /// Also downmixes multi-channel to mono.
    private func resample(
        _ samples: [Float],
        from sourceRate: Double,
        channels: Int,
        to targetRate: Double
    ) -> [Float] {
        // Downmix to mono first if multi-channel
        let mono: [Float]
        if channels > 1 {
            let frameCount = samples.count / channels
            mono = (0..<frameCount).map { frame in
                var sum: Float = 0
                for ch in 0..<channels {
                    sum += samples[frame * channels + ch]
                }
                return sum / Float(channels)
            }
        } else {
            mono = samples
        }

        // Resample using linear interpolation
        let ratio = sourceRate / targetRate
        let outputCount = Int(Double(mono.count) / ratio)
        guard outputCount > 0 else { return [] }

        var output: [Float] = []
        output.reserveCapacity(outputCount)

        for i in 0..<outputCount {
            let srcIndex = Double(i) * ratio
            let idx = Int(srcIndex)
            let frac = Float(srcIndex - Double(idx))

            if idx + 1 < mono.count {
                output.append(mono[idx] * (1.0 - frac) + mono[idx + 1] * frac)
            } else if idx < mono.count {
                output.append(mono[idx])
            }
        }

        return output
    }
}
