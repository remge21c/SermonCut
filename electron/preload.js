const { contextBridge, ipcRenderer } = require("electron");

// Renderer ↔ Main 안전 브리지 (P0-T0.3)
// 엔진 호출은 모두 이 API를 통해서만 이루어진다.
contextBridge.exposeInMainWorld("sermoncut", {
  // 엔진 명령 실행: analyze | render | ping
  runEngine: (command, payload) =>
    ipcRenderer.invoke("engine:run", { command, payload }),

  // 엔진 진행률/로그 스트림 구독 (stdout JSON 라인)
  onEngineProgress: (handler) => {
    const listener = (_e, data) => handler(data);
    ipcRenderer.on("engine:progress", listener);
    return () => ipcRenderer.removeListener("engine:progress", listener);
  },

  // output/ JSON 산출물 읽기
  readArtifact: (name) => ipcRenderer.invoke("artifact:read", name),
});
