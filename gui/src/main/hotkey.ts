import { globalShortcut } from "electron";
import { uIOhook, UiohookKey } from "uiohook-napi";
import { showRecordingIndicator, hideRecordingIndicator } from "./windows";
import { setTrayRecording } from "./tray";
import { sendToRenderer } from "./ipc-handlers";
import { getBackendPort } from "./backend";
import {
  applyBindingPlan,
  chordKeycodes,
  chordSatisfied,
  normalizeHotkey,
  type HotkeyBinding,
  type HotkeyFailure,
  type HotkeyTrigger,
} from "./hotkey-bindings";

export type HotkeyRegisterResult = { ok: true } | { ok: false; failed: HotkeyFailure[] };

let registry: HotkeyBinding[] = [];
let recordingMode: string | null = null;
let recordingTrigger: HotkeyTrigger | null = null;
let isRecordingActive = false;
let isProcessing = false; // Lock to prevent concurrent operations
let lastHotkeyTime = 0;
const DEBOUNCE_MS = 500;

// Push-to-Talk Auto-Lock
const LOCK_THRESHOLD_MS = 60000; // 60 seconds
let lockTimer: NodeJS.Timeout | null = null;
let isLocked = false;

// One shared uiohook listener drives every push-to-talk chord.
interface ChordState {
  binding: HotkeyBinding;
  keys: number[];
  pressed: Set<number>;
  satisfied: boolean;
}
const pttChords = new Map<string, ChordState>();
let uiohookStarted = false;

// Electron accelerator format -> uiohook key codes
const keyCodeMap: Record<string, number> = {
  commandorcontrol: UiohookKey.Ctrl,
  control: UiohookKey.Ctrl,
  ctrl: UiohookKey.Ctrl,
  alt: UiohookKey.Alt,
  shift: UiohookKey.Shift,
  command: UiohookKey.Meta,
  meta: UiohookKey.Meta,
  space: UiohookKey.Space,
  return: UiohookKey.Enter,
  enter: UiohookKey.Enter,
  escape: UiohookKey.Escape,
  tab: UiohookKey.Tab,
  backspace: UiohookKey.Backspace,
  delete: UiohookKey.Delete,
  up: UiohookKey.ArrowUp,
  down: UiohookKey.ArrowDown,
  left: UiohookKey.ArrowLeft,
  right: UiohookKey.ArrowRight,
  a: UiohookKey.A,
  b: UiohookKey.B,
  c: UiohookKey.C,
  d: UiohookKey.D,
  e: UiohookKey.E,
  f: UiohookKey.F,
  g: UiohookKey.G,
  h: UiohookKey.H,
  i: UiohookKey.I,
  j: UiohookKey.J,
  k: UiohookKey.K,
  l: UiohookKey.L,
  m: UiohookKey.M,
  n: UiohookKey.N,
  o: UiohookKey.O,
  p: UiohookKey.P,
  q: UiohookKey.Q,
  r: UiohookKey.R,
  s: UiohookKey.S,
  t: UiohookKey.T,
  u: UiohookKey.U,
  v: UiohookKey.V,
  w: UiohookKey.W,
  x: UiohookKey.X,
  y: UiohookKey.Y,
  z: UiohookKey.Z,
  "0": UiohookKey[0],
  "1": UiohookKey[1],
  "2": UiohookKey[2],
  "3": UiohookKey[3],
  "4": UiohookKey[4],
  "5": UiohookKey[5],
  "6": UiohookKey[6],
  "7": UiohookKey[7],
  "8": UiohookKey[8],
  "9": UiohookKey[9],
  f1: UiohookKey.F1,
  f2: UiohookKey.F2,
  f3: UiohookKey.F3,
  f4: UiohookKey.F4,
  f5: UiohookKey.F5,
  f6: UiohookKey.F6,
  f7: UiohookKey.F7,
  f8: UiohookKey.F8,
  f9: UiohookKey.F9,
  f10: UiohookKey.F10,
  f11: UiohookKey.F11,
  f12: UiohookKey.F12,
};

