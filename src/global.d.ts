// preload.js가 노출하는 브리지 API 타입 (P0-T0.3)
export interface SermonCutBridge {
  runEngine: <T = unknown>(
    command: "analyze" | "render" | "ping",
    payload?: Record<string, unknown>
  ) => Promise<T>;
  cancelEngine: () => Promise<boolean>;
  onEngineProgress: (handler: (data: EngineProgress) => void) => () => void;
  readArtifact: <T = unknown>(name: string) => Promise<T>;
  listProjects: () => Promise<ProjectInfo[]>;
  createProject: (name: string) => Promise<ProjectInfo>;
  pickVideo: () => Promise<string | null>;
  mediaUrl: (p: string) => Promise<string>;
  openPath: (p: string) => Promise<string>;
  showInFolder: (p: string) => Promise<boolean>;
}

export interface ProjectInfo {
  name: string;
  dir: string;
  created: string | null;
}

export interface EngineProgress {
  type: "progress";
  step: string;
  percent?: number;
  message?: string;
}

declare global {
  interface Window {
    sermoncut: SermonCutBridge;
  }
}
