import { Outlet, useLocation } from "react-router-dom";

const STEPS = [
  { path: "/quick/input", label: "입력" },
  { path: "/quick/candidates", label: "후보" },
  { path: "/quick/render", label: "설정" },
  { path: "/quick/result", label: "결과" },
];

// 공통 레이아웃 + Quick Shorts 진행 stepper (P1-S0)
export default function App() {
  const { pathname } = useLocation();
  const showStepper = pathname.startsWith("/quick");

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-logo">SermonCut</h1>
        {showStepper && (
          <nav className="stepper">
            {STEPS.map((s, i) => (
              <span
                key={s.path}
                className={"step" + (pathname === s.path ? " step--active" : "")}
              >
                {i + 1}. {s.label}
              </span>
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
