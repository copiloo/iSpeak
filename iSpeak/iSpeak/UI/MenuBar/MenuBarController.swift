//
//  MenuBarController.swift
//  iSpeak
//
//  Manages the menu bar icon and menu
//

import AppKit
import SwiftUI

class MenuBarController: NSObject, NSMenuDelegate {
    private var statusItem: NSStatusItem?

    /// Reference to AppCoordinator for state updates
    weak var coordinator: AppCoordinator?

    /// Settings window
    private var settingsWindow: SettingsWindow?

    /// Timer for updating status bar during downloads
    private var progressTimer: Timer?

    override init() {
        super.init()
        setupMenuBar()
    }

    /// Start polling coordinator state to update the status bar icon
    func startProgressUpdates() {
        stopProgressUpdates()
        progressTimer = Timer.scheduledTimer(withTimeInterval: 0.3, repeats: true) { [weak self] _ in
            self?.updateStatusBarFromState()
        }
    }

    /// Stop polling
    func stopProgressUpdates() {
        progressTimer?.invalidate()
        progressTimer = nil
    }

    // MARK: - Setup

    private func setupMenuBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

        guard let button = statusItem?.button else {
            print("Failed to create status bar button")
            return
        }

        // Set initial icon
        updateStatusBarIcon(button)

