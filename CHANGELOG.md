# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive error handling system with user-friendly messages
- Error recovery mechanisms (retry with backoff, GPU fallback, audio device fallback)
- Smart typing fallback with proper shift key handling and Unicode support
- Performance profiling utilities and lazy loading for faster startup
- Settings validation with automatic correction and backup
- Stability and stress testing suite
- Cross-configuration testing documentation and tools
- Comprehensive troubleshooting guide and FAQ
- Automatic model download retry with exponential backoff

### Changed
- Optimized startup time with lazy module loading (200-500ms improvement)
- Enhanced thread safety throughout the application
- Improved hotkey debouncing for better responsiveness
- Better memory management with explicit cleanup methods
- Enhanced clipboard operations with context managers

### Fixed
- Settings corruption now handled gracefully with automatic recovery
- Audio buffer overflow now warns users when approaching limits
- Model download failures now retry automatically
- Thread safety issues in state variables resolved
- Memory leaks after long recordings addressed
- GPU initialization failures now fall back to CPU automatically
- Audio device disconnects now attempt reconnection with fallback

## [0.4.3] - 2025-01-15

### Added
- Initial Voxtral model support
- Flet GUI modern interface

### Changed
- Improved model selection UI
- Enhanced settings management

### Fixed
- Minor bug fixes

## [0.4.2] - 2025-01-10

### Added
- Canary 1b v2 model support
- Parakeet TDT 0.6b v3 model support

### Changed
- Updated dependencies
- Improved multi-language support

## [0.4.1] - 2025-01-05

### Fixed
- Installation issues on Windows
- Model download path problems

## [0.4.0] - 2024-12-20

### Added
- Multi-model support (Whisper, Parakeet, Canary, Voxtral)
- Modern Flet-based GUI
- History search functionality
- Auto-paste rules for different applications
- Hardware detection and model recommendations

### Changed
- Complete UI redesign
- Improved settings persistence

## [0.3.0] - 2024-12-01

### Added
- Initial hotkey-based transcription
- System tray integration
- Basic settings management
