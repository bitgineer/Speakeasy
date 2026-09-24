import { motion } from 'motion/react'
import { Mic } from 'lucide-react'

interface IdlePillProps {
  onClick?: () => void
  mode?: string | null
}

export function IdlePill({ onClick, mode }: IdlePillProps): JSX.Element {
  const modeLabel = mode ? mode.charAt(0).toUpperCase() + mode.slice(1) : null
  const label = modeLabel ? `${modeLabel} · Start recording` : 'Start recording'

  return (
    <motion.button
      layout
      initial={{ width: 'auto' }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      title={modeLabel ? `Start recording in ${modeLabel} mode` : 'Start recording'}
      aria-label={label}
      className="overlay-idle"
    >
      <span className="overlay-idle-glyph">
        <Mic size={20} aria-hidden="true" />
      </span>
      <span className="overlay-idle-label">{label}</span>
    </motion.button>
  )
}
