"""Governed OpenAI Responses API adapter for VX.

The adapter is opt-in: callers must provide a model and explicitly pass an API key
(or configure OPENAI_API_KEY). It never reads credentials from task payloads.
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_TIMEOUT_SECONDS = 30.0


class OpenAIAdapterError(RuntimeError):
    """Sanitized provider/transport failure; never includes credentials."""


def _https_transport(
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout: float,
) -> Mapping[str, Any]:
    request = Request(url, data=body, headers=dict(headers), method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        # Do not include provider response bodies: they may contain sensitive data.
        raise OpenAIAdapterError(f"OPENAI_HTTP_ERROR:{exc.code}") from None
    except (URLError, TimeoutError, OSError) as exc:
        raise OpenAIAdapterError("OPENAI_TRANSPORT_ERROR") from None
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise OpenAIAdapterError("OPENAI_INVALID_JSON") from None
    if not isinstance(value, dict):
        raise OpenAIAdapterError("OPENAI_INVALID_RESPONSE")
    return value


def extract_output_text(response: Mapping[str, Any]) -> str:
    """Extract text from a Responses API result without inventing missing output."""
    direct = response.get("output_text")
    if isinstance(direct, str):
        return direct
    pieces: list[str] = []
    output = response.get("output", [])
    if not isinstance(output, list):
        raise OpenAIAdapterError("OPENAI_INVALID_OUTPUT")
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "output_text":
                text = block.get("text")
                if isinstance(text, str):
                    pieces.append(text)
    if not pieces:
        raise OpenAIAdapterError("OPENAI_NO_TEXT_OUTPUT")
    return "".join(pieces)


class OpenAIResponsesAdapter:
    """Small, auditable adapter; authorization must be enforced by VX before calling."""

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        transport: Callable[[str, Mapping[str, str], bytes, float], Mapping[str, Any]] | None = None,
    ) -> None:
        if not model or not model.strip():
            raise ValueError("OPENAI_MODEL_REQUIRED")
        if timeout <= 0:
            raise ValueError("TIMEOUT_MUST_BE_POSITIVE")
        self.model = model.strip()
        self._api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.timeout = timeout
        self._transport = transport or _https_transport

    def generate(self, prompt: str, *, instructions: str | None = None,
                 max_output_tokens: int = 512) -> dict[str, Any]:
        if not self._api_key:
            raise OpenAIAdapterError("OPENAI_API_KEY_MISSING")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("PROMPT_REQUIRED")
        if max_output_tokens < 1:
            raise ValueError("MAX_OUTPUT_TOKENS_MUST_BE_POSITIVE")

        payload: dict[str, Any] = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": max_output_tokens,
        }
        if instructions:
            payload["instructions"] = instructions
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        response = self._transport(
            RESPONSES_URL,
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            body,
            self.timeout,
        )
        if not isinstance(response, Mapping):
            raise OpenAIAdapterError("OPENAI_INVALID_RESPONSE")
        text = extract_output_text(response)
        # Keep a bounded, non-secret subset of provider metadata for evidence.
        metadata = {
            key: response[key]
            for key in ("id", "model", "status")
            if isinstance(response.get(key), (str, int, float, bool))
        }
        return {"text": text, "provider": "openai", "response": metadata}


def openai_worker(adapter: OpenAIResponsesAdapter) -> Callable[[Mapping[str, Any]], dict[str, Any]]:
    """Return a VX worker callable. VX policy must allow 'model.openai.responses'."""
    def worker(payload: Mapping[str, Any]) -> dict[str, Any]:
        return adapter.generate(
            str(payload.get("prompt", "")),
            instructions=payload.get("instructions"),
            max_output_tokens=int(payload.get("max_output_tokens", 512)),
        )
    return worker


__all__ = [
    "OpenAIAdapterError",
    "OpenAIResponsesAdapter",
    "extract_output_text",
    "openai_worker",
]
