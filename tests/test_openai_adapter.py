import json

import pytest

from vxruntime import ExecutionPolicy, ExecutionStatus, VXRuntime
from vxruntime.openai_adapter import (
    OpenAIAdapterError,
    OpenAIResponsesAdapter,
    RESPONSES_URL,
    extract_output_text,
    openai_worker,
)


def fake_transport(response):
    calls = []

    def transport(url, headers, body, timeout):
        calls.append((url, dict(headers), json.loads(body), timeout))
        return response

    return transport, calls


def test_responses_adapter_builds_request_and_extracts_output():
    transport, calls = fake_transport({
        "id": "resp_test", "model": "configured-model", "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": "hello VX"}]}],
    })
    adapter = OpenAIResponsesAdapter("configured-model", api_key="test-secret", transport=transport)
    result = adapter.generate("Say hello", instructions="Be concise", max_output_tokens=80)
    assert result["text"] == "hello VX"
    assert result["provider"] == "openai"
    assert result["response"]["id"] == "resp_test"
    assert calls[0][0] == RESPONSES_URL
    assert calls[0][1]["Authorization"] == "Bearer test-secret"
    assert calls[0][2]["model"] == "configured-model"
    assert calls[0][2]["instructions"] == "Be concise"
    assert calls[0][3] > 0


def test_direct_output_text_supported():
    assert extract_output_text({"output_text": "direct"}) == "direct"


def test_missing_key_fails_closed():
    adapter = OpenAIResponsesAdapter("configured-model", api_key="", transport=lambda *_: pytest.fail("network called"))
    with pytest.raises(OpenAIAdapterError, match="OPENAI_API_KEY_MISSING"):
        adapter.generate("hello")


def test_empty_prompt_and_invalid_limits_rejected():
    adapter = OpenAIResponsesAdapter("configured-model", api_key="secret", transport=lambda *_: {})
    with pytest.raises(ValueError, match="PROMPT_REQUIRED"):
        adapter.generate("  ")
    with pytest.raises(ValueError, match="MAX_OUTPUT_TOKENS_MUST_BE_POSITIVE"):
        adapter.generate("hello", max_output_tokens=0)


def test_no_text_output_rejected():
    with pytest.raises(OpenAIAdapterError, match="OPENAI_NO_TEXT_OUTPUT"):
        extract_output_text({"output": []})


def test_vx_policy_blocks_model_call_before_provider_transport():
    transport, calls = fake_transport({"output_text": "must not happen"})
    adapter = OpenAIResponsesAdapter("configured-model", api_key="secret", transport=transport)
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"math.add"})))
    result = runtime.execute(
        "openai-blocked-001",
        "model.openai.responses",
        {"prompt": "hello"},
        openai_worker(adapter),
    )
    assert result.status is ExecutionStatus.BLOCKED
    assert calls == []
    assert runtime.verify()


def test_authorized_vx_execution_records_provider_result_and_replay_evidence():
    transport, calls = fake_transport({"id": "resp_ok", "output_text": "approved call"})
    adapter = OpenAIResponsesAdapter("configured-model", api_key="secret", transport=transport)
    runtime = VXRuntime(policy=ExecutionPolicy(
        allowed_capabilities=frozenset({"model.openai.responses"})
    ))
    result = runtime.execute(
        "openai-allowed-001",
        "model.openai.responses",
        {"prompt": "hello", "max_output_tokens": 40},
        openai_worker(adapter),
    )
    assert result.status is ExecutionStatus.SUCCESS
    assert result.output["text"] == "approved call"
    assert result.event_hash
    assert runtime.verify()
    assert len(calls) == 1
