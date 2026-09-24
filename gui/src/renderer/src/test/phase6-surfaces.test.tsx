import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import ExportDialog from '../components/ExportDialog'
import ModelDownloadDialog from '../components/ModelDownloadDialog'
import Toast from '../components/Toast'
import RecordingIndicator from '../components/RecordingIndicator'
import useDownloadStore from '../store/download-store'
import { apiClient } from '../api/client'

vi.mock('../api/client', () => ({
  apiClient: {
    exportHistory: vi.fn(),
    exportHistoryFiltered: vi.fn(),
    cancelDownload: vi.fn(),
    getSettings: vi.fn(() => new Promise(() => {})),
  },
}))

const exportHistory = vi.mocked(apiClient.exportHistory)
const cancelDownloadRequest = vi.mocked(apiClient.cancelDownload)
let anchorClick: { mockRestore: () => void } | null = null

beforeEach(() => {
  exportHistory.mockReset()
  cancelDownloadRequest.mockReset()
  URL.createObjectURL = vi.fn(() => 'blob:mock')
  URL.revokeObjectURL = vi.fn()
  useDownloadStore.getState().reset()
})

afterEach(() => {
  anchorClick?.mockRestore()
  anchorClick = null
  vi.useRealTimers()
  delete (window as unknown as { api?: unknown }).api
})

describe('export dialog flows', () => {
  it('calls onClose from Cancel without exporting', () => {
    const onClose = vi.fn()
    render(<ExportDialog isOpen onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onClose).toHaveBeenCalledTimes(1)
    expect(exportHistory).not.toHaveBeenCalled()
  })

  it('exports the history and closes on confirm', async () => {
    const onClose = vi.fn()
    exportHistory.mockResolvedValue(new Blob(['[]'], { type: 'application/json' }))
    anchorClick = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    render(<ExportDialog isOpen onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: 'Export' }))
    await waitFor(() => expect(exportHistory).toHaveBeenCalledWith('json', true))
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1))
    expect(anchorClick).toHaveBeenCalled()
  })

  it('drops the date range for a single-record export', () => {
    render(<ExportDialog isOpen onClose={() => {}} singleRecordId="abc" />)
    expect(screen.getByText('Export Transcription')).toBeTruthy()
    expect(screen.queryByText('Date Range (optional)')).toBeNull()
  })
})

describe('download dialog flows', () => {
  it('shows the failure and retries', () => {
    useDownloadStore.setState({ status: 'error', errorMessage: 'disk full' })
    const onRetry = vi.fn()
    render(<ModelDownloadDialog isOpen onClose={() => {}} onRetry={onRetry} />)
    expect(screen.getByText('Download Failed')).toBeTruthy()
    expect(screen.getByText('disk full')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('cancels an active download', async () => {
    useDownloadStore.setState({
      isDownloading: true,
      status: 'downloading',
      downloadProgress: 42,
      modelName: 'whisper-base',
    })
    cancelDownloadRequest.mockResolvedValue({ status: 'cancelled' })
    render(<ModelDownloadDialog isOpen onClose={() => {}} />)
    expect(screen.getByText('Model: whisper-base')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel Download' }))
    await waitFor(() => expect(cancelDownloadRequest).toHaveBeenCalledTimes(1))
  })
})

describe('recording indicator states', () => {
  it('wires stop and cancel from the recording pill', () => {
    const startHandlers: Array<() => void> = []
    const stopRecording = vi.fn()
    const cancelRecording = vi.fn()
    ;(window as unknown as { api: Record<string, unknown> }).api = {
      getRecordingStatus: vi.fn(() => Promise.resolve(false)),
      onRecordingStart: vi.fn((callback: () => void) => {
        startHandlers.push(callback)
        return () => {}
      }),
      onRecordingLocked: vi.fn(() => () => {}),
      onRecordingProcessing: vi.fn(() => () => {}),
      onRecordingComplete: vi.fn(() => () => {}),
      onRecordingError: vi.fn(() => () => {}),
      onLiveTranscript: vi.fn(() => () => {}),
      resizeIndicator: vi.fn(),
      showIndicator: vi.fn(),
      hideIndicator: vi.fn(),
      checkHealth: vi.fn(() => Promise.resolve({ state: 'ready' })),
      stopRecording,
      cancelRecording,
    }

    render(<RecordingIndicator />)
    act(() => startHandlers.forEach((callback) => callback()))

    fireEvent.click(screen.getByTitle('Stop and transcribe'))
    expect(stopRecording).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByTitle('Cancel recording'))
    expect(cancelRecording).toHaveBeenCalledTimes(1)
  })
})

describe('toast lifecycle', () => {
  it.each(['success', 'error', 'warning'] as const)('tags the %s tone', (type) => {
    render(<Toast id="t" type={type} message="notice" onClose={() => {}} />)
    expect(screen.getByRole('alert').getAttribute('data-tone')).toBe(type)
  })

  it('removes itself after the exit delay when closed', () => {
    vi.useFakeTimers()
    const onClose = vi.fn()
    render(<Toast id="t1" type="warning" message="Careful" onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    act(() => {
      vi.advanceTimersByTime(299)
    })
    expect(onClose).not.toHaveBeenCalled()
    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(onClose).toHaveBeenCalledWith('t1')
  })
})
