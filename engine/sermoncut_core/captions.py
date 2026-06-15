"""transcript 리소스 — 자막 확보 + 정규화 (P2-R2 / P1-R0-T1).

확보 우선순위(기획서): YouTube 자막(VTT) → 없으면 Whisper 전사 → import(SRT/VTT).
파서는 VTT/SRT 를 공통 세그먼트 [{start,end,text}] 로 정규화한다.
외부 의존성(자막 다운로드/Whisper)은 주입 가능.
"""
from __future__ import annotations

import re

from .io_utils import write_json

_TS = re.compile(r"(\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3}")


def _ts_to_seconds(ts: str) -> float:
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0.0, parts[0], parts[1]
    else:
        h, m, s = 0.0, 0.0, parts[0]
    return round(h * 3600 + m * 60 + s, 3)


def _parse_cues(text: str) -> list[dict]:
    """VTT/SRT 공통: 'start --> end' 줄 + 다음 텍스트 줄들을 세그먼트로."""
    segments: list[dict] = []
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if "-->" in line:
            left, right = line.split("-->")[0], line.split("-->")[1]
            try:
                start = _ts_to_seconds(_TS.search(left).group())
                end = _ts_to_seconds(_TS.search(right).group())
            except AttributeError:
                i += 1
                continue
            i += 1
            buf = []
            while i < len(lines) and lines[i].strip() and "-->" not in lines[i]:
                # SRT 인덱스 숫자만 있는 줄은 건너뜀
                if not lines[i].strip().isdigit():
                    buf.append(lines[i].strip())
                i += 1
            text_joined = " ".join(buf).strip()
            if text_joined:
                segments.append({"start": start, "end": end, "text": text_joined})
        else:
            i += 1
    return segments


def parse_vtt(text: str) -> list[dict]:
    return _parse_cues(text)


def parse_srt(text: str) -> list[dict]:
    return _parse_cues(text)


def _parse_caption_text(text: str) -> list[dict]:
    return _parse_cues(text)


def acquire_transcript(
    source: dict,
    *,
    method: str = "auto",
    subs_downloader=None,   # (url)->vtt_text|None
    whisper_fn=None,        # (video_path)->segments
    import_text: str | None = None,
    persist: bool = False,
) -> dict:
    """source → transcript dict {source_id, caption_source, segments}."""
    segments: list[dict]
    caption_source: str

    if method == "import":
        if import_text is None:
            raise ValueError("import 방식은 import_text 가 필요합니다")
        segments = _parse_caption_text(import_text)
        caption_source = "import"

    elif method == "whisper":
        if whisper_fn is None:
            raise ValueError("whisper 방식은 whisper_fn 이 필요합니다")
        segments = whisper_fn(source["video_path"])
        caption_source = "whisper"

    else:  # auto: youtube 자막 우선 → whisper 폴백
        vtt = None
        if source.get("type") == "youtube" and subs_downloader is not None:
            vtt = subs_downloader(source["url"])
        if vtt:
            segments = _parse_caption_text(vtt)
            caption_source = "youtube"
        elif whisper_fn is not None:
            segments = whisper_fn(source["video_path"])
            caption_source = "whisper"
        else:
            raise RuntimeError("자막 확보 실패: YouTube 자막 없음 + Whisper 미제공")

    transcript = {
        "source_id": source["id"],
        "caption_source": caption_source,
        "segments": segments,
    }
    if persist:
        write_json("transcript.json", transcript)
    return transcript
