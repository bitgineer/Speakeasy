---
type: guide
title: Release Process
created: 2025-01-23
tags:
  - release
  - deployment
  - ci-cd
  - versioning
related:
  - "[[TESTING]]"
  - "[[INSTALLATION]]"
  - "[[PORTABLE_MODE]]"
---

# Release Process

This guide describes how to create and publish a new release of faster-whisper-hotkey.

## Overview

The release process consists of:
1. Preparing the release (version bump, changelog)
2. Running the build pipeline (tests, executable, installer, portable)
3. Testing on clean systems
4. Publishing to GitHub Releases
5. Post-release tasks

## Version Numbering

We follow [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH

- MAJOR: Incompatible API changes
- MINOR: New functionality (backwards compatible)
- PATCH: Bug fixes (backwards compatible)
```

### Examples

| Version | Type | Example Changes |
|---------|------|-----------------|
| `0.4.3` → `0.4.4` | Patch | Bug fix, minor improvement |
| `0.4.3` → `0.5.0` | Minor | New feature, UI improvements |
| `0.4.3` → `1.0.0` | Major | Stable release, API changes |

### Pre-releases

For beta/preview releases, append a suffix:

- `0.5.0-beta.1` - First beta for 0.5.0
- `0.5.0-rc.1` - First release candidate
- `1.0.0-alpha.1` - Early alpha

## Pre-Release Checklist

Before creating a release, verify:

- [ ] All tests pass (`make test`)
- [ ] No critical bugs open
- [ ] Documentation is updated
- [ ] Version number is updated in `pyproject.toml`
- [ ] Changelog is prepared
- [ ] Spec file version is updated
- [ ] Build script works correctly

## Release Steps

### Step 1: Update Version

1. Update `pyproject.toml`:
   ```toml
   [project]
   version = "0.5.0"  # New version
   ```

2. Update the spec file version `faster-whisper-hotkey-flet.spec`:
   ```python
   APP_VERSION = '0.5.0'
   ```

3. Update VSVersionInfo in the spec file if major version changed:
   ```python
   filevers=(0, 5, 0, 0),
   prodvers=(0, 5, 0, 0),
   ```

### Step 2: Update Changelog

1. Create/edit `CHANGELOG.md`:

   ```markdown
   # Changelog

   ## [0.5.0] - 2025-01-23

   ### Added
   - Feature A description
   - Feature B description

   ### Changed
   - Improved C description
   - Updated D to new behavior

   ### Fixed
   - Bug E fix
   - Bug F fix

   ### Removed
   - Deprecated G feature

   ## [0.4.3] - 2025-01-15
   ...
   ```

2. Keep entries in reverse chronological order
3. Use conventional commit prefixes: Added, Changed, Fixed, Removed

### Step 3: Commit Changes

```bash
git add pyproject.toml faster-whisper-hotkey-flet.spec CHANGELOG.md
git commit -m "MAESTRO: Bump version to 0.5.0"
```

### Step 4: Create Git Tag

```bash
# Create annotated tag
git tag -a v0.5.0 -m "Release v0.5.0"

# Or with full message
git tag -a v0.5.0 -m "Release v0.5.0" -m "New features and bug fixes"
```

### Step 5: Push to GitHub

```bash
# Push commit
git push origin main

# Push tag (triggers CI/CD)
git push origin v0.5.0
```

### Step 6: Monitor CI/CD Pipeline

The `.github/workflows/build-release.yml` workflow will:

1. Run on Windows runner
2. Install Python, PyInstaller, NSIS
3. Run test suite
4. Build executable with PyInstaller
5. Upload build artifacts
6. Create GitHub Release with:
   - Auto-generated changelog
   - Distribution files (exe installer, portable zip, checksums)

Monitor at: `https://github.com/blakkd/faster-whisper-hotkey/actions`

### Step 7: Verify Release

1. Download artifacts from the release
2. Test on clean Windows 10
3. Test on clean Windows 11
4. Verify installer and uninstaller
5. Test portable version
6. Check auto-update system works

## Manual Build (Local)

For testing before release, build locally:

```bash
# Full build with tests
make build

# Or specific targets
make build-flet         # Build Flet GUI version
make build-qt           # Build Qt GUI version
make build-portable     # Build only portable ZIP
make build-installer    # Build only NSIS installer

# Build without tests (faster)
make build-no-tests
```

### Build Script Options

```bash
python scripts/build.py [options]

Options:
  --skip-tests     Skip running tests
  --test-only      Only run tests, don't build
  --clean-only     Only clean build artifacts
  --no-installer   Skip NSIS installer creation
  --no-portable    Skip portable ZIP creation
  --no-checksums   Skip checksum generation
  --spec flet|qt   Choose which spec file to build (default: flet)
```

### Build Artifacts

After a successful build, `dist/` contains:

| File | Description |
|------|-------------|
| `faster-whisper-hotkey.exe` | Main executable |
| `faster-whisper-hotkey-setup-{version}.exe` | NSIS installer |
| `faster-whisper-hotkey-portable-{version}-windows.zip` | Portable ZIP |
| `*.sha256` | SHA256 checksums |
| `RELEASE_NOTES.md` | Auto-generated release notes |

## Testing Checklist

Before public release:

### Automated Tests
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Test coverage is adequate

### Manual Testing - Windows 10
- [ ] Installer runs without errors
- [ ] Application launches successfully
- [ ] First-run setup wizard completes
- [ ] Recording and transcription works
- [ ] Settings persist after restart
- [ ] System tray icon appears
- [ ] Hotkeys work globally
- [ ] Auto-start on boot works (if enabled)
- [ ] Uninstaller removes all files

### Manual Testing - Windows 11
- [ ] Same as Windows 10 checklist

### Hardware Scenarios
- [ ] CPU-only system
- [ ] NVIDIA GPU system (CUDA)
- [ ] Limited disk space scenario

### Upgrade Testing
- [ ] Upgrade from previous version preserves settings
- [ ] Old models still work
- [ ] No migration errors

## Creating GitHub Release Manually

If CI/CD fails or you need manual control:

### Option A: GitHub Web UI

1. Go to [Releases page](https://github.com/blakkd/faster-whisper-hotkey/releases)
2. Click "Draft a new release"
3. Enter tag: `v0.5.0`
4. Enter title: `Release 0.5.0`
5. Paste changelog in description
6. Attach files:
   - `faster-whisper-hotkey-setup-{version}.exe`
   - `faster-whisper-hotkey-portable-{version}-windows.zip`
   - Corresponding `.sha256` files
7. Click "Publish release"

### Option B: GitHub CLI

```bash
# Install gh CLI first
# https://cli.github.com/

# Create release
gh release create v0.5.0 \
  --title "Release 0.5.0" \
  --notes-file CHANGELOG.md \
  dist/faster-whisper-hotkey-setup-*.exe \
  dist/faster-whisper-hotkey-portable-*.zip \
  dist/*.sha256
```

## Post-Release Tasks

### Immediate
- [ ] Verify download counts increase
- [ ] Monitor GitHub Issues for new bug reports
- [ ] Update website/documentation links if needed

### Short-term (1 week)
- [ ] Gather user feedback
- [ ] Track critical bugs
- [ ] Plan next release

### Long-term
- [ ] Analyze telemetry (if opted in)
- [ ] Review crash reports
- [ ] Update documentation based on user questions

## Emergency Releases

For critical bugs requiring immediate fix:

1. Create hotfix branch from release tag:
   ```bash
   git checkout -b hotfix/v0.5.1 v0.5.0
   ```

2. Apply the fix and test

3. Update version to patch:
   ```toml
   version = "0.5.1"
   ```

4. Commit, tag, and push:
   ```bash
   git add .
   git commit -m "MAESTRO: Hotfix for critical bug"
   git tag -a v0.5.1 -m "Hotfix v0.5.1"
   git push origin hotfix/v0.5.1
   git push origin v0.5.1
   ```

5. Merge back to main:
   ```bash
   git checkout main
   git merge hotfix/v0.5.1
   ```

## Rollback Procedure

If a release has critical issues:

1. **Yank the release** (GitHub):
   - Go to the release page
   - Edit the release
   - Mark as "Pre-release" or delete entirely

2. **Communicate**:
   - Post issue on GitHub
   - Update README with warning
   - Notify users via available channels

3. **Fix and re-release**:
   - Create new patch version
   - Thoroughly test the fix
   - Release with notes about the fix

## CI/CD Workflow Details

### Trigger Conditions

The workflow triggers on:
- Push to version tags: `v*.*.*`
- Manual workflow dispatch (from Actions tab)
- Pull requests (build test only)

### Build Matrix

Currently builds on:
- `windows-latest` with Python 3.11

### Job Stages

1. **build-windows**: Builds executable and creates artifacts
2. **create-release**: Creates GitHub release with artifacts (tagged releases only)
3. **build-pr-check**: Verifies build works on PRs

### Build Time

Typical build times:
- Clean build: ~10-15 minutes
- Incremental build: ~5-10 minutes

## Changelog Format

Use the [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (New features)

## [0.5.0] - 2025-01-23

### Added
- Windows installer with NSIS
- Portable ZIP distribution
- Auto-update system
- Setup wizard for first-time users

### Changed
- Improved model download reliability
- Better error handling

### Fixed
- Memory leak during long recordings
- Hotkey not working in some apps

### Removed
- Deprecated command-line options

## [0.4.3] - 2025-01-15
...
```

## Signing and Notarization (Future)

For wider distribution, consider:

### Code Signing

Sign executables to reduce SmartScreen warnings:

```bash
signtool sign /f certificate.pfx /p password /t timestamp_url dist/*.exe
```

### Notarization (macOS, future)

If macOS support is added:
- Use Apple notarization service
- Required for macOS 10.15+

## Related Documentation

- [[TESTING]] - Testing procedures and pre-release checklist
- [[INSTALLATION]] - Installation methods and troubleshooting
- [[PORTABLE_MODE]] - Portable distribution details
