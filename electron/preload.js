const { contextBridge, ipcRenderer } = require("electron");

// Renderer ↔ Main 안전 브리지 (P0-T0.3)
// 엔진 호출은 모두 이 API를 통해서만 이루어진다.
contextBridge.exposeInMainWorld("sermoncut", {
  // 엔진 명령 실행: analyze | render | ping
  runEngine: (command, payload) =>
    ipcRenderer.invoke("engine:run", { command, payload }),

  // 실행 중인 엔진 프로세스 취소
  cancelEngine: () => ipcRenderer.invoke("engine:cancel"),

  // 엔진 진행률/로그 스트림 구독 (stdout JSON 라인)
  onEngineProgress: (handler) => {
    const listener = (_e, data) => handler(data);
    ipcRenderer.on("engine:progress", listener);
    return () => ipcRenderer.removeListener("engine:progress", listener);
  },

  // output/ JSON 산출물 읽기
  readArtifact: (name) => ipcRenderer.invoke("artifact:read", name),

  // 프로젝트 관리
  listProjects: () => ipcRenderer.invoke("projects:list"),
  createProject: (name) => ipcRenderer.invoke("projects:create", name),
  loadProjectState: (dir) => ipcRenderer.invoke("project:state", dir),
  deleteProject: (dir) => ipcRenderer.invoke("projects:delete", dir),

  // 로컬 영상 파일 선택 다이얼로그
  pickVideo: () => ipcRenderer.invoke("dialog:openVideo"),

  // 미리보기/열기
  mediaUrl: (p) => ipcRenderer.invoke("media:url", p),
  openPath: (p) => ipcRenderer.invoke("shell:openPath", p),
  showInFolder: (p) => ipcRenderer.invoke("shell:showInFolder", p),
});
