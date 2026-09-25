"""Tests for core.processing.execute_plan."""

import asyncio

import pytest

from speakeasy.core import processing
from speakeasy.core.processing import (
    MAX_LLM_INPUT_CHARS,
    CleanupSpec,
    LlmRequest,
    LlmResponse,
    ProcessingPlan,
    ProcessingRun,
    ProcessResult,
    ProviderError,
    RewriteSpec,
    execute_plan,
)
from speakeasy.services.settings import LlmProvider, ProcessingMode

PROVIDER = LlmProvider(id="p", model="m", timeout_seconds=1.0)


def _plan(*, cleanup: CleanupSpec | None = None, rewrite: bool = True) -> ProcessingPlan:
    rewrite_spec = RewriteSpec(provider=PROVIDER, system_prompt="Be natural.") if rewrite else None
    return ProcessingPlan(mode=ProcessingMode.WRITE, cleanup=cleanup, rewrite=rewrite_spec)


async def test_success_returns_the_sanitized_response():
    seen = {}

    async def complete(request):
        seen["request"] = request
        return LlmResponse(text="```text\nHello there.\n```")

    result = await execute_plan(_plan(), "hello there", complete=complete, run=ProcessingRun())

    assert result == ProcessResult(text="Hello there.")
    assert seen["request"] == LlmRequest(system="Be natural.", user="hello there")


async def test_provider_error_returns_the_fallback_and_the_detail():
    async def complete(request):
        raise ProviderError("auth", "provider rejected the API key")

    result = await execute_plan(_plan(), "hello", complete=complete, run=ProcessingRun())

    assert result == ProcessResult(text="hello", error="provider rejected the API key")


async def test_timeout_returns_the_fallback_with_a_safe_detail():
    async def complete(request):
        await asyncio.sleep(30)

    result = await execute_plan(_plan(), "hello", complete=complete, run=ProcessingRun())

    assert result == ProcessResult(text="hello", error="provider timed out after 1s")


async def test_blank_transcript_skips_the_call():
    called = False

    async def complete(request):
        nonlocal called
        called = True
        return LlmResponse(text="unused")

    result = await execute_plan(_plan(), "   \n", complete=complete, run=ProcessingRun())

    assert result == ProcessResult(text="   \n")
    assert called is False


async def test_oversized_transcript_skips_the_call():
    called = False
    text = "a" * (MAX_LLM_INPUT_CHARS + 1)

    async def complete(request):
        nonlocal called
        called = True
        return LlmResponse(text="unused")

    result = await execute_plan(_plan(), text, complete=complete, run=ProcessingRun())

    assert result == ProcessResult(text=text, error="transcript too long for AI processing")
    assert called is False


async def test_no_rewrite_returns_the_fallback():
    result = await execute_plan(_plan(rewrite=False), "hello", complete=None, run=ProcessingRun())

    assert result == ProcessResult(text="hello")


async def test_missing_complete_returns_the_fallback():
    result = await execute_plan(_plan(), "hello", complete=None, run=ProcessingRun())

    assert result == ProcessResult(text="hello")


async def test_fallback_text_uses_the_plan_cleanup(monkeypatch):
    calls = {}

    def fake_cleanup(text, custom_fillers=None, use_cache=True):
        calls.update(text=text, custom_fillers=custom_fillers, use_cache=use_cache)
        return "clean text"

    monkeypatch.setattr(processing, "safe_cleanup", fake_cleanup)
    plan = _plan(cleanup=CleanupSpec(custom_fillers=["hmm"]))

    async def complete(request):
        raise ProviderError("connection", "could not reach the provider")

    result = await execute_plan(plan, "hmm hello", complete=complete, run=ProcessingRun())

    assert result == ProcessResult(text="clean text", error="could not reach the provider")
    assert calls == {"text": "hmm hello", "custom_fillers": ["hmm"], "use_cache": True}


async def test_sanitized_empty_response_returns_the_fallback():
    async def complete(request):
        return LlmResponse(text="```text\n\n```")

    result = await execute_plan(_plan(), "hello", complete=complete, run=ProcessingRun())

    assert result == ProcessResult(text="hello", error="empty response")


async def test_supersession_cancels_the_call_and_returns_not_insertable():
    started = asyncio.Event()
    cancelled = False

    async def complete(request):
        nonlocal cancelled
        started.set()
        try:
            await asyncio.sleep(30)
        finally:
            cancelled = True
        return LlmResponse(text="too late")

    run = ProcessingRun()
    task = asyncio.create_task(execute_plan(_plan(), "hello", complete=complete, run=run))
    await started.wait()

    run.supersede()
    result = await task

    assert result == ProcessResult(text="hello", error="cancelled", insertable=False)
    assert cancelled is True
    assert run.task is None


async def test_external_cancellation_propagates():
    started = asyncio.Event()

    async def complete(request):
        started.set()
        await asyncio.sleep(30)
        return LlmResponse(text="too late")

    run = ProcessingRun()
    task = asyncio.create_task(execute_plan(_plan(), "hello", complete=complete, run=run))
    await started.wait()

    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert run.task is None


async def test_run_task_is_cleared_after_success():
    run = ProcessingRun()

    async def complete(request):
        return LlmResponse(text="done")

    await execute_plan(_plan(), "hello", complete=complete, run=run)

    assert run.task is None
