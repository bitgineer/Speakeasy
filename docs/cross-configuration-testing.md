---
type: guide
title: Cross-Configuration Testing Guide
created: 2025-01-23
tags:
  - testing
  - cross-platform
  - hardware
  - compatibility
related:
  - "[[TESTING]]"
  - "[[known-issues]]"
  - "[[installation]]"
---

# Cross-Configuration Testing Guide

This guide provides comprehensive testing procedures for verifying faster-whisper-hotkey works across different Windows configurations, hardware setups, and environmental conditions.

## Overview

Cross-configuration testing ensures the application works reliably for users with different:
- Windows versions and editions
- Hardware configurations (GPU, CPU, RAM)
- Audio devices
- System permissions
- Third-party software (antivirus, etc.)

## Test Categories

### 1. Windows Version Testing

#### Windows 10 Testing Matrix

| Edition | Build | Priority | Key Differences |
|---------|-------|----------|-----------------|
| Home | 22H2 (19045) | High | No Group Policy, basic features |
| Home | 21H2 (19044) | Medium | Older stable build |
| Pro | 22H2 (19045) | High | Group Policy, more features |
| Pro | 21H2 (19044) | Medium | Older stable build |
| Enterprise | LTSC 2021 | Low | Long-term support, stripped features |
| Enterprise | 21H2 (19044) | Low | Domain-joined scenarios |

**Test Procedures:**
1. Verify installer runs and completes
2. Confirm application launches without errors
3. Test system tray icon functionality
4. Verify hotkey registration works globally
5. Check settings persistence in `%APPDATA%`
6. Test model download and installation

**Windows 10 Specific Considerations:**
- N editions don't include media features (may need Media Feature Pack)
- May need VC++ Redistributable 2015-2022
- Older builds may have different audio subsystem behavior

#### Windows 11 Testing Matrix

| Edition | Build | Priority | Key Differences |
|---------|-------|----------|-----------------|
| Home | 23H2 (22631) | High | Latest consumer features |
| Home | 22H2 (22621) | Medium | First stable Win11 release |
| Pro | 23H2 (22631) | High | Latest professional features |
| Pro | 22H2 (22621) | Medium | First stable Win11 release |
| Pro for Workstations | 23H2 | Low | Specialized hardware optimizations |

**Test Procedures:**
Same as Windows 10, plus:
1. Verify Windows 11 UI compatibility (rounded corners, etc.)
2. Test with new Windows Security settings
3. Verify compatibility with Windows Studio Effects (if available)

**Windows 11 Specific Considerations:**
- stricter code signing requirements
- different audio subsystem (Audio Graphs)
- potential SmartScreen warnings for unsigned builds

### 2. Hardware Configuration Testing

#### GPU Testing Matrix

| GPU VRAM | Model | GPU Examples | Recommended Model | Test Priority |
|----------|-------|--------------|-------------------|---------------|
| >= 12GB | High-end | RTX 4090, 4080, RX 7900 XTX | large-v3 | High |
| 8-12GB | Upper-mid | RTX 3080, 3070 Ti, RX 6800 XT | distil-large-v3 | High |
| 6-8GB | Mid-range | RTX 3060, 3060 Ti, RX 6600 XT | medium | High |
| 4-6GB | Lower-mid | RTX 2060, GTX 1660 Ti, RX 5500 XT | small | Medium |
| 2-4GB | Entry-level | GTX 1050 Ti, RX 560 | base | Medium |
| < 2GB | Very low | GT 1030, integrated GPU | tiny | Low |

**GPU Test Procedures:**
1. Run hardware detection and verify GPU is correctly identified
2. Check CUDA/cuDNN availability and version
3. Load recommended model for the VRAM tier
4. Perform transcription test (5-10 seconds)
5. Verify VRAM usage is within expected bounds
6. Test with compute type variations (float16, int8_float16, int8)
7. Verify no memory leaks after 10 consecutive transcriptions

