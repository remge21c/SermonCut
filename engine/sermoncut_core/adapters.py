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


def download_youtube_video(url: str, dest_dir: str, progress_cb=None) -> str:
    """YouTube 영상을 mp4(h264/aac)로 다운로드하고 경로 반환. 캐시 재사용.

    - curl_cffi 위장(impersonate)으로 403 회피
    - 같은 영상 id 파일이 이미 있으면 재다운로드 안 함
    """
    import os
    import glob
    import yt_dlp

    # 캐시 확인 (id 기반)
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    vid = info.get("id", "video")
    existing = glob.glob(os.path.join(dest_dir, f"{vid}.*"))
    existing = [p for p in existing if not p.endswith((".part", ".vtt", ".srt"))]
    if existing:
        return existing[0]

    def _hook(d):
        if progress_cb and d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            if total:
                progress_cb(round(done / total * 100, 1))

    opts = {
        "format": "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(dest_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "noprogress": True,
        "progress_hooks": [_hook],
    }
    # curl_cffi 위장(impersonate): API는 ImpersonateTarget 객체를 요구.
    # 백엔드가 없으면 위장 없이 진행(폴백).
    try:
        from yt_dlp.networking.impersonate import ImpersonateTarget
        opts["impersonate"] = ImpersonateTarget("chrome")
    except Exception:
        pass

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    out = glob.glob(os.path.join(dest_dir, f"{vid}.*"))
    out = [p for p in out if p.endswith(".mp4")] or out
    if not out:
        raise RuntimeError("영상 다운로드 실패")
    return out[0]


def whisper_transcribe(
    video_path: str, model_size: str | None = None, progress_cb=None
) -> list[dict]:
    """faster-whisper 전사 → [{start,end,text}].

    기본 CPU(int8) — GPU(CUDA) 라이브러리가 없어도 항상 동작.
    WHISPER_DEVICE=cuda 로 GPU 사용 가능하며, 실패 시 CPU로 자동 폴백.
    속도: VAD(무음 건너뜀) + beam_size=1 + 멀티코어. progress_cb(percent) 로 진행률 전달.
    """
    import os
    from faster_whisper import WhisperModel

    model_size = model_size or os.environ.get("WHISPER_MODEL", "base")
    device = os.environ.get("WHISPER_DEVICE", "cpu")
    compute = os.environ.get("WHISPER_COMPUTE", "int8")
    threads = int(os.environ.get("WHISPER_THREADS", os.cpu_count() or 4))

    def _run(dev: str, ct: str) -> list[dict]:
        model = WhisperModel(model_size, device=dev, compute_type=ct, cpu_threads=threads)
        segments, info = model.transcribe(
            video_path,
            language="ko",
            beam_size=1,            # greedy → 빠름
            vad_filter=True,        # 무음 구간 건너뜀 → 가속
        )
        total = getattr(info, "duration", 0) or 0
        out = []
        for s in segments:
            out.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip()})
            if progress_cb and total:
                # 전사된 위치(초)와 전체 길이(초)를 전달 → 호출측에서 시간 표시
                progress_cb(round(s.end, 1), round(total, 1))
        return out

    try:
        return _run(device, compute)
    except Exception:
        if device != "cpu":
            return _run("cpu", "int8")   # GPU 실패 → CPU 폴백
        raise
