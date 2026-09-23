#!/usr/bin/env node
/**
 * Capture the main-window routes of an isolated SpeakEasy instance to PNG.
 *
 * Isolation follows the verify-speakeasy recipe: a scratch home holds the
 * history database, and the backend runs on the port the app reads from
 * ~/.speakeasy/settings.json. Electron resolves its home folder through the
 * Windows shell, not USERPROFILE, so the GUI itself always targets that port;
 * the preflight below refuses to run while a real app or backend holds it.
 * Nothing under ~/.speakeasy is read or written except that one port number.
 *
 * Usage:
 *   npm run capture:ui -- --out <dir> [--theme dark,light] [--accent violet]
 *                                  [--app-root <checkout>] [--seed <fixture>]
 *                                  [--no-seed] [--keep]
 */

import { spawn, spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, openSync, readFileSync, writeFileSync } from 'node:fs'
import { createServer, Socket } from 'node:net'
import { dirname, isAbsolute, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { homedir, tmpdir } from 'node:os'

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url))
const DEFAULT_APP_ROOT = resolve(SCRIPT_DIR, '..', '..')
const DEFAULT_SEED = join(SCRIPT_DIR, 'fixtures', 'capture-history.json')
const VIEWPORT = { width: 900, height: 670 }
const IS_WIN = process.platform === 'win32'
const BACKEND_TIMEOUT_MS = 120_000
const GUI_TIMEOUT_MS = 240_000
const ROUTE_TIMEOUT_MS = 30_000

const ROUTES = [
  { name: 'dashboard', path: '/', marker: /transcriptions|transcription history/i },
  { name: 'batch', path: '/batch', marker: /batch transcription/i },
  { name: 'stats', path: '/stats', marker: /statistics/i },
  { name: 'settings-model', path: '/settings/model', marker: /model settings/i },
  { name: 'settings-behavior', path: '/settings/behavior', marker: /behavior/i },
  { name: 'settings-hotkey', path: '/settings/hotkey', marker: /hotkey settings/i },
  { name: 'settings-audio', path: '/settings/audio', marker: /audio settings/i },
  { name: 'settings-appearance', path: '/settings/appearance', marker: /appearance/i },
  { name: 'settings-data', path: '/settings/data', marker: /data management/i },
  { name: 'settings-processing', path: '/settings/processing', marker: /processing/i },
  { name: 'settings-about', path: '/settings/about', marker: /about/i }
]

function usage() {
  return [
    'Usage: npm run capture:ui -- [options]',
    '  --out <dir>        output directory (default: <tmp>/opencode/ui-captures/<timestamp>)',
    '  --theme <list>     "default" or comma list of dark,light (default: default)',
    '  --accent <name>    violet or ink (default: violet)',
    '  --app-root <dir>   checkout to launch (default: this repo)',
    '  --seed <file>      history fixture to import before capture',
    '  --no-seed          skip seeding; captures the empty states',
    '  --keep             leave the instance running after capture'
  ].join('\n')
}

function parseArgs(argv) {
  const args = {
    out: null,
    themes: ['default'],
    accent: 'violet',
    appRoot: DEFAULT_APP_ROOT,
    seed: DEFAULT_SEED,
    keep: false
  }
  for (let i = 0; i < argv.length; i += 1) {
    const [flag, inline] = argv[i].split(/=(.*)/s)
    const value = () => inline ?? argv[++i]
    switch (flag) {
      case '--out':
        args.out = value()
        break
      case '--theme':
        args.themes = value()
          .split(',')
          .map((part) => part.trim())
          .filter(Boolean)
        break
      case '--accent':
        args.accent = value()
        break
      case '--app-root':
        args.appRoot = value()
        break
      case '--seed':
        args.seed = value()
        break
      case '--no-seed':
        args.seed = null
        break
      case '--keep':
        args.keep = true
        break
      case '--help':
      case '-h':
        console.log(usage())
        process.exit(0)
        break
      default:
        throw new Error(`unknown argument ${argv[i]}\n${usage()}`)
    }
  }
  for (const theme of args.themes) {
    if (!['default', 'dark', 'light'].includes(theme)) throw new Error(`unknown theme ${theme}`)
  }
  if (!['violet', 'ink'].includes(args.accent)) throw new Error(`unknown accent ${args.accent}`)
  if (!args.out) {
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*$/, '').replace('T', '-')
    args.out = join(tmpdir(), 'opencode', 'ui-captures', stamp)
  }
  args.out = resolve(args.out)
  args.appRoot = resolve(args.appRoot)
  if (args.seed && !isAbsolute(args.seed)) args.seed = resolve(process.cwd(), args.seed)
  return args
}

