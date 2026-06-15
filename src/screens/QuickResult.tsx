import { useNavigate } from "react-router-dom";
import { usePipeline } from "../store/usePipeline";

// Quick Shorts - 렌더 진행 및 결과 — specs/screens/quick-result.yaml (P3-S5-T1)
export default function QuickResult() {
  const nav = useNavigate();
  const s = usePipeline();
  const rendering = s.status === "rendering";

  return (
    <section className="screen">
      <h2>4. 렌더 진행 및 결과</h2>

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
        </div>
      )}

      {s.status === "done" && (
        <ul className="result-list">
          {s.results.map((r) => (
            <li key={r.id} className="result-card">
              <strong>{r.title || r.id}</strong>
              <span className={"badge badge--" + r.status}>{r.status}</span>
              <code>{r.output_path}</code>
              {r.hashtags && <div className="chips">{r.hashtags.join(" ")}</div>}
            </li>
          ))}
        </ul>
      )}

      {s.status === "error" && <p className="error">⚠ {s.error}</p>}

      {s.status === "done" && (
        <button
          className="btn-primary"
          onClick={() => {
            s.reset();
            nav("/");
          }}
        >
          새 작업 시작
        </button>
      )}
    </section>
  );
}
