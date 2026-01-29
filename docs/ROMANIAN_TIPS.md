# Romanian Language Tips for VoiceDev

## Understanding Romanian Support

VoiceDev uses OpenAI's Whisper model for speech recognition. While Whisper supports Romanian, **its accuracy for Romanian is lower than for English**. This is a limitation of the AI model itself, not VoiceDev.

### Why Romanian Is Harder

1. **Training Data**: Whisper was trained on significantly more English audio than Romanian
2. **Diacritics**: Romanian characters like ă, â, î, ș, ț can be challenging
3. **Technical Terms**: Most programming terms are English-based, causing confusion
4. **Model Size**: Larger models = better Romanian support

## Optimizations Applied

VoiceDev has been optimized for Romanian:

✅ **Upgraded to "small" model** - Better accuracy than "base" model
✅ **Enhanced diacritics correction** - Automatically fixes common mistakes
✅ **Romanian vocabulary** - Custom dictionary for tech terms
✅ **Post-processing** - Cleans up common transcription errors

## Best Practices for Romanian

### 1. Speak Clearly and Slowly

Unlike English, Romanian requires extra clarity:

```
❌ Fast: "funcțiapentruvalidare"
✅ Slow: "funcție... pentru... validare"
```

**Tip**: Pause briefly between words, especially technical terms.

### 2. Use Standard Pronunciation

- Avoid regional dialects or heavy accents
- Pronounce diacritics clearly (ă, â, î, ș, ț)
- Use standard Romanian, not colloquial speech

### 3. Shorter Sentences Work Better

```
❌ Long: "Creează o funcție care primește doi parametri și returnează suma lor dacă ambii sunt numere întregi"
✅ Short: "Funcție cu doi parametri"
[pause, dictate again]
✅ Short: "Returnează suma numerelor"
```

**Tip**: Break complex thoughts into 3-5 second chunks.

### 4. Mix Romanian and English Strategically

For programming, consider this approach:

**Option A: Romanian descriptions, English code terms**
```
Say: "funcție numită calculate total"
Result: "funcție numită calculateTotal"
```

**Option B: Switch to English for code blocks**
```
1. Toggle language to EN (Right-click menu)
2. Dictate code in English
3. Toggle back to RO for comments
```

**Option C: Pure Romanian (hardest but possible)**
```
Say: "funcție pentru calcul"
Result: "funcție pentru calcul"
```

### 5. Use the Custom Vocabulary

Add common terms you use to [vocabulary.json](resources/vocabulary.json):

```json
{
  "gheata hab": "GitHub",
  "pai ton": "Python",
  "your custom term": "YourCustomTerm"
}
```

Then restart VoiceDev to load the changes.

## Common Romanian Issues & Solutions

### Issue 1: Missing Diacritics

**Problem**: Whisper outputs "functie" instead of "funcție"

**Solution**: VoiceDev automatically corrects these common words:
- functie → funcție
- variabila → variabilă
- metoda → metodă
- fisier → fișier
- and 30+ more...

**If a word isn't corrected**: Add it to the corrections list in [text_processor.py](voicedev/text_processor.py#L50)

### Issue 2: Tech Terms Misheard

**Problem**: "GitHub" becomes "get hub" or "gheata hab"

**Solution**: Already added to vocabulary.json. If you find more, add them:

```json
{
  "your mispronunciation": "CorrectTerm"
}
```

### Issue 3: Slow Transcription

**Problem**: Takes 3-5+ seconds to transcribe

**Possible causes**:
1. **Long sentence** - Try shorter phrases (3-5 seconds max)
2. **Complex vocabulary** - Simplify your speech
3. **Model size** - "small" model is slower than "tiny" but more accurate

