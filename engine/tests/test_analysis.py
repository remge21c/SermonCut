from sermoncut_core.analysis import analyze_sermon, transcript_to_prompt

TRANSCRIPT = {
    "source_id": "src_001",
    "caption_source": "youtube",
    "segments": [
        {"start": 1536.0, "end": 1539.0, "text": "오늘 본문은 요한복음 6장입니다"},
        {"start": 4500.0, "end": 4505.0, "text": "예수 그리스도 이름으로 기도합니다"},
    ],
}


def test_transcript_to_prompt_uses_hms():
    out = transcript_to_prompt(TRANSCRIPT, "2부 예배")
    assert "제목: 2부 예배" in out
    assert "[00:25:36] 오늘 본문은" in out


def test_analyze_converts_hms_to_seconds():
    fake = lambda _sys, _usr: {
        "part": "2부",
        "sermon_start": "00:25:36",
        "sermon_end": "01:15:00",
        "start_reason": "본문 멘트",
        "end_reason": "마무리 기도 후 찬송",
        "benediction_start": "01:18:10",
        "benediction_end": "01:20:05",
        "summary": "요약",
        "keywords": ["은혜", "믿음"],
    }
    out = analyze_sermon(TRANSCRIPT, "2부", gemini=fake)
    assert out["sermon_start"] == 1536.0
    assert out["sermon_end"] == 4500.0
    assert out["benediction_start"] == 4690.0
    assert out["part"] == "2부"
    assert out["keywords"] == ["은혜", "믿음"]


def test_analyze_handles_null_benediction():
    fake = lambda _sys, _usr: {
        "part": "1부",
        "sermon_start": "00:10:00",
        "sermon_end": "00:50:00",
        "benediction_start": None,
        "benediction_end": None,
        "summary": "s",
        "keywords": [],
    }
    out = analyze_sermon(TRANSCRIPT, gemini=fake)
    assert out["benediction_start"] is None
    assert out["benediction_end"] is None


def test_analyze_accepts_numeric_seconds():
    fake = lambda _sys, _usr: {
        "part": "수요예배",
        "sermon_start": 600.0,
        "sermon_end": 3000.0,
        "summary": "s",
        "keywords": ["기도"],
    }
    out = analyze_sermon(TRANSCRIPT, gemini=fake)
    assert out["sermon_start"] == 600.0
    assert out["benediction_start"] is None  # 누락 → None
