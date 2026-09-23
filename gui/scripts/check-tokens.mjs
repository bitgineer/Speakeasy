#!/usr/bin/env node
/**
 * Token check for the renderer style layer.
 *
 * Fails when:
 *   1. a var(--x) in a .tsx file is not defined in the loaded stylesheets;
 *   2. a raw hex color appears in a .tsx file (unless allow-listed);
 *   3. the dark and light theme blocks define different semantic name sets;
 *   4. a data-accent block declares anything but accent role tokens;
 *   5. tailwind.config.js maps a color to a variable that does not exist;
 *   6. a loaded stylesheet references a variable that is not declared;
 *   7. the legacy --color-* usage count grew past the ratchet baseline.
 *
 * The legacy count is the migration ratchet. Lower LEGACY_BASELINE as pages
 * migrate; the count prints on every run.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const guiRoot = join(dirname(fileURLToPath(import.meta.url)), '..')
const srcRoot = join(guiRoot, 'src', 'renderer', 'src')
const stylesRoot = join(srcRoot, 'styles')
const loadedStyles = ['tokens.css', 'themes.css', 'globals.css'].map((f) => join(stylesRoot, f))
const tailwindConfig = join(guiRoot, 'tailwind.config.js')

const LEGACY_BASELINE = 554
const HEX_ALLOWLIST = []
const ACCENT_ROLE_TOKENS = new Set([
  '--accent-solid',
  '--accent-solid-hover',
  '--accent-solid-active',
  '--accent-on-solid',
  '--accent-text',
  '--accent-muted',
  '--accent-border',
  '--focus'
])

const failures = []
const fail = (message) => failures.push(message)

const read = (path) => readFileSync(path, 'utf8')

// Replaces comments with spaces so offsets and line numbers stay exact.
const blankComments = (text) => text.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))

const lineAt = (text, index) => text.slice(0, index).split('\n').length

const refsIn = (text) => {
  const refs = []
  const re = /var\(\s*(--[a-zA-Z0-9-]+)/g
  let m
  while ((m = re.exec(text))) refs.push({ name: m[1], index: m.index })
  return refs
}

const parseRules = (css) => {
  const rules = []
  let i = 0
  while (i < css.length) {
    const open = css.indexOf('{', i)
    if (open === -1) break
    const selector = css.slice(i, open).trim()
    let depth = 1
    let j = open + 1
    while (j < css.length && depth > 0) {
      if (css[j] === '{') depth++
      else if (css[j] === '}') depth--
      j++
    }
    rules.push({ selector, body: css.slice(open + 1, j - 1) })
    i = j
  }
  return rules
}

const declaredNames = (rules) => {
  const names = new Set()
  const re = /(--[a-zA-Z0-9-]+)\s*:/g
  for (const rule of rules) {
    let m
    while ((m = re.exec(rule.body))) names.add(m[1])
  }
  return names
}

const selectorHasTheme = (selector, theme) =>
  selector
    .split(',')
    .some((part) => new RegExp(`\\[data-theme\\s*=\\s*["']${theme}["']\\]`).test(part))

const walk = (dir, extension) => {
  const out = []
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry)
    if (statSync(path).isDirectory()) out.push(...walk(path, extension))
    else if (path.endsWith(extension)) out.push(path)
  }
  return out
}

// ---- Load and index the loaded stylesheets ----

const styleSources = loadedStyles.map((path) => ({
  path,
  label: relative(guiRoot, path).replace(/\\/g, '/'),
  css: blankComments(read(path))
}))
const allRules = styleSources.flatMap((source) => parseRules(source.css))
const defined = declaredNames(allRules)

// ---- 1 and 2: tsx var references and raw hex ----

const tsxFiles = walk(srcRoot, '.tsx')
let legacyUsages = 0
const arbitraryViolations = []
const ARBITRARY_BASELINE = 19

for (const file of tsxFiles) {
  const text = read(file)
  const label = relative(guiRoot, file).replace(/\\/g, '/')

  for (const ref of refsIn(text)) {
    if (!defined.has(ref.name)) {
      fail(`${label}:${lineAt(text, ref.index)} references ${ref.name}, which no loaded stylesheet defines`)
    }
  }

  let hexIndex = -1
  while ((hexIndex = text.indexOf('#', hexIndex + 1)) !== -1) {
    const match = /^#[0-9a-fA-F]{3,8}\b/.exec(text.slice(hexIndex))
    if (!match) continue
    if (HEX_ALLOWLIST.includes(match[0].toLowerCase())) continue
    fail(`${label}:${lineAt(text, hexIndex)} has raw hex ${match[0]}; use a semantic token or extend HEX_ALLOWLIST`)
  }

  for (const arbitrary of text.match(/\[[^\]\n]*(?:px|#[0-9a-fA-F]{3,8})[^\]\n]*\]/g) ?? []) {
    arbitraryViolations.push(`${label} has arbitrary value ${arbitrary}; use a token-backed utility`)
  }
  for (const fn of text.match(/\b(?:rgba?|hsla?)\(/g) ?? []) {
    arbitraryViolations.push(`${label} uses raw ${fn.slice(0, -1)}() color; use a semantic token`)
  }

  legacyUsages += refsIn(text).filter((ref) => ref.name.startsWith('--color-')).length
}

console.log(`  arbitrary or raw-color values in tsx: ${arbitraryViolations.length} (baseline ${ARBITRARY_BASELINE})`)
if (arbitraryViolations.length > ARBITRARY_BASELINE) {
  for (const message of arbitraryViolations) fail(message)
}
if (arbitraryViolations.length < ARBITRARY_BASELINE) {
  console.log(`  lower ARBITRARY_BASELINE to ${arbitraryViolations.length} in scripts/check-tokens.mjs`)
}

// ---- 3 and 4: theme parity and accent-only overrides ----

const themeNames = { dark: new Set(), light: new Set() }
for (const rule of allRules) {
  const isAccentOverride = rule.selector.includes('data-accent')
  const theme = selectorHasTheme(rule.selector, 'dark')
    ? 'dark'
    : selectorHasTheme(rule.selector, 'light')
      ? 'light'
      : null
  if (!theme) continue

  if (isAccentOverride) {
    for (const name of declaredNames([rule])) {
      if (!ACCENT_ROLE_TOKENS.has(name)) {
        fail(`themes.css: accent block "${rule.selector.trim()}" declares ${name}, which is not an accent role token`)
      }
    }
    continue
  }

  for (const name of declaredNames([rule])) themeNames[theme].add(name)
}

if (themeNames.dark.size === 0 || themeNames.light.size === 0) {
  fail('themes.css: could not find both [data-theme="dark"] and [data-theme="light"] blocks')
} else {
  for (const name of themeNames.dark) {
    if (!themeNames.light.has(name)) fail(`themes.css: ${name} is defined for dark but not light`)
  }
  for (const name of themeNames.light) {
    if (!themeNames.dark.has(name)) fail(`themes.css: ${name} is defined for light but not dark`)
  }
}

// ---- 5: tailwind config variables ----

const tailwindText = blankComments(read(tailwindConfig))
for (const ref of refsIn(tailwindText)) {
  if (!defined.has(ref.name)) {
    fail(`tailwind.config.js:${lineAt(tailwindText, ref.index)} maps ${ref.name}, which no loaded stylesheet defines`)
  }
}

// ---- 6: loaded stylesheets reference only declared variables ----

for (const source of styleSources) {
  for (const ref of refsIn(source.css)) {
    if (!defined.has(ref.name)) {
      fail(`${source.label}:${lineAt(source.css, ref.index)} references ${ref.name}, which is never declared`)
    }
  }
}

// ---- 7: legacy ratchet ----

if (legacyUsages > LEGACY_BASELINE) {
  fail(`legacy --color-* usages grew to ${legacyUsages} (baseline ${LEGACY_BASELINE})`)
}

// ---- Report ----

if (failures.length > 0) {
  console.error('check:tokens FAILED')
  for (const message of failures) console.error(`  - ${message}`)
  process.exit(1)
}

const note =
  legacyUsages < LEGACY_BASELINE
    ? ` (down from ${LEGACY_BASELINE}; lower LEGACY_BASELINE in scripts/check-tokens.mjs)`
    : ''
console.log('check:tokens OK')
console.log(`  semantic names per theme: ${themeNames.dark.size} dark / ${themeNames.light.size} light`)
console.log(`  tsx var references: all defined`)
console.log(`  raw hex in tsx: 0`)
console.log(`  tailwind config mappings: all defined`)
console.log(`  legacy --color-* usages: ${legacyUsages}${note}`)
