/**
 * About Settings Page
 * 
 * Application information and version.
 */

import { useEffect, useState } from 'react'
import { Check, Mic } from 'lucide-react'

const TECH_STACK: Array<{ label: string; value: string }> = [
  { label: 'Desktop framework', value: 'Electron' },
  { label: 'Frontend', value: 'React + TypeScript' },
  { label: 'Backend', value: 'FastAPI (Python)' },
  { label: 'ASR engine', value: 'Whisper / faster-whisper' }
]

const FEATURES = [
  '100% local processing - your data never leaves your device',
  'Global hotkey support for quick voice-to-text',
  'Multiple Whisper model sizes for accuracy vs speed tradeoffs',
  'GPU acceleration (CUDA) for faster transcription',
  'Batch transcription for audio files',
  'Customizable themes and appearance'
]

export default function AboutSettings(): JSX.Element {
  const [version, setVersion] = useState<string>('...')

  useEffect(() => {
    window.api?.getVersion().then(v => setVersion(v)).catch(() => setVersion('Unknown'))
  }, [])

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Settings / about</p>
          <h1>About</h1>
          <p className="page-subtitle">Application information and license.</p>
        </div>
      </header>

      <div className="settings-stack">
        {/* App Info */}
        <section className="card settings-panel">
          <div className="app-intro">
            <span className="app-mark">
              <Mic size={22} strokeWidth={2} aria-hidden="true" />
            </span>
            <div>
              <h2 className="app-name">SpeakEasy</h2>
              <p className="panel-subtitle">Open-source voice transcription</p>
            </div>
          </div>
          
          <div className="about-facts">
            <div>
              <span className="field-hint">Version</span>
              <p className="about-value">{version}</p>
            </div>
            <div>
              <span className="field-hint">License</span>
              <p className="about-value">MIT</p>
            </div>
          </div>
        </section>

        {/* Tech Stack */}
        <section className="card settings-panel" aria-labelledby="technology-title">
          <div className="settings-head">
            <h2 id="technology-title">Technology</h2>
          </div>
          <div className="settings-table">
            {TECH_STACK.map((row) => (
              <div className="table-row" key={row.label}>
                <span className="table-key">{row.label}</span>
                <span className="table-value">{row.value}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section className="card settings-panel" aria-labelledby="features-title">
          <div className="settings-head">
            <h2 id="features-title">Key features</h2>
          </div>
          <ul className="check-list">
            {FEATURES.map((feature) => (
              <li key={feature}>
                <Check size={15} strokeWidth={2.25} aria-hidden="true" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
