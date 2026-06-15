import { create } from "zustand";
import {
  defaultSelection,
  toggleSelection,
  type Candidate,
} from "../lib/selection";

type Status = "idle" | "analyzing" | "ready" | "rendering" | "done" | "error";
type Crop = "left" | "center" | "right";

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

  // actions
  setInputType: (t: "youtube" | "local") => void;
  setUrl: (v: string) => void;
  setPath: (v: string) => void;
  setCaptionMethod: (m: "auto" | "whisper" | "import") => void;
  toggleCandidate: (id: string) => void;
  setCrop: (c: Crop) => void;
  analyze: () => Promise<void>;
  render: () => Promise<void>;
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

  setInputType: (t) => set({ inputType: t }),
  setUrl: (v) => set({ url: v }),
  setPath: (v) => set({ path: v }),
  setCaptionMethod: (m) => set({ captionMethod: m }),

  toggleCandidate: (id) => set({ selected: toggleSelection(get().selected, id) }),
  setCrop: (c) => set({ crop: c }),

  analyze: async () => {
    const { inputType, url, path, captionMethod } = get();
    set({ status: "analyzing", error: null });
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
      set({ status: "error", error: String(e) });
    }
  },

  render: async () => {
    const { candidatesData, selected, crop, source } = get();
    if (!candidatesData) return;
    const chosen = candidatesData.candidates.filter((c) =>
      selected.includes(c.id)
    );
    set({ status: "rendering", results: [] });

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
      set({ status: "error", error: String(e) });
    } finally {
      unsub?.();
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
    }),
}));
