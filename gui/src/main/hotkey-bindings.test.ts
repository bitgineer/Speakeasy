import { describe, expect, it } from 'vitest'
import {
  applyBindingPlan,
  chordKeycodes,
  chordSatisfied,
  normalizeHotkey,
  planBindingDiff,
  type BindingRegistrationHooks,
  type HotkeyBinding
} from './hotkey-bindings'

const KEYMAP: Record<string, number> = {
  ctrl: 11,
  control: 11,
  shift: 12,
  alt: 13,
  commandorcontrol: 11,
  space: 20,
  d: 30,
  w: 31
}

function binding(
  accelerator: string,
  trigger: HotkeyBinding['trigger'] = 'toggle',
  mode: string | null = null
): HotkeyBinding {
  return { accelerator, trigger, mode }
}

describe('normalizeHotkey', () => {
  it('canonicalizes modifier names and key case', () => {
    expect(normalizeHotkey('ctrl+shift+space')).toBe('CommandOrControl+Shift+Space')
    expect(normalizeHotkey('Control+W')).toBe('CommandOrControl+W')
  })

  it('normalizes enter, escape, and function keys', () => {
    expect(normalizeHotkey('return')).toBe('Return')
    expect(normalizeHotkey('esc')).toBe('Escape')
    expect(normalizeHotkey('f5')).toBe('F5')
  })
})

describe('planBindingDiff', () => {
  it('adds bindings when the current set is empty', () => {
    const next = [binding('ctrl+shift+w')]
    const diff = planBindingDiff([], next)

    expect(diff.add).toEqual(next)
    expect(diff.remove).toEqual([])
    expect(diff.keep).toEqual([])
  })

  it('removes bindings missing from the next set', () => {
    const current = [binding('ctrl+shift+w'), binding('ctrl+shift+d', 'push-to-talk')]
    const next = [binding('ctrl+shift+d', 'push-to-talk')]
    const diff = planBindingDiff(current, next)

    expect(diff.remove).toEqual([binding('ctrl+shift+w')])
    expect(diff.add).toEqual([])
    expect(diff.keep).toEqual(next)
  })

  it('keeps unchanged bindings', () => {
    const current = [binding('ctrl+shift+w', 'toggle', 'write')]
    const diff = planBindingDiff(current, [...current])

    expect(diff.keep).toEqual(current)
    expect(diff.remove).toEqual([])
    expect(diff.add).toEqual([])
  })

  it('reorders without adding or removing', () => {
    const current = [binding('ctrl+shift+w'), binding('ctrl+shift+d', 'push-to-talk')]
    const diff = planBindingDiff(current, [current[1], current[0]])

    expect(diff.keep).toEqual([current[1], current[0]])
    expect(diff.remove).toEqual([])
    expect(diff.add).toEqual([])
  })

  it('replaces a binding whose trigger or mode changed', () => {
    const current = [binding('ctrl+shift+w', 'toggle', 'write')]
    const next = [binding('ctrl+shift+w', 'push-to-talk', 'dictate')]
    const diff = planBindingDiff(current, next)

    expect(diff.remove).toEqual(current)
    expect(diff.add).toEqual(next)
    expect(diff.keep).toEqual([])
  })

  it('treats accelerator aliases as the same binding', () => {
    const diff = planBindingDiff([binding('ctrl+shift+w')], [binding('Control+Shift+W')])

    expect(diff.keep).toHaveLength(1)
    expect(diff.remove).toEqual([])
    expect(diff.add).toEqual([])
  })
})

interface FakeRegistration {
  hooks: BindingRegistrationHooks
  installed: Set<string>
  installCalls: string[]
  uninstallCalls: string[]
}