**To make it faster** (at cost of accuracy):
Edit [transcription.py:7](voicedev/transcription.py#L7):
```python
def __init__(self, model_size="tiny", models_dir="./models"):  # Changed from "small"
```

### Issue 4: Wrong Words Entirely

**Problem**: You say "listă" but get "list" or random text

**Causes**:
1. **Background noise** - Find a quieter environment
2. **Microphone quality** - Use a better mic
3. **Unclear pronunciation** - Speak more clearly
4. **Model limitation** - Whisper struggles with that specific word

**Solutions**:
1. Speak louder and clearer
2. Add the word to vocabulary.json with phonetic spelling
3. Try saying it differently (synonym)
4. Switch to English for that specific term

## Recommended Workflow for Romanian Developers

### Strategy 1: Bilingual Approach (Recommended)

1. **Comments in Romanian** (set to RO)
   ```python
   # funcție pentru validare
   ```

2. **Code in English** (toggle to EN)
   ```python
   def validate_user(username, password):
       return True
   ```

3. **Toggle as needed** (Right-click menu)

**Why this works**:
- English code is understood globally
- Romanian comments for your team
- Each language gets optimal recognition

### Strategy 2: Full Romanian (Advanced)

If you must use Romanian for everything:

1. **Set language to RO** (default)
2. **Speak very clearly** with pauses
3. **Use shorter sentences** (3-5 seconds)
4. **Add custom vocabulary** for your project's terms
5. **Be patient** - transcription will be slower

### Strategy 3: English-First (Easiest)

If accuracy > language preference:

1. **Toggle to EN** at startup
2. **Code and comment in English**
3. **Only use RO** for documentation/notes

**Result**: Fast, accurate, but not Romanian

## Model Comparison for Romanian

| Model | Speed | Romanian Accuracy | Recommended For |
|-------|-------|-------------------|-----------------|
| tiny | ⚡⚡⚡ Very Fast | ⭐⭐ Poor | Not recommended for Romanian |
| base | ⚡⚡ Fast | ⭐⭐⭐ Fair | Quick tests only |
| **small** | ⚡ Medium | ⭐⭐⭐⭐ Good | **Default - Best balance** |
| medium | 🐌 Slow | ⭐⭐⭐⭐⭐ Excellent | If accuracy > speed |
| large | 🐌🐌 Very Slow | ⭐⭐⭐⭐⭐ Best | Not practical for real-time |

**Current setting**: `small` (good balance)

**To change model** edit [transcription.py:7](voicedev/transcription.py#L7):
```python
def __init__(self, model_size="medium", models_dir="./models"):  # For better accuracy
```

Note: First run with new model will download it (~500MB for medium).

## Testing Your Romanian Setup

### Test 1: Simple Phrase

```
Set language: RO
Press and hold: Right Alt
Say: "Aceasta este o funcție"
Release: Right Alt
Expected: "Aceasta este o funcție" (or close)
```

### Test 2: Technical Term

```
Set language: RO
Press and hold: Right Alt
Say: "importă librăria pentru calcul"
Release: Right Alt
Expected: "importă librăria pentru calcul"
```

### Test 3: Code Context

```
Open: VS Code or text editor
Set language: RO
Press and hold: Right Alt
Say: "funcție pentru validare utilizator"
Release: Right Alt
Expected: "funcție pentru validare utilizator"
```

## Improving Romanian Over Time

VoiceDev learns from your custom vocabulary:

1. **Notice patterns** - What words are consistently wrong?
2. **Add to vocabulary** - Add mispronunciations → correct spelling
3. **Update corrections** - Add missing diacritics rules
4. **Share findings** - Help improve VoiceDev for Romanian users

### Example Learning Process

**Day 1**: "autentificare" becomes "autentificare" ✅ (lucky!)

**Day 2**: "autentificare" becomes "authentication" ❌

**Solution**: Add to vocabulary.json:
```json
{
  "authentication": "autentificare",
  "authenticate": "autentificare"
}
```

**Day 3**: "autentificare" works every time ✅

## When to Use English Instead

Consider using English when:

1. **Collaborating internationally** - Code understood globally
2. **Using English libraries/frameworks** - Easier to dictate
3. **Speed is critical** - English recognition is 2-3x faster
4. **High accuracy needed** - English model is more reliable
5. **Learning resources** - Most docs are in English

**Remember**: There's no shame in using English for code. Many Romanian developers do this professionally.

## Getting Help

If Romanian transcription isn't working well:

1. Check [LANGUAGE_TIPS.md](LANGUAGE_TIPS.md) - Language detection issues
2. Read [USAGE_TIPS.md](USAGE_TIPS.md) - Basic usage
3. Verify language is set to RO (Right-click menu icon)
4. Try the "small" or "medium" model for better accuracy
5. Add your problematic words to vocabulary.json

## Summary

✅ **DO**:
- Speak clearly and slowly
- Use shorter sentences (3-5 seconds)
- Add custom vocabulary for your terms
- Consider mixing Romanian and English
- Use the "small" or "medium" model

❌ **DON'T**:
- Expect perfect accuracy (Whisper limitation)
- Rush through complex sentences
- Use heavy dialect or slang
- Give up - it improves with custom vocabulary!

---

**Romanian support is possible, but requires patience and optimization.**

For best results, consider the **bilingual approach**: Romanian for comments/docs, English for code.
