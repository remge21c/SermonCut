import pytest

from sermoncut_core.source import build_source


def test_local_source(tmp_path):
    f = tmp_path / "sermon.mp4"
    f.write_bytes(b"\x00")  # 더미 파일
    src = build_source(
        {"type": "local", "path": str(f)},
        probe_duration=lambda _p: 5400.0,
    )
    assert src["type"] == "local"
    assert src["title"] == "sermon"
    assert src["duration_sec"] == 5400.0
    assert src["url"] is None
    assert src["video_path"].endswith("sermon.mp4")


def test_local_source_missing_file():
    with pytest.raises(FileNotFoundError):
        build_source({"type": "local", "path": "no_such_file.mp4"})


def test_youtube_source_metadata():
    fake_info = lambda _url: {
        "title": "2026년 주일예배 2부",
        "duration": 5400,
        "_filename": "cache/source.mp4",
    }
    src = build_source(
        {"type": "youtube", "url": "https://youtu.be/abc"},
        ydl_info=fake_info,
    )
    assert src["type"] == "youtube"
    assert src["title"] == "2026년 주일예배 2부"
    assert src["duration_sec"] == 5400.0
    assert src["url"] == "https://youtu.be/abc"


def test_unknown_type():
    with pytest.raises(ValueError):
        build_source({"type": "vimeo", "url": "x"})
