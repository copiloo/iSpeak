# iSpeak Swift - Testing Guide

Comprehensive testing checklist for validating iSpeak functionality before distribution.

## Environment Setup

- [ ] **macOS Version:** 14.0+ (Sonoma or later)
- [ ] **Xcode Version:** 15.0+
- [ ] **Hardware:** Mac with Apple Silicon (M1/M2/M3) recommended for WhisperKit
- [ ] **Microphone:** Built-in or external microphone connected
- [ ] **Input Device:** Verify audio input working in System Settings

---

## Phase 1: Initial Setup & Permissions

### First Launch
- [ ] Build and run app from Xcode
- [ ] App launches without crashes
- [ ] App icon appears in menu bar (microphone icon)
- [ ] No Dock icon visible (accessory app mode)
- [ ] Console shows: "✅ iSpeak is ready!"

### Permissions
- [ ] **Microphone Permission:**
  - [ ] First audio capture attempt prompts for permission
  - [ ] Grant permission → recording works
  - [ ] Deny permission → clear error message shown
  - [ ] Settings → Permissions tab shows "Open Settings" button

- [ ] **Input Monitoring Permission:**
  - [ ] First hotkey attempt prompts for permission (System Settings)
  - [ ] Grant permission → hotkey works
  - [ ] Deny permission → error message with instructions

---

## Phase 2: Audio Capture

### Basic Recording
- [ ] Press and hold Right Option (⌥)
- [ ] Overlay appears at bottom-center of screen
- [ ] **Listening state:** Blue waveform animates (7 bars)
- [ ] Speak clearly for 2-3 seconds
- [ ] Release Right Option
- [ ] **Processing state:** Orange dots bounce (3 dots)
- [ ] Overlay disappears after processing

### Edge Cases
- [ ] **Short recording (< 0.3s):**
  - [ ] Hold Right Option briefly, release immediately
  - [ ] Console shows: "Recording too short, ignoring"
  - [ ] Console shows: "Hold the key longer to record"
  - [ ] No transcription occurs

- [ ] **Silent recording:**
  - [ ] Press Right Option but don't speak
  - [ ] Console warns: "Audio appears to be silent"
  - [ ] Console suggests: "Check microphone permissions and input device"
  - [ ] Transcription may return empty or background noise

- [ ] **Bluetooth device handling:**
  - [ ] Connect Bluetooth headphones/earbuds
  - [ ] First recording after connection works
  - [ ] Audio engine reinitializes successfully
  - [ ] No crashes or audio glitches

- [ ] **Device switching:**
  - [ ] Switch from built-in mic to USB mic (or vice versa)
  - [ ] Next recording uses new device
  - [ ] No error messages

### Audio Buffer
- [ ] **Long recording (8-10 seconds):**
  - [ ] Hold Right Option for 10+ seconds
  - [ ] Audio buffer caps at ~10 seconds
  - [ ] Transcription processes full buffer
  - [ ] No memory issues or crashes

---

## Phase 3: Transcription

### WhisperKit Integration
- [ ] **First transcription:**
  - [ ] Model downloads automatically (if not cached)
  - [ ] Console shows download progress
  - [ ] Model loads successfully
  - [ ] Transcription completes

- [ ] **Subsequent transcriptions:**
  - [ ] Model loads from cache (faster)
  - [ ] No re-download
  - [ ] Consistent transcription quality

### Accuracy Tests

**English (default language):**
- [ ] Say: "Hello world this is a test"
  - Expected: "Hello world this is a test" (or close)
- [ ] Say: "The quick brown fox jumps over the lazy dog"
  - Expected: Accurate transcription
- [ ] Say: "Open brackets close brackets"
  - Expected: Code pattern detected if in code editor

**Romanian (switch language in menu):**
- [ ] Switch to Romanian in menu bar
- [ ] Say: "Bună ziua funcție pentru variabilă"
  - Expected: "Bună ziua funcție pentru variabilă" (with diacritics)
- [ ] Console shows: "Language changed to: Romanian"

### Confidence Warnings
- [ ] **Low confidence transcription:**
  - [ ] Speak unclearly or with background noise
  - [ ] If confidence < 0.5, console shows warning:
    - "⚠️ Low confidence transcription (0.XX)"
  - [ ] Text still injected but user warned

---

## Phase 4: Text Processing

### Vocabulary Substitution
- [ ] Say: "git hub"
  - Expected: "GitHub" (from vocabulary.json)
- [ ] Say: "java script"
  - Expected: "JavaScript"
