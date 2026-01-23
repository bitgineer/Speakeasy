---
type: guide
title: Frequently Asked Questions
created: 2025-01-23
tags:
  - faq
  - how-to
  - tips
  - help
related:
  - "[[installation]]"
  - "[[troubleshooting]]"
  - "[[known-issues]]"
---

# Frequently Asked Questions

Common questions about faster-whisper-hotkey, with quick answers and detailed explanations.

---

## Getting Started

### What is faster-whisper-hotkey?

A Windows application that converts speech to text using a hotkey. Press your hotkey, speak, and the transcribed text appears in your active application. Great for dictation, notes, coding, and more.

**Key Features:**
- Global hotkey activation from any application
- Multiple AI models (Whisper, Parakeet, Canary, Voxtral)
- GPU acceleration for faster transcription
- Auto-paste into your active window
- History of all transcriptions
- Multi-language support (100+ languages)

---

### How does it work?

1. **Press your hotkey** (default: Pause key)
2. **Speak into your microphone**
3. **Press hotkey again** to stop recording
4. **Text is transcribed** and pasted automatically

The transcription happens locally on your computer - no cloud API needed. Your audio never leaves your device.

---

### What are the system requirements?

**Minimum:**
- Windows 10 (64-bit) or later
- 4 GB RAM
- 2 GB disk space

**Recommended:**
- Windows 11
- 8+ GB RAM
- NVIDIA GPU with CUDA (optional but recommended)

---

## Installation and Setup

### Which installation method should I choose?

| Method | Best For |
|--------|----------|
| **Windows Installer** | Most users - easy setup and uninstall |
| **Portable ZIP** | Testing, USB drives, no-admin situations |
| **pip/uv** | Developers, Python users |

See [[installation]] for detailed instructions.

---

### Do I need a GPU?

No, but it helps. CPU transcription works but is slower:

| Model | CPU Speed | GPU Speed |
|-------|-----------|-----------|
| tiny  | 2x slower | Real-time |
| base  | 4x slower | Real-time |
| large | 20x slower | 2x slower |

For occasional use, CPU is fine. For heavy use, consider a GPU.

---

### Which model should I choose?

**For most users:** `base` or `small`
- Good balance of speed and accuracy
- Works well on CPU

**For best accuracy:** `medium` or `large-v3`
- Requires GPU for real-time performance
- Use on powerful computers

**For fastest:** `tiny`
- Best for slow computers
- Lower accuracy

**Model Comparison:**
| Model | Size | Speed | Accuracy | RAM |
|-------|------|-------|----------|-----|
| tiny  | 40 MB | Fastest | Good | 500 MB |
| base  | 140 MB | Fast | Very Good | 1 GB |
| small | 460 MB | Medium | Excellent | 2 GB |
| medium| 1.5 GB| Slow | Excellent | 4 GB |
| large-v3| 3 GB| Very Slow | Best | 8 GB |

---

## Usage

### How do I change the hotkey?

1. Open Settings (gear icon)
2. Go to "Hotkey" section
3. Press your desired key combination
4. Click "Save"

**Good alternatives to Pause:**
- `Ctrl+Alt+R`
- `Ctrl+Shift+Space`
- `Ctrl+;`

**Avoid:** Common shortcuts like `Ctrl+C`, `Ctrl+V`

---

### How do I transcribe in a different language?

1. Open Settings
2. Go to "Language" section
3. Select your language from the dropdown
4. Click "Save"

The app supports 100+ languages including:
- English, Spanish, French, German
- Chinese, Japanese, Korean
- Hindi, Arabic, Russian

Or enable **Auto-detect** to let the model detect the language automatically.

---

### Why isn't the text pasting?

**Check these:**

1. **Is the target window focused?**
   - Click in the application where you want text
   - Wait 1 second after recording stops

2. **Is clipboard blocked?**
   - Some secure apps block clipboard (password managers, terminals)
   - The app will fall back to typing mode

3. **Is paste delay too short?**
   - Increase "Paste delay" in settings
   - Try 100-200ms for slow applications

---

### Can I use it with VS Code / terminals?

**Yes**, but limitations exist:

- **VS Code editor**: Works perfectly
- **VS Code terminal**: May need manual paste (Ctrl+Shift+V)
- **Windows Terminal**: May need manual paste
- **PowerShell**: Works, usually needs Ctrl+V

**Tip:** Use the typing fallback mode for terminals if clipboard paste doesn't work.

---

### How do I access previous transcriptions?

1. Click the history icon (clock/table icon)
2. Browse your transcription history
3. Click any item to copy it to clipboard
4. Right-click for options (delete, edit, re-copy)

History is saved indefinitely unless you set a limit in settings.

---

## Performance Tips

### How can I make transcription faster?

**Immediate improvements:**
1. Use a smaller model (tiny or base)
2. Enable GPU acceleration if available
3. Close other applications
4. Reduce recording length