**Expected VRAM Usage:**
| Model | Approximate VRAM Usage |
|-------|------------------------|
| large-v3 | 9-10 GB |
| distil-large-v3 | 5-6 GB |
| medium | 4-5 GB |
| small | 1.5-2 GB |
| base | 1-1.5 GB |
| tiny | 0.7-1 GB |

#### CPU Testing Matrix

| CPU Features | CPU Examples | Recommended Model | Test Priority |
|--------------|--------------|-------------------|---------------|
| AVX512 | Xeon W, i9-11900K | small | Medium |
| AVX2 | Ryzen 5000+, Intel 10th gen+ | small | High |
| AVX | Older Ryzen, Intel 4th-9th gen | base | Medium |
| SSE2/SSE3 | Very old CPUs | tiny | Low |

**CPU Test Procedures:**
1. Run hardware detection and verify CPU features are detected
2. Load recommended model
3. Perform transcription test
4. Measure CPU usage during transcription
5. Measure transcription latency
6. Verify no memory leaks after extended use

**Expected Performance (CPU):**
| Model | Relative Speed | Typical Latency (10s audio) |
|-------|---------------|----------------------------|
| tiny | ~4x | 2-3 seconds |
| base | ~3x | 3-5 seconds |
| small | ~2x | 5-8 seconds |
| medium | ~1.5x | 8-12 seconds |
| large-v3 | ~1x | 15-25 seconds |

*Note: These are approximate values and depend on CPU capabilities*

#### RAM Configuration Testing

| RAM Size | Test Priority | Expected Behavior |
|----------|---------------|-------------------|
| 32GB+ | Low | No issues expected |
| 16GB | Medium | CPU transcription may be slow |
| 8GB | High | Close other apps, use small model |
| 4GB | High | Use tiny model, expect paging |

**RAM Test Procedures:**
1. Monitor memory usage during idle
2. Monitor memory usage during model loading
3. Monitor memory usage during transcription
4. Monitor memory usage after 10 transcriptions
5. Verify memory is released (not leaked)

**Expected Memory Usage:**
- Idle (no model): ~100-200 MB
- Idle (model loaded): +model size in RAM
- During transcription: +2-3x model size
- After transcription: should return to idle (model loaded)

### 3. Audio Device Testing

#### Audio Device Types

| Device Type | Test Priority | Known Issues |
|-------------|---------------|--------------|
| Built-in laptop mic | High | May have noise, low volume |
| USB microphone | High | Generally reliable |
| Bluetooth headset | Medium | May have latency/connect issues |
| Analog headset (3.5mm) | Medium | Reliable but quiet |
| Virtual audio cable | Low | May require special config |
| Multiple mics (USB+analog) | Medium | Selection test needed |

**Audio Device Test Procedures:**
1. **Device Detection:**
   - List all available audio devices in app
   - Verify all Windows audio devices are shown
   - Test device selection

2. **Recording Test:**
   - Test 5-second recording
   - Verify audio level indicator moves
   - Check transcription quality
   - Verify no clipping/distortion

3. **Device Switching:**
   - Start with Device A
   - Switch to Device B
   - Verify Device B is used
   - Switch back to Device A

4. **Disconnect/Reconnect:**
   - Start recording
   - Unplug USB mic
   - Verify graceful error handling
   - Replug mic
   - Verify it works again

**Sample Test Script:**
```
Test Case: USB Microphone Recording
1. Plug in USB microphone
2. Open faster-whisper-hotkey
3. Go to Settings > Audio Device
4. Select USB microphone
5. Press hotkey and speak: "The quick brown fox jumps over the lazy dog"
6. Release hotkey
7. Verify transcription appears within 5 seconds
8. Verify transcription is accurate
9. Check that text appears in target application
```

### 4. Permission and Security Testing

#### User Permission Levels

| Permission Level | Test Priority | Expected Issues |
|------------------|---------------|-----------------|
| Administrator | High | None expected |
| Standard User | High | May need permission for auto-start |
| Guest/Restricted | Medium | Settings may not persist |
| Child Account (Family Safety) | Low | May be blocked |

