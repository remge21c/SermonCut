import { useNavigate } from "react-router-dom";
import { usePipeline } from "../store/usePipeline";
import { ElapsedTimer } from "../components/ElapsedTimer";
import { formatDuration } from "../lib/time";
import { MediaVideo } from "../components/MediaVideo";

// Quick Shorts - 렌더 진행 및 결과 — specs/screens/quick-result.yaml (P3-S5-T1)
export default function QuickResult() {
  const nav = useNavigate();
  const s = usePipeline();
  const rendering = s.status === "rendering";

  return (
    <section className="screen">
      <h2>4. 렌더 진행 및 결과</h2>

      {rendering && (
        <p className="elapsed-note">
          렌더 진행 중{" "}
          <ElapsedTimer startedAt={s.renderStartedAt} running finalMs={null} />
        </p>
      )}
      {s.status === "done" && s.renderElapsedMs != null && (
        <p className="elapsed-note">⏱ 렌더 소요 {formatDuration(s.renderElapsedMs)}</p>
      )}

      {rendering && (
        <div className="progress-list">
          {Object.entries(s.progress).map(([step, pct]) => (
            <div key={step} className="progress-row">
              <span>{step}</span>
              <div className="bar">
                <div className="bar-fill" style={{ width: `${pct}%` }} />
              </div>
            </div>
          ))}
          {Object.keys(s.progress).length === 0 && <p>렌더 준비 중...</p>}
          <button className="btn-cancel" onClick={() => s.cancel()}>
            렌더 취소
          </button>
        </div>
      )}

      {s.status === "cancelled" && (
        <div>
          <p className="placeholder">렌더가 취소되었습니다.</p>
          <button className="btn-primary" onClick={() => { s.reset(); nav("/"); }}>
            처음으로
          </button>
        </div>
      )}

      {s.status === "done" && (
        <ul className="result-list">
          {s.results.map((r) => (
            <li key={r.id} className="result-card">
              <strong>{r.title || r.id}</strong>
              <span className={"badge badge--" + r.status}>{r.status}</span>
              {r.status === "done" && <MediaVideo path={r.output_path} autoPlay={false} />}
              <code>{r.output_path}</code>
              {r.hashtags && <div className="chips">{r.hashtags.join(" ")}</div>}
              <div className="btn-row">
                <button className="btn-ghost" onClick={() => window.sermoncut.openPath(r.output_path)}>
                  파일 열기
                </button>
                <button className="btn-ghost" onClick={() => window.sermoncut.showInFolder(r.output_path)}>
                  폴더 열기
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {s.status === "error" && <p className="error">⚠ {s.error}</p>}

      {s.status === "done" && (
        <div className="btn-row">
          <button className="btn-ghost" onClick={() => nav("/quick/candidates")}>
            ← 후보 다시 선택
          </button>
          <button className="btn-ghost" onClick={() => nav("/quick/render")}>
            ← 렌더 설정
          </button>
          <button
            className="btn-primary"
            onClick={() => {
              s.reset();
              nav("/");
            }}
          >
            새 작업 시작
          </button>
        </div>
      )}
    </section>
  );
}
