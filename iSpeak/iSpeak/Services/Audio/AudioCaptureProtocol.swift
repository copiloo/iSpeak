//
//  AudioCaptureProtocol.swift
//  iSpeak
//
//  Protocol for audio capture service
//  Enables testing with mock implementations
//

import Foundation

/// Protocol for audio capture service
protocol AudioCaptureService {
    /// Whether currently recording
    var isRecording: Bool { get }

    /// Start capturing audio from microphone
    /// - Throws: AudioCaptureError if unable to start recording
    func startRecording() throws

    /// Stop recording and return captured audio buffer
    /// - Returns: AudioBuffer with captured samples
    func stopRecording() -> AudioBuffer

    /// Clean up audio resources
    func cleanup() async
}

/// Errors that can occur during audio capture
enum AudioCaptureError: Error, LocalizedError {
    case permissionDenied
    case deviceNotAvailable
    case engineFailedToStart
    case configurationFailed(String)

    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "Microphone permission denied. Please grant access in System Settings."
        case .deviceNotAvailable:
            return "No audio input device available."
        case .engineFailedToStart:
            return "Failed to start audio engine."
        case .configurationFailed(let message):
            return "Audio configuration failed: \(message)"
        }
    }
}
