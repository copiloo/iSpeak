//
//  SettingsView.swift
//  iSpeak
//
//  Settings window UI
//

import SwiftUI

/// Settings window main view
struct SettingsView: View {
    // MARK: - Properties

    @State private var viewModel: SettingsViewModel

    // MARK: - Initialization

    init(coordinator: AppCoordinator?) {
        _viewModel = State(initialValue: SettingsViewModel(coordinator: coordinator))
    }

    // MARK: - Body

    var body: some View {
        TabView {
            // General tab
            GeneralSettingsView(viewModel: viewModel)
                .tabItem {
                    Label("General", systemImage: "gear")
                }
                .tag(0)

            // Keyboard tab
            KeyboardSettingsView(viewModel: viewModel)
                .tabItem {
                    Label("Keyboard", systemImage: "keyboard")
                }
                .tag(1)

            // Permissions tab
            PermissionsSettingsView(viewModel: viewModel)
                .tabItem {
                    Label("Permissions", systemImage: "lock.shield")
                }
                .tag(2)

            // About tab
            AboutSettingsView(viewModel: viewModel)
                .tabItem {
                    Label("About", systemImage: "info.circle")
                }
                .tag(3)
        }
        .frame(width: 500, height: 400)
    }
}

// MARK: - General Settings

struct GeneralSettingsView: View {
    let viewModel: SettingsViewModel

    var body: some View {
        Form {
            Section("Transcription") {
                Picker("Language:", selection: Binding(
                    get: { viewModel.currentLanguage },
                    set: { viewModel.currentLanguage = $0 }
                )) {
                    ForEach(viewModel.availableLanguages, id: \.self) { language in
                        Text(language.displayName).tag(language)
                    }
                }
                .pickerStyle(.menu)

                Picker("Model:", selection: Binding(
                    get: { viewModel.currentModel },
                    set: { viewModel.currentModel = $0 }
                )) {
                    ForEach(viewModel.availableModels, id: \.self) { model in
                        Text(model.displayName).tag(model)
                    }
                }
                .pickerStyle(.menu)

                Text("Model determines accuracy and speed. 'Small' is recommended for Romanian.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Section("Models Directory") {
                HStack {
                    Text(viewModel.modelsDirectory.path)
                        .font(.system(.caption, design: .monospaced))
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                        .truncationMode(.middle)

                    Spacer()

                    Button("Open") {
                        viewModel.openModelsDirectory()
                    }
                }

                Text("Downloaded Whisper models are stored here.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .formStyle(.grouped)
        .padding(20)
    }
}

// MARK: - Keyboard Settings

struct KeyboardSettingsView: View {
    let viewModel: SettingsViewModel

    var body: some View {
        Form {
            Section("Hotkey") {
                HStack {
                    Text("Recording Hotkey:")
                    Spacer()
                    Text("Right Option (⌥)")
                        .font(.system(.body, design: .monospaced))
                        .foregroundColor(.secondary)
                }

                Text("Hold Right Option to record, release to transcribe.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Section("Behavior") {
                Toggle("Auto-press Enter after dictation", isOn: Binding(
                    get: { viewModel.autoEnterEnabled },
                    set: { viewModel.autoEnterEnabled = $0 }
                ))

                Text("Useful for Terminal and command-line apps.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .formStyle(.grouped)
        .padding(20)
    }
}

// MARK: - Permissions Settings

struct PermissionsSettingsView: View {
    let viewModel: SettingsViewModel

    var body: some View {
        Form {
            Section("Required Permissions") {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "mic.fill")
                            .foregroundColor(.blue)
                            .frame(width: 24)

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Microphone Access")
                                .font(.headline)
                            Text("Required for voice recording")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        Spacer()

                        Button("Open Settings") {
                            viewModel.openMicrophoneSettings()
                        }
                    }

                    Divider()

                    HStack {
                        Image(systemName: "keyboard.fill")
                            .foregroundColor(.purple)
                            .frame(width: 24)

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Accessibility")
                                .font(.headline)
                            Text("Required for global hotkey (Right Option)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        Spacer()

                        Button("Open Settings") {
                            viewModel.openInputMonitoringSettings()
                        }
                    }
                }
                .padding(.vertical, 8)
            }

            Section {
                Text("iSpeak needs these permissions to function. Your voice never leaves your Mac - all processing happens offline.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .formStyle(.grouped)
        .padding(20)
    }
}

// MARK: - About Settings

struct AboutSettingsView: View {
    let viewModel: SettingsViewModel

    var body: some View {
        VStack(spacing: 24) {
            // App Icon
            if let appIcon = NSImage(named: "AppIcon") {
                Image(nsImage: appIcon)
                    .resizable()
                    .frame(width: 80, height: 80)
                    .cornerRadius(16)
            } else {
                Image(systemName: "mic.circle.fill")
                    .resizable()
                    .frame(width: 80, height: 80)
                    .foregroundColor(.accentColor)
            }

            // App Info
            VStack(spacing: 4) {
                Text("iSpeak")
                    .font(.title)
                    .fontWeight(.bold)

                Text("Version \(viewModel.appVersion) (\(viewModel.buildNumber))")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            // Description
            Text("Offline voice dictation for developers")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            Divider()
                .padding(.horizontal, 60)

            // Features
            VStack(spacing: 12) {
                FeatureRow(icon: "lock.fill", title: "Private", description: "All processing happens on your Mac")
                FeatureRow(icon: "bolt.fill", title: "Fast", description: "Optimized with WhisperKit + CoreML")
                FeatureRow(icon: "text.word.spacing", title: "Code-Aware", description: "Romanian diacritics + code patterns")
            }

            Spacer()

            // Footer
            Text("Built with ❤️ for developers")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(20)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Feature Row

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.accentColor)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()
        }
        .padding(.horizontal, 40)
    }
}

// MARK: - Preview

#Preview {
    SettingsView(coordinator: nil)
}
