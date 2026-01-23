# Phase 05: Windows Installer and Distribution

This phase creates a streamlined Windows installation experience that eliminates the complexity of Python, dependencies, and manual configuration. This is critical for mass adoption.

## Goals

- Create a single .exe installer that includes all dependencies
- Implement automatic hardware detection during installation
- Set up auto-update mechanism for future releases
- Create distribution pipeline for releases

## Tasks

- [ ] Set up PyInstaller configuration for Windows executable:
  - Create `faster-whisper-hotkey.spec` file:
    - Configure one-file mode for single exe output
    - Include all necessary data files (configs, icons)
    - Exclude unnecessary packages to reduce size
    - Set up proper console/scriptw mode handling
  - Create app icon with multiple resolutions (16x16 to 256x256)
  - Configure metadata (version, description, company info)
  - Test executable on clean Windows system

- [ ] Create NSIS installer script:
  - Create `installer/installer.nsi`:
    - Welcome screen with app description
    - License agreement page
    - Installation directory selection
    - Start menu folder creation
    - Desktop shortcut creation (optional)
    - Auto-start on Windows startup option
    - Installation progress bar
    - Finish page with "Launch app" option
  - Add uninstaller that removes:
    - Program files
    - Start menu shortcuts
    - Desktop shortcuts
    - Registry entries
    - User data (optional, with prompt)
  - Include option to preserve user data on uninstall

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

- [ ] Set up release build pipeline:
  - Create `scripts/build.py`:
    - Clean build artifacts
    - Run tests
    - Build executable with PyInstaller
    - Package NSIS installer
    - Generate portable zip
    - Create checksums for release files
    - Generate release notes from git log
  - Create Makefile or GitHub Actions workflow:
    - Trigger on tag push
    - Run on Windows runner
    - Build all distribution formats
    - Upload artifacts to GitHub Releases
    - Create GitHub Release with changelog

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
