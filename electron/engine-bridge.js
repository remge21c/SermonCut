const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs/promises");
const fsSync = require("fs");

const ROOT = path.join(__dirname, "..");
const OUTPUT_DIR = path.join(ROOT, "output");

// 의존성을 우리가 관리하는 engine/.venv 파이썬을 우선 사용 (없으면 시스템 python)
const VENV_PY = path.join(ROOT, "engine", ".venv", "Scripts", "python.exe");
const PYTHON =
  process.env.PYTHON_BIN || (fsSync.existsSync(VENV_PY) ? VENV_PY : "python");

// 실행 중인 엔진 프로세스를 sender(webContents.id) 기준으로 추적 → 취소 지원
const running = new Map();

const CANCELLED = "__CANCELLED__";

// Python 엔진(sermoncut_core)을 자식 프로세스로 호출하고
// stdout의 JSON 라인을 진행률 이벤트로 중계한다. (P0-T0.3)
function runEngine(win, senderId, command, payload) {
  return new Promise((resolve, reject) => {
    const args = ["-m", "sermoncut_core.cli", command, "--json", JSON.stringify(payload || {})];
    const proc = spawn(PYTHON, args, {
      cwd: path.join(ROOT, "engine"),
      // 한글 깨짐 방지: Python stdout/stderr 를 UTF-8 로 강제
      env: { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1" },
    });
    proc._cancelled = false;
    running.set(senderId, proc);

    let lastResult = null;
    let stderr = "";

    proc.stdout.on("data", (buf) => {
      for (const line of buf.toString().split(/\r?\n/)) {
        if (!line.trim()) continue;
        try {
          const msg = JSON.parse(line);
          if (msg.type === "progress") win?.webContents.send("engine:progress", msg);
          else if (msg.type === "result") lastResult = msg.data;
        } catch {
          // 비 JSON 로그는 무시 (디버깅 출력)
        }
      }
    });

    proc.stderr.on("data", (buf) => (stderr += buf.toString()));

    proc.on("close", (code) => {
      running.delete(senderId);
      if (proc._cancelled) {
        const err = new Error(CANCELLED);
        err.cancelled = true;
        reject(err);
      } else if (code === 0) {
        resolve(lastResult);
      } else {
        reject(new Error(`engine exited ${code}: ${stderr}`));
      }
    });
    proc.on("error", (e) => {
      running.delete(senderId);
      reject(e);
    });
  });
}

function cancelEngine(senderId) {
  const proc = running.get(senderId);
  if (!proc) return false;
  proc._cancelled = true;
  // Windows에서 프로세스 트리 종료
  if (process.platform === "win32") {
    spawn("taskkill", ["/pid", String(proc.pid), "/T", "/F"]);
  } else {
    proc.kill("SIGTERM");
  }
  return true;
}

function resolveAbs(p) {
  return path.isAbsolute(p) ? p : path.join(ROOT, p);
}

function registerEngineHandlers(ipcMain) {
  const { BrowserWindow, shell, dialog } = require("electron");

  // 네이티브 파일 선택 다이얼로그 (로컬 영상)
  ipcMain.handle("dialog:openVideo", async (e) => {
    const win = BrowserWindow.fromWebContents(e.sender);
    const res = await dialog.showOpenDialog(win, {
      title: "설교 영상 선택",
      properties: ["openFile"],
      filters: [
        { name: "영상 파일", extensions: ["mp4", "mov", "mkv", "avi", "webm", "m4v"] },
        { name: "모든 파일", extensions: ["*"] },
      ],
    });
    if (res.canceled || res.filePaths.length === 0) return null;
    return res.filePaths[0];
  });

  ipcMain.handle("engine:run", async (e, { command, payload }) => {
    const win = BrowserWindow.fromWebContents(e.sender);
    return runEngine(win, e.sender.id, command, payload);
  });

  ipcMain.handle("engine:cancel", async (e) => cancelEngine(e.sender.id));

  ipcMain.handle("artifact:read", async (_e, name) => {
    const file = path.join(OUTPUT_DIR, name);
    const raw = await fs.readFile(file, "utf-8");
    return JSON.parse(raw);
  });

  // 미리보기/열기 지원
  ipcMain.handle("media:url", (_e, p) =>
    `media://m/${encodeURIComponent(resolveAbs(p))}`);
  ipcMain.handle("shell:openPath", (_e, p) => shell.openPath(resolveAbs(p)));
  ipcMain.handle("shell:showInFolder", (_e, p) => {
    shell.showItemInFolder(resolveAbs(p));
    return true;
  });
}

module.exports = { registerEngineHandlers, runEngine, CANCELLED };
