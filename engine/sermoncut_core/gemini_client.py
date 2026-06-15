"""Gemini 호출 + JSON 파싱 (P1-R0-T2).

기존 sermon_finder.py의 call_gemini / parse_json 역할.
- 규칙 문서(설교규칙/쇼츠규칙)를 system instruction으로 주입
- 응답에서 JSON만 추출/파싱, 실패 시 재시도
SDK: google-genai (google.genai)
"""
from __future__ import annotations

import json
import os
import re

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def parse_json(text: str):
    """모델 응답 문자열에서 JSON 객체를 추출/파싱한다.

    - ```json ... ``` 코드펜스 제거
    - 펜스가 없으면 첫 '{' ~ 마지막 '}' 구간 사용
    """
    if text is None:
        raise ValueError("빈 응답")
    candidate = text.strip()

    m = _FENCE_RE.search(candidate)
    if m:
        candidate = m.group(1).strip()
    else:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = candidate[start : end + 1]

    return json.loads(candidate)


def _build_client():
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 미설정")
    return genai.Client(api_key=api_key)


def call_gemini(
    system_prompt: str,
    user_content: str,
    *,
    model: str = DEFAULT_MODEL,
    retries: int = 2,
    client=None,
) -> dict:
    """Gemini 호출 후 JSON dict 반환. 파싱 실패 시 retries 만큼 재시도."""
    from google.genai import types

    client = client or _build_client()
    last_err: Exception | None = None

    for _ in range(retries + 1):
        resp = client.models.generate_content(
            model=model,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
            ),
        )
        try:
            return parse_json(resp.text)
        except (ValueError, json.JSONDecodeError) as e:
            last_err = e

    raise ValueError(f"Gemini JSON 파싱 실패: {last_err}")