const sleep = (ms) => new Promise((done) => setTimeout(done, ms))

async function waitFor(label, predicate, timeoutMs, intervalMs = 500) {
  const deadline = Date.now() + timeoutMs
  let last = null
  while (Date.now() < deadline) {
    try {
      last = await predicate()
      if (last) return last
    } catch {
      last = null
    }
    await sleep(intervalMs)
  }
  throw new Error(`${label} did not happen within ${Math.round(timeoutMs / 1000)}s`)
}

function freePort() {
  return new Promise((resolvePort, reject) => {
    const server = createServer()
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address()
      server.close(() => resolvePort(port))
    })
  })
}

function configuredPort() {
  try {
    const settings = JSON.parse(
      readFileSync(join(homedir(), '.speakeasy', 'settings.json'), 'utf8')
    )
    const port = Number(settings.server_port)
    if (Number.isInteger(port) && port >= 1024 && port <= 65535) return port
  } catch {
    /* no settings file yet; the app falls back to 8765 */
  }
  return 8765
}

function portBusy(port) {
  return new Promise((resolveBusy) => {
    const socket = new Socket()
    socket.once('connect', () => {
      socket.destroy()
      resolveBusy(true)
    })
    socket.once('error', () => resolveBusy(false))
    socket.connect(port, '127.0.0.1')
  })
}

async function httpJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`GET ${url} -> ${response.status}`)
  return response.json()
}

function spawnDetached(command, argv, cwd, env, outPath, errPath) {
  const out = openSync(outPath, 'a')
  const err = openSync(errPath, 'a')
  const child = spawn(command, argv, {
    cwd,
    env,
    detached: true,
    windowsHide: true,
    stdio: ['ignore', out, err]
  })
  child.unref()
  return child.pid
}

function killTree(pid) {
  if (!pid) return
  if (IS_WIN) spawnSync('taskkill', ['/PID', String(pid), '/T', '/F'], { windowsHide: true })
  else {
    try {
      process.kill(-pid, 'SIGTERM')
    } catch {
      /* already gone */
    }
  }
}

// --- CDP client over the built-in WebSocket ---

function connectCdp(wsUrl) {
  return new Promise((resolveConnection, reject) => {
    const socket = new WebSocket(wsUrl)
    const pending = new Map()
    const events = []
    let nextId = 0

    socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data)
      if (message.id && pending.has(message.id)) {
        const { resolveCall, rejectCall } = pending.get(message.id)
        pending.delete(message.id)
        if (message.error) rejectCall(new Error(JSON.stringify(message.error)))
        else resolveCall(message.result)
      } else if (message.method) {
        events.push(message)
      }
    })
    socket.addEventListener('error', () => reject(new Error('CDP websocket failed to connect')))
    socket.addEventListener('open', () => {
      const call = (method, params = {}, timeoutMs = 20_000) =>
        new Promise((resolveCall, rejectCall) => {
          const id = (nextId += 1)
          pending.set(id, { resolveCall, rejectCall })
          socket.send(JSON.stringify({ id, method, params }))
          setTimeout(() => {
            if (pending.delete(id)) rejectCall(new Error(`CDP ${method} timed out`))
          }, timeoutMs)
        })
      const evaluate = async (expression, timeoutMs = 20_000) => {
        const result = await call(
          'Runtime.evaluate',
          { expression, returnByValue: true, awaitPromise: true },
          timeoutMs
        )
        if (result.exceptionDetails) {
          throw new Error(result.exceptionDetails.text || 'evaluation failed')
        }
        return result.result?.value
      }
      resolveConnection({ call, evaluate, events, close: () => socket.close() })
    })
  })
}

