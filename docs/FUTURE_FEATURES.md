# Future Features & Roadmap

This document tracks planned features and improvements for VoiceDev.

## Status Legend
- 🎯 **Planned** - Confirmed for development
- 💡 **Proposed** - Under consideration
- 🚧 **In Progress** - Currently being worked on
- ✅ **Completed** - Already implemented
- ❌ **Rejected** - Decided not to implement

---

## High Priority Features

### 💡 Text-to-Speech (Read Back)
**Status**: Proposed
**Priority**: High
**Complexity**: Medium

**Description**: Add TTS capability to read back transcribed text for verification before insertion.

**Use Cases**:
- Verify transcription accuracy without looking at screen
- Accessibility for visually impaired users
- Proofreading support

**Implementation Options**:
1. **Option A: Read Back After Transcription**
   - Automatic playback after transcription
   - Optional: Toggle in menu "Enable Read-Back"
   - Delay text insertion until audio completes
   - User can interrupt with hotkey

2. **Option B: Read Selected Text**
   - New hotkey (e.g., Right Shift)
   - Reads currently selected text from any app
   - Useful for proofreading written content

3. **Option C: Custom Text Input**
   - Dialog box for typing text
   - "Speak" button to read it aloud
   - Less relevant for dictation app

**TTS Engine Options**:
- macOS `say` command (native, offline, fast) ⭐ **Recommended**
- pyttsx3 (cross-platform, offline)
- gTTS (Google TTS, requires internet)
- Coqui TTS (offline, high quality, large download)

**Voice Selection**:
- Match current language (RO/EN)
- Romanian voice: "Ioana" (macOS built-in)
- English voice: "Samantha" or "Alex" (macOS built-in)
- Optional: User-selectable voice in settings

**Implementation Plan**:
1. Create `tts_engine.py` module
2. Add "Enable Read-Back" toggle in menu
3. Play audio after transcription (if enabled)
4. Add hotkey for reading selected text
5. Test with Romanian and English voices

**Estimated Time**: 2-3 hours

---

### 💡 Custom Hotkey Configuration
**Status**: Proposed
**Priority**: High
**Complexity**: Medium

**Description**: Allow users to customize the dictation hotkey (currently fixed to Right Alt).

**Features**:
- GUI for selecting hotkey combination
- Support modifier keys (Ctrl, Alt, Cmd, Shift)
- Support function keys (F1-F12)
- Conflict detection (warn if hotkey already used by system)
- Save hotkey preference to config file

**Implementation**:
- Settings dialog with hotkey recorder
- Validate hotkey before saving
- Update `hotkey_controller.py` to use dynamic key
- Store preference in JSON config file

**Estimated Time**: 3-4 hours

---

### 💡 Vocabulary Editor UI
**Status**: Proposed
**Priority**: Medium
**Complexity**: Medium

**Description**: Graphical interface for managing custom vocabulary instead of editing JSON manually.

**Features**:
- List all custom vocabulary entries
- Add new word pairs (spoken → written)
- Edit existing entries
- Delete entries
- Test pronunciation (speak a word, see if it matches)
- Import/export vocabulary
- Categorize by language (RO/EN)

**UI Design**:
```
┌─────────────────────────────────────┐
│ Custom Vocabulary Editor            │
├─────────────────────────────────────┤
│ Spoken         → Written             │
│ gheata hab     → GitHub         [✎][✖] │
│ pai ton        → Python         [✎][✖] │
│ nod ge es      → Node.js        [✎][✖] │
│                                     │
│ [+ Add New]  [Import]  [Export]    │
└─────────────────────────────────────┘
```

**Estimated Time**: 4-5 hours

---

### 💡 Multi-Language Support (Beyond RO/EN)
**Status**: Proposed
**Priority**: Low
**Complexity**: Low

**Description**: Add support for more languages beyond Romanian and English.

**Supported by Whisper**: Spanish, French, German, Italian, Portuguese, Polish, Russian, Japanese, Korean, Chinese, Arabic, Hindi, Turkish, and 80+ more

**Implementation**:
- Expand language menu to show all supported languages
- Add language-specific diacritics corrections
- Add language-specific vocabulary files
- Test with common languages (ES, FR, DE)

**Estimated Time**: 2-3 hours per language

---

### 💡 Voice Commands for Code Patterns
**Status**: Proposed
**Priority**: Medium
**Complexity**: Medium

**Description**: Expand voice command support for common code patterns.

