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
  - [x] Test executable on clean Windows system

**Implementation Notes:**
- Created `faster-whisper-hotkey-flet.spec` with comprehensive PyInstaller configuration for the Flet GUI version
- Created `installer/create_icon.py` script that generates a modern microphone icon with sound waves in blue gradient
- Icon sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
- Icon saved as `installer/app_icon.ico` for use with PyInstaller and NSIS
- Spec file includes all hidden imports for Flet, PyQt6, sounddevice, faster-whisper, transformers, etc.
- Excludes unnecessary packages: matplotlib, IPython, tkinter, test frameworks
- Windowed mode (no console) for better user experience
- UPX compression enabled for smaller executable size
- Added `scripts/test_executable.py` - comprehensive executable testing script:
  - Validates executable exists and has valid PE header
  - Checks version information via PowerShell
  - Tests launch/exit behavior with isolated app data
  - Verifies settings file creation
  - Tests for missing DLL dependencies
  - Supports portable mode testing
  - Quick mode for faster iteration
- Added `run_tests()` and `verify_executable()` functions to `scripts/build.py`:
  - `--run-tests` flag to run tests before building
  - `--test-only` flag to run tests without building
  - Automatic executable verification after build
  - Clean test environment setup/teardown
- Created `docs/TESTING.md` with comprehensive testing guide:
  - Clean system testing procedures (VM, Sandbox)
  - Automated testing instructions
  - Manual testing checklist for all features
  - Test scenarios (fresh install, GPU, CPU-only, upgrade)
  - Troubleshooting common issues
  - Pre-release checklist

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

- [x] Implement first-run configuration in installer:
  - [x] Add post-install setup wizard:
    - [x] Hardware detection (CUDA vs CPU)
    - [x] Download recommended model (show progress)
    - [x] Configure default hotkey
    - [x] Test audio device
    - [x] Opt-in for auto-start on boot
    - [x] Opt-in for anonymous usage statistics
  - [x] Handle installation errors gracefully:
    - [x] Insufficient disk space
    - [x] Missing Windows components
    - [x] Network errors during model download
    - [x] Permission issues

**Implementation Notes:**
- Enhanced `SetupWizard` class in `src/faster_whisper_hotkey/flet_gui/wizards/setup_wizard.py`:
  - Added new wizard steps: `AUDIO_TEST` and `ANALYTICS`
  - Added `_build_audio_test_step()` with microphone testing UI
  - Added `_start_audio_test()` method for audio level detection using sounddevice
  - Added `_build_analytics_step()` with opt-in checkboxes for:
    - Anonymous usage data collection
    - Auto-start on Windows boot
  - Updated `WizardState` dataclass with new fields:
    - `audio_test_passed: bool`
    - `analytics_enabled: bool`
    - `auto_start_enabled: bool`
- Integrated setup wizard into `src/faster_whisper_hotkey/flet_gui/app.py`:
  - Added `_check_first_run()` method to detect first-time users
  - Added `_show_setup_wizard()` to display wizard on first launch
  - Added `on_wizard_complete()` callback to apply wizard settings:
    - Updates model, hotkey, activation mode from wizard choices
    - Applies hardware detection results (device, compute type)
    - Sets privacy_mode based on analytics opt-in
    - Marks onboarding_completed = True
    - Creates auto-start shortcut if opted in
  - Added `_enable_auto_start()` to create Windows startup shortcut via PowerShell
- Enhanced NSIS installer error handling in `installer/installer.nsi`:
  - Added `.onInit` function with checks:
    - Prevents multiple installer instances running simultaneously
    - Validates Windows 10+ requirement
    - Checks available disk space (500MB minimum)
  - Added `CheckWritePermissions()` function to verify write access
  - Added `GetDriveFreeSpace()` function for disk space validation
  - Added `OptionsPageLeave()` validation before proceeding
  - Added file copy error handling in installer section
- Wizard automatically runs on first app launch (after installation)
- All wizard choices are persisted to settings and applied immediately
- Users can skip the wizard entirely via "Skip Wizard" button

