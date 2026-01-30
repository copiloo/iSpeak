# Auto-Press Enter Feature

## Overview

The **Auto-Press Enter** feature automatically presses the Enter key after iSpeak inserts your transcribed text. This is perfect for chat applications, messaging apps, and any scenario where you want to immediately send your dictated message.

## Use Cases

### Perfect For:
- 💬 **Chat Applications** - Slack, Discord, Teams, WhatsApp Web
- 📧 **Messaging Apps** - iMessage, Telegram, Signal
- 🤖 **AI Chat Interfaces** - ChatGPT, Claude, Copilot
- 📝 **Comment Boxes** - GitHub, Jira, Confluence
- 🔍 **Search Bars** - Google, documentation sites

### Not Recommended For:
- ❌ **Code Editors** - You usually don't want auto-Enter when coding
- ❌ **Word Processors** - Text editing apps where Enter starts new paragraph
- ❌ **Forms** - Multi-field forms where Enter might submit prematurely

## How to Enable

1. **Right-click** the iSpeak menu bar icon
2. **Click** "Auto-Press Enter After Dictation"
3. A checkmark (✓) appears when enabled

## How It Works

### Without Auto-Press Enter (Default):
```
1. Hold Right Alt
2. Speak: "Hello, how are you?"
3. Release Right Alt
4. Text appears: "Hello, how are you?"
5. YOU press Enter manually ← Extra step!
6. Message sends
```

### With Auto-Press Enter (Enabled):
```
1. Hold Right Alt
2. Speak: "Hello, how are you?"
3. Release Right Alt
4. Text appears: "Hello, how are you?"
5. iSpeak presses Enter automatically ✨
6. Message sends immediately!
```

## Example Workflow

### Using with ChatGPT/Claude:

1. **Enable Auto-Press Enter** (one-time setup)
2. Open ChatGPT or Claude in browser
3. Click in the message box
4. **Dictate your question**:
   - Hold Right Alt
   - Say: "Explain how async await works in JavaScript"
   - Release
5. **Message sends automatically!** No need to press Enter
6. AI responds
7. **Dictate your follow-up**:
   - Hold Right Alt
   - Say: "Can you show an example?"
   - Release
8. **Sent automatically again!**

### Using with Slack:

1. **Enable Auto-Press Enter**
2. Open Slack channel
3. Click in message box
4. **Dictate**: "The meeting is moved to 3 PM"
5. **Sent automatically!**
6. Continue conversation hands-free

## Timing

The Enter key is pressed **100ms after text insertion** to ensure:
- Text is fully inserted before Enter
- No race conditions
- Smooth, reliable operation

## Toggling On/Off

You can toggle this feature anytime:

**Enable**: Menu → "Auto-Press Enter After Dictation" (adds ✓)
**Disable**: Menu → "Auto-Press Enter After Dictation" (removes ✓)

The setting persists until you quit iSpeak.

## Tips for Best Results

### When to Enable:
- 💬 Chatting or messaging
- 🤖 Using AI assistants
- 🔍 Doing multiple searches
- 📝 Adding comments rapidly

### When to Disable:
- 📄 Writing documents
- 💻 Coding
- 📋 Filling forms with multiple fields
- ✏️ Composing emails (where you review before sending)

### Pro Tip: Quick Toggle

Create a workflow:
1. **Default: Disabled** (for coding, writing)
2. **When chatting**: Right-click → Enable Auto-Enter
3. **After chat**: Right-click → Disable Auto-Enter

It only takes 2 clicks to toggle!

## Technical Details

### What iSpeak Does:

1. Transcribes your speech
2. Inserts text via clipboard (Cmd+V)
3. Waits 100ms
4. **If Auto-Enter enabled**: Simulates Enter key press
5. Your message sends!

### Implementation:

The feature uses `pynput` to simulate the Enter key press, just like typing it yourself.

## Troubleshooting

### Enter Pressed Too Soon

**Problem**: Enter is pressed before text finishes inserting

**Solution**: This shouldn't happen due to the 100ms delay, but if it does:
- The text injection might be slow
- Try disabling and re-enabling the feature
- Report the issue if it persists

### Enter Not Working

**Problem**: Auto-Enter is enabled but Enter isn't being pressed

**Causes**:
1. **Accessibility permissions** not granted
2. **Application not focused** (click in message box first)
3. **Different Enter key expected** (some apps use Cmd+Enter)

**Solutions**:
1. Grant Accessibility permissions: System Settings > Privacy & Security > Accessibility
2. Click in the message box before dictating
3. For apps using Cmd+Enter (like Slack with setting enabled), disable Auto-Enter and use the app's hotkey

### Enters Too Much

**Problem**: Multiple Enters being pressed

**Solution**: Shouldn't happen - please report if it does!

## Compatibility

### Works Great:
- ✅ ChatGPT web interface
- ✅ Claude web interface
- ✅ Slack (default Enter-to-send setting)
- ✅ Discord
- ✅ WhatsApp Web
- ✅ Google search
- ✅ iMessage
- ✅ Terminal (sends command)

### Requires App-Specific Hotkey:
- ⚠️ Slack (if "Cmd+Enter to send" is enabled)
- ⚠️ Microsoft Teams (uses Cmd+Enter)
- ⚠️ Some enterprise chat apps

**Solution**: For these apps, keep Auto-Enter disabled and use their native send hotkey.

## Future Enhancements

Potential improvements tracked in [FUTURE_FEATURES.md](FUTURE_FEATURES.md):

- **Custom send keys** - Configure Cmd+Enter, Ctrl+Enter, etc.
- **App-specific rules** - Auto-enable for chat apps, auto-disable for editors
- **Delay customization** - Adjust the 100ms delay if needed
- **Send confirmation** - Optional sound or notification when sent

## Summary

**Auto-Press Enter** is a simple but powerful feature that makes iSpeak perfect for conversational use cases.

**Enable it when**: Chatting, messaging, using AI assistants
**Disable it when**: Coding, writing documents, filling forms

Toggle anytime via the menu - it's just 2 clicks away!

---

**Happy hands-free chatting!** 💬🎤
