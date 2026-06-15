from sermoncut_core.shorts import (
    body_segments,
    generate_candidates,
    validate_candidates,
)

ANALYSIS = {"sermon_start": 1500.0, "sermon_end": 4500.0,
            "benediction_start": 4800.0, "benediction_end": 4900.0}

TRANSCRIPT = {
    "source_id": "s", "caption_source": "youtube",
    "segments": [
        {"start": 1000.0, "end": 1005.0, "text": "광고(본문 전)"},
        {"start": 1600.0, "end": 1605.0, "text": "본문 도입"},
        {"start": 4490.0, "end": 4495.0, "text": "본문 마지막"},
        {"start": 4850.0, "end": 4855.0, "text": "축도(제외)"},
    ],
}


def _good_raw():
    cands = []
    for i in range(5):
        s = 1600.0 + i * 100
        cands.append({
            "id": f"cand_{i+1:03d}",
            "type": "후킹형",
            "start": s, "end": s + 25, "duration_sec": 25,
            "title": "t", "hook_line": "h", "highlight": "hi",
            "hashtags": ["#설교"], "reason": "r", "score": 80,
        })
    return {"summary": "요약", "keywords": ["은혜"],
            "candidates": cands,
            "selected_candidate_ids": ["cand_001", "cand_002", "cand_003"]}


def test_body_segments_excludes_outside_and_benediction():
    segs = body_segments(TRANSCRIPT, ANALYSIS)
    texts = [s["text"] for s in segs]
    assert "본문 도입" in texts and "본문 마지막" in texts
    assert "광고(본문 전)" not in texts
    assert "축도(제외)" not in texts


def test_generate_candidates_normalizes_and_validates():
    out = generate_candidates(TRANSCRIPT, ANALYSIS, gemini=lambda _s, _u: _good_raw())
    assert len(out["candidates"]) == 5
    assert out["_issues"] == []
    assert out["candidates"][0]["duration_sec"] == 25


def test_generate_candidates_converts_hms():
    raw = _good_raw()
    raw["candidates"][0]["start"] = "00:26:40"  # 1600
    raw["candidates"][0]["end"] = "00:27:05"    # 1625
    raw["candidates"][0]["duration_sec"] = None
    out = generate_candidates(TRANSCRIPT, ANALYSIS, gemini=lambda _s, _u: raw)
    assert out["candidates"][0]["start"] == 1600.0
    assert out["candidates"][0]["duration_sec"] == 25.0


def test_validate_flags_wrong_count():
    data = _good_raw()
    data["candidates"] = data["candidates"][:3]
    issues = validate_candidates(data)
    assert any("후보 개수" in i for i in issues)


def test_validate_flags_bad_length_and_overlap():
    data = _good_raw()
    data["candidates"][0]["duration_sec"] = 90  # 너무 김
    data["candidates"][1]["start"] = data["candidates"][0]["start"] + 5  # 겹침
    data["candidates"][1]["end"] = data["candidates"][0]["end"] + 5
    issues = validate_candidates(data)
    assert any("길이" in i for i in issues)
    assert any("겹침" in i for i in issues)


def test_validate_flags_selection_count():
    data = _good_raw()
    data["selected_candidate_ids"] = ["cand_001"]
    issues = validate_candidates(data)
    assert any("추천 선택" in i for i in issues)
