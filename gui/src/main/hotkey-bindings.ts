/**
 * Pure hotkey binding helpers.
 *
 * No electron or uiohook imports here so vitest can exercise the diff and
 * chord matching without native modules.
 */

export type HotkeyTrigger = 'toggle' | 'push-to-talk'

export interface HotkeyBinding {
  accelerator: string
  trigger: HotkeyTrigger
  mode?: string | null
}

export interface BindingDiff {
  keep: HotkeyBinding[]
  remove: HotkeyBinding[]
  add: HotkeyBinding[]
}

export interface HotkeyFailure {
  accelerator: string
  error: string
}

export interface BindingRegistrationHooks {
  /** Returns an error message, or null when the binding installed. */
  install: (binding: HotkeyBinding) => string | null
  uninstall: (binding: HotkeyBinding) => void
}

export interface BindingApplication {
  /** The registry that matches what is actually installed after the attempt. */
  registry: HotkeyBinding[]
  failed: HotkeyFailure[]
}

export function normalizeHotkey(hotkey: string): string {
  return hotkey
    .split('+')
    .map((part) => {
      const lower = part.toLowerCase().trim()
      switch (lower) {
        case 'ctrl':
        case 'control':
          return 'CommandOrControl'
        case 'cmd':
        case 'command':
          return 'Command'
        case 'alt':
          return 'Alt'
        case 'shift':
          return 'Shift'
        case 'space':
          return 'Space'
        case 'enter':
        case 'return':
          return 'Return'
        case 'esc':
        case 'escape':
          return 'Escape'
        case 'tab':
          return 'Tab'
        case 'backspace':
          return 'Backspace'
        case 'delete':
          return 'Delete'
        case 'up':
          return 'Up'
        case 'down':
          return 'Down'
        case 'left':
          return 'Left'
        case 'right':
          return 'Right'
        default:
          if (lower.length === 1) return lower.toUpperCase()
          if (lower.match(/^f\d+$/)) return lower.toUpperCase()
          return part
      }
    })
    .join('+')
}

function bindingKey(binding: HotkeyBinding): string {
  return normalizeHotkey(binding.accelerator)
}

function sameConfig(a: HotkeyBinding, b: HotkeyBinding): boolean {
  return a.trigger === b.trigger && (a.mode ?? null) === (b.mode ?? null)
}

/**
 * Diff two binding lists by normalized accelerator. A binding whose trigger or
 * mode changed counts as one removal plus one addition; reordering alone is a no-op.
 */
export function planBindingDiff(current: HotkeyBinding[], next: HotkeyBinding[]): BindingDiff {
  const currentByKey = new Map(current.map((binding) => [bindingKey(binding), binding]))
  const nextByKey = new Map(next.map((binding) => [bindingKey(binding), binding]))

  const keep = next.filter((binding) => {
    const existing = currentByKey.get(bindingKey(binding))
    return existing !== undefined && sameConfig(existing, binding)
  })

  const remove = current.filter((binding) => {
    const replacement = nextByKey.get(bindingKey(binding))
    return replacement === undefined || !sameConfig(binding, replacement)
  })

  const add = next.filter((binding) => {
    const existing = currentByKey.get(bindingKey(binding))
    return existing === undefined || !sameConfig(existing, binding)
  })

  return { keep, remove, add }
}

/**
 * Apply a binding change transactionally. Removed/changed accelerators are
 * uninstalled first, then additions are installed. On any failure the additions
 * are uninstalled and the removals are restored; a binding that cannot be
 * restored is dropped from the resulting registry so the next attempt retries it.
 */
export function applyBindingPlan(
  previous: HotkeyBinding[],
  next: HotkeyBinding[],
  hooks: BindingRegistrationHooks
): BindingApplication {
  const diff = planBindingDiff(previous, next)
  const failed: HotkeyFailure[] = []

  for (const binding of diff.remove) hooks.uninstall(binding)

  const installed: HotkeyBinding[] = []
  for (const binding of diff.add) {
    const error = hooks.install(binding)
    if (error) {
      failed.push({ accelerator: binding.accelerator, error })
      break
    }
    installed.push(binding)
  }

  if (failed.length === 0) {
    return { registry: next.slice(), failed }
  }

  for (const binding of installed) hooks.uninstall(binding)

  const unrestored = new Set<string>()
  for (const binding of diff.remove) {
    const error = hooks.install(binding)
    if (error) {
      failed.push({ accelerator: binding.accelerator, error: `restore failed: ${error}` })
      unrestored.add(bindingKey(binding))
    }
  }

  return {
    registry: previous.filter((binding) => !unrestored.has(bindingKey(binding))),
    failed
  }
}

export function chordKeycodes(accelerator: string, keymap: Record<string, number>): number[] {
  return accelerator
    .toLowerCase()
    .split('+')
    .map((part) => part.trim())
    .map((part) => keymap[part] ?? 0)
    .filter((keycode) => keycode !== 0)
}

/**
 * A chord is satisfied when every required key is pressed. Extra pressed keys
 * stay satisfied, so holding a chord through a subsequent keypress does not
 * drop a push-to-talk recording. An empty chord is never satisfied.
 */
export function chordSatisfied(
  pressedKeycodes: ReadonlySet<number>,
  chord: readonly number[]
): boolean {
  return chord.length > 0 && chord.every((keycode) => pressedKeycodes.has(keycode))
}
