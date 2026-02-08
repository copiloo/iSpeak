//
//  ClipboardManager.swift
//  iSpeak
//
//  Manager for clipboard operations (NSPasteboard wrapper)
//  Sandboxable clipboard access
//

import Foundation
import AppKit

/// Manager for clipboard operations
final class ClipboardManager {
    // MARK: - Properties

    /// General pasteboard
    private let pasteboard = NSPasteboard.general

    // MARK: - Public Methods

    /// Read text from clipboard
    /// - Returns: Current clipboard text or nil
    /// Python: pyperclip.paste() from line 45
    func read() -> String? {
        pasteboard.string(forType: .string)
    }

    /// Write text to clipboard
    /// - Parameter text: Text to write
    /// Python: pyperclip.copy(text) from line 52
    func write(_ text: String) {
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
    }

    /// Save and restore clipboard (sandwich pattern)
    /// - Parameter operation: Operation to perform with new clipboard content
    /// - Returns: Result of operation
    /// Python: Clipboard sandwich from lines 43-71
    func withTemporaryContent<T>(
        _ newContent: String,
        operation: () async throws -> T
    ) async throws -> T {
        // Save old clipboard
        let oldClipboard = read()
        print("[TextInjection] Saved old clipboard")

        // Set new content
        write(newContent)
        print("[TextInjection] Copied text to clipboard")

        // Perform operation
        let result: T
        do {
            result = try await operation()
        } catch {
            // Restore clipboard even on error
            if let old = oldClipboard {
                write(old)
                print("[TextInjection] Restored old clipboard (after error)")
            }
            throw error
        }

        // Restore old clipboard
        if let old = oldClipboard {
            write(old)
            print("[TextInjection] Restored old clipboard")
        }

        return result
    }

    /// Check if clipboard is available
    /// - Returns: True if clipboard is accessible
    func isAvailable() -> Bool {
        return true  // NSPasteboard is always available in sandboxed apps
    }
}
