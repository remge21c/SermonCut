import pytest

from sermoncut_core.captions import parse_vtt, parse_srt, acquire_transcript

VTT = """WEBVTT

00:00:01.000 --> 00:00:04.000
오늘 본문은 요한복음 6장입니다

00:00:04.500 --> 00:00:07.000
함께 읽겠습니다
"""

SRT = """1
00:00:01,000 --> 00:00:04,000
오늘 본문은 요한복음 6장입니다

2
00:00:04,500 --> 00:00:07,000
함께 읽겠습니다
"""


def test_parse_vtt():
    segs = parse_vtt(VTT)
    assert len(segs) == 2
    assert segs[0] == {"start": 1.0, "end": 4.0, "text": "오늘 본문은 요한복음 6장입니다"}
    assert segs[1]["start"] == 4.5


def test_parse_srt():
    segs = parse_srt(SRT)
    assert len(segs) == 2
    assert segs[0]["text"] == "오늘 본문은 요한복음 6장입니다"
    assert segs[1]["end"] == 7.0


def test_acquire_auto_prefers_youtube():
    source = {"id": "src_001", "type": "youtube", "url": "u", "video_path": "v.mp4"}
    out = acquire_transcript(
        source,
        method="auto",
        subs_downloader=lambda _u: VTT,
        whisper_fn=lambda _p: [{"start": 0, "end": 1, "text": "whisper"}],
    )
    assert out["caption_source"] == "youtube"
    assert len(out["segments"]) == 2


def test_acquire_auto_falls_back_to_whisper():
    source = {"id": "src_001", "type": "youtube", "url": "u", "video_path": "v.mp4"}
    out = acquire_transcript(
        source,
        method="auto",
        subs_downloader=lambda _u: None,   # 자막 없음
        whisper_fn=lambda _p: [{"start": 0.0, "end": 2.0, "text": "전사됨"}],
    )
    assert out["caption_source"] == "whisper"
    assert out["segments"][0]["text"] == "전사됨"


def test_acquire_import():
    source = {"id": "src_001", "type": "local", "video_path": "v.mp4"}
    out = acquire_transcript(source, method="import", import_text=SRT)
    assert out["caption_source"] == "import"
    assert len(out["segments"]) == 2


def test_acquire_auto_no_caption_no_whisper_raises():
    source = {"id": "s", "type": "youtube", "url": "u", "video_path": "v.mp4"}
    with pytest.raises(RuntimeError):
        acquire_transcript(source, method="auto", subs_downloader=lambda _u: None)
