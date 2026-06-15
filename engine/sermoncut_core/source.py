"""source 리소스 — 입력 처리 (P2-R1).

youtube_url | local_mp4 → source_info.json
- youtube: yt-dlp로 메타데이터(title/duration/id) 확보
- local: 파일 검증 + ffprobe 길이
의존성(yt-dlp/ffprobe)은 주입 가능하게 하여 단위테스트에서 모킹한다.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .io_utils import write_json


def _youtube_info(url: str) -> dict:
    import yt_dlp

    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        return ydl.extract_info(url, download=False)


def _probe_duration(path: str) -> float | None:
    ffprobe = shutil.which("ffprobe") or "ffprobe"
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except (FileNotFoundError, ValueError, subprocess.SubprocessError):
        return None


def build_source(
    spec: dict,
    *,
    source_id: str = "src_001",
    ydl_info=None,
    probe_duration=None,
    persist: bool = False,
) -> dict:
    """입력 spec → source dict (resources.source 스키마)."""
    stype = spec.get("type")

    if stype == "youtube":
        url = spec["url"]
        info_fn = ydl_info or _youtube_info   # 주입 가능한 (url)->dict
        info = info_fn(url)
        source = {
            "id": source_id,
            "type": "youtube",
            "url": url,
            "video_path": info.get("filepath") or info.get("_filename") or "",
            "title": info.get("title", ""),
            "duration_sec": float(info.get("duration") or 0),
        }
    elif stype == "local":
        path = spec["path"]
        if not Path(path).is_file():
            raise FileNotFoundError(f"영상 파일 없음: {path}")
        dur_fn = probe_duration or _probe_duration
        source = {
            "id": source_id,
            "type": "local",
            "url": None,
            "video_path": os.path.abspath(path),
            "title": Path(path).stem,
            "duration_sec": float(dur_fn(path) or 0),
        }
    else:
        raise ValueError(f"알 수 없는 입력 type: {stype!r}")

    if persist:
        write_json("source_info.json", source)
    return source
