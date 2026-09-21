# Usage

## Dictation with the global hotkey

Press the global hotkey to start recording and press it again to stop. The default is
`Ctrl+Shift+Space`; the current value lives in Settings, Hotkey.

While recording:

- The recording overlay appears above other windows, bottom center of the display under your
  cursor. It shows a timer, a stop button, and the live transcript when live captions are on.
- The tray icon turns red.
- The Dashboard status chip shows Recording.

When you stop, the overlay shows Processing while the final transcription runs. The result is
saved to history, copied to the clipboard, and pasted into the active window. The paste is
performed by the backend.

### Hotkey modes

| Mode | Behavior |
|---|---|
| Toggle | Press to start, press again to stop |
| Push-to-talk | Hold the keys to record, release to stop. After 60 seconds recording locks so you can release; press the combination again to stop |

## Live captions

Enable live captions in Settings, Behavior. The backend re-transcribes the audio every
`live_chunk_seconds` (1 to 10 seconds, default 3) and pushes the growing transcript to the
overlay. The overlay shows the newest text, up to a fixed height, and scrolls as you speak.

Live captions add CPU/GPU load during recording because each pass transcribes the audio recorded
so far.

## History

Every finished transcription is stored in `~/.speakeasy/speakeasy.db` (SQLite). The Dashboard:

- lists transcriptions, newest first, with infinite scrolling
- searches with full-text search
- deletes individual entries
- exports the full history, or a single record, to TXT, JSON, CSV, SRT, or VTT
- imports a previously exported JSON file, with a merge option

SRT and VTT timestamps are generated from each record's duration. They are not offsets into a
single audio file.

## Batch transcription

The Batch page accepts audio and video files (drag and drop, or the file picker). Files are
transcribed one at a time with the model currently loaded. Each file shows queued, processing,
completed, or failed, and failed files can be retried. Jobs and their state are stored in
`~/.speakeasy/batch.db`.

FFmpeg must be on `PATH` for batch and file transcription.

## Statistics

The Stats page shows totals from the history database: total transcriptions, total duration,
today/this week/this month counts, and the first and latest transcription. Words and average
duration are computed from the currently loaded page of history.

## Settings

| Page | What it controls |
|---|---|
| Model | Model type and variant, compute device and precision, language, downloaded model cache |
| Audio | Input device |
| Hotkey | The global hotkey and its mode |
| Behavior | Live captions and interval, text cleanup and custom filler words, indicator visibility |
| Appearance | Color theme |
| Data | History import and export |
| About | Version and license |

Changes to model settings apply after Load Model. Settings are stored in
`~/.speakeasy/settings.json`.

## System tray

The tray icon shows Ready or Recording. The menu offers Open Dashboard, Settings, and Quit
SpeakEasy. Clicking the icon shows the main window.

Closing the main window hides it; the app keeps running in the tray.
