import { beforeEach, describe, expect, it } from 'vitest'
import { recordFromTranscriptionEvent, useHistoryStore } from '../store/history-store'
import type { TranscriptionRecord } from '../api/types'

function record(overrides: Partial<TranscriptionRecord> = {}): TranscriptionRecord {
  return {
    id: 'r-1',
    text: 'hello',
    duration_ms: 1000,
    model_used: null,
    language: null,
    created_at: '2026-09-23T00:00:00.000Z',
    original_text: null,
    is_ai_enhanced: false,
    ...overrides
  }
}

describe('history store record path', () => {
  beforeEach(() => {
    useHistoryStore.setState({ items: [], total: 0 })
  })

  it('prepends a record that is not in the list', () => {
    useHistoryStore.getState().upsertItem(record({ id: 'first' }))
    useHistoryStore.getState().upsertItem(record({ id: 'second' }))

    expect(useHistoryStore.getState().items.map(item => item.id)).toEqual(['second', 'first'])
    expect(useHistoryStore.getState().total).toBe(2)
  })

  it('replaces an existing record with the same id in place and keeps the total', () => {
    useHistoryStore.setState({ items: [record({ id: 'a' }), record({ id: 'b' })], total: 2 })

    useHistoryStore.getState().upsertItem(
      record({
        id: 'a',
        text: 'processed text',
        original_text: 'raw text',
        is_ai_enhanced: true
      })
    )

    const { items, total } = useHistoryStore.getState()
    expect(items.map(item => item.id)).toEqual(['a', 'b'])
    expect(items[0].text).toBe('processed text')
    expect(items[0].original_text).toBe('raw text')
    expect(items[0].is_ai_enhanced).toBe(true)
    expect(total).toBe(2)
  })

  it('maps a processed event to a record with the original text and the processed flag', () => {
    const built = recordFromTranscriptionEvent({
      type: 'transcription',
      id: 'r-9',
      text: 'Rewritten words.',
      duration_ms: 1500,
      original_text: 'raw words',
      processing_error: null
    })

    expect(built.text).toBe('Rewritten words.')
    expect(built.original_text).toBe('raw words')
    expect(built.is_ai_enhanced).toBe(true)
    expect('processing_error' in built).toBe(false)
  })

  it('maps a degraded event to an unprocessed record', () => {
    const built = recordFromTranscriptionEvent({
      type: 'transcription',
      id: 'r-10',
      text: 'raw words',
      duration_ms: 1500,
      original_text: null,
      processing_error: 'provider timed out after 20s'
    })

    expect(built.original_text).toBeNull()
    expect(built.is_ai_enhanced).toBe(false)
  })
})
