"""OpenAI-compatible provider adapter for LLM rewrite calls.

One wire protocol serves every provider kind; a future kind with a different protocol replaces
its own entry in ``PROVIDER_ADAPTERS``. Nothing here logs a key, a prompt, or a response body.
"""

from collections.abc import Awaitable, Callable

import httpx

from speakeasy.core.processing import (
    CompleteFn,
    LlmRequest,
    LlmResponse,
    ProviderError,
    effective_base_url,
)
from speakeasy.services.settings import LlmProvider, ProviderKind

ProviderAdapter = Callable[[LlmProvider, LlmRequest, str | None], Awaitable[LlmResponse]]


async def complete_openai_compatible(
    provider: LlmProvider,
    request: LlmRequest,
    api_key: str | None,
    *,
    client: httpx.AsyncClient | None = None,
) -> LlmResponse:
    """POST one non-streaming chat completion.

    Raises ``ProviderError`` with a safe detail on any transport, status, or payload failure.
    The caller owns a supplied client; otherwise one is created and closed here.
    """
    url = f"{effective_base_url(provider).rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": provider.model,
        "messages": [
            {"role": "system", "content": request.system},
            {"role": "user", "content": request.user},
        ],
        "temperature": 0,
        "stream": False,
    }

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=provider.timeout_seconds + 2.0)
    try:
        response = await client.post(url, json=payload, headers=headers)
        content = _content_of(response)
    except httpx.TimeoutException as exc:
        timeout = provider.timeout_seconds
        raise ProviderError("timeout", f"provider timed out after {timeout:g}s") from exc
    except httpx.InvalidURL as exc:
        raise ProviderError("connection", "provider base url is invalid") from exc
    except httpx.HTTPError as exc:
        raise ProviderError("connection", "could not reach the provider") from exc
    finally:
        if owns_client:
            await client.aclose()
    return LlmResponse(text=content)


def _content_of(response: httpx.Response) -> str:
    error = _status_error(response)
    if error is not None:
        raise error
    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise ProviderError("bad_response", "provider returned an unexpected response") from None
    if not isinstance(content, str) or not content.strip():
        raise ProviderError("bad_response", "provider returned an empty response")
    return content.strip()


def _status_error(response: httpx.Response) -> ProviderError | None:
    status = response.status_code
    if status in (401, 403):
        return ProviderError("auth", "provider rejected the API key")
    if status == 429:
        return ProviderError("rate_limit", "provider rate limit reached")
    if status >= 500:
        return ProviderError("server", f"provider server error ({status})")
    if not 200 <= status < 300:
        return ProviderError("bad_response", f"provider returned HTTP {status}")
    return None


PROVIDER_ADAPTERS: dict[ProviderKind, ProviderAdapter] = {
    kind: complete_openai_compatible for kind in ProviderKind
}


def build_provider_client(provider: LlmProvider, api_key: str | None) -> CompleteFn:
    """A ``complete`` callable with one short-lived client per call, and no retries."""

    async def complete(request: LlmRequest) -> LlmResponse:
        async with httpx.AsyncClient(timeout=provider.timeout_seconds + 2.0) as client:
            return await complete_openai_compatible(provider, request, api_key, client=client)

    return complete
