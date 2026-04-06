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
    <a href="#-quick-start">🚀 Install</a> •
    <a href="#-features">✨ Features</a> •
    <a href="#-usage">💻 Usage</a> •
    <a href="#-architecture">🏗️ Architecture</a> •
    <a href="#-contributing">🤝 Contribute</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-blue?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40NzcgMiAyIDYuNDc3IDIgMTJzNC40NzcgMTAgMTAgMTAgMTAtNC40NzcgMTAtMTBTMTcuNTIzIDIgMTIgMnptMCAxOGMtNC40MTggMC04LTMuNTgyLTgtOHMzLjU4Mi04IDgtOCA4IDMuNTgyIDggOC0zLjU4MiA4LTggOHoiLz48L3N2Zz4=" alt="Platform Support" />
    <img src="https://img.shields.io/github/license/bitgineer/speakeasy?style=flat-square&color=green" alt="License MIT" />
    <img src="https://img.shields.io/badge/privacy-100%25%20local-success?style=flat-square" alt="Privacy First" />
    <img src="https://img.shields.io/badge/ai-whisper%20%7C%20nemo%20%7C%20voxtral-purple?style=flat-square" alt="AI Models" />
    <img src="https://img.shields.io/github/stars/bitgineer/speakeasy?style=flat-square&color=yellow" alt="GitHub Stars" />
    <img src="https://img.shields.io/badge/vibe%20coding-ready-orange?style=flat-square" alt="Vibe Coding" />
    <img src="https://github.com/bitgineer/speakeasy/workflows/Tests/badge.svg" alt="Tests" />
  </p>
</div>

---

## 📖 Overview

**SpeakEasy** is an open-source, privacy-focused **voice-to-text** and **speech recognition** application built for developers, writers, and privacy-conscious users. Unlike cloud-based transcription services like Otter.ai, Rev.ai, or Google Speech-to-Text, SpeakEasy runs **entirely offline** on your local machine using open-source AI models including **OpenAI Whisper**, **NVIDIA NeMo**, and **Mistral Voxtral**.

- 🎙️ **Real-time transcription** with near-zero latency
- 🔒 **100% offline** - no internet required, no data leaves your device
- ⚡ **GPU accelerated** - CUDA support for NVIDIA graphics cards
- 💻 **Cross-platform** - Windows, macOS, and Linux support
- 🚀 **Vibe Coding** - Stay in flow, dictate code naturally
- 🎯 **Developer-first** - IDE integration, hotkeys, CLI support

### Why Choose SpeakEasy?

| 🏆 **Best For** | 💡 **Why** |
|----------------|-----------|
| **Developers** | Code faster with voice. Global hotkeys work in any IDE (VS Code, Cursor, JetBrains) |
| **Privacy Advocates** | Zero cloud calls. Your voice stays on your machine |
| **Writers** | Dictate articles, emails, notes without typing fatigue |
| **Accessibility** | Voice control for users with RSI, disabilities, or typing limitations |
| **Security-Conscious** | Air-gapped environments, no data exfiltration risk |

## ✨ Features

### 🎙️ Core Transcription

| Feature | Description |
|---------|-------------|
| **Global Hotkey** | Press and hold to transcribe into any active window |
| **Universal Compatibility** | Works with any application (IDEs, editors, browsers, chat apps) |
| **Smart Formatting** | Automatic punctuation, capitalization, and code formatting |
| **Multi-Model Support** | Choose between Whisper, NeMo, or Voxtral based on your needs |
| **Audio File Processing** | Batch transcribe MP3, WAV, M4A, and more |
| **Real-time Preview** | See transcription as you speak |

### 🔐 Privacy & Security

- ✅ **100% Offline** - Zero network calls for transcription
- ✅ **Local Processing** - All models run on your hardware
- ✅ **No Signup** - No account, email, or API keys required
- ✅ **No Telemetry** - No usage tracking or data collection
- ✅ **Open Source** - Full transparency, audit the code

### ⚡ Power Features

- **Batch Transcription**: Process multiple audio files in a queue with real-time progress tracking
- **Transcription History**: Searchable SQLite database of all your transcriptions
- **History Import/Export**: Backup and restore your history with merge or replace options
- **Export Formats**: JSON, TXT, SRT, VTT, CSV, DOCX for different use cases
- **Model Download Progress**: Real-time download tracking with speed and ETA
- **Model Caching**: Download and cache models for faster startup times
- **Custom Hotkeys**: Configure global shortcuts to your preference
- **System Tray**: Quick access without cluttering your dock
- **CLI Support**: Command-line transcription for automation
- **Plugin System**: Custom post-processing scripts (WIP)