function fakeRegistration(failFor: string[] = []): FakeRegistration {
  const installed = new Set<string>()
  const installCalls: string[] = []
  const uninstallCalls: string[] = []

  return {
    installed,
    installCalls,
    uninstallCalls,
    hooks: {
      install: (binding) => {
        installCalls.push(binding.accelerator)
        if (failFor.includes(binding.accelerator)) {
          return `failed to register ${binding.accelerator}`
        }
        installed.add(binding.accelerator)
        return null
      },
      uninstall: (binding) => {
        uninstallCalls.push(binding.accelerator)
        installed.delete(binding.accelerator)
      }
    }
  }
}

describe('applyBindingPlan', () => {
  it('installs additions and uninstalls removals on success', () => {
    const previous = [binding('ctrl+shift+w')]
    const next = [binding('ctrl+shift+d', 'push-to-talk')]
    const io = fakeRegistration()

    const result = applyBindingPlan(previous, next, io.hooks)

    expect(result.failed).toEqual([])
    expect(result.registry).toEqual(next)
    expect(io.installed).toEqual(new Set(['ctrl+shift+d']))
    expect(io.uninstallCalls).toEqual(['ctrl+shift+w'])
  })

  it('leaves an unchanged set alone', () => {
    const current = [binding('ctrl+shift+w', 'toggle', 'write')]
    const io = fakeRegistration()

    const result = applyBindingPlan(current, [...current], io.hooks)

    expect(result.registry).toEqual(current)
    expect(io.installCalls).toEqual([])
    expect(io.uninstallCalls).toEqual([])
  })

  it('rolls back installed additions and restores removals when an install fails', () => {
    const previous = [binding('ctrl+shift+w')]
    const next = [binding('ctrl+shift+d'), binding('ctrl+shift+b')]
    const io = fakeRegistration(['ctrl+shift+b'])

    const result = applyBindingPlan(previous, next, io.hooks)

    expect(result.failed).toEqual([
      { accelerator: 'ctrl+shift+b', error: 'failed to register ctrl+shift+b' }
    ])
    expect(result.registry).toEqual(previous)
    expect(io.installed).toEqual(new Set(['ctrl+shift+w']))
  })

  it('drops a binding from the registry when its restore also fails', () => {
    const previous = [binding('ctrl+shift+w')]
    const next = [binding('ctrl+shift+d')]
    const io = fakeRegistration(['ctrl+shift+d', 'ctrl+shift+w'])

    const result = applyBindingPlan(previous, next, io.hooks)

    expect(result.failed).toEqual([
      { accelerator: 'ctrl+shift+d', error: 'failed to register ctrl+shift+d' },
      { accelerator: 'ctrl+shift+w', error: 'restore failed: failed to register ctrl+shift+w' }
    ])
    expect(result.registry).toEqual([])
  })
})

describe('chordKeycodes', () => {
  it('maps accelerator parts through the provided keymap', () => {
    expect(chordKeycodes('ctrl+shift+d', KEYMAP)).toEqual([11, 12, 30])
  })

  it('drops parts the keymap does not know', () => {
    expect(chordKeycodes('ctrl+banana+d', KEYMAP)).toEqual([11, 30])
  })

  it('returns no keycodes for an unmappable accelerator', () => {
    expect(chordKeycodes('', KEYMAP)).toEqual([])
  })
})

describe('chordSatisfied', () => {
  it('is true when the pressed set matches exactly', () => {
    expect(chordSatisfied(new Set([11, 12, 20]), chordKeycodes('ctrl+shift+space', KEYMAP))).toBe(
      true
    )
  })

  it('is false when a required key is missing', () => {
    expect(chordSatisfied(new Set([11, 20]), chordKeycodes('ctrl+shift+space', KEYMAP))).toBe(false)
  })

  it('stays true when extra keys are pressed', () => {
    expect(chordSatisfied(new Set([11, 12, 20, 30]), chordKeycodes('ctrl+shift+space', KEYMAP))).toBe(
      true
    )
  })

  it('is false for an empty chord', () => {
    expect(chordSatisfied(new Set([11, 12, 20]), [])).toBe(false)
  })
})
