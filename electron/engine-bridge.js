const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs/promises");

const ROOT = path.join(__dirname, "..");
const OUTPUT_DIR = path.join(ROOT, "output");
const PYTHON = process.env.PYTHON_BIN || "python";

// Python 엔진(sermoncut_core)을 자식 프로세스로 호출하고
// stdout의 JSON 라인을 진행률 이벤트로 중계한다. (P0-T0.3)
function runEngine(win, command, payload) {
  return new Promise((resolve, reject) => {
    const args = ["-m", "sermoncut_core.cli", command, "--json", JSON.stringify(payload || {})];
    const proc = spawn(PYTHON, args, { cwd: path.join(ROOT, "engine") });

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
      if (code === 0) resolve(lastResult);
      else reject(new Error(`engine exited ${code}: ${stderr}`));
    });
    proc.on("error", reject);
  });
}

function registerEngineHandlers(ipcMain) {
  const { BrowserWindow } = require("electron");

  ipcMain.handle("engine:run", async (e, { command, payload }) => {
    const win = BrowserWindow.fromWebContents(e.sender);
    return runEngine(win, command, payload);
  });

  ipcMain.handle("artifact:read", async (_e, name) => {
    const file = path.join(OUTPUT_DIR, name);
    const raw = await fs.readFile(file, "utf-8");
    return JSON.parse(raw);
  });
}

module.exports = { registerEngineHandlers, runEngine };
