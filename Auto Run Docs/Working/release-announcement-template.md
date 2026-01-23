---
type: template
title: Release Announcement Template
created: 2025-01-23
tags:
  - release
  - template
  - announcement
related:
  - "[[marketing-descriptions]]"
  - "[[demo-video-storyboard]]"
---

# Release Announcement Template

Use this template for announcing new releases of faster-whisper-hotkey.

---

## GitHub Release

### Title
```
🎤 Release v{VERSION}: {SHORT_DESCRIPTION}
```

### Body Template

```markdown
## 🎉 What's New in v{VERSION}

{HIGHLIGHT_FEATURES}

## 📦 Download

### Windows Installer (Recommended)
- **[faster-whisper-hotkey-setup-{VERSION}.exe](https://github.com/blakkd/faster-whisper-hotkey/releases/download/v{VERSION}/faster-whisper-hotkey-setup-{VERSION}.exe)**
  - Includes all dependencies
  - First-run setup wizard
  - Start menu integration

### Portable Version
- **[faster-whisper-hotkey-portable-{VERSION}-windows.zip](https://github.com/blakkd/faster-whisper-hotkey/releases/download/v{VERSION}/faster-whisper-hotkey-portable-{VERSION}-windows.zip)**
  - No installation required
  - Settings stored alongside executable

### From PyPI
```bash
pip install --upgrade faster-whisper-hotkey
# or with uv
uv pip install --upgrade faster-whisper-hotkey
```

## 🚀 Features

{FEATURE_LIST}

## 🐛 Bug Fixes

{BUG_FIX_LIST}

## 🔧 Technical Changes

{TECHNICAL_CHANGES}

## 📚 Documentation

{DOCUMENTATION_UPDATES}

## 🙏 Acknowledgments

Special thanks to:
- All contributors for this release
- The developers of [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [NVIDIA](https://huggingface.co/nvidia) for Parakeet and Canary models
- [Mistral](https://huggingface.co/mistralai) for Voxtral models

## 📝 Full Changelog

{FULL_CHANGELOG}

---

**Previous Release**: [v{PREVIOUS_VERSION}](https://github.com/blakkd/faster-whisper-hotkey/releases/tag/v{PREVIOUS_VERSION})
```

---

## Reddit Post Template

### Subreddits
- r/Python
- r/programming
- r/opensource
- r/WindowsApps
- r/VoiceRecognition

### Title
```
[Release] faster-whisper-hotkey v{VERSION}: {FEATURE_HIGHLIGHT}
```

### Body

```markdown
I'm excited to announce **faster-whisper-hotkey v{VERSION}**!

**faster-whisper-hotkey** is a minimalist push-to-talk transcription tool that works anywhere you can type. Just hold your hotkey, speak, release, and your text appears instantly.

## ✨ What's New in v{VERSION}

{NEW_FEATURES}

## 🎯 Key Features

- **Hold hotkey → Speak → Release → Text appears**
- Works in any text field (terminal, editor, browser, games)
- 25+ languages with automatic detection
- Multiple AI models: Parakeet, Canary, Voxtral, faster-whisper
- CPU or GPU support with automatic hardware detection
- 100% private—all processing happens locally

## 📥 Download

**Windows**: [Download Installer](https://github.com/blakkd/faster-whisper-hotkey/releases/latest) (no Python required!)

**From PyPI**: `pip install faster-whisper-hotkey`

**GitHub**: https://github.com/blakkd/faster-whisper-hotkey

---

Would love feedback from the community!
```

---

## Twitter/X Thread Template

### Tweet 1 (Main Announcement)

```
🎤 faster-whisper-hotkey v{VERSION} is here!

{MAIN_FEATURE_HIGHLIGHT}

Hold hotkey → Speak → Release → Text appears instantly

Works in terminal, editor, browser, or games.

Download: github.com/blakkd/faster-whisper-hotkey

🧵 Thread with features 📜
```

### Tweet 2 (Feature Highlight)

```
What's new in v{VERSION}?

{NEW_FEATURE_BULLET_POINTS}

#VoiceToText #Transcription #DevTools
```

### Tweet 3 (How It Works)

```
How it works:

1️⃣ Download & install (Windows - no Python needed!)
2️⃣ First-run wizard sets everything up
3️⃣ Focus any text field
4️⃣ Hold hotkey, speak, release
5️⃣ ✨ Text appears!

Literally anywhere you can type.
```

### Tweet 4 (Models)

```
Choose your AI model:

🐦 Parakeet - Fast, works on CPU
🐤 Canary - Includes translation
🦜 Voxtral - Highest accuracy (GPU)
🗣️ faster-whisper - Lightweight options

Auto-detects your hardware and recommends the best model.
```

### Tweet 5 (CTA)

```
Ready to type less and speak more?

🔗 github.com/blakkd/faster-whisper-hotkey

⭐ Star on GitHub
🐛 Report issues
💬 Join discussions

#OpenSource #Python #VoiceToText
```

---

## LinkedIn Post Template

```
I'm excited to announce the release of faster-whisper-hotkey v{VERSION}!

{INTRO_PARAGRAPH}

## What's New

{NEW_FEATURES}

## Why It Matters

- Works literally anywhere you can type—terminal, editors, browsers, games
- 25+ languages supported with automatic detection
- CPU or GPU with automatic hardware detection
- 100% private—all transcription happens locally on your machine

Perfect for developers, content creators, and anyone who wants to reduce typing strain.

## Download

Windows Installer (no Python required): github.com/blakkd/faster-whisper-hotkey

Open source and free to use. Would love to hear your feedback!

#VoiceToText #Transcription #DeveloperTools #Productivity #OpenSource #Python
```

