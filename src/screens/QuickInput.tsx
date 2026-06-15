import { useNavigate } from "react-router-dom";
import { usePipeline } from "../store/usePipeline";
import { ElapsedTimer } from "../components/ElapsedTimer";

// Quick Shorts - 입력 및 분석 — specs/screens/quick-input.yaml (P3-S2-T1)
export default function QuickInput() {
  const nav = useNavigate();
  const s = usePipeline();
  const isYoutube = s.inputType === "youtube";
  const canRun =
    s.status !== "analyzing" && (isYoutube ? s.url.trim() : s.path.trim());

  async function onAnalyze() {
    await usePipeline.getState().analyze();
    if (usePipeline.getState().status === "ready") nav("/quick/candidates");
  }

  return (
    <section className="screen">
      <h2>1. 입력 및 분석</h2>

      <div className="tabs">
        <button
          className={"tab" + (isYoutube ? " tab--active" : "")}
          onClick={() => s.setInputType("youtube")}
        >
          유튜브 URL
        </button>
        <button
          className={"tab" + (!isYoutube ? " tab--active" : "")}
          onClick={() => s.setInputType("local")}
        >
          로컬 파일
        </button>
      </div>

      {isYoutube ? (
        <input
          className="field"
          placeholder="https://youtube.com/watch?v=..."
          value={s.url}
          onChange={(e) => s.setUrl(e.target.value)}
        />
      ) : (
        <div className="file-row">
          <input
            className="field"
            placeholder="영상 파일을 선택하세요"
            value={s.path}
            onChange={(e) => s.setPath(e.target.value)}
          />
          <button
            className="btn-ghost"
            onClick={async () => {
              const p = await window.sermoncut.pickVideo();
              if (p) s.setPath(p);
            }}
          >
            파일 선택…
          </button>
        </div>
      )}

      <fieldset className="radio-group">
        <legend>자막 확보 방식</legend>
        {[
          ["auto", "자동 (YouTube 자막 우선 → Whisper)"],
          ["whisper", "Whisper 전사 강제"],
          ["import", "기존 SRT/VTT 불러오기"],
        ].map(([v, label]) => (
          <label key={v}>
            <input
              type="radio"
              name="caption"
              checked={s.captionMethod === v}
              onChange={() => s.setCaptionMethod(v as never)}
            />
            {label}
          </label>
        ))}
      </fieldset>

      <div className="btn-row">
        <button className="btn-primary" disabled={!canRun} onClick={onAnalyze}>
          {s.status === "analyzing" ? "분석 중..." : "분석 실행"}
        </button>
        {s.status === "analyzing" && (
          <button className="btn-cancel" onClick={() => s.cancel()}>
            분석 취소
          </button>
        )}
      </div>

      {s.status === "analyzing" && (
        <p className="placeholder">
          분석 진행 중{" "}
          <ElapsedTimer startedAt={s.analyzeStartedAt} running finalMs={null} />
          {" "}— 취소하려면 위 버튼을 누르세요.
        </p>
      )}
      {s.status === "cancelled" && (
        <p className="placeholder">
          분석이 취소되었습니다.{" "}
          <ElapsedTimer startedAt={s.analyzeStartedAt} running={false} finalMs={s.analyzeElapsedMs} />
        </p>
      )}
      {s.status === "error" && <p className="error">⚠ {s.error}</p>}
    </section>
  );
}
