//
//  AppCoordinator.swift
//  iSpeak
//
//  Central orchestration of all services
//  Implements Python's iSpeakApp from main.py
//

import Foundation
import AppKit
import Observation
import WhisperKit

/// Schedule a @MainActor block via CFRunLoop (bypasses GCD which stops draining
/// after the overlay window is shown). Fire-and-forget — does not block the caller.
nonisolated func scheduleOnMainActor(_ block: @MainActor @Sendable @escaping () -> Void) {
    CFRunLoopPerformBlock(CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue) {
        MainActor.assumeIsolated {
            block()
        }
    }
    CFRunLoopWakeUp(CFRunLoopGetMain())
}

/// Central coordinator for all iSpeak services
/// Matches Python's iSpeakApp behavior from main.py
@Observable
@MainActor
final class AppCoordinator {
    // MARK: - Services

    /// Audio capture service
    private let audioService: AudioCaptureService

    /// Transcription service
    private let transcriptionService: TranscriptionService

    /// Text processing service
    private let textProcessingService: TextProcessingService

    /// Text injection service
    private let textInjectionService: TextInjectionService

    /// Hotkey service
    private let hotkeyService: HotkeyService

    /// Context detection service
    private let contextService: ContextDetectionService

    /// Visual overlay window
    private let overlayWindow: OverlayWindow

    /// Serial queue for audio start/stop to prevent race conditions.
    /// AVAudioEngine.start() pumps the main run loop internally,
    /// causing CFRunLoopPerformBlock re-entrancy. By running audio
    /// operations on a serial background queue, start always completes
    /// before stop begins.
    private nonisolated let audioQueue = DispatchQueue(label: "com.ispeak.audio")

    // MARK: - State

    /// Current language
    var currentLanguage: Language = .english {
        didSet {
            print("[Coordinator] Language changed to: \(currentLanguage.displayName)")
            transcriptionService.setLanguage(currentLanguage.code)
        }
    }

    /// Current model size
    var currentModel: iSpeakModelSize = .small

    /// Model download/load state
    var modelDownloadState: ModelDownloadState = .idle

    /// Whether the model is ready for transcription
    var modelReady: Bool {
        modelDownloadState == .ready
    }

    /// Auto-press Enter after dictation
    var autoEnterEnabled: Bool = false {
        didSet {
            let status = autoEnterEnabled ? "enabled" : "disabled"
            print("[Coordinator] Auto-press Enter \(status)")
        }
    }

    /// Whether Accessibility permission has been granted (hotkey works)
    var accessibilityGranted: Bool = false

    /// Currently processing transcription
    var isProcessing: Bool = false

    /// Currently recording audio
    var isRecording: Bool = false

    /// Menu bar tooltip text
    var statusMessage: String = "iSpeak - Ready"

    // MARK: - Initialization

    /// Initialize with all services
    /// Python: __init__ from lines 22-63
    init(
        audioService: AudioCaptureService,
        transcriptionService: TranscriptionService,
        textProcessingService: TextProcessingService,
        textInjectionService: TextInjectionService,
        hotkeyService: HotkeyService,
        contextService: ContextDetectionService,
        overlayWindow: OverlayWindow
    ) {
        self.audioService = audioService
        self.transcriptionService = transcriptionService
        self.textProcessingService = textProcessingService
        self.textInjectionService = textInjectionService
        self.hotkeyService = hotkeyService
        self.contextService = contextService
        self.overlayWindow = overlayWindow

        print("[Coordinator] ✅ AppCoordinator initialized")
    }

    /// Convenience initializer with default implementations
    convenience init() {
        // Create default service instances
        let audioService = AVAudioCaptureService()
        let transcriptionService = WhisperKitTranscriptionService()
        let textProcessingService = StandardTextProcessingService()
        let textInjectionService = ClipboardTextInjectionService()
        let hotkeyService = CGEventTapHotkeyService()
        let contextService = NSWorkspaceContextDetectionService()
        let overlayWindow = OverlayWindow()

        self.init(
            audioService: audioService,
            transcriptionService: transcriptionService,
            textProcessingService: textProcessingService,
            textInjectionService: textInjectionService,
            hotkeyService: hotkeyService,
            contextService: contextService,
            overlayWindow: overlayWindow
        )
    }

