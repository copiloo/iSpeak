//
//  AppDelegate.swift
//  iSpeak
//
//  Menu bar app lifecycle management
//

import SwiftUI
import AppKit

class AppDelegate: NSObject, NSApplicationDelegate {
    var menuBarController: MenuBarController?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Hide dock icon and main window - we're a menu bar only app
        NSApp.setActivationPolicy(.accessory)

        // Initialize menu bar
        menuBarController = MenuBarController()

        // Request necessary permissions on first launch
        requestPermissions()
    }

    func applicationWillTerminate(_ notification: Notification) {
        // Cleanup resources
        menuBarController?.cleanup()
    }

    private func requestPermissions() {
        // Microphone permission will be requested when first used
        // Input monitoring permission will be requested by CGEventTap
        // This method can be expanded to show permission guidance
    }
}
