import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@renderer/test/utils'
import userEvent from '@testing-library/user-event'
import Settings from '../Settings'
import * as storeExports from '../../store'
import * as downloadStore from '../../store/download-store'

// Mock the stores
vi.mock('../../store', () => ({
  useSettingsStore: vi.fn(),
  useAppStore: vi.fn()
}))

vi.mock('../../store/download-store', () => ({
  default: vi.fn()
}))

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

describe('Settings Page', () => {
  const mockSettings = {
    model_type: 'faster-whisper',
    model_name: 'tiny',
    device: 'cpu',
    compute_type: 'int8',
    language: 'en',
    hotkey: 'ctrl+shift+space',
    hotkey_mode: 'toggle',
    auto_paste: false,
    show_recording_indicator: true
  }

  const mockActions = {
    fetchSettings: vi.fn(),
    fetchModels: vi.fn(),
    fetchDevices: vi.fn(),
    updateSettings: vi.fn().mockResolvedValue(true),
    loadModel: vi.fn(),
    setDevice: vi.fn(),
    clearError: vi.fn(),
    fetchCacheInfo: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup default store mocks
    (storeExports.useSettingsStore as any).mockReturnValue({
      settings: mockSettings,
      isLoading: false,
      isSaving: false,
      error: null,
      availableModels: {
        'faster-whisper': {
          description: 'Faster Whisper',
          languages: ['en'],
          models: { 'tiny': { speed: 'fast', accuracy: 'low', vram_gb: 1 } }
        }
      },
      availableDevices: [
        { id: 'default', name: 'Default Mic', is_default: true }
      ],
      needsModelReload: false,
      ...mockActions
    })

    (storeExports.useAppStore as any).mockReturnValue({
      gpuAvailable: false,
      gpuName: null,
      gpuVramGb: null
    })

    (downloadStore.default as any).mockReturnValue({
      isDownloading: false,
      cachedModels: [],
      cacheDir: '/tmp/cache',
      totalCacheSizeHuman: '0 B',
      fetchCacheInfo: vi.fn(),
      clearCache: vi.fn(),
      isClearingCache: false
    })
  })

  it('renders settings page with all sections', () => {
    render(<Settings />)
    
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Model Settings')).toBeInTheDocument()
    expect(screen.getByText('Audio Settings')).toBeInTheDocument()
    expect(screen.getByText('Hotkey Settings')).toBeInTheDocument()
    expect(screen.getByText('Behavior')).toBeInTheDocument()
  })

  it('Model section shows ModelSelector', () => {
    render(<Settings />)
    expect(screen.getByText('Model Type')).toBeInTheDocument()
    expect(screen.getByText('Model Variant')).toBeInTheDocument()
  })

  it('Device section shows DeviceSelector', () => {
    render(<Settings />)
    expect(screen.getByText('Audio Input Device')).toBeInTheDocument()
  })

  it('Hotkey section shows HotkeyInput', () => {
    render(<Settings />)
    expect(screen.getByText('Recording Hotkey')).toBeInTheDocument()
  })

  it('Save button triggers settings update', async () => {
    const user = userEvent.setup()
    render(<Settings />)
    
    const saveButton = screen.getByText('Save Changes')
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(mockActions.updateSettings).toHaveBeenCalledWith(expect.objectContaining({
        model_type: 'faster-whisper',
        model_name: 'tiny'
      }))
    })
  })

  it('shows loading state', () => {
    (storeExports.useSettingsStore as any).mockReturnValue({
      isLoading: true,
      fetchSettings: vi.fn(),
      fetchModels: vi.fn(),
      fetchDevices: vi.fn(),
      fetchCacheInfo: vi.fn()
    })
    
    render(<Settings />)
    expect(screen.queryByText('Model Settings')).not.toBeInTheDocument()
  })

  it('shows error message', () => {
    (storeExports.useSettingsStore as any).mockReturnValue({
      ...mockActions,
      settings: mockSettings,
      error: 'Failed to save settings',
      availableModels: {},
      availableDevices: []
    })
    
    render(<Settings />)
    expect(screen.getByText('Failed to save settings')).toBeInTheDocument()
  })

  it('handles navigation back', async () => {
    const user = userEvent.setup()
    render(<Settings />)
    
    // The back button has no text, just an SVG
    const buttons = screen.getAllByRole('button')
    await user.click(buttons[0])
    
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })
})
