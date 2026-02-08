//
//  AudioDeviceMonitor.swift
//  iSpeak
//
//  Monitor for audio device changes (Bluetooth, USB devices)
//  Matches Python's device detection from audio_capture.py lines 32-49
//

import Foundation
import AVFoundation
import CoreAudio

/// Monitor for audio input device changes
class AudioDeviceMonitor {
    // MARK: - Properties

    /// Callback when device changes detected
    private var onDeviceChanged: (() -> Void)?

    /// Current default input device
    private var currentDeviceID: AudioDeviceID?

    // MARK: - Initialization

    init() {
        setupNotifications()
    }

    // MARK: - Public Methods

    /// Start monitoring for device changes
    /// - Parameter callback: Called when device changes
    func startMonitoring(onDeviceChanged: @escaping () -> Void) {
        self.onDeviceChanged = onDeviceChanged
    }

    /// Stop monitoring
    func stopMonitoring() {
        self.onDeviceChanged = nil
    }

    /// Get information about the current default input device
    /// - Returns: Tuple of (device name, is Bluetooth)
    /// Python: _get_default_input_device from lines 32-49
    func getDefaultInputDevice() -> (name: String, isBluetooth: Bool) {
        guard let device = AVCaptureDevice.default(for: .audio) else {
            print("[Audio] Could not get default input device")
            return ("Unknown", false)
        }

        let deviceName = device.localizedName
        print("[Audio] Using input device: \(deviceName)")

        // Check if it's a Bluetooth device (needs warm-up time)
        // Python: checks for 'airpods', 'bluetooth', 'wireless', 'bt' in name
        let bluetoothKeywords = ["airpods", "bluetooth", "wireless", "bt"]
        let isBluetooth = bluetoothKeywords.contains { keyword in
            deviceName.lowercased().contains(keyword)
        }

        if isBluetooth {
            print("[Audio] Bluetooth device detected, may need warm-up time")
        }

        return (deviceName, isBluetooth)
    }

    /// Clean up resources
    func cleanup() {
        NotificationCenter.default.removeObserver(self)
    }

    // MARK: - Private Methods

    private func setupNotifications() {
        // On macOS, we use CoreAudio property listeners for device changes
        // For now, we'll rely on the audio engine's automatic device switching
        // More sophisticated monitoring can be added later if needed
        print("[Audio] Device monitoring initialized (macOS CoreAudio)")
    }

    @objc private func handleRouteChange() {
        print("[Audio] Audio route changed (device connected/disconnected)")
        onDeviceChanged?()
    }

    deinit {
        cleanup()
    }
}
