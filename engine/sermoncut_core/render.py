"""shorts_render 리소스 — 세로 9:16 렌더 + 자막 번인 (P2-R5).

고정 기본 템플릿(기획서 §8.4): 1080x1920 / 30fps / mp4, 중앙(좌/우) 크롭,
자막 흰 글씨 + 검은 외곽선. FFmpeg 명령은 순수 함수로 빌드하여 단위테스트 가능.
"""
from __future__ import annotations

import os
import shutil
import subprocess

from .io_utils import output_path, write_json
from .timecode import hms

RES_W, RES_H = 1080, 1920
FPS = 30

# 9:16 크롭 x 오프셋 (소스 높이 기준 폭 = ih*9/16)
_CROP_X = {
    "center": "(iw-ih*9/16)/2",
    "left": "0",
    "right": "iw-ih*9/16",
}

# 자막 스타일: 흰 글씨 + 검은 외곽선, 하단 중앙
_SUB_STYLE = (
    "FontName=Malgun Gothic,FontSize=18,"
    "PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,"
    "BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=120"
)


def crop_filter(crop: str = "center") -> str:
    if crop not in _CROP_X:
        raise ValueError(f"알 수 없는 crop: {crop}")
    return f"crop=ih*9/16:ih:{_CROP_X[crop]}:0,scale={RES_W}:{RES_H}"


def _escape_sub_path(path: str) -> str:
    # ffmpeg subtitles 필터는 Windows 경로의 ':' 와 '\' 이스케이프 필요
    return path.replace("\\", "/").replace(":", "\\:")


def build_ffmpeg_command(
    input_video: str,
    start: float,
    end: float,
    output: str,
    *,
    crop: str = "center",
    subtitle_path: str | None = None,
    ffmpeg: str = "ffmpeg",
) -> list[str]:
    """쇼츠 1개 렌더용 ffmpeg argv 리스트 생성."""
    duration = round(end - start, 3)
    vf = crop_filter(crop)
    if subtitle_path:
        vf += f",subtitles='{_escape_sub_path(subtitle_path)}':force_style='{_SUB_STYLE}'"

    return [
        ffmpeg, "-y",
        "-ss", f"{start:.3f}",
        "-i", input_video,
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        output,
    ]


def write_clip_srt(segments: list[dict], clip_start: float, name: str) -> str:
    """클립 구간 자막을 클립 기준(0초 시작) SRT 파일로 저장하고 경로 반환."""
    def srt_ts(t: float) -> str:
        ms = int(round((t - int(t)) * 1000))
        return hms(int(t)).replace(".", ",") + f",{ms:03d}"

    lines = []
    idx = 1
    for seg in segments:
        rs, re = seg["start"] - clip_start, seg["end"] - clip_start
        if re <= 0:
            continue
        rs = max(rs, 0)
        lines += [str(idx), f"{srt_ts(rs)} --> {srt_ts(re)}", seg["text"], ""]
        idx += 1
    path = output_path(name)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def render_short(
    job: dict,
    input_video: str,
    *,
    runner=None,        # (argv)->returncode (주입용)
    ffmpeg: str = "ffmpeg",
    persist_name: str | None = None,
) -> dict:
    """단일 쇼츠 렌더. job: shorts_render 스키마. 결과 status/progress 갱신."""
    ff = shutil.which(ffmpeg) or ffmpeg
    out = output_path(job["output_path"].split("/")[-1])
    cmd = build_ffmpeg_command(
        input_video, job["source_start"], job["source_end"], str(out),
        crop=job.get("crop", "center"),
        subtitle_path=job.get("subtitle_path"),
        ffmpeg=ff,
    )

    run = runner or (lambda argv: subprocess.run(argv).returncode)
    code = run(cmd)

    job = dict(job)
    if code == 0:
        job["status"], job["progress"] = "done", 100
    else:
        job["status"], job["progress"] = "failed", 0
    job["output_path"] = f"output/{out.name}"

    if persist_name:
        write_json(persist_name, job)
    return job