- [ ] Say: "react jay ess"
  - Expected: "ReactJS"

### Romanian Diacritics (with Romanian language selected)
- [ ] Say: "functie" → Expected: "funcție"
- [ ] Say: "variabila" → Expected: "variabilă"
- [ ] Say: "clasa" → Expected: "clasă"
- [ ] Say: "fisier" → Expected: "fișier"
- [ ] Say: "conditie" → Expected: "condiție"

### Code-Aware Formatting

**In Code Editor (VS Code, Xcode, Cursor):**
- [ ] Open VS Code or Xcode
- [ ] Focus on editor
- [ ] Say: "new line"
  - Expected: "\n" inserted
- [ ] Say: "tab"
  - Expected: "\t" inserted
- [ ] Say: "equals"
  - Expected: " = " inserted
- [ ] Say: "open brace"
  - Expected: " {" inserted
- [ ] Say: "arrow"
  - Expected: " => " inserted

**In Non-Code App (TextEdit, Notes):**
- [ ] Open TextEdit
- [ ] Say: "new line"
  - Expected: Literal "new line" text (not "\n")
- [ ] Code formatting NOT applied

### Whitespace Cleanup
- [ ] Say: "hello    world" (multiple spaces)
  - Expected: "hello world" (single space)
- [ ] Say: "test , another" (space before comma)
  - Expected: "test, another" (no space before comma)

---

## Phase 5: Text Injection

### Basic Injection
- [ ] Open TextEdit
- [ ] Click in empty document
- [ ] Hold Right Option, say "Hello world", release
- [ ] Text appears in TextEdit
- [ ] Cursor positioned after text

### Clipboard Preservation
- [ ] Copy some text to clipboard (Cmd+C)
- [ ] Perform voice dictation
- [ ] Paste clipboard (Cmd+V)
- [ ] Original copied text pastes correctly
- [ ] Clipboard NOT overwritten by dictation

### Auto-Press Enter
- [ ] **Without auto-enter (default):**
  - [ ] Open Terminal
  - [ ] Dictate: "echo hello"
  - [ ] Text inserted but not executed
  - [ ] Press Enter manually → command runs

- [ ] **With auto-enter enabled:**
  - [ ] Menu bar → Toggle "Auto-press Enter"
  - [ ] Dictate: "echo hello"
  - [ ] Text inserted AND Enter pressed automatically
  - [ ] Command executes immediately

### Multiple Applications
Test text injection in various apps:
- [ ] **TextEdit:** Basic text editor
- [ ] **Notes:** Apple Notes app
- [ ] **VS Code:** Code editor
- [ ] **Terminal:** Command line
- [ ] **Chrome/Safari:** Browser text field
- [ ] **Slack/Discord:** Chat app
- [ ] **Mail:** Email compose window

---

## Phase 6: Context Detection

### Application Detection
- [ ] **Code Editor Detected:**
  - [ ] Open VS Code
  - [ ] Console shows: "Context: Code" (or similar)
  - [ ] Console shows: "Code context detected: editor=true"

- [ ] **Non-Code App:**
  - [ ] Open TextEdit
  - [ ] Console shows: "Context: TextEdit"
  - [ ] Code formatting NOT applied

### File Type Detection
- [ ] **Xcode (Swift file):**
  - [ ] Console shows: "file=.swift"
- [ ] **PyCharm (Python file):**
  - [ ] Console shows: "file=.py"
- [ ] **Generic editor:**
  - [ ] VS Code shows: "file=" (empty, multi-language)

---

## Phase 7: Visual Overlay

### Listening State
- [ ] Press Right Option
- [ ] Overlay appears at bottom-center
- [ ] **Waveform animation:**
  - [ ] 7 blue bars
  - [ ] Smooth sine wave motion (60fps)
  - [ ] Animation continues while recording
- [ ] Overlay has rounded corners (15px)
- [ ] Semi-transparent dark background

### Processing State
- [ ] Release Right Option
- [ ] Overlay transitions to processing
- [ ] **Bouncing dots animation:**
  - [ ] 3 orange dots
  - [ ] Smooth bouncing with phase offset
  - [ ] Animation at 60fps
- [ ] Overlay disappears after transcription

### Multi-Monitor Support
- [ ] **Multiple displays:**
  - [ ] Overlay appears on main screen
  - [ ] Positioned correctly at bottom-center
  - [ ] No positioning glitches

### Focus Behavior
- [ ] Overlay NEVER steals focus
- [ ] Clicking other apps doesn't hide overlay
- [ ] Overlay always on top (floating level)

