/**
 * WebSocket Client for real-time updates
 */

import type { WebSocketEvent, StatusEvent, TranscriptionEvent, ErrorEvent } from './types'

type EventCallback<T = WebSocketEvent> = (event: T) => void

interface InternalEvent {
  type: string
  [key: string]: unknown
}

interface QueuedMessage {
  event: string
  data: WebSocketEvent | InternalEvent
  priority: 'critical' | 'normal'
  timestamp: number
}

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private listeners: Map<string, Set<EventCallback>> = new Map()
  private isIntentionallyClosed = false
  
  // Message queue and throttling
  private messageQueue: QueuedMessage[] = []
  private flushInterval: number | null = null
  private readonly FLUSH_INTERVAL_MS = 100
  private readonly MAX_MESSAGES_PER_SECOND = 10
  private lastEmitTimes: Map<string, number> = new Map()
  private readonly criticalEvents = new Set(['error', 'close', 'open'])

  constructor(port: number = 8765) {
    this.url = `ws://127.0.0.1:${port}/api/ws`
  }

  setPort(port: number): void {
    this.url = `ws://127.0.0.1:${port}/api/ws`
    // Reconnect if currently connected
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.disconnect()
      this.connect()
    }
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.isIntentionallyClosed = false
    this.startFlushInterval()
    
    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.emitMessage('open', { type: 'open' }, 'critical')
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketEvent
          const priority = this.criticalEvents.has(data.type) ? 'critical' : 'normal'
          this.emitMessage(data.type, data, priority)
          this.emitMessage('message', data, priority)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed')
        this.stopFlushInterval()
        this.emitMessage('close', { type: 'close' }, 'critical')
        
        if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
          setTimeout(() => this.connect(), delay)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.emitMessage('error', { type: 'error', message: 'WebSocket connection error' }, 'critical')
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }

  disconnect(): void {
    this.isIntentionallyClosed = true
    this.stopFlushInterval()
    this.flushQueue()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  ping(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send('ping')
    }
  }

  // Event subscription
  on<T = WebSocketEvent>(event: string, callback: EventCallback<T>): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback as EventCallback)
    
    // Return unsubscribe function
    return () => this.off(event, callback)
  }

  off<T = WebSocketEvent>(event: string, callback: EventCallback<T>): void {
    this.listeners.get(event)?.delete(callback as EventCallback)
  }

  private emitMessage(event: string, data: WebSocketEvent | InternalEvent, priority: 'critical' | 'normal'): void {
    if (priority === 'critical') {
      this.emitImmediately(event, data)
      return
    }

    if (this.shouldThrottle(event)) {
      this.queueMessage(event, data, priority)
    } else {
      this.emitImmediately(event, data)
      this.lastEmitTimes.set(event, Date.now())
    }
  }

  private emitImmediately(event: string, data: WebSocketEvent | InternalEvent): void {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(data as WebSocketEvent)
      } catch (error) {
        console.error(`Error in ${event} listener:`, error)
      }
    })
  }

  private shouldThrottle(event: string): boolean {
    const lastEmit = this.lastEmitTimes.get(event)
    if (!lastEmit) return false
    
    const timeSinceLastEmit = Date.now() - lastEmit
    const minInterval = 1000 / this.MAX_MESSAGES_PER_SECOND
    return timeSinceLastEmit < minInterval
  }

  private queueMessage(event: string, data: WebSocketEvent | InternalEvent, priority: 'critical' | 'normal'): void {
    const existingIndex = this.messageQueue.findIndex(
      msg => msg.event === event && msg.data.type === data.type
    )
    
    if (existingIndex !== -1) {
      this.messageQueue[existingIndex] = { event, data, priority, timestamp: Date.now() }
    } else {
      this.messageQueue.push({ event, data, priority, timestamp: Date.now() })
    }
  }

  private startFlushInterval(): void {
    if (this.flushInterval !== null) return
    
    this.flushInterval = window.setInterval(() => {
      this.flushQueue()
    }, this.FLUSH_INTERVAL_MS)
  }

  private stopFlushInterval(): void {
    if (this.flushInterval !== null) {
      clearInterval(this.flushInterval)
      this.flushInterval = null
    }
  }

  private flushQueue(): void {
    if (this.messageQueue.length === 0) return

    const messagesToFlush = [...this.messageQueue]
    this.messageQueue = []

    messagesToFlush.forEach(({ event, data }) => {
      this.emitImmediately(event, data)
      this.lastEmitTimes.set(event, Date.now())
    })
  }

  // Typed event helpers
  onStatus(callback: EventCallback<StatusEvent>): () => void {
    return this.on('status', callback)
  }

  onTranscription(callback: EventCallback<TranscriptionEvent>): () => void {
    return this.on('transcription', callback)
  }

  onTranscriptionUpdate(callback: EventCallback<TranscriptionEvent>): () => void {
    return this.on('transcription_update', callback)
  }

  onError(callback: EventCallback<ErrorEvent>): () => void {
    return this.on('error', callback)
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// Singleton instance
export const wsClient = new WebSocketClient()

export default wsClient
