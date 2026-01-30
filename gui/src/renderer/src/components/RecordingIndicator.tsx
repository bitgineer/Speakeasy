import { useEffect, useState, useRef, useLayoutEffect, useCallback } from 'react'
import { useSettingsStore } from '../store'
import { OverlayContainer } from './Overlay/OverlayContainer'
import { IdlePill } from './Overlay/IdlePill'
import { RecordingPill } from './Overlay/RecordingPill'
import { TranscribingLine } from './Overlay/TranscribingLine'

export default function RecordingIndicator(): JSX.Element | null {
  const [status, setStatus] = useState<'recording' | 'transcribing' | 'idle' | 'locked'>('idle')
  const [duration, setDuration] = useState(0)
  const startTimeRef = useRef<number>(0)
  const contentRef = useRef<HTMLDivElement>(null)
  
  const { settings, fetchSettings } = useSettingsStore()
  
  // Timer effect
  useEffect(() => {
    if (status !== 'recording' && status !== 'locked') {
      return
    }
    
    // If start time hasn't been set (e.g. page refresh during recording), start from now
    if (startTimeRef.current === 0) {
      startTimeRef.current = Date.now()
    }

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
  

  
  // Listen for recording events
  useEffect(() => {
    window.api?.getRecordingStatus?.().then((isActive: boolean) => {
      if (isActive) setStatus('recording')
    })

    const unsubStart = window.api?.onRecordingStart(() => {
      setStatus('recording')
      setDuration(0)
      startTimeRef.current = Date.now()
    })
    
    const unsubLocked = window.api?.onRecordingLocked?.(() => {
      setStatus('locked')
    })
    
    const unsubProcessing = window.api?.onRecordingProcessing(() => {
      setStatus('transcribing')
    })

    const unsubComplete = window.api?.onRecordingComplete(() => {
      setStatus('idle')
      startTimeRef.current = 0
    })
    
    const unsubError = window.api?.onRecordingError(() => {
      setStatus('idle')
      startTimeRef.current = 0
    })
    
    return () => {
      unsubStart?.()
      unsubLocked?.()
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
      // Recording/Locked/Transcribing
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
          
          {(status === 'recording' || status === 'locked') && (
            <RecordingPill 
              durationMs={duration} 
              onStop={handleStop} 
              isLocked={status === 'locked'}
            />
          )}
          
          {status === 'transcribing' && (
            <TranscribingLine />
          )}
        </OverlayContainer>
      </div>
    </div>
  )
}
