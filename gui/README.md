# SpeakEasy GUI

The Electron desktop app for SpeakEasy. It talks to the Python backend over HTTP and WebSocket
and provides the dashboard, batch transcription, statistics, settings, the system tray, the
global hotkey, and the recording overlay.

## Requirements

- Node.js 18 or newer
- A running backend, or let the app start one (see below)

## Setup

```bash
npm install
```

The root setup script (`python install.py --no-launch`) installs these dependencies together with
the backend.

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the app in development with hot reload |
| `npm run build` | Build main, preload, and renderer into `out/` |
| `npm run preview` | Run the production build |
| `npm run lint` | ESLint |
| `npm run typecheck` | TypeScript checks for main/preload and renderer |
| `npm test` | Vitest |
| `npm run test:coverage` | Vitest with coverage |
| `npm run build:win` | Windows installer |
| `npm run build:linux` | Linux AppImage and deb |
| `npm run build:unpack` | Unpacked build directory |

There is no macOS packaging script. `electron-builder.yml` has a macOS section, but the icon
assets it references are not all present.

## How it talks to the backend

In development the main process spawns the backend and waits for
`http://127.0.0.1:8765/api/health`. If a backend is already healthy on that port, the app reuses
it. Ports and endpoints are in [docs/api.md](../docs/api.md).

The renderer receives events over `ws://127.0.0.1:8765/api/ws`. Live transcript text is relayed
to the overlay window over IPC.

## Layout

- `src/main/`: windows, tray, global hotkey, backend process, IPC handlers
- `src/preload/`: the `window.api` bridge
- `src/renderer/src/pages/`: Dashboard, BatchTranscription, Stats, and the settings pages
- `src/renderer/src/components/`: shared components and the recording overlay
- `src/renderer/src/store/`: Zustand stores
- `src/renderer/src/api/`: HTTP client and WebSocket client
- `src/renderer/src/test/`: test setup and the live transcript test

## Themes

Nine themes are defined in `src/renderer/src/styles/themes.css`: default, tokyo-night, catppuccin,
gruvbox, everforest, nord, kanagawa, ayu, and one-dark.

## Known gaps

- The model download progress dialog is not reachable: the WebSocket subscription that drives it
  is not mounted.
- The Behavior page's grammar controls call backend routes that do not exist.
- Cancelling a recording has backend and IPC support but no UI.

Full list in [docs/configuration.md](../docs/configuration.md#known-limitations).
