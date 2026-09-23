/**
 * ModelSelector Component
 * 
 * Dropdown for selecting ASR model type and variant.
 */

import { useMemo, memo } from 'react'
import { Check, Download, Loader2 } from 'lucide-react'
import type { ModelInfo } from '../api/types'
import useDownloadStore from '../store/download-store'

interface ModelSelectorProps {
  availableModels: Record<string, ModelInfo>
  selectedType: string
  selectedName: string
  onTypeChange: (type: string) => void
  onNameChange: (name: string) => void
  disabled?: boolean
  isLoadingModels?: boolean
  isLoadingModel?: boolean
}

function ModelSelector({
  availableModels,
  selectedType,
  selectedName,
  onTypeChange,
  onNameChange,
  disabled = false,
  isLoadingModels = false,
  isLoadingModel = false
}: ModelSelectorProps): JSX.Element {
  // Use cached models from store - data is populated by "Sync Models" button in ModelSettings
  const { cachedModels, isDownloading } = useDownloadStore()

  const isModelDownloaded = (name: string) => {
    return cachedModels.some((m) => m.model_name === name)
  }

  const getModelSize = (name: string) => {
    return cachedModels.find((m) => m.model_name === name)?.size_human
  }

  // Get models for selected type
  const currentModelInfo = useMemo(() => {
    return availableModels[selectedType] || null
  }, [availableModels, selectedType])
  
  // Get model variants for selected type
  const modelVariants = useMemo(() => {
    if (!currentModelInfo) return []
    return Object.keys(currentModelInfo.models)
  }, [currentModelInfo])
  
  const isComponentDisabled = disabled || isLoadingModels || isLoadingModel || isDownloading
  const modelDetails = currentModelInfo?.models[selectedName]

  return (
    <div className="model-selector">
      {isLoadingModels && (
        <div className="model-overlay">
          <div className="model-overlay-body">
            <span className="spinner animate-spin" role="status" aria-label="Loading models" />
            <span className="muted text-small">Loading models...</span>
          </div>
        </div>
      )}

      {/* Model Type */}
      <div className="field">
        <label htmlFor="model-type-select" className="label">
          Model Type
        </label>
        <select
          id="model-type-select"
          value={selectedType}
          onChange={(e) => {
            onTypeChange(e.target.value)
            // Reset model name when type changes
            const newModelInfo = availableModels[e.target.value]
            if (newModelInfo) {
              const firstModel = Object.keys(newModelInfo.models)[0]
              if (firstModel) {
                onNameChange(firstModel)
              }
            }
          }}
          disabled={isComponentDisabled}
          className="select"
        >
          {Object.entries(availableModels).map(([type, info]) => (
            <option key={type} value={type}>
              {type} - {info.description}
            </option>
          ))}
        </select>
        {currentModelInfo && (
          <p className="field-hint">
            Languages: {currentModelInfo.languages.slice(0, 5).join(', ')}
            {currentModelInfo.languages.length > 5 && ` +${currentModelInfo.languages.length - 5} more`}
          </p>
        )}
      </div>
      
      {/* Model Variant */}
      <div className="field">
        <label htmlFor="model-variant-select" className="label">
          Model Variant
        </label>
        <select
          id="model-variant-select"
          value={selectedName}
          onChange={(e) => onNameChange(e.target.value)}
          disabled={isComponentDisabled || modelVariants.length === 0}
          className="select"
        >
          {modelVariants.map((name) => {
            const details = currentModelInfo?.models[name]
            const isDownloaded = isModelDownloaded(name)
            return (
              <option key={name} value={name}>
                {isDownloaded ? '✓ ' : '⬇ '}
                {name}
                {details && ` (${details.speed}, ${details.vram_gb}GB VRAM)`}
              </option>
            )
          })}
        </select>
        
        {isLoadingModel && (
          <p className="field-status">
            <Loader2 className="animate-spin" size={12} aria-hidden="true" />
            Loading model...
          </p>
        )}

        {!isLoadingModel && modelDetails && (
          <div className="model-pills">
            {isModelDownloaded(selectedName) ? (
              <span className="pill" data-tone="success">
                <Check size={12} aria-hidden="true" />
                Downloaded
                {getModelSize(selectedName) && ` (${getModelSize(selectedName)})`}
              </span>
            ) : (
              <span className="pill">
                <Download size={12} aria-hidden="true" />
                Not downloaded - click to download
              </span>
            )}
            <span className="pill">Speed: {modelDetails.speed}</span>
            <span className="pill">Accuracy: {modelDetails.accuracy}</span>
            <span className="pill" data-tone="warning">
              VRAM: {modelDetails.vram_gb}GB
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(ModelSelector)
