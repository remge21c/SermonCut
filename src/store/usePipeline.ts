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
type Crop = "left" | "center" | "right";

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
  // 입력
  inputType: "youtube" | "local";
  url: string;
  path: string;
  captionMethod: "auto" | "whisper" | "import";

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

  // 경과 시간(ms)
  analyzeStartedAt: number | null;
  analyzeElapsedMs: number | null;
  renderStartedAt: number | null;
  renderElapsedMs: number | null;

  // actions
  setInputType: (t: "youtube" | "local") => void;
  setUrl: (v: string) => void;
  setPath: (v: string) => void;
  setCaptionMethod: (m: "auto" | "whisper" | "import") => void;
  toggleCandidate: (id: string) => void;
  setCrop: (c: Crop) => void;
  analyze: () => Promise<void>;
  render: () => Promise<void>;
  cancel: () => Promise<void>;
  reset: () => void;
}

export const usePipeline = create<PipelineState>((set, get) => ({
  inputType: "youtube",
  url: "",
  path: "",
  captionMethod: "auto",

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

  analyzeStartedAt: null,
  analyzeElapsedMs: null,
  renderStartedAt: null,
  renderElapsedMs: null,

  setInputType: (t) => set({ inputType: t }),
  setUrl: (v) => set({ url: v }),
  setPath: (v) => set({ path: v }),
  setCaptionMethod: (m) => set({ captionMethod: m }),

  toggleCandidate: (id) => set({ selected: toggleSelection(get().selected, id) }),
  setCrop: (c) => set({ crop: c }),

  analyze: async () => {
    const { inputType, url, path, captionMethod } = get();
    set({
      status: "analyzing",
      error: null,
      analyzeStartedAt: Date.now(),
      analyzeElapsedMs: null,
    });
    try {
      const input =
        inputType === "youtube"
          ? { type: "youtube", url }
          : { type: "local", path };
      const res = await window.sermoncut.runEngine<{
        source: Record<string, unknown>;
        analysis: Record<string, unknown>;
        candidates: CandidatesData;
      }>("analyze", { input, caption_method: captionMethod });

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
        { selected: chosen, crop, source }
      );
      set({ status: "done", results: res.shorts });
    } catch (e) {
      if (isCancel(e)) set({ status: "cancelled", error: null });
      else set({ status: "error", error: String(e) });
    } finally {
      unsub?.();
      const startedAt = get().renderStartedAt;
      set({ renderElapsedMs: startedAt ? Date.now() - startedAt : null });
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
