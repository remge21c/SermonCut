# SermonCut — TASKS (Domain-Guarded)

> 1차 MVP = **Quick Shorts**. 입력 → 자막 → 분석 → 후보 5개 → 3개 선택 → 세로 MP4 3개.
> 구조: **Resource 태스크(Python 엔진 = 백엔드)** + **Screen 태스크(React/Electron = 프론트)**.
> 모든 P1+ 태스크는 TDD(RED → GREEN → REFACTOR).
>
> 입력: `specs/domain/resources.yaml`, `specs/screens/*.yaml`, `docs/SermonCut_최종기획서.md`, `docs/설교규칙.md`, `docs/쇼츠규칙.md`
> ICV(Interface Contract Validation): 화면 needs vs 리소스 fields **커버리지 100% 통과**.

## 기술 스택
- Electron(데스크톱 셸) + React(UI)
- Python Engine `sermoncut-core`(자막/분석/렌더 명령) — Electron Main ↔ Python: 자식 프로세스 + JSON stdout/파일 I/O
- FFmpeg(자르기/9:16 크롭/자막 번인/렌더), Whisper(로컬 전사), yt-dlp(유튜브 영상·자막), Gemini API(분석/후보)

## 리소스 ↔ 산출물 매핑
| Resource | 산출 파일 | 규칙 문서 |
|---|---|---|
| source | output/source_info.json | — |
| transcript | output/transcript.json | — |
| sermon_analysis | output/sermon_analysis.json | 설교규칙.md |
| shorts_candidate | output/shorts_candidates.json | 쇼츠규칙.md |
| shorts_render | output/selected_shorts.json + short_00N.mp4 | §8.4 렌더 사양 |

---

## P0 — 프로젝트 셋업

### P0-T0.1: 모노레포 + 빌드 골격
- Electron + React(Vite) + Python engine 폴더 구조 (`app/`, `engine/`, `specs/`, `output/`)
- electron-builder(Windows) 패키징 기본 설정
- 산출: 빈 창이 뜨고 홈 라우트가 렌더됨
- DoD: `npm run dev`로 Electron 창 실행, React 라우터 동작

### P0-T0.2: 외부 의존성 + 설정
- FFmpeg / Whisper / yt-dlp 바이너리·패키지 설치 및 경로 탐지
- Gemini API 키 설정(.env), 키 미설정 시 친절한 오류
- DoD: `engine`에서 ffmpeg/whisper/yt-dlp/gemini 헬스체크 스크립트 통과

### P0-T0.3: Electron ↔ Python IPC 브리지 + 파일 I/O 규약
- Main에서 Python 엔진을 자식 프로세스로 호출, 진행률 이벤트(stdout JSON 라인) 수신
- `output/` JSON 읽기/쓰기 헬퍼(스키마: specs/domain/resources.yaml)
- DoD: Renderer 버튼 → Main → Python "ping" → 결과 JSON Renderer 표시(E2E 1건)

---

## P1 — 코어 공통 (엔진 유틸 + 공통 UI)  *(P0 완료 후)*

### P1-R0-T1: transcript 정규화 + 자막 파서  *(엔진)*
- `sermon_finder.py`에서 재사용: `parse_vtt`, `build_transcript`, `to_seconds`, `hms`, `video_id`
- VTT/SRT → `{start, end, text}` 세그먼트 정규화
- 시간 변환 규약: AI 출력 "HH:MM:SS" ↔ 내부 초 float
- TDD: 샘플 VTT/SRT 픽스처로 파싱·변환 단위 테스트 (RED→GREEN→REFACTOR)

### P1-R0-T2: Gemini 클라이언트  *(엔진)*
- `call_gemini`(프롬프트 주입), `parse_json`(JSON-only 응답 파싱·검증·재시도)
- 규칙 문서(설교규칙/쇼츠규칙)를 시스템 프롬프트로 주입하는 로더
- TDD: 모킹된 응답으로 파싱/재시도/오류 처리 테스트

