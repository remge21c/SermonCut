import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { usePipeline } from "../store/usePipeline";
import { canConfirm, type Candidate } from "../lib/selection";
import { formatDuration, formatTimecode } from "../lib/time";
import { MediaVideo } from "../components/MediaVideo";

// Quick Shorts - 쇼츠 후보 선택 — specs/screens/quick-candidates.yaml (P3-S3-T1)
export default function QuickCandidates() {
  const nav = useNavigate();
  const s = usePipeline();
  // Hook은 항상 같은 순서로 호출 (early return 위에 위치해야 함)
  const rowRef = useRef<HTMLDivElement>(null);
  const data = s.candidatesData;

  // 한 영상 재생 시 같은 행의 다른 영상은 정지
  function handlePlay(el: HTMLVideoElement) {
    rowRef.current?.querySelectorAll("video").forEach((v) => {
      if (v !== el) v.pause();
    });
  }

  if (!data) {
    return (
      <section className="screen">
        <p className="placeholder">먼저 입력 화면에서 분석을 실행하세요.</p>
        <button className="btn-primary" onClick={() => nav("/quick/input")}>
          ← 입력 화면으로
        </button>
      </section>
    );
  }

  const confirmable = canConfirm(s.selected);
  const videoPath = (s.source?.video_path as string) || "";

  return (
    <section className="screen">
      <h2>2. 쇼츠 후보 선택</h2>

      {s.analyzeElapsedMs != null && (
        <p className="elapsed-note">⏱ 분석 소요 {formatDuration(s.analyzeElapsedMs)}</p>
      )}

      <div className="summary-panel">
        <p>{data.summary}</p>
        <div className="chips">
          {data.keywords.map((k) => (
            <span className="chip" key={k}>
              #{k}
            </span>
          ))}
        </div>
      </div>

      <div className="counter">선택 {s.selected.length} / 3 · 카드를 가로로 넘기며 미리보기하세요</div>

      <div className="candidate-row" ref={rowRef}>
        {data.candidates.map((c: Candidate) => {
          const checked = s.selected.includes(c.id);
          const full = s.selected.length >= 3 && !checked;
          return (
            <div
              key={c.id}
              className={"candidate-card-h" + (checked ? " candidate-card--on" : "")}
            >
              {videoPath ? (
                <MediaVideo
                  path={videoPath}
                  start={Number(c.start)}
                  end={Number(c.end)}
                  autoPlay={false}
                  onPlay={handlePlay}
                />
              ) : (
                <div className="video-loading">미리보기 불가(영상 없음)</div>
              )}
              <label className="card-head">
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={full}
                  onChange={() => s.toggleCandidate(c.id)}
                />
                <span className="badge">{String(c.type)}</span>
                <span className="badge badge--score">{String(c.score)}</span>
              </label>
              <strong className="card-title">{String(c.title)}</strong>
              <p className="seg-time">
                ⏱ {formatTimecode(Number(c.start))} ~ {formatTimecode(Number(c.end))}{" "}
                ({Math.round(Number(c.end) - Number(c.start))}초)
              </p>
              <div className="adjust">
                <span className="adjust-label">시작</span>
                <button className="adj-btn" onClick={() => s.adjustCandidate(c.id, "start", -1)}>−1s</button>
                <button className="adj-btn" onClick={() => s.adjustCandidate(c.id, "start", +1)}>+1s</button>
                <span className="adjust-label">끝</span>
                <button className="adj-btn" onClick={() => s.adjustCandidate(c.id, "end", -1)}>−1s</button>
                <button className="adj-btn" onClick={() => s.adjustCandidate(c.id, "end", +1)}>+1s</button>
                <button className="adj-btn" onClick={() => s.adjustCandidate(c.id, "end", +3)}>+3s</button>
              </div>
              <p className="hook">{String(c.hook_line)}</p>
              <p className="highlight">“{String(c.highlight)}”</p>
            </div>
          );
        })}
      </div>

      <button
        className="btn-primary"
        disabled={!confirmable}
        onClick={() => nav("/quick/render")}
      >
        선택 확정 ({s.selected.length}/3)
      </button>
    </section>
  );
}
