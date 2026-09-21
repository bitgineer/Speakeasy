/**
 * useWebSocket Hook
 * 
 * Connects to the backend WebSocket for real-time updates.
 * Updates stores based on WebSocket events.
 */

import { useEffect, useCallback } from 'react'
import wsClient from '../api/websocket'
import { useAppStore, useHistoryStore } from '../store'
import { useDownloadStore } from '../store/download-store'
import type { StatusEvent, TranscriptionEvent, ErrorEvent, WebSocketEvent, DownloadProgressEvent, LiveTranscriptEvent } from '../api/types'

interface UseWebSocketOptions {
  port?: number
  enabled?: boolean
}

export function useWebSocket(options: UseWebSocketOptions = {}): {
  isConnected: boolean
  reconnect: () => void
} {
  const { port = 8765, enabled = true } = options
  
  const { 
    setWsConnected, 
    setAppState, 
    startRecording, 
    stopRecording,
    setError 
  } = useAppStore()
  const { addItem } = useHistoryStore()
  const { updateFromWebSocket } = useDownloadStore()
  
  const handleMessage = useCallback((event: WebSocketEvent) => {
    switch (event.type) {
      case 'connected':
        setWsConnected(true)
        break
        
      case 'status': {
        const statusEvent = event as StatusEvent
        if (statusEvent.recording) {
          startRecording()
        } else if (statusEvent.state === 'transcribing') {
          stopRecording()
          useAppStore.getState().setLiveTranscriptText('')
        } else {
          setAppState('idle')
          useAppStore.getState().setLiveTranscriptText('')
        }
        break
      }
      
      case 'transcription': {
        const transcriptionEvent = event as TranscriptionEvent
        addItem({
          id: transcriptionEvent.id,
          text: transcriptionEvent.text,
          duration_ms: transcriptionEvent.duration_ms,
          model_used: null,
          language: null,
          created_at: new Date().toISOString(),
          original_text: null,
          is_ai_enhanced: false
        })
        setAppState('idle')
        break
      }
      
      case 'error': {
        const errorEvent = event as ErrorEvent
        setError(errorEvent.message)
        setAppState('error')
        break
      }
      
      case 'download_progress':
        updateFromWebSocket(event as DownloadProgressEvent)
        break

      case 'live_transcript': {
        const liveEvent = event as LiveTranscriptEvent
        useAppStore.getState().setLiveTranscriptText(liveEvent.text)
        // Also send to recording indicator overlay window via IPC
        window.api?.sendLiveTranscript?.(liveEvent.text)
        break
      }
    }
  }, [setWsConnected, setAppState, startRecording, stopRecording, setError, addItem, updateFromWebSocket])
  
  const handleDisconnect = useCallback(() => {
    setWsConnected(false)
  }, [setWsConnected])
  
  const handleError = useCallback(() => {
    setWsConnected(false)
  }, [setWsConnected])
  
  useEffect(() => {
    if (!enabled) return
    
    wsClient.setPort(port)
    
    const unsubMessage = wsClient.on('message', handleMessage)
    const unsubClose = wsClient.on('close', handleDisconnect)
    const unsubError = wsClient.on('error', handleError)
    
    wsClient.connect()
    
    return () => {
      unsubMessage()
      unsubClose()
      unsubError()
    }
  }, [port, enabled, handleMessage, handleDisconnect, handleError])
  
  const reconnect = useCallback(() => {
    wsClient.disconnect()
    wsClient.connect()
  }, [])
  
  return {
    isConnected: useAppStore.getState().wsConnected,
    reconnect
  }
}

export default useWebSocket
