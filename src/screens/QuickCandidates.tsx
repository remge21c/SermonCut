import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { usePipeline } from "../store/usePipeline";
import { canConfirm, type Candidate } from "../lib/selection";
import { formatDuration, formatTimecode } from "../lib/time";
import { MediaVideo } from "../components/MediaVideo";

// Quick Shorts - 쇼츠 후보 선택 — specs/screens/quick-candidates.yaml (P3-S3-T1)
export default function QuickCandidates() {
  const nav = useNavigate();
  const s = usePipeline();
  const data = s.candidatesData;

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
  const [previewId, setPreviewId] = useState<string | null>(null);

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

      <div className="counter">선택 {s.selected.length} / 3</div>

      <ul className="candidate-list">
        {data.candidates.map((c: Candidate) => {
          const checked = s.selected.includes(c.id);
          const full = s.selected.length >= 3 && !checked;
          return (
            <li
              key={c.id}
              className={"candidate-card" + (checked ? " candidate-card--on" : "")}
            >
              <label>
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={full}
                  onChange={() => s.toggleCandidate(c.id)}
                />
                <span className="badge">{String(c.type)}</span>
                <span className="badge badge--score">{String(c.score)}</span>
                <strong>{String(c.title)}</strong>
              </label>
              <p className="seg-time">
                ⏱ {formatTimecode(Number(c.start))} ~ {formatTimecode(Number(c.end))}{" "}
                ({Math.round(Number(c.end) - Number(c.start))}초)
              </p>
              <p className="hook">{String(c.hook_line)}</p>
              <p className="highlight">“{String(c.highlight)}”</p>
              {videoPath ? (
                <button
                  className="btn-ghost"
                  onClick={() => setPreviewId(previewId === c.id ? null : c.id)}
                >
                  {previewId === c.id ? "미리보기 닫기" : "▶ 구간 미리보기"}
                </button>
              ) : (
                <span className="muted-note">미리보기 불가(영상 없음)</span>
              )}
              {previewId === c.id && videoPath && (
                <MediaVideo
                  path={videoPath}
                  start={Number(c.start)}
                  end={Number(c.end)}
                />
              )}
            </li>
          );
        })}
      </ul>

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
