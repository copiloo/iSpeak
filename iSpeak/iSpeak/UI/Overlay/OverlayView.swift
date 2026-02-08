//
//  OverlayView.swift
//  iSpeak
//
//  Custom view with animated visual feedback
//  Uses Core Animation (render server) — zero main thread work.
//

import AppKit
import QuartzCore

/// Custom view with animated waveform and bouncing dots
/// All animations use CABasicAnimation/CAKeyframeAnimation which run
/// on the Core Animation render server, never touching the main queue.
final class OverlayView: NSView {
    // MARK: - Properties

    /// Current state
    private var state: OverlayState = .hidden

    /// Waveform bars (7 bars for listening state)
    private var waveformBars: [CAShapeLayer] = []

    /// Bouncing dots (3 dots for processing state)
    private var bouncingDots: [CAShapeLayer] = []

    /// Text layer for streaming state
    private var textLayer: CATextLayer?

    // Animation constants
    private let barCount = 7
    private let barWidth: CGFloat = 3
    private let barSpacing: CGFloat = 3
    private let barMinHeight: CGFloat = 8
    private let barMaxHeight: CGFloat = 15

    private let dotCount = 3
    private let dotRadius: CGFloat = 2
    private let dotSpacing: CGFloat = 10

    // Colors
    private let listeningColor = NSColor(red: 0, green: 0.784, blue: 1.0, alpha: 1.0)  // Cyan
    private let processingColor = NSColor(white: 1.0, alpha: 1.0) // White
    private let backgroundColor = NSColor(white: 0.118, alpha: 0.86)

