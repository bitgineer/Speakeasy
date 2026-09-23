/**
 * Processing Settings Page
 *
 * LLM providers and API keys, write-mode tone profiles, the default tone,
 * and the command-mode prompt.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { Trash2, X } from 'lucide-react'
import { useSettingsStore } from '../../store'
import { apiClient } from '../../api/client'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { Button } from '../../components/ui/button'
import type {
  AppMatch,
  FocusedAppResponse,
  LlmProvider,
  ProviderKind,
  ProviderModel,
  Settings,
  ToneProfile
} from '../../api/types'

type ToneDraft = Omit<ToneProfile, 'matches'> & { matches: AppMatch[] }

interface ProcessingDraft {
  providers: LlmProvider[]
  active_provider_id: string
  default_tone: ToneDraft
  tone_profiles: ToneDraft[]
  command_prompt: string
}

const PRESETS: Record<ProviderKind, { label: string; base_url: string; model: string }> = {
  local: {
    label: 'Local',
    base_url: 'http://127.0.0.1:11434/v1',
    model: 'llama3.1:8b'
  },
  openai: {
    label: 'OpenAI',
    base_url: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini'
  },
  groq: {
    label: 'Groq',
    base_url: 'https://api.groq.com/openai/v1',
    model: 'llama-3.3-70b-versatile'
  },
  custom: {
    label: 'Custom',
    base_url: '',
    model: ''
  }
}

const PRESET_KINDS: ProviderKind[] = ['local', 'openai', 'groq', 'custom']

function toToneDraft(tone: ToneProfile): ToneDraft {
  return { ...tone, matches: tone.matches ?? [] }
}

function toDraft(settings: Settings): ProcessingDraft {
  return structuredClone({
    providers: settings.providers ?? [],
    active_provider_id: settings.active_provider_id ?? '',
    default_tone: toToneDraft(settings.default_tone ?? { name: 'Default', prompt: '', matches: [] }),
    tone_profiles: (settings.tone_profiles ?? []).map(toToneDraft),
    command_prompt: settings.command_prompt ?? ''
  })
}

function uniqueProviderId(base: string, providers: LlmProvider[]): string {
  const slug = base.toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '') || 'provider'
  const taken = new Set(providers.map((provider) => provider.id))
  let candidate = slug
  let suffix = 2
  while (taken.has(candidate)) {
    candidate = `${slug}-${suffix}`
    suffix += 1
  }
  return candidate
}

export default function ProcessingSettings(): JSX.Element {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    fetchSettings,
    updateSettings,
    setError,
    clearError
  } = useSettingsStore()

  const [draft, setDraft] = useState<ProcessingDraft | null>(null)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'unsaved' | 'saving' | 'saved'>('idle')
  const originalSettings = useRef<ProcessingDraft | null>(null)
  const [hasKeys, setHasKeys] = useState<Record<string, boolean>>({})
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({})
  const [savingKeyId, setSavingKeyId] = useState<string | null>(null)
  const [providerModels, setProviderModels] = useState<Record<string, ProviderModel[]>>({})
  const [loadingModelsId, setLoadingModelsId] = useState<string | null>(null)
  const [modelErrors, setModelErrors] = useState<Record<string, string>>({})
  const [focusedApp, setFocusedApp] = useState<FocusedAppResponse | null>(null)
  const [focusedAppLoaded, setFocusedAppLoaded] = useState(false)

  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === 'unsaved'
  })

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  useEffect(() => {
    if (!settings) return
    const next = toDraft(settings)
    setDraft(next)
    originalSettings.current = next
  }, [settings])

  useEffect(() => {
    apiClient
      .getProviderKeys()
      .then(setHasKeys)
      .catch(() => setHasKeys({}))
  }, [settings?.providers])

  const refreshFocusedApp = useCallback((): void => {
    apiClient
      .getFocusedApp()
      .then(setFocusedApp)
      .catch(() => setFocusedApp(null))
      .finally(() => setFocusedAppLoaded(true))
  }, [])

  useEffect(() => {
    refreshFocusedApp()
  }, [refreshFocusedApp])

  useEffect(() => {
    if (!draft || !originalSettings.current) return
    const isDirty = JSON.stringify(draft) !== JSON.stringify(originalSettings.current)
    if (isDirty && saveStatus !== 'saving') {
      setSaveStatus('unsaved')
    } else if (!isDirty && saveStatus === 'unsaved') {
      setSaveStatus('idle')
    }
  }, [draft, saveStatus])

  const updateDraft = (updater: (current: ProcessingDraft) => ProcessingDraft): void => {
    setDraft((current) => (current ? updater(current) : current))
  }

  const addProvider = (kind: ProviderKind): void => {
    const preset = PRESETS[kind]
    updateDraft((current) => ({
      ...current,
      providers: [
        ...current.providers,
        {
          id: uniqueProviderId(preset.label, current.providers),
          label: preset.label,
          kind,
          base_url: preset.base_url,
          model: preset.model,
          timeout_seconds: 20
        }
      ]
    }))
  }

  const updateProvider = (id: string, patch: Partial<LlmProvider>): void => {
    updateDraft((current) => ({
      ...current,
      providers: current.providers.map((provider) =>
        provider.id === id ? { ...provider, ...patch } : provider
      )
    }))
  }

  const removeProvider = (id: string): void => {
    updateDraft((current) => ({
      ...current,
      providers: current.providers.filter((provider) => provider.id !== id),
      active_provider_id: current.active_provider_id === id ? '' : current.active_provider_id
    }))
  }

  const updateTone = (index: number, patch: Partial<ToneProfile>): void => {
    updateDraft((current) => ({
      ...current,
      tone_profiles: current.tone_profiles.map((profile, i) =>
        i === index ? { ...profile, ...patch } : profile
      )
    }))
  }

  const loadModels = async (provider: LlmProvider): Promise<void> => {
    setLoadingModelsId(provider.id)
    setModelErrors((current) => ({ ...current, [provider.id]: '' }))
    try {
      const response = await apiClient.getProviderModels(provider.id)
      setProviderModels((current) => ({ ...current, [provider.id]: response.models }))
    } catch (modelError) {
      setModelErrors((current) => ({
        ...current,
        [provider.id]: modelError instanceof Error ? modelError.message : 'Failed to load models'
      }))
    } finally {
      setLoadingModelsId(null)
    }
  }

  const handleSaveKey = async (providerId: string, key: string): Promise<void> => {
    setSavingKeyId(providerId)
    try {
      const response = await apiClient.setProviderKey(providerId, key)
      setHasKeys((prev) => ({ ...prev, [response.provider_id]: response.has_key }))
      setKeyDrafts((prev) => ({ ...prev, [providerId]: '' }))
    } catch (keyError) {
      setError(keyError instanceof Error ? keyError.message : 'Failed to store the API key')
    } finally {
      setSavingKeyId(null)
    }
  }

  const invalidToneName =
    draft !== null &&
    (draft.default_tone.name.trim() === '' ||
      draft.tone_profiles.some((profile) => profile.name.trim() === ''))

  const handleSave = async (): Promise<void> => {
    if (!draft || invalidToneName) return
    setSaveStatus('saving')
    const success = await updateSettings({
      providers: draft.providers,
      active_provider_id: draft.active_provider_id,
      default_tone: draft.default_tone,
      tone_profiles: draft.tone_profiles,
      command_prompt: draft.command_prompt
    })

    if (success) {
      setSaveStatus('saved')
      originalSettings.current = draft
    } else {
      setSaveStatus('unsaved')
    }
  }

  if (isLoading || !draft) {
    return (
      <div className="workspace settings-loading">
        <span className="spinner animate-spin" role="status" aria-label="Loading processing settings" />
      </div>
    )
  }

  const persistedIds = new Set((settings?.providers ?? []).map((provider) => provider.id))

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Settings / processing</p>
          <h1>Processing</h1>
          <p className="page-subtitle">
            Providers, API keys, and the prompts behind Write and Command modes.
          </p>
        </div>
        <div className="page-actions">
          <SaveStatusIndicator status={saveStatus} />
          <Button
            onClick={handleSave}
            disabled={isSaving || invalidToneName || saveStatus === 'idle' || saveStatus === 'saved'}
            title={invalidToneName ? 'Tone names cannot be empty' : undefined}
          >
            {isSaving ? 'Saving...' : 'Save changes'}
          </Button>
        </div>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button
            type="button"
            onClick={clearError}
            title="Dismiss error"
            aria-label="Dismiss error"
          >
            <X size={14} aria-hidden="true" />
          </button>
        </div>
      )}

      <div className="settings-grid">
        {/* Providers */}
        <section className="card settings-panel" aria-labelledby="providers-title">
          <div className="settings-head">
            <div>
              <h2 id="providers-title">Providers</h2>
              <p className="panel-subtitle">Add an endpoint, then choose the active provider.</p>
            </div>
            <div className="input-row">
              <span className="muted text-caption">Add:</span>
              {PRESET_KINDS.map((kind) => (
                <Button
                  key={kind}
                  variant="secondary"
                  size="sm"
                  onClick={() => addProvider(kind)}
                  disabled={isSaving}
                >
                  {PRESETS[kind].label}
                </Button>
              ))}
            </div>
          </div>

          <div className="active-row">
            <label className="label" htmlFor="active-provider">
              Active provider
            </label>
            <select
              id="active-provider"
              value={draft.active_provider_id}
              onChange={(e) =>
                updateDraft((current) => ({ ...current, active_provider_id: e.target.value }))
              }
              disabled={isSaving}
              className="select"
            >
              <option value="">None (dictation only)</option>
              {draft.providers.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.label || provider.id}
                </option>
              ))}
              {draft.active_provider_id !== '' && !persistedIds.has(draft.active_provider_id) && (
                <option value={draft.active_provider_id}>
                  {draft.active_provider_id} (not configured)
                </option>
              )}
            </select>
          </div>

          {draft.providers.length === 0 ? (
            <p className="empty-panel">
              No providers configured. Write and Command modes degrade to dictation until one is
              ready.
            </p>
          ) : (
            <div>
              {draft.providers.map((provider) => {
                const persisted = persistedIds.has(provider.id)
                return (
                  <div key={provider.id} className="subpanel">
                    <div className="subpanel-head">
                      <div className="subpanel-title">
                        <h3>{provider.label || provider.id}</h3>
                        <span className="provider-id">
                          {provider.kind} · {provider.id}
                        </span>
                        {hasKeys[provider.id] && (
                          <span className="pill" data-tone="success">
                            <span className="save-dot" aria-hidden="true" />
                            Key stored
                          </span>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => removeProvider(provider.id)}
                        disabled={isSaving}
                        className="icon-button"
                        data-tone="danger"
                        title="Remove provider"
                        aria-label="Remove provider"
                      >
                        <Trash2 size={15} aria-hidden="true" />
                      </button>
                    </div>

                    <div className="field-grid">
                      <div className="field">
                        <label className="label" htmlFor={`provider-label-${provider.id}`}>
                          Label
                        </label>
                        <input
                          id={`provider-label-${provider.id}`}
                          type="text"
                          value={provider.label}
                          onChange={(e) => updateProvider(provider.id, { label: e.target.value })}
                          disabled={isSaving}
                          className="input"
                        />
                      </div>
                      <div className="field">
                        <label className="label" htmlFor={`provider-model-${provider.id}`}>
                          Model
                        </label>
                        <div className="input-row">
                          <input
                            id={`provider-model-${provider.id}`}
                            type="text"
                            list={`provider-models-${provider.id}`}
                            value={provider.model}
                            onChange={(e) => updateProvider(provider.id, { model: e.target.value })}
                            disabled={isSaving}
                            placeholder={provider.kind === 'custom' ? 'model id' : undefined}
                            className="input"
                          />
                          <datalist id={`provider-models-${provider.id}`}>
                            {(providerModels[provider.id] ?? []).map((model) => (
                              <option key={model.id} value={model.id}>
                                {model.name ?? undefined}
                              </option>
                            ))}
                          </datalist>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => void loadModels(provider)}
                            disabled={!persisted || loadingModelsId === provider.id || isSaving}
                            title={
                              persisted ? 'Load models from the provider' : 'Save settings first'
                            }
                          >
                            {loadingModelsId === provider.id ? 'Loading...' : 'Load models'}
                          </Button>
                        </div>
                        {providerModels[provider.id] && (
                          <p className="field-hint">
                            {providerModels[provider.id].length}{' '}
                            {providerModels[provider.id].length === 1 ? 'model' : 'models'} available
                          </p>
                        )}
                        {modelErrors[provider.id] && (
                          <p className="field-error">{modelErrors[provider.id]}</p>
                        )}
                      </div>
                      <div className="field field-wide">
                        <label className="label" htmlFor={`provider-url-${provider.id}`}>
                          Base URL
                        </label>
                        <input
                          id={`provider-url-${provider.id}`}
                          type="text"
                          value={provider.base_url}
                          onChange={(e) => updateProvider(provider.id, { base_url: e.target.value })}
                          disabled={isSaving}
                          placeholder={
                            provider.kind === 'custom' ? 'https://host/v1' : 'empty uses the kind default'
                          }
                          className="input"
                        />
                      </div>
                      <div className="field">
                        <label className="label" htmlFor={`provider-timeout-${provider.id}`}>
                          Timeout (s)
                        </label>
                        <input
                          id={`provider-timeout-${provider.id}`}
                          type="number"
                          min={1}
                          max={120}
                          step={1}
                          value={provider.timeout_seconds}
                          onChange={(e) =>
                            updateProvider(provider.id, {
                              timeout_seconds: Number.isFinite(Number(e.target.value))
                                ? Number(e.target.value)
                                : 20
                            })
                          }
                          disabled={isSaving}
                          className="input"
                        />
                      </div>
                      <div className="field">
                        <label className="label" htmlFor={`provider-key-${provider.id}`}>
                          API key
                        </label>
                        <div className="input-row">
                          <input
                            id={`provider-key-${provider.id}`}
                            type="password"
                            value={keyDrafts[provider.id] ?? ''}
                            onChange={(e) =>
                              setKeyDrafts((prev) => ({ ...prev, [provider.id]: e.target.value }))
                            }
                            disabled={!persisted || savingKeyId === provider.id || isSaving}
                            placeholder={hasKeys[provider.id] ? 'stored - enter to replace' : 'not stored'}
                            className="input"
                          />
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() =>
                              void handleSaveKey(provider.id, keyDrafts[provider.id] ?? '')
                            }
                            disabled={
                              !persisted ||
                              savingKeyId === provider.id ||
                              isSaving ||
                              !(keyDrafts[provider.id] ?? '').trim()
                            }
                            title={persisted ? 'Store key' : 'Save settings first'}
                          >
                            {savingKeyId === provider.id ? 'Saving...' : 'Store key'}
                          </Button>
                          {hasKeys[provider.id] && (
                            <button
                              type="button"
                              onClick={() => void handleSaveKey(provider.id, '')}
                              disabled={!persisted || savingKeyId === provider.id || isSaving}
                              className="text-button"
                              data-tone="danger"
                            >
                              Clear
                            </button>
                          )}
                        </div>
                        {!persisted && (
                          <p className="field-hint">
                            Save settings before storing a key for this provider.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        <div className="settings-column">
          {/* Tone profiles */}
          <section className="card settings-panel" aria-labelledby="tones-title">
            <div className="settings-head">
              <div>
                <h2 id="tones-title">Tone profiles</h2>
                <p className="panel-subtitle">
                  Write mode appends the first profile whose match fires, else the default tone.
                </p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  updateDraft((current) => ({
                    ...current,
                    tone_profiles: [
                      ...current.tone_profiles,
                      { name: 'New tone', prompt: '', matches: [{ field: 'app', pattern: '' }] }
                    ]
                  }))
                }
                disabled={isSaving}
              >
                Add profile
              </Button>
            </div>

            <div className="focused-row">
              <span>
                {focusedAppLoaded ? (
                  focusedApp ? (
                    <>
                      Focused app:{' '}
                      <span className="focused-key">{focusedApp.key}</span>
                      {focusedApp.title && <span className="muted"> · {focusedApp.title}</span>}
                    </>
                  ) : (
                    'Focused app: not detected'
                  )
                ) : (
                  'Detecting the focused app...'
                )}
              </span>
              <button type="button" className="text-button" onClick={refreshFocusedApp}>
                Refresh
              </button>
            </div>

            {draft.tone_profiles.length === 0 ? (
              <p className="empty-panel">No tone profiles. Write mode uses the default tone below.</p>
            ) : (
              <div>
                {draft.tone_profiles.map((profile, index) => (
                  <div key={index} className="subpanel">
                    <div className="tone-head">
                      <input
                        type="text"
                        value={profile.name}
                        onChange={(e) => updateTone(index, { name: e.target.value })}
                        disabled={isSaving}
                        placeholder="Profile name"
                        aria-label={`Tone profile ${index + 1} name`}
                        className="input"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          updateDraft((current) => ({
                            ...current,
                            tone_profiles: current.tone_profiles.filter((_, i) => i !== index)
                          }))
                        }
                        disabled={isSaving}
                        className="icon-button"
                        data-tone="danger"
                        title="Remove profile"
                        aria-label={`Remove tone profile ${index + 1}`}
                      >
                        <X size={15} aria-hidden="true" />
                      </button>
                    </div>
                    <div className="tone-fields">
                      <textarea
                        value={profile.prompt}
                        onChange={(e) => updateTone(index, { prompt: e.target.value })}
                        disabled={isSaving}
                        placeholder="Tone instructions appended to the rewrite prompt"
                        aria-label={`Tone profile ${index + 1} prompt`}
                        rows={2}
                        className="textarea"
                      />
                      {profile.matches.map((match, matchIndex) => (
                        <div key={matchIndex} className="tone-match">
                          <select
                            value={match.field}
                            onChange={(e) => {
                              const field = e.target.value as 'app' | 'title'
                              updateTone(index, {
                                matches: profile.matches.map((entry, i) =>
                                  i === matchIndex ? { ...entry, field } : entry
                                )
                              })
                            }}
                            disabled={isSaving}
                            aria-label={`Tone profile ${index + 1} match field ${matchIndex + 1}`}
                            className="select"
                          >
                            <option value="app">App</option>
                            <option value="title">Title</option>
                          </select>
                          <div className="input-row">
                            <input
                              type="text"
                              value={match.pattern}
                              onChange={(e) =>
                                updateTone(index, {
                                  matches: profile.matches.map((entry, i) =>
                                    i === matchIndex ? { ...entry, pattern: e.target.value } : entry
                                  )
                                })
                              }
                              disabled={isSaving}
                              placeholder="match pattern (case-insensitive substring)"
                              aria-label={`Tone profile ${index + 1} match pattern ${matchIndex + 1}`}
                              className="input"
                            />
                            <button
                              type="button"
                              onClick={() =>
                                updateTone(index, {
                                  matches: profile.matches.filter((_, i) => i !== matchIndex)
                                })
                              }
                              disabled={isSaving}
                              className="icon-button"
                              data-tone="danger"
                              title="Remove match"
                              aria-label={`Remove match ${matchIndex + 1}`}
                            >
                              <X size={15} aria-hidden="true" />
                            </button>
                          </div>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() =>
                          updateTone(index, {
                            matches: [...profile.matches, { field: 'app', pattern: '' }]
                          })
                        }
                        disabled={isSaving}
                        className="text-button"
                      >
                        + Add match
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Default tone and command prompt */}
          <div className="prompt-grid">
            <section className="card settings-panel" aria-labelledby="default-tone-title">
              <div className="settings-head">
                <div>
                  <h2 id="default-tone-title">Default tone</h2>
                  <p className="panel-subtitle">Used when no profile matches.</p>
                </div>
              </div>
              <div className="settings-rows">
                <div className="field">
                  <label className="label" htmlFor="default-tone-name">
                    Name
                  </label>
                  <input
                    id="default-tone-name"
                    type="text"
                    value={draft.default_tone.name}
                    onChange={(e) =>
                      updateDraft((current) => ({
                        ...current,
                        default_tone: { ...current.default_tone, name: e.target.value }
                      }))
                    }
                    disabled={isSaving}
                    className="input"
                  />
                </div>
                <div className="field">
                  <label className="label" htmlFor="default-tone-prompt">
                    Prompt
                  </label>
                  <textarea
                    id="default-tone-prompt"
                    value={draft.default_tone.prompt}
                    onChange={(e) =>
                      updateDraft((current) => ({
                        ...current,
                        default_tone: { ...current.default_tone, prompt: e.target.value }
                      }))
                    }
                    disabled={isSaving}
                    placeholder="Empty uses the built-in rewrite instruction"
                    rows={2}
                    className="textarea"
                  />
                </div>
              </div>
            </section>

            <section className="card settings-panel" aria-labelledby="command-prompt-title">
              <div className="settings-head">
                <div>
                  <h2 id="command-prompt-title">Command prompt</h2>
                  <p className="panel-subtitle">Turns speech into a direct instruction.</p>
                </div>
              </div>
              <div className="field">
                <label className="label" htmlFor="command-prompt">
                  Prompt
                </label>
                <textarea
                  id="command-prompt"
                  value={draft.command_prompt}
                  onChange={(e) =>
                    updateDraft((current) => ({ ...current, command_prompt: e.target.value }))
                  }
                  disabled={isSaving}
                  rows={3}
                  className="textarea"
                />
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}
