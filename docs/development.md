# Development

## Repository layout

```
backend/            Python backend (FastAPI, models, services)
  speakeasy/
    __main__.py     Server entry point
    server.py       HTTP and WebSocket routes
    core/           Model wrapper, transcriber, audio, text cleanup
    services/       Settings, history, batch, export, download state
    utils/          Clipboard, paste, device helpers
  tests/            pytest suite
gui/                Electron desktop app
  src/main/         Main process: windows, tray, hotkey, backend spawn, IPC
  src/preload/      Context bridge
  src/renderer/     React app (pages, components, stores)
docs/               Documentation
install.py          Setup and launcher
install.bat/.sh     Bootstrap wrappers
```

## Setup

```bash
python install.py --no-launch
```

This creates `backend/.venv`, installs dependencies, and installs `gui/node_modules`.

## Backend

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/ -q     # Windows
.venv/bin/python -m pytest tests/ -q             # macOS/Linux
```

- 409 tests, all with mocked models. No GPU needed.
- Lint: `uv run ruff check .` and `uv run ruff format --check .`
- The suite imports `sounddevice`, which needs PortAudio on Linux
  (`sudo apt install portaudio19-dev`).

## Desktop app

```bash
cd gui
npm run lint          # eslint
npm run typecheck     # tsc for main/preload and renderer
npm test              # vitest
npm run test:coverage # vitest with coverage
npm run dev           # electron-vite dev, hot reload
npm run build         # production bundle into out/
```

Packaging uses `electron-builder.yml`:

```bash
npm run build:win     # Windows NSIS installer
npm run build:linux   # AppImage and deb
```

These artifacts are for development only. They do not bundle a Python runtime or the backend
dependencies. A packaged build exits with setup instructions when no backend environment is found,
instead of hanging. End-user distribution is `install.py` (`install.bat` on Windows, `install.sh`
on macOS and Linux), which launches the app with `npm run dev`.

There is no `build:mac` script; the config has a macOS section but the icon assets it expects are
not all present.

## Continuous integration

`.github/workflows/test.yml` runs on pushes and pull requests to `main`:

| Job | What it runs |
|---|---|
| Backend Tests | Ruff check and format, then pytest with coverage on Ubuntu |
| Frontend Tests | ESLint, typecheck, and vitest with coverage on Ubuntu |
| All Tests Passed | Summary gate |

The backend job installs PortAudio and xvfb because the suite imports audio and input libraries.

The backend OpenAPI schema is committed at `backend/openapi.json`; regenerate it with
`python scripts/export_openapi.py` from `backend/`. The GUI derives its API types from it with
`npm run gen:api`, which writes `gui/src/renderer/src/api/generated.ts`. CI checks that both files
are current.

## Conventions

- Python is formatted and linted by Ruff (line length 100, target 3.10+).
- TypeScript is linted by ESLint and checked by `tsc`.
- Commit messages follow the conventional style already in the history
  (`feat:`, `fix:`, `chore:`, `docs:`).
- `main` is the only long-lived branch.
