# iSpeak Usage Tips

## Getting Started

### First Test - Use the Prototype

Start with the simple prototype to test the basic functionality:

```bash
source venv/bin/activate
python prototype.py
```

**Wait for:** "iSpeak Prototype Ready!"

## How to Dictate

### The Right Way ✅

1. **Press and HOLD** the Right Alt key
2. **Speak clearly** for at least 1-2 seconds
3. **Release** the Right Alt key
4. **Wait** 1-2 seconds for transcription
5. Text appears!

### Common Mistakes ❌

**Mistake 1: Too Quick**
```
Press-Release immediately ❌
"Recording too short, ignoring"
```
**Fix:** Hold the key for at least 1-2 seconds while speaking

**Mistake 2: Speaking Before Pressing**
```
Speak first, then press key ❌
```
**Fix:** Press key FIRST, then speak

**Mistake 3: Not Waiting**
```
Press again before transcription finishes ❌
```
**Fix:** Wait for "✅ Ready" before dictating again

## Understanding the Messages

### During Operation

- **🎤 Recording started...** - You're now recording, speak!
- **⏸️ Recording stopped, transcribing...** - Processing your audio
- **Transcribing (X samples)...** - Converting speech to text
- **Transcription took X.XXs** - How long it took
- **✅ Text inserted: '...'** - Success!
- **✅ Ready** - Ready for next dictation

### Warning Messages

- **❌ Recording too short, ignoring (hold key longer)**
  - You released the key too quickly
  - Hold for at least 1-2 seconds

- **⚠️ Already processing, please wait...**
  - Previous transcription still running
  - Wait for it to finish

- **❌ Transcription failed**
  - Something went wrong
  - Check the error message above
  - Try again

### Error Messages

- **No speech detected**
  - Microphone might not be working
  - Check System Settings > Microphone
  - Speak louder or closer to mic

## Best Practices

### For Best Accuracy

1. **Speak Clearly** - Don't mumble or rush
2. **Use Complete Sentences** - "Acesta este un test" not just "test"
3. **Pause Between Words** - Give Whisper time to recognize
4. **Avoid Background Noise** - Find a quiet spot
5. **Good Microphone** - Built-in Mac mic works, but external is better

### Timing

- **Minimum Recording:** 1-2 seconds
- **Optimal Recording:** 3-5 seconds
- **Maximum Recording:** ~10 seconds (buffer limit)
- **Processing Time:** Usually 0.5-2 seconds

### Language Switching

**Romanian (default):**
```
Right-click menu bar icon > Language shows "RO"
Speak Romanian: "funcție pentru calcul"
```

**Switch to English:**
```
Right-click menu bar icon > "Toggle Language (RO ⇄ EN)"
Speak English: "function for calculation"
```

## Testing Your Setup

### Test 1: Basic Dictation

```bash
# Start app
./run.sh

# When ready:
1. Open TextEdit or any text editor
2. Click in the document
3. Press and HOLD Right Alt for 2 seconds
4. Say: "Acesta este un test"
5. Release key
6. Wait for text to appear
```

**Expected:** "Acesta este un test" appears

### Test 2: Code Dictation

```bash
# Open VS Code
1. Create new Python file
2. Press and HOLD Right Alt
3. Say: "def main new line print hello world"
4. Release key
```

**Expected:**
```python
def main
print hello world
```

(Note: Code formatting depends on context detection)

### Test 3: Language Switch

```bash
1. Right-click menu icon
2. Click "Toggle Language (RO ⇄ EN)"
3. Notice: Language: EN in menu
4. Press and HOLD Right Alt
5. Say: "this is a test"
6. Release key
```

**Expected:** "this is a test" appears

## Troubleshooting

### "Recording too short" Every Time

**Cause:** Not holding key long enough

**Solution:**
1. Count "one-mississippi, two-mississippi" while holding
2. Practice holding for 2 full seconds
3. Speak while holding, not before/after

### No Text Appears

**Cause 1:** No Accessibility permission

**Solution:**
1. System Settings > Privacy & Security > Accessibility
2. Find Terminal or Python
3. Enable the checkbox
4. Restart iSpeak

**Cause 2:** Wrong app focused

**Solution:**
1. Click in the target app first
2. Then press hotkey to dictate

### Microphone Not Working

**Check:**
```bash
# Test microphone access
python -c "import pyaudio; p = pyaudio.PyAudio(); print('Mic OK')"
```

**If error:**
1. System Settings > Privacy & Security > Microphone
2. Enable Terminal or Python
3. Restart iSpeak

### Poor Accuracy

**Romanian not recognized:**
1. Check language is set to RO (menu icon)
2. Speak standard Romanian (not dialect)
3. Avoid slang or very technical terms
4. Add custom words to vocabulary.json

**English not recognized:**
1. Switch to EN language
2. Speak clearly in English
3. American accent works best (Whisper training)

## Performance Tips

### If Slow (>3 seconds)

Edit `ispeak/transcription.py` line 23:
```python
# Change from "base" to "tiny"
self.model = WhisperModel(
    "tiny",  # Faster but less accurate
    ...
```

### If Inaccurate

Edit `ispeak/transcription.py` line 23:
```python
# Change from "base" to "small"
self.model = WhisperModel(
    "small",  # Slower but more accurate
    ...
```

## Advanced Usage

### Custom Vocabulary

Edit `resources/vocabulary.json`:

```json
{
  "git hub": "GitHub",
  "my project name": "MyProjectName",
  "custom term": "CustomTerm"
}
```

Restart iSpeak to load changes.

### Keyboard Shortcuts

Currently only Right Alt is supported. Future versions will allow customization.

## Getting Help

If you're still having issues:

1. Check the terminal output for error messages
2. Read [SETUP_COMPLETE.md](SETUP_COMPLETE.md)
3. Read [docs/INSTALL.md](docs/INSTALL.md)
4. Check permissions in System Settings
5. Restart iSpeak
6. Restart your Mac (if all else fails)

## Quick Reference

| Action | Key | Duration |
|--------|-----|----------|
| Start Recording | Press Right Alt | - |
| Speak | While holding | 1-2 seconds minimum |
| Stop Recording | Release Right Alt | - |
| Wait | - | 1-2 seconds |
| Text Appears | - | - |

**Remember:** Press → Speak → Release → Wait → Success!

---

Happy dictating! 🎤