    // MARK: - Lifecycle

    /// Start all services
    /// Python: run() from lines 393-419
    func start() async {
        print("\n" + String(repeating: "=", count: 60))
        print("🚀 iSpeak Started!")
        print(String(repeating: "=", count: 60))
        print("   Hotkey: Right Option (⌥)")
        print("   Language: \(currentLanguage.displayName)")
        print("   Model: \(currentModel.displayName)")
        print(String(repeating: "=", count: 60))
        print("\nSelect a model from the menu bar to download it.")
        print("Then press and hold Right Option to start dictating!\n")

        modelDownloadState = .idle

        // Load vocabulary from Resources
        do {
            try await textProcessingService.loadVocabulary()
            print("[Coordinator] ✅ Vocabulary loaded")
        } catch {
            print("[Coordinator] ⚠️ Failed to load vocabulary: \(error)")
            // Continue without vocabulary - not critical
        }

        // Try to start hotkey listener — if Accessibility not granted, just log it.
        // AppDelegate will poll and call startHotkeyListener() when permission is granted.
        await tryStartHotkeyListener()

        // Auto-load a cached model if available
        await autoLoadCachedModel()
    }

    /// Try to start the hotkey listener. Sets accessibilityGranted accordingly.
    private func tryStartHotkeyListener() async {
        do {
            try await hotkeyService.startListening(
                onPress: { [weak self] in
                    MainActor.assumeIsolated {
                        self?.startDictation()
                    }
                },
                onRelease: { [weak self] in
                    MainActor.assumeIsolated {
                        self?.stopDictation()
                    }
                }
            )
            accessibilityGranted = true
            print("[Coordinator] ✅ Hotkey listener started")
        } catch {
            accessibilityGranted = false
            print("[Coordinator] ⚠️ Hotkey not available (Accessibility permission needed)")
        }
    }

    /// Retry starting the hotkey listener (called by AppDelegate when permission is detected).
    func startHotkeyListener() async {
        guard !hotkeyService.isListening else { return }
        await tryStartHotkeyListener()
    }

    /// Auto-load a previously downloaded model on startup.
    /// Prefers .small (recommended), falls back to any cached model.
    private func autoLoadCachedModel() async {
        guard let whisperService = transcriptionService as? WhisperKitTranscriptionService else {
            statusMessage = "iSpeak - Select a model to get started"
            return
        }

        // Prefer small (recommended), then check others
        let preferredOrder: [iSpeakModelSize] = [.small] + iSpeakModelSize.allCases.filter { $0 != .small }

        for size in preferredOrder {
            if await whisperService.isModelCached(size) {
                print("[Coordinator] Found cached model: \(size.rawValue), loading...")
                await performModelDownload(size)
                return
            }
        }

        print("[Coordinator] No cached models found")
        statusMessage = "iSpeak - Select a model to get started"
    }

    /// Download and load a WhisperKit model with progress tracking
    func downloadAndLoadModel(_ size: iSpeakModelSize) {
        guard case .downloading = modelDownloadState else {
            // Allow starting download unless already downloading
            Task {
                await performModelDownload(size)
            }
            return
        }
        print("[Coordinator] ⚠️ Already downloading a model, please wait...")
    }

