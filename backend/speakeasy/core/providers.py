"""OpenAI-compatible provider adapter for LLM rewrite calls.

One wire protocol serves every provider kind; a future kind with a different protocol replaces
its own entry in ``PROVIDER_ADAPTERS``. Nothing here logs a key, a prompt, or a response body.
"""

import asyncio
from collections.abc import Awaitable, Callable

import httpx
from pydantic import BaseModel, ConfigDict

from speakeasy.core.processing import (
    CompleteFn,
    LlmRequest,
    LlmResponse,
    ProviderError,
    effective_base_url,
)
from speakeasy.services.settings import LlmProvider, ProviderKind

ProviderAdapter = Callable[[LlmProvider, LlmRequest, str | None], Awaitable[LlmResponse]]

_MODELS_TIMEOUT_SECONDS = 15.0
_ERROR_MESSAGE_MAX_CHARS = 200


class ProviderModel(BaseModel):
    """One model id a provider advertises, as returned by its ``/models`` endpoint."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str | None = None


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
    url = f"{effective_base_url(provider)}/chat/completions"
    headers = {"Content-Type": "application/json", **_auth_header(api_key)}
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


def _auth_header(api_key: str | None) -> dict[str, str]:
    """Bearer auth when a key exists, nothing otherwise."""
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


async def fetch_provider_models(
    provider: LlmProvider,
    api_key: str | None,
    *,
    client: httpx.Client | None = None,
) -> list[ProviderModel]:
    """List the models the provider advertises.

    The blocking GET runs on a worker thread. Raises ``ProviderError`` with a safe detail
    on any transport, status, or payload failure. The caller owns a supplied client;
    otherwise one is created and closed here.
    """
    return await asyncio.to_thread(_fetch_models, provider, api_key, client)


def _fetch_models(
    provider: LlmProvider, api_key: str | None, client: httpx.Client | None
) -> list[ProviderModel]:
    if client is not None:
        return _get_models(client, provider, api_key)
    with httpx.Client(timeout=_MODELS_TIMEOUT_SECONDS) as owned:
        return _get_models(owned, provider, api_key)


def _get_models(
    client: httpx.Client, provider: LlmProvider, api_key: str | None
) -> list[ProviderModel]:
    url = f"{effective_base_url(provider)}/models"
    try:
        response = client.get(url, headers=_auth_header(api_key), timeout=_MODELS_TIMEOUT_SECONDS)
    except httpx.TimeoutException as exc:
        timeout = _MODELS_TIMEOUT_SECONDS
        raise ProviderError("timeout", f"provider timed out after {timeout:g}s") from exc
    except httpx.InvalidURL as exc:
        raise ProviderError("connection", "provider base url is invalid") from exc
    except httpx.HTTPError as exc:
        raise ProviderError("connection", "could not reach the provider") from exc

    error = _status_error(response)
    if error is not None:
        raise error
    try:
        payload = response.json()
    except ValueError:
        raise ProviderError(
            "bad_response", "provider returned an unexpected models response"
        ) from None
    return _parse_models(payload)


def _parse_models(payload: object) -> list[ProviderModel]:
    """Tolerant parse of ``{"data": [...]}`` or a bare list; unique ids, sorted."""
    entries = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise ProviderError("bad_response", "provider returned an unexpected models response")
    by_id: dict[str, ProviderModel] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        model_id = entry.get("id")
        if not isinstance(model_id, str) or not model_id:
            continue
        name = entry.get("name")
        by_id[model_id] = ProviderModel(id=model_id, name=name if isinstance(name, str) else None)
    return sorted(by_id.values(), key=lambda model: model.id)


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
    if 200 <= status < 300:
        return None
    message = _provider_message(response)
    suffix = f": {message}" if message else ""
    if status in (401, 403):
        return ProviderError("auth", f"provider rejected the API key{suffix}")
    if status == 429:
        return ProviderError("rate_limit", f"provider rate limit reached{suffix}")
    if status >= 500:
        return ProviderError("server", f"provider server error ({status}){suffix}")
    return ProviderError("bad_response", f"provider returned HTTP {status}{suffix}")


def _provider_message(response: httpx.Response) -> str | None:
    """The provider's own error message when the body carries the OpenAI-compatible shape."""
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    error = payload.get("error")
    if not isinstance(error, dict):
        return None
    message = error.get("message")
    if not isinstance(message, str) or not message.strip():
        return None
    return message.strip()[:_ERROR_MESSAGE_MAX_CHARS]


PROVIDER_ADAPTERS: dict[ProviderKind, ProviderAdapter] = {
    kind: complete_openai_compatible for kind in ProviderKind
}


def build_provider_client(provider: LlmProvider, api_key: str | None) -> CompleteFn:
    """A ``complete`` callable with one short-lived client per call, and no retries."""

    async def complete(request: LlmRequest) -> LlmResponse:
        async with httpx.AsyncClient(timeout=provider.timeout_seconds + 2.0) as client:
            return await complete_openai_compatible(provider, request, api_key, client=client)

    return complete
