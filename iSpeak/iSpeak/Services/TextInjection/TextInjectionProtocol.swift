//
//  TextInjectionProtocol.swift
//  iSpeak
//
//  Protocol for text injection service
//  Enables testing with mock implementations
//

import Foundation
import CoreGraphics

/// Protocol for text injection service
protocol TextInjectionService {
    /// Inject text into the active application
    /// - Parameter text: Text to inject
    /// - Throws: TextInjectionError if injection fails
    /// Python: type_text from lines 12-23 (instant=True)
    func inject(_ text: String) async throws

    /// Press a special key (Enter, Tab, etc.)
    /// - Parameter key: Key to press
    /// - Throws: TextInjectionError if key press fails
    /// Python: press_key from lines 83-103
    func pressKey(_ key: SpecialKey) async throws
}

/// Special keys that can be pressed
enum SpecialKey: String {
    case enter = "enter"
    case tab = "tab"
    case escape = "escape"
    case space = "space"
    case backspace = "backspace"
    case delete = "delete"

    /// Virtual key code for macOS
    var keyCode: CGKeyCode {
        switch self {
        case .enter: return 0x24      // Return key
        case .tab: return 0x30        // Tab key
        case .escape: return 0x35     // Escape key
        case .space: return 0x31      // Space key
        case .backspace: return 0x33  // Delete/Backspace key
        case .delete: return 0x75     // Forward delete key
        }
    }
}

/// Errors that can occur during text injection
enum TextInjectionError: Error, LocalizedError {
    case clipboardAccessFailed
    case keyEventCreationFailed
    case injectionFailed(String)

    var errorDescription: String? {
        switch self {
        case .clipboardAccessFailed:
            return "Failed to access clipboard"
        case .keyEventCreationFailed:
            return "Failed to create keyboard event"
        case .injectionFailed(let message):
            return "Text injection failed: \(message)"
        }
    }
}