async function findPageTarget(debugPort) {
  const targets = await httpJson(`http://127.0.0.1:${debugPort}/json/list`)
  return (
    targets.find(
      (target) =>
        target.type === 'page' &&
        target.webSocketDebuggerUrl &&
        !(target.url || '').includes('recording-indicator') &&
        /^http:\/\/(localhost|127\.0\.0\.1)/.test(target.url || '')
    ) || null
  )
}

function pngSize(buffer) {
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) }
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const guiRoot = join(args.appRoot, 'gui')
  const backendRoot = join(args.appRoot, 'backend')
  const venvPython = join(
    backendRoot,
    '.venv',
    ...(IS_WIN ? ['Scripts', 'python.exe'] : ['bin', 'python'])
  )
  const electronVite = join(guiRoot, 'node_modules', 'electron-vite', 'bin', 'electron-vite.js')
  if (!existsSync(venvPython)) throw new Error(`no backend venv at ${venvPython}`)
  if (!existsSync(electronVite)) throw new Error(`no electron-vite at ${electronVite}`)

  mkdirSync(join(args.out, 'logs'), { recursive: true })
  const home = join(args.out, 'home')
  mkdirSync(join(home, '.speakeasy'), { recursive: true })

  const backendPort = configuredPort()
  if (await portBusy(backendPort)) {
    throw new Error(
      `port ${backendPort} is in use; close the running SpeakEasy app or stop its backend first`
    )
  }
  const debugPort = await freePort()
  writeFileSync(
    join(home, '.speakeasy', 'settings.json'),
    JSON.stringify(
      {
        model_name: '',
        device: 'cpu',
        server_port: backendPort,
        custom_filler_words: [`capture-${Date.now()}`],
        show_recording_indicator: false,
        always_show_indicator: false
      },
      null,
      2
    )
  )

  const scratchEnv = { ...process.env, USERPROFILE: home, HOME: home }
  const backendLog = join(args.out, 'logs', 'backend.log')
  const backendPid = spawnDetached(
    venvPython,
    ['-m', 'speakeasy', '--port', String(backendPort)],
    backendRoot,
    { ...scratchEnv, HF_HOME: join(args.out, 'hf-home'), PYTHONUNBUFFERED: '1' },
    backendLog,
    backendLog
  )
  console.log(`backend pid ${backendPid} on 127.0.0.1:${backendPort} (scratch home ${home})`)

  let guiPid = null
  const captured = []
  const failures = []
  try {
    await waitFor('backend health', async () => {
      const health = await httpJson(`http://127.0.0.1:${backendPort}/api/health`)
      return health.status === 'ok' ? health : null
    }, BACKEND_TIMEOUT_MS)
    console.log('backend healthy')

    if (args.seed) {
      const fixture = JSON.parse(readFileSync(args.seed, 'utf8'))
      const transcriptions = (fixture.transcriptions ?? []).map((record, index) => ({
        ...record,
        created_at:
          record.created_at ?? new Date(Date.now() - index * 21 * 60_000).toISOString()
      }))
      const response = await fetch(`http://127.0.0.1:${backendPort}/api/history/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: { transcriptions }, merge: true })
      })
      if (!response.ok) throw new Error(`seeding failed: POST /api/history/import -> ${response.status}`)
      console.log(`seeded ${JSON.stringify(await response.json())}`)
    }

    guiPid = spawnDetached(
      process.execPath,
      [electronVite, 'dev', '--remoteDebuggingPort', String(debugPort)],
      guiRoot,
      { ...process.env, PYTHONUNBUFFERED: '1' },
      join(args.out, 'logs', 'gui.log'),
      join(args.out, 'logs', 'gui.log')
    )
    console.log(`gui pid ${guiPid}; waiting for CDP on 127.0.0.1:${debugPort}`)

    const target = await waitFor('renderer page target', () => findPageTarget(debugPort), GUI_TIMEOUT_MS, 1000)
    const cdp = await connectCdp(target.webSocketDebuggerUrl)
    try {
      await cdp.call('Runtime.enable')
      await cdp.call('Page.enable')
      await waitFor(
        'app shell',
        () => cdp.evaluate("document.readyState === 'complete' && !!document.querySelector('aside nav')"),
        GUI_TIMEOUT_MS,
        500
      )
      await cdp.call('Emulation.setDeviceMetricsOverride', {
        width: VIEWPORT.width,
        height: VIEWPORT.height,
        deviceScaleFactor: 1,
        mobile: false
      })

      for (const [routeIndex, route] of ROUTES.entries()) {
        const eventStart = cdp.events.length
        const routeFailures = []
        await cdp.evaluate(`location.hash = ${JSON.stringify('#' + route.path)}; true`)

        const check = `(() => {
          const main = document.querySelector('main');
          const text = main ? main.innerText : '';
          return {
            marker: new RegExp(${JSON.stringify(route.marker.source)}, 'i').test(text),
            length: text.trim().length,
            broken: /System Malfunction|Something went wrong|Failed to load/i.test(text)
          };
        })()`

        try {
          await waitFor(`route ${route.path} content`, async () => {
            const state = await cdp.evaluate(check)
            return state.marker && state.length > 40 && !state.broken ? state : null
          }, ROUTE_TIMEOUT_MS, 400)
        } catch (error) {
          const state = await cdp.evaluate(check).catch(() => null)
          routeFailures.push(
            `${route.path} did not render: ${error.message}` +
              (state ? ` (length=${state.length} broken=${state.broken})` : '')
          )
        }

        const uncaught = cdp.events
          .slice(eventStart)
          .filter((event) => event.method === 'Runtime.exceptionThrown')
          .map((event) => event.params?.exceptionDetails?.text || 'unknown exception')
        if (uncaught.length) routeFailures.push(`${route.path} threw: ${uncaught.join('; ')}`)

        for (const theme of args.themes) {
          const override =
            theme === 'default'
              ? "delete root.dataset.theme; delete root.dataset.accent;"
              : `root.dataset.theme = ${JSON.stringify(theme)}; root.dataset.accent = ${JSON.stringify(args.accent)};`
          await cdp.evaluate(`(() => { const root = document.documentElement; ${override} return true })()`)
          await cdp.evaluate(
            'new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))'
          )
          const shot = await cdp.call('Page.captureScreenshot', { format: 'png' })
          const buffer = Buffer.from(shot.data, 'base64')
          const { width, height } = pngSize(buffer)
          const suffix = theme === 'default' ? '' : `-${theme}`
          const file = join(
            args.out,
            `${String(routeIndex + 1).padStart(2, '0')}-${route.name}${suffix}.png`
          )
          writeFileSync(file, buffer)
          if (width !== VIEWPORT.width || height !== VIEWPORT.height) {
            routeFailures.push(
              `${route.name}${suffix} captured ${width}x${height}, expected ${VIEWPORT.width}x${VIEWPORT.height}`
            )
          }
          captured.push({ route: route.path, theme, file })
          console.log(`captured ${file.split(/[\\/]/).pop()} (${width}x${height}, ${buffer.length} bytes)`)
        }

        if (routeFailures.length) failures.push(...routeFailures)
      }
    } finally {
      cdp.close()
    }
  } catch (error) {
    failures.push(error.message)
  } finally {
    if (!args.keep) {
      killTree(guiPid)
      killTree(backendPid)
      await waitFor('process shutdown', async () => {
        try {
          await fetch(`http://127.0.0.1:${backendPort}/api/health`)
          return false
        } catch {
          return true
        }
      }, 20_000, 500).catch(() => console.warn('warning: backend still answering after stop'))
    } else {
      console.log(`--keep: gui pid ${guiPid}, backend pid ${backendPid}`)
    }
  }

  const meta = {
    appRoot: args.appRoot,
    backendPort,
    debugPort,
    themes: args.themes,
    accent: args.accent,
    seeded: Boolean(args.seed),
    viewport: VIEWPORT,
    captured,
    failures,
    finishedAt: new Date().toISOString()
  }
  writeFileSync(join(args.out, 'capture-run.json'), JSON.stringify(meta, null, 2))

  console.log(`\n${captured.length} captures in ${args.out}`)
  if (failures.length) {
    console.error(`${failures.length} failure(s):`)
    for (const failure of failures) console.error(`  - ${failure}`)
    process.exit(1)
  }
}

main().catch((error) => {
  console.error(`capture:ui failed: ${error.message}`)
  process.exit(1)
})
