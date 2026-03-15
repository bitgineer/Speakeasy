/**
 * ConfidenceText Component
 *
 * Renders transcription text with per-word confidence highlighting.
 * Uses word_data from faster-whisper to color-code low-confidence words.
 *
 * Confidence thresholds:
 *   >= 0.9  → normal text (no highlight)
 *   >= 0.7  → amber (text-amber-400) — worth a second look
 *   <  0.7  → red (text-red-400) — likely error
 *
 * Falls back to plain text when word_data is null (NeMo/Voxtral models).
 */

import type { WordData } from '../api/types'

interface ConfidenceTextProps {
  text: string
  wordData: WordData[] | null
}

function getConfidenceClass(probability: number): string {
  if (probability >= 0.9) return ''
  if (probability >= 0.7) return 'text-amber-400'
  return 'text-red-400'
}

function ConfidenceText({ text, wordData }: ConfidenceTextProps): JSX.Element {
  // Graceful fallback: no word data means plain text (NeMo/Voxtral models)
  if (!wordData || wordData.length === 0) {
    return <span>{text}</span>
  }

  return (
    <span>
      {wordData.map((w, i) => {
        const cls = getConfidenceClass(w.probability)
        const pct = Math.round(w.probability * 100)
        const title = `${w.word.trim()} (${pct}%)`
        return (
          <span key={i} className={cls || undefined} title={title}>
            {w.word}
          </span>
        )
      })}
    </span>
  )
}

export default ConfidenceText