---

## Phase 8: Settings Window

### Opening Settings
- [ ] Click menu bar icon
- [ ] Click "Settings..." (Cmd+,)
- [ ] Settings window opens
- [ ] Window properly titled "iSpeak Settings"

### General Tab
- [ ] **Language picker:**
  - [ ] Shows English and Romanian
  - [ ] Current selection highlighted
  - [ ] Change language → updates immediately
  - [ ] Console confirms: "Language changed to: X"

- [ ] **Model picker:**
  - [ ] Shows all 6 model sizes
  - [ ] "Small (recommended)" selected by default
  - [ ] Change model → triggers model switch
  - [ ] Console shows model loading progress

- [ ] **Models directory:**
  - [ ] Path displayed correctly
  - [ ] Click "Open" → Finder opens
  - [ ] Correct directory shown

### Keyboard Tab
- [ ] Hotkey display shows: "Right Option (⌥)"
- [ ] Auto-press Enter toggle:
  - [ ] Toggle ON → next dictation auto-presses Enter
  - [ ] Toggle OFF → manual Enter required

### Permissions Tab
- [ ] **Microphone section:**
  - [ ] Shows icon + description
  - [ ] "Open Settings" button works
  - [ ] Opens System Settings → Privacy → Microphone

- [ ] **Input Monitoring section:**
  - [ ] Shows icon + description
  - [ ] "Open Settings" button works
  - [ ] Opens System Settings → Privacy → Accessibility

### About Tab
- [ ] App icon displayed (or system mic icon)
- [ ] App name: "iSpeak"
- [ ] Version number correct
- [ ] Build number correct
- [ ] Feature highlights visible:
  - [ ] 🔒 Private
  - [ ] ⚡ Fast
  - [ ] 📝 Code-Aware

### Window Behavior
- [ ] **Position persistence:**
  - [ ] Move window to new position
  - [ ] Close window
  - [ ] Reopen → window at same position

- [ ] **Singleton pattern:**
  - [ ] Open Settings twice
  - [ ] Second click brings window to front
  - [ ] Only one settings window exists

---

## Phase 9: Menu Bar Integration

### Menu Items
- [ ] Click menu bar icon
- [ ] **Language section:**
  - [ ] Shows "Language"
  - [ ] English/Romanian items
  - [ ] Current language has checkmark
  - [ ] Click switches language

- [ ] **Model section:**
  - [ ] Shows "Model"
  - [ ] 6 model size items
  - [ ] Current model has checkmark
  - [ ] Click switches model

- [ ] **Auto-press Enter:**
  - [ ] Toggle item present
  - [ ] Checkmark shows current state
  - [ ] Click toggles state

- [ ] **Settings... (Cmd+,):**
  - [ ] Opens settings window

- [ ] **Quit iSpeak (Cmd+Q):**
  - [ ] Quits app cleanly
  - [ ] No crashes or errors

---

## Phase 10: Model Management

### Model Downloading
- [ ] **First use of new model:**
  - [ ] Switch to "medium" model (if not downloaded)
  - [ ] Console shows: "Model not loaded, loading medium..."
  - [ ] Progress updates shown
  - [ ] Model downloads successfully
  - [ ] Cached in Application Support

- [ ] **Subsequent use:**
  - [ ] Model loads from cache
  - [ ] Fast loading (no download)

### Model Switching
- [ ] **During active recording:**
  - [ ] Start recording
  - [ ] Try to switch model via menu
  - [ ] Operation blocked (processing in progress)

- [ ] **When idle:**
  - [ ] Switch model via menu
  - [ ] Next transcription uses new model
  - [ ] Quality/speed changes as expected

---

## Phase 11: Error Handling & Edge Cases

### Permission Errors
- [ ] **Microphone denied:**
  - [ ] Deny microphone permission
  - [ ] Try to record
  - [ ] Clear error alert shown
  - [ ] "Open System Settings" button works

- [ ] **Input monitoring denied:**
  - [ ] Deny input monitoring
  - [ ] Try to use hotkey
  - [ ] Error message shown
  - [ ] Instructions provided

### Network Errors (Model Download)
- [ ] **No internet connection:**
  - [ ] Disconnect from network
  - [ ] Switch to un-downloaded model
  - [ ] Download fails gracefully
  - [ ] Error message shown
  - [ ] App doesn't crash

### Memory & Performance
- [ ] **Rapid hotkey presses:**
  - [ ] Press/release Right Option rapidly
  - [ ] App handles correctly
  - [ ] No memory leaks
  - [ ] No crashes

