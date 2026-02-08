//
//  SettingsWindow.swift
//  iSpeak
//
//  Settings window wrapper
//

import SwiftUI
import AppKit

/// Settings window manager
@MainActor
final class SettingsWindow {
    // MARK: - Properties

    /// The actual window
    private var window: NSWindow?

    /// Reference to coordinator
    private weak var coordinator: AppCoordinator?

    // MARK: - Initialization

    init(coordinator: AppCoordinator?) {
        self.coordinator = coordinator
    }

    // MARK: - Public Methods

    /// Show settings window
    func show() {
        if let window = window {
            // Window already exists, just bring to front
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }

        // Create new window
        let settingsView = SettingsView(coordinator: coordinator)
        let hostingController = NSHostingController(rootView: settingsView)

        let newWindow = NSWindow(contentViewController: hostingController)
        newWindow.title = "iSpeak Settings"
        newWindow.styleMask = [.titled, .closable, .miniaturizable]
        newWindow.isReleasedWhenClosed = false
        newWindow.center()
        newWindow.setFrameAutosaveName("SettingsWindow")

        // Prevent window from being minimized to Dock (we're accessory app)
        newWindow.collectionBehavior = [.canJoinAllSpaces]

        // Show window
        newWindow.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        self.window = newWindow
    }

    /// Hide settings window
    func hide() {
        window?.close()
    }
}
