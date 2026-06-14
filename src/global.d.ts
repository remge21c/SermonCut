// preload.js가 노출하는 브리지 API 타입 (P0-T0.3)
export interface SermonCutBridge {
  runEngine: <T = unknown>(
    command: "analyze" | "render" | "ping",
    payload?: Record<string, unknown>
  ) => Promise<T>;
  onEngineProgress: (handler: (data: EngineProgress) => void) => () => void;
  readArtifact: <T = unknown>(name: string) => Promise<T>;
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
