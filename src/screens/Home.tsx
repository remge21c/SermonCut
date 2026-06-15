import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { usePipeline } from "../store/usePipeline";
import type { ProjectInfo } from "../global";

// 홈 / 프로젝트 선택·생성
export default function Home() {
  const nav = useNavigate();
  const setProject = usePipeline((s) => s.setProject);
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setProjects(await window.sermoncut.listProjects());
  }
  useEffect(() => {
    refresh();
  }, []);

  function open(p: ProjectInfo) {
    setProject(p.name, p.dir);
    usePipeline.getState().reset();
    nav("/quick/input");
  }

  async function create() {
    setError(null);
    try {
      const p = await window.sermoncut.createProject(name.trim());
      setName("");
      await refresh();
      open(p);
    } catch (e) {
      setError(String(e).replace(/^Error:\s*/, ""));
    }
  }

  return (
    <section className="screen">
      <h2>SermonCut — 프로젝트</h2>

      <div className="summary-panel">
        <h3 className="block-title">새 프로젝트</h3>
        <div className="file-row">
          <input
            className="field"
            placeholder="프로젝트 이름 (예: 2026-06-15 주일2부)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && name.trim() && create()}
          />
          <button className="btn-primary" disabled={!name.trim()} onClick={create}>
            만들기
          </button>
        </div>
        {error && <p className="error">⚠ {error}</p>}
      </div>

      <h3 className="block-title">기존 프로젝트 열기</h3>
      {projects.length === 0 ? (
        <p className="placeholder">아직 프로젝트가 없습니다. 위에서 새로 만들어 보세요.</p>
      ) : (
        <ul className="project-list">
          {projects.map((p) => (
            <li key={p.dir} className="project-item" onClick={() => open(p)}>
              <strong>{p.name}</strong>
              <span className="muted-note">
                {p.created ? new Date(p.created).toLocaleString() : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
