# SpeakEasy

<div align="center">
  <img src="docs/images/logo.png" alt="SpeakEasy Logo" width="120" height="120" />
  <h1>SpeakEasy</h1>
  <h3>Privacy-First Voice-to-Text for Developers</h3>
  <p>
    Local AI transcription that runs 100% offline. Code at the speed of thought.<br/>
    <b>Private. Open Source. No Cloud Required.</b>
  </p>
  
  <p align="center">
    <a href="#-quick-start">Install</a> •
    <a href="#-features">Features</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-contributing">Contribute</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-blue?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40NzcgMiAyIDYuNDc3IDIgMTJzNC40NzcgMTAgMTAgMTAgMTAtNC40NzcgMTAtMTBTMTcuNTIzIDIgMTIgMnptMCAxOGMtNC40MTggMC04LTMuNTgyLTgtOHMzLjU4Mi04IDgtOCA4IDMuNTgyIDggOC0zLjU4MiA4LTggOHoiLz48L3N2Zz4=" alt="Platform Support" />
    <img src="https://img.shields.io/github/license/razing/speakeasy?style=flat-square&color=green" alt="License MIT" />
    <img src="https://img.shields.io/badge/privacy-100%25%20local-success?style=flat-square" alt="Privacy First" />
    <img src="https://img.shields.io/badge/ai-whisper%20%7C%20nemo%20%7C%20voxtral-purple?style=flat-square" alt="AI Models" />
    <img src="https://img.shields.io/github/stars/razing/speakeasy?style=flat-square&color=yellow" alt="GitHub Stars" />
  </p>
</div>

---

## Overview

**SpeakEasy** is an open-source, privacy-focused voice-to-text application built for developers, writers, and privacy-conscious users. Unlike cloud-based transcription services like Otter.ai or Rev.ai, SpeakEasy runs entirely on your local machine using open-source AI models like **OpenAI Whisper**, **NVIDIA NeMo**, and **Mistral Voxtral**.

- 🎙️ **Real-time transcription** with near-zero latency
- 🔒 **100% offline** - no internet required, no data leaves your device
- ⚡ **GPU accelerated** - CUDA support for NVIDIA graphics cards
- 💻 **Cross-platform** - Windows, macOS, and Linux

## Why SpeakEasy?

**Privacy First**: Your voice data never leaves your computer. No API keys, no cloud uploads, no privacy concerns.

**Open Source**: Fully transparent codebase. No hidden telemetry or data collection.

**Developer-Friendly**: Works seamlessly with VS Code, Cursor, Obsidian, Slack, and any application that accepts text input.

**Vibe Coding Ready**: Stay in your creative flow. Dictate code, comments, documentation, and ideas without breaking concentration.

## Features

### Core Transcription

| Feature | Description |
|---------|-------------|
| **Global Hotkey** | Press and hold to transcribe into any active window |
| **Universal Compatibility** | Works with any application (IDEs, editors, browsers, chat apps) |
| **Smart Formatting** | Automatic punctuation, capitalization, and formatting |
| **Multi-Model Support** | Choose between Whisper, NeMo, or Voxtral based on your needs |
| **Audio File Processing** | Batch transcribe MP3, WAV, M4A, and more |

### Privacy & Security

- ✅ Zero network calls for transcription
- ✅ Local model storage and inference
- ✅ No account or signup required
- ✅ No usage tracking or telemetry

### Power Features

- **Transcription History**: Searchable database of all your transcriptions
- **Export Options**: JSON, TXT, SRT, VTT, CSV formats
- **Custom Hotkeys**: Configure global shortcuts to your preference
- **System Tray Integration**: Quick access without cluttering your dock

## Quick Start

### Prerequisites

- **Python 3.10 - 3.12** (Python 3.13+ not yet supported)
- **Node.js 18+** (LTS)
- **FFmpeg** (must be in system PATH)
- **UV** package manager (recommended)
- **Windows**: Visual C++ Build Tools

### Installation

**Windows (Automatic)**:
```bash
git clone https://github.com/bitgineer/speakeasy.git
cd speakeasy
install.bat
```

**Manual Setup**:

```bash
# Clone repository
git clone https://github.com/bitgineer/speakeasy.git
cd speakeasy

# Setup backend
cd backend
uv venv --python 3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[cuda]"  # Or without CUDA: uv pip install -e .

# Setup frontend
cd ../gui
npm install
npm run dev
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Electron UI   │◄───►│   Python API     │◄───►│   AI Models     │
│   (React)       │     │   (FastAPI)      │     │   (Whisper/etc) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   SQLite DB      │
                        │   (History)      │
                        └──────────────────┘
```

**Tech Stack**:
- **Frontend**: Electron + React + Tailwind CSS
- **Backend**: Python + FastAPI
- **AI**: PyTorch, CTranslate2, ONNX Runtime
- **Database**: SQLite

## Supported Models

| Model | Use Case | Hardware |
|-------|----------|----------|
| **OpenAI Whisper** | General purpose, high accuracy | CPU/GPU |
| **NVIDIA NeMo** | Real-time, ultra-low latency | GPU recommended |
| **Mistral Voxtral** | Complex dictation, long-form | GPU required |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Reporting bugs and requesting features
- Setting up your development environment
- Code style and submission process
- Review and approval workflow

## Roadmap

- [ ] VS Code extension
- [ ] Custom wake words
- [ ] Voice commands (beyond transcription)
- [ ] Mobile companion app
- [ ] Plugin system for custom post-processing

See [GitHub Issues](https://github.com/razing/speakeasy/issues) for detailed backlog.

## Alternatives Comparison

| Feature | SpeakEasy | Otter.ai | Whisper API | Dragon |
|---------|-----------|----------|-------------|--------|
| **Privacy** | ✅ 100% offline | ❌ Cloud only | ❌ Cloud only | ❌ Cloud required |
| **Cost** | Free | $10-20/mo | $0.006/min | $500+ |
| **Open Source** | ✅ Yes | ❌ No | ✅ Yes (API) | ❌ No |
| **Local Models** | ✅ Yes | ❌ No | ❌ No | ⚠️ Limited |
| **Cross-Platform** | ✅ Yes | ✅ Yes | N/A | ❌ Windows only |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [NVIDIA NeMo](https://github.com/NVIDIA/NeMo) - Speech AI toolkit
- [Mistral AI](https://mistral.ai/) - Voxtral models
- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper) - Optimized inference

---

<div align="center">
  <p>
    <b>Star ⭐ this repo if you find it useful!</b>
  </p>
  <p>
    <a href="https://github.com/bitgineer/speakeasy/issues">Report Bug</a> •
    <a href="https://github.com/bitgineer/speakeasy/issues">Request Feature</a> •
    <a href="https://github.com/bitgineer/speakeasy/discussions">Discussions</a>
  </p>
</div>