---

## Discord/Community Announcement Template

```
@everyone 🎤 faster-whisper-hotkey v{VERSION} released!

**What is it?**
A push-to-talk transcription tool that works anywhere you can type. Hold hotkey, speak, release, and text appears instantly.

**What's new in v{VERSION}:**
{NEW_FEATURES}

**Download:**
- Windows: github.com/blakkd/faster-whisper-hotkey/releases
- PyPI: pip install faster-whisper-hotkey

**Quick Start:**
1. Download installer
2. Run setup wizard (auto-detects hardware)
3. Press your hotkey and speak!

Check it out and let me know what you think!
```

---

## Email Newsletter Template

### Subject
```
faster-whisper-hotkey v{VERSION}: {FEATURE_HIGHLIGHT}
```

### Body

```markdown
Hi [Name],

faster-whisper-hotkey v{VERSION} is now available!

## What's New

{NEW_FEATURES}

## Quick Install

**Windows (Recommended)**
Download the installer - no Python required:
[Download v{VERSION}](https://github.com/blakkd/faster-whisper-hotkey/releases/latest)

**From PyPI**
```bash
pip install --upgrade faster-whisper-hotkey
```

## Featured Feature

[Highlight one major feature with a brief explanation]

## Community

- 🐛 [Report bugs](https://github.com/blakkd/faster-whisper-hotkey/issues)
- 💡 [Request features](https://github.com/blakkd/faster-whisper-hotkey/discussions)
- ⭐ [Star on GitHub](https://github.com/blakkd/faster-whisper-hotkey)

Thanks for using faster-whisper-hotkey!

Best,
The faster-whisper-hotkey team
```

---

## Changelog Generation

Use this script snippet to generate changelog from git commits:

```bash
# Get commits since last tag
git log v{PREVIOUS_VERSION}..HEAD --pretty=format:"- %s" --reverse

# Or using the release notes from build
cat RELEASE_NOTES.md
```

---

## Milestone Release Template

For major versions (e.g., v1.0.0, v2.0.0), use this enhanced template:

```markdown
# 🎉 faster-whisper-hotkey v{MAJOR_VERSION}: {MILESTONE_NAME}

## 🌟 A Major Milestone

{MILESTONE_INTRO}

## 📊 By The Numbers

- {COMMITS} commits
- {FILES_CHANGED} files changed
- {CONTRIBUTORS} contributors
- {ISSUES_CLOSED} issues closed
- {FEATURES_ADDED} new features

## 🎯 What's New

### Headline Features
{HEADLINE_FEATURES}

### Improvements
{IMPROVEMENTS}

## 🎥 Demo Video

[Link to demo video]

## 📚 Full Documentation

[Link to updated documentation]

## 🙏 Special Thanks

{SPECIAL_THANKS}

## 🔮 What's Next

{ROADMAP_PREVIEW}

---
```

---

## Pre-Release Checklist

Before announcing:

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog written
- [ ] Release notes generated
- [ ] Assets uploaded to GitHub
- [ ] PyPI version published
- [ ] Tag pushed to GitHub
- [ ] GitHub release created
- [ ] Screenshots/videos prepared
- [ ] Social media posts drafted
- [ ] Announcement scheduled

---

## Post-Release Tasks

After announcing:

- [ ] Monitor for issues
- [ ] Respond to comments/feedback
- [ ] Track download metrics
- [ ] Update documentation with FAQs
- [ ] Plan next iteration

---

## Platform-Specific Notes

### GitHub
- Use semantic versioning tags (v1.0.0)
- Include all assets
- Write detailed release notes
- Link to relevant issues/PRs

### Reddit
- Follow subreddit rules
- Use appropriate flairs
- Engage with comments

### Twitter/X
- Use relevant hashtags
- Tag relevant accounts (@PyPI, @pythonetc, etc.)
- Consider pinning the thread

### LinkedIn
- Include professional context
- Tag relevant connections
- Link to full article/demo

---

## Hashtags

Use these hashtags for social media posts:

`#VoiceToText #Transcription #SpeechRecognition #ASR #Python #OpenSource #DeveloperTools #Productivity #Accessibility #Dictation #PushToTalk #Windows #GitHub`

---

## Images to Include

1. App logo/icon
2. Screenshot of main interface
3. Demo GIF (hotkey → speak → release)
4. Feature comparison chart
5. Download statistics (if applicable)

---

## Template Variables

Replace these placeholders when using the template:

| Variable | Description |
|----------|-------------|
| `{VERSION}` | Current version (e.g., 1.0.0) |
| `{PREVIOUS_VERSION}` | Previous version |
| `{SHORT_DESCRIPTION}` | One-line feature summary |
| `{HIGHLIGHT_FEATURES}` | Top 2-3 new features |
| `{MAIN_FEATURE_HIGHLIGHT}` | Single headline feature |
| `{NEW_FEATURES}` | Full list of new features |
| `{FEATURE_LIST}` | All features in this release |
| `{BUG_FIX_LIST}` | All bug fixes |
| `{TECHNICAL_CHANGES}` | Technical updates |
| `{DOCUMENTATION_UPDATES}` | Documentation changes |
| `{FULL_CHANGELOG}` | Complete changelog |
| `{MILESTONE_NAME}` | Major release name |
| `{COMMITS}` | Commit count |
| `{CONTRIBUTORS}` | Contributor count |
