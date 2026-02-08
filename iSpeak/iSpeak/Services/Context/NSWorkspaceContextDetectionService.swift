//
//  NSWorkspaceContextDetectionService.swift
//  iSpeak
//
//  Context detection service using NSWorkspace
//  Implements Python's ContextDetector from context_detector.py
//

import Foundation
import AppKit

/// Context detection service using NSWorkspace
/// Matches Python's ContextDetector behavior
final class NSWorkspaceContextDetectionService: ContextDetectionService {
    // MARK: - Properties

    /// Shared workspace instance
    private let workspace = NSWorkspace.shared

    // MARK: - Initialization

    init() {
        print("[Context] NSWorkspace context detection service initialized")
    }

    // MARK: - ContextDetectionService Protocol

    /// Get current application context
    /// Python: get_current_context from lines 21-50
    func getCurrentContext() -> AppContext {
        guard let frontApp = workspace.frontmostApplication else {
            print("[Context] Could not get frontmost application")
            return .unknown
        }

        let appName = frontApp.localizedName ?? "Unknown"
        let bundleID = frontApp.bundleIdentifier ?? ""
        let fileType = guessFileType(for: appName)

        return AppContext(
            appName: appName,
            bundleID: bundleID,
            fileType: fileType
        )
    }

    // MARK: - Private Methods

    /// Guess file type based on application name
    /// Python: _guess_file_type from lines 52-79
    private func guessFileType(for appName: String) -> String {
        // Map specialized IDEs to their primary file types
        // Generic editors (VS Code, Sublime) return empty since they're multi-language
        // Python: app_file_map from lines 62-71
        let appFileMap: [String: String] = [
            "PyCharm": ".py",
            "IntelliJ IDEA": ".java",
            "WebStorm": ".js",
            "GoLand": ".go",
            "RubyMine": ".rb",
            "Xcode": ".swift",
            "Android Studio": ".kt",
            "TextEdit": ".txt"
        ]

        // Check if app name contains any of the specialized IDE names
        // Python: lines 73-75
        for (key, fileType) in appFileMap {
            if appName.contains(key) {
                return fileType
            }
        }

        // Generic multi-language editors - return empty to avoid wrong assumptions
        // Code formatting will still apply based on app detection in isCodeEditor()
        // Python: line 79
        return ""
    }
}