function debounceAllows(): boolean {
  const now = Date.now();
  if (now - lastHotkeyTime < DEBOUNCE_MS) return false;
  lastHotkeyTime = now;
  return true;
}

function handleTogglePress(binding: HotkeyBinding): void {
  if (isProcessing) return;
  if (!debounceAllows()) return;

  if (isRecordingActive) {
    stopRecording();
  } else {
    startFromBinding(binding);
  }
}

function installToggle(binding: HotkeyBinding): string | null {
  const accelerator = normalizeHotkey(binding.accelerator);
  const registered = globalShortcut.register(accelerator, () => handleTogglePress(binding));
  if (!registered) return `failed to register ${accelerator}`;
  return null;
}

function installPushToTalk(binding: HotkeyBinding): string | null {
  const accelerator = normalizeHotkey(binding.accelerator);
  const keys = chordKeycodes(accelerator, keyCodeMap);
  if (keys.length === 0) return `could not parse accelerator: ${binding.accelerator}`;

  pttChords.set(accelerator, { binding, keys, pressed: new Set(), satisfied: false });
  ensureUiohookListener();
  return null;
}

function installBinding(binding: HotkeyBinding): string | null {
  return binding.trigger === "push-to-talk" ? installPushToTalk(binding) : installToggle(binding);
}

function uninstallBinding(binding: HotkeyBinding): void {
  const accelerator = normalizeHotkey(binding.accelerator);
  if (binding.trigger === "push-to-talk") {
    pttChords.delete(accelerator);
  } else {
    globalShortcut.unregister(accelerator);
  }
}

/**
 * Transactional registry update. Unregisters removed/changed accelerators,
 * registers added/changed ones, and on any failure puts the previous set back.
 *
 * Failure entries carry the accelerators that could not be registered. A
 * `restore failed:` entry means that previous binding could not be put back
 * either; the registry drops it so a later call retries instead of treating it
 * as still active.
 */
export function registerHotkeys(bindings: HotkeyBinding[]): HotkeyRegisterResult {
  const result = applyBindingPlan(registry, bindings, {
    install: installBinding,
    uninstall: uninstallBinding,
  });
  registry = result.registry;

  if (result.failed.length > 0) {
    console.error(
      `Hotkey registration failed for: ${result.failed
        .map((failure) => failure.accelerator)
        .join(", ")}`,
    );
    return { ok: false, failed: result.failed };
  }

  console.log(`Registered ${registry.length} hotkey binding(s)`);
  return { ok: true };
}

export function unregisterAllHotkeys(): void {
  for (const binding of registry) uninstallBinding(binding);
  registry = [];
  pttChords.clear();
}

export function getCurrentBindings(): HotkeyBinding[] {
  return registry.slice();
}

function ensureUiohookListener(): void {
  if (uiohookStarted) return;
  uIOhook.on("keydown", handleKeydown);
  uIOhook.on("keyup", handleKeyup);
  uIOhook.start();
  uiohookStarted = true;
}

function handleKeydown(e: { keycode: number }): void {
  for (const chord of pttChords.values()) {
    chord.pressed.add(e.keycode);
    const satisfied = chordSatisfied(chord.pressed, chord.keys);

    if (satisfied && !chord.satisfied) {
      if (!isRecordingActive && !isProcessing) {
        if (debounceAllows()) startFromBinding(chord.binding);
      } else if (isRecordingActive && isLocked && !isProcessing) {
        if (debounceAllows()) stopRecording();
      }
    }

    chord.satisfied = satisfied;
  }
}

function handleKeyup(e: { keycode: number }): void {
  for (const chord of pttChords.values()) {
    chord.pressed.delete(e.keycode);
    const satisfied = chordSatisfied(chord.pressed, chord.keys);

    if (!satisfied && chord.satisfied && isRecordingActive && !isLocked && !isProcessing) {
      stopRecording();
    }

    chord.satisfied = satisfied;
  }
}

function startFromBinding(binding: HotkeyBinding): void {
  recordingTrigger = binding.trigger;
  startRecording(binding.mode ?? null);
}

