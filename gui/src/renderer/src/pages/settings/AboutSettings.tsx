/**
 * About Settings Page
 * 
 * Application information and version.
 */

import { useEffect, useState } from 'react'

export default function AboutSettings(): JSX.Element {
  const [version, setVersion] = useState<string>('...')

  useEffect(() => {
    window.api?.getVersion().then(v => setVersion(v)).catch(() => setVersion('Unknown'))
  }, [])

  return (
    <div className="p-6 max-w-2xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">About</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">Application information</p>
      </div>

      <div className="space-y-6">
        {/* App Info */}
        <section className="card p-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-2xl bg-[var(--color-accent)] flex items-center justify-center">
              <svg className="w-10 h-10 text-[var(--color-text-on-accent)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">SpeakEasy</h2>
              <p className="text-sm text-[var(--color-text-muted)]">Open-source voice transcription</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-[var(--color-text-muted)]">Version</span>
              <p className="text-[var(--color-text-primary)] font-medium">{version}</p>
            </div>
            <div>
              <span className="text-[var(--color-text-muted)]">License</span>
              <p className="text-[var(--color-text-primary)] font-medium">MIT</p>
            </div>
          </div>
        </section>

        {/* Tech Stack */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Technology</h2>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between py-2 border-b border-[var(--color-border)]">
              <span className="text-[var(--color-text-secondary)]">Desktop Framework</span>
              <span className="text-[var(--color-text-primary)]">Electron</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-[var(--color-border)]">
              <span className="text-[var(--color-text-secondary)]">Frontend</span>
              <span className="text-[var(--color-text-primary)]">React + TypeScript</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-[var(--color-border)]">
              <span className="text-[var(--color-text-secondary)]">Backend</span>
              <span className="text-[var(--color-text-primary)]">FastAPI (Python)</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-[var(--color-text-secondary)]">ASR Engine</span>
              <span className="text-[var(--color-text-primary)]">Whisper / faster-whisper</span>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Key Features</h2>
          <ul className="space-y-2 text-sm text-[var(--color-text-secondary)]">
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>100% local processing - your data never leaves your device</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Global hotkey support for quick voice-to-text</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Multiple Whisper model sizes for accuracy vs speed tradeoffs</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>GPU acceleration (CUDA) for faster transcription</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Batch transcription for audio files</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Customizable themes and appearance</span>
            </li>
          </ul>
        </section>
      </div>
    </div>
  )
}
