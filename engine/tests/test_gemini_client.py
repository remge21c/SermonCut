import pytest

from sermoncut_core.gemini_client import parse_json, call_gemini


def test_parse_json_with_fence():
    text = '```json\n{"a": 1, "b": [2, 3]}\n```'
    assert parse_json(text) == {"a": 1, "b": [2, 3]}


def test_parse_json_plain():
    assert parse_json('{"x": "값"}') == {"x": "값"}


def test_parse_json_with_surrounding_text():
    text = '설명입니다.\n{"ok": true}\n끝.'
    assert parse_json(text) == {"ok": True}


def test_parse_json_invalid():
    with pytest.raises(Exception):
        parse_json("not json at all")


class _FakeResp:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, texts):
        self._texts = list(texts)
        self.calls = 0

    def generate_content(self, **_kwargs):
        self.calls += 1
        return _FakeResp(self._texts.pop(0))


class _FakeClient:
    def __init__(self, texts):
        self.models = _FakeModels(texts)


def test_call_gemini_parses_first_success():
    client = _FakeClient(['{"result": 1}'])
    out = call_gemini("sys", "user", client=client)
    assert out == {"result": 1}
    assert client.models.calls == 1


def test_call_gemini_retries_then_succeeds():
    client = _FakeClient(["garbage", '{"ok": true}'])
    out = call_gemini("sys", "user", retries=2, client=client)
    assert out == {"ok": True}
    assert client.models.calls == 2


def test_call_gemini_exhausts_retries():
    client = _FakeClient(["bad", "bad", "bad"])
    with pytest.raises(ValueError):
        call_gemini("sys", "user", retries=2, client=client)
