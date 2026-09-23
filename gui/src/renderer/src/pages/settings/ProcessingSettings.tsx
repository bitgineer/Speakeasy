/**
 * Processing Settings Page
 *
 * LLM providers and API keys, write-mode tone profiles, the default tone,
 * and the command-mode prompt.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useSettingsStore } from '../../store'
import { apiClient } from '../../api/client'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import type {
  AppMatch,
  FocusedAppResponse,
  LlmProvider,
  ProviderKind,
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
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
      </div>
    )
  }

  const persistedIds = new Set((settings?.providers ?? []).map((provider) => provider.id))

  return (
    <div className="p-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Processing</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Providers, API keys, and the prompts behind Write and Command modes
          </p>
        </div>
        <div className="flex items-center gap-4">
          <SaveStatusIndicator status={saveStatus} />
          <button
            onClick={handleSave}
            disabled={isSaving || invalidToneName || saveStatus === 'idle' || saveStatus === 'saved'}
            className="btn-primary"
            title={invalidToneName ? 'Tone names cannot be empty' : undefined}
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 p-3 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg flex items-center justify-between">
          <span className="text-[var(--color-error)] text-sm">{error}</span>
          <button onClick={clearError} className="text-[var(--color-error)] hover:opacity-80">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="space-y-6">
        {/* Providers */}
        <section className="card p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-medium text-[var(--color-text-primary)]">Providers</h2>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[var(--color-text-muted)]">Add:</span>
              {PRESET_KINDS.map((kind) => (
                <button
                  key={kind}
                  onClick={() => addProvider(kind)}
                  disabled={isSaving}
                  className="px-2.5 py-1 text-xs font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-md border border-[var(--color-border)] transition-colors disabled:opacity-50"
                >
                  {PRESETS[kind].label}
                </button>
              ))}
            </div>
          </div>

          {draft.providers.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)] py-4 text-center">
              No providers configured. Write and Command modes degrade to dictation until one is ready.
            </p>
          ) : (
            <div className="space-y-4">
              {draft.providers.map((provider) => {
                const persisted = persistedIds.has(provider.id)
                return (
                  <div
                    key={provider.id}
                    className="p-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-tertiary)] space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-[var(--color-text-primary)]">
                          {provider.label || provider.id}
                        </span>
                        <span className="text-xs font-mono text-[var(--color-text-muted)]">
                          {provider.kind} · {provider.id}
                        </span>
                        {hasKeys[provider.id] && (
                          <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-[var(--color-success-muted)] text-[var(--color-success)]">
                            Key stored
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => removeProvider(provider.id)}
                        disabled={isSaving}
                        className="p-1 text-[var(--color-text-muted)] hover:text-[var(--color-error)] rounded transition-colors disabled:opacity-50"
                        title="Remove provider"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="label">Label</label>
                        <input
                          type="text"
                          value={provider.label}
                          onChange={(e) => updateProvider(provider.id, { label: e.target.value })}
                          disabled={isSaving}
                          className="input w-full"
                        />
                      </div>
                      <div>
                        <label className="label">Model</label>
                        <input
                          type="text"
                          value={provider.model}
                          onChange={(e) => updateProvider(provider.id, { model: e.target.value })}
                          disabled={isSaving}
                          placeholder={provider.kind === 'custom' ? 'model id' : undefined}
                          className="input w-full"
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="label">Base URL</label>
                        <input
                          type="text"
                          value={provider.base_url}
                          onChange={(e) => updateProvider(provider.id, { base_url: e.target.value })}
                          disabled={isSaving}
                          placeholder={provider.kind === 'custom' ? 'https://host/v1' : 'empty uses the kind default'}
                          className="input w-full"
                        />
                      </div>
                      <div>
                        <label className="label">Timeout (s)</label>
                        <input
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
                          className="input w-full"
                        />
                      </div>
                      <div>
                        <label className="label">API key</label>
                        <div className="flex items-center gap-2">
                          <input
                            type="password"
                            value={keyDrafts[provider.id] ?? ''}
                            onChange={(e) =>
                              setKeyDrafts((prev) => ({ ...prev, [provider.id]: e.target.value }))
                            }
                            disabled={!persisted || savingKeyId === provider.id || isSaving}
                            placeholder={hasKeys[provider.id] ? 'stored - enter to replace' : 'not stored'}
                            className="input w-full"
                          />
                          <button
                            onClick={() => void handleSaveKey(provider.id, keyDrafts[provider.id] ?? '')}
                            disabled={
                              !persisted ||
                              savingKeyId === provider.id ||
                              isSaving ||
                              !(keyDrafts[provider.id] ?? '').trim()
                            }
                            className="px-2.5 py-1.5 text-xs font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-secondary)] hover:text-[var(--color-text-primary)] rounded-md border border-[var(--color-border)] transition-colors disabled:opacity-50 whitespace-nowrap"
                            title={persisted ? 'Store key' : 'Save settings first'}
                          >
                            {savingKeyId === provider.id ? 'Saving...' : 'Store key'}
                          </button>
                          {hasKeys[provider.id] && (
                            <button
                              onClick={() => void handleSaveKey(provider.id, '')}
                              disabled={!persisted || savingKeyId === provider.id || isSaving}
                              className="px-2.5 py-1.5 text-xs font-medium text-[var(--color-error)] hover:bg-[var(--color-error-muted)] rounded-md transition-colors disabled:opacity-50 whitespace-nowrap"
                            >
                              Clear
                            </button>
                          )}
                        </div>
                        {!persisted && (
                          <p className="text-xs text-[var(--color-text-muted)] mt-1">
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

          <div className="mt-4">
            <label className="label">Active provider</label>
            <select
              value={draft.active_provider_id}
              onChange={(e) => updateDraft((current) => ({ ...current, active_provider_id: e.target.value }))}
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
        </section>

        {/* Tone profiles */}
        <section className="card p-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-medium text-[var(--color-text-primary)]">Tone Profiles</h2>
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                Write mode appends the first profile whose match fires, else the default tone.
              </p>
            </div>
            <button
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
              className="px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-lg border border-[var(--color-border)] transition-colors disabled:opacity-50"
            >
              Add profile
            </button>
          </div>

          <div className="mb-4 p-2.5 rounded-lg bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] flex items-center justify-between">
            <div className="text-xs text-[var(--color-text-muted)]">
              {focusedAppLoaded ? (
                focusedApp ? (
                  <>
                    Focused app: <span className="font-mono text-[var(--color-text-secondary)]">{focusedApp.key}</span>
                    {focusedApp.title && <span className="ml-2">· {focusedApp.title}</span>}
                  </>
                ) : (
                  'Focused app: not detected'
                )
              ) : (
                'Detecting the focused app...'
              )}
            </div>
            <button
              onClick={refreshFocusedApp}
              className="text-xs text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
            >
              Refresh
            </button>
          </div>

          {draft.tone_profiles.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)] py-4 text-center">
              No tone profiles. Write mode uses the default tone below.
            </p>
          ) : (
            <div className="space-y-4">
              {draft.tone_profiles.map((profile, index) => (
                <div
                  key={index}
                  className="p-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-tertiary)] space-y-3"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={profile.name}
                      onChange={(e) => updateTone(index, { name: e.target.value })}
                      disabled={isSaving}
                      placeholder="Profile name"
                      className="input flex-1"
                    />
                    <button
                      onClick={() =>
                        updateDraft((current) => ({
                          ...current,
                          tone_profiles: current.tone_profiles.filter((_, i) => i !== index)
                        }))
                      }
                      disabled={isSaving}
                      className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-error)] rounded transition-colors disabled:opacity-50"
                      title="Remove profile"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <textarea
                    value={profile.prompt}
                    onChange={(e) => updateTone(index, { prompt: e.target.value })}
                    disabled={isSaving}
                    placeholder="Tone instructions appended to the rewrite prompt"
                    rows={2}
                    className="input w-full resize-y"
                  />
                  <div className="space-y-2">
                    {profile.matches.map((match, matchIndex) => (
                      <div key={matchIndex} className="flex items-center gap-2">
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
                          className="select w-28"
                        >
                          <option value="app">App</option>
                          <option value="title">Title</option>
                        </select>
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
                          className="input flex-1"
                        />
                        <button
                          onClick={() =>
                            updateTone(index, {
                              matches: profile.matches.filter((_, i) => i !== matchIndex)
                            })
                          }
                          disabled={isSaving}
                          className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-error)] rounded transition-colors disabled:opacity-50"
                          title="Remove match"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                    <button
                      onClick={() =>
                        updateTone(index, {
                          matches: [...profile.matches, { field: 'app', pattern: '' }]
                        })
                      }
                      disabled={isSaving}
                      className="text-xs text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
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
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Default Tone</h2>
          <div className="space-y-3">
            <div>
              <label className="label">Name</label>
              <input
                type="text"
                value={draft.default_tone.name}
                onChange={(e) =>
                  updateDraft((current) => ({
                    ...current,
                    default_tone: { ...current.default_tone, name: e.target.value }
                  }))
                }
                disabled={isSaving}
                className="input w-full"
              />
            </div>
            <div>
              <label className="label">Prompt</label>
              <textarea
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
                className="input w-full resize-y"
              />
            </div>
          </div>
        </section>

        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Command Prompt</h2>
          <textarea
            value={draft.command_prompt}
            onChange={(e) => updateDraft((current) => ({ ...current, command_prompt: e.target.value }))}
            disabled={isSaving}
            rows={3}
            className="input w-full resize-y"
          />
        </section>
      </div>
    </div>
  )
}