### P1-S0-T1: 공통 레이아웃 + 라우팅  *(프론트)*
- 라우터(/ , /quick/*), 단계 표시 stepper(입력→후보→설정→결과)
- 공통 컴포넌트 골격: candidate_card, progress_bar, status_badge, type_badge, keyword_chips (specs/shared/components.yaml)
- TDD: 라우팅/스텝퍼 렌더 컴포넌트 테스트

---

## P2 — Resource 태스크 (Python 엔진)  *(P1 완료 후, R간 의존 순서 주의)*

### P2-R1-T1: source — 입력 처리  *(병렬 가능: R1)*
- 입력: youtube_url | local_mp4 → `source_info.json` 생성
- 유튜브: yt-dlp로 영상/메타데이터 확보(`get_title`, `video_id`), 로컬: 파일 검증·복사
- TDD: 로컬 파일 케이스 + 유튜브 메타 파싱(모킹) 테스트
- 산출: source(id,type,url,video_path,title,duration_sec)

### P2-R2-T1: transcript — 자막 확보 (YouTube 우선 → Whisper 폴백)  *(R1 의존)*
- 1순위: `download_subs`로 YouTube 자막(VTT) → 2순위: 자막 없으면 Whisper 전사 → 3순위: import(SRT/VTT)
- P1-R0-T1 파서로 정규화하여 `transcript.json` 생성, `caption_source` 기록
- TDD: 자막 있음/없음(폴백 트리거)/임포트 3 케이스
- 산출: transcript(source_id,caption_source,segments)

### P2-R3-T1: sermon_analysis — 설교 구간 분석  *(R2 의존)*
- 설교규칙.md 프롬프트 + transcript → Gemini → `sermon_analysis.json`
- 키 정합: part, sermon_start, sermon_end, *_reason, benediction_*(못 찾으면 null), summary, keywords
- HH:MM:SS → 초 float 변환 후 저장
- TDD: 부별 시작/끝, 축도 null, 여는/맺는 기도 구분 케이스(고정 transcript 픽스처 + 모킹 응답)
- 산출: sermon_analysis(설교규칙.md 출력과 1:1)

### P2-R4-T1: shorts_candidate — 쇼츠 후보 5개  *(R3 의존)*
- 입력 범위: sermon_start~sermon_end(축도 제외) 본문 transcript
- 쇼츠규칙.md 프롬프트 → Gemini → 후보 5개 + selected_candidate_ids(추천 3개) → `shorts_candidates.json`
- 검증: 정확히 5개, 길이 15~40초, 구간 비겹침, 타입 분배(후킹2·예화2·핵심1 권장)
- TDD: 후보 개수/길이/겹침/선택3 검증 테스트
- 산출: shorts_candidate(쇼츠규칙.md 출력과 1:1)

### P2-R5-T1: shorts_render — 세로 렌더 + 자막 번인  *(R4 + R1 의존)*
- 선택 3개 → FFmpeg: 9:16 중앙 크롭(crop left/center/right) + 자막 번인(흰글씨/검은외곽선) + 1080x1920/30fps/mp4
- hook_line/highlight 자막 오버레이, 진행률 stdout 이벤트, `selected_shorts.json` + short_00N.mp4
- TDD: FFmpeg 명령 빌더 단위 테스트(스냅샷) + 짧은 샘플 실제 렌더 1건
- 산출: shorts_render(id,candidate_id,...,crop,status,progress,output_path)

---

## P3 — Screen 태스크 (React)  *(해당 Resource 완료 후)*

### P3-S1-T1: home — 모드 선택  *(P1-S0 의존)*
- A Quick Shorts 카드(활성) / B 본문편집 카드(비활성, "준비 중")
- TDD: 카드 렌더, A 클릭 시 /quick/input 이동, B 비활성 (specs/screens/home.yaml tests)

### P3-S2-T1: quick-input — 입력 및 분석  *(R1~R4 의존)*
- URL/로컬 탭, 자막 방식 라디오(auto/whisper/import), 분석 실행 → run_pipeline(analyze) → 진행 로그
- 성공 시 /quick/candidates 이동, URL 검증, 자막 없음 폴백 표시
- TDD: 4개 테스트(유튜브/로컬+whisper/URL검증/폴백) — quick-input.yaml

### P3-S3-T1: quick-candidates — 후보 선택  *(R4 의존)*
- 요약/키워드 패널, 후보 5개 카드, 추천 3개 기본 선택, n/3 카운터, 3개 정확 선택 시 확정
- 확정 시 selected_candidate_ids 저장 → /quick/render
- TDD: 5개 표시+추천프리셋 / 최대3개 제한 / 3개미만 차단 / 확정이동 — quick-candidates.yaml

### P3-S4-T1: quick-render-settings — 렌더 설정  *(R5 의존)*
- 선택 3개 미리보기, 크롭 위치(좌/중/우, 기본 중앙), 자막/출력 사양 readonly, 렌더 시작
- 시작 시 shorts_render 3건 생성 → /quick/result
- TDD: 기본설정표시 / 크롭변경반영 / 렌더시작 — quick-render-settings.yaml

### P3-S5-T1: quick-result — 진행 및 결과  *(R5 의존)*
- 3개 진행률/상태 실시간, 완료 카드(파일/폴더 열기, 메타 복사), 실패 재렌더, 새 작업
- TDD: 진행표시 / 완료결과 / 실패재렌더 / 새작업 — quick-result.yaml

---

## P4 — Verification (연결점 + E2E)  *(관련 태스크 완료 후)*

### P4-S1-V ~ P4-S5-V: 화면별 연결점 검증
- 각 화면의 data_requirements ↔ Resource 산출 JSON 키 일치 확인
- 화면 tests(YAML) 전부 통과

### P4-E2E: 전체 파이프라인 E2E
- 시나리오: 유튜브 링크 입력 → 분석 → 후보 5개 → 3개 선택 → 렌더 → output/short_001~003.mp4 생성 검증
- 폴백 시나리오: 자막 없는 영상 → Whisper 폴백 → 정상 산출

---

## 의존성 그래프 (요약)
```
P0(셋업) → P1(코어 유틸/공통 UI)
P1 → P2-R1(source) → R2(transcript) → R3(analysis) → R4(candidate) → R5(render)
P2-R* → P3-S*(화면)   (S1은 P1-S0만 의존, S2는 R1~R4, S3는 R4, S4·S5는 R5)
P3-S* → P4-V/E2E
병렬: P2-R1과 P1-S0 / P3-S1은 초기 병렬 가능. R2~R5는 직렬(데이터 흐름).
```

## 태스크 집계
- 셋업(P0): 3
- 코어 공통(P1): 3 (R0×2, S0×1)
- Resource(P2): 5
- Screen(P3): 5
- Verification(P4): 5(화면별 V) + 1(E2E) = 6
- **총 22 태스크**