        // Empty menu — items are populated dynamically in menuWillOpen
        let menu = NSMenu()
        menu.delegate = self
        statusItem?.menu = menu
    }

    // MARK: - NSMenuDelegate

    func menuWillOpen(_ menu: NSMenu) {
        // Rebuild all items fresh each time the menu opens.
        // This ensures checkmarks, status text, and model state are always current.
        menu.removeAllItems()

        // Accessibility permission warning (if not granted)
        if coordinator?.accessibilityGranted == false {
            let warningItem = NSMenuItem(title: "⚠️ Accessibility Permission Required", action: nil, keyEquivalent: "")
            warningItem.isEnabled = false
            menu.addItem(warningItem)

            let openSettingsItem = NSMenuItem(
                title: "   Open System Settings...",
                action: #selector(openAccessibilitySettings),
                keyEquivalent: ""
            )
            openSettingsItem.target = self
            menu.addItem(openSettingsItem)
            menu.addItem(NSMenuItem.separator())
        }

        // Status header
        let statusText = coordinator?.statusMessage ?? "iSpeak"
        let headerItem = NSMenuItem(title: statusText, action: nil, keyEquivalent: "")
        headerItem.isEnabled = false
        menu.addItem(headerItem)
        menu.addItem(NSMenuItem.separator())

        // Language section
        let langHeader = NSMenuItem(title: "Language", action: nil, keyEquivalent: "")
        langHeader.isEnabled = false
        menu.addItem(langHeader)
        menu.addItem(createLanguageItem(.english))
        menu.addItem(createLanguageItem(.romanian))
        menu.addItem(NSMenuItem.separator())

        // Model section
        let modelHeader = NSMenuItem(title: "Model (select to download)", action: nil, keyEquivalent: "")
        modelHeader.isEnabled = false
        menu.addItem(modelHeader)
        menu.addItem(createModelItem(.tiny))
        menu.addItem(createModelItem(.base))
        menu.addItem(createModelItem(.small))
        menu.addItem(createModelItem(.medium))
        menu.addItem(createModelItem(.large))
        menu.addItem(createModelItem(.largeTurbo))
        menu.addItem(NSMenuItem.separator())

        // Auto-enter toggle
        let autoEnterItem = NSMenuItem(
            title: "Auto-press Enter",
            action: #selector(toggleAutoEnter),
            keyEquivalent: ""
        )
        autoEnterItem.target = self
        autoEnterItem.state = (coordinator?.autoEnterEnabled ?? false) ? .on : .off
        menu.addItem(autoEnterItem)
        menu.addItem(NSMenuItem.separator())

        // Settings
        let settingsItem = NSMenuItem(
            title: "Settings...",
            action: #selector(openSettings),
            keyEquivalent: ","
        )
        settingsItem.target = self
        menu.addItem(settingsItem)
        menu.addItem(NSMenuItem.separator())

        // Quit
        menu.addItem(NSMenuItem(
            title: "Quit iSpeak",
            action: #selector(NSApplication.terminate(_:)),
            keyEquivalent: "q"
        ))
    }

    // MARK: - Status Bar Icon

    private func updateStatusBarIcon(_ button: NSStatusBarButton) {
        // Show gear icon when Accessibility permission is missing
        if coordinator?.accessibilityGranted == false {
            if let image = NSImage(systemSymbolName: "gearshape", accessibilityDescription: "iSpeak - Setup Required") {
                image.size = NSSize(width: 18, height: 18)
                button.image = image
                button.title = ""
            }
            return
        }

        let state = coordinator?.modelDownloadState ?? .idle

        switch state {
        case .idle:
            if let image = NSImage(systemSymbolName: "mic.badge.xmark", accessibilityDescription: "iSpeak - No model") {
                image.size = NSSize(width: 18, height: 18)
                button.image = image
                button.title = ""
            }
        case .downloading(let progress):
            let pct = Int(progress * 100)
            button.image = nil
            button.title = "\(pct)%"
        case .loading:
            button.image = nil
            button.title = "Loading..."
        case .ready:
            if let image = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "iSpeak") {
                image.size = NSSize(width: 18, height: 18)
                button.image = image
                button.title = ""
            }
        case .error:
            if let image = NSImage(systemSymbolName: "exclamationmark.triangle", accessibilityDescription: "iSpeak - Error") {
                image.size = NSSize(width: 18, height: 18)
                button.image = image
                button.title = ""
            }
        }
    }

    /// Update status bar from coordinator state (called by timer)
    private func updateStatusBarFromState() {
        guard let button = statusItem?.button else { return }
        updateStatusBarIcon(button)

        // Stop timer when no longer downloading/loading
        if let state = coordinator?.modelDownloadState {
            switch state {
            case .downloading, .loading:
                break // keep timer running
            default:
                stopProgressUpdates()
            }
        }
    }

    // MARK: - Menu Item Factories

    private func createLanguageItem(_ language: Language) -> NSMenuItem {
        let item = NSMenuItem(
            title: "  \(language.displayName)",
            action: #selector(selectLanguage(_:)),
            keyEquivalent: ""
        )
        item.target = self
        item.representedObject = language
        item.state = language == coordinator?.currentLanguage ? .on : .off
        return item
    }

    private func createModelItem(_ model: iSpeakModelSize) -> NSMenuItem {
        let isSelected = model == coordinator?.currentModel && coordinator?.modelReady == true
        let title = "  \(model.displayName)"

        let item = NSMenuItem(
            title: title,
            action: #selector(selectModel(_:)),
            keyEquivalent: ""
        )
        item.target = self
        item.representedObject = model
        item.state = isSelected ? .on : .off

        // Disable during download/loading
        if case .downloading = coordinator?.modelDownloadState {
            item.isEnabled = false
        } else if case .loading = coordinator?.modelDownloadState {
            item.isEnabled = false
        }

        return item
    }

    // MARK: - Actions

    @objc private func selectLanguage(_ sender: NSMenuItem) {
        guard let language = sender.representedObject as? Language else { return }
        coordinator?.currentLanguage = language
    }

    @objc private func selectModel(_ sender: NSMenuItem) {
        guard let model = sender.representedObject as? iSpeakModelSize else { return }
        coordinator?.downloadAndLoadModel(model)
        startProgressUpdates()
    }

    @objc private func toggleAutoEnter(_ sender: NSMenuItem) {
        if let coordinator = coordinator {
            coordinator.autoEnterEnabled.toggle()
            sender.state = coordinator.autoEnterEnabled ? .on : .off
        }
    }

    @objc private func openAccessibilitySettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility") {
            NSWorkspace.shared.open(url)
        }
    }

    @objc private func openSettings() {
        if settingsWindow == nil {
            settingsWindow = SettingsWindow(coordinator: coordinator)
        }
        settingsWindow?.show()
    }

    func cleanup() {
        stopProgressUpdates()
        if let statusItem = statusItem {
            NSStatusBar.system.removeStatusItem(statusItem)
        }
    }
}
