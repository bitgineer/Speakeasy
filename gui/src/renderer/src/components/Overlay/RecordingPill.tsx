import { motion } from 'motion/react'
import { Square, Lock, X } from 'lucide-react'

interface RecordingPillProps {
  durationMs: number
  onStop: () => void
  onCancel: () => void
  isLocked?: boolean
  mode?: string | null
}

export function RecordingPill({
  durationMs,
  onStop,
  onCancel,
  isLocked,
  mode,
}: RecordingPillProps): JSX.Element {
  const seconds = Math.floor(durationMs / 1000)
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  const time = `${mins}:${secs.toString().padStart(2, '0')}`

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="overlay-pill"
    >
      <span className="overlay-recording-dot" aria-hidden="true">
        <motion.span
          animate={{ scale: [1, 2.5, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="overlay-recording-ring"
        />
        <span className="overlay-recording-core" />
      </span>

      {isLocked && (
        <motion.span
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          className="-ml-1"
        >
          <Lock size={14} className="text-danger-text" aria-hidden="true" />
        </motion.span>
      )}

      {mode && <span className="overlay-mode">{mode}</span>}

      <span className="overlay-timer">{time}</span>

      <span className="overlay-divider" aria-hidden="true" />

      <button
        type="button"
        onClick={onStop}
        title="Stop and transcribe"
        aria-label="Stop and transcribe"
        className="overlay-action overlay-action--stop"
      >
        <Square size={14} aria-hidden="true" />
      </button>

      <button
        type="button"
        onClick={onCancel}
        title="Cancel recording"
        aria-label="Cancel recording"
        className="overlay-action"
      >
        <X size={14} aria-hidden="true" />
      </button>
    </motion.div>
  )
}
