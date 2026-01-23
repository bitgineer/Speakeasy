# faster-whisper-hotkey: Modernization Auto Run Playbook

## Project Overview

**faster-whisper-hotkey** is a push-to-talk speech-to-text transcription tool using state-of-the-art ASR models. This playbook guides the transformation from a clunky CLI application into a polished, modern Windows-first application ready for mass adoption.

### Current State

- CLI-based with multiple incomplete GUI implementations (tkinter, PyQt6)
- Complex installation requiring Python environment management
- Cross-platform (Linux-primary) but Windows support exists
- Powerful backend but rough user experience
- Many bugs and configuration issues

### Target State

- Modern Flet-based GUI with Windows Fluent Design aesthetic
- Single .exe installer - no Python dependencies for end users
- Automatic CUDA detection and optimal configuration
- Push-to-talk transcription with visual feedback
- Model management with on-demand downloading
- Searchable transcription history with slash commands
- Intelligent auto-paste to active window
- Polished, professional user experience

## Auto Run Phases

Each phase is designed to be executed autonomously by an AI coding assistant. Phase 1 delivers a working prototype - subsequent phases add features and polish.

| Phase | Title | Deliverable |
|-------|-------|-------------|
| 1 | Foundation and Working Prototype | Working Flet app with push-to-talk transcription |
| 2 | History, Search, and Auto-Paste | Searchable history + intelligent paste to active window |
| 3 | Model Management and Auto-Detection | CUDA detection + on-demand model downloads |
| 4 | UI Polish and Modern Design | Theme system + animations + refined UX |
| 5 | Windows Installer and Distribution | Single .exe installer + auto-updates |
| 6 | Testing, Bug Fixes, and Refinement | Comprehensive testing + bug fixes + optimization |

## Execution Guide

### For the AI Assistant

1. **Start with Phase 1** - It must complete entirely before moving on
2. **Follow tasks in order** - Each phase builds on previous work
3. **Write files as you complete them** - Don't batch all writes at the end
4. **Read before modifying** - Always read a file before editing it
5. **Ask when uncertain** - Use the AskUserQuestion tool if clarification is needed

### Critical Requirements

- **Phase 1 is autonomous** - No user input should be required during execution
- **Phase 1 must work** - By end of Phase 1, there should be something runnable
- **Preserve backend logic** - Keep `transcriber.py`, `models.py`, `settings.py`, etc.
- **Replace UI only** - Discard tkinter, PyQt6 GUIs; build new Flet UI

## Preserved Backend Modules

These core modules should be preserved and wrapped for Flet integration:

- `transcriber.py` - Core transcription engine
- `transcribe.py` - Setup wizard and model configuration
- `models.py` - Model management
- `settings.py` - Configuration persistence
- `shortcuts_manager.py` - Hotkey system
- `clipboard.py` - Clipboard operations
- `paste.py` - Text insertion
- `app_detector.py` - Window/application detection
- `config.py` - Model configurations
- `text_processor.py` - Text processing pipeline
- `app_rules_manager.py` - Per-app settings

## Discarded UI Modules

These will be replaced entirely by the Flet GUI:

- `gui.py` - Legacy tkinter GUI
- `gui_modern.py` - Modern system tray GUI
- `gui_qt/` - PyQt6 GUI components
- `ui.py` - Terminal UI
- `*_panel.py` - All UI panels
- `*_dialog.py` - All UI dialogs
- `*_overlay.py` - All UI overlays

## Technology Stack

- **GUI**: Flet (Python, Flutter-style)
- **Backend**: Existing Python transcription engine
- **ASR Models**: faster-whisper, NeMo (Parakeet/Canary), Mistral (Voxtral)
- **Packaging**: PyInstaller + NSIS for Windows installer

## MVP Feature Scope

Phase 1-2 deliver the essential MVP:

1. Push-to-talk transcription
2. Model selection & switching
3. Hotkey configuration
4. Auto-paste to active window
5. Searchable history (slash search)

## Getting Started

Execute the phases sequentially:

```
Phase-01-Foundation-and-Working-Prototype.md
Phase-02-History-Search-and-Auto-Paste.md
Phase-03-Model-Management-and-Auto-Detection.md
Phase-04-UI-Polish-and-Modern-Design.md
Phase-05-Windows-Installer-and-Distribution.md
Phase-06-Testing-Bug-Fixes-and-Refinement.md
```

Each phase document contains detailed tasks that guide the AI assistant through implementation.

## Notes

- All Auto Run documents are in `Auto Run Docs/Initiation/`
- Working files go in `Auto Run Docs/Initiation/Working/`
- This is a Windows-first release; Linux support can be added later
- The goal is mass adoption - UX simplicity is paramount
