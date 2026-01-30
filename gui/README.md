# SpeakEasy GUI

The modern frontend for SpeakEasy, built with [Electron](https://www.electronjs.org/), [React](https://react.dev/), and [Vite](https://vitejs.dev/).

## Overview

This directory contains the source code for the desktop application interface. It communicates with the [Python Backend](../backend/README.md) to provide voice transcription capabilities.

## Prerequisites

- Node.js 18+
- npm (usually bundled with Node.js)

## Setup

1. Navigate to the GUI directory:
   ```bash
   cd gui
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Development Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start the development server (Vite + Electron) |
| `npm run build` | Build the application for production |
| `npm run preview` | Preview the built application |
| `npm run lint` | Lint code with ESLint |
| `npm run typecheck` | Run TypeScript type checking |

## Testing

We have comprehensive testing strategies in place:

- **Unit/Component Tests**: Run with `npm test` (Vitest). See [Tests README](tests/README.md).
- **End-to-End Tests**: Run with `npm run test:e2e` (Playwright). See [E2E README](e2e/README.md).

## Project Structure

- `src/main/`: Electron main process code (window management, backend spawning).
- `src/preload/`: Preload scripts for secure IPC communication.
- `src/renderer/`: React application (UI components, pages, state).
- `tests/`: Unit and component tests.
- `e2e/`: End-to-end tests.

## Building for Distribution

To build the installer for your platform:

```bash
# Windows
npm run build:win

# Linux
npm run build:linux

# Unpacked (directory)
npm run build:unpack
```
