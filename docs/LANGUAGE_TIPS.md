# Language Detection Tips

## Understanding Language Settings

iSpeak has a **language preference** that you set, but Whisper may still **detect** a different language based on what it hears.

### Default Language

**The app starts in ROMANIAN (RO) by default.**

When you see:
```
Language: RO (Romanian)
Current setting: RO
```

This means the app will try to transcribe in Romanian first.

## How Language Detection Works

1. **You set the language:** RO or EN via the menu
2. **Whisper transcribes:** Uses your setting as a hint
3. **Whisper may detect differently:** If it thinks you spoke English when set to RO

### Example Scenario

```
Your setting: RO (Romanian)
You say: "Hello, how are you?" (in English)
Whisper hears: English words
Result: May take longer and/or give poor results
```

**Why?** Whisper is trying to interpret English as Romanian!

## Switching Languages

### Via Menu (Recommended)

1. Right-click the iSpeak menu bar icon
2. Click "Toggle Language (RO ⇄ EN)"
3. The menu will show the new language

### Check Current Language

Look at the menu:
- Language: RO = Romanian mode
- Language: EN = English mode

## Best Practices

### For Romanian Speech

1. Make sure language is set to **RO**
2. Speak standard Romanian (avoid heavy slang)
3. Speak clearly with proper diacritics pronunciation
4. Use complete sentences

### For English Speech

1. **IMPORTANT:** Switch to **EN** first!
2. Right-click menu > Toggle Language
3. Then dictate in English
4. Transcription will be faster and more accurate

## Performance Tips

### Slow Transcription?

If transcription takes longer than 2-3 seconds:

**Check 1: Language Mismatch**
```
Transcribing using language: RO...  ← You set Romanian
Transcribed: 'Hello there'  ← But spoke English
```

**Fix:** Switch to EN before speaking English!

**Check 2: Long Sentences**
- Longer audio = longer processing
- Try shorter phrases (3-5 seconds max)

**Check 3: Model Size**
- Using "base" model (default)
- Slower than "tiny" but more accurate

### Mixed Language Conversations?

If you switch between Romanian and English frequently:

**Option 1: Use Language Toggle**
```
1. Dictate in Romanian (RO mode)
2. Switch to EN
3. Dictate in English
4. Switch back to RO
5. Dictate in Romanian
```

**Option 2: Stick to One Language**
- Easier and faster
- Less switching needed
- More consistent results

## Debug Logging

The terminal shows which language is being used:

```
Transcribing (21504 samples) using language: RO...
Transcription took 0.44s
Requested: RO, Detected: RO  ← Good match!
Transcribed: 'Ce faci?'
```

vs

```
Transcribing (21504 samples) using language: RO...
Transcription took 2.5s  ← Took longer!
Requested: RO, Detected: EN  ← Mismatch!
Transcribed: 'What are you doing?'
```

**Notice:** When there's a mismatch, transcription takes longer.

## Common Issues

### "App keeps switching languages"

**Cause:** You're not actually switching the language setting, just speaking different languages.

**Fix:**
1. Check the menu: What does it say?
2. Match your speech to the setting
3. Or switch the setting to match your speech

### "Romanian words come out wrong"

**Possible causes:**
1. Language is set to EN (check menu!)
2. Pronunciation isn't clear
3. Word not in Whisper's vocabulary

**Fixes:**
1. Ensure language is set to RO
2. Speak more clearly
3. Add custom words to vocabulary.json

### "English works but Romanian doesn't"

**Check:**
1. Is language set to RO in the menu?
2. Are you using standard Romanian pronunciation?
3. Try simpler, more common words first

## Testing Each Language

### Test Romanian (RO)

1. Set language to RO (right-click menu)
2. Press Right Alt
3. Say: "Aceasta este o funcție pentru testare"
4. Release
5. Should appear quickly (~1s)

### Test English (EN)

1. Set language to EN (right-click menu)
2. Press Right Alt
3. Say: "This is a function for testing"
4. Release
5. Should appear quickly (~1s)

## Summary

✅ **DO:**
- Set language before dictating
- Match your speech to the setting
- Check the menu to confirm current language

❌ **DON'T:**
- Speak English when set to Romanian
- Speak Romanian when set to English
- Expect instant language auto-detection

---

**Quick Reference:**
- Default: RO (Romanian)
- Toggle: Right-click menu > "Toggle Language (RO ⇄ EN)"
- Check: Look at menu - "Language: XX"
- Match: Speech language = Menu language
