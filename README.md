# SermonCut

설교 영상 반자동 편집 앱 (Windows 로컬). 1차 MVP = **Quick Shorts**:
유튜브/로컬 영상 → 자막 확보 → AI 분석 → 쇼츠 후보 5개 → 3개 선택 → 세로 9:16 MP4 3개.

## 구조
```
app(렌더러)      : src/            React 19 + react-router (HashRouter)
electron(메인)   : electron/       창 + IPC + Python 엔진 브리지
engine(코어)     : engine/         Python sermoncut_core (자막/분석/렌더)
명세             : specs/          domain/resources.yaml, screens/*.yaml
기획             : docs/           최종기획서 + 설교규칙 + 쇼츠규칙 + planning/06-tasks.md
산출물           : output/         *.json + short_00N.mp4 (gitignore)
```

## 기술 스택
Electron + React(Vite) · Python Engine · FFmpeg · Whisper · yt-dlp · Gemini API

## 개발 셋업
```bash
# 1) 프론트/일렉트론 의존성
npm install

# 2) 엔진 (Python 3.11+)
cd engine && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt

# 3) 환경변수
copy .env.example .env   # GEMINI_API_KEY 등 입력

# 4) 엔진 헬스체크 (IPC 프로토콜 확인)
cd engine && python -m sermoncut_core.cli ping --json "{}"

# 5) 앱 실행 (dev)
npm run dev
```

## 진행 상황
- [x] 기획/규칙/화면 명세/태스크 (`docs/`, `specs/`, `docs/planning/06-tasks.md`)
- [x] P0 스캐폴드 (Electron + React + Python 엔진 + IPC 브리지)
- [ ] P1~P4 구현 — `docs/planning/06-tasks.md` 참조
