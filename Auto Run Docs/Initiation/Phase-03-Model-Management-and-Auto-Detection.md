# Phase 03: Model Management and Hardware Auto-Detection

This phase streamlines the model and hardware experience by implementing automatic CUDA detection, on-demand model downloading, and a modern model management interface. This eliminates configuration friction for mass-market users.

## Goals

- Auto-detect CUDA/GPU availability and configure optimal settings automatically
- Implement on-demand model downloading with progress visualization
- Create a modern model management interface for browsing, selecting, and managing models
- Handle model updates and caching transparently

## Tasks

- [x] Implement hardware detection system:
  - Create `src/faster_whisper_hotkey/flet_gui/hardware_detector.py`:
    - Detect NVIDIA GPU presence using `torch.cuda.is_available()`
    - Query GPU details: name, VRAM, compute capability
    - Determine optimal compute type based on hardware (float16 for GPU, int8 for CPU)
    - Detect CPU capabilities (AVX, AVX2, etc.) for optimization hints
    - Return a recommended configuration profile
  - Create detection result display showing:
    - GPU status (Detected: RTX 3080 / Not Detected)
    - Recommended settings (Device: CUDA, Compute: float16)
    - VRAM availability and model size recommendations

- [x] Create model download manager with progress tracking:
  - Create `src/faster_whisper_hotkey/flet_gui/model_download.py`:
    - Integrate with existing `models.py` for HuggingFace downloads
    - Implement download progress callbacks (percentage, speed, ETA)
    - Add pause/resume capability for large downloads
    - Show download queue for multiple models
    - Implement checksum verification for downloaded models
    - Handle download errors with retry logic
    - Cache downloaded models with version tracking
  - Create download progress UI component:
    - Progress bar with percentage
    - Download speed and remaining time display
    - Cancel button
    - Background download support (minimize doesn't stop download)

- [x] Build the model management interface:
  - Create `src/faster_whisper_hotkey/flet_gui/views/model_manager.py`:
    - Grid layout showing all available models with cards:
      - Model name and description
      - Size (download size, memory requirement)
      - Supported languages
      - Features (transcription, translation, auto-language-detect)
      - Current status (Installed, Not Installed, Update Available)
      - Download/Install/Update/Remove buttons
    - Model detail view when clicking a model card:
      - Full description and technical details
      - Performance benchmarks (transcription speed)
      - Language support list
      - Recommended hardware
      - Changelog/version history
    - Filter and sort options (by size, speed, language support)
    - "Recommended for your system" badge based on hardware detection

- [x] Implement automatic model selection:
  - Create `src/faster_whisper_hotkey/flet_gui/model_selector.py`:
    - Smart recommendation engine that selects optimal model based on:
      - Available VRAM
      - User's language preference
      - Whether translation is needed
    - First-run wizard that:
      - Detects hardware
      - Recommends and downloads best model automatically
      - Shows download progress
      - Tests transcription with downloaded model
    - Allow users to override recommendations with advanced options

- [x] Add model update and maintenance features:
  - Implement version checking for installed models
  - Notify users when model updates are available
  - Add "Update All" button for batch updates
  - Implement model cleanup (remove unused models to free disk space)
  - Add model repair/re-download if corrupted
  - Show disk space usage for all models

- [x] Create first-run setup wizard:
  - Create `src/faster_whisper_hotkey/flet_gui/wizards/setup_wizard.py`:
    - Step 1: Welcome screen with app overview
    - Step 2: Hardware detection (show detected GPU/CPU)
    - Step 3: Model selection with recommendations
    - Step 4: Download selected model with progress
    - Step 5: Hotkey configuration with test
    - Step 6: Quick tutorial (how to use push-to-talk)
    - Step 7: Ready to use summary
  - Make wizard skippable for advanced users
  - Allow re-running wizard from settings later

- [x] Integrate model management into settings:
  - Add "Models" tab to settings panel
  - Show current model with "Change Model" button
  - Display model status (loaded, loading, error)
  - Add "Download More Models" link
  - Show model memory usage when loaded
  - Allow quick model switching without full settings navigation

- [x] Implement model loading optimization:
  - Add lazy loading (only load model on first use)
  - Keep model loaded in background for faster response
  - Show loading state in UI when model is warming up
  - Add "Unload model" option to free memory
  - Implement model pre-loading on app startup (optional setting)
  - Handle model loading errors gracefully with user-friendly messages

- [x] Test model management across hardware configurations:
  - Test on systems without GPU (CPU-only)
  - Test on systems with NVIDIA GPU
  - Test model download interruption and resume
  - Test switching between models
  - Verify auto-detection recommendations are appropriate
  - Test with limited disk space scenarios

## Notes

### Completed Implementation (2024-01-23)

The following components were implemented:

1. **Hardware Detection System** (`hardware_detector.py`)
   - Automatic GPU/CUDA detection using torch
   - GPU detail querying (name, VRAM, compute capability)
   - CPU feature detection (AVX, AVX2, etc.)
   - Automatic recommendation of optimal settings
   - Formatted display of hardware information

2. **Model Download Manager** (`model_download.py`)
   - Download progress tracking with callbacks
   - Progress display (percentage, speed, ETA)
   - Pause/resume/cancel capabilities
   - Error handling with retry logic
   - Model registry with detailed information
   - Integration with faster-whisper

3. **Model Management Interface** (`views/model_manager.py`)
   - Grid layout of model cards with status indicators
   - Model detail dialogs with specifications
   - Filter and sort options
   - Hardware-based recommendations
   - Download/install/remove buttons
   - Real-time download progress display

4. **Automatic Model Selector** (`model_selector.py`)
   - Smart recommendation engine
   - Hardware-based model selection
   - Language preference support
   - First-run recommendation method
   - Alternative model suggestions

5. **Model Maintenance** (`model_maintenance.py`)
   - Model installation detection
   - Version checking
   - Disk space usage tracking
   - Model removal/uninstall
   - Corruption detection and repair
   - Integrity verification

6. **First-Run Setup Wizard** (`wizards/setup_wizard.py`)
   - 7-step guided setup process
   - Hardware detection display
   - Model selection with recommendations
   - Download progress integration
   - Hotkey configuration
   - Tutorial step
   - Skip functionality

7. **Settings Integration**
   - Hardware detection display in settings
   - "Browse All Models" button
   - Automatic device/compute type recommendations
   - Model manager panel integration in main app

8. **Model Loading Optimization** (`model_loader.py`)
   - Lazy loading support
   - Background pre-loading
   - Load state tracking
   - Memory management with auto-unload
   - Progress callbacks
   - Memory usage estimation

9. **Test Suite** (`tests/test_model_management.py`)
   - CPU-only hardware detection tests
   - Simulated GPU hardware detection tests
   - Model download manager tests (registry, callbacks, progress tracking)
   - Model selector recommendation tests
   - Model maintenance tests (version checking, cleanup, repair)
   - Model loader tests (lazy loading, state tracking, memory management)
   - Model switching tests
   - Auto-detection appropriateness tests
   - Limited disk space scenario tests
   - Thread safety tests
   - Error handling tests