**Permission Test Procedures:**

1. **Standard User (No Admin):**
   - Install while logged in as standard user
   - Verify installation to user profile
   - Test all core features
   - Verify settings persist in user AppData

2. **Elevated Permissions:**
   - Start with standard user
   - Right-click > Run as Administrator
   - Verify app works correctly
   - Verify settings go to correct location

3. **Restricted Folder Access:**
   - Install to Program Files (requires admin)
   - Verify app can write to AppData
   - Verify model downloads work

#### Antivirus Compatibility

| Antivirus | Test Priority | Known Issues |
|-----------|---------------|--------------|
| Windows Defender | High | May need folder exclusion |
| Norton | Medium | May flag as suspicious |
| McAfee | Medium | May flag as suspicious |
| Kaspersky | Medium | May flag as suspicious |
| Bitdefender | Medium | May flag as suspicious |
| Malwarebytes | Low | Generally compatible |

**Antivirus Test Procedures:**
1. Install and enable antivirus
2. Download and install faster-whisper-hotkey
3. Check if any files are flagged/quarantined
4. Run the application
5. Test model download (network activity)
6. Test transcription (CPU usage pattern)
7. Check if real-time scanning affects performance

**Recommended Exclusions (if needed):**
- Installation directory (e.g., `C:\Program Files\faster-whisper-hotkey\`)
- Settings directory (`%APPDATA%\faster-whisper-hotkey\`)
- Model cache (`%USERPROFILE%\.cache\huggingface\` or portable `models\`)

### 5. Third-Party Software Compatibility

#### Application Paste Targets

| Application | Test Priority | Known Issues |
|-------------|---------------|--------------|
| Notepad | High | Should work perfectly |
| Notepad++ | High | Should work perfectly |
| VS Code (editor) | High | Works in editor |
| VS Code (terminal) | High | **Known issue**: doesn't work |
| Windows Terminal | High | Works with Ctrl+V |
| PowerShell | High | Works with Ctrl+V |
| Command Prompt | High | Works with Ctrl+V |
| Discord | Medium | Works in chat/input |
| Slack | Medium | Works in message input |
| Telegram Desktop | Medium | Works in chat |
| Chrome (address bar) | Medium | Works |
| Chrome (text inputs) | Medium | Works |
| Firefox (text inputs) | Medium | Works |
| Edge (text inputs) | Medium | Works |
| Microsoft Word | Medium | Works |
| Excel | Medium | Works in cells |

**Application Paste Test Procedure:**
1. Open target application
2. Focus on text input area
3. Press hotkey and speak test phrase
4. Release hotkey
5. Verify text appears in correct location
6. Verify no extra characters/spaces

#### Screen Readers and Accessibility

| Tool | Test Priority | Notes |
|------|---------------|-------|
| Narrator | Medium | Built-in Windows screen reader |
| NVDA | Low | Third-party screen reader |
| JAWS | Low | Commercial screen reader |

### 6. Network Configuration Testing

#### Network Conditions

| Condition | Test Priority | Impact |
|-----------|---------------|--------|
| Wired Ethernet | High | Fastest model download |
| WiFi 5GHz | High | Fast model download |
| WiFi 2.4GHz | Medium | Slower download |
| Metered connection | Medium | Windows may warn about data usage |
| No internet (local models) | High | App should work if models cached |
| Proxy server | Low | May need config |
| VPN | Low | May slow downloads |

**Network Test Procedures:**
1. Test model download on each connection type
2. Test with metered connection enabled
3. Test with no internet (cached models)
4. Verify timeout handling (disconnect during download)
5. Verify resume capability (if implemented)

### 7. Special Configurations

#### Multiple Monitors
1. App on primary, focus on secondary
2. App on secondary, focus on primary
3. Focus on different monitor windows
4. Verify hotkey works from any window

#### High DPI / 4K Displays
1. Test at 150% scaling
2. Test at 200% scaling
3. Test on 4K display
4. Verify UI elements render correctly
5. Verify no blurriness

#### Different Languages (Windows UI)
1. English UI
2. Non-English UI (if available)
3. Verify UI displays correctly

#### Roaming Profiles
1. Install with roaming profile
2. Log in on different machine
3. Verify settings sync
4. Verify models are cached correctly

## Test Execution

### Automated Tests

Run the hardware detection tests:
```bash
pytest tests/unit/test_hardware_detector.py -v
```

Run all unit tests:
```bash
pytest tests/unit/ -v -m unit
```

### Manual Test Checklist

Use this checklist for manual cross-configuration testing:

#### Quick Smoke Test (15 minutes)
- [ ] Application launches
- [ ] Settings can be opened
- [ ] Hardware is detected correctly
- [ ] Model can be downloaded (if not cached)
- [ ] Recording works (check audio level indicator)
- [ ] Transcription completes
- [ ] Text is pasted correctly

#### Standard Test (30 minutes)
- [ ] All Quick Smoke Test items
- [ ] Settings persist after restart
- [ ] Multiple consecutive transcriptions work
- [ ] Hotkey can be changed
- [ ] Audio device can be changed
- [ ] History panel opens and shows entries
- [ ] System tray icon menu works
- [ ] Application exits cleanly

#### Comprehensive Test (1-2 hours)
- [ ] All Standard Test items
- [ ] Each model type loads correctly
- [ ] Each compute type works (float16, int8, int8_float16)
- [ ] Clipboard backup/restore works
- [ ] Text processing features work
- [ ] Paste rules work for different applications
- [ ] Memory usage is stable over time
- [ ] No errors in logs
- [ ] Application survives suspend/resume

## Test Result Recording

When reporting cross-configuration test results, include:

### System Information
```
Windows Version: [e.g., Windows 11 Pro 23H2 22631]
Build Number: [e.g., 22631.3007]
CPU: [e.g., AMD Ryzen 7 5800X]
GPU: [e.g., NVIDIA GeForce RTX 3070]
RAM: [e.g., 16GB DDR4-3200]
Audio Device: [e.g., Blue Yeti USB Microphone]
Antivirus: [e.g., Windows Defender]
```

### Test Results
```
Test Date: YYYY-MM-DD
Application Version: [version]
Tests Passed: X/Y
Tests Failed: X/Y
Issues Found:
- [List any issues encountered]
```

### Performance Metrics (if applicable)
```
Startup Time: [seconds]
Model Load Time: [seconds]
Transcription Latency: [seconds for 10s audio]
Idle Memory: [MB]
Peak Memory: [MB]
```

## Troubleshooting Cross-Configuration Issues

### Issue: GPU Not Detected
**Possible Causes:**
- CUDA not installed
- PyTorch CUDA version mismatch
- GPU drivers out of date

**Solutions:**
1. Verify CUDA installation: `nvcc --version`
2. Update GPU drivers
3. Reinstall with correct CUDA version

### Issue: Model Download Fails
**Possible Causes:**
- Network firewall blocking
- Proxy configuration needed
- Insufficient disk space

**Solutions:**
1. Check network connectivity
2. Temporarily disable antivirus
3. Verify sufficient disk space (at least 2x model size)

### Issue: Paste Doesn't Work
**Possible Causes:**
- Target application doesn't accept simulated input
- Special permissions required
- Known limitation (e.g., VSCode terminal)

**Solutions:**
1. Try different paste method (clipboard vs typing)
2. Run application as administrator
3. Check if target is in known limitations

## Continuous Testing

### Automated CI Testing

The following should be tested in CI:
1. Unit tests on every PR
2. Integration tests on every merge
3. Build verification on every release

### Manual Testing Schedule

| Frequency | Tests | Platforms |
|-----------|-------|-----------|
| Weekly | Smoke test | Windows 10/11 Pro |
| Monthly | Standard test | Multiple configurations |
| Pre-release | Comprehensive test | All supported configurations |
