import { describe, it, expect } from "vitest";
import {
  toggleSelection,
  canConfirm,
  defaultSelection,
  type Candidate,
} from "./selection";

describe("toggleSelection", () => {
  it("미선택 항목을 추가한다", () => {
    expect(toggleSelection(["a"], "b")).toEqual(["a", "b"]);
  });

  it("선택된 항목을 해제한다", () => {
    expect(toggleSelection(["a", "b"], "a")).toEqual(["b"]);
  });

  it("3개 한도 도달 시 추가를 무시한다", () => {
    expect(toggleSelection(["a", "b", "c"], "d")).toEqual(["a", "b", "c"]);
  });

  it("한도여도 해제는 허용한다", () => {
    expect(toggleSelection(["a", "b", "c"], "b")).toEqual(["a", "c"]);
  });
});

describe("canConfirm", () => {
  it("정확히 3개일 때만 true", () => {
    expect(canConfirm(["a", "b", "c"])).toBe(true);
    expect(canConfirm(["a", "b"])).toBe(false);
    expect(canConfirm([])).toBe(false);
  });
});

describe("defaultSelection", () => {
  const cands: Candidate[] = [
    { id: "c1", score: 70 },
    { id: "c2", score: 90 },
    { id: "c3", score: 80 },
    { id: "c4", score: 60 },
    { id: "c5", score: 50 },
  ];

  it("유효한 추천 3개를 그대로 사용", () => {
    expect(defaultSelection(cands, ["c1", "c3", "c5"])).toEqual(["c1", "c3", "c5"]);
  });

  it("추천이 없으면 점수 상위 3개", () => {
    expect(defaultSelection(cands, [])).toEqual(["c2", "c3", "c1"]);
  });

  it("추천에 잘못된 id가 섞이면 점수 상위로 폴백", () => {
    expect(defaultSelection(cands, ["c2", "bad"])).toEqual(["c2", "c3", "c1"]);
  });
});
