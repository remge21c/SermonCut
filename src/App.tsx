import { Outlet, useLocation, useNavigate } from "react-router-dom";

const STEPS = [
  { path: "/quick/input", label: "입력" },
  { path: "/quick/candidates", label: "후보" },
  { path: "/quick/render", label: "설정" },
  { path: "/quick/result", label: "결과" },
];

// 공통 레이아웃 + Quick Shorts 진행 stepper (P1-S0)
export default function App() {
  const { pathname } = useLocation();
  const nav = useNavigate();
  const showStepper = pathname.startsWith("/quick");

  return (
    <div className="app">
      <header className="app-header">
        <h1
          className="app-logo"
          onClick={() => nav("/")}
          title="홈으로"
          style={{ cursor: "pointer" }}
        >
          SermonCut
        </h1>
        {showStepper && (
          <nav className="stepper">
            {STEPS.map((s) => (
              <button
                key={s.path}
                className={"step" + (pathname === s.path ? " step--active" : "")}
                onClick={() => nav(s.path)}
                title={`${s.label}(으)로 이동`}
              >
                {s.label}
              </button>
            ))}
          </nav>
        )}
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
