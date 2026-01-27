# Phase 09: Voice Activity Detection and Audio Enhancement

This phase significantly improves transcription quality and efficiency by adding Voice Activity Detection (VAD) to automatically skip silence, and audio enhancement to reduce noise. These features make recordings cleaner, reduce transcription time, and improve accuracy - especially important for users in noisy environments.

## Tasks

- [ ] Add VAD dependency and integration:
  - Add `webrtcvad` or `silero-vad` to backend dependencies
  - Create `backend/speakeasy/core/vad.py` module for VAD operations
  - Implement `detect_voice_activity()` function returning speech segments
  - Add VAD configuration parameters (sensitivity, min speech duration, max silence duration)
  - Add VAD settings to AppSettings model

- [ ] Integrate VAD into recording pipeline:
  - Update `transcriber.py` to run VAD during recording
  - Show live VAD status in UI (speech detected vs. silence)
  - Implement auto-stop recording after N seconds of silence
  - Add "Skip silence" setting to enable/disable VAD
  - Implement post-recording silence trimming

- [ ] Add audio enhancement dependencies:
  - Add `noisereduce` or similar noise reduction library
  - Create `backend/speakeasy/core/enhancement.py` module
  - Implement `reduce_noise()` function for audio cleanup
  - Add normalization to prevent clipping
  - Add enhancement settings (enable/disable, strength)

- [ ] Integrate audio enhancement into transcription pipeline:
  - Update `transcribe()` method to apply enhancement before model
  - Add progress feedback during enhancement (can be slow)
  - Cache enhanced audio to avoid re-processing
  - Add "Enhance audio" toggle to Settings

- [ ] Create VAD and enhancement UI:
  - Add VAD settings section to Settings page
  - Add "Auto-stop after silence" slider (5-60 seconds)
  - Add "Skip silence in transcription" toggle
  - Add "Reduce background noise" toggle
  - Add "Normalize audio volume" toggle
  - Show estimated time savings from VAD

- [ ] Add real-time VAD visualization:
  - Update `RecordingIndicator.tsx` to show VAD status
  - Add audio level meter with speech detection highlight
  - Show silence timer counting up during quiet periods
  - Visual feedback when speech is detected vs. silence

- [ ] Implement pre-recording VAD check:
  - Add "Detect speech" test microphone feature
  - Show live speech detection before starting recording
  - Help user position microphone correctly
  - Display signal-to-noise ratio estimate

- [ ] Add post-processing options:
  - Add automatic punctuation cleanup option
  - Add filler word removal (um, uh, like) option
  - Add number formatting (write "one" vs "1") option
  - Add profanity filter option

- [ ] Performance optimization for VAD/enhancement:
  - Profile VAD performance overhead
  - Implement chunked processing for long audio
  - Add progress reporting for long-running enhancement
  - Consider GPU acceleration for noise reduction if available

- [ ] Add VAD/enhancement to API:
  - Add VAD parameters to `/api/transcribe/stop` request
  - Add enhancement parameters to `/api/settings`
  - Return VAD statistics in transcription result (silence removed, etc.)
  - Add `GET /api/audio/analyze` endpoint for audio analysis

- [ ] Test VAD and enhancement features:
  - Test VAD accurately detects speech vs. silence
  - Test auto-stop after silence works reliably
  - Test noise reduction improves transcription accuracy
  - Test enhancement doesn't introduce artifacts
  - Measure performance impact of VAD and enhancement
  - Test with various audio quality levels

- [ ] Document VAD and enhancement features:
  - Add user-facing documentation for new features
  - Document best practices for clear recordings
  - Add troubleshooting tips for poor audio quality
  - Explain trade-offs between speed and quality
