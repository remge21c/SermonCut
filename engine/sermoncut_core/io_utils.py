"""출력 산출물 경로 + JSON I/O (specs/domain/resources.yaml 영속화 규약)."""
import json
import os
from pathlib import Path

# 프로젝트 루트 = engine/ 의 상위
ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output"
CACHE_DIR = ROOT / "cache"
DOCS_DIR = ROOT / "docs"


def cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def output_path(name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / name


def write_json(name: str, data) -> Path:
    path = output_path(name)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_json(name: str):
    path = OUTPUT_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def read_rule(filename: str) -> str:
    """docs/ 의 규칙 문서(설교규칙.md / 쇼츠규칙.md)를 프롬프트 텍스트로 로드."""
    return (DOCS_DIR / filename).read_text(encoding="utf-8")
