"""stdout JSON 라인 프로토콜 — Electron engine-bridge.js와 짝.

progress: 진행률/단계 이벤트, result: 최종 결과 1회.
"""
import json
import sys


def emit_progress(step: str, percent: float | None = None, message: str | None = None) -> None:
    line = {"type": "progress", "step": step}
    if percent is not None:
        line["percent"] = percent
    if message is not None:
        line["message"] = message
    print(json.dumps(line, ensure_ascii=False), flush=True)


def emit_result(data) -> None:
    print(json.dumps({"type": "result", "data": data}, ensure_ascii=False), flush=True)


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr, flush=True)
    sys.exit(code)
