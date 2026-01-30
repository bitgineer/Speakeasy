import { useEffect, useState, useRef, useLayoutEffect, useCallback } from 'react'
import { useSettingsStore } from '../store'
import { OverlayContainer } from './Overlay/OverlayContainer'
import { IdlePill } from './Overlay/IdlePill'
import { RecordingPill } from './Overlay/RecordingPill'
import { TranscribingLine } from './Overlay/TranscribingLine'

export default function RecordingIndicator(): JSX.Element | null {
  const [status, setStatus] = useState<'recording' | 'transcribing' | 'idle'>('idle')
  const [duration, setDuration] = useState(0)
  const startTimeRef = useRef<number>(0)
  const contentRef = useRef<HTMLDivElement>(null)
  
  const { settings, fetchSettings } = useSettingsStore()
  
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

  // Measure content and resize window to fit
  const updateWindowSize = useCallback(() => {
    if (contentRef.current) {
      const rect = contentRef.current.getBoundingClientRect()
      // Add buffer for shadows (shadow-xl needs space)
      const width = Math.ceil(rect.width) + 40
      const height = Math.ceil(rect.height) + 40
      window.api?.resizeIndicator?.(width, height)
    }
  }, [])
  
  // Update window size when content changes
  useLayoutEffect(() => {
    updateWindowSize()
  }, [status, duration, updateWindowSize])
  
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
  
  // Listen for recording events
  useEffect(() => {
    window.api?.getRecordingStatus?.().then((isActive: boolean) => {
      if (isActive) setStatus('recording')
    })

    const unsubStart = window.api?.onRecordingStart(() => {
      setStatus('recording')
      setDuration(0)
    })
    
    const unsubProcessing = window.api?.onRecordingProcessing(() => {
      setStatus('transcribing')
    })

    const unsubComplete = window.api?.onRecordingComplete(() => {
      setStatus('idle')
    })
    
    const unsubError = window.api?.onRecordingError(() => {
      setStatus('idle')
    })
    
    return () => {
      unsubStart?.()
      unsubProcessing?.()
      unsubComplete?.()
      unsubError?.()
    }
  }, [])
  
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
  
  // Handlers
  const handleStart = (): void => {
    window.api?.startRecording?.()
  }
  
  const handleStop = (): void => {
    window.api?.stopRecording?.()
  }

  return (
    <div className="flex items-center justify-center w-full h-full overflow-hidden">
      {/* Wrapper to capture dimensions including shadows */}
      <div ref={contentRef} className="p-4">
        <OverlayContainer className="flex items-center justify-center">
          {status === 'idle' && (
            <IdlePill onClick={handleStart} />
          )}
          
          {status === 'recording' && (
            <RecordingPill durationMs={duration} onStop={handleStop} />
          )}
          
          {status === 'transcribing' && (
            <TranscribingLine />
          )}
        </OverlayContainer>
      </div>
    </div>
  )
}
