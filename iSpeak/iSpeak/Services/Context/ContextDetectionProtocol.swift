//
//  ContextDetectionProtocol.swift
//  iSpeak
//
//  Protocol for context detection service
//  Enables testing with mock implementations
//

import Foundation

/// Protocol for context detection service
protocol ContextDetectionService {
    /// Get current application context
    /// - Returns: AppContext with app name, bundle ID, and file type
    /// Python: get_current_context from lines 21-50
    func getCurrentContext() -> AppContext
}
