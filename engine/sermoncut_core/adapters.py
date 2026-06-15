"""실제 외부 의존 어댑터 (E2E 전용, 단위테스트 대상 아님).

- download_youtube_subs: yt-dlp 로 YouTube 자막(VTT) 텍스트 확보
- whisper_transcribe: faster-whisper 로 로컬 전사 → 세그먼트
captions.acquire_transcript 에 주입된다.
"""
from __future__ import annotations

import glob
import os
import tempfile


def download_youtube_subs(url: str, lang: str = "ko") -> str | None:
    """YouTube 수동/자동 자막을 VTT 텍스트로 반환. 없으면 None."""
    import yt_dlp

    with tempfile.TemporaryDirectory() as tmp:
        opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [lang],
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
            "quiet": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception:
            return None
        files = glob.glob(os.path.join(tmp, "*.vtt"))
        if not files:
            return None
        with open(files[0], encoding="utf-8") as f:
            return f.read()


def whisper_transcribe(video_path: str, model_size: str | None = None) -> list[dict]:
    """faster-whisper 전사 → [{start,end,text}]."""
    from faster_whisper import WhisperModel

    model_size = model_size or os.environ.get("WHISPER_MODEL", "base")
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _info = model.transcribe(video_path, language="ko")
    return [
        {"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip()}
        for s in segments
    ]
