//
//  iSpeakApp.swift
//  iSpeak
//
//  Created by Ionut Coroiu on 2/6/26.
//
//  Main app entry point for menu bar application
//

import SwiftUI

@main
struct iSpeakApp: App {
    // Connect to AppDelegate for menu bar management
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        // Empty scene - we're a menu bar only app (LSUIElement = true)
        // The menu bar is managed by AppDelegate
        Settings {
            EmptyView()
        }
    }
}
