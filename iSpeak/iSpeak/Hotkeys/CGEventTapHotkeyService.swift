//
//  CGEventTapHotkeyService.swift
//  iSpeak
//
//  Global hotkey service using CGEventTap
//  Implements Python's HotkeyController from hotkey_controller.py
//

import Foundation
import CoreGraphics

/// Global hotkey service using CGEventTap
/// Matches Python's HotkeyController behavior (lines 6-76)
/// NOTE: Must NOT be @Observable — properties are accessed from the CGEventTap
/// callback thread, and @Observable's observation registrar is not thread-safe.
final class CGEventTapHotkeyService: HotkeyService {
    // MARK: - Properties

    /// Event tap manager
    private var eventTapManager: CGEventTapManager?

    /// Whether currently listening
    private(set) var isListening: Bool = false

    /// Current hotkey configuration
    private(set) var configuration: HotkeyConfiguration

    /// Press callback
    private var onPressCallback: (() -> Void)?

    /// Release callback
    private var onReleaseCallback: (() -> Void)?

    /// Thread-safe state protection
    /// Python: self._state_lock = threading.Lock() from line 17
    private let stateLock = NSLock()

    /// Whether key is currently pressed
    /// Python: self.is_recording from line 16
    private var isKeyPressed: Bool = false

    // MARK: - Initialization

    /// Initialize with default Right Option key
    /// Python: Default hotkey from line 21
    init(configuration: HotkeyConfiguration = .defaultRightOption) {
        self.configuration = configuration
        print("[Hotkey] Service initialized with hotkey: \(configuration.displayName)")
    }

    // MARK: - HotkeyService Protocol

    /// Start listening for global hotkey events
    /// Python: start_listening from lines 25-33
    func startListening(
        onPress: @escaping () -> Void,
        onRelease: @escaping () -> Void
    ) async throws {
        guard !isListening else {
            throw HotkeyError.alreadyListening
        }

        // Store callbacks
        self.onPressCallback = onPress
        self.onReleaseCallback = onRelease

        // Reset state
        stateLock.withLock {
            isKeyPressed = false
        }

        // Create event tap manager
        let manager = CGEventTapManager()
        self.eventTapManager = manager

        // Create event tap with our handler
        try manager.createEventTap { [weak self] event in
            self?.handleEvent(event)
        }

        isListening = true
        print("[Hotkey] 🎯 Hotkey listener started. Press \(configuration.displayName) to dictate.")
    }

    /// Stop listening for hotkey events
    /// Python: stop_listening from lines 35-39
    func stopListening() {
        guard isListening else { return }

        eventTapManager?.destroyEventTap()
        eventTapManager = nil

        onPressCallback = nil
        onReleaseCallback = nil

        isListening = false
        print("[Hotkey] Hotkey listener stopped.")
    }

    /// Change the hotkey configuration
    /// Python: set_hotkey from lines 63-69
    func setHotkey(_ config: HotkeyConfiguration) throws {
        let wasListening = isListening

        // Stop if listening
        if wasListening {
            stopListening()
        }

        self.configuration = config
        print("[Hotkey] Hotkey changed to: \(config.displayName)")

        // Restart if was listening
        if wasListening {
            // Note: Can't use async in sync method, caller must restart
            print("[Hotkey] ⚠️  Please restart listening for new hotkey to take effect")
        }
    }

    // MARK: - Private Methods

    /// Handle keyboard event
    /// Returns event to pass through or nil to consume
    private func handleEvent(_ event: CGEvent) -> Unmanaged<CGEvent>? {
        let eventType = event.type

        // Modifier keys (Option, Command, etc.) generate flagsChanged events,
        // not keyDown/keyUp. We detect press/release by checking the flags.
        if eventType == .flagsChanged {
            return handleFlagsChanged(event)
        }

        // For regular key events, pass through
        return Unmanaged.passUnretained(event)
    }

    /// Handle modifier key press/release via flagsChanged events
    private func handleFlagsChanged(_ event: CGEvent) -> Unmanaged<CGEvent>? {
        let keyCode = event.getIntegerValueField(.keyboardEventKeycode)

        // Check if this is our hotkey
        guard keyCode == Int64(configuration.keyCode) else {
            return Unmanaged.passUnretained(event)
        }

        // For flagsChanged, detect press vs release by checking
        // whether the modifier flag is currently set in the event flags
        let flags = event.flags
        let isOptionDown = flags.contains(.maskAlternate)

        // Determine action under lock, dispatch via GCD outside lock.
        // DispatchQueue.main.async is REQUIRED here to bridge from the CFRunLoop
        // callback context to GCD, where the Swift MainActor executor drains.
        var action: (() -> Void)?

        stateLock.withLock {
            if isOptionDown && !isKeyPressed {
                isKeyPressed = true
                print("[Hotkey] ⬇️  Hotkey pressed (Right Option)")
                action = onPressCallback
            } else if !isOptionDown && isKeyPressed {
                isKeyPressed = false
                print("[Hotkey] ⬆️  Hotkey released (Right Option)")
                action = onReleaseCallback
            }
        }

        if let action {
            CFRunLoopPerformBlock(CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue) {
                action()
            }
            CFRunLoopWakeUp(CFRunLoopGetMain())
        }

        // Pass through the event
        return Unmanaged.passUnretained(event)
    }

    // MARK: - Deinitialization

    deinit {
        stopListening()
    }
}
