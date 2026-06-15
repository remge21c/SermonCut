"""sermon_analysis 리소스 — 설교 구간/요약 분석 (P2-R3).

설교규칙.md 를 system instruction 으로 Gemini 호출 → 시작/끝/축도 + 요약/키워드.
AI 출력 "HH:MM:SS" → 초(float) 변환 후 저장 (resources.sermon_analysis 스키마).
"""
from __future__ import annotations

from .gemini_client import call_gemini
from .io_utils import read_rule, write_json
from .timecode import hms, to_seconds

_TIME_KEYS = ("sermon_start", "sermon_end", "benediction_start", "benediction_end")


def transcript_to_prompt(transcript: dict, title: str = "") -> str:
    """transcript 세그먼트를 '[HH:MM:SS] text' 라인으로 직렬화."""
    lines = [f"제목: {title}"] if title else []
    for seg in transcript["segments"]:
        lines.append(f"[{hms(seg['start'])}] {seg['text']}")
    return "\n".join(lines)


def _coerce_seconds(value):
    """AI가 'HH:MM:SS' 또는 숫자/None 으로 줄 수 있으니 모두 초(float)로."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return to_seconds(str(value))


def analyze_sermon(
    transcript: dict,
    title: str = "",
    *,
    gemini=None,        # (system_prompt, user_content)->dict (주입용)
    persist: bool = False,
) -> dict:
    rule = read_rule("설교규칙.md")
    user_content = transcript_to_prompt(transcript, title)

    caller = gemini or (lambda sys_p, usr: call_gemini(sys_p, usr))
    raw = caller(rule, user_content)

    analysis = dict(raw)
    for key in _TIME_KEYS:
        analysis[key] = _coerce_seconds(raw.get(key))

    # 스키마 보정: 누락 키 기본값
    analysis.setdefault("part", "미상")
    analysis.setdefault("summary", "")
    analysis.setdefault("keywords", [])

    if persist:
        write_json("sermon_analysis.json", analysis)
    return analysis
