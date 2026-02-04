/**
 * ModelSelector Component
 * 
 * Dropdown for selecting ASR model type and variant.
 */

import { useMemo, memo } from 'react'
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

  return (
    <div className="space-y-4 relative">
      {isLoadingModels && (
        <div className="absolute inset-0 z-10 bg-gray-900/50 backdrop-blur-[1px] flex items-center justify-center rounded-lg">
          <div className="flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-medium text-white">Loading models...</span>
          </div>
        </div>
      )}

      {/* Model Type */}
      <div className={isLoadingModels ? 'opacity-50 pointer-events-none' : ''}>
        <label htmlFor="model-type-select" className="label">Model Type</label>
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
          className={`select ${isComponentDisabled ? 'cursor-not-allowed opacity-70' : ''}`}
        >
          {Object.entries(availableModels).map(([type, info]) => (
            <option key={type} value={type}>
              {type} - {info.description}
            </option>
          ))}
        </select>
        {currentModelInfo && (
          <p className="mt-1 text-xs text-gray-500">
            Languages: {currentModelInfo.languages.slice(0, 5).join(', ')}
            {currentModelInfo.languages.length > 5 && ` +${currentModelInfo.languages.length - 5} more`}
          </p>
        )}
      </div>
      
      {/* Model Variant */}
      <div className={isLoadingModels ? 'opacity-50 pointer-events-none' : ''}>
        <label htmlFor="model-variant-select" className="label">Model Variant</label>
        <select
          id="model-variant-select"
          value={selectedName}
          onChange={(e) => onNameChange(e.target.value)}
          disabled={isComponentDisabled || modelVariants.length === 0}
          className={`select ${isComponentDisabled ? 'cursor-not-allowed opacity-70' : ''}`}
        >
          {modelVariants.map((name) => {
            const modelDetails = currentModelInfo?.models[name]
            const isDownloaded = isModelDownloaded(name)
            return (
              <option key={name} value={name}>
                {isDownloaded ? '✓ ' : '⬇ '}
                {name}
                {modelDetails && ` (${modelDetails.speed}, ${modelDetails.vram_gb}GB VRAM)`}
              </option>
            )
          })}
        </select>
        
        {isLoadingModel && (
          <div className="mt-2 flex items-center gap-2 text-blue-400 animate-pulse">
            <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            <span className="text-xs font-medium">Loading model...</span>
          </div>
        )}

        {!isLoadingModel && currentModelInfo && selectedName && currentModelInfo.models[selectedName] && (
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            {isModelDownloaded(selectedName) ? (
              <span className="badge-green flex items-center gap-1">
                ✓ Downloaded
                {getModelSize(selectedName) && ` (${getModelSize(selectedName)})`}
              </span>
            ) : (
              <span className="badge-gray flex items-center gap-1">
                ⬇ Not downloaded - click to download
              </span>
            )}
            <span className="badge-blue">
              Speed: {currentModelInfo.models[selectedName].speed}
            </span>
            <span className="badge-green">
              Accuracy: {currentModelInfo.models[selectedName].accuracy}
            </span>
            <span className="badge-yellow">
              VRAM: {currentModelInfo.models[selectedName].vram_gb}GB
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(ModelSelector)
