//
//  HotkeyProtocol.swift
//  iSpeak
//
//  Protocol for hotkey service
//  Enables testing with mock implementations
//

import Foundation

/// Protocol for global hotkey service
protocol HotkeyService {
    /// Whether the service is currently listening for hotkeys
    var isListening: Bool { get }

    /// Current hotkey configuration
    var configuration: HotkeyConfiguration { get }

    /// Start listening for global hotkey events
    /// - Parameters:
    ///   - onPress: Called when hotkey is pressed
    ///   - onRelease: Called when hotkey is released
    /// - Throws: HotkeyError if unable to start listening
    /// Python: start_listening from lines 25-33
    func startListening(
        onPress: @escaping () -> Void,
        onRelease: @escaping () -> Void
    ) async throws

    /// Stop listening for hotkey events
    /// Python: stop_listening from lines 35-39
    func stopListening()

    /// Change the hotkey configuration
    /// - Parameter config: New hotkey configuration
    /// Python: set_hotkey from lines 63-69
    func setHotkey(_ config: HotkeyConfiguration) throws
}

/// Errors that can occur with hotkey system
enum HotkeyError: Error, LocalizedError {
    case permissionDenied
    case eventTapCreationFailed
    case alreadyListening
    case notListening

    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return """
            Input Monitoring permission denied.

            Please grant permission in:
            System Settings → Privacy & Security → Input Monitoring

            Add iSpeak to the list and enable it.
            """
        case .eventTapCreationFailed:
            return "Failed to create event tap for hotkey monitoring."
        case .alreadyListening:
            return "Hotkey service is already listening."
        case .notListening:
            return "Hotkey service is not listening."
        }
    }
}
