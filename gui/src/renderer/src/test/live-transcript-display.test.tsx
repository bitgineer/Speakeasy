import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen, waitFor } from '@testing-library/react'
import App from '../App'
import RecordingIndicator from '../components/RecordingIndicator'

class FakeWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
  static instances: FakeWebSocket[] = []

  url: string
  readyState = FakeWebSocket.CONNECTING
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: ((event: { code: number; reason: string }) => void) | null = null
  onerror: ((event: unknown) => void) | null = null

  constructor(url: string) {
    this.url = url
    FakeWebSocket.instances.push(this)
  }

  send(): void {}

  close(): void {
    this.readyState = FakeWebSocket.CLOSED
  }
}

function setWindowApi(overrides: Record<string, unknown> = {}): void {
  ;(window as unknown as { api: Record<string, unknown> }).api = {
    sendLiveTranscript: vi.fn(),
    onNavigate: vi.fn(() => () => {}),
    onRecordingStart: vi.fn(() => () => {}),
    onRecordingLocked: vi.fn(() => () => {}),
    onRecordingProcessing: vi.fn(() => () => {}),
    onRecordingComplete: vi.fn(() => () => {}),
    onRecordingError: vi.fn(() => () => {}),
    onLiveTranscript: vi.fn(() => () => {}),
    getRecordingStatus: vi.fn(() => Promise.resolve(false)),
    resizeIndicator: vi.fn(),
    showIndicator: vi.fn(),
    hideIndicator: vi.fn(),
    ...overrides,
  }
}

describe('live transcript display wiring', () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    vi.stubGlobal('WebSocket', FakeWebSocket)
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    setWindowApi()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    delete (window as unknown as { api?: unknown }).api
  })

  it('connects the WebSocket on mount and relays live_transcript text to the overlay', async () => {
    render(<App />)

    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1))

    const socket = FakeWebSocket.instances[0]
    act(() => {
      socket.readyState = FakeWebSocket.OPEN
      socket.onopen?.()
    })

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({ type: 'live_transcript', text: 'hello world' }),
      })
    })

    expect(
      (window as unknown as { api: { sendLiveTranscript: ReturnType<typeof vi.fn> } }).api
        .sendLiveTranscript
    ).toHaveBeenCalledWith('hello world')
  })

  it('renders live transcript text in the recording indicator while recording', () => {
    const startHandlers: Array<() => void> = []
    const liveHandlers: Array<(text: string) => void> = []
    setWindowApi({
      onRecordingStart: vi.fn((cb: () => void) => {
        startHandlers.push(cb)
        return () => {}
      }),
      onLiveTranscript: vi.fn((cb: (text: string) => void) => {
        liveHandlers.push(cb)
        return () => {}
      }),
    })

    render(<RecordingIndicator />)

    act(() => startHandlers.forEach((cb) => cb()))
    act(() => liveHandlers.forEach((cb) => cb('spoken words')))

    expect(screen.getByText('spoken words')).toBeTruthy()
  })
})
