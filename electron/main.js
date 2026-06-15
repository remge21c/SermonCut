const { app, BrowserWindow, ipcMain, protocol, net } = require("electron");
const path = require("path");
const { pathToFileURL } = require("url");
const { registerEngineHandlers } = require("./engine-bridge");

const isDev = !app.isPackaged;

// 로컬 영상/결과 파일을 렌더러 <video>에 안전하게 제공하기 위한 커스텀 스킴
protocol.registerSchemesAsPrivileged([
  {
    scheme: "media",
    privileges: { stream: true, supportFetchAPI: true, bypassCSP: true, secure: true },
  },
]);

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 640,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    win.loadURL("http://localhost:5173");
    win.webContents.openDevTools({ mode: "detach" });
  } else {
    win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }
}

app.whenReady().then(() => {
  // media://m/<encoded abs path> → 로컬 파일 스트리밍 (range 지원)
  protocol.handle("media", (req) => {
    const url = new URL(req.url);
    const p = decodeURIComponent(url.pathname).replace(/^\//, "");
    return net.fetch(pathToFileURL(p).toString());
  });

  registerEngineHandlers(ipcMain);
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