**Long-term:**
1. Upgrade RAM (more RAM = faster processing)
2. Get an NVIDIA GPU (huge speedup)
3. Use SSD for model cache

---

### Why is transcription slow on my computer?

**Most likely causes:**
1. **Using CPU instead of GPU** - Check Settings → Device
2. **Large model** - Try tiny or base instead of large
3. **Old computer** - Consider smaller models
4. **Other apps using resources** - Close browsers, games

**Expected speeds (per minute of audio):**
| Setup | tiny | base | small | medium | large |
|-------|------|------|-------|--------|-------|
| CPU (modern) | 5s | 10s | 20s | 40s | 80s |
| GPU (RTX 3060) | 2s | 3s | 5s | 10s | 20s |

---

### How do I reduce memory usage?

1. **Use a smaller model** - tiny uses 1/10 the memory of large
2. **Enable "Unload model when idle"** - Frees memory between uses
3. **Limit history size** - Settings → Advanced → Max history items
4. **Close when not in use** - Right-click tray icon → Exit

---

## Troubleshooting

### The hotkey doesn't work

**Try these:**
1. Check if another app is using the hotkey
2. Try a different hotkey combination
3. Run as Administrator
4. Restart the application

**Common conflicts:**
- Screen recorders (OBS, Fraps)
- Game overlays (Steam, Discord)
- Hotkey utilities (AutoHotkey, PowerToys)

---

### "No audio device found"

**Solutions:**
1. Check microphone is plugged in
2. Set as default recording device in Windows
3. Check Privacy → Microphone settings
4. Try a different USB port

---

### Transcription is inaccurate

**Improve accuracy by:**
1. Speak clearly and at moderate pace
2. Reduce background noise
3. Use a better microphone
4. Try a larger model (small or medium)
5. Specify language instead of auto-detect
6. Get closer to the microphone

---

### "Model download failed"

**Solutions:**
1. Check internet connection
2. Try again - automatic retry is enabled
3. Check firewall isn't blocking HuggingFace
4. Manually download from HuggingFace website

---

## Advanced Usage

### Can I use it for dictation in Word/Google Docs?

**Yes!**
1. Open Word or Google Docs
2. Click where you want text
3. Press hotkey and speak
4. Text appears after you stop

**Tips:**
- Speak punctuation ("comma", "period", "new line")
- Keep recordings under 30 seconds for best results
- Use "Auto-punctuation" feature in settings

---

### Can I use it for coding?

**Yes!** Great for:
- Writing comments
- Dictating variable names
- Adding documentation
- Writing commit messages

**Setup:**
- Use a code editor (VS Code, Sublime, etc.)
- Enable "Typing fallback" for terminals
- Use smaller snippets for better accuracy

---

### Can I transcribe audio files?

**Not directly**, but you can:
1. Play the audio file on your computer
2. Press hotkey to start recording
3. Let it play through
4. Press hotkey to stop

**For better results,** use a dedicated audio transcription tool that can process files directly.

---

### How does portable mode work?

Portable mode stores settings next to the executable instead of in AppData:

1. Create a file named `portable.txt` next to the exe
2. Settings are stored in `./settings/`
3. Models are cached in `./models/`

Great for:
- USB drives
- Running from network shares
- Keeping settings self-contained

See [[PORTABLE_MODE]] for details.

---

## Privacy and Data

### Does my audio leave my computer?

**No.** All transcription happens locally on your machine.

**Exceptions:**
- Model downloads (from HuggingFace, one-time)
- Anonymous analytics (optional, can be disabled)

**No cloud transcription.** No API calls. Your audio stays private.

---

### What data is collected?

**By default:** Nothing

**Optional analytics** (with your consent):
- Anonymous usage statistics
- Model performance data
- Error reports

**Disable in:** Settings → Privacy → Disable telemetry

---

### Can I use it offline?

**Yes,** after the initial model download.

1. Download models while online
2. Use offline anytime after
3. No internet connection required for transcription

---

## Tips and Tricks

### Best Practices

1. **Use a consistent hotkey** - Build muscle memory
2. **Keep recordings short** - Under 30 seconds is best
3. **Speak clearly** - Moderate pace, clear pronunciation
4. **Reduce background noise** - Quiet environment works best
5. **Use the right model** - Balance speed and accuracy

### Productivity Hacks

1. **Use for note-taking** - Capture thoughts quickly
2. **Draft emails** - Dictate, then edit
3. **Write commit messages** - Dictate while coding
4. **Accessibility** - Alternative to typing for RSI
5. **Voice commands** - Use with voice command feature

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Hotkey (default: Pause) | Start/Stop recording |
| Ctrl+H | Open history |
| Ctrl+, | Open settings |
| Ctrl+Q | Quit (when window focused) |

---

## Related Documentation

- [[installation]] - Installation guide
- [[troubleshooting]] - Detailed troubleshooting
- [[known-issues]] - Known bugs and limitations
- [[PORTABLE_MODE]] - Portable mode details
