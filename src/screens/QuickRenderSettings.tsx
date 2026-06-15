import { useNavigate } from "react-router-dom";
import { usePipeline } from "../store/usePipeline";
import type { Candidate } from "../lib/selection";

// Quick Shorts - 렌더 설정 — specs/screens/quick-render-settings.yaml (P3-S4-T1)
const CROPS: Array<["left" | "center" | "right", string]> = [
  ["left", "왼쪽"],
  ["center", "가운데"],
  ["right", "오른쪽"],
];

export default function QuickRenderSettings() {
  const nav = useNavigate();
  const s = usePipeline();
  const data = s.candidatesData;
  const chosen =
    data?.candidates.filter((c: Candidate) => s.selected.includes(c.id)) ?? [];

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

  async function onRender() {
    nav("/quick/result");
    await usePipeline.getState().render();
  }

  return (
    <section className="screen">
      <h2>3. 렌더 설정</h2>

      <ul className="selected-list">
        {chosen.map((c) => (
          <li key={c.id}>
            <span className="badge">{String(c.type)}</span> {String(c.title)}
          </li>
        ))}
      </ul>

      <div className="field-row">
        <span>세로 크롭 위치</span>
        <div className="segmented">
          {CROPS.map(([v, label]) => (
            <button
              key={v}
              className={"seg" + (s.crop === v ? " seg--active" : "")}
              onClick={() => s.setCrop(v)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <p className="readonly-info">자막 스타일: 기본 템플릿 (흰 글씨 + 검은 외곽선)</p>
      <p className="readonly-info">출력: 1080 × 1920 / 30fps / mp4</p>

      <button className="btn-primary" disabled={chosen.length !== 3} onClick={onRender}>
        렌더 시작
      </button>
    </section>
  );
}