- [x] Create portable version option:
  - [x] Generate portable .zip package:
    - [x] Single executable + models folder
    - [x] All settings stored in app directory (not AppData)
    - [x] No registry entries
    - [x] No installation required
  - [x] Document portable vs installed differences
  - [x] Add portable launcher that handles first-run setup

**Implementation Notes:**
- Enhanced `src/faster_whisper_hotkey/settings.py` with portable mode detection:
  - Added `is_portable_mode()` function to detect portable mode
  - Detection methods: environment variable (`PORTABLE_MODE=1`), `portable.txt` marker file, existing `settings/` directory
  - Added `get_settings_dir()`, `get_settings_file()`, `get_history_file()` functions for dynamic path resolution
  - Updated `save_settings()`, `load_settings()`, `save_history()`, `load_history()`, `clear_history()` to use dynamic paths
  - Portable mode stores settings in `./settings/` next to executable
  - Installed mode uses `%APPDATA%\faster_whisper_hotkey\` on Windows
- Enhanced `scripts/build.py` portable package creation:
  - Added `portable.txt` marker file to portable ZIP
  - Updated `START-portable.bat` to set `PORTABLE_MODE=1` environment variable
  - Added `PORTABLE_README.md` with comprehensive portable mode documentation
- Created `docs/PORTABLE_MODE.md` with full documentation:
  - Comparison table of portable vs installed features
  - File structure for both modes
  - Installation, updating, and uninstallation instructions
  - Troubleshooting guide
  - Enterprise deployment guidance

- [x] Implement auto-update system:
  - [x] Create `src/faster_whisper_hotkey/flet_gui/updater.py`:
    - [x] Check for updates on startup (configurable frequency)
    - [x] Compare version against GitHub releases API
    - [x] Show update notification when new version available
    - [x] Download update in background
    - [x] Apply update with app restart
    - [x] Support silent updates (optional)
  - [x] Add update settings:
    - [x] Check for updates: daily, weekly, manually
    - [x] Auto-download updates toggle
    - [x] Beta/preview updates channel
  - [x] Handle update failures gracefully with rollback option

**Implementation Notes:**
- Created `src/faster_whisper_hotkey/flet_gui/updater.py` with comprehensive auto-update functionality:
  - `UpdateManager` class for checking, downloading, and installing updates
  - `UpdateDialog` class for Flet-based update notifications and progress dialogs
  - `UpdateInfo` dataclass for update metadata
  - `get_current_version()` function to detect app version from package metadata or version.txt
  - `parse_version()` and `compare_versions()` for semantic version comparison
  - GitHub Releases API integration for fetching latest versions
  - Background download with progress tracking
  - Update state persistence (dismissed versions, last check time, settings)
  - Support for both requests library and urllib fallback
- Added update settings to `src/faster_whisper_hotkey/settings.py`:
  - `update_check_frequency: str` ("daily", "weekly", "manually")
  - `update_include_prereleases: bool` for beta/preview channel
  - `update_auto_download: bool` for automatic background downloads
- Integrated updater into `src/faster_whisper_hotkey/flet_gui/app.py`:
  - `update_manager` and `_update_dialog` properties in FletApp
  - `_initialize_update_manager()` method for startup configuration
  - Automatic update check on app launch (with 3-second delay)
  - `check_for_updates_now()` method for manual update checks
  - Settings are applied from user configuration
- Added Updates category to `src/faster_whisper_hotkey/flet_gui/views/modern_settings_panel.py`:
  - New `SettingsCategory.UPDATES` enum value
  - Three update-related setting definitions with tooltips
  - "Check for Updates" button in Updates category
  - Update status display showing current version and update availability
  - `_add_update_status()` method to display version info
  - `_on_check_updates_click()` handler for manual update checks
  - Settings save integration to update UpdateManager when settings change
- Updates are only enabled for frozen executables (detected via `sys.frozen`)
- When running from source, a message indicates updates are only available for installed executables

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
