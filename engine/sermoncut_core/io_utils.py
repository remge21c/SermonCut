"""프로젝트 기준 경로 + JSON I/O.

각 프로젝트는 project/<이름>/ 아래 하위 폴더로 구성된다:
  config/      설정(project.json)
  input/       입력 영상(다운로드/복사 원본)
  candidates/  분석 산출(source_info/transcript/sermon_analysis/shorts_candidates)
  results/     결과 메타(selected_shorts.json)
  output/      최종 쇼츠 MP4 + 자막
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
PROJECTS_ROOT = ROOT / "project"

_project: Path | None = None


def set_project(path) -> Path:
    """활성 프로젝트 디렉터리 지정(없으면 생성)."""
    global _project
    _project = Path(path)
    _project.mkdir(parents=True, exist_ok=True)
    return _project


def active_project() -> Path | None:
    return _project


def _require() -> Path:
    if _project is None:
        raise RuntimeError("프로젝트가 설정되지 않았습니다 (--json 에 project 필요)")
    return _project


def _sub(name: str) -> Path:
    d = _require() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_dir() -> Path:
    return _sub("config")


def input_dir() -> Path:
    return _sub("input")


def candidates_dir() -> Path:
    return _sub("candidates")


def results_dir() -> Path:
    return _sub("results")


def output_dir() -> Path:
    return _sub("output")


def write_json(path, data) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_rule(filename: str) -> str:
    """docs/ 의 규칙 문서(설교규칙.md / 쇼츠규칙.md)를 프롬프트 텍스트로 로드."""
    return (DOCS_DIR / filename).read_text(encoding="utf-8")
