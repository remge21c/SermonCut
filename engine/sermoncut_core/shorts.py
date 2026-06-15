"""shorts_candidate 리소스 — 쇼츠 후보 5개 생성 + 검증 (P2-R4).

입력 범위: 설교 본문(sermon_start~sermon_end), 축도 제외.
쇼츠규칙.md 를 system instruction 으로 Gemini 호출 → 후보 5개 + 추천 3개.
"HH:MM:SS" → 초 변환, 개수/길이/겹침/선택수 검증.
"""
from __future__ import annotations

from .gemini_client import call_gemini
from .io_utils import read_rule, write_json
from .timecode import hms, to_seconds

CANDIDATE_COUNT = 5
SELECTED_COUNT = 3
DUR_MIN = 15
DUR_MAX = 40


def body_segments(transcript: dict, analysis: dict) -> list[dict]:
    """설교 본문 구간 내 세그먼트만 추출 (축도 제외)."""
    start = analysis.get("sermon_start") or 0
    end = analysis.get("sermon_end")
    out = []
    for seg in transcript["segments"]:
        if seg["start"] >= start and (end is None or seg["end"] <= end):
            out.append(seg)
    return out


def _coerce_seconds(value):
    if isinstance(value, (int, float)):
        return float(value)
    return to_seconds(str(value))


def _normalize_candidates(raw: dict) -> dict:
    data = dict(raw)
    cands = []
    for i, c in enumerate(raw.get("candidates", []), start=1):
        c = dict(c)
        c.setdefault("id", f"cand_{i:03d}")
        c["start"] = _coerce_seconds(c["start"])
        c["end"] = _coerce_seconds(c["end"])
        c["duration_sec"] = round(c.get("duration_sec") or (c["end"] - c["start"]), 1)
        cands.append(c)
    data["candidates"] = cands
    data.setdefault("selected_candidate_ids", [])
    data.setdefault("summary", "")
    data.setdefault("keywords", [])
    return data


def validate_candidates(data: dict) -> list[str]:
    """규칙 위반 사항을 문자열 리스트로 반환 (빈 리스트 = 통과)."""
    issues: list[str] = []
    cands = data.get("candidates", [])

    if len(cands) != CANDIDATE_COUNT:
        issues.append(f"후보 개수 {len(cands)} (기대 {CANDIDATE_COUNT})")

    for c in cands:
        dur = c.get("duration_sec", 0)
        if not (DUR_MIN <= dur <= DUR_MAX):
            issues.append(f"{c.get('id')} 길이 {dur}s (허용 {DUR_MIN}~{DUR_MAX})")

    # 구간 겹침 검사
    ordered = sorted(cands, key=lambda c: c.get("start", 0))
    for a, b in zip(ordered, ordered[1:]):
        if a.get("end", 0) > b.get("start", 0):
            issues.append(f"구간 겹침: {a.get('id')} ↔ {b.get('id')}")

    sel = data.get("selected_candidate_ids", [])
    if len(sel) != SELECTED_COUNT:
        issues.append(f"추천 선택 {len(sel)}개 (기대 {SELECTED_COUNT})")
    ids = {c.get("id") for c in cands}
    for s in sel:
        if s not in ids:
            issues.append(f"선택 id {s} 가 후보에 없음")

    return issues


def generate_candidates(
    transcript: dict,
    analysis: dict,
    *,
    gemini=None,
    persist: bool = False,
) -> dict:
    rule = read_rule("쇼츠규칙.md")
    segs = body_segments(transcript, analysis)
    user_content = "\n".join(f"[{hms(s['start'])}] {s['text']}" for s in segs)

    caller = gemini or (lambda sys_p, usr: call_gemini(sys_p, usr))
    raw = caller(rule, user_content)

    data = _normalize_candidates(raw)
    data["_issues"] = validate_candidates(data)

    if persist:
        write_json("shorts_candidates.json", data)
    return data
