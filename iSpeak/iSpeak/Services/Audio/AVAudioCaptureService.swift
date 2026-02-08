//
//  AVAudioCaptureService.swift
//  iSpeak
//
//  Audio capture service using AVFoundation
//  Implements Python's AudioCapture from audio_capture.py
//

import Foundation
import AVFoundation

/// Audio capture service using AVAudioEngine
/// Matches Python's AudioCapture class behavior
/// NOTE: Must NOT be @Observable — audio tap callback accesses properties
/// from a non-main thread, and @Observable is not thread-safe.
final class AVAudioCaptureService: AudioCaptureService {
    // MARK: - Properties

    /// Audio engine for recording
    private var audioEngine: AVAudioEngine?

    /// Input node for microphone
    private var inputNode: AVAudioInputNode?

    /// Buffer manager (thread-safe circular buffer)
    private let bufferManager = AudioBufferManager()

    /// Device monitor
    private let deviceMonitor = AudioDeviceMonitor()

    /// Recording state
    private(set) var isRecording: Bool = false

    // Audio configuration (Python: lines 10-16)
    private let sampleRate: Double = 16000.0  // Whisper expects 16kHz
    private let channels: UInt32 = 1           // Mono audio
    private let chunkSize: AVAudioFrameCount = 1024  // Process in small chunks

    // MARK: - Initialization

    init() {
        // Monitor device changes
        deviceMonitor.startMonitoring { [weak self] in
            print("[Audio] Device changed, will reinitialize on next recording")
        }
    }

    // MARK: - AudioCaptureService Protocol

    /// Start capturing audio from microphone (synchronous)
    /// Must complete before stopRecording() is called.
    /// Python: start_recording from lines 51-96
    func startRecording() throws {
        isRecording = true

        // Clear buffer (Python: line 54)
        bufferManager.clear()

        // Reinitialize audio engine to detect device changes
        // Python: _init_pyaudio from line 57
        try reinitializeEngine()

        // Get device info
        let (_, isBluetooth) = deviceMonitor.getDefaultInputDevice()

        // Configure audio session
        try configureAudioSession()

        // Start the engine
        guard let engine = audioEngine, let input = inputNode else {
            throw AudioCaptureError.engineFailedToStart
        }

        // Install tap using the input node's native format.
        // AVAudioEngine requires the tap format to match the hardware;
        // passing a custom 16kHz format causes "format mismatch" crash.
        // We resample to 16kHz during consolidation instead.
        let nativeFormat = input.outputFormat(forBus: 0)
        print("[Audio] Native format: \(nativeFormat.sampleRate) Hz, \(nativeFormat.channelCount) ch")
        bufferManager.setInputFormat(nativeFormat)

        input.installTap(onBus: 0, bufferSize: chunkSize, format: nativeFormat) { [weak self] buffer, _ in
            guard let self, self.isRecording else { return }

            // Append buffer directly — lock-based, no Task creation needed.
            // Creating Tasks from the audio render thread corrupts the
            // Swift concurrency runtime and causes MainActor.assumeIsolated to segfault.
            self.bufferManager.append(buffer)
        }

        // Start the audio engine
        do {
            try engine.start()
            print("[Audio] 🎤 Recording started (bluetooth: \(isBluetooth))")
        } catch {
            throw AudioCaptureError.engineFailedToStart
        }

        // Note: Bluetooth warm-up delay handled by caller if needed
    }

    /// Stop recording and return captured audio buffer
    /// Python: stop_recording from lines 104-133
    func stopRecording() -> iSpeak.AudioBuffer {
        isRecording = false

        // Stop the tap and engine
        if let input = inputNode {
            input.removeTap(onBus: 0)
        }

        audioEngine?.stop()

        // Consolidate all chunks into single buffer
        let buffer = bufferManager.consolidate()

        print("[Audio] ⏸️ Recording stopped (\(String(format: "%.1f", buffer.duration))s captured)")

        return buffer
    }

    /// Clean up audio resources
    /// Python: cleanup from lines 135-146
    func cleanup() async {
        if isRecording {
            _ = stopRecording()
        }

        inputNode?.removeTap(onBus: 0)
        audioEngine?.stop()
        audioEngine = nil
        inputNode = nil

        deviceMonitor.cleanup()
        print("[Audio] ✅ Audio resources cleaned up")
    }

    // MARK: - Private Methods

    /// Reinitialize audio engine
    /// Handles device changes (e.g., AirPods connected)
    /// Python: _init_pyaudio from lines 23-30
    private func reinitializeEngine() throws {
        // Stop existing engine
        audioEngine?.stop()
        inputNode?.removeTap(onBus: 0)

        // Create new engine
        audioEngine = AVAudioEngine()

        guard let engine = audioEngine else {
            throw AudioCaptureError.engineFailedToStart
        }

        // Get input node
        inputNode = engine.inputNode

        guard inputNode != nil else {
            throw AudioCaptureError.deviceNotAvailable
        }
    }

    /// Configure audio session for recording
    private func configureAudioSession() throws {
        #if os(macOS)
        // macOS doesn't use AVAudioSession like iOS
        // Audio configuration is handled by the engine
        #else
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .measurement, options: [])
        try session.setActive(true, options: .notifyOthersOnDeactivation)
        #endif
    }

    // MARK: - Deinitialization

    deinit {
        // Cleanup is async, so we can't call it directly from deinit
        // Rely on explicit cleanup() call before deallocation
        inputNode?.removeTap(onBus: 0)
        audioEngine?.stop()
        deviceMonitor.cleanup()
    }
}
