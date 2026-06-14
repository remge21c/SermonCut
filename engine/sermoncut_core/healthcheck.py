"""외부 의존성 헬스체크 (P0-T0.2).

ffmpeg / yt-dlp / whisper(faster-whisper) / gemini 키 가용성을 확인한다.
실행: python -m sermoncut_core.healthcheck
"""
import os
import shutil
import subprocess

from dotenv import load_dotenv


def _bin_version(name: str, args: list[str]) -> str | None:
    path = shutil.which(name) or name
    try:
        out = subprocess.run([path, *args], capture_output=True, text=True, timeout=15)
        first = (out.stdout or out.stderr).splitlines()[0] if (out.stdout or out.stderr) else ""
        return first.strip() or "ok"
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def check() -> dict:
    # .env 는 프로젝트 루트(engine 상위)에 위치
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

    results: dict[str, object] = {}

    ffmpeg = os.environ.get("FFMPEG_PATH", "ffmpeg")
    results["ffmpeg"] = _bin_version(ffmpeg, ["-version"])

    ytdlp = os.environ.get("YTDLP_PATH", "yt-dlp")
    results["yt_dlp"] = _bin_version(ytdlp, ["--version"])

    try:
        import faster_whisper  # noqa: F401
        results["whisper"] = "faster-whisper installed"
    except ImportError:
        results["whisper"] = None

    try:
        from google import genai  # noqa: F401
        results["gemini_sdk"] = "google-genai installed"
    except ImportError:
        results["gemini_sdk"] = None

    results["gemini_key"] = bool(os.environ.get("GEMINI_API_KEY"))

    return results


def main() -> None:
    results = check()
    print("SermonCut 엔진 헬스체크")
    print("-" * 40)
    for k, v in results.items():
        mark = "OK " if v else "-- "
        print(f"[{mark}] {k}: {v}")
    # 필수: ffmpeg + yt-dlp (Gemini 키는 분석 단계에서만 필요)
    essential = results["ffmpeg"] and results["yt_dlp"]
    print("-" * 40)
    print("essential(ffmpeg+yt-dlp):", "READY" if essential else "MISSING")


if __name__ == "__main__":
    main()