**Current Commands** (already implemented):
- "new line" → \n
- "tab" → \t
- "equals" → =
- "open brace" → {

**New Commands to Add**:
- **Control Flow**:
  - "if statement" → if ():
  - "else if" → elif:
  - "for loop" → for in range():
  - "while loop" → while :
  - "try catch" → try: ... except:

- **Functions**:
  - "function [name]" → def name():
  - "arrow function" → () => {}
  - "return" → return

- **Common Patterns**:
  - "print statement" → print()
  - "import [module]" → import module
  - "class [name]" → class Name:

**Language-Aware**:
- Python-specific patterns when in .py file
- JavaScript patterns when in .js file
- Detect context and adapt

**Estimated Time**: 3-4 hours

---

### 💡 Undo Last Transcription
**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

**Description**: Add ability to undo the last inserted text.

**Features**:
- Hotkey (e.g., Cmd+Z or custom)
- Deletes last transcribed text
- Works with text injection history
- Limit: Last 5 transcriptions

**Implementation**:
- Store last N transcriptions in queue
- On undo: delete characters equal to last text length
- Use backspace simulation or select+delete

**Estimated Time**: 2 hours

---

## Medium Priority Features

### 💡 Transcription History Log
**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

**Description**: Keep a log of all transcriptions for review and debugging.

**Features**:
- Save all transcriptions to log file
- Include timestamp, language, model used
- View history in menu or separate window
- Export history to CSV
- Clear history option

**Log Format**:
```
2024-12-27 14:23:15 | RO | small | "Aceasta este o funcție"
2024-12-27 14:24:30 | EN | small | "This is a test"
```

**Estimated Time**: 2-3 hours

---

### 💡 Confidence Score Display
**Status**: Proposed
**Priority**: Low
**Complexity**: Low

**Description**: Show Whisper's confidence score for each transcription.

**Features**:
- Display confidence % in tooltip or notification
- Warn if confidence < 70%
- Option to auto-discard low-confidence results
- Helps identify when to re-dictate

**Implementation**:
- Whisper already provides confidence scores
- Extract from transcription result
- Display in terminal and optionally in UI

**Estimated Time**: 1-2 hours

---

### 💡 Pause/Resume Recording
**Status**: Proposed
**Priority**: Low
**Complexity**: Medium

**Description**: Allow pausing mid-dictation without stopping.

**Current Behavior**: Hold key → speak → release = transcribe

**New Behavior**:
- Hold key → speak → tap another key to pause
- Continue speaking → tap to resume
- Release main key → transcribe everything

**Use Case**: Take a breath or think without ending dictation

**Complexity Note**: Requires multi-key handling and audio buffer management

**Estimated Time**: 4-5 hours

---

### 💡 Punctuation Commands
**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

**Description**: Voice commands for punctuation marks.

**Commands**:
- "period" → .
- "comma" → ,
- "question mark" → ?
- "exclamation point" → !
- "semicolon" → ;
- "colon" → :
- "new paragraph" → \n\n
- "quote" → "
- "apostrophe" → '

**Note**: Some already implemented in text_processor.py, expand coverage

**Estimated Time**: 1-2 hours

---

## Low Priority Features

### 💡 Cloud Sync for Vocabulary
**Status**: Proposed
**Priority**: Low
**Complexity**: High

**Description**: Sync custom vocabulary across multiple Macs.

**Options**:
- iCloud Drive sync (vocabulary.json)
- Dropbox sync
- Custom server sync
- Git repository sync

**Privacy Concern**: Ensure user controls where data goes

**Estimated Time**: 5-6 hours

---

### 💡 Noise Cancellation
**Status**: Proposed
**Priority**: Low
**Complexity**: High

**Description**: Filter out background noise for better transcription.

**Implementation**:
- Use noisereduce library
- Apply to audio before transcription
- May slow down processing
- Optional toggle

**Estimated Time**: 4-5 hours

---

### 💡 Training on Custom Vocabulary
**Status**: Proposed
**Priority**: Low
**Complexity**: Very High

**Description**: Fine-tune Whisper model on user's custom vocabulary.

**Challenges**:
- Requires audio samples of user speaking custom words
- Computationally expensive
- Large storage requirement
- May not provide significant improvement

**Estimated Time**: 20+ hours (complex ML work)

---

### 💡 Multi-User Support
**Status**: Proposed
**Priority**: Low
**Complexity**: Medium

**Description**: Different profiles for different users.

**Features**:
- Separate vocabulary per user
- Separate language preferences
- Voice recognition to auto-switch profiles
- User management UI

**Use Case**: Shared computer with multiple users

**Estimated Time**: 6-8 hours

---

## Quality of Life Improvements

### 💡 Statistics Dashboard
**Status**: Proposed
**Priority**: Low
**Complexity**: Low

**Description**: Track and display usage statistics.

**Metrics**:
- Total transcriptions
- Total words dictated
- Average transcription time
- Most used words
- Language usage breakdown
- Model usage breakdown
- Accuracy estimates

**UI**: Simple dashboard in settings or separate window

**Estimated Time**: 3-4 hours

---

### 💡 Dark Mode Icon
**Status**: Proposed
**Priority**: Low
**Complexity**: Very Low

**Description**: Adaptive menu bar icon for dark/light mode.

**Implementation**:
- Detect macOS appearance mode
- Use appropriate icon color
- Or create template icon (auto-adapts)

**Estimated Time**: 30 minutes

---

### 💡 Notification System
**Status**: Proposed
**Priority**: Low
**Complexity**: Low

**Description**: macOS notifications for events.

**Events**:
- Transcription completed
- Model download completed
- Error occurred
- Low confidence warning

**Implementation**:
- Use Qt notification system or macOS native notifications
- User can enable/disable in settings

**Estimated Time**: 2 hours

---

## Platform Expansion

### 💡 Windows Support
**Status**: Proposed
**Priority**: Medium
**Complexity**: High

**Description**: Port VoiceDev to Windows.

**Changes Required**:
- Hotkey detection (Windows API)
- Context detection (Windows apps)
- Text injection (Windows keyboard simulation)
- System tray icon (Windows notification area)
- Audio capture (should work with PyAudio)
- Whisper (already cross-platform)

**Estimated Time**: 15-20 hours

---

### 💡 Linux Support
**Status**: Proposed
**Priority**: Low
**Complexity**: High

**Description**: Port VoiceDev to Linux.

**Challenges**:
- Multiple desktop environments (GNOME, KDE, etc.)
- Different hotkey systems
- System tray varies by DE
- Packaging complexity

**Estimated Time**: 20-25 hours

---

## Features Under Consideration

### 💡 Plugin System
**Status**: Under Consideration
**Priority**: Low
**Complexity**: Very High

**Description**: Allow third-party plugins to extend functionality.

**Use Cases**:
- Custom text processors
- Custom TTS engines
- Integration with IDEs
- Language-specific enhancements

**Challenges**:
- Security (sandboxing)
- API design
- Documentation
- Maintenance

**Estimated Time**: 30+ hours

---

### 💡 Web API Mode
**Status**: Under Consideration
**Priority**: Low
**Complexity**: High

**Description**: Run VoiceDev as a local web service.

**Use Case**:
- Use from web browsers
- Integration with web apps
- Remote access (LAN only)

**Privacy Concern**: Audio over network (even locally)

**Estimated Time**: 10-15 hours

---

## Rejected Ideas

### ❌ Cloud-Based Transcription
**Reason**: Violates offline-first principle, privacy concerns

### ❌ Mobile App
**Reason**: Out of scope, different use case

### ❌ Video Recording
**Reason**: Not relevant to dictation app

---

## How to Propose a Feature

If you have an idea for a new feature:

1. **Check existing list** - Is it already here?
2. **Consider use case** - Who benefits? How often used?
3. **Estimate complexity** - Simple fix or major change?
4. **Privacy impact** - Does it compromise offline/privacy goals?
5. **Add to this document** with:
   - Clear description
   - Use case
   - Proposed implementation
   - Estimated time (if known)

---

## Implementation Priority

Features will be prioritized based on:

1. **User Impact** - How many users benefit?
2. **Frequency of Use** - Daily vs occasional?
3. **Complexity** - Quick wins vs large projects?
4. **Privacy/Offline Alignment** - Fits VoiceDev's core values?
5. **Dependencies** - Blocks other features?

**Current Top 3 Priorities**:
1. 🎯 Text-to-Speech (Read Back)
2. 🎯 Custom Hotkey Configuration
3. 🎯 Vocabulary Editor UI

---

**Last Updated**: 2024-12-27
**Maintainer**: VoiceDev Team

**Want to contribute?** Pick a feature, implement it, and submit a PR!
