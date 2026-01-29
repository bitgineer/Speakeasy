/**
 * RecordingIndicator Component
 * 
 * Minimalist floating pill shown while recording.
 * Features audio waveform, timer, and quick cancel.
 */

import { useEffect, useState, useRef } from 'react'
import { useSettingsStore } from '../store'

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

// Minimalist animated waveform
function AudioWaveform(): JSX.Element {
  const bars = [0.4, 0.7, 1, 0.6, 0.8, 0.5, 0.9, 0.6, 1, 0.7]
  
  return (
    <div className="flex items-center gap-[3px] h-6 mx-3">
      {bars.map((height, i) => (
        <div
          key={i}
          className="w-[3px] rounded-full bg-red-500/90 shadow-[0_0_8px_rgba(239,68,68,0.5)]"
          style={{
            animation: `waveform 0.8s ease-in-out infinite`,
            animationDelay: `${i * 0.08}s`,
            height: `${height * 100}%`
          }}
        />
      ))}
    </div>
  )
}

export default function RecordingIndicator(): JSX.Element {
  const [duration, setDuration] = useState(0)
  const [status, setStatus] = useState<'recording' | 'transcribing' | 'idle'>('idle')
  const [isLocked, setIsLocked] = useState(false)
  const startTimeRef = useRef<number>(0)
  const { settings, fetchSettings } = useSettingsStore()
  
  // Force transparent background on mount
  useEffect(() => {
    // Save original styles
    const originalHtmlBg = document.documentElement.style.background
    const originalBodyBg = document.body.style.background
    const originalBodyOverflow = document.body.style.overflow
    
    // Apply transparent styles with !important to override Tailwind classes
    document.documentElement.style.setProperty('background', 'transparent', 'important')
    document.body.style.setProperty('background', 'transparent', 'important')
    document.body.style.setProperty('overflow', 'hidden', 'important')
    
    // Initial settings fetch
    fetchSettings()
    
    // Poll settings to react to changes (simple sync)
    const interval = setInterval(() => fetchSettings(), 2000)
    
    return () => {
      // Restore styles on unmount
      document.documentElement.style.background = originalHtmlBg
      document.body.style.background = originalBodyBg
      document.body.style.overflow = originalBodyOverflow
      clearInterval(interval)
    }
  }, [fetchSettings])
  
  // Manage visibility based on settings
  useEffect(() => {
    if (!settings) return
    
    const showFeature = settings.show_recording_indicator ?? true
    const alwaysShow = settings.always_show_indicator ?? true
    
    if (!showFeature) {
      window.api?.hideIndicator?.()
      return
    }
    
    if (status === 'idle') {
      if (alwaysShow) {
        window.api?.showIndicator?.()
      } else {
        window.api?.hideIndicator?.()
      }
    } else {
      // Recording/Transcribing
      window.api?.showIndicator?.()
    }
  }, [status, settings])

  // Timer effect
  useEffect(() => {
    if (status !== 'recording') {
      return
    }
    
    startTimeRef.current = Date.now()
    setDuration(0)
    const interval = setInterval(() => {
      setDuration(Date.now() - startTimeRef.current)
    }, 100)
    
    return () => clearInterval(interval)
  }, [status])
  
  // Listen for recording events and sync initial state
  useEffect(() => {
    // Check initial state (in case window reloaded/re-rendered)
    window.api?.getRecordingStatus?.().then((isActive: boolean) => {
      if (isActive) {
        setStatus('recording')
        setIsLocked(false) // Assume not locked initially, or we'd need isLocked status from backend too
        // For now, if we recover, we just show recording state. 
        // We could ask for lock state too, but recording is most important.
      }
    })

    const unsubStart = window.api?.onRecordingStart(() => {
      setStatus('recording')
      setIsLocked(false)
      setDuration(0)
    })
    
    const unsubLocked = window.api?.onRecordingLocked?.(() => {
      setIsLocked(true)
    })
    
    const unsubComplete = window.api?.onRecordingComplete(() => {
      setStatus('idle')
      setIsLocked(false)
    })
    
    const unsubError = window.api?.onRecordingError(() => {
      setStatus('idle')
      setIsLocked(false)
    })
    
    return () => {
      unsubStart?.()
      unsubLocked?.()
      unsubComplete?.()
      unsubError?.()
    }
  }, [])
  
  // When idle, render Ready state (Always On)
  if (status === 'idle') {
    return (
      <div className="flex items-center justify-center w-full h-full overflow-hidden">
        <div 
          className="
            flex items-center h-9 px-4 rounded-full
            bg-[#0a0a0a]/60 backdrop-blur-sm
            border border-zinc-800/30
            shadow-lg hover:bg-[#0a0a0a]/80 hover:border-zinc-700/50 transition-all
            cursor-default select-none
          "
        >
          <div className="w-2 h-2 rounded-full bg-zinc-500 mr-2" />
          <span className="text-xs font-medium text-zinc-400">Ready</span>
        </div>
      </div>
    )
  }
  
  return (
    <div className="flex items-center justify-center w-full h-full overflow-hidden">
      {/* Sleek Horizontal Pill */}
      <div 
        className={`
          flex items-center h-12 px-1 pl-2 rounded-full
          bg-[#0a0a0a]/90 backdrop-blur-md
          border ${isLocked ? 'border-yellow-500/50' : 'border-zinc-800/50'}
          shadow-lg shadow-black/40
          transition-all duration-300
        `}
      >
        {status === 'recording' ? (
          <>
            {/* 1. Pulse Indicator */}
            <div className="relative flex items-center justify-center w-8 h-8 ml-1">
              <div className={`absolute w-full h-full rounded-full ${isLocked ? 'bg-yellow-500/20' : 'bg-red-500/20'} animate-ping opacity-75`} />
              <div className={`w-2.5 h-2.5 rounded-full ${isLocked ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.8)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]'}`} />
            </div>

            {/* 2. Waveform */}
            <AudioWaveform />
            
            {/* 3. Timer & Status */}
            <div className="flex flex-col items-center justify-center min-w-[60px] mx-2">
              <div className={`text-sm font-mono font-bold ${isLocked ? 'text-amber-400' : 'text-zinc-100'} tracking-wide`}>
                {formatTime(duration)}
              </div>
              {isLocked && (
                <div className="text-[9px] font-bold text-amber-500 uppercase leading-none mt-0.5 animate-pulse">
                  LOCKED
                </div>
              )}
            </div>

            {/* Lock Icon / Instruction */}
            {isLocked && (
              <div className="flex items-center text-amber-500 mr-2 animate-in fade-in slide-in-from-left-2 duration-300">
                <svg className="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span className="text-[10px] font-medium whitespace-nowrap opacity-80">
                  Press hotkey to stop
                </span>
              </div>
            )}

            {/* 4. Divider (Hidden if locked to save space/reduce clutter) */}
            {!isLocked && <div className="w-px h-5 bg-zinc-800 mx-2" />}

            {/* 5. Cancel Button */}
            <button
              onClick={() => window.api?.cancelRecording?.()}
              className="
                flex items-center justify-center w-7 h-7 rounded-full
                text-zinc-500 hover:text-white hover:bg-zinc-800
                transition-all mr-1
              "
              title="Cancel Recording"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </>
        ) : (
          /* Transcribing State */
          <div className="flex items-center gap-3 px-3">
            <div className="w-4 h-4 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            <span className="text-sm font-medium text-zinc-200">Transcribing...</span>
          </div>
        )}
      </div>
      
      {/* CSS for animations */}
      <style>{`
        @keyframes waveform {
          0%, 100% { height: 30%; opacity: 0.6; }
          50% { height: 100%; opacity: 1; }
        }
      `}</style>
    </div>
  )
}