- [ ] **Long-running session:**
  - [ ] Perform 20+ transcriptions
  - [ ] Monitor memory usage (Activity Monitor)
  - [ ] Memory stays stable
  - [ ] No memory leaks

---

## Phase 12: Integration Testing

### End-to-End Workflow
- [ ] **Complete cycle:**
  1. Launch app
  2. Grant permissions
  3. Press Right Option
  4. See listening overlay
  5. Speak test phrase
  6. Release Right Option
  7. See processing overlay
  8. Text injected correctly
  9. Overlay disappears
  10. Ready for next recording

- [ ] **Multiple recordings:**
  - [ ] Perform 5 recordings in a row
  - [ ] All succeed without errors
  - [ ] Overlay animations smooth
  - [ ] Text injection consistent

### Cross-Feature Testing
- [ ] **Romanian + Code Editor + Auto-Enter:**
  - [ ] Switch to Romanian
  - [ ] Open VS Code
  - [ ] Enable auto-enter
  - [ ] Say: "functie new line variabila"
  - [ ] Expected: "funcție\nvariabilă" + Enter pressed

- [ ] **Model switching + Transcription:**
  - [ ] Switch from small → large
  - [ ] Perform transcription
  - [ ] Verify improved quality

---

## Phase 13: Build & Distribution

### Debug Build
- [ ] Build succeeds in Xcode (Debug configuration)
- [ ] All warnings addressed (or documented)
- [ ] No build errors
- [ ] App runs from Xcode

### Release Build
- [ ] Build succeeds in Xcode (Release configuration)
- [ ] Code signing configured
- [ ] Entitlements correct:
  - [ ] `com.apple.security.microphone`
  - [ ] `com.apple.security.personal-information.input-monitoring`
  - [ ] `com.apple.security.automation.apple-events`
  - [ ] App Sandbox enabled
- [ ] Archive builds successfully

### Code Signing & Notarization
- [ ] Developer ID certificate configured
- [ ] App signed with Developer ID
- [ ] Hardened runtime enabled
- [ ] Notarization submitted to Apple
- [ ] Notarization succeeds
- [ ] Staple ticket to app

### Distribution
- [ ] **DMG creation:**
  - [ ] Create DMG installer
  - [ ] DMG opens correctly
  - [ ] Drag-to-Applications works
  - [ ] App launches from /Applications

- [ ] **Gatekeeper:**
  - [ ] Fresh Mac test (or `xattr -cr iSpeak.app`)
  - [ ] Double-click app
  - [ ] No "unidentified developer" warning
  - [ ] App launches normally

---

## Performance Benchmarks

Target performance (compared to Python version):

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| **Audio latency** | < 50ms | ___ ms | ☐ |
| **Transcription (small model, 5s audio)** | 2-3s | ___ s | ☐ |
| **Text injection** | < 100ms | ___ ms | ☐ |
| **Total end-to-end** | < 5s | ___ s | ☐ |
| **Memory usage (idle)** | < 100MB | ___ MB | ☐ |
| **Memory usage (processing)** | < 500MB | ___ MB | ☐ |
| **App bundle size** | ~50MB | ___ MB | ☐ |

---

## Regression Testing

After any code changes, re-test:
- [ ] Core workflow (Press → Speak → Release → Inject)
- [ ] Overlay animations
- [ ] Settings window
- [ ] Model switching
- [ ] Permission handling

---

## Final Checklist

Before release:
- [ ] All critical tests pass
- [ ] No known crashes or data loss
- [ ] README.md updated with usage instructions
- [ ] CHANGELOG.md created (if versioning)
- [ ] Code signing & notarization complete
- [ ] DMG installer tested on clean Mac
- [ ] Documentation complete
- [ ] GitHub releases page prepared (if open source)

---

## Test Log

Record test results:

**Date:** _______________
**Tester:** _______________
**macOS Version:** _______________
**Hardware:** _______________

**Critical Issues Found:**
-
-
-

**Minor Issues Found:**
-
-
-

**Performance Notes:**
-
-

**Overall Status:** ☐ Pass  ☐ Fail  ☐ Conditional Pass

---

## Known Limitations

Document any known issues that won't be fixed in this release:
- WhisperKit may not expose avg_logprob yet (confidence defaulting to 0.7)
- Hotkey is hardcoded to Right Option (customization in future version)
- No streaming transcription yet (future enhancement)
- Vocabulary editor not implemented (edit JSON file manually)

---

**Testing complete! Ready for distribution?** ✅
