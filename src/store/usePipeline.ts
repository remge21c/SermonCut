import { create } from "zustand";
import {
  defaultSelection,
  toggleSelection,
  type Candidate,
} from "../lib/selection";

type Status =
  | "idle"
  | "analyzing"
  | "ready"
  | "rendering"
  | "done"
  | "cancelled"
  | "error";
export type Crop = "left" | "center" | "right" | "fit" | "fit_black";

const CANCELLED = "__CANCELLED__";
const isCancel = (e: unknown) => String(e).includes(CANCELLED);

interface CandidatesData {
  summary: string;
  keywords: string[];
  candidates: Candidate[];
  selected_candidate_ids: string[];
}

interface RenderResult {
  id: string;
  title?: string;
  status: string;
  progress: number;
  output_path: string;
  hashtags?: string[];
}

interface PipelineState {
  // 프로젝트
  projectName: string;
  projectDir: string;

  // 입력
  inputType: "youtube" | "local";
  url: string;
  path: string;
  captionMethod: "auto" | "whisper" | "import";
  whisperModel: "tiny" | "base" | "small";

  // 분석 결과
  status: Status;
  error: string | null;
  source: Record<string, unknown> | null;
  transcript: Record<string, unknown> | null;
  analysis: Record<string, unknown> | null;
  candidatesData: CandidatesData | null;
  selected: string[];

  // 렌더
  crop: Crop;
  results: RenderResult[];
  progress: Record<string, number>;
  renderTick: number;   // 렌더 완료 시마다 증가(영상 캐시 갱신용)

  // 분석 진행 표시
  analyzePct: number;
  analyzeMsg: string;

  // 경과 시간(ms)
  analyzeStartedAt: number | null;
  analyzeElapsedMs: number | null;
  renderStartedAt: number | null;
  renderElapsedMs: number | null;

  // actions
  setProject: (name: string, dir: string) => void;
  loadProjectState: (data: {
    source: Record<string, unknown> | null;
    analysis: Record<string, unknown> | null;
    candidatesData: CandidatesData | null;
    results: RenderResult[] | null;
  }) => void;
  setInputType: (t: "youtube" | "local") => void;
  setWhisperModel: (m: "tiny" | "base" | "small") => void;
  setUrl: (v: string) => void;
  setPath: (v: string) => void;
  setCaptionMethod: (m: "auto" | "whisper" | "import") => void;
  toggleCandidate: (id: string) => void;
  adjustCandidate: (id: string, field: "start" | "end", delta: number) => void;
  setCrop: (c: Crop) => void;
  analyze: () => Promise<void>;
  render: () => Promise<void>;
  renderOne: (index: number) => Promise<void>;
  cancel: () => Promise<void>;
  reset: () => void;
}

