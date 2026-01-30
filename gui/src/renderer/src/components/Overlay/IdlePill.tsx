import { motion } from 'motion/react'
import { Mic } from 'lucide-react'

interface IdlePillProps {
  onClick?: () => void
}

export function IdlePill({ onClick }: IdlePillProps): JSX.Element {
  return (
    <motion.button
      layout
      initial={{ width: 'auto' }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className="group flex items-center gap-2 bg-black/80 text-white p-2.5 rounded-full backdrop-blur-md shadow-xl overflow-hidden hover:pr-5 transition-all duration-300 outline-none ring-0 border-0"
    >
      <div className="p-1 bg-white/10 rounded-full group-hover:bg-red-500/20 transition-colors">
        <Mic className="w-5 h-5 text-zinc-300 group-hover:text-red-500 transition-colors" />
      </div>
      <span className="max-w-0 opacity-0 group-hover:max-w-[200px] group-hover:opacity-100 whitespace-nowrap overflow-hidden transition-all duration-300 text-sm font-medium">
        Start Recording
      </span>
    </motion.button>
  )
}
