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


def cmd_analyze(_payload: dict) -> dict:
    # TODO(P2-R1~R4): source → transcript → sermon_analysis → shorts_candidate
    fail("analyze 미구현 (P2-R1~R4 태스크에서 구현)")


def cmd_render(_payload: dict) -> dict:
    # TODO(P2-R5): 선택 3개 → FFmpeg 9:16 크롭 + 자막 번인
    fail("render 미구현 (P2-R5 태스크에서 구현)")


COMMANDS = {"ping": cmd_ping, "analyze": cmd_analyze, "render": cmd_render}


def main() -> None:
    parser = argparse.ArgumentParser(prog="sermoncut-core")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--json", default="{}", help="명령 페이로드(JSON 문자열)")
    args = parser.parse_args()

    try:
        payload = json.loads(args.json)
    except json.JSONDecodeError as e:
        fail(f"잘못된 --json 페이로드: {e}")

    result = COMMANDS[args.command](payload)
    emit_result(result)


if __name__ == "__main__":
    main()