export async function startRecording(mode: string | null = null): Promise<void> {
  if (isRecordingActive || isProcessing) return;

  isProcessing = true;
  try {
    recordingMode = mode;
    isRecordingActive = true;
    isLocked = false;
    console.log("Starting recording");

    // Start lock timer for push-to-talk mode
    if (recordingTrigger === "push-to-talk") {
      if (lockTimer) clearTimeout(lockTimer);
      lockTimer = setTimeout(() => {
        if (isRecordingActive) {
          isLocked = true;
          console.log("Recording locked (long press)");
          sendToRenderer("recording:locked");
        }
      }, LOCK_THRESHOLD_MS);
    }

    setTrayRecording(true);
    showRecordingIndicator();
    sendToRenderer("recording:start", { mode: recordingMode });

    const response = await fetch(`http://127.0.0.1:${getBackendPort()}/api/transcribe/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(15_000),
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: `Backend returned ${response.status}` }));
      throw new Error(
        errorData.detail || `Backend returned ${response.status}`,
      );
    }
  } catch (error) {
    console.error("Failed to start recording:", error);
    isRecordingActive = false;
    recordingMode = null;
    recordingTrigger = null;
    setTrayRecording(false);
    hideRecordingIndicator();
    const errorMessage = error instanceof Error ? error.message : String(error);
    sendToRenderer("recording:error", errorMessage);
  } finally {
    isProcessing = false;
  }
}

export async function stopRecording(): Promise<void> {
  if (!isRecordingActive || isProcessing) return;

  // Clear lock timer
  if (lockTimer) {
    clearTimeout(lockTimer);
    lockTimer = null;
  }
  isLocked = false;

  isProcessing = true;
  try {
    isRecordingActive = false;
    console.log("Stopping recording");

    setTrayRecording(false);
    // Don't hide indicator - keep it visible in idle state
    // hideRecordingIndicator()

    // Notify renderer immediately that recording has stopped and processing started
    sendToRenderer("recording:processing");

    // The mode rides only when the pressed binding carried one; null means the
    // backend resolves active_mode at stop time.
    const body = recordingMode === null ? {} : { mode: recordingMode };

    // Generous bound: transcribing a long recording is slow, but a wedged backend must eventually error instead of swallowing input.
    const response = await fetch(`http://127.0.0.1:${getBackendPort()}/api/transcribe/stop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(15 * 60 * 1000),
    });

    if (!response.ok) throw new Error(`Backend returned ${response.status}`);

    const result = await response.json();
    console.log("Transcription result:", result.text?.substring(0, 50));
    sendToRenderer("recording:complete", result);
  } catch (error) {
    console.error("Failed to stop recording:", error);
    sendToRenderer("recording:error", String(error));
  } finally {
    recordingMode = null;
    recordingTrigger = null;
    isProcessing = false;
  }
}

export async function cancelRecording(): Promise<void> {
  if (!isRecordingActive || isProcessing) return;

  // Clear lock timer
  if (lockTimer) {
    clearTimeout(lockTimer);
    lockTimer = null;
  }
  isLocked = false;

  isProcessing = true;
  try {
    isRecordingActive = false;
    console.log("Cancelling recording");

    setTrayRecording(false);
    // Don't hide indicator - keep it visible in idle state
    // hideRecordingIndicator()

    const response = await fetch(
      `http://127.0.0.1:${getBackendPort()}/api/transcribe/cancel`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: AbortSignal.timeout(15_000),
      },
    );

    if (!response.ok) throw new Error(`Backend returned ${response.status}`);

    sendToRenderer("recording:error", "Cancelled by user");
  } catch (error) {
    console.error("Failed to cancel recording:", error);
    sendToRenderer("recording:error", String(error));
  } finally {
    recordingMode = null;
    recordingTrigger = null;
    isProcessing = false;
  }
}

export function stopUiohook(): void {
  if (uiohookStarted) {
    uIOhook.stop();
    uiohookStarted = false;
  }
}

export function isRecording(): boolean {
  return isRecordingActive;
}
