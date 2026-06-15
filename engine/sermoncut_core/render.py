"""shorts_render 리소스 — 세로 9:16 렌더 + 자막 번인 (P2-R5).

고정 기본 템플릿(기획서 §8.4): 1080x1920 / 30fps / mp4, 중앙(좌/우) 크롭,
자막 흰 글씨 + 검은 외곽선. FFmpeg 명령은 순수 함수로 빌드하여 단위테스트 가능.
"""
from __future__ import annotations

import os
import shutil
import subprocess

from .io_utils import output_dir, results_dir, write_json
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


def _sub_filter(subtitle_path: str) -> str:
    return f"subtitles='{_escape_sub_path(subtitle_path)}':force_style='{_SUB_STYLE}'"


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
    """쇼츠 1개 렌더용 ffmpeg argv 리스트 생성.

    crop: left/center/right(세로 크롭) · fit(전체+블러배경) · fit_black(전체+검은여백)
    """
    duration = round(end - start, 3)
    base = [ffmpeg, "-y", "-progress", "pipe:1", "-nostats",
            "-ss", f"{start:.3f}", "-i", input_video, "-t", f"{duration:.3f}"]
    enc = [
        "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
    ]

    if crop == "fit":
        # 가로 영상 전체를 세로 안에 넣고 위/아래는 확대·블러한 배경으로 채움
        graph = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={RES_W}:{RES_H}:force_original_aspect_ratio=increase,"
            f"crop={RES_W}:{RES_H},boxblur=20[bgb];"
            f"[fg]scale={RES_W}:-2[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2"
        )
        graph += f"[v];[v]{_sub_filter(subtitle_path)}[vout]" if subtitle_path else "[vout]"
        return base + ["-filter_complex", graph, "-map", "[vout]", "-map", "0:a?"] + enc + [output]

    if crop == "fit_black":
        vf = (f"scale={RES_W}:{RES_H}:force_original_aspect_ratio=decrease,"
              f"pad={RES_W}:{RES_H}:(ow-iw)/2:(oh-ih)/2:black")
    else:
        vf = crop_filter(crop)
    if subtitle_path:
        vf += "," + _sub_filter(subtitle_path)

    return base + ["-vf", vf] + enc + [output]


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
    path = output_dir() / name
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def _out_time_seconds(line: str):
    v = line.split("=", 1)[1].strip()
    if not v or v == "N/A":
        return None
    try:
        h, m, s = v.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except ValueError:
        return None


def _run_with_progress(cmd, duration, progress_cb) -> int:
    """ffmpeg -progress 출력을 파싱해 진행률(%)을 progress_cb로 전달."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    if proc.stdout:
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("out_time=") and duration > 0:
                sec = _out_time_seconds(line)
                if sec is not None and progress_cb:
                    progress_cb(min(99.0, round(sec / duration * 100, 1)))
            elif line.startswith("progress=") and line.endswith("end"):
                break
    proc.wait()
    return proc.returncode


def render_short(
    job: dict,
    input_video: str,
    *,
    runner=None,        # (argv)->returncode (주입용)
    ffmpeg: str = "ffmpeg",
    persist_name: str | None = None,
    progress_cb=None,   # (percent: float)->None 실시간 진행률
) -> dict:
    """단일 쇼츠 렌더. job: shorts_render 스키마. 결과 status/progress 갱신."""
    ff = shutil.which(ffmpeg) or ffmpeg
    out = output_dir() / (job["output_path"].split("/")[-1])
    cmd = build_ffmpeg_command(
        input_video, job["source_start"], job["source_end"], str(out),
        crop=job.get("crop", "center"),
        subtitle_path=job.get("subtitle_path"),
        ffmpeg=ff,
    )

    duration = float(job["source_end"]) - float(job["source_start"])
    if runner:
        code = runner(cmd)
    elif progress_cb:
        code = _run_with_progress(cmd, duration, progress_cb)
    else:
        code = subprocess.run(cmd).returncode

    job = dict(job)
    if code == 0:
        job["status"], job["progress"] = "done", 100
    else:
        job["status"], job["progress"] = "failed", 0
    job["output_path"] = str(out)   # 절대 경로(프로젝트 output/)

    if persist_name:
        write_json(results_dir() / persist_name, job)
    return job
