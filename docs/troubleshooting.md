# Troubleshooting

## The first launch seems stuck

The backend downloads the default model (about 2 GB) on first launch. Watch the terminal that
runs `npm run dev`, or open Settings, Model, to see the download state. Later launches start
offline.

## No audio is recorded

1. Open Settings, Audio and pick the right input device.
2. Check that the device works in your system sound settings.
3. On Linux, make sure PortAudio is installed (`portaudio19-dev` on Debian/Ubuntu) and that your
   user can access the audio server.

## FFmpeg is missing

Batch and audio file transcription need FFmpeg on `PATH`.

| Platform | Command |
|---|---|
| Windows | `winget install Gyan.FFmpeg` |
| macOS | `brew install ffmpeg` |
| Debian/Ubuntu | `sudo apt install ffmpeg` |

Reopen the terminal afterwards. Live dictation works without FFmpeg.

## CUDA errors, or the GPU is not used

- Set the device to `cpu` in Settings, Model, and reload the model.
- Or rebuild the backend for CPU: `python install.py --reinstall --cpu`.
- Check the driver with `nvidia-smi`. The CUDA extra installs `cuda-python` and CUDA PyTorch
  wheels.
- Parakeet and Canary ignore `compute_type`; only Whisper and Voxtral use it.

## The app does not connect to the backend

The app connects to `http://127.0.0.1:8765`. If another process holds that port, stop it. If a
healthy backend is already running on 8765, the app reuses it instead of starting its own.

## The hotkey does not work

- Another application may have registered the same combination. Pick another in Settings, Hotkey.
- Push-to-talk supports a limited set of keys. Function keys and letters work; some combinations
  cannot be parsed and are ignored.
- On some systems the hotkey needs the app to have been granted accessibility permissions
  (macOS: System Settings, Privacy and Security, Accessibility).

## Where are the logs

- The backend prints to the terminal that runs the app (`npm run dev`).
- The desktop app prints to the same terminal.

## Settings do not seem to apply

Model changes need Load Model on the Model page. Everything else applies immediately. If the file
was edited by hand, restart the app so the backend reloads it.

## Known limitations

See the list at the end of [configuration.md](configuration.md). It covers the auto-paste toggle,
grammar correction, the download progress dialog, recording cancel, tray quit, and `server_port`.
