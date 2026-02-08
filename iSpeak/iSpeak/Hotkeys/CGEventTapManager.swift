//
//  CGEventTapManager.swift
//  iSpeak
//
//  Low-level CGEventTap management for global keyboard monitoring
//  Sandboxable with input-monitoring entitlement
//

import Foundation
import CoreGraphics
import ApplicationServices

/// Manager for CGEventTap
final class CGEventTapManager {
    // MARK: - Properties

    /// Event tap instance
    private var eventTap: CFMachPort?

    /// Run loop source
    private var runLoopSource: CFRunLoopSource?

    /// Event mask for key events (including flagsChanged for modifier keys)
    private let eventMask: CGEventMask = (1 << CGEventType.keyDown.rawValue) |
                                          (1 << CGEventType.keyUp.rawValue) |
                                          (1 << CGEventType.flagsChanged.rawValue)

    /// Event handler callback
    private var eventHandler: ((CGEvent) -> Unmanaged<CGEvent>?)?

    // MARK: - Public Methods

    /// Check if accessibility permission is granted
    /// Returns true if permission granted, false otherwise
    static func checkPermission() -> Bool {
        let trusted = AXIsProcessTrusted()

        if !trusted {
            print("[Hotkey] ⚠️  Accessibility permission not granted")
            print("[Hotkey] Please enable in: System Settings → Privacy & Security → Accessibility")
        }

        return trusted
    }

    /// Request accessibility permission
    /// Shows system prompt dialog if not already granted
    static func requestPermission() {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeUnretainedValue(): true]
        let trusted = AXIsProcessTrustedWithOptions(options)

        if !trusted {
            print("[Hotkey] Requesting accessibility permission...")
        }
    }

    /// Create and start event tap
    /// - Parameter handler: Callback for handling events
    /// - Throws: HotkeyError if creation fails
    func createEventTap(handler: @escaping (CGEvent) -> Unmanaged<CGEvent>?) throws {
        self.eventHandler = handler

        // Create event tap
        // location: .cgSessionEventTap for session-wide monitoring
        // place: .headInsertEventTap to see events before apps
        // options: .defaultTap (pass through events)
        // eventsOfInterest: key down/up events
        // callback: our handler
        // userInfo: self reference
        guard let tap = CGEvent.tapCreate(
            tap: CGEventTapLocation.cgSessionEventTap,
            place: .headInsertEventTap,
            options: .defaultTap,
            eventsOfInterest: eventMask,
            callback: { proxy, type, event, userInfo in
                // Get manager instance from userInfo
                let manager = Unmanaged<CGEventTapManager>.fromOpaque(userInfo!).takeUnretainedValue()

                // Call handler
                return manager.eventHandler?(event) ?? Unmanaged.passUnretained(event)
            },
            userInfo: Unmanaged.passUnretained(self).toOpaque()
        ) else {
            throw HotkeyError.eventTapCreationFailed
        }

        self.eventTap = tap

        // Create run loop source and add to current run loop
        let runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
        self.runLoopSource = runLoopSource

        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)

        // Enable the event tap
        CGEvent.tapEnable(tap: tap, enable: true)

        print("[Hotkey] Event tap created and enabled")
    }

    /// Destroy event tap and clean up
    func destroyEventTap() {
        if let source = runLoopSource {
            CFRunLoopRemoveSource(CFRunLoopGetCurrent(), source, .commonModes)
            runLoopSource = nil
        }

        if let tap = eventTap {
            CGEvent.tapEnable(tap: tap, enable: false)
            eventTap = nil
        }

        eventHandler = nil

        print("[Hotkey] Event tap destroyed")
    }

    deinit {
        destroyEventTap()
    }
}
