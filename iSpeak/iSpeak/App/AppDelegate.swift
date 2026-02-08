//
//  AppDelegate.swift
//  iSpeak
//
//  Menu bar app lifecycle management
//

import SwiftUI
import AppKit
import AVFoundation
import ApplicationServices

@MainActor
class AppDelegate: NSObject, NSApplicationDelegate {
    /// Menu bar controller
    var menuBarController: MenuBarController?

    /// Central coordinator for all services
    var coordinator: AppCoordinator?

    /// Timer that polls AXIsProcessTrusted() until Accessibility is granted
    private var accessibilityTimer: Timer?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Hide dock icon and main window - we're a menu bar only app
        NSApp.setActivationPolicy(.accessory)

        print("[AppDelegate] Initializing iSpeak...")

        // Initialize AppCoordinator with all services
        coordinator = AppCoordinator()

        // Initialize menu bar and wire it to coordinator
        menuBarController = MenuBarController()
        menuBarController?.coordinator = coordinator

        // Trigger macOS Accessibility system dialog (one-time prompt).
        // This shows "iSpeak would like to control this computer..."
        // with a button to open System Settings.
        CGEventTapManager.requestPermission()

        // Request microphone permission if not yet determined, then start
        requestMicrophoneAndStart()
    }

    func applicationWillTerminate(_ notification: Notification) {
        print("[AppDelegate] Application terminating...")
        stopAccessibilityPolling()

        Task {
            await coordinator?.stop()
        }

        menuBarController?.cleanup()
    }

    // MARK: - Startup Flow

    /// Request microphone permission (non-blocking), then start coordinator.
    private func requestMicrophoneAndStart() {
        let micStatus = AVCaptureDevice.authorizationStatus(for: .audio)

        if micStatus == .notDetermined {
            AVCaptureDevice.requestAccess(for: .audio) { [weak self] granted in
                DispatchQueue.main.async {
                    print("[AppDelegate] Microphone permission: \(granted ? "granted" : "denied")")
                    self?.startCoordinator()
                }
            }
        } else {
            startCoordinator()
        }
    }

    /// Start the coordinator (never throws). If Accessibility isn't granted,
    /// begin polling until it is.
    private func startCoordinator() {
        Task {
            await coordinator?.start()
            menuBarController?.startProgressUpdates()

            if coordinator?.accessibilityGranted == false {
                print("[AppDelegate] Accessibility not granted, polling...")
                startAccessibilityPolling()
            } else {
                print("[AppDelegate] ✅ iSpeak is ready!")
            }
        }
    }

    // MARK: - Accessibility Polling

    /// Poll AXIsProcessTrusted() every 2 seconds. When it returns true,
    /// automatically start the hotkey listener.
    private func startAccessibilityPolling() {
        stopAccessibilityPolling()

        accessibilityTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            guard let self else { return }

            if AXIsProcessTrusted() {
                print("[AppDelegate] ✅ Accessibility permission granted!")
                self.stopAccessibilityPolling()

                Task { @MainActor in
                    await self.coordinator?.startHotkeyListener()
                    print("[AppDelegate] ✅ iSpeak is ready!")
                }
            }
        }
    }

    /// Stop the accessibility polling timer
    private func stopAccessibilityPolling() {
        accessibilityTimer?.invalidate()
        accessibilityTimer = nil
    }
}
