# Developer Guide: faster-whisper-hotkey

This guide covers everything new developers need to contribute to the faster-whisper-hotkey project.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Environment Setup](#environment-setup)
3. [Development Workflow](#development-workflow)
4. [Code Structure](#code-structure)
5. [Common Tasks](#common-tasks)
6. [Testing Conventions](#testing-conventions)
7. [Troubleshooting](#troubleshooting)

---

## Project Overview

**faster-whisper-hotkey** is a push-to-talk transcription tool that converts speech to text using various ASR models (Whisper, Parakeet, Canary, Voxtral). It features:

- Cross-platform support (Linux, Windows, macOS)
- Both CLI and GUI interfaces
- System tray integration
- Multiple transcription engine backends
- Hotkey-based activation (hold or toggle mode)

### Architecture

The application follows a modular architecture:

```
src/faster_whisper_hotkey/
├── __main__.py          # Entry point, dispatches to wizard
├── cli.py               # CLI interface with subcommands
├── gui.py               # GUI application with system tray
├── transcriber.py       # Core transcription engine
├── models.py            # ASR model abstraction layer
├── settings.py          # Configuration management
├── clipboard.py         # Clipboard operations
├── paste.py             # Platform-specific paste handling
├── terminal.py          # Terminal window detection
├── config.py            # Model and language config
├── hotkey_dialog.py     # Hotkey configuration dialog
├── history_panel.py     # Transcription history viewer
├── shortcuts_panel.py   # Shortcuts configuration UI
├── shortcuts_manager.py # Keyboard shortcuts management
└── onboarding.py        # Interactive tutorial overlay
```

---

## Environment Setup

### Prerequisites

- **Python**: 3.10 or higher
- **OS**: Linux (primary), Windows (in development), macOS (basic support)
- **Git**: For version control

### Platform-Specific Requirements

#### Linux

```bash
# System dependencies for audio
sudo apt-get install portaudio19-dev python3-pyaudio

# For PulseAudio control (optional, for advanced audio routing)
sudo apt-get install libpulse-dev
```

#### Windows

```powershell
# No special system dependencies required
# The project uses windows-curses for CLI compatibility
```

#### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install portaudio
brew install portaudio
```

### Installation Methods

#### Method 1: UV (Recommended)

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/faster-whisper-hotkey.git
cd faster-whisper-hotkey

# Create virtual environment and install in editable mode
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

#### Method 2: pip

```bash
# Clone the repository
git clone https://github.com/yourusername/faster-whisper-hotkey.git
cd faster-whisper-hotkey

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Development Dependencies

```bash
# Install development tools
uv pip install ruff pytest pytest-cov mypy

# Or with pip
pip install ruff pytest pytest-cov mypy
```

### Verify Installation

```bash
# Run the CLI
faster-whisper-hotkey --help

# Run the GUI (requires display)
faster-whisper-hotkey-gui --help

# Check Python path
which python  # Should point to your virtual environment
```

---

## Development Workflow

### Git Workflow

1. **Main Branch**: `main` - stable releases
2. **Feature Branches**: `feature/*` - new features
3. **Fix Branches**: `fix/*` - bug fixes
4. **Docs Branches**: `docs/*` - documentation updates

#### Creating a Feature Branch

```bash
# Start from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: description of your feature"

# Push and create PR
git push origin feature/your-feature-name
```

#### Commit Message Convention

Follow conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks

Examples:
```bash
git commit -m "feat: add Voxtral model support"
git commit -m "fix: resolve audio device enumeration on Windows"
git commit -m "docs: update installation instructions for macOS"
```

### Code Style

The project uses **ruff** for linting:

```bash
# Check code style
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

#### Configuration

The project ignores E402 (import not at top) in `pyproject.toml`:
```toml
[tool.ruff.lint]
ignore = ["E402"]
```

This allows dynamic imports needed for platform-specific code.

---

## Code Structure

### Core Components

#### 1. Transcriber (`transcriber.py`)

The main engine that handles:
- Audio recording from selected device
- Hotkey detection (pynput)
- Circular audio buffer (10 minutes max)
- Model inference triggering
- Result delivery to clipboard

**Key Classes:**
- `Transcriber`: Main class orchestrating the transcription pipeline

#### 2. Models (`models.py`)

Abstraction layer for different ASR engines:

**Key Classes:**
- `Model`: Base class for all models
- `WhisperModel`: faster-whisper implementation
- `NemoModel`: NVIDIA NeMo models (Parakeet, Canary)
- `VoxtralModel`: Mistral's Voxtral via transformers

#### 3. Settings (`settings.py`)

Configuration management with JSON persistence:

**Location:** `~/.config/faster_whisper_hotkey/transcriber_settings.json`

**Key Settings:**
- Audio device (name/index)
- Model type and name
- Language (or "auto" for detection)
- Compute device (cpu/cuda)
- Hotkey combination
- Activation mode (hold/toggle)

#### 4. CLI (`cli.py`)

Command-line interface with subcommands:

```bash
faster-whisper-hotkey wizard      # Interactive setup
faster-whisper-hotkey record      # One-shot recording
faster-whisper-hotkey transcribe  # Transcribe audio file
faster-whisper-hotkey settings    # View/edit settings
faster-whisper-hotkey history     # View transcription history
faster-whisper-hotkey batch       # Batch transcribe files
```

#### 5. GUI (`gui.py`)

System tray application:

**Key Classes:**
- `HotkeyTray`: Main GUI class
- `HistoryPanel`: Transcription history viewer
- `HotkeyDialog`: Hotkey configuration
- `ShortcutsPanel`: Shortcut management
- `OnboardingOverlay`: Interactive tutorial

---

## Common Tasks

### Adding a New ASR Model

1. **Create model class** in `models.py`:

```python
class YourModel(Model):
    def __init__(self, model_name: str, device: str, language: str = None):
        super().__init__(model_name, device, language)
        # Initialize your model

    def transcribe(self, audio: np.ndarray) -> str:
        # Implement transcription
        pass
```

2. **Register in `config.py`**:

```python
AVAILABLE_MODELS = {
    # ... existing models
    "your_model": {
        "class": YourModel,
        "models": ["small", "base"],
    },
}
```

3. **Update settings schema** if needed.

### Adding a New CLI Command

1. **Add subcommand** in `cli.py`:

```python
@app.command()
def your_command(arg: str = "default"):
    """Your command description."""
    # Implementation
    tycho.echo(f"Running with {arg}")
```

2. **Test locally**:

```bash
faster-whisper-hotkey your-command --arg value
```

### Adding GUI Components

1. **Create component file** (e.g., `your_panel.py`):

```python
from tkinter import ttk

class YourPanel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        # Build your UI
        pass
```

2. **Integrate in `gui.py`**:

```python
from .your_panel import YourPanel

# Add to tray menu or main window
```

### Platform-Specific Code

Use the `platform` module for conditional code:

```python
import platform

if platform.system() == "Linux":
    # Linux-specific code
    import pulsectl
elif platform.system() == "Windows":
    # Windows-specific code
    import windows_curses as curses
elif platform.system() == "Darwin":
    # macOS-specific code
    pass
```

For audio input:
```python
from .paste import get_input_devices
# Returns platform-appropriate device list
```

---

## Testing Conventions

### Current State

The project currently uses manual testing. A formal test suite is planned but not yet implemented.

### Manual Testing Checklist

When making changes, test:

1. **CLI Functionality:**
   ```bash
   faster-whisper-hotkey wizard
   faster-whisper-hotkey record
   faster-whisper-hotkey transcribe audio.wav
   ```

2. **GUI Functionality:**
   ```bash
   faster-whisper-hotkey-gui
   ```
   - Test system tray icon
   - Test hotkey activation
   - Test settings dialog
   - Test history panel

3. **Cross-Platform:**
   - Test on Linux (primary)
   - Test on Windows (if applicable)
   - Test on macOS (if applicable)

### Writing Tests (Planned)

When adding tests, use pytest:

```python
# tests/test_transcriber.py
import pytest
from faster_whisper_hotkey.transcriber import Transcriber

def test_transcriber_init():
    t = Transcriber()
    assert t is not None

def test_transcriber_with_settings():
    settings = {"model": "tiny", "language": "en"}
    t = Transcriber(settings)
    assert t.model == "tiny"
```

Run tests:
```bash
pytest tests/
pytest tests/ --cov=src/faster_whisper_hotkey
```

---

## Troubleshooting

### Headless Environments (SSH, Docker, CI)

#### Issue: No Display Available

GUI version requires a display server:

```
_tkinter.TclError: no display name and no $DISPLAY environment variable
```

**Solutions:**

1. **Use CLI version instead:**
   ```bash
   faster-whisper-hotkey --help
   # CLI works fine in headless environments
   ```

2. **Enable X11 forwarding (SSH):**
   ```bash
   ssh -X user@host
   faster-whisper-hotkey-gui
   ```

3. **Use VNC or RDP** for remote GUI access.

4. **Dummy X server for testing:**
   ```bash
   # Install Xvfb
   sudo apt-get install xvfb

   # Run with virtual display
   xvfb-run faster-whisper-hotkey-gui
   ```

#### Issue: Audio Device Not Found in Headless Environment

```
ValueError: No audio devices found
```

**Solutions:**

1. **Check available devices:**
   ```bash
   faster-whisper-hotkey settings
   # Look for "audio_device" option
   ```

2. **Specify device explicitly:**
   ```bash
   faster-whisper-hotkey record --device 0
   ```

3. **Set up virtual audio (Linux):**
   ```bash
   # Install PulseAudio dummy module
   sudo apt-get install pulseaudio
   pulseaudio --load=module-dummy
   ```

### Windows-Specific Issues

#### Issue: Curses Module Not Found

```
ModuleNotFoundError: No module named 'curses'
```

**Solution:**
```bash
pip install windows-curses
```

#### Issue: libpulse.so.0 Missing

```
ImportError: libpulse.so.0: cannot open shared object file
```

**Cause:** Trying to run Linux version on Windows.

**Solution:**
- Use the `feature/supportWindows` branch
- Or wait for Windows support to be merged to main
- Ensure you're installing Windows-specific dependencies:
  ```powershell
  pip install faster-whisper-hotkey[windows]
  ```

#### Issue: PyInstaller Build Fails on Windows

```
PyInstaller cannot check for assembly membership
```

**Solution:**
- Use `--onefile` flag
- Exclude unnecessary modules:
  ```bash
  pyinstaller --onefile --exclude-module tkinter src/__main__.py
  ```

### Linux-Specific Issues

#### Issue: Permission Denied on Audio Device

```
[Errno 13] Permission denied: '/dev/snd/...'
```

**Solution:**
```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Log out and back in for changes to take effect
```

#### Issue: PulseAudio Not Running

```
OSError: [Errno 2] Connection refused
```

**Solution:**
```bash
# Start PulseAudio
pulseaudio --start

# Or use system-wide PulseAudio
sudo systemctl start pulseaudio
```

### Model-Related Issues

#### Issue: Model Download Fails

```
HTTPError: 404 Not Found
```

**Solutions:**

1. **Check internet connection**
2. **Try different model size:**
   ```bash
   faster-whisper-hotkey settings --model tiny
   ```
3. **Clear cache and retry:**
   ```bash
   rm -rf ~/.cache/huggingface
   rm -rf ~/.cache/whisper
   ```

#### Issue: CUDA Out of Memory

```
RuntimeError: CUDA out of memory
```

**Solutions:**

1. **Use CPU instead:**
   ```bash
   faster-whisper-hotkey settings --device cpu
   ```

2. **Use smaller model:**
   ```bash
   faster-whisper-hotkey settings --model tiny
   ```

3. **Reduce batch size** (edit settings manually):
   ```json
   {
     "batch_size": 1
   }
   ```

### Hotkey Issues

#### Issue: Hotkey Not Responding

**Solutions:**

1. **Check for conflicts:**
   - Other apps using same hotkey
   - System shortcuts

2. **Try different hotkey:**
   ```bash
   faster-whisper-hotkey settings
   # Follow prompts to change hotkey
   ```

3. **Check permissions:**
   - macOS: Accessibility permissions
   - Linux: No special permissions needed
   - Windows: Run as administrator if needed

#### Issue: Toggle Mode Stuck

```
Toggle mode: ON (won't turn off)
```

**Solution:**
- Press hotkey again to toggle off
- If stuck, restart application:
  ```bash
  pkill -f faster-whisper-hotkey
  faster-whisper-hotkey-gui
  ```

### Clipboard Issues

#### Issue: Text Not Pasting Automatically

**Solutions:**

1. **Check paste method in settings:**
   ```json
   {
     "paste_method": "auto"  # or "ctrl_v", "middle_click"
   }
   ```

2. **Test clipboard manually:**
   ```bash
   # Transcribe something
   faster-whisper-hotkey record

   # Check if text is in clipboard
   xclip -o  # Linux
   clip < /dev/null  # Windows (PowerShell: Get-Clipboard)
   ```

3. **Focus issue**: Ensure target window has focus before hotkey press

---

## Getting Help

- **GitHub Issues**: [https://github.com/yourusername/faster-whisper-hotkey/issues](https://github.com/yourusername/faster-whisper-hotkey/issues)
- **Documentation**: See [README.md](README.md) for user-facing docs
- **Code Comments**: Source files have docstrings for key functions

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (when test suite is ready)
5. Run linting: `ruff check --fix .`
6. Submit a pull request

### Code Review Guidelines

- Keep changes focused and atomic
- Update documentation for new features
- Follow existing code style and patterns
- Test on at least one platform (Linux preferred)
- For cross-platform changes, test on all supported platforms
