"""Pure planning for AI processing modes.

Turns settings, a requested mode, the focused app, and provider key presence into a
``ProcessingPlan``. No I/O and no persistence live here.
"""

from pydantic import BaseModel, ConfigDict, Field

from speakeasy.services.settings import (
    AppSettings,
    LlmProvider,
    ProcessingMode,
    ProviderKind,
    ToneProfile,
)

DEFAULT_BASE_URLS: dict[ProviderKind, str] = {
    ProviderKind.LOCAL: "http://127.0.0.1:11434/v1",
    ProviderKind.OPENAI: "https://api.openai.com/v1",
    ProviderKind.GROQ: "https://api.groq.com/openai/v1",
    ProviderKind.CUSTOM: "",
}

WRITE_SYSTEM = (
    "Rewrite the dictated text so it reads naturally in the current application. "
    "Preserve the speaker's meaning, facts, and language. Output only the rewritten text."
)


class FocusedApp(BaseModel):
    """The app that had focus when the utterance was recorded."""

    model_config = ConfigDict(frozen=True)

    key: str
    title: str = ""


class CleanupSpec(BaseModel):
    """Regex cleanup for the fallback text when no LLM call runs."""

    model_config = ConfigDict(frozen=True)

    custom_fillers: list[str] = Field(default_factory=list)


class RewriteSpec(BaseModel):
    """The exact provider call a plan will make."""

    model_config = ConfigDict(frozen=True)

    provider: LlmProvider
    system_prompt: str


class ProcessingPlan(BaseModel):
    """What the executor will do. ``rewrite`` is present iff an LLM call will run."""

    model_config = ConfigDict(frozen=True)

    mode: ProcessingMode
    cleanup: CleanupSpec | None
    rewrite: RewriteSpec | None


class ModeReadiness(BaseModel):
    """Whether a mode can run an LLM call, and why not when it cannot."""

    model_config = ConfigDict(frozen=True)

    mode: ProcessingMode
    ready: bool
    reason: str | None


def requires_key(kind: ProviderKind) -> bool:
    """Whether credentials are mandatory for this provider kind."""
    return kind in (ProviderKind.OPENAI, ProviderKind.GROQ)


def effective_base_url(provider: LlmProvider) -> str:
    """The provider's base URL, falling back to its kind default (empty for custom)."""
    return provider.base_url or DEFAULT_BASE_URLS[provider.kind]


def matches_app(profile: ToneProfile, app: FocusedApp) -> bool:
    """True when any match rule fires. An ``app`` rule reads ``key``, a ``title`` rule ``title``."""
    fields = {"app": app.key, "title": app.title}
    return any(rule.pattern.lower() in fields[rule.field].lower() for rule in profile.matches)


def _write_system(tone: ToneProfile) -> str:
    tone_prompt = tone.prompt.strip()
    if not tone_prompt:
        return WRITE_SYSTEM
    return f"{WRITE_SYSTEM}\n\nTone guidance: {tone_prompt}"


def _first_matching_tone(settings: AppSettings, app: FocusedApp | None) -> ToneProfile:
    if app is not None:
        for profile in settings.tone_profiles:
            if matches_app(profile, app):
                return profile
    return settings.default_tone


def _active_provider(settings: AppSettings) -> LlmProvider | None:
    return next((p for p in settings.providers if p.id == settings.active_provider_id), None)


def _provider_issue(settings: AppSettings, keyed_provider_ids: frozenset[str]) -> str | None:
    """The one readiness rule. None means the active provider can serve a call."""
    if not settings.active_provider_id:
        return "no provider configured"
    provider = _active_provider(settings)
    if provider is None:
        return "provider not found"
    if not provider.model:
        return "model missing"
    if not effective_base_url(provider):
        return "base url missing"
    if requires_key(provider.kind) and provider.id not in keyed_provider_ids:
        return "key missing"
    return None


def _ready_provider(settings: AppSettings, keyed_provider_ids: frozenset[str]) -> LlmProvider | None:
    if _provider_issue(settings, keyed_provider_ids) is not None:
        return None
    return _active_provider(settings)


def resolve_processing(
    settings: AppSettings,
    mode: ProcessingMode | None,
    app: FocusedApp | None,
    keyed_provider_ids: frozenset[str],
) -> ProcessingPlan:
    """Pure and total. ``mode`` None falls back to ``settings.active_mode``.

    A mode without a ready provider degrades to cleanup-only; it never raises.
    """
    resolved_mode = mode or settings.active_mode
    cleanup = (
        CleanupSpec(custom_fillers=settings.custom_filler_words or [])
        if settings.enable_text_cleanup
        else None
    )

    rewrite: RewriteSpec | None = None
    if resolved_mode is not ProcessingMode.DICTATE:
        provider = _ready_provider(settings, keyed_provider_ids)
        if provider is not None:
            system_prompt = (
                _write_system(_first_matching_tone(settings, app))
                if resolved_mode is ProcessingMode.WRITE
                else settings.command_prompt
            )
            rewrite = RewriteSpec(provider=provider, system_prompt=system_prompt)

    return ProcessingPlan(mode=resolved_mode, cleanup=cleanup, rewrite=rewrite)


def describe_readiness(
    settings: AppSettings, keyed_provider_ids: frozenset[str]
) -> list[ModeReadiness]:
    """Readiness for every mode, from the same rule execution resolves against."""
    reason = _provider_issue(settings, keyed_provider_ids)
    return [
        ModeReadiness(mode=ProcessingMode.WRITE, ready=reason is None, reason=reason),
        ModeReadiness(mode=ProcessingMode.COMMAND, ready=reason is None, reason=reason),
        ModeReadiness(mode=ProcessingMode.DICTATE, ready=True, reason=None),
    ]