    // MARK: - Initialization

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        setupView()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupView()
    }

    // MARK: - Setup

    private func setupView() {
        wantsLayer = true

        guard let layer = layer else { return }

        // Background
        layer.backgroundColor = backgroundColor.cgColor

        // Create waveform bars
        createWaveformBars()

        // Create bouncing dots
        createBouncingDots()

        // Create text layer
        createTextLayer()

        // Hide all by default
        hideAllLayers()
    }

    /// Create waveform bars — each bar is a CAShapeLayer at a fixed X position.
    /// The bar's bounds.size.height is animated; anchorPoint is (0.5, 0.5)
    /// so it grows symmetrically from center.
    private func createWaveformBars() {
        guard let layer = layer else { return }

        let totalWidth = CGFloat(barCount) * (barWidth + barSpacing) - barSpacing
        let startX = (bounds.width - totalWidth) / 2

        for i in 0..<barCount {
            let barLayer = CAShapeLayer()
            barLayer.backgroundColor = listeningColor.cgColor

            let x = startX + CGFloat(i) * (barWidth + barSpacing)

            // Position bar centered vertically, at its X
            barLayer.anchorPoint = CGPoint(x: 0.5, y: 0.5)
            barLayer.bounds = CGRect(x: 0, y: 0, width: barWidth, height: barMinHeight)
            barLayer.position = CGPoint(x: x + barWidth / 2, y: bounds.midY)
            barLayer.cornerRadius = barWidth / 2

            // Gradient alpha: center bars brighter, edge bars dimmer (Python lines 213-216)
            let distanceFromCenter = abs(CGFloat(i) - CGFloat(barCount - 1) / 2) / (CGFloat(barCount - 1) / 2)
            barLayer.opacity = Float(1.0 - 0.3 * distanceFromCenter)

            layer.addSublayer(barLayer)
            waveformBars.append(barLayer)
        }
    }

    /// Create bouncing dots — each dot is a CAShapeLayer with a circular path.
    /// Position.y is animated for the bounce effect.
    private func createBouncingDots() {
        guard let layer = layer else { return }

        let totalWidth = CGFloat(dotCount) * (dotRadius * 2 + dotSpacing) - dotSpacing
        let startX = (bounds.width - totalWidth) / 2

        for i in 0..<dotCount {
            let dotLayer = CAShapeLayer()
            dotLayer.fillColor = processingColor.cgColor

            let x = startX + CGFloat(i) * (dotRadius * 2 + dotSpacing) + dotRadius

            // Circle path in local coordinates
            let circlePath = CGPath(
                ellipseIn: CGRect(x: -dotRadius, y: -dotRadius, width: dotRadius * 2, height: dotRadius * 2),
                transform: nil
            )
            dotLayer.path = circlePath
            dotLayer.position = CGPoint(x: x, y: bounds.midY)

            layer.addSublayer(dotLayer)
            bouncingDots.append(dotLayer)
        }
    }

    /// Create text layer for streaming state
    private func createTextLayer() {
        guard let layer = layer else { return }

        let tl = CATextLayer()
        tl.frame = bounds.insetBy(dx: 10, dy: 10)
        tl.fontSize = 14
        tl.foregroundColor = NSColor.white.cgColor
        tl.alignmentMode = .center
        tl.contentsScale = NSScreen.main?.backingScaleFactor ?? 2.0

        layer.addSublayer(tl)
        self.textLayer = tl
    }

    /// Hide all animation layers
    private func hideAllLayers() {
        waveformBars.forEach { $0.isHidden = true }
        bouncingDots.forEach { $0.isHidden = true }
        textLayer?.isHidden = true
    }

    // MARK: - State Management

    /// Update overlay state
    func setState(_ newState: OverlayState) {
        state = newState

        // Stop any running animations and hide all
        stopAnimations()
        hideAllLayers()

        switch newState {
        case .hidden:
            break

        case .listening:
            waveformBars.forEach { $0.isHidden = false }
            startWaveformAnimations()

        case .processing:
            bouncingDots.forEach { $0.isHidden = false }
            startBouncingDotAnimations()

        case .streaming(let text):
            textLayer?.string = text
            textLayer?.isHidden = false
            waveformBars.forEach { $0.isHidden = false }
            startWaveformAnimations()
        }
    }

    // MARK: - Core Animation Animations

    /// Animate waveform bars using CABasicAnimation on bounds.size.height.
    /// Each bar gets a different timeOffset to create the wave effect.
    /// Runs entirely on the Core Animation render server — zero main thread work.
    private func startWaveformAnimations() {
        print("[Overlay] startAnimations called (waveform)")

        let duration: CFTimeInterval = 0.5  // Period of one full wave cycle
        let phaseStep: CFTimeInterval = 0.07  // Time offset between adjacent bars

        for (index, barLayer) in waveformBars.enumerated() {
            // Reset bounds to min height
            barLayer.bounds = CGRect(x: 0, y: 0, width: barWidth, height: barMinHeight)

            // Animate bounds.size.height from min to max
            let anim = CABasicAnimation(keyPath: "bounds.size.height")
            anim.fromValue = barMinHeight
            anim.toValue = barMaxHeight
            anim.duration = duration
            anim.autoreverses = true
            anim.repeatCount = .infinity
            anim.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            // Stagger each bar with a time offset for the wave effect
            anim.timeOffset = Double(index) * phaseStep

            barLayer.add(anim, forKey: "waveform")
        }
    }

    /// Animate bouncing dots using CAKeyframeAnimation on position.y.
    /// Each dot gets a different timeOffset to create the sequential bounce.
    /// Runs entirely on the Core Animation render server — zero main thread work.
    private func startBouncingDotAnimations() {
        print("[Overlay] startAnimations called (bouncing dots)")

        let bounceHeight: CGFloat = 4
        let baseY = bounds.midY
        let duration: CFTimeInterval = 0.6
        let phaseStep: CFTimeInterval = 0.2  // Stagger between dots

        for (index, dotLayer) in bouncingDots.enumerated() {
            // Reset position
            dotLayer.position = CGPoint(x: dotLayer.position.x, y: baseY)

            let anim = CAKeyframeAnimation(keyPath: "position.y")
            anim.values = [
                baseY,
                baseY + bounceHeight,
                baseY
            ]
            anim.keyTimes = [0, 0.5, 1.0]
            anim.duration = duration
            anim.repeatCount = .infinity
            anim.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            anim.timeOffset = Double(index) * phaseStep

            dotLayer.add(anim, forKey: "bounce")
        }
    }

    /// Stop all running animations
    func stopAnimations() {
        print("[Overlay] stopAnimations called")

        for barLayer in waveformBars {
            barLayer.removeAllAnimations()
            // Reset to min height
            barLayer.bounds = CGRect(x: 0, y: 0, width: barWidth, height: barMinHeight)
        }

        for dotLayer in bouncingDots {
            dotLayer.removeAllAnimations()
        }
    }

    // MARK: - Cleanup

    deinit {
        stopAnimations()
    }
}
