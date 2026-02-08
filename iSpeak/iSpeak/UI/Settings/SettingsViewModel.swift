//
//  SettingsViewModel.swift
//  iSpeak
//
//  View model for settings window
//

import Foundation
import SwiftUI
import Observation

/// View model for settings window
@Observable
@MainActor
final class SettingsViewModel {
    // MARK: - Properties

    /// Reference to coordinator for reading/writing settings
    weak var coordinator: AppCoordinator?

    /// Available languages
    let availableLanguages = Language.allCases

    /// Available model sizes
    let availableModels = iSpeakModelSize.allCases

    /// Current language (bound to coordinator)
    var currentLanguage: Language {
        get { coordinator?.currentLanguage ?? .english }
        set { coordinator?.currentLanguage = newValue }
    }

    /// Current model (bound to coordinator)
    var currentModel: iSpeakModelSize {
        get { coordinator?.currentModel ?? .small }
        set { coordinator?.currentModel = newValue }
    }

    /// Auto-enter enabled (bound to coordinator)
    var autoEnterEnabled: Bool {
        get { coordinator?.autoEnterEnabled ?? false }
        set { coordinator?.autoEnterEnabled = newValue }
    }

    // MARK: - Computed Properties

    /// App version from bundle
    var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
    }

    /// Build number from bundle
    var buildNumber: String {
        Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
    }

    /// Models directory path
    var modelsDirectory: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("iSpeak")
            .appendingPathComponent("models")
    }

    // MARK: - Initialization

    init(coordinator: AppCoordinator? = nil) {
        self.coordinator = coordinator
    }

    // MARK: - Actions

    /// Open models directory in Finder
    func openModelsDirectory() {
        NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: modelsDirectory.path)
    }

    /// Open System Settings for microphone permissions
    func openMicrophoneSettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone") {
            NSWorkspace.shared.open(url)
        }
    }

    /// Open System Settings for input monitoring permissions
    func openInputMonitoringSettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility") {
            NSWorkspace.shared.open(url)
        }
    }
}
