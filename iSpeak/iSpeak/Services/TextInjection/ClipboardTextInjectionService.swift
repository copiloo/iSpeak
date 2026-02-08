//
//  ClipboardTextInjectionService.swift
//  iSpeak
//
//  Text injection service using clipboard sandwich pattern
//  Implements Python's TextInjector from text_injector.py
//

import Foundation
import CoreGraphics

/// Text injection service using clipboard + Cmd+V
/// Matches Python's _paste_text method (lines 35-81)
final class ClipboardTextInjectionService: TextInjectionService {
    // MARK: - Properties

    /// Clipboard manager
    private let clipboardManager = ClipboardManager()

    // MARK: - Initialization

    init() {
        print("[TextInjection] Clipboard text injection service initialized")
    }

    // MARK: - TextInjectionService Protocol

    /// Inject text into active application via clipboard paste
    /// Python: _paste_text from lines 35-81
    func inject(_ text: String) async throws {
        guard !text.isEmpty else { return }

        print("[TextInjection] Starting paste operation for text: '\(text.prefix(30))...'")

        do {
            try await clipboardManager.withTemporaryContent(text) {
                // Small delay to ensure clipboard is updated
                // Python: time.sleep(0.025) from line 56
                try await Task.sleep(nanoseconds: 25_000_000)  // 25ms

                // Simulate Cmd+V
                // Python: lines 59-62
                try await simulateCmdV()

                // Wait for paste to complete
                // Python: time.sleep(0.05) from line 65
                try await Task.sleep(nanoseconds: 50_000_000)  // 50ms

                print("[TextInjection] Paste complete")
            }

            print("[TextInjection] ✅ Paste operation successful")
        } catch {
            print("[TextInjection] ❌ Error pasting text: \(error)")
            throw TextInjectionError.injectionFailed(error.localizedDescription)
        }
    }

    /// Press a special key
    /// Python: press_key from lines 83-103
    func pressKey(_ key: SpecialKey) async throws {
        print("[TextInjection] Pressing key: \(key.rawValue)")

        let keyDown = CGEvent(
            keyboardEventSource: nil,
            virtualKey: key.keyCode,
            keyDown: true
        )

        let keyUp = CGEvent(
            keyboardEventSource: nil,
            virtualKey: key.keyCode,
            keyDown: false
        )

        guard let down = keyDown, let up = keyUp else {
            throw TextInjectionError.keyEventCreationFailed
        }

        // Post events to system
        down.post(tap: CGEventTapLocation.cgSessionEventTap)
        up.post(tap: CGEventTapLocation.cgSessionEventTap)

        print("[TextInjection] ✅ Key pressed: \(key.rawValue)")
    }

    // MARK: - Private Methods

    /// Simulate Cmd+V keyboard shortcut
    /// Python: lines 59-62 (with self.keyboard.pressed(Key.cmd))
    private func simulateCmdV() async throws {
        // Create key events for Cmd+V
        // Cmd key code: 0x37 (Left Command)
        // V key code: 0x09

        let cmdDown = CGEvent(keyboardEventSource: nil, virtualKey: 0x37, keyDown: true)
        let vDown = CGEvent(keyboardEventSource: nil, virtualKey: 0x09, keyDown: true)
        let vUp = CGEvent(keyboardEventSource: nil, virtualKey: 0x09, keyDown: false)
        let cmdUp = CGEvent(keyboardEventSource: nil, virtualKey: 0x37, keyDown: false)

        guard let cmd1 = cmdDown,
              let v1 = vDown,
              let v2 = vUp,
              let cmd2 = cmdUp else {
            throw TextInjectionError.keyEventCreationFailed
        }

        // Set command flag on V key events
        cmd1.flags = .maskCommand
        v1.flags = .maskCommand

        // Post events in sequence
        cmd1.post(tap: CGEventTapLocation.cgSessionEventTap)
        v1.post(tap: CGEventTapLocation.cgSessionEventTap)
        v2.post(tap: CGEventTapLocation.cgSessionEventTap)
        cmd2.post(tap: CGEventTapLocation.cgSessionEventTap)

        print("[TextInjection] Simulated Cmd+V")
    }
}
