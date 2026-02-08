//
//  OverlayWindow.swift
//  iSpeak
//
//  Floating overlay window for visual feedback
//  Implements Python's OverlayWidget from overlay_widget.py
//

import AppKit
import Observation

/// Floating overlay window for recording/processing feedback
/// Matches Python's OverlayWidget behavior
@MainActor
final class OverlayWindow {
    // MARK: - Properties

    /// The actual NSWindow
    private var window: NSPanel?

    /// Content view with animations
    private var contentView: OverlayView?

    /// Current state
    private(set) var state: OverlayState = .hidden

    // Window dimensions (Python: lines 40-42)
    private let windowWidth: CGFloat = 80
    private let windowHeight: CGFloat = 20
    private let cornerRadius: CGFloat = 15

    // MARK: - Initialization

    init() {
        setupWindow()
        print("[Overlay] Overlay window initialized")
    }

    // MARK: - Public Methods

    /// Show listening state with waveform animation
    /// Python: show_listening from lines 195-205
    func show(_ newState: OverlayState) {
        guard state != newState else { return }

        state = newState

        switch newState {
        case .hidden:
            hide()
        case .listening:
            showListening()
        case .processing:
            showProcessing()
        case .streaming(let text):
            showStreaming(text: text)
        }
    }

    /// Hide overlay
    /// Python: hide_overlay from lines 237-243
    func hide() {
        state = .hidden
        contentView?.stopAnimations()
        window?.orderOut(nil)
        print("[Overlay] Hidden")
    }

    // MARK: - Private Methods

    /// Setup the overlay window
    /// Python: __init__ from lines 32-98
    private func setupWindow() {
        // Calculate position (bottom-center of screen)
        // Python: lines 62-70
        guard let screen = NSScreen.main else { return }

        let screenFrame = screen.visibleFrame
        let x = (screenFrame.width - windowWidth) / 2 + screenFrame.origin.x
        let y = screenFrame.origin.y + 50  // 50pt from bottom

        let windowRect = NSRect(
            x: x,
            y: y,
            width: windowWidth,
            height: windowHeight
        )

        // Create window with special properties
        // Python: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint from lines 77-82
        window = NSPanel(
            contentRect: windowRect,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )

        guard let window = window else { return }

        // Window behavior
        window.level = .floating  // Always on top (Python: Qt.WindowStaysOnTopHint)
        window.backgroundColor = .clear
        window.isOpaque = false
        window.hasShadow = true
        window.collectionBehavior = [.canJoinAllSpaces, .stationary]

        // Don't steal focus (Python: lines 83-85)
        window.hidesOnDeactivate = false
        window.isMovable = false

        // Create content view
        contentView = OverlayView(frame: windowRect.size)
        contentView?.wantsLayer = true
        contentView?.layer?.cornerRadius = cornerRadius
        contentView?.layer?.masksToBounds = true

        window.contentView = contentView
    }

    /// Show listening state
    /// Python: show_listening from lines 195-205
    private func showListening() {
        guard let window = window, let contentView = contentView else { return }

        print("[Overlay] Showing listening state")

        // Update content view to show waveform
        contentView.setState(.listening)

        // Show window
        window.orderFrontRegardless()
    }

    /// Show processing state
    /// Python: show_processing from lines 207-217
    private func showProcessing() {
        guard let window = window, let contentView = contentView else { return }

        print("[Overlay] Showing processing state")

        // Update content view to show bouncing dots
        contentView.setState(.processing)

        // Show window (if not already visible)
        if !window.isVisible {
            window.orderFrontRegardless()
        }
    }

    /// Show streaming state with live text
    /// Python: show_streaming from lines 219-235
    private func showStreaming(text: String) {
        guard let window = window, let contentView = contentView else { return }

        print("[Overlay] Showing streaming state: '\(text.prefix(30))...'")

        // Update content view to show text + mini waveform
        contentView.setState(.streaming(text: text))

        // Show window (if not already visible)
        if !window.isVisible {
            window.orderFrontRegardless()
        }
    }
}

// MARK: - OverlayView Helper

/// Helper extension for NSRect size initialization
private extension OverlayView {
    convenience init(frame size: CGSize) {
        self.init(frame: NSRect(origin: .zero, size: size))
    }
}