export const usePipeline = create<PipelineState>((set, get) => ({
  projectName: "",
  projectDir: "",

  inputType: "youtube",
  url: "",
  path: "",
  captionMethod: "auto",
  whisperModel: "base",

  status: "idle",
  error: null,
  source: null,
  transcript: null,
  analysis: null,
  candidatesData: null,
  selected: [],

  crop: "center",
  results: [],
  progress: {},
  renderTick: 0,

  analyzePct: 0,
  analyzeMsg: "",

  analyzeStartedAt: null,
  analyzeElapsedMs: null,
  renderStartedAt: null,
  renderElapsedMs: null,

  // 탭 전환 시 자막 방식 기본값: 유튜브→자동, 로컬→Whisper(자막 없음)
  setProject: (name, dir) => set({ projectName: name, projectDir: dir }),

  // 저장된 프로젝트 산출물로 상태 복원 (재개)
  loadProjectState: ({ source, analysis, candidatesData, results }) =>
    set(() => {
      const patch: Partial<PipelineState> = {};
      if (source) patch.source = source;
      if (analysis) patch.analysis = analysis;
      if (candidatesData) {
        patch.candidatesData = candidatesData;
        patch.selected = defaultSelection(
          candidatesData.candidates,
          candidatesData.selected_candidate_ids
        );
        patch.status = "ready";
      }
      if (results && results.length) {
        patch.results = results;
        patch.status = "done";
      }
      return patch;
    }),

  setInputType: (t) =>
    set({ inputType: t, captionMethod: t === "local" ? "whisper" : "auto" }),

  setWhisperModel: (m) => set({ whisperModel: m }),
  setUrl: (v) => set({ url: v }),
  setPath: (v) => set({ path: v }),
  setCaptionMethod: (m) => set({ captionMethod: m }),

  toggleCandidate: (id) => set({ selected: toggleSelection(get().selected, id) }),

  // 후보 시작/끝 시각 미세조정 (초). start<end, start>=0, 최소 1초 유지.
  adjustCandidate: (id, field, delta) =>
    set((state) => {
      if (!state.candidatesData) return {};
      const candidates = state.candidatesData.candidates.map((c) => {
        if (c.id !== id) return c;
        const start = Number(c.start);
        const end = Number(c.end);
        const next = { ...c } as Candidate & { start: number; end: number; duration_sec: number };
        if (field === "start") {
          next.start = Math.max(0, Math.min(start + delta, end - 1));
        } else {
          next.end = Math.max(start + 1, end + delta);
        }
        next.duration_sec = Math.round((next.end - next.start) * 10) / 10;
        return next;
      });
      return { candidatesData: { ...state.candidatesData, candidates } };
    }),

  setCrop: (c) => set({ crop: c }),

  analyze: async () => {
    const { inputType, url, path, captionMethod } = get();
    set({
      status: "analyzing",
      error: null,
      analyzePct: 0,
      analyzeMsg: "분석 준비 중",
      analyzeStartedAt: Date.now(),
      analyzeElapsedMs: null,
    });
    const unsub = window.sermoncut.onEngineProgress((p) =>
      set({ analyzePct: p.percent ?? 0, analyzeMsg: p.message ?? "" })
    );
    try {
      const input =
        inputType === "youtube"
          ? { type: "youtube", url }
          : { type: "local", path };
      const res = await window.sermoncut.runEngine<{
        source: Record<string, unknown>;
        analysis: Record<string, unknown>;
        candidates: CandidatesData;
      }>("analyze", {
        project: get().projectDir,
        input,
        caption_method: captionMethod,
        whisper_model: get().whisperModel,
      });

      const selected = defaultSelection(
        res.candidates.candidates,
        res.candidates.selected_candidate_ids
      );
      set({
        status: "ready",
        source: res.source,
        analysis: res.analysis,
        candidatesData: res.candidates,
        selected,
      });
    } catch (e) {
      if (isCancel(e)) set({ status: "cancelled", error: null });
      else set({ status: "error", error: String(e) });
    } finally {
      unsub?.();
      const startedAt = get().analyzeStartedAt;
      set({ analyzeElapsedMs: startedAt ? Date.now() - startedAt : null });
    }
  },

  render: async () => {
    const { candidatesData, selected, crop, source } = get();
    if (!candidatesData) return;
    const chosen = candidatesData.candidates.filter((c) =>
      selected.includes(c.id)
    );
    set({
      status: "rendering",
      results: [],
      renderStartedAt: Date.now(),
      renderElapsedMs: null,
    });

    const unsub = window.sermoncut.onEngineProgress((p) => {
      set((s) => ({ progress: { ...s.progress, [p.step]: p.percent ?? 0 } }));
    });
    try {
      const res = await window.sermoncut.runEngine<{ shorts: RenderResult[] }>(
        "render",
        { project: get().projectDir, selected: chosen, crop, source }
      );
      set({ status: "done", results: res.shorts, renderTick: get().renderTick + 1 });
    } catch (e) {
      if (isCancel(e)) set({ status: "cancelled", error: null });
      else set({ status: "error", error: String(e) });
    } finally {
      unsub?.();
      const startedAt = get().renderStartedAt;
      set({ renderElapsedMs: startedAt ? Date.now() - startedAt : null });
    }
  },

  // 단일 쇼츠만 재렌더 (미세조정 후). 나머지는 엔진에서 기존 결과 유지.
  renderOne: async (index) => {
    const { candidatesData, selected, crop, source } = get();
    if (!candidatesData) return;
    const chosen = candidatesData.candidates.filter((c) => selected.includes(c.id));
    set({ status: "rendering" });

    const unsub = window.sermoncut.onEngineProgress((p) => {
      set((s) => ({ progress: { ...s.progress, [p.step]: p.percent ?? 0 } }));
    });
    try {
      const res = await window.sermoncut.runEngine<{ shorts: RenderResult[] }>(
        "render",
        { project: get().projectDir, selected: chosen, crop, source, only: [index] }
      );
      set({ status: "done", results: res.shorts, renderTick: get().renderTick + 1 });
    } catch (e) {
      if (isCancel(e)) set({ status: "cancelled", error: null });
      else set({ status: "error", error: String(e) });
    } finally {
      unsub?.();
    }
  },

  cancel: async () => {
    try {
      await window.sermoncut.cancelEngine();
    } catch {
      // 취소 호출 자체 실패는 무시
    }
  },

  reset: () =>
    set({
      status: "idle",
      error: null,
      source: null,
      transcript: null,
      analysis: null,
      candidatesData: null,
      selected: [],
      results: [],
      progress: {},
      analyzeStartedAt: null,
      analyzeElapsedMs: null,
      renderStartedAt: null,
      renderElapsedMs: null,
    }),
}));
