"""SermonCut 코어 엔진 (headless).

기획서 §3.2 / §12.1 — 자막 확보, 분석, 쇼츠 후보, 렌더 명령을 담당한다.
GUI 없이 CLI(cli.py)로 호출되며, stdout에 JSON 라인(progress/result)을 출력한다.
"""

__version__ = "0.1.0"
