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
  - `src/renderer/src/api/`: API client and type definitions
  - `src/renderer/src/components/`: Reusable UI components
  - `src/renderer/src/pages/`: Application pages (Home, History, Settings, etc.)
  - `src/renderer/src/stores/`: State management (Zustand)
- `tests/`: Unit and component tests.
- `e2e/`: End-to-end tests.

## API Client

The GUI communicates with the backend via a typed API client (`src/renderer/src/api/client.ts`):

```typescript
import { apiClient } from '@/api/client';

// Start/stop recording
await apiClient.recording.start();
await apiClient.recording.stop();

// Get transcription history
const history = await apiClient.history.get();

// Import/export history
await apiClient.history.export({ format: 'json' });
await apiClient.history.import({ file: fileData, mode: 'merge' });

// Batch transcription
const job = await apiClient.batch.create({ files: ['audio1.mp3', 'audio2.mp3'] });
await apiClient.batch.cancel(job.id);

// Model management
await apiClient.models.downloadStatus();
await apiClient.models.cancelDownload();
```

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

## Features

### Batch Transcription
Process multiple audio files in a queue with:
- Real-time progress tracking via WebSocket
- Per-file error handling and retry
- Job cancellation support
- Progress bars for individual files and overall job

### Model Download Progress
Real-time download status updates:
- Download progress percentage and speed
- Estimated time remaining
- Stall detection and error reporting
- Cancellation support

### History Import/Export
Export transcription history in multiple formats:
- JSON (full backup)
- TXT (plain text)
- CSV (tabular)
- SRT (subtitles)
- VTT (web subtitles)

Import with merge or replace options, plus filtering by date and search query.

## UI/UX Design System

### Modern Visual Language

The application uses a modern, polished design system with the following characteristics:

**Glassmorphism Effects**
- Subtle transparency (`bg-[var(--glass-bg)]`) with backdrop blur
- Layered shadows for depth perception
- Border highlights for visual interest
- Applied to cards, modals, and overlays

**Enhanced Interactions**
- Scale transforms on hover/active states for tactile feedback
- Smooth transitions (200ms duration) on all interactive elements
- Ring animations on focus for accessibility
- Brightness adjustments on hover states

**Depth & Hierarchy**
- Layered shadow system: `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-xl`
- Glow effects: `--glow-accent`, `--glow-primary`
- Visual depth through z-index stacking

### Theming System

The application supports 9 color themes using CSS variables:

| Theme | Description |
|-------|-------------|
| Default | Clean, neutral color palette |
| Tokyo Night | Dark theme inspired by Tokyo aesthetic |
| Catppuccin | Pastel colors with soft gradients |
| Gruvbox | Warm, retro color scheme |
| Dracula | High-contrast dark theme |
| Nord | Cool, arctic-inspired colors |
| Rose Pine | Soft, muted earth tones |
| Solarized | Low-contrast, eye-friendly palette |
| Monokai | Classic dark theme for developers |

All themes support light/dark variants and respect system preferences.

### Component Patterns

**Buttons**
- Primary, secondary, ghost, outline, and destructive variants
- Hover states with brightness increase and subtle scale (1.02x)
- Active states with scale down (0.97x) and pressed appearance
- Focus ring animation for keyboard navigation
- Layered shadows for depth

**Cards**
- Glassmorphism background with backdrop blur
- Hover lift effect with scale (1.02x)
- Border shine effect on hover
- Responsive shadows that intensify on interaction

**History Items**
- Modern card layout with visual hierarchy
- Action buttons with hover states
- Badge components with subtle gradients
- Smooth transitions for all interactions

**Inputs & Forms**
- Focus states with ring animation and color accent
- Smooth transition on all states
- Error states with visual feedback
- Accessible focus indicators

### Design Principles

- **Accessibility**: Focus rings, semantic HTML, ARIA labels
- **Performance**: Hardware-accelerated transforms (scale, translate)
- **Responsive**: Mobile-first design with fluid layouts
- **Consistency**: Unified spacing, typography, and interaction patterns

## WebSocket Integration

The GUI connects to `ws://localhost:8000/api/ws` for real-time updates:

```typescript
// Listen for transcription updates
socket.on('transcription', (data) => {
  console.log('New transcription:', data);
});

// Listen for model download progress
socket.on('download_progress', (data) => {
  console.log('Download progress:', data.percent, '%');
});

// Listen for batch job updates
socket.on('batch_progress', (data) => {
  console.log('Batch job progress:', data);
});
```
