import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@renderer/test/utils'
import userEvent from '@testing-library/user-event'
import ModelSelector from '../ModelSelector'
import * as downloadStore from '../../store/download-store'

// Mock the store
vi.mock('../../store/download-store', () => ({
  default: vi.fn()
}))

describe('ModelSelector', () => {
  const mockAvailableModels = {
    'faster-whisper': {
      description: 'Faster Whisper',
      languages: ['en', 'fr', 'de'],
      models: {
        'tiny': { speed: 'fast', accuracy: 'low', vram_gb: 1 },
        'base': { speed: 'medium', accuracy: 'medium', vram_gb: 2 }
      }
    },
    'other-model': {
      description: 'Other Model',
      languages: ['en'],
      models: {
        'default': { speed: 'slow', accuracy: 'high', vram_gb: 4 }
      }
    }
  }

  const defaultProps = {
    availableModels: mockAvailableModels,
    selectedType: 'faster-whisper',
    selectedName: 'tiny',
    onTypeChange: vi.fn(),
    onNameChange: vi.fn(),
  }

  beforeEach(() => {
    // Setup default store mock - no fetchCachedModels since ModelSelector no longer auto-fetches
    (downloadStore.default as any).mockReturnValue({
      cachedModels: [],
      isDownloading: false
    })
  })

  it('renders model dropdown correctly', () => {
    render(<ModelSelector {...defaultProps} />)
    
    expect(screen.getByText('Model Type')).toBeInTheDocument()
    expect(screen.getByText('Model Variant')).toBeInTheDocument()
    
    const typeSelect = screen.getByRole('combobox', { name: /model type/i })
    expect(typeSelect).toHaveValue('faster-whisper')
    
    const variantSelect = screen.getByRole('combobox', { name: /model variant/i })
    expect(variantSelect).toHaveValue('tiny')
  })

  it('displays available model variants', () => {
    render(<ModelSelector {...defaultProps} />)
    
    const variantSelect = screen.getByRole('combobox', { name: /model variant/i })
    const options = Array.from(variantSelect.children)
    
    expect(options).toHaveLength(2)
    expect(options[0]).toHaveTextContent('tiny')
    expect(options[1]).toHaveTextContent('base')
  })

  it('handles model selection', async () => {
    const user = userEvent.setup()
    const onNameChange = vi.fn()
    render(<ModelSelector {...defaultProps} onNameChange={onNameChange} />)
    
    const variantSelect = screen.getByRole('combobox', { name: /model variant/i })
    await user.selectOptions(variantSelect, 'base')
    
    expect(onNameChange).toHaveBeenCalledWith('base')
  })

  it('handles model type selection', async () => {
    const user = userEvent.setup()
    const onTypeChange = vi.fn()
    const onNameChange = vi.fn()
    render(<ModelSelector {...defaultProps} onTypeChange={onTypeChange} onNameChange={onNameChange} />)
    
    const typeSelect = screen.getByRole('combobox', { name: /model type/i })
    await user.selectOptions(typeSelect, 'other-model')
    
    expect(onTypeChange).toHaveBeenCalledWith('other-model')
    // It should also trigger name change to the first model of the new type
    expect(onNameChange).toHaveBeenCalledWith('default')
  })

  it('shows loading state when model is loading', () => {
    render(<ModelSelector {...defaultProps} isLoadingModel={true} />)
    
    expect(screen.getByText('Loading model...')).toBeInTheDocument()
  })

  it('shows global loading overlay when loading models list', () => {
    render(<ModelSelector {...defaultProps} isLoadingModels={true} />)
    
    expect(screen.getByText('Loading models...')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /model type/i })).toBeDisabled()
  })

  it('disables when disabled prop is true', () => {
    render(<ModelSelector {...defaultProps} disabled={true} />)
    
    expect(screen.getByRole('combobox', { name: /model type/i })).toBeDisabled()
    expect(screen.getByRole('combobox', { name: /model variant/i })).toBeDisabled()
  })

  it('shows downloaded status correctly', () => {
    (downloadStore.default as any).mockReturnValue({
      cachedModels: [{ model_name: 'tiny', size_human: '75MB' }],
      isDownloading: false
    })

    render(<ModelSelector {...defaultProps} />)
    
    // Check for the checkmark in the option
    const variantSelect = screen.getByRole('combobox', { name: /model variant/i })
    expect(variantSelect.children[0]).toHaveTextContent('✓ tiny')
    
    // Check for the badge
    expect(screen.getByText(/Downloaded/)).toBeInTheDocument()
    expect(screen.getByText(/\(75MB\)/)).toBeInTheDocument()
  })
})
