"""시간 변환 유틸 (P1-R0-T1) — 기존 sermon_finder.py to_seconds/hms 재사용 대상.

AI 출력은 "HH:MM:SS" 문자열, 내부 저장은 초 단위 float.
"""


def to_seconds(hms: str) -> float:
    """'HH:MM:SS' 또는 'MM:SS' → 초(float)."""
    parts = [float(p) for p in hms.strip().split(":")]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0.0, parts[0], parts[1]
    else:
        h, m, s = 0.0, 0.0, parts[0]
    return h * 3600 + m * 60 + s


def hms(seconds: float) -> str:
    """초(float) → 'HH:MM:SS'."""
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
