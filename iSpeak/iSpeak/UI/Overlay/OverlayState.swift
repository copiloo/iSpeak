//
//  OverlayState.swift
//  iSpeak
//
//  Overlay display states
//  Implements Python's OverlayWidget states from overlay_widget.py
//

import Foundation

/// Overlay display state
/// Python: show_listening, show_processing, hide_overlay from lines 195-235
enum OverlayState: Equatable {
    /// Hidden (not visible)
    case hidden

    /// Listening state with animated waveform
    /// Python: show_listening from lines 195-205
    case listening

    /// Processing state with bouncing dots
    /// Python: show_processing from lines 207-217
    case processing

    /// Streaming state with live text (future enhancement)
    /// Python: show_streaming from lines 219-235
    case streaming(text: String)

    var isVisible: Bool {
        self != .hidden
    }
}
