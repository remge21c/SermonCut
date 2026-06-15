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


# --- 일시적 서버 오류(503) 재시도 ---
from google.genai.errors import APIError


class _FakeServerError(APIError):
    def __init__(self, code):
        self.code = code
        self.message = "transient"


class _FlakyModels:
    """처음 n번은 503, 그 다음 성공"""
    def __init__(self, fail_times, text):
        self.fail_times = fail_times
        self.text = text
        self.calls = 0

    def generate_content(self, **_kwargs):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise _FakeServerError(503)
        return _FakeResp(self.text)


class _FlakyClient:
    def __init__(self, fail_times, text):
        self.models = _FlakyModels(fail_times, text)


def test_call_gemini_retries_on_503(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)  # 백오프 즉시 통과
    client = _FlakyClient(fail_times=2, text='{"ok": true}')
    out = call_gemini("sys", "user", retries=3, backoff=0, client=client)
    assert out == {"ok": True}
    assert client.models.calls == 3


def test_call_gemini_4xx_not_retried(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)
    client = _FlakyClient(fail_times=99, text="x")
    client.models.generate_content = lambda **_k: (_ for _ in ()).throw(_FakeServerError(400))
    with pytest.raises(APIError):
        call_gemini("sys", "user", retries=3, client=client)