    private func performModelDownload(_ size: iSpeakModelSize) async {
        // Cast to access WhisperKit-specific methods
        guard let whisperService = transcriptionService as? WhisperKitTranscriptionService else {
            print("[Coordinator] ❌ Transcription service does not support model download")
            modelDownloadState = .error("Unsupported transcription service")
            return
        }

        currentModel = size
        modelDownloadState = .downloading(progress: 0)
        statusMessage = "Downloading \(size.displayName)..."
        print("[Coordinator] ⬇️  Starting download of model: \(size.rawValue)")

        do {
            let modelsDir = await whisperService.getModelsDirectory()

            // Download with progress callback
            _ = try await WhisperKit.download(
                variant: size.rawValue,
                downloadBase: modelsDir
            ) { [weak self] progress in
                let fraction = progress.fractionCompleted
                scheduleOnMainActor { [weak self] in
                    self?.modelDownloadState = .downloading(progress: fraction)
                    let pct = Int(fraction * 100)
                    self?.statusMessage = "Downloading \(size.displayName)... \(pct)%"
                }
            }

            print("[Coordinator] ✅ Download complete, loading model...")
            modelDownloadState = .loading
            statusMessage = "Loading model..."

            // Load the model into memory
            try await whisperService.preloadModel(size)

            // Warm up CoreML — first inference compiles the neural engine graph
            statusMessage = "Warming up model..."
            await whisperService.warmUpModel()

            modelDownloadState = .ready
            statusMessage = "iSpeak - Ready"
            print("[Coordinator] ✅ Model \(size.rawValue) ready!")

        } catch {
            print("[Coordinator] ❌ Model download/load failed: \(error)")
            modelDownloadState = .error(error.localizedDescription)
            statusMessage = "Model failed - tap to retry"
        }
    }

    /// Stop all services
    /// Python: quit() from lines 421-441
    func stop() async {
        print("\n[Coordinator] Shutting down iSpeak...")

        // Stop hotkey listener
        hotkeyService.stopListening()
        print("[Coordinator] Hotkey listener stopped")

        // Cleanup audio
        await audioService.cleanup()
        print("[Coordinator] Audio cleaned up")

        print("[Coordinator] Goodbye!")
    }

    // MARK: - Dictation Workflow

    /// Start dictation (hotkey pressed)
    /// Python: start_dictation from lines 65-75
    private func startDictation() {
        guard modelReady else {
            print("[Coordinator] ⚠️ No model loaded. Please select a model from the menu bar first.")
            return
        }

        guard !isProcessing else {
            print("[Coordinator] ⚠️ Already processing, ignoring hotkey")
            return
        }

        guard !isRecording else {
            print("[Coordinator] ⚠️ Already recording, ignoring press")
            return
        }

        print("\n[Coordinator] 🎤 Recording starting...")
        isRecording = true
        statusMessage = "🎤 Recording..."

        // Show overlay immediately
        overlayWindow.show(.listening)

        // Start audio engine on the serial audio queue.
        // We CANNOT call startRecording() synchronously on MainActor because
        // AVAudioEngine.start() internally pumps the run loop, causing
        // CFRunLoopPerformBlock re-entrancy (release fires during press).
        // The serial audioQueue ensures stop always waits for start to finish.
        let audioSvc = audioService
        audioQueue.async {
            do {
                try audioSvc.startRecording()
                print("[Coordinator] ✅ Audio engine running")
            } catch {
                print("[Coordinator] ❌ Failed to start recording: \(error)")
                scheduleOnMainActor { [weak self] in
                    self?.statusMessage = "Recording failed - Ready"
                    self?.isRecording = false
                    self?.overlayWindow.hide()
                }
            }
        }
    }

