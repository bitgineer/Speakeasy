import { useEffect, useState, useRef, useLayoutEffect, useCallback } from 'react'
import { useSettingsStore } from '../store'
import { OverlayContainer } from './Overlay/OverlayContainer'
import { IdlePill } from './Overlay/IdlePill'
import { RecordingPill } from './Overlay/RecordingPill'
import { TranscribingLine } from './Overlay/TranscribingLine'

export default function RecordingIndicator(): JSX.Element | null {
  const [status, setStatus] = useState<'recording' | 'transcribing' | 'idle' | 'locked' | 'loading'>('idle')
  const [duration, setDuration] = useState(0)
  const startTimeRef = useRef<number>(0)
  const contentRef = useRef<HTMLDivElement>(null)
  
  const { settings, fetchSettings } = useSettingsStore()

  // Listen for backend loading status
  useEffect(() => {
    // Poll for status or listen for events if available
    // For now we can use the window.api if exposed, or rely on AppStore status if we can access it.
    // Since this is a separate window, we might need to rely on IPC events for status updates.
    
    const checkStatus = async () => {
        try {
            const health = await window.api?.checkHealth?.()
            if (health && health.state === 'loading') {
                setStatus('loading')
            } else if (status === 'loading' && health && health.state === 'ready') {
                setStatus('idle')
            }
        } catch (e) {
            // ignore
        }
    }
    
    const interval = setInterval(checkStatus, 1000)
    return () => clearInterval(interval)
  }, [status])
  
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
      // Small buffer for hover zone (OverlayContainer has p-2)
      const width = Math.ceil(rect.width) + 8
      const height = Math.ceil(rect.height) + 8
      window.api?.resizeIndicator?.(width, height)
    }
  }, [])

  // Use ResizeObserver to catch dynamic size changes (hover, animations, etc.)
  useLayoutEffect(() => {
    if (!contentRef.current) return

    const resizeObserver = new ResizeObserver(() => {
      updateWindowSize()
    })

    resizeObserver.observe(contentRef.current)

    return () => {
      resizeObserver.disconnect()
    }
  }, [updateWindowSize])
  

  
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
    // If settings haven't loaded yet, don't do anything to avoid flashing
    if (!settings) return
    
    const showFeature = settings.show_recording_indicator ?? true
    const alwaysShow = settings.always_show_indicator ?? true
    
    // If the entire feature is disabled, hide it regardless of state
    if (!showFeature) {
      window.api?.hideIndicator?.()
      return
    }
    
    // Feature is enabled, check specific states
    if (status === 'idle') {
      if (alwaysShow) {
        window.api?.showIndicator?.()
      } else {
        window.api?.hideIndicator?.()
      }
    } else {
      // Recording/Locked/Transcribing/Loading -> Always show
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
      {/* Just the pill button - no background layers */}
      <OverlayContainer ref={contentRef} className="flex items-center justify-center">
        {status === 'loading' && (
             <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--color-bg-secondary)] rounded-full border border-[var(--color-border)] select-none animate-pulse">
                <div className="w-3 h-3 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin" />
                <span className="text-xs font-medium text-[var(--color-text-primary)] whitespace-nowrap">
                  Loading...
                </span>
             </div>
        )}

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
  )
}
