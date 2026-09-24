import { motion } from 'motion/react'
import { Loader2 } from 'lucide-react'

export function TranscribingLine(): JSX.Element {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="overlay-pill"
    >
      <Loader2 size={16} className="animate-spin text-accent-text" aria-hidden="true" />
      <span className="overlay-pill-text">Processing...</span>
    </motion.div>
  )
}
