"""Pure planning and execution for AI processing modes.

Turns settings, a requested mode, the focused app, and provider key presence into a
``ProcessingPlan``, then runs the plan against a caller-supplied provider call. No I/O and
no persistence live here; the only provider I/O is the injected ``complete`` callable.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from speakeasy.core.text_cleanup import safe_cleanup
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

# Users paste a full endpoint from provider docs; the adapter appends the path itself.
_ENDPOINT_SUFFIXES = ("/chat/completions", "/completions")

WRITE_SYSTEM = (
    "Rewrite the dictated text so it reads naturally in the current application. "
    "Preserve the speaker's meaning, facts, and language. Output only the rewritten text."
)

# Bounded provider input: a longer dictation degrades to its fallback text.
MAX_LLM_INPUT_CHARS = 6000

ProviderReason = Literal[
    "timeout", "connection", "auth", "rate_limit", "server", "bad_response", "cancelled"
]


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
    """The provider's API root, falling back to its kind default (empty for custom).

    Accepts a pasted endpoint by stripping a trailing chat-completions path, so the
    adapter can append its own without doubling it.
    """
    url = (provider.base_url or DEFAULT_BASE_URLS[provider.kind]).rstrip("/")
    for suffix in _ENDPOINT_SUFFIXES:
        if url.endswith(suffix):
            return url[: -len(suffix)].rstrip("/")
    return url


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


def _ready_provider(
    settings: AppSettings, keyed_provider_ids: frozenset[str]
) -> LlmProvider | None:
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


class ProviderError(Exception):
    """A provider call failure with a safe, human-readable detail.

    ``detail`` never contains the request key, the prompt, or the full response body.
    A status failure may include up to 200 characters of the provider's own
    ``error.message``, with the request key and prompt text redacted.
    """

    def __init__(self, reason: ProviderReason, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class LlmRequest(BaseModel):
    """One chat completion request, already resolved by the plan."""

    model_config = ConfigDict(frozen=True)

    system: str
    user: str


class LlmResponse(BaseModel):
    """The provider's reply text."""

    model_config = ConfigDict(frozen=True)

    text: str


CompleteFn = Callable[[LlmRequest], Awaitable[LlmResponse]]


class ProcessResult(BaseModel):
    """The executor's outcome. ``insertable`` is False only when a newer run superseded it."""

    model_config = ConfigDict(frozen=True)

    text: str
    error: str | None = None
    insertable: bool = True


@dataclass
class ProcessingRun:
    """Single-slot owner of the in-flight provider call.

    The app records one session at a time, so one slot is the true invariant.
    """

    generation: int = 0
    task: asyncio.Task | None = None

    def supersede(self) -> None:
        """Invalidate the current generation and cancel the in-flight task. Idempotent."""
        self.generation += 1
        if self.task is not None:
            self.task.cancel()
            self.task = None


_active_run = ProcessingRun()


def begin_processing() -> ProcessingRun:
    """Supersede whatever is in flight, then hand back the current run."""
    _active_run.supersede()
    return _active_run


def cancel_processing() -> None:
    """Cancel the in-flight provider call, if any."""
    _active_run.supersede()


_FENCE = re.compile(r"^```[^\n]*\n(.*?)\n```$", re.DOTALL)


def sanitize(text: str) -> str:
    """Strip, and unwrap one markdown fence that wraps the whole response."""
    text = text.strip()
    fenced = _FENCE.match(text)
    if fenced is not None:
        return fenced.group(1).strip()
    return text


async def execute_plan(
    plan: ProcessingPlan,
    text: str,
    *,
    complete: CompleteFn | None,
    run: ProcessingRun,
) -> ProcessResult:
    """Run the plan's LLM step. Never raises for provider trouble.

    Every degraded path returns the plan's fallback text: the cleaned transcript when the
    plan carries cleanup, the raw text otherwise. A superseded run returns its fallback
    with ``error="cancelled"`` and ``insertable=False``, so the caller must not paste it.
    """
    fallback = (
        safe_cleanup(text, custom_fillers=plan.cleanup.custom_fillers, use_cache=True)
        if plan.cleanup is not None
        else text
    )
    if plan.rewrite is None or complete is None:
        return ProcessResult(text=fallback)
    if not text.strip():
        return ProcessResult(text=fallback)
    if len(text) > MAX_LLM_INPUT_CHARS:
        return ProcessResult(text=fallback, error="transcript too long for AI processing")

    generation = run.generation
    request = LlmRequest(system=plan.rewrite.system_prompt, user=text)
    task: asyncio.Task[LlmResponse] = asyncio.create_task(complete(request))
    run.task = task
    try:
        response = await asyncio.wait_for(task, timeout=plan.rewrite.provider.timeout_seconds)
    except asyncio.TimeoutError:
        timeout = plan.rewrite.provider.timeout_seconds
        return ProcessResult(text=fallback, error=f"provider timed out after {timeout:g}s")
    except ProviderError as exc:
        return ProcessResult(text=fallback, error=exc.detail)
    except asyncio.CancelledError:
        if run.generation != generation:
            return ProcessResult(text=fallback, error="cancelled", insertable=False)
        raise
    finally:
        if run.task is task:
            run.task = None

    if run.generation != generation:
        return ProcessResult(text=fallback, error="cancelled", insertable=False)
    sanitized = sanitize(response.text)
    if not sanitized:
        return ProcessResult(text=fallback, error="empty response")
    return ProcessResult(text=sanitized)
