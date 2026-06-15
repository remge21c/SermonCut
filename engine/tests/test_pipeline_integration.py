"""P4 헤드리스 파이프라인 통합테스트.

cmd_analyze / cmd_render 의 모듈 배선을 mock 주입으로 end-to-end 검증한다.
(네트워크/Gemini/ffmpeg 실제 호출 없음 — 어댑터·Gemini·subprocess 를 patch)
"""
import json

import pytest

from sermoncut_core import cli, io_utils, source as source_mod, render as render_mod
from sermoncut_core import analysis as analysis_mod, shorts as shorts_mod

VTT = """WEBVTT

00:25:36.000 --> 00:25:40.000
오늘 본문은 요한복음 6장입니다

00:30:00.000 --> 00:30:05.000
정말 끝이라고 생각한 적 있습니까

01:15:00.000 --> 01:15:05.000
예수 그리스도 이름으로 기도합니다
"""

ANALYSIS_JSON = {
    "part": "2부",
    "sermon_start": "00:25:36",
    "sermon_end": "01:15:05",
    "start_reason": "본문 멘트",
    "end_reason": "마무리 기도 후 찬송",
    "benediction_start": None,
    "benediction_end": None,
    "summary": "은혜에 관한 설교",
    "keywords": ["은혜", "믿음", "기도"],
}


def _candidates_json():
    cands = []
    for i in range(5):
        s = 1600.0 + i * 120
        cands.append({
            "id": f"cand_{i+1:03d}", "type": "후킹형",
            "start": s, "end": s + 25, "duration_sec": 25,
            "title": f"제목{i+1}", "hook_line": "정말 끝이라고 생각했습니까",
            "highlight": "끝이 아니라 시작입니다", "hashtags": ["#설교"],
            "reason": "도입 질문", "score": 90 - i,
        })
    return {"summary": "은혜에 관한 설교", "keywords": ["은혜", "믿음"],
            "candidates": cands,
            "selected_candidate_ids": ["cand_001", "cand_002", "cand_003"]}


def _fake_gemini(system_prompt, _user):
    # system_prompt 로 어느 규칙인지 구분
    if "쇼츠" in system_prompt:
        return _candidates_json()
    return ANALYSIS_JSON


@pytest.fixture
def project(tmp_path):
    io_utils.set_project(tmp_path)
    return tmp_path


def test_analyze_pipeline_end_to_end(project, monkeypatch):
    # 어댑터(자막) + Gemini patch
    monkeypatch.setattr(source_mod, "_youtube_info",
                        lambda url: {"title": "2026 주일 2부", "duration": 5400, "id": "abc"})
    monkeypatch.setattr("sermoncut_core.adapters.download_youtube_video",
                        lambda url, dest, progress_cb=None: "cache/abc.mp4")
    monkeypatch.setattr("sermoncut_core.adapters.download_youtube_subs", lambda url, lang="ko": VTT)
    monkeypatch.setattr(analysis_mod, "call_gemini", _fake_gemini)
    monkeypatch.setattr(shorts_mod, "call_gemini", _fake_gemini)

    result = cli.cmd_analyze({
        "input": {"type": "youtube", "url": "https://youtu.be/abc"},
        "caption_method": "auto",
    })

    # 반환 구조
    assert result["source"]["video_path"] == "cache/abc.mp4"
    assert result["caption_source"] == "youtube"
    assert result["analysis"]["sermon_start"] == 1536.0
    assert len(result["candidates"]["candidates"]) == 5
    assert result["candidates"]["_issues"] == []

    # 산출 파일은 candidates/ 하위에 생성
    cand = project / "candidates"
    for name in ("source_info.json", "transcript.json",
                 "sermon_analysis.json", "shorts_candidates.json"):
        assert (cand / name).exists(), name

    saved = json.loads((cand / "sermon_analysis.json").read_text(encoding="utf-8"))
    assert saved["part"] == "2부"
    assert saved["benediction_start"] is None


def test_render_pipeline_end_to_end(project, monkeypatch):
    # ffmpeg 실제 실행 대신 subprocess.run patch
    class _OK:
        returncode = 0
    monkeypatch.setattr(render_mod.subprocess, "run", lambda *a, **k: _OK())

    source = {"id": "src_001", "type": "youtube", "url": "u",
              "video_path": "in.mp4", "title": "t", "duration_sec": 5400}
    transcript = {"source_id": "src_001", "caption_source": "youtube",
                  "segments": [{"start": 1600.0, "end": 1605.0, "text": "한 토막"}]}
    selected = _candidates_json()["candidates"][:3]

    result = cli.cmd_render({
        "source": source, "transcript": transcript,
        "selected": selected, "crop": "center",
    })

    assert len(result["shorts"]) == 3
    assert all(s["status"] == "done" for s in result["shorts"])
    # 결과 메타는 results/, MP4·SRT는 output/
    assert (project / "results" / "selected_shorts.json").exists()
    assert (project / "output" / "short_001.srt").exists()
    assert result["shorts"][0]["output_path"].endswith("short_001.mp4")
