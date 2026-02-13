# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible receiving such patches depend on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report (suspected) security vulnerabilities to **[INSERT CONTACT EMAIL]**. You will receive a response from us within 48 hours.

If the issue is confirmed, we will release a patch as soon as possible depending on complexity but historically within a few days.

## Security Best Practices

### Local-First Privacy

SpeakEasy is designed with privacy in mind:

- **100% Local Processing**: All transcription happens on your device
- **No Cloud Uploads**: Your voice data never leaves your machine
- **No Telemetry**: We don't collect usage data
- **Offline Capable**: Works without internet connection

### Model Downloads

When you first run SpeakEasy, it downloads AI models from HuggingFace. These models are:
- Downloaded over HTTPS
- Verified via checksums when available
- Stored locally in your user directory

### Data Storage

- **Transcriptions**: Stored locally in SQLite database
- **Audio**: Never stored unless explicitly enabled in settings
- **Settings**: Stored in local configuration files

### Microphone Access

SpeakEasy requires microphone access. On first run:
- Windows: Grant permission via system dialog
- macOS: Grant permission in System Preferences → Security & Privacy
- Linux: May require adding user to `audio` group

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine the affected versions
2. Audit code to find any potential similar problems
3. Prepare fixes for all still-supported versions
4. Release new versions as quickly as possible

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a pull request.
