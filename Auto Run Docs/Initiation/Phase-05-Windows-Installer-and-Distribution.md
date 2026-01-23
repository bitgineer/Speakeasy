# Phase 05: Windows Installer and Distribution

This phase creates a streamlined Windows installation experience that eliminates the complexity of Python, dependencies, and manual configuration. This is critical for mass adoption.

## Goals

- Create a single .exe installer that includes all dependencies
- Implement automatic hardware detection during installation
- Set up auto-update mechanism for future releases
- Create distribution pipeline for releases

## Tasks

- [x] Set up PyInstaller configuration for Windows executable:
  - [x] Create `faster-whisper-hotkey.spec` file:
    - [x] Configure one-file mode for single exe output
    - [x] Include all necessary data files (configs, icons)
    - [x] Exclude unnecessary packages to reduce size
    - [x] Set up proper console/scriptw mode handling
  - [x] Create app icon with multiple resolutions (16x16 to 256x256)
  - [x] Configure metadata (version, description, company info)
  - [ ] Test executable on clean Windows system

**Implementation Notes:**
- Created `faster-whisper-hotkey-flet.spec` with comprehensive PyInstaller configuration for the Flet GUI version
- Created `installer/create_icon.py` script that generates a modern microphone icon with sound waves in blue gradient
- Icon sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
- Icon saved as `installer/app_icon.ico` for use with PyInstaller and NSIS
- Spec file includes all hidden imports for Flet, PyQt6, sounddevice, faster-whisper, transformers, etc.
- Excludes unnecessary packages: matplotlib, IPython, tkinter, test frameworks
- Windowed mode (no console) for better user experience
- UPX compression enabled for smaller executable size

- [x] Create NSIS installer script:
  - [x] Create `installer/installer.nsi`:
    - [x] Welcome screen with app description
    - [x] License agreement page
    - [x] Installation directory selection
    - [x] Start menu folder creation
    - [x] Desktop shortcut creation (optional)
    - [x] Auto-start on Windows startup option
    - [x] Installation progress bar
    - [x] Finish page with "Launch app" option
  - [x] Add uninstaller that removes:
    - [x] Program files
    - [x] Start menu shortcuts
    - [x] Desktop shortcuts
    - [x] Registry entries
    - [x] User data (optional, with prompt)
  - [x] Include option to preserve user data on uninstall

**Implementation Notes:**
- Created `installer/installer.nsi` with full NSIS installer configuration
- Custom options page for desktop shortcut and auto-start selections
- LZMA compression for smaller installer size
- Registers application in Windows "Add/Remove Programs"
- Uninstaller prompts for user data deletion

- [ ] Implement first-run configuration in installer:
  - Add post-install setup wizard:
    - Hardware detection (CUDA vs CPU)
    - Download recommended model (show progress)
    - Configure default hotkey
    - Test audio device
    - Opt-in for auto-start on boot
    - Opt-in for anonymous usage statistics
  - Handle installation errors gracefully:
    - Insufficient disk space
    - Missing Windows components
    - Network errors during model download
    - Permission issues

- [ ] Create portable version option:
  - Generate portable .zip package:
    - Single executable + models folder
    - All settings stored in app directory (not AppData)
    - No registry entries
    - No installation required
  - Document portable vs installed differences
  - Add portable launcher that handles first-run setup

- [ ] Implement auto-update system:
  - Create `src/faster_whisper_hotkey/flet_gui/updater.py`:
    - Check for updates on startup (configurable frequency)
    - Compare version against GitHub releases API
    - Show update notification when new version available
    - Download update in background
    - Apply update with app restart
    - Support silent updates (optional)
  - Add update settings:
    - Check for updates: daily, weekly, manually
    - Auto-download updates toggle
    - Beta/preview updates channel
  - Handle update failures gracefully with rollback option

- [x] Set up release build pipeline:
  - [x] Create `scripts/build.py`:
    - [x] Clean build artifacts
    - [ ] Run tests
    - [x] Build executable with PyInstaller
    - [x] Package NSIS installer
    - [x] Generate portable zip
    - [x] Create checksums for release files
    - [x] Generate release notes from git log
  - [ ] Create Makefile or GitHub Actions workflow:
    - [ ] Trigger on tag push
    - [ ] Run on Windows runner
    - [ ] Build all distribution formats
    - [ ] Upload artifacts to GitHub Releases
    - [ ] Create GitHub Release with changelog

**Implementation Notes:**
- Created `scripts/build.py` with command-line options for flexible building
- Supports: `--clean-only`, `--no-installer`, `--no-portable`, `--no-checksums`, `--spec (flet|qt)`
- Automatically detects version from `pyproject.toml`
- Generates SHA256 checksums for all distribution files
- Creates RELEASE_NOTES.md with git log history
- Portable package includes START-portable.bat launcher for local settings storage

- [ ] Add telemetry and crash reporting (optional):
  - Create `src/faster_whisper_hotkey/flet_gui/telemetry.py`:
    - Anonymous usage statistics (opt-in):
      - Version in use
      - Model used
      - OS version
      - Crash reports
    - Performance metrics:
      - Transcription latency
      - Model loading time
      - Error rates
  - Respect privacy:
    - Clear opt-in during setup
    - Easy toggle in settings
    - No sensitive data recorded
    - Link to privacy policy

- [ ] Create distribution documentation:
  - Write `docs/installation.md`:
    - Installation methods (installer, portable, pip)
    - System requirements
    - Troubleshooting common installation issues
    - Uninstallation instructions
  - Write `docs/release-process.md`:
    - How to create a new release
    - Version number conventions
    - Changelog format
    - Testing checklist before release
  - Update README with new installation options
  - Add installation video/tutorial link

- [ ] Test distribution on clean systems:
  - Test on fresh Windows 10 installation
  - Test on fresh Windows 11 installation
  - Test without GPU (CPU-only)
  - Test with NVIDIA GPU
  - Test with limited disk space
  - Test upgrade from previous version
  - Test portable version
  - Verify uninstaller cleans up correctly

- [ ] Create branding and marketing materials:
  - Design app logo and icon
  - Create banner screenshots for README/GitHub
  - Write short description for app stores/listings
  - Create demo video showing key features
  - Draft release announcement
