/**
 * RecordingIndicator Component
 * 
 * Minimal floating overlay shown in the center of the screen while recording.
 * This is rendered in a separate frameless window.
 */

import { useEffect, useState, useRef } from 'react'
import { useToast } from '../hooks/useToast'

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

export default function RecordingIndicator(): JSX.Element {
  const [duration, setDuration] = useState(0)
  const [status, setStatus] = useState<'recording' | 'transcribing' | 'idle'>('idle')
  const [lastError, setLastError] = useState<string | null>(null)
  const { toast } = useToast()
  const prevStatus = useRef<'recording' | 'transcribing' | 'idle'>('recording')
  
  // Timer effect
  useEffect(() => {
    if (status !== 'recording') {
      setDuration(0)
      return
    }
    
    const startTime = Date.now()
    setDuration(0) // Reset immediately when recording starts
    const interval = setInterval(() => {
      setDuration(Date.now() - startTime)
    }, 100)
    
    return () => clearInterval(interval)
  }, [status])
  
  // Listen for recording events from main process
  useEffect(() => {
    const unsubStart = window.api?.onRecordingStart(() => {
      setStatus('recording')
      setDuration(0)
    })
    
    const unsubComplete = window.api?.onRecordingComplete(() => {
      setStatus('idle')
    })
    
    const unsubError = window.api?.onRecordingError((error: string) => {
      setLastError(error)
      setStatus('idle')
    })
    
    return () => {
      unsubStart?.()
      unsubComplete?.()
      unsubError?.()
    }
  }, [])
  
  // Detect transcription completion and show toast
  useEffect(() => {
    if (lastError) {
      toast.error(`Transcription failed: ${lastError}`)
      setLastError(null)
    } else if (prevStatus.current === 'transcribing' && status === 'idle') {
      toast.success('Transcription complete!')
    }
    prevStatus.current = status
  }, [status, lastError, toast])
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-transparent">
      <div 
        className={`
          flex items-center gap-3 px-5 py-3 rounded-full
          bg-gray-900/95 border shadow-2xl backdrop-blur-sm
          ${status === 'recording' 
            ? 'border-red-500/50 recording-pulse' 
            : 'border-blue-500/50'
          }
        `}
      >
        {/* Recording indicator dot */}
        {status === 'recording' && (
          <div className="relative">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="absolute inset-0 w-3 h-3 rounded-full bg-red-500 animate-ping" />
          </div>
        )}
        
        {/* Transcribing spinner */}
        {status === 'transcribing' && (
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        )}
        
        {/* Status text */}
        <span className={`
          text-sm font-medium
          ${status === 'recording' ? 'text-red-400' : 'text-blue-400'}
        `}>
          {status === 'recording' ? 'Recording' : 'Transcribing...'}
        </span>
        
        {/* Timer */}
        {status === 'recording' && (
          <span className="text-sm font-mono text-gray-400 min-w-[50px]">
            {formatTime(duration)}
          </span>
        )}
      </div>
    </div>
  )
}
