//
//  MenuBarController.swift
//  iSpeak
//
//  Manages the menu bar icon and menu
//

import AppKit
import SwiftUI

class MenuBarController {
    private var statusItem: NSStatusItem?
    private var currentLanguage: Language = .english
    private var currentModel: ModelSize = .small
    private var autoEnterEnabled: Bool = false

    init() {
        setupMenuBar()
    }

    private func setupMenuBar() {
        // Create status bar item
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

        guard let button = statusItem?.button else {
            print("Failed to create status bar button")
            return
        }

        // Set icon - for now use a system symbol, we'll replace with custom icon later
        if let image = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "iSpeak") {
            image.size = NSSize(width: 18, height: 18)
            button.image = image
        }

        // Create menu
        let menu = NSMenu()

        // Language section
        menu.addItem(NSMenuItem(title: "Language", action: nil, keyEquivalent: ""))
        menu.addItem(createLanguageItem(.english))
        menu.addItem(createLanguageItem(.romanian))
        menu.addItem(NSMenuItem.separator())

        // Model section
        menu.addItem(NSMenuItem(title: "Model", action: nil, keyEquivalent: ""))
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
        autoEnterItem.state = autoEnterEnabled ? .on : .off
        menu.addItem(autoEnterItem)
        menu.addItem(NSMenuItem.separator())

        // Settings (placeholder for Phase 10)
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

        statusItem?.menu = menu
    }

    private func createLanguageItem(_ language: Language) -> NSMenuItem {
        let item = NSMenuItem(
            title: "  \(language.displayName)",
            action: #selector(selectLanguage(_:)),
            keyEquivalent: ""
        )
        item.target = self
        item.representedObject = language
        item.state = language == currentLanguage ? .on : .off
        return item
    }

    private func createModelItem(_ model: ModelSize) -> NSMenuItem {
        let item = NSMenuItem(
            title: "  \(model.displayName)",
            action: #selector(selectModel(_:)),
            keyEquivalent: ""
        )
        item.target = self
        item.representedObject = model
        item.state = model == currentModel ? .on : .off
        return item
    }

    @objc private func selectLanguage(_ sender: NSMenuItem) {
        guard let language = sender.representedObject as? Language else { return }
        currentLanguage = language

        // Update menu checkmarks
        if let menu = statusItem?.menu {
            for item in menu.items {
                if let itemLanguage = item.representedObject as? Language {
                    item.state = itemLanguage == language ? .on : .off
                }
            }
        }

        // TODO: Notify AppCoordinator of language change (Phase 9)
        print("Language changed to: \(language.displayName)")
    }

    @objc private func selectModel(_ sender: NSMenuItem) {
        guard let model = sender.representedObject as? ModelSize else { return }
        currentModel = model

        // Update menu checkmarks
        if let menu = statusItem?.menu {
            for item in menu.items {
                if let itemModel = item.representedObject as? ModelSize {
                    item.state = itemModel == model ? .on : .off
                }
            }
        }

        // TODO: Notify AppCoordinator of model change (Phase 9)
        print("Model changed to: \(model.displayName)")
    }

    @objc private func toggleAutoEnter(_ sender: NSMenuItem) {
        autoEnterEnabled.toggle()
        sender.state = autoEnterEnabled ? .on : .off

        // TODO: Notify AppCoordinator of auto-enter change (Phase 9)
        print("Auto-enter: \(autoEnterEnabled)")
    }

    @objc private func openSettings() {
        // TODO: Open settings window (Phase 10)
        print("Settings clicked - to be implemented in Phase 10")
    }

    func cleanup() {
        if let statusItem = statusItem {
            NSStatusBar.system.removeStatusItem(statusItem)
        }
    }
}

// MARK: - Supporting Types

enum Language: String, CaseIterable {
    case english = "en"
    case romanian = "ro"

    var displayName: String {
        switch self {
        case .english: return "English"
        case .romanian: return "Romanian"
        }
    }

    var code: String {
        return rawValue
    }
}

enum ModelSize: String, CaseIterable {
    case tiny = "tiny"
    case base = "base"
    case small = "small"
    case medium = "medium"
    case large = "large"
    case largeTurbo = "large-v3-turbo"

    var displayName: String {
        switch self {
        case .tiny: return "Tiny (fastest, least accurate)"
        case .base: return "Base"
        case .small: return "Small (recommended)"
        case .medium: return "Medium"
        case .large: return "Large"
        case .largeTurbo: return "Large V3 Turbo (best, slower)"
        }
    }
}