## 🚀 Quick Start

### Prerequisites

- **Python 3.10 - 3.12** (Python 3.13+ not yet supported)
- **Node.js 18+** (LTS recommended)
- **FFmpeg** (must be in system PATH)
- **UV** package manager (`pip install uv`)
- **Windows**: Visual C++ Build Tools

### ⚡ One-Command Install

**Windows (Recommended)**:
```bash
git clone https://github.com/bitgineer/speakeasy.git
cd speakeasy
start.bat
```

**macOS/Linux**:
```bash
git clone https://github.com/bitgineer/speakeasy.git
cd speakeasy
./start.sh
```

### 🛠️ Manual Setup

```bash
# Clone repository
git clone https://github.com/bitgineer/speakeasy.git
cd speakeasy

# Setup backend
cd backend
uv venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[cuda]"  # Without CUDA: uv pip install -e .

# Run tests
uv run pytest tests/ -v

# Setup frontend
cd ../gui
npm install
npm run dev
```

## 💻 Usage

### 🖱️ GUI Mode (Desktop App)

The easiest way to use SpeakEasy is through the Electron GUI:

```bash
# Quick start with default settings
npm run dev        # Development mode
npm run build      # Production build
npm run start      # Run built app
```

**Features:**
- Visual transcription history
- Model switching (Whisper/NeMo/Voxtral)
- Settings management
- Audio file import

### ⌨️ CLI Mode (Command Line)

Use SpeakEasy from the terminal for automation and scripting:

```bash
# Transcribe with default settings
python -m speakeasy transcribe

# Transcribe an audio file
python -m speakeasy transcribe --file recording.mp3 --output transcript.txt

# List available models
python -m speakeasy models

# Use specific model
python -m speakeasy transcribe --model whisper-large-v3

# Batch process directory
python -m speakeasy transcribe --batch ./audio_files/ --output ./transcripts/

# Get help
python -m speakeasy --help
python -m speakeasy transcribe --help
```

### 🔥 Global Hotkey Mode

Set up a global hotkey to transcribe into any active window:

1. **Start the backend**:
   ```bash
   cd backend
   source .venv/bin/activate
   python -m speakeasy.server
   ```

2. **Configure hotkey** in the GUI (default: `Ctrl+Shift+Space`)

3. **Use anywhere**:
   - Hold hotkey → Speak → Release → Text appears in focused window

### 🎙️ Live Mode

Stream transcription in real-time:

