import { motion } from 'motion/react'
import { Loader2 } from 'lucide-react'

export function TranscribingLine(): JSX.Element {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex items-center gap-3 bg-black/80 text-white px-4 py-2.5 rounded-full backdrop-blur-md shadow-xl outline-none ring-0 border-0"
    >
      <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
      <span className="text-sm font-medium text-zinc-200">Processing...</span>
    </motion.div>
  )
}
