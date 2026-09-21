import { motion } from 'motion/react'
import { Square, Lock } from 'lucide-react'

interface RecordingPillProps {
  durationMs: number
  onStop: () => void
  isLocked?: boolean
}

export function RecordingPill({ durationMs, onStop, isLocked }: RecordingPillProps): JSX.Element {
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
      className="flex items-center gap-4 bg-black/90 text-white px-4 py-2.5 rounded-full backdrop-blur-md shadow-2xl outline-none ring-0 border-0"
    >
      <div className="relative flex items-center justify-center w-3 h-3">
        <motion.div
          animate={{ scale: [1, 2.5, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="absolute w-full h-full bg-red-500 rounded-full"
        />
        <div className="relative w-2.5 h-2.5 bg-red-500 rounded-full shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
      </div>

      {isLocked && (
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          className="-ml-1"
        >
          <Lock className="w-4 h-4 text-red-400" />
        </motion.div>
      )}

      <span className="font-mono text-lg font-medium tracking-wide min-w-[60px] text-center">
        {time}
      </span>

      <div className="h-5 w-px bg-white/10" />

      <button
        onClick={onStop}
        className="p-1.5 hover:bg-white/10 rounded-full transition-colors group"
      >
        <Square className="w-4 h-4 fill-zinc-400 text-zinc-400 group-hover:fill-white group-hover:text-white transition-colors" />
      </button>
    </motion.div>
  )
}
