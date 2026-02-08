//
//  HotkeyConfiguration.swift
//  iSpeak
//
//  Configuration for global hotkeys
//  Matches Python's hotkey settings from hotkey_controller.py
//

import Foundation
import Carbon

/// Hotkey configuration
struct HotkeyConfiguration {
    /// Virtual key code for the hotkey
    let keyCode: CGKeyCode

    /// Required modifier flags (empty for Right Option alone)
    let modifiers: CGEventFlags

    /// Human-readable name
    let displayName: String

    /// Default configuration: Right Option key
    /// Python: self.hotkey = keyboard.Key.alt_r from line 21
    static let defaultRightOption = HotkeyConfiguration(
        keyCode: CGKeyCode(kVK_RightOption),  // 0x3D (61 decimal)
        modifiers: [],  // No additional modifiers needed
        displayName: "Right Option"
    )

    /// Alternative: Left Option key
    static let leftOption = HotkeyConfiguration(
        keyCode: CGKeyCode(kVK_Option),
        modifiers: [],
        displayName: "Left Option"
    )

    /// Alternative: Right Command key
    static let rightCommand = HotkeyConfiguration(
        keyCode: CGKeyCode(kVK_RightCommand),
        modifiers: [],
        displayName: "Right Command"
    )
}
