"""SermonCut 엔진 CLI 진입점.

호출 예: python -m sermoncut_core.cli ping --json '{}'
명령: ping | analyze | render
stdout으로 progress/result JSON 라인을 출력한다 (ipc.py 프로토콜).
"""
import argparse
import json

from . import __version__
from .ipc import emit_progress, emit_result, fail


def cmd_ping(_payload: dict) -> dict:
    emit_progress("ping", percent=100, message="engine alive")
    return {"ok": True, "version": __version__}


def cmd_analyze(payload: dict) -> dict:
    """입력 → source → transcript → sermon_analysis → shorts_candidate."""
    from . import adapters
    from .io_utils import input_dir
    from .source import build_source
    from .captions import acquire_transcript
    from .analysis import analyze_sermon
    from .shorts import generate_candidates

    spec = payload.get("input") or {}
    method = payload.get("caption_method", "auto")

    emit_progress("source", percent=5, message="영상 확보")

    def _dl(url):
        emit_progress("download", percent=5, message="유튜브 영상 다운로드 중")
        return adapters.download_youtube_video(
            url, str(input_dir()),
            progress_cb=lambda p: emit_progress("download", percent=p, message="영상 다운로드"),
        )

    source = build_source(spec, video_downloader=_dl, persist=True)

    emit_progress("transcript", percent=30, message="자막 확보")

    def _whisper(path):
        # 전사 진행률(0~100)을 전체 30~60% 구간으로 매핑
        return adapters.whisper_transcribe(
            path,
            model_size=payload.get("whisper_model"),
            progress_cb=lambda p: emit_progress(
                "transcript", percent=round(30 + p * 0.3, 1), message=f"음성 전사 중 {int(p)}%"
            ),
        )

    transcript = acquire_transcript(
        source,
        method=method,
        subs_downloader=adapters.download_youtube_subs,
        whisper_fn=_whisper,
        import_text=payload.get("import_text"),
        persist=True,
    )

    emit_progress("analysis", percent=60, message="설교 구간 분석")
    analysis = analyze_sermon(transcript, source.get("title", ""), persist=True)

    emit_progress("candidates", percent=85, message="쇼츠 후보 생성")
    candidates = generate_candidates(transcript, analysis, persist=True)

    emit_progress("done", percent=100)
    return {
        "source": source,
        "caption_source": transcript["caption_source"],
        "analysis": analysis,
        "candidates": candidates,
    }


def cmd_render(payload: dict) -> dict:
    """선택된 후보 → 세로 9:16 렌더 (자막 번인)."""
    from .render import render_short, write_clip_srt
    from .io_utils import candidates_dir, read_json, results_dir, write_json

    source = payload.get("source") or read_json(candidates_dir() / "source_info.json")
    transcript = payload.get("transcript") or read_json(candidates_dir() / "transcript.json")
    selected = payload["selected"]           # 후보 dict 리스트(정확히 3개)
    crop = payload.get("crop", "center")
    only = payload.get("only")               # 0-based 인덱스 목록(None=전체)
    input_video = source["video_path"]

    # 기존 결과(개별 재렌더 시 미대상 쇼츠 유지)
    existing = {}
    try:
        for r in read_json(results_dir() / "selected_shorts.json"):
            existing[r["id"]] = r
    except Exception:
        pass

    results = []
    for idx, cand in enumerate(selected):
        i = idx + 1
        short_id = f"short_{i:03d}"

        # 재렌더 대상이 아니고 기존 결과가 있으면 그대로 유지
        if only is not None and idx not in only and short_id in existing:
            results.append(existing[short_id])
            continue

        emit_progress(short_id, percent=0, message=f"{short_id} 렌더 시작")

        clip_segs = [s for s in transcript["segments"]
                     if s["end"] > cand["start"] and s["start"] < cand["end"]]
        srt = write_clip_srt(clip_segs, cand["start"], f"{short_id}.srt")

        job = {
            "id": short_id, "candidate_id": cand["id"],
            "title": cand.get("title", ""), "hook_line": cand.get("hook_line", ""),
            "highlight": cand.get("highlight", ""), "hashtags": cand.get("hashtags", []),
            "source_start": cand["start"], "source_end": cand["end"],
            "crop": crop, "subtitle_path": srt,
            "status": "pending", "progress": 0,
            "output_path": f"output/{short_id}.mp4",
        }

        def _cb(p, sid=short_id):
            emit_progress(sid, percent=p, message=f"{sid} 렌더 중")

        result = render_short(job, input_video, progress_cb=_cb)
        emit_progress(short_id, percent=100, message=f"{short_id} 완료")
        results.append(result)

    write_json(results_dir() / "selected_shorts.json", results)
    emit_progress("done", percent=100)
    return {"shorts": results}


COMMANDS = {"ping": cmd_ping, "analyze": cmd_analyze, "render": cmd_render}


def _load_env() -> None:
    """프로젝트 루트 .env 를 로드. .env 값이 시스템 환경변수보다 우선(override)."""
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        env_path = Path(__file__).resolve().parents[2] / ".env"
        load_dotenv(env_path, override=True)
    except Exception:
        pass  # dotenv 없거나 .env 없으면 시스템 환경변수 사용


def main() -> None:
    _load_env()
    parser = argparse.ArgumentParser(prog="sermoncut-core")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--json", default="{}", help="명령 페이로드(JSON 문자열)")
    args = parser.parse_args()

    try:
        payload = json.loads(args.json)
    except json.JSONDecodeError as e:
        fail(f"잘못된 --json 페이로드: {e}")

    # 프로젝트 디렉터리 지정 (analyze/render 에 필요, ping 은 생략 가능)
    project = payload.get("project")
    if project:
        from .io_utils import set_project
        set_project(project)

    result = COMMANDS[args.command](payload)
    emit_result(result)


if __name__ == "__main__":
    main()
