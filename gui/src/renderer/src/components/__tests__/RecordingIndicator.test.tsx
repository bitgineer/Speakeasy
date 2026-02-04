import { render, screen, fireEvent, act } from '../../test/utils'
import RecordingIndicator from '../RecordingIndicator'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// Mock settings store
vi.mock('../store', () => ({
  useSettingsStore: vi.fn(() => ({
    settings: { 
      show_recording_indicator: true, 
      always_show_indicator: true 
    },
    fetchSettings: vi.fn()
  }))
}))

describe('RecordingIndicator', () => {
  const mockApi = {
    onRecordingStart: vi.fn(),
    onRecordingComplete: vi.fn(),
    onRecordingError: vi.fn(),
    onRecordingLocked: vi.fn(),
    cancelRecording: vi.fn(),
    getRecordingStatus: vi.fn().mockResolvedValue(false)
  }

  beforeEach(() => {
    // Mock window.api
    window.api = mockApi as any
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders Ready state when idle', () => {
    const { container } = render(<RecordingIndicator />)
    expect(screen.getByText('Ready')).toBeInTheDocument()
  })

  it('shows recording state when recording starts', async () => {
    let startCallback: () => void = () => {}
    mockApi.onRecordingStart.mockImplementation((cb) => {
      startCallback = cb
      return () => {}
    })

    render(<RecordingIndicator />)
    
    // Trigger start
    act(() => {
      startCallback()
    })
    
    // Should show timer
    expect(await screen.findByText('00:00')).toBeInTheDocument()
    // Should have cancel button
    expect(screen.getByTitle('Cancel Recording')).toBeInTheDocument()
  })

  it('calls cancelRecording when cancel button clicked', async () => {
    let startCallback: () => void = () => {}
    mockApi.onRecordingStart.mockImplementation((cb) => {
      startCallback = cb
      return () => {}
    })

    render(<RecordingIndicator />)
    
    act(() => {
      startCallback()
    })
    
    // Click cancel button (found by title)
    const cancelButton = await screen.findByTitle('Cancel Recording')
    fireEvent.click(cancelButton)
    
    expect(mockApi.cancelRecording).toHaveBeenCalled()
  })

  it('shows locked state when recording is locked', async () => {
    let startCallback: () => void = () => {}
    let lockCallback: () => void = () => {}
    
    mockApi.onRecordingStart.mockImplementation((cb) => {
      startCallback = cb
      return () => {}
    })
    
    mockApi.onRecordingLocked.mockImplementation((cb) => {
      lockCallback = cb
      return () => {}
    })

    const { container } = render(<RecordingIndicator />)
    
    act(() => {
      startCallback()
    })
    
    // Trigger lock
    act(() => {
      lockCallback()
    })
    
    // Should show locked UI elements
    expect(screen.getByText('LOCKED')).toBeInTheDocument()
    expect(screen.getByText(/Press hotkey to stop/i)).toBeInTheDocument()
    
    // Should show yellow border (checking class presence)
    // Note: checking for specific tailwind classes can be brittle, but effective for now
    const pill = container.querySelector('.border-yellow-500\\/50')
    expect(pill).toBeInTheDocument()
  })
})

