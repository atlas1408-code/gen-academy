"""Malformed-JSON handling: repaired or degraded, never crashes."""
from app.tools.json_repair import call_agent_with_repair, extract_json


class _Resp:
    def __init__(self, content):
        self.content = content
        self.usage_metadata = {"input_tokens": 3, "output_tokens": 4}


class _ScriptedLLM:
    """Returns scripted replies in order; repeats the last one."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def invoke(self, _messages):
        reply = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return _Resp(reply)


class _RaisingLLM:
    def invoke(self, _messages):
        raise RuntimeError("simulated model/network failure")


# --- extract_json ---------------------------------------------------------

def test_extract_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_fenced_json():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_amid_prose():
    assert extract_json('Sure, here you go: {"a": 1} — hope that helps!') == {"a": 1}


def test_extract_returns_none_for_garbage():
    assert extract_json("no json at all") is None
    assert extract_json("") is None


# --- call_agent_with_repair ----------------------------------------------

def test_valid_on_first_try():
    llm = _ScriptedLLM(['{"findings": []}'])
    res = call_agent_with_repair(llm, "p", "quality", max_retries=2)
    assert res.ok and res.data == {"findings": []}
    assert res.attempts == 1
    assert res.prompt_tokens == 3 and res.completion_tokens == 4


def test_repaired_after_one_bad_attempt():
    llm = _ScriptedLLM(["not json", '{"findings": [{"x": 1}]}'])
    res = call_agent_with_repair(llm, "p", "security", max_retries=2)
    assert res.ok and res.attempts == 2
    assert res.prompt_tokens == 6  # accumulated across two calls


def test_degrades_when_never_parseable():
    llm = _ScriptedLLM(["never json"])
    res = call_agent_with_repair(llm, "p", "test_gap", max_retries=2)
    assert not res.ok and res.data is None
    assert res.attempts == 3            # initial + 2 retries
    assert res.errors                    # recorded, but did not raise


def test_model_exception_degrades_not_crashes():
    res = call_agent_with_repair(_RaisingLLM(), "p", "quality", max_retries=2)
    assert not res.ok and res.data is None
    assert any("invoke error" in e for e in res.errors)