```bash
# Real-time transcription to stdout
python -m speakeasy live

# Real-time with specific model
python -m speakeasy live --model nemo --language en

# Save to file while transcribing
python -m speakeasy live --output live_transcript.txt
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                        │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │  Electron GUI │  │    CLI Tool   │  │  Global Hotkey  │ │
│  │   (React)     │  │  (Python)     │  │   (Listener)    │ │
│  └───────┬───────┘  └───────┬───────┘  └────────┬────────┘ │
└──────────┼──────────────────┼──────────────────┼──────────┘
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     SPEAKEASY BACKEND                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   FastAPI Server │  │  Audio Processor │                │
│  │   (Python)       │  │  (FFmpeg/Buffer) │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                     │                          │
│           └───────────┬─────────┘                          │
│                       │ Load & Run                         │
│           ┌───────────▼───────────┐                       │
│           │    AI Model Engine    │                       │
│           │  (CTranslate2/ONNX)   │                       │
│           └───────────┬───────────┘                       │
│                       │                                   │
│           ┌───────────▼───────────┐                       │
│           │  ┌─────┐ ┌─────┐ ┌──┐ │                       │
│           │  │Whis │ │NeMo │ │Vox│ │                       │
│           │  │per  │ │     │ │tral│                       │
│           │  └─────┘ └─────┘ └──┘ │                       │
│           └───────────────────────┘                       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA STORAGE                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   SQLite DB      │  │   Model Cache    │                │
│  │  (History/Config)│  │  (~2-10GB each)  │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

**Tech Stack**:
- **Frontend**: Electron + React + Tailwind CSS + TypeScript
- **Backend**: Python + FastAPI + WebSocket
- **AI Engine**: PyTorch, CTranslate2, ONNX Runtime
- **Audio**: FFmpeg, PyAudio, SoundDevice
- **Database**: SQLite with full-text search

## 🤖 Supported Models

| Model | Size | Speed | Accuracy | Best For | Hardware |
|-------|------|-------|----------|----------|----------|
| **Whisper Tiny** | 39MB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Quick tests, low-resource | CPU |
| **Whisper Base** | 74MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Balanced speed/accuracy | CPU |
| **Whisper Small** | 244MB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Good general use | CPU/GPU |
| **Whisper Medium** | 769MB | ⚡⚡ | ⭐⭐⭐⭐⭐ | High accuracy | GPU recommended |
| **Whisper Large-v3** | 1.5GB | ⚡ | ⭐⭐⭐⭐⭐ | Best accuracy | GPU required |
| **NeMo FastConformer** | 110MB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Real-time streaming | GPU recommended |
| **Voxtral Mini** | 3B | ⚡ | ⭐⭐⭐⭐⭐ | Complex dictation | GPU required |
| **Voxtral Large** | 7B | ⚡ | ⭐⭐⭐⭐⭐ | Maximum accuracy | High-end GPU |

## 🆚 Alternatives Comparison

| Feature | SpeakEasy | Otter.ai | Whisper API | Dragon | Apple Dictation |
|---------|-----------|----------|-------------|--------|-----------------|
| **Privacy** | ✅ 100% offline | ❌ Cloud only | ❌ Cloud only | ❌ Cloud required | ⚠️ Cloud optional |
| **Cost** | 🆓 Free | 💰 $10-20/mo | 💰 $0.006/min | 💰 $500+ | 🆓 Free |
| **Open Source** | ✅ Yes | ❌ No | ✅ Yes (API only) | ❌ No | ❌ No |
| **Offline** | ✅ Yes | ❌ No | ❌ No | ⚠️ Limited | ⚠️ Limited |
| **Cross-Platform** | ✅ Win/Mac/Linux | ✅ Yes | N/A | ❌ Windows only | ❌ Apple only |
| **Custom Models** | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |
| **Latency** | 🟢 <100ms | 🟡 ~1s | 🟡 ~500ms | 🟢 <200ms | 🟡 ~300ms |

## 🗺️ Roadmap

### Current (v0.1.0)
- [x] Local Whisper transcription
- [x] Electron GUI
- [x] Global hotkeys
- [x] CLI interface
- [x] Multi-model support (Whisper, NeMo, Voxtral)
- [x] Audio file processing
- [x] Batch transcription
- [x] History import/export
- [x] Model download progress tracking
- [x] Real-time WebSocket updates
- [x] Advanced export formats (SRT, VTT, CSV, DOCX)

### Near-term (v0.2.0)
- [ ] VS Code extension
- [ ] Custom wake words
- [ ] Voice commands (beyond transcription)
- [ ] Plugin system
- [ ] Docker deployment

### Future (v1.0.0)
- [ ] Mobile companion app
- [ ] Web interface
- [ ] Enterprise features (SSO, audit logs)
- [ ] Real-time collaboration

See [GitHub Issues](https://github.com/bitgineer/speakeasy/issues) for detailed backlog.

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- 🐛 Reporting bugs and requesting features
- 🛠️ Setting up your development environment
- 📝 Code style and submission process
- 👀 Review and approval workflow

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [NVIDIA NeMo](https://github.com/NVIDIA/NeMo) - Speech AI toolkit
- [Mistral AI](https://mistral.ai/) - Voxtral models
- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper) - Optimized inference
- [CTranslate2](https://github.com/OpenNMT/CTranslate2) - Fast inference engine

---

<div align="center">
  <p>
    <b>⭐ Star this repo if you find it useful!</b>
  </p>
  <p>
    <a href="https://github.com/bitgineer/speakeasy/issues">🐛 Report Bug</a> •
    <a href="https://github.com/bitgineer/speakeasy/issues">💡 Request Feature</a> •
    <a href="https://github.com/bitgineer/speakeasy/discussions">💬 Discussions</a>
  </p>
  <p>
    <sub>Made with ❤️ for privacy-conscious developers everywhere</sub>
  </p>
</div>