    /// Stop dictation (hotkey released)
    /// Python: stop_dictation from lines 76-117
    private func stopDictation() {
        guard isRecording else {
            print("[Coordinator] ⚠️ Not recording, ignoring release")
            return
        }

        guard !isProcessing else {
            print("[Coordinator] ⚠️ Already processing, please wait...")
            return
        }

        print("[Coordinator] ⏸️  Recording stopped, transcribing...")
        isRecording = false
        isProcessing = true
        statusMessage = "Transcribing..."

        // Show overlay in processing state
        overlayWindow.show(.processing)

        // Capture @MainActor values before entering the detached task.
        // The detached task cannot hop to MainActor (GCD is blocked),
        // so we pass everything it needs as local values.
        let languageCode = currentLanguage.code
        let shouldAutoEnter = autoEnterEnabled
        let audioSvc = audioService
        let transcriptionSvc = transcriptionService
        let textProcessingSvc = textProcessingService
        let textInjectionSvc = textInjectionService
        let contextSvc = contextService

        // Stop recording and process entirely off MainActor.
        // audioQueue.sync {} acts as a barrier — blocks until startRecording
        // completes on the serial audio queue, preventing the race condition.
        let audioQueue = self.audioQueue
        Task.detached {
            audioQueue.sync {}  // Barrier: wait for startRecording to finish
            let startTime = Date()

            // Safety: always reset isProcessing and hide overlay when done
            defer {
                scheduleOnMainActor { [weak self] in
                    guard let self else { return }
                    if self.isProcessing {
                        self.isProcessing = false
                        self.overlayWindow.hide()
                    }
                }
            }

            // Get audio buffer
            let audioBuffer = audioSvc.stopRecording()

            // Check minimum duration (0.3 seconds = 4800 samples at 16kHz)
            let minimumSamples = Int(0.3 * audioBuffer.sampleRate)
            guard audioBuffer.samples.count >= minimumSamples else {
                print("[Coordinator] ❌ Recording too short (\(audioBuffer.duration)s), ignoring")
                print("[Coordinator] 💡 Hold the key longer to record")
                return  // defer handles UI reset
            }

            print("[Coordinator] Audio captured: \(audioBuffer.duration)s, \(audioBuffer.samples.count) samples")

            // Check if audio is silent
            if audioBuffer.isSilent {
                print("[Coordinator] ⚠️ Audio appears to be silent (max level: \(audioBuffer.maxLevel))")
                print("[Coordinator] 💡 Check microphone permissions and input device")
            }

            do {
                // 1. Transcribe audio
                print("[Coordinator] Transcribing \(audioBuffer.samples.count) samples...")
                let result = try await transcriptionSvc.transcribe(
                    audio: audioBuffer.samples,
                    language: languageCode
                )

                let transcribeTime = Date().timeIntervalSince(startTime)
                print("[Coordinator] Transcription took \(String(format: "%.2f", transcribeTime))s")
                print("[Coordinator] Detected language: \(result.language.uppercased()), Confidence: \(String(format: "%.2f", result.confidence))")

                if result.isLowConfidence {
                    print("[Coordinator] ⚠️ Low confidence (\(String(format: "%.2f", result.confidence)))")
                }

                guard !result.text.isEmpty else {
                    print("[Coordinator] No speech detected")
                    return  // defer handles UI reset
                }

                print("[Coordinator] Transcribed: '\(result.text)'")

                // 2. Get context for code-aware formatting
                let context = contextSvc.getCurrentContext()
                print("[Coordinator] Context: \(context.appName)")

                // 3. Process text
                let processedText = await textProcessingSvc.process(result.text, context: context)
                print("[Coordinator] Processed: '\(processedText)'")

                let totalTime = Date().timeIntervalSince(startTime)
                print("[Coordinator] Total time: \(String(format: "%.2f", totalTime))s")

                // 4. Inject text (with delay to avoid hotkey interference)
                try await Task.sleep(nanoseconds: 100_000_000)  // 100ms delay

                try await textInjectionSvc.inject(processedText)
                print("[Coordinator] ✅ Text inserted: '\(processedText.prefix(50))\(processedText.count > 50 ? "..." : "")'")

                // Auto-press Enter if enabled
                if shouldAutoEnter {
                    print("[Coordinator] Auto-pressing Enter...")
                    try await Task.sleep(nanoseconds: 100_000_000)
                    try await textInjectionSvc.pressKey(.enter)
                }

                // Mark complete
                scheduleOnMainActor { [weak self] in
                    self?.statusMessage = "Ready"
                    self?.isProcessing = false
                    self?.overlayWindow.hide()
                }

            } catch {
                print("[Coordinator] ❌ Error during transcription: \(error)")
                // defer handles UI reset
            }
        }
    }
}

// MARK: - Supporting Types

/// Language enumeration
/// Python: current_language from line 38
enum Language: String, CaseIterable {
    case english = "en"
    case romanian = "ro"

    var displayName: String {
        switch self {
        case .english: return "English"
        case .romanian: return "Romanian"
        }
    }

    var code: String {
        return rawValue
    }
}

/// State of model download/loading
enum ModelDownloadState: Equatable {
    case idle
    case downloading(progress: Double)
    case loading
    case ready
    case error(String)
}
