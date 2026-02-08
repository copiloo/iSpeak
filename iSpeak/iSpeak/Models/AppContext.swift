//
//  AppContext.swift
//  iSpeak
//
//  Model for application context (active app, file type)
//  Used for code-aware text processing
//

import Foundation

/// Application context for text processing
/// Matches Python's context dict from text_processor.py line 109
struct AppContext {
    /// Active application name
    let appName: String

    /// Application bundle identifier
    let bundleID: String

    /// Current file type/extension (if detectable)
    let fileType: String

    /// Check if context indicates a code editor
    /// Python: _is_code_context from lines 137-148
    var isCodeEditor: Bool {
        let codeApps = ["Code", "VS Code", "PyCharm", "Cursor", "Sublime",
                        "IntelliJ", "WebStorm", "Atom", "Xcode", "GoLand",
                        "RubyMine", "Android Studio"]

        return codeApps.contains { appName.contains($0) }
    }

    /// Check if file type indicates code
    /// Python: lines 141-142
    var isCodeFile: Bool {
        let codeExtensions = [".py", ".js", ".ts", ".java", ".cpp", ".go",
                              ".rb", ".php", ".swift", ".kt", ".rs", ".c",
                              ".h", ".m", ".mm", ".jsx", ".tsx", ".vue"]

        return codeExtensions.contains { fileType.hasSuffix($0) }
    }

    /// Check if we're in a code context (editor OR file)
    var isCodeContext: Bool {
        isCodeEditor || isCodeFile
    }

    /// Initialize context
    /// - Parameters:
    ///   - appName: Application name
    ///   - bundleID: Bundle identifier
    ///   - fileType: File extension/type
    init(appName: String, bundleID: String, fileType: String) {
        self.appName = appName
        self.bundleID = bundleID
        self.fileType = fileType
    }

    /// Create unknown context
    static var unknown: AppContext {
        AppContext(appName: "Unknown", bundleID: "", fileType: "")
    }
}
