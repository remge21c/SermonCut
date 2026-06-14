import { useNavigate } from "react-router-dom";

// 홈 / 모드 선택 — specs/screens/home.yaml
export default function Home() {
  const nav = useNavigate();
  return (
    <section className="screen screen--centered">
      <h2>무엇을 만들까요?</h2>
      <div className="mode-cards">
        <button className="mode-card" onClick={() => nav("/quick/input")}>
          <strong>A. Quick Shorts</strong>
          <span>유튜브 링크나 영상 파일로 쇼츠만 빠르게 만들기</span>
        </button>
        <button className="mode-card mode-card--disabled" disabled title="2차 예정">
          <strong>B. 본문영상 편집</strong>
          <span>준비 중 (2차 예정)</span>
        </button>
      </div>
    </section>
  );
}
